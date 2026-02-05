"""Bounded reflexion loop for auto-fix with verification.

This module provides the BoundedReflexion class that implements a fix-verify loop
with a maximum number of iterations. It ensures fixes actually work by re-scanning
after each fix attempt.

The reflexion loop:
1. Apply fix
2. Re-scan to verify fix worked
3. If finding gone -> SUCCESS
4. If finding still there -> try different approach
5. If new findings introduced -> ROLLBACK
6. Maximum 3 iterations to prevent infinite loops

Example:
    >>> from aios.autofix.reflexion import BoundedReflexion
    >>> from aios.autofix.framework import AutoFixFramework
    >>> from aios.security.orchestrator import SecurityOrchestrator
    >>>
    >>> reflexion = BoundedReflexion(framework, orchestrator)
    >>> result = reflexion.fix_with_verification(finding)
    >>> if result.success:
    ...     print(f"Fixed in {result.iterations} iteration(s)")
    >>> else:
    ...     print(f"Failed after {result.iterations} attempts: {result.error}")
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from aios.autofix.base import BaseFixer
    from aios.autofix.framework import AutoFixFramework
    from aios.autofix.models import FixResult
    from aios.security.models import SecurityFinding
    from aios.security.models import SecurityReport
    from aios.security.orchestrator import SecurityOrchestrator


# Configure module logger
logger = logging.getLogger(__name__)


# Default configuration constants
DEFAULT_MAX_ITERATIONS = 3
DEFAULT_TIMEOUT_PER_ITERATION = 30.0  # seconds


@dataclass
class _VerificationResult:
    """Internal result from verification scan."""

    success: bool
    regression_detected: bool
    report: SecurityReport | None


@dataclass
class ReflexionResult:
    """Result of a bounded reflexion fix attempt.

    Attributes:
        success: Whether the fix ultimately succeeded.
        iterations: Number of fix attempts made.
        original_finding: The finding that was being fixed.
        final_fix: The last fix result (if any fix was applied).
        verification_report: The final verification scan report.
        rolled_back: Whether the fix was rolled back due to regression.
        error: Error message if fix failed.
        attempt_history: List of all fix attempts made.
        started_at: When the reflexion loop started.
        completed_at: When the reflexion loop completed.
        duration_ms: Total duration in milliseconds.
    """

    success: bool
    iterations: int
    original_finding: SecurityFinding
    final_fix: FixResult | None = None
    verification_report: SecurityReport | None = None
    rolled_back: bool = False
    error: str | None = None
    attempt_history: list[FixResult] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None
    duration_ms: int = 0

    @property
    def needs_escalation(self) -> bool:
        """Check if this finding needs human escalation.

        A finding needs escalation if:
        - All iterations were exhausted without success
        - The fix was rolled back due to regression
        """
        return not self.success and self.iterations >= DEFAULT_MAX_ITERATIONS


class BoundedReflexion:
    """Bounded reflexion loop for fix verification.

    Implements a fix-verify-retry loop with configurable maximum iterations.
    Ensures fixes actually resolve findings by re-scanning after each attempt.

    Attributes:
        framework: The auto-fix framework to use for applying fixes.
        orchestrator: The security orchestrator for verification scans.
        max_iterations: Maximum number of fix attempts (default 3).
        timeout_per_iteration: Timeout in seconds per iteration (default 30).

    Example:
        >>> reflexion = BoundedReflexion(framework, orchestrator, max_iterations=3)
        >>> result = reflexion.fix_with_verification(finding)
        >>> print(f"Success: {result.success}, Iterations: {result.iterations}")
    """

    def __init__(
        self,
        framework: AutoFixFramework,
        orchestrator: SecurityOrchestrator,
        max_iterations: int = DEFAULT_MAX_ITERATIONS,
        timeout_per_iteration: float = DEFAULT_TIMEOUT_PER_ITERATION,
    ) -> None:
        """Initialize the bounded reflexion loop.

        Args:
            framework: Auto-fix framework for applying fixes.
            orchestrator: Security orchestrator for verification.
            max_iterations: Maximum fix attempts (1-10, default 3).
            timeout_per_iteration: Timeout per iteration in seconds (default 30).

        Raises:
            ValueError: If max_iterations is not between 1 and 10.
        """
        if not 1 <= max_iterations <= 10:
            raise ValueError(
                f"max_iterations must be between 1 and 10, got {max_iterations}"
            )

        self._framework = framework
        self._orchestrator = orchestrator
        self._max_iterations = max_iterations
        self._timeout_per_iteration = timeout_per_iteration

    @property
    def framework(self) -> AutoFixFramework:
        """Get the auto-fix framework."""
        return self._framework

    @property
    def orchestrator(self) -> SecurityOrchestrator:
        """Get the security orchestrator."""
        return self._orchestrator

    @property
    def max_iterations(self) -> int:
        """Get the maximum iterations."""
        return self._max_iterations

    @property
    def timeout_per_iteration(self) -> float:
        """Get the timeout per iteration."""
        return self._timeout_per_iteration

    def fix_with_verification(
        self,
        finding: SecurityFinding,
        dry_run: bool = False,
    ) -> ReflexionResult:
        """Fix a finding with verification loop.

        Attempts to fix the finding and verifies the fix worked by re-scanning.
        If the fix didn't work, tries a different approach. If the fix introduced
        new issues, rolls back.

        Args:
            finding: The security finding to fix.
            dry_run: If True, only simulate (no actual changes).

        Returns:
            ReflexionResult with the outcome of the fix attempts.
        """

        started_at = datetime.now()
        attempt_history: list[FixResult] = []
        used_fixer_ids: set[str] = set()

        logger.info(
            "Starting bounded reflexion for finding %s (max %d iterations)",
            finding.id,
            self._max_iterations,
        )

        for iteration in range(1, self._max_iterations + 1):
            start_time = time.time()

            logger.debug(
                "Iteration %d/%d for finding %s",
                iteration,
                self._max_iterations,
                finding.id,
            )

            # Check timeout
            elapsed = time.time() - start_time
            if elapsed > self._timeout_per_iteration:
                logger.warning(
                    "Iteration %d timed out after %.2fs", iteration, elapsed
                )
                break

            # Get available fixers (excluding already tried ones)
            available_fixers = [
                f
                for f in self._framework.get_all_fixers_for(finding)
                if f.fixer_id not in used_fixer_ids
            ]

            if not available_fixers:
                logger.debug("No more available fixers for finding %s", finding.id)
                # If we've tried fixers and none worked, that's a failure
                if attempt_history:
                    return self._create_failure_result(
                        finding=finding,
                        iterations=iteration,
                        attempt_history=attempt_history,
                        error="All available fixers exhausted without success",
                        started_at=started_at,
                    )
                # No fixers available at all
                return self._create_failure_result(
                    finding=finding,
                    iterations=0,
                    attempt_history=[],
                    error=f"No fixer available for finding '{finding.id}'",
                    started_at=started_at,
                )

            # Try the next available fixer
            fixer = available_fixers[0]
            used_fixer_ids.add(fixer.fixer_id)

            logger.debug(
                "Trying fixer '%s' for finding %s", fixer.fixer_id, finding.id
            )

            # Apply the fix
            fix_result = self._framework.fix_finding(
                finding,
                dry_run=dry_run,
                fixer_id=fixer.fixer_id,
            )
            attempt_history.append(fix_result)

            if not fix_result.success:
                logger.debug(
                    "Fixer '%s' failed: %s",
                    fixer.fixer_id,
                    fix_result.error_message,
                )
                continue

            # In dry-run mode, we can't verify - just return success
            if dry_run:
                logger.info("Dry-run mode: fix applied (iteration %d)", iteration)
                return ReflexionResult(
                    success=True,
                    iterations=iteration,
                    original_finding=finding,
                    final_fix=fix_result,
                    verification_report=None,
                    rolled_back=False,
                    error=None,
                    attempt_history=attempt_history,
                    started_at=started_at,
                    completed_at=datetime.now(),
                    duration_ms=int((time.time() - started_at.timestamp()) * 1000),
                )

            # Verify the fix by re-scanning
            verification_result = self._verify_fix(finding, fix_result)

            if verification_result.success:
                logger.info(
                    "Fix verified successfully in iteration %d using fixer '%s'",
                    iteration,
                    fixer.fixer_id,
                )
                return ReflexionResult(
                    success=True,
                    iterations=iteration,
                    original_finding=finding,
                    final_fix=fix_result,
                    verification_report=verification_result.report,
                    rolled_back=False,
                    error=None,
                    attempt_history=attempt_history,
                    started_at=started_at,
                    completed_at=datetime.now(),
                    duration_ms=int((time.time() - started_at.timestamp()) * 1000),
                )

            if verification_result.regression_detected:
                logger.warning(
                    "Regression detected in iteration %d, rolling back",
                    iteration,
                )
                # Rollback the fix
                self._rollback_fix(fixer, fix_result)
                return ReflexionResult(
                    success=False,
                    iterations=iteration,
                    original_finding=finding,
                    final_fix=fix_result,
                    verification_report=verification_result.report,
                    rolled_back=True,
                    error="Fix introduced new security findings (regression)",
                    attempt_history=attempt_history,
                    started_at=started_at,
                    completed_at=datetime.now(),
                    duration_ms=int((time.time() - started_at.timestamp()) * 1000),
                )

            # Fix didn't work, try again with different fixer
            logger.debug(
                "Fix from '%s' did not resolve finding, trying next fixer",
                fixer.fixer_id,
            )
            # Rollback before trying next fixer
            self._rollback_fix(fixer, fix_result)

        # All iterations exhausted
        logger.warning(
            "Exhausted all %d iterations for finding %s",
            self._max_iterations,
            finding.id,
        )
        return self._create_failure_result(
            finding=finding,
            iterations=self._max_iterations,
            attempt_history=attempt_history,
            error=f"Failed to fix after {self._max_iterations} attempts",
            started_at=started_at,
        )

    def fix_all_with_verification(
        self,
        findings: Sequence[SecurityFinding],
        dry_run: bool = False,
    ) -> list[ReflexionResult]:
        """Fix multiple findings with verification.

        Processes each finding through the bounded reflexion loop.
        Findings are processed sequentially to avoid conflicts.

        Args:
            findings: Sequence of security findings to fix.
            dry_run: If True, only simulate (no actual changes).

        Returns:
            List of ReflexionResult for each finding.
        """
        results: list[ReflexionResult] = []

        for finding in findings:
            # Only process auto-fixable findings
            if not finding.auto_fixable:
                logger.debug("Skipping non-auto-fixable finding %s", finding.id)
                results.append(
                    ReflexionResult(
                        success=False,
                        iterations=0,
                        original_finding=finding,
                        final_fix=None,
                        verification_report=None,
                        rolled_back=False,
                        error="Finding is not marked as auto-fixable",
                        started_at=datetime.now(),
                        completed_at=datetime.now(),
                        duration_ms=0,
                    )
                )
                continue

            result = self.fix_with_verification(finding, dry_run=dry_run)
            results.append(result)

        return results

    def _verify_fix(
        self,
        original_finding: SecurityFinding,
        fix_result: FixResult,
    ) -> _VerificationResult:
        """Verify a fix by re-scanning.

        Re-scans the file to check if:
        1. The original finding is gone (success)
        2. The original finding persists (fix didn't work)
        3. New findings were introduced (regression)

        Args:
            original_finding: The finding that was fixed.
            fix_result: The result of the fix attempt.

        Returns:
            _VerificationResult with verification outcome.
        """
        if fix_result.file_path is None:
            return _VerificationResult(
                success=False,
                regression_detected=False,
                report=None,
            )

        file_path = Path(fix_result.file_path)

        # Re-scan the file using the same validator
        try:
            report = self._orchestrator.scan(
                file_path,
                validators=[original_finding.validator_id],
            )
        except Exception as e:
            logger.error("Verification scan failed: %s", e)
            return _VerificationResult(
                success=False,
                regression_detected=False,
                report=None,
            )

        # Check if original finding is still present
        finding_present = self._is_finding_present(original_finding, report)

        # Check for regressions (new findings in the same file)
        regression_detected = self._check_for_regressions(
            original_finding,
            report,
        )

        return _VerificationResult(
            success=not finding_present and not regression_detected,
            regression_detected=regression_detected,
            report=report,
        )

    def _is_finding_present(
        self,
        finding: SecurityFinding,
        report: SecurityReport,
    ) -> bool:
        """Check if a finding is still present in the report.

        Matches by:
        1. Same location (file, line)
        2. Same category
        3. Similar title

        Args:
            finding: The finding to check for.
            report: The scan report to search.

        Returns:
            True if the finding appears to still be present.
        """
        for result in report.results:
            for f in result.findings:
                # Check file path
                if f.location.file_path != finding.location.file_path:
                    continue

                # Check if line overlaps
                if not self._lines_overlap(
                    (finding.location.line_start, finding.location.line_end),
                    (f.location.line_start, f.location.line_end),
                ):
                    continue

                # Check category
                if f.category == finding.category:
                    return True

        return False

    def _check_for_regressions(
        self,
        original_finding: SecurityFinding,
        report: SecurityReport,
    ) -> bool:
        """Check if new findings were introduced.

        A regression is detected if there are new HIGH or CRITICAL findings
        in the same file that weren't in the original scan.

        Args:
            original_finding: The original finding that was fixed.
            report: The verification scan report.

        Returns:
            True if regression detected.
        """
        from aios.security.models import Severity

        for result in report.results:
            for f in result.findings:
                # Only check same file
                if f.location.file_path != original_finding.location.file_path:
                    continue

                # Skip the original finding
                if f.id == original_finding.id:
                    continue

                # Check severity - only HIGH and CRITICAL count as regressions
                if f.severity in (Severity.CRITICAL, Severity.HIGH):
                    # This is a new severe finding - regression!
                    logger.warning(
                        "Regression: new %s finding '%s' at line %d",
                        f.severity.value,
                        f.title,
                        f.location.line_start,
                    )
                    return True

        return False

    def _rollback_fix(self, fixer: BaseFixer, fix_result: FixResult) -> bool:
        """Rollback a fix using the fixer.

        Args:
            fixer: The fixer that applied the fix.
            fix_result: The fix result to rollback.

        Returns:
            True if rollback succeeded.
        """
        if not fix_result.can_rollback:
            logger.warning("Fix cannot be rolled back (no backup)")
            return False

        try:
            success = fixer.rollback(fix_result)
            if success:
                logger.info("Successfully rolled back fix")
            else:
                logger.warning("Rollback returned False")
            return success
        except Exception as e:
            logger.error("Rollback failed: %s", e)
            return False

    def _lines_overlap(
        self,
        range1: tuple[int, int],
        range2: tuple[int, int],
    ) -> bool:
        """Check if two line ranges overlap.

        Args:
            range1: First range (start, end).
            range2: Second range (start, end).

        Returns:
            True if ranges overlap.
        """
        start1, end1 = range1
        start2, end2 = range2
        return start1 <= end2 and start2 <= end1

    def _create_failure_result(
        self,
        finding: SecurityFinding,
        iterations: int,
        attempt_history: list[FixResult],
        error: str,
        started_at: datetime,
    ) -> ReflexionResult:
        """Create a failure result.

        Args:
            finding: The original finding.
            iterations: Number of iterations attempted.
            attempt_history: History of fix attempts.
            error: Error message.
            started_at: When the loop started.

        Returns:
            ReflexionResult indicating failure.
        """
        completed_at = datetime.now()
        duration_ms = int((completed_at.timestamp() - started_at.timestamp()) * 1000)

        return ReflexionResult(
            success=False,
            iterations=iterations,
            original_finding=finding,
            final_fix=attempt_history[-1] if attempt_history else None,
            verification_report=None,
            rolled_back=False,
            error=error,
            attempt_history=attempt_history,
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=duration_ms,
        )


__all__ = [
    "DEFAULT_MAX_ITERATIONS",
    "DEFAULT_TIMEOUT_PER_ITERATION",
    "BoundedReflexion",
    "ReflexionResult",
]
