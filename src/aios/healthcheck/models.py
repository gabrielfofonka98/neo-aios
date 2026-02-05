"""Health check models.

Defines the data structures for health check results and system health reports.
"""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel
from pydantic import Field


class HealthStatus(StrEnum):
    """Health check status.

    Attributes:
        HEALTHY: All checks passed, system operating normally.
        DEGRADED: Some non-critical issues detected.
        UNHEALTHY: Critical issues detected, system may not function properly.
        UNKNOWN: Health status could not be determined.
    """

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class CheckResult(BaseModel):
    """Result of a single health check.

    Attributes:
        name: Name of the check (e.g., 'agent_registry', 'session_persistence').
        status: Health status of this check.
        message: Human-readable description of the check result.
        details: Optional additional details about the check.
        checked_at: Timestamp when the check was performed.
    """

    name: str
    status: HealthStatus
    message: str | None = None
    details: dict[str, Any] | None = None
    checked_at: datetime = Field(default_factory=datetime.now)

    @property
    def is_healthy(self) -> bool:
        """Check if this result indicates healthy status."""
        return self.status == HealthStatus.HEALTHY


class SystemHealth(BaseModel):
    """Overall system health report.

    Aggregates multiple check results and calculates overall system status.

    Attributes:
        status: Overall system health status.
        checks: List of individual check results.
        checked_at: Timestamp when the health check was performed.
    """

    status: HealthStatus = HealthStatus.UNKNOWN
    checks: list[CheckResult] = Field(default_factory=list)
    checked_at: datetime = Field(default_factory=datetime.now)

    @property
    def is_healthy(self) -> bool:
        """Check if the system is healthy."""
        return self.status == HealthStatus.HEALTHY

    @property
    def healthy_count(self) -> int:
        """Count of healthy checks."""
        return sum(1 for c in self.checks if c.is_healthy)

    @property
    def unhealthy_count(self) -> int:
        """Count of unhealthy checks."""
        return len(self.checks) - self.healthy_count

    def add_check(self, check: CheckResult) -> None:
        """Add a check result and update overall status.

        Args:
            check: The check result to add.
        """
        self.checks.append(check)
        self._recalculate_status()

    def _recalculate_status(self) -> None:
        """Recalculate overall status based on checks.

        Status priority:
        1. UNHEALTHY if any check is unhealthy
        2. DEGRADED if any check is degraded or unknown
        3. HEALTHY if all checks are healthy
        4. UNKNOWN if no checks
        """
        if not self.checks:
            self.status = HealthStatus.UNKNOWN
            return

        statuses = [c.status for c in self.checks]

        if HealthStatus.UNHEALTHY in statuses:
            self.status = HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses or HealthStatus.UNKNOWN in statuses:
            self.status = HealthStatus.DEGRADED
        else:
            self.status = HealthStatus.HEALTHY

    def get_checks_by_status(self, status: HealthStatus) -> list[CheckResult]:
        """Get all checks with a specific status.

        Args:
            status: The status to filter by.

        Returns:
            List of checks with the specified status.
        """
        return [c for c in self.checks if c.status == status]

    def to_summary(self) -> dict[str, Any]:
        """Generate a summary of the health report.

        Returns:
            Dictionary with summary information.
        """
        return {
            "status": self.status.value,
            "total_checks": len(self.checks),
            "healthy": self.healthy_count,
            "unhealthy": self.unhealthy_count,
            "checked_at": self.checked_at.isoformat(),
            "checks": [
                {
                    "name": c.name,
                    "status": c.status.value,
                    "message": c.message,
                }
                for c in self.checks
            ],
        }
