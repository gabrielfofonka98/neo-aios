"""Pre-commit gate for quality checks.

This module provides the PreCommitGate class that runs quality checks
before commits, including linting, type checking, testing, and security scans.

Example:
    >>> from pathlib import Path
    >>> from aios.quality.precommit import precommit_gate
    >>> result = precommit_gate.run_checks([Path("src/aios/module.py")])
    >>> if result.blocked:
    ...     print("Commit blocked!")
"""

from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import TYPE_CHECKING

from aios.quality.config import CheckResult
from aios.quality.config import CheckStatus
from aios.quality.config import GateConfig
from aios.quality.config import GateResult
from aios.quality.config import default_gate_config

if TYPE_CHECKING:
    from aios.security.models import SecurityReport


class PreCommitGate:
    """Pre-commit quality gate that runs all checks.

    This class coordinates running ruff, mypy, pytest, and security
    scans on staged files before commit, blocking if critical issues
    are found.

    Attributes:
        config: The gate configuration.

    Example:
        >>> from aios.quality.precommit import PreCommitGate
        >>> gate = PreCommitGate()
        >>> result = gate.run_checks([Path("src/module.py")])
        >>> result.passed
        True
    """

    def __init__(self, config: GateConfig | None = None) -> None:
        """Initialize the pre-commit gate.

        Args:
            config: Optional gate configuration. Uses default if not provided.
        """
        self._config = config or default_gate_config

    @property
    def config(self) -> GateConfig:
        """Get the gate configuration."""
        return self._config

    def run_checks(
        self,
        files: list[Path],
        *,
        run_ruff: bool = True,
        run_mypy: bool = True,
        run_tests: bool = True,
        run_security: bool = True,
    ) -> GateResult:
        """Run all pre-commit checks on the given files.

        Args:
            files: List of file paths to check.
            run_ruff: Whether to run ruff lint check.
            run_mypy: Whether to run mypy type check.
            run_tests: Whether to run pytest.
            run_security: Whether to run security scan.

        Returns:
            GateResult with overall pass/fail and individual check results.
        """
        start_time = time.time()
        checks: list[CheckResult] = []
        warnings: list[str] = []
        errors: list[str] = []

        # Filter out excluded files
        filtered_files = self._filter_files(files)
        if not filtered_files:
            return GateResult(
                passed=True,
                checks=[
                    CheckResult(
                        name="filter",
                        status=CheckStatus.SKIPPED,
                        message="No files to check after filtering",
                    )
                ],
                blocked=False,
            )

        # Get only Python files for Python-specific checks
        python_files = [f for f in filtered_files if f.suffix == ".py"]

        # Run checks
        if run_ruff and python_files:
            ruff_result = self.run_ruff(python_files)
            checks.append(ruff_result)
            if ruff_result.status == CheckStatus.FAILED:
                errors.append(f"Ruff: {ruff_result.message}")

        if run_mypy and python_files:
            mypy_result = self.run_mypy(python_files)
            checks.append(mypy_result)
            if mypy_result.status == CheckStatus.FAILED:
                errors.append(f"Mypy: {mypy_result.message}")

        if run_tests and python_files:
            test_result = self.run_tests(python_files)
            checks.append(test_result)
            if test_result.status == CheckStatus.FAILED:
                errors.append(f"Pytest: {test_result.message}")

        if run_security and filtered_files:
            security_result = self.run_security_scan(filtered_files)
            checks.append(security_result)
            if security_result.status == CheckStatus.FAILED:
                errors.append(f"Security: {security_result.message}")
            elif security_result.status == CheckStatus.WARNING:
                warnings.append(f"Security: {security_result.message}")

        # Determine overall result
        blocked = self._should_block(checks)
        passed = not blocked

        total_duration_ms = int((time.time() - start_time) * 1000)

        return GateResult(
            passed=passed,
            checks=checks,
            blocked=blocked,
            warnings=warnings,
            errors=errors,
            total_duration_ms=total_duration_ms,
        )

    def run_ruff(self, files: list[Path]) -> CheckResult:
        """Run ruff lint check on files.

        Args:
            files: List of Python files to check.

        Returns:
            CheckResult with pass/fail status.
        """
        start_time = time.time()

        if not files:
            return CheckResult(
                name="ruff",
                status=CheckStatus.SKIPPED,
                message="No Python files to check",
            )

        try:
            # Run ruff check
            file_paths = [str(f) for f in files]
            result = subprocess.run(
                ["ruff", "check", "--output-format=concise", *file_paths],
                capture_output=True,
                text=True,
                timeout=self._config.timeout_seconds,
                check=False,
            )

            duration_ms = int((time.time() - start_time) * 1000)

            if result.returncode == 0:
                return CheckResult(
                    name="ruff",
                    status=CheckStatus.PASSED,
                    message="No lint errors",
                    duration_ms=duration_ms,
                    files_checked=len(files),
                )

            # Parse output to count errors
            output = result.stdout or result.stderr
            error_count = output.count("\n") if output else 1

            return CheckResult(
                name="ruff",
                status=CheckStatus.FAILED,
                message=f"Found {error_count} lint error(s)",
                details=output.strip() if output else None,
                duration_ms=duration_ms,
                files_checked=len(files),
            )

        except subprocess.TimeoutExpired:
            return CheckResult(
                name="ruff",
                status=CheckStatus.ERROR,
                message=f"Timed out after {self._config.timeout_seconds}s",
            )
        except FileNotFoundError:
            return CheckResult(
                name="ruff",
                status=CheckStatus.ERROR,
                message="ruff not found. Install with: pip install ruff",
            )
        except Exception as e:
            return CheckResult(
                name="ruff",
                status=CheckStatus.ERROR,
                message=f"Error running ruff: {e}",
            )

    def run_mypy(self, files: list[Path]) -> CheckResult:
        """Run mypy type check on files.

        Args:
            files: List of Python files to check.

        Returns:
            CheckResult with pass/fail status.
        """
        start_time = time.time()

        if not files:
            return CheckResult(
                name="mypy",
                status=CheckStatus.SKIPPED,
                message="No Python files to check",
            )

        try:
            # Run mypy with strict mode
            file_paths = [str(f) for f in files]
            result = subprocess.run(
                ["mypy", "--strict", "--no-error-summary", *file_paths],
                capture_output=True,
                text=True,
                timeout=self._config.timeout_seconds,
                check=False,
            )

            duration_ms = int((time.time() - start_time) * 1000)

            if result.returncode == 0:
                return CheckResult(
                    name="mypy",
                    status=CheckStatus.PASSED,
                    message="No type errors",
                    duration_ms=duration_ms,
                    files_checked=len(files),
                )

            # Parse output to count errors
            output = result.stdout or result.stderr
            error_lines = [
                line for line in (output or "").split("\n") if ": error:" in line
            ]

            return CheckResult(
                name="mypy",
                status=CheckStatus.FAILED,
                message=f"Found {len(error_lines)} type error(s)",
                details=output.strip() if output else None,
                duration_ms=duration_ms,
                files_checked=len(files),
            )

        except subprocess.TimeoutExpired:
            return CheckResult(
                name="mypy",
                status=CheckStatus.ERROR,
                message=f"Timed out after {self._config.timeout_seconds}s",
            )
        except FileNotFoundError:
            return CheckResult(
                name="mypy",
                status=CheckStatus.ERROR,
                message="mypy not found. Install with: pip install mypy",
            )
        except Exception as e:
            return CheckResult(
                name="mypy",
                status=CheckStatus.ERROR,
                message=f"Error running mypy: {e}",
            )

    def run_tests(self, files: list[Path]) -> CheckResult:  # noqa: PLR0911
        """Run pytest on related test files.

        Only runs fast tests by default (tests not marked as 'slow').

        Args:
            files: List of Python files that were modified.

        Returns:
            CheckResult with pass/fail status.
        """
        start_time = time.time()

        if not files:
            return CheckResult(
                name="pytest",
                status=CheckStatus.SKIPPED,
                message="No Python files to test",
            )

        try:
            # Build pytest command
            cmd = ["pytest", "-x", "--tb=short", "-q"]

            if self._config.run_fast_tests_only:
                cmd.extend(["-m", "not slow"])

            # Add timeout
            cmd.extend(["--timeout", str(int(self._config.timeout_seconds))])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self._config.timeout_seconds * 2,  # Allow extra time
                check=False,
            )

            duration_ms = int((time.time() - start_time) * 1000)

            if result.returncode == 0:
                return CheckResult(
                    name="pytest",
                    status=CheckStatus.PASSED,
                    message="All tests passed",
                    duration_ms=duration_ms,
                    files_checked=len(files),
                )

            # Check if it's just "no tests collected"
            output = result.stdout or result.stderr or ""
            if "no tests ran" in output.lower() or "collected 0 items" in output.lower():
                return CheckResult(
                    name="pytest",
                    status=CheckStatus.SKIPPED,
                    message="No tests found",
                    duration_ms=duration_ms,
                )

            # Parse failures
            failed_count = output.count(" FAILED")
            if failed_count == 0:
                failed_count = 1  # At least one failure

            return CheckResult(
                name="pytest",
                status=CheckStatus.FAILED,
                message=f"{failed_count} test(s) failed",
                details=output.strip() if output else None,
                duration_ms=duration_ms,
                files_checked=len(files),
            )

        except subprocess.TimeoutExpired:
            return CheckResult(
                name="pytest",
                status=CheckStatus.ERROR,
                message=f"Timed out after {self._config.timeout_seconds * 2}s",
            )
        except FileNotFoundError:
            return CheckResult(
                name="pytest",
                status=CheckStatus.ERROR,
                message="pytest not found. Install with: pip install pytest",
            )
        except Exception as e:
            return CheckResult(
                name="pytest",
                status=CheckStatus.ERROR,
                message=f"Error running pytest: {e}",
            )

    def run_security_scan(self, files: list[Path]) -> CheckResult:
        """Run security quick scan on files.

        Uses the SecurityOrchestrator's quick_scan for fast feedback.

        Args:
            files: List of files to scan.

        Returns:
            CheckResult with pass/fail status.
        """
        start_time = time.time()

        if not files:
            return CheckResult(
                name="security",
                status=CheckStatus.SKIPPED,
                message="No files to scan",
            )

        try:
            # Import here to avoid circular imports
            from aios.security.orchestrator import security_orchestrator

            # Run quick scan on each file's parent directory (or file directly)
            all_findings_critical = 0
            all_findings_high = 0

            for file_path in files:
                report: SecurityReport = security_orchestrator.quick_scan(file_path)
                all_findings_critical += report.critical_findings
                all_findings_high += report.high_findings

            duration_ms = int((time.time() - start_time) * 1000)

            if all_findings_critical > 0:
                return CheckResult(
                    name="security",
                    status=CheckStatus.FAILED,
                    message=f"Found {all_findings_critical} CRITICAL security issue(s)",
                    duration_ms=duration_ms,
                    files_checked=len(files),
                )

            if all_findings_high > 0 and self._config.warn_on_high:
                return CheckResult(
                    name="security",
                    status=CheckStatus.WARNING,
                    message=f"Found {all_findings_high} HIGH security issue(s)",
                    duration_ms=duration_ms,
                    files_checked=len(files),
                )

            return CheckResult(
                name="security",
                status=CheckStatus.PASSED,
                message="No critical security issues",
                duration_ms=duration_ms,
                files_checked=len(files),
            )

        except ImportError:
            return CheckResult(
                name="security",
                status=CheckStatus.ERROR,
                message="Security module not available",
            )
        except Exception as e:
            return CheckResult(
                name="security",
                status=CheckStatus.ERROR,
                message=f"Error running security scan: {e}",
            )

    def _filter_files(self, files: list[Path]) -> list[Path]:
        """Filter out excluded files.

        Args:
            files: List of files to filter.

        Returns:
            List of files that should be checked.
        """
        filtered: list[Path] = []
        for file_path in files:
            if not self._config.should_exclude(str(file_path)):
                filtered.append(file_path)
        return filtered

    def _should_block(self, checks: list[CheckResult]) -> bool:
        """Determine if checks should block the commit.

        Args:
            checks: List of check results.

        Returns:
            True if commit should be blocked.
        """
        for check in checks:
            if check.status != CheckStatus.FAILED:
                continue

            if check.name == "ruff" and self._config.block_on_ruff_error:
                return True
            if check.name == "mypy" and self._config.block_on_mypy_error:
                return True
            if check.name == "pytest" and self._config.block_on_test_failure:
                return True
            if check.name == "security" and self._config.block_on_critical:
                return True

        return False


