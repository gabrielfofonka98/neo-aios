"""Security orchestrator for coordinating validators.

This module provides the SecurityOrchestrator class that coordinates the execution
of multiple security validators, supporting parallel execution, timeouts, and
progress tracking.

Example:
    >>> from pathlib import Path
    >>> from aios.security.orchestrator import security_orchestrator
    >>> report = security_orchestrator.scan(Path("./src"))
    >>> print(f"Found {report.total_findings} issues")
"""

from __future__ import annotations

import asyncio
import time
import uuid
from concurrent.futures import Future
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from datetime import datetime
from typing import TYPE_CHECKING
from typing import Protocol

from aios.security.models import SecurityFinding
from aios.security.models import SecurityReport
from aios.security.models import Severity
from aios.security.models import ValidatorResult
from aios.security.validators.registry import ValidatorRegistry
from aios.security.validators.registry import validator_registry

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from aios.security.validators.base import SecurityValidator


# Severity ordering for sorting (lower index = higher priority)
SEVERITY_ORDER: dict[Severity, int] = {
    Severity.CRITICAL: 0,
    Severity.HIGH: 1,
    Severity.MEDIUM: 2,
    Severity.LOW: 3,
    Severity.INFO: 4,
}


class ProgressCallback(Protocol):
    """Protocol for progress callback functions.

    Progress callbacks receive the validator ID, current index,
    and total count of validators being run.
    """

    def __call__(
        self,
        validator_id: str,
        current: int,
        total: int,
        status: str,
    ) -> None:
        """Called when a validator starts or completes.

        Args:
            validator_id: ID of the validator.
            current: Current validator index (1-based).
            total: Total number of validators.
            status: Status message ("starting", "completed", "timeout", "error").
        """
        ...


class ScanConfig:
    """Configuration for a security scan.

    Attributes:
        timeout_per_validator: Timeout in seconds for each validator (default 30).
        max_workers: Maximum concurrent validators (default 4).
        fail_fast: Stop on first critical finding (default False).
        quick_scan_validators: Validator IDs for quick scan mode.
    """

    def __init__(
        self,
        timeout_per_validator: float = 30.0,
        max_workers: int = 4,
        fail_fast: bool = False,
        quick_scan_validators: list[str] | None = None,
    ) -> None:
        """Initialize scan configuration.

        Args:
            timeout_per_validator: Timeout in seconds per validator.
            max_workers: Maximum concurrent validators.
            fail_fast: Whether to stop on first critical finding.
            quick_scan_validators: Validator IDs for quick scan mode.
        """
        self.timeout_per_validator = timeout_per_validator
        self.max_workers = max_workers
        self.fail_fast = fail_fast
        self.quick_scan_validators = quick_scan_validators or [
            "sec-secret-scanner",
            "sec-xss-hunter",
            "sec-injection-detector",
        ]


