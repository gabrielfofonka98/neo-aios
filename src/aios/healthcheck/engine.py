"""Health check engine.

Provides the main engine for running health checks and producing
system health reports.
"""

from typing import Any

from aios.healthcheck.checks import DEFAULT_CHECKS
from aios.healthcheck.checks import HealthCheck
from aios.healthcheck.models import CheckResult
from aios.healthcheck.models import HealthStatus
from aios.healthcheck.models import SystemHealth


class HealthCheckEngine:
    """Runs health checks and produces system health report.

    The engine manages a collection of health checks and provides
    methods to run all checks or specific checks by name.

    Example:
        >>> engine = HealthCheckEngine()
        >>> health = engine.run_all()
        >>> print(health.status)
        HealthStatus.HEALTHY
        >>> print(health.healthy_count)
        6

    Attributes:
        _checks: List of registered health checks.
    """

    def __init__(self, checks: list[HealthCheck] | None = None) -> None:
        """Initialize the health check engine.

        Args:
            checks: Optional list of checks. If None, uses DEFAULT_CHECKS.
        """
        self._checks: list[HealthCheck] = (
            list(checks) if checks is not None else list(DEFAULT_CHECKS)
        )

    def add_check(self, check: HealthCheck) -> None:
        """Add a health check to the engine.

        Args:
            check: The health check to add.
        """
        self._checks.append(check)

    def remove_check(self, name: str) -> bool:
        """Remove a health check by name.

        Args:
            name: Name of the check to remove.

        Returns:
            True if check was found and removed, False otherwise.
        """
        for i, check in enumerate(self._checks):
            if check.name == name:
                self._checks.pop(i)
                return True
        return False

    def run_all(self) -> SystemHealth:
        """Run all health checks and return system health.

        Each check is run independently. If a check raises an exception,
        it's caught and converted to an UNHEALTHY result.

        Returns:
            SystemHealth with aggregated results from all checks.
        """
        health = SystemHealth(status=HealthStatus.UNKNOWN)

        for check in self._checks:
            try:
                result = check.check()
            except Exception as e:
                result = CheckResult(
                    name=check.name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Check raised exception: {e!s}",
                )

            health.add_check(result)

        return health

    def run_check(self, name: str) -> SystemHealth | None:
        """Run a specific health check by name.

        Args:
            name: Name of the check to run.

        Returns:
            SystemHealth with the single check result, or None if not found.
        """
        for check in self._checks:
            if check.name == name:
                health = SystemHealth(status=HealthStatus.UNKNOWN)
                try:
                    result = check.check()
                except Exception as e:
                    result = CheckResult(
                        name=check.name,
                        status=HealthStatus.UNHEALTHY,
                        message=f"Check raised exception: {e!s}",
                    )
                health.add_check(result)
                return health
        return None

    def run_checks(self, names: list[str]) -> SystemHealth:
        """Run specific health checks by name.

        Args:
            names: List of check names to run.

        Returns:
            SystemHealth with results from requested checks.
        """
        health = SystemHealth(status=HealthStatus.UNKNOWN)

        for check in self._checks:
            if check.name in names:
                try:
                    result = check.check()
                except Exception as e:
                    result = CheckResult(
                        name=check.name,
                        status=HealthStatus.UNHEALTHY,
                        message=f"Check raised exception: {e!s}",
                    )
                health.add_check(result)

        return health

    @property
    def check_names(self) -> list[str]:
        """Get list of registered check names.

        Returns:
            List of check name strings.
        """
        return [c.name for c in self._checks]

    @property
    def check_count(self) -> int:
        """Get number of registered checks.

        Returns:
            Number of checks.
        """
        return len(self._checks)

    def get_check(self, name: str) -> HealthCheck | None:
        """Get a health check by name.

        Args:
            name: Name of the check.

        Returns:
            The HealthCheck if found, None otherwise.
        """
        for check in self._checks:
            if check.name == name:
                return check
        return None

    def to_dict(self) -> dict[str, Any]:
        """Get engine status as dictionary.

        Returns:
            Dictionary with engine information.
        """
        return {
            "check_count": self.check_count,
            "check_names": self.check_names,
        }


# Global engine instance
health_engine = HealthCheckEngine()
