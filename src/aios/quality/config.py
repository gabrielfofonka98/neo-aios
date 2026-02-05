"""Quality gate configuration.

This module provides configuration classes for quality gates,
defining thresholds and behaviors for pre-commit and CI checks.

Example:
    >>> from aios.quality.config import GateConfig
    >>> config = GateConfig()
    >>> config.block_on_critical
    True
"""

from dataclasses import dataclass
from dataclasses import field
from enum import Enum


class CheckStatus(Enum):
    """Result status of a quality check.

    Attributes:
        PASSED: Check passed with no issues.
        WARNING: Check passed with warnings (non-blocking).
        FAILED: Check failed (blocking).
        SKIPPED: Check was skipped.
        ERROR: Check encountered an error during execution.
    """

    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass(frozen=True)
class CheckResult:
    """Result of a single quality check.

    Attributes:
        name: Name of the check (e.g., "ruff", "mypy").
        status: The check status.
        message: Human-readable result message.
        details: Optional detailed output from the check.
        duration_ms: How long the check took in milliseconds.
        files_checked: Number of files processed.
    """

    name: str
    status: CheckStatus
    message: str
    details: str | None = None
    duration_ms: int = 0
    files_checked: int = 0


@dataclass(frozen=True)
class GateResult:
    """Result of running all quality gate checks.

    Attributes:
        passed: Whether the gate passed overall.
        checks: List of individual check results.
        blocked: Whether the commit should be blocked.
        warnings: List of warning messages.
        errors: List of error messages.
        total_duration_ms: Total time for all checks.
    """

    passed: bool
    checks: list[CheckResult] = field(default_factory=list)
    blocked: bool = False
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    total_duration_ms: int = 0

    @property
    def summary(self) -> str:
        """Generate a human-readable summary."""
        passed_count = sum(1 for c in self.checks if c.status == CheckStatus.PASSED)
        failed_count = sum(1 for c in self.checks if c.status == CheckStatus.FAILED)
        warning_count = sum(1 for c in self.checks if c.status == CheckStatus.WARNING)

        status = "PASSED" if self.passed else "FAILED"
        return (
            f"Gate {status}: {passed_count} passed, {failed_count} failed, "
            f"{warning_count} warnings ({self.total_duration_ms}ms)"
        )


@dataclass
class GateConfig:
    """Configuration for quality gates.

    Attributes:
        block_on_critical: Block commit on CRITICAL security findings.
        block_on_ruff_error: Block commit on ruff lint errors.
        block_on_mypy_error: Block commit on mypy type errors.
        block_on_test_failure: Block commit on test failures.
        warn_on_high: Show warning for HIGH severity findings.
        run_fast_tests_only: Only run tests marked as 'fast'.
        timeout_seconds: Timeout for each check in seconds.
        max_parallel_checks: Maximum concurrent checks.
        excluded_paths: Paths to exclude from checks.
    """

    # Blocking rules
    block_on_critical: bool = True
    block_on_ruff_error: bool = True
    block_on_mypy_error: bool = True
    block_on_test_failure: bool = True

    # Warning rules
    warn_on_high: bool = True

    # Performance
    run_fast_tests_only: bool = True
    timeout_seconds: float = 30.0
    max_parallel_checks: int = 4

    # Exclusions
    excluded_paths: list[str] = field(
        default_factory=lambda: [
            "__pycache__",
            ".git",
            ".venv",
            "node_modules",
            "*.pyc",
            ".mypy_cache",
            ".ruff_cache",
            ".pytest_cache",
        ]
    )

    def should_exclude(self, path: str) -> bool:
        """Check if a path should be excluded from checks.

        Args:
            path: The path to check.

        Returns:
            True if path should be excluded.
        """
        import fnmatch

        for pattern in self.excluded_paths:
            if fnmatch.fnmatch(path, pattern) or pattern in path:
                return True
        return False


# Default configuration
default_gate_config = GateConfig()


__all__ = [
    "CheckResult",
    "CheckStatus",
    "GateConfig",
    "GateResult",
    "default_gate_config",
]
