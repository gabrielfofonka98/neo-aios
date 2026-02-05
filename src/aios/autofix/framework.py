"""Auto-fix framework.

This module provides the main framework for managing and applying auto-fixes
to security findings. It handles fixer registration, finding matching,
and batch fix operations.

Example:
    >>> from aios.autofix.framework import AutoFixFramework
    >>> from aios.autofix.base import BaseFixer
    >>>
    >>> framework = AutoFixFramework()
    >>> framework.register_fixer(MyCustomFixer())
    >>>
    >>> # Fix a single finding
    >>> result = framework.fix_finding(finding, dry_run=True)
    >>>
    >>> # Fix all findings
    >>> batch_result = framework.fix_all(findings, dry_run=True)
"""

from collections.abc import Sequence
from datetime import datetime
from typing import TYPE_CHECKING

from aios.autofix.base import BaseFixer
from aios.autofix.models import FixBatchResult
from aios.autofix.models import FixConfidence
from aios.autofix.models import FixerCapability
from aios.autofix.models import FixResult
from aios.autofix.models import FixStatus
from aios.autofix.models import FixSuggestion

if TYPE_CHECKING:
    from aios.security.models import SecurityFinding


class AutoFixFramework:
    """Framework for managing and applying auto-fixes.

    The AutoFixFramework acts as a registry and orchestrator for fixers.
    It handles:
    - Registering fixers for different finding types
    - Finding the appropriate fixer for a given finding
    - Applying fixes (single or batch)
    - Managing dry-run vs actual application
    - Rollback support

    Attributes:
        fixers: Dictionary of registered fixers by ID.
    """

    def __init__(self) -> None:
        """Initialize the auto-fix framework."""
        self._fixers: dict[str, BaseFixer] = {}
        self._fixer_order: list[str] = []  # Ordered by priority

    @property
    def fixers(self) -> dict[str, BaseFixer]:
        """Get all registered fixers."""
        return self._fixers.copy()

    @property
    def fixer_count(self) -> int:
        """Get the number of registered fixers."""
        return len(self._fixers)

    def register_fixer(self, fixer: BaseFixer) -> None:
        """Register a fixer with the framework.

        Args:
            fixer: The fixer to register.

        Raises:
            ValueError: If a fixer with the same ID is already registered.
        """
        if fixer.fixer_id in self._fixers:
            raise ValueError(f"Fixer with ID '{fixer.fixer_id}' already registered")

        self._fixers[fixer.fixer_id] = fixer
        self._update_fixer_order()

    def unregister_fixer(self, fixer_id: str) -> bool:
        """Unregister a fixer from the framework.

        Args:
            fixer_id: ID of the fixer to remove.

        Returns:
            True if the fixer was removed, False if not found.
        """
        if fixer_id in self._fixers:
            del self._fixers[fixer_id]
            self._update_fixer_order()
            return True
        return False

    def get_fixer(self, fixer_id: str) -> BaseFixer | None:
        """Get a fixer by ID.

        Args:
            fixer_id: ID of the fixer to retrieve.

        Returns:
            The fixer if found, None otherwise.
        """
        return self._fixers.get(fixer_id)

    def get_fixer_for(self, finding: "SecurityFinding") -> BaseFixer | None:
        """Find a fixer that can handle the given finding.

        Searches through registered fixers in priority order and returns
        the first one that can handle the finding.

        Args:
            finding: The security finding to find a fixer for.

        Returns:
            A fixer that can handle the finding, or None if no match.
        """
        for fixer_id in self._fixer_order:
            fixer = self._fixers[fixer_id]
            if fixer.can_fix(finding):
                return fixer
        return None

    def get_all_fixers_for(self, finding: "SecurityFinding") -> list[BaseFixer]:
        """Find all fixers that can handle the given finding.

        Args:
            finding: The security finding to find fixers for.

        Returns:
            List of fixers that can handle the finding (by priority).
        """
        matching: list[BaseFixer] = []
        for fixer_id in self._fixer_order:
            fixer = self._fixers[fixer_id]
            if fixer.can_fix(finding):
                matching.append(fixer)
        return matching

    def get_capabilities(self) -> list[FixerCapability]:
        """Get capabilities of all registered fixers.

        Returns:
            List of FixerCapability for all registered fixers.
        """
        return [fixer.get_capability() for fixer in self._fixers.values()]

    def fix_finding(
        self,
        finding: "SecurityFinding",
        dry_run: bool = True,
        fixer_id: str | None = None,
    ) -> FixResult:
        """Fix a single security finding.

        Args:
            finding: The security finding to fix.
            dry_run: If True, only generate diff without applying.
                    Defaults to True for safety.
            fixer_id: Optional specific fixer ID to use.
                     If None, automatically selects the best fixer.

        Returns:
            FixResult with the outcome of the fix operation.
        """
        # Get the fixer to use
        if fixer_id:
            fixer = self.get_fixer(fixer_id)
            if fixer is None:
                return self._create_error_result(
                    finding.id,
                    f"Fixer '{fixer_id}' not found",
                )
            if not fixer.can_fix(finding):
                return self._create_error_result(
                    finding.id,
                    f"Fixer '{fixer_id}' cannot fix finding '{finding.id}'",
                )
        else:
            fixer = self.get_fixer_for(finding)
            if fixer is None:
                return self._create_error_result(
                    finding.id,
                    f"No fixer available for finding '{finding.id}'",
                )

        # Apply the fix
        return fixer.apply_fix(finding, dry_run=dry_run)

    def fix_all(
        self,
        findings: Sequence["SecurityFinding"],
        dry_run: bool = True,
        stop_on_error: bool = False,
    ) -> FixBatchResult:
        """Fix multiple security findings.

        Args:
            findings: Sequence of security findings to fix.
            dry_run: If True, only generate diffs without applying.
                    Defaults to True for safety.
            stop_on_error: If True, stop on first error.
                          Defaults to False.

        Returns:
            FixBatchResult with aggregated results.
        """
        batch_result = FixBatchResult(
            dry_run=dry_run,
            started_at=datetime.now(),
        )

        for finding in findings:
            # Only process auto-fixable findings
            if not finding.auto_fixable:
                result = self._create_error_result(
                    finding.id,
                    "Finding is not marked as auto-fixable",
                    status=FixStatus.SKIPPED,
                )
                batch_result.add_result(result)
                continue

            result = self.fix_finding(finding, dry_run=dry_run)
            batch_result.add_result(result)

            if stop_on_error and not result.success:
                break

        batch_result.completed_at = datetime.now()
        return batch_result

    def fix_auto_fixable(
        self,
        findings: Sequence["SecurityFinding"],
        dry_run: bool = True,
    ) -> FixBatchResult:
        """Fix only findings marked as auto-fixable.

        Convenience method that filters to auto-fixable findings.

        Args:
            findings: Sequence of security findings.
            dry_run: If True, only generate diffs.

        Returns:
            FixBatchResult with results for auto-fixable findings only.
        """
        auto_fixable = [f for f in findings if f.auto_fixable]
        return self.fix_all(auto_fixable, dry_run=dry_run)

    def rollback_batch(self, batch_result: FixBatchResult) -> int:
        """Rollback all fixes from a batch operation.

        Args:
            batch_result: The batch result to rollback.

        Returns:
            Number of fixes successfully rolled back.
        """
        rolled_back = 0
        for result in batch_result.get_successful_results():
            if result.backup_path is None or result.file_path is None:
                continue

            fixer = self.get_fixer_for_finding_id(result.finding_id)
            if fixer and fixer.rollback(result):
                rolled_back += 1

        return rolled_back

    def get_fixer_for_finding_id(self, finding_id: str) -> BaseFixer | None:
        """Get a fixer by examining a finding ID pattern.

        This is a best-effort method that tries to match fixer to finding
        based on ID patterns. Override in subclass for custom matching.

        Args:
            finding_id: The finding ID to match.

        Returns:
            A potentially matching fixer, or None.
        """
        # Default implementation: try to match by category prefix
        # e.g., "xss-001" -> look for fixer that handles "xss"
        prefix = finding_id.split("-", maxsplit=1)[0] if "-" in finding_id else finding_id

        for fixer_id in self._fixer_order:
            fixer = self._fixers[fixer_id]
            if prefix in fixer.supported_categories:
                return fixer

        # Fallback: return first fixer
        if self._fixer_order:
            return self._fixers[self._fixer_order[0]]
        return None

    def _update_fixer_order(self) -> None:
        """Update the fixer order based on priority."""
        self._fixer_order = sorted(
            self._fixers.keys(),
            key=lambda x: self._fixers[x].priority,
            reverse=True,  # Higher priority first
        )

    def _create_error_result(
        self,
        finding_id: str,
        error_message: str,
        status: FixStatus = FixStatus.FAILED,
    ) -> FixResult:
        """Create an error FixResult.

        Args:
            finding_id: ID of the finding.
            error_message: Error message to include.
            status: Status to set. Defaults to FAILED.

        Returns:
            FixResult with error information.
        """
        return FixResult(
            success=False,
            finding_id=finding_id,
            suggestion=FixSuggestion(
                old_code="",
                new_code="",
                explanation=error_message,
                confidence=FixConfidence.LOW,
            ),
            status=status,
            error_message=error_message,
        )