# Global pre-commit gate instance
precommit_gate = PreCommitGate()


def run_precommit_hook(files: list[str] | None = None) -> int:
    """Run pre-commit hook and return exit code.

    This function is designed to be called from a pre-commit hook script.

    Args:
        files: Optional list of file paths. If None, gets staged files from git.

    Returns:
        0 if checks passed, 1 if blocked.
    """
    # Get files to check
    if files is None:
        files = _get_staged_files()

    if not files:
        print("No files to check.")
        return 0

    file_paths = [Path(f) for f in files]
    result = precommit_gate.run_checks(file_paths)

    # Print summary
    print(result.summary)

    # Print details for failures
    for check in result.checks:
        if check.status == CheckStatus.FAILED:
            print(f"\n{check.name}: {check.message}")
            if check.details:
                print(check.details[:500])  # Limit output

    if result.warnings:
        print("\nWarnings:")
        for warning in result.warnings:
            print(f"  - {warning}")

    return 1 if result.blocked else 0


def _get_staged_files() -> list[str]:
    """Get list of staged files from git.

    Returns:
        List of staged file paths.
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            capture_output=True,
            text=True,
            check=True,
        )
        return [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []


__all__ = [
    "PreCommitGate",
    "precommit_gate",
    "run_precommit_hook",
]
