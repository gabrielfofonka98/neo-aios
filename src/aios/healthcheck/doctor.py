"""Doctor engine with health check + auto-fix capabilities."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from typing import TYPE_CHECKING

from aios.healthcheck.engine import HealthCheckEngine
from aios.healthcheck.models import CheckResult
from aios.healthcheck.models import HealthStatus

if TYPE_CHECKING:
    from aios.healthcheck.fixes import Fix


@dataclass
class DoctorResult:
    """Result of a doctor run."""

    check_results: list[CheckResult] = field(default_factory=list)
    fixes_applied: list[str] = field(default_factory=list)
    fixes_failed: list[str] = field(default_factory=list)

    @property
    def all_healthy(self) -> bool:
        return all(r.status == HealthStatus.HEALTHY for r in self.check_results)

    @property
    def summary(self) -> str:
        total = len(self.check_results)
        healthy = sum(1 for r in self.check_results if r.status == HealthStatus.HEALTHY)
        return f"{healthy}/{total} checks passed, {len(self.fixes_applied)} fixes applied"


class DoctorEngine:
    """Runs health checks and optionally applies fixes."""

    def __init__(self) -> None:
        self._engine = HealthCheckEngine()
        self._fixes: dict[str, Fix] = {}

    def register_fix(self, check_name: str, fix: Fix) -> None:
        self._fixes[check_name] = fix

    def run(self, auto_fix: bool = False) -> DoctorResult:
        health = self._engine.run_all()
        result = DoctorResult(check_results=list(health.checks))

        if auto_fix:
            for check_result in health.checks:
                if check_result.status != HealthStatus.HEALTHY and check_result.name in self._fixes:
                        fix = self._fixes[check_result.name]
                        try:
                            fix.apply()
                            result.fixes_applied.append(check_result.name)
                        except Exception:
                            result.fixes_failed.append(check_result.name)

        return result

    def list_checks(self) -> list[str]:
        return self._engine.check_names

    @property
    def engine(self) -> HealthCheckEngine:
        return self._engine
