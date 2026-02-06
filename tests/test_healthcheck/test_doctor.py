"""Tests for DoctorEngine."""

from aios.healthcheck.doctor import DoctorEngine
from aios.healthcheck.doctor import DoctorResult
from aios.healthcheck.models import CheckResult
from aios.healthcheck.models import HealthStatus


class TestDoctorResult:
    def test_all_healthy_when_empty(self) -> None:
        result = DoctorResult()
        assert result.all_healthy

    def test_all_healthy_with_healthy_checks(self) -> None:
        result = DoctorResult(
            check_results=[
                CheckResult(name="a", status=HealthStatus.HEALTHY),
                CheckResult(name="b", status=HealthStatus.HEALTHY),
            ]
        )
        assert result.all_healthy

    def test_not_all_healthy(self) -> None:
        result = DoctorResult(
            check_results=[
                CheckResult(name="a", status=HealthStatus.HEALTHY),
                CheckResult(name="b", status=HealthStatus.UNHEALTHY),
            ]
        )
        assert not result.all_healthy

    def test_summary(self) -> None:
        result = DoctorResult(
            check_results=[
                CheckResult(name="a", status=HealthStatus.HEALTHY),
            ],
            fixes_applied=["x"],
        )
        assert "1/1" in result.summary
        assert "1 fixes" in result.summary


class TestDoctorEngine:
    def test_list_checks(self) -> None:
        engine = DoctorEngine()
        names = engine.list_checks()
        assert isinstance(names, list)
        assert len(names) > 0

    def test_run_returns_result(self) -> None:
        engine = DoctorEngine()
        result = engine.run()
        assert isinstance(result, DoctorResult)
        assert len(result.check_results) > 0