class SecurityOrchestrator:
    """Orchestrates security validators for comprehensive scanning.

    The orchestrator coordinates multiple security validators, running them
    in parallel for performance while handling timeouts and errors gracefully.

    Attributes:
        registry: The validator registry to use.
        config: Scan configuration.

    Example:
        >>> from aios.security.orchestrator import SecurityOrchestrator
        >>> from aios.security.validators import validator_registry
        >>> orchestrator = SecurityOrchestrator(validator_registry)
        >>> report = orchestrator.scan(Path("./src"))
    """

    def __init__(
        self,
        registry: ValidatorRegistry,
        config: ScanConfig | None = None,
    ) -> None:
        """Initialize the orchestrator.

        Args:
            registry: Validator registry containing available validators.
            config: Optional scan configuration.
        """
        self._registry = registry
        self._config = config or ScanConfig()

    @property
    def registry(self) -> ValidatorRegistry:
        """Get the validator registry."""
        return self._registry

    @property
    def config(self) -> ScanConfig:
        """Get the scan configuration."""
        return self._config

    def scan(
        self,
        path: Path,
        validators: list[str] | None = None,
        progress_callback: ProgressCallback | None = None,
    ) -> SecurityReport:
        """Execute a synchronous security scan.

        Runs validators in parallel using ThreadPoolExecutor for performance.
        Each validator has a timeout to prevent hanging.

        Args:
            path: Path to scan (file or directory).
            validators: Optional list of validator IDs to run. If None, runs all.
            progress_callback: Optional callback for progress updates.

        Returns:
            SecurityReport with aggregated findings from all validators.

        Example:
            >>> report = orchestrator.scan(Path("./src"))
            >>> if report.has_blockers:
            ...     print("Critical/High findings detected!")
        """
        scan_id = str(uuid.uuid4())[:8]
        started_at = datetime.now()

        # Get validators to run
        validators_to_run = self._get_validators(validators)
        total_validators = len(validators_to_run)

        report = SecurityReport(
            scan_id=scan_id,
            started_at=started_at,
            target_path=str(path),
        )

        if not validators_to_run:
            report.completed_at = datetime.now()
            return report

        # Run validators in parallel
        with ThreadPoolExecutor(max_workers=self._config.max_workers) as executor:
            # Submit all validator tasks
            futures: dict[Future[ValidatorResult], tuple[SecurityValidator, int]] = {}
            for idx, validator in enumerate(validators_to_run):
                future = executor.submit(self._run_validator, validator, path)
                futures[future] = (validator, idx + 1)

            # Collect results as they complete
            for future, (validator, current_idx) in futures.items():

                if progress_callback:
                    progress_callback(validator.id, current_idx, total_validators, "starting")

                try:
                    result = future.result(timeout=self._config.timeout_per_validator)
                    report.add_result(result)

                    if progress_callback:
                        status = "completed" if not result.error else "error"
                        progress_callback(validator.id, current_idx, total_validators, status)

                    # Check fail_fast condition
                    if self._config.fail_fast and result.critical_count > 0:
                        # Cancel remaining futures
                        for f in futures:
                            f.cancel()
                        break

                except FuturesTimeoutError:
                    # Validator timed out
                    timeout_result = ValidatorResult(
                        validator_id=validator.id,
                        validator_name=validator.name,
                        error=f"Validator timed out after {self._config.timeout_per_validator}s",
                        scan_duration_ms=int(self._config.timeout_per_validator * 1000),
                    )
                    report.add_result(timeout_result)

                    if progress_callback:
                        progress_callback(validator.id, current_idx, total_validators, "timeout")

                except Exception as e:
                    # Validator raised an exception
                    error_result = ValidatorResult(
                        validator_id=validator.id,
                        validator_name=validator.name,
                        error=f"Validator failed: {e!s}",
                    )
                    report.add_result(error_result)

                    if progress_callback:
                        progress_callback(validator.id, current_idx, total_validators, "error")

        # Sort findings by severity
        self._sort_findings_by_severity(report)

        report.completed_at = datetime.now()
        return report

    async def scan_async(
        self,
        path: Path,
        validators: list[str] | None = None,
        progress_callback: Callable[
            [str, int, int, str], None
        ] | None = None,
    ) -> SecurityReport:
        """Execute an asynchronous security scan.

        Runs validators concurrently using asyncio for non-blocking execution.
        Useful in async contexts like web servers.

        Args:
            path: Path to scan (file or directory).
            validators: Optional list of validator IDs to run. If None, runs all.
            progress_callback: Optional callback for progress updates.

        Returns:
            SecurityReport with aggregated findings from all validators.

        Example:
            >>> report = await orchestrator.scan_async(Path("./src"))
        """
        scan_id = str(uuid.uuid4())[:8]
        started_at = datetime.now()

        validators_to_run = self._get_validators(validators)
        total_validators = len(validators_to_run)

        report = SecurityReport(
            scan_id=scan_id,
            started_at=started_at,
            target_path=str(path),
        )

        if not validators_to_run:
            report.completed_at = datetime.now()
            return report

        # Create async tasks for all validators
        tasks: list[asyncio.Task[ValidatorResult]] = []
        validator_map: dict[asyncio.Task[ValidatorResult], tuple[SecurityValidator, int]] = {}

        for idx, validator in enumerate(validators_to_run):
            task = asyncio.create_task(
                self._run_validator_async(validator, path, idx + 1, total_validators, progress_callback)
            )
            tasks.append(task)
            validator_map[task] = (validator, idx + 1)

        # Wait for all tasks with overall timeout
        # Add buffer to allow individual task timeouts to complete before overall timeout
        overall_timeout = (self._config.timeout_per_validator + 1.0) * len(validators_to_run)

        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=overall_timeout,
            )

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    validator = validators_to_run[i]
                    error_result = ValidatorResult(
                        validator_id=validator.id,
                        validator_name=validator.name,
                        error=f"Validator failed: {result!s}",
                    )
                    report.add_result(error_result)
                elif isinstance(result, ValidatorResult):
                    report.add_result(result)

        except TimeoutError:
            # Overall timeout - add timeout results for incomplete validators
            for task in tasks:
                if not task.done():
                    task.cancel()
                    validator, _ = validator_map[task]
                    timeout_result = ValidatorResult(
                        validator_id=validator.id,
                        validator_name=validator.name,
                        error="Scan timed out",
                    )
                    report.add_result(timeout_result)

        # Sort findings by severity
        self._sort_findings_by_severity(report)

        report.completed_at = datetime.now()
        return report

    def quick_scan(
        self,
        path: Path,
        progress_callback: ProgressCallback | None = None,
    ) -> SecurityReport:
        """Run a quick scan with essential validators only.

        Quick scan runs only the most critical validators for fast feedback,
        suitable for pre-commit hooks.

        Args:
            path: Path to scan.
            progress_callback: Optional progress callback.

        Returns:
            SecurityReport with findings from quick scan validators.
        """
        return self.scan(
            path,
            validators=self._config.quick_scan_validators,
            progress_callback=progress_callback,
        )

    def full_audit(
        self,
        path: Path,
        progress_callback: ProgressCallback | None = None,
    ) -> SecurityReport:
        """Run a full security audit with all validators.

        Full audit runs all registered validators for comprehensive coverage,
        suitable for PR reviews and security audits.

        Args:
            path: Path to scan.
            progress_callback: Optional progress callback.

        Returns:
            SecurityReport with findings from all validators.
        """
        return self.scan(path, validators=None, progress_callback=progress_callback)

    def _get_validators(
        self, validator_ids: list[str] | None
    ) -> list[SecurityValidator]:
        """Get validators to run based on IDs.

        Args:
            validator_ids: List of validator IDs or None for all.

        Returns:
            List of validators to run.
        """
        if validator_ids is None:
            return self._registry.get_all()

        validators: list[SecurityValidator] = []
        for vid in validator_ids:
            validator = self._registry.get(vid)
            if validator is not None:
                validators.append(validator)
        return validators

    def _run_validator(
        self,
        validator: SecurityValidator,
        path: Path,
    ) -> ValidatorResult:
        """Run a single validator.

        Args:
            validator: The validator to run.
            path: Path to scan.

        Returns:
            ValidatorResult from the validator.
        """
        start_time = time.time()
        try:
            result = validator.validate(path)
            return result
        except Exception as e:
            return ValidatorResult(
                validator_id=validator.id,
                validator_name=validator.name,
                error=f"Validator exception: {e!s}",
                scan_duration_ms=int((time.time() - start_time) * 1000),
            )

    async def _run_validator_async(
        self,
        validator: SecurityValidator,
        path: Path,
        current: int,
        total: int,
        progress_callback: Callable[[str, int, int, str], None] | None,
    ) -> ValidatorResult:
        """Run a validator asynchronously.

        Wraps the synchronous validate() call in an executor for async execution.

        Args:
            validator: The validator to run.
            path: Path to scan.
            current: Current validator index.
            total: Total validator count.
            progress_callback: Optional progress callback.

        Returns:
            ValidatorResult from the validator.
        """
        if progress_callback:
            progress_callback(validator.id, current, total, "starting")

        loop = asyncio.get_event_loop()

        try:
            result = await asyncio.wait_for(
                loop.run_in_executor(None, validator.validate, path),
                timeout=self._config.timeout_per_validator,
            )

            if progress_callback:
                status = "completed" if not result.error else "error"
                progress_callback(validator.id, current, total, status)

            return result

        except TimeoutError:
            if progress_callback:
                progress_callback(validator.id, current, total, "timeout")

            return ValidatorResult(
                validator_id=validator.id,
                validator_name=validator.name,
                error=f"Validator timed out after {self._config.timeout_per_validator}s",
                scan_duration_ms=int(self._config.timeout_per_validator * 1000),
            )

        except Exception as e:
            if progress_callback:
                progress_callback(validator.id, current, total, "error")

            return ValidatorResult(
                validator_id=validator.id,
                validator_name=validator.name,
                error=f"Validator exception: {e!s}",
            )

    def _sort_findings_by_severity(self, report: SecurityReport) -> None:
        """Sort all findings in the report by severity.

        Args:
            report: The report to sort findings in.
        """
        for result in report.results:
            result.findings.sort(
                key=lambda f: SEVERITY_ORDER.get(f.severity, 999)
            )

    def get_all_findings_sorted(
        self, report: SecurityReport
    ) -> list[SecurityFinding]:
        """Get all findings from a report sorted by severity.

        Args:
            report: The security report.

        Returns:
            List of all findings sorted by severity (critical first).
        """
        all_findings: list[SecurityFinding] = []
        for result in report.results:
            all_findings.extend(result.findings)

        all_findings.sort(key=lambda f: SEVERITY_ORDER.get(f.severity, 999))
        return all_findings

    def should_block_commit(self, report: SecurityReport) -> bool:
        """Check if findings should block a commit.

        Commits are blocked if there are any CRITICAL findings.

        Args:
            report: The security report.

        Returns:
            True if commit should be blocked.
        """
        return report.critical_findings > 0

    def should_block_merge(self, report: SecurityReport) -> bool:
        """Check if findings should block a merge/PR.

        Merges are blocked if there are CRITICAL or HIGH findings.

        Args:
            report: The security report.

        Returns:
            True if merge should be blocked.
        """
        return report.has_blockers

    def get_scan_summary(self, report: SecurityReport) -> dict[str, int | bool | float]:
        """Get a summary of scan results.

        Args:
            report: The security report.

        Returns:
            Dictionary with summary statistics.
        """
        duration_ms = report.total_duration_ms
        if report.completed_at and report.started_at:
            duration_ms = int(
                (report.completed_at - report.started_at).total_seconds() * 1000
            )

        return {
            "total_findings": report.total_findings,
            "critical": report.critical_findings,
            "high": report.high_findings,
            "medium": report.medium_findings,
            "low": report.low_findings,
            "info": report.info_findings,
            "files_scanned": report.files_scanned,
            "validators_run": len(report.results),
            "has_errors": report.has_errors,
            "should_block_commit": self.should_block_commit(report),
            "should_block_merge": self.should_block_merge(report),
            "duration_ms": duration_ms,
        }


# Global orchestrator instance with default configuration
security_orchestrator = SecurityOrchestrator(
    registry=validator_registry,
    config=ScanConfig(),
)


__all__ = [
    "SEVERITY_ORDER",
    "ProgressCallback",
    "ScanConfig",
    "SecurityOrchestrator",
    "security_orchestrator",
]
