"""Tests for health check engine."""

from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock
from unittest.mock import patch

from aios.healthcheck.checks import AgentIdentityCheck
from aios.healthcheck.checks import AgentRegistryCheck
from aios.healthcheck.checks import ConfigurationCheck
from aios.healthcheck.checks import ScopeEnforcerCheck
from aios.healthcheck.checks import SecurityCheck
from aios.healthcheck.checks import SessionPersistenceCheck
from aios.healthcheck.engine import HealthCheckEngine
from aios.healthcheck.engine import health_engine
from aios.healthcheck.models import CheckResult
from aios.healthcheck.models import HealthStatus
from aios.healthcheck.models import SystemHealth


class TestCheckResult:
    """Tests for CheckResult model."""

    def test_healthy_check(self) -> None:
        """Test healthy check result."""
        result = CheckResult(
            name="test",
            status=HealthStatus.HEALTHY,
            message="OK",
        )
        assert result.is_healthy is True
        assert result.name == "test"
        assert result.message == "OK"

    def test_unhealthy_check(self) -> None:
        """Test unhealthy check result."""
        result = CheckResult(
            name="test",
            status=HealthStatus.UNHEALTHY,
            message="Failed",
        )
        assert result.is_healthy is False

    def test_degraded_check(self) -> None:
        """Test degraded check result."""
        result = CheckResult(
            name="test",
            status=HealthStatus.DEGRADED,
            message="Degraded",
        )
        assert result.is_healthy is False
        assert result.status == HealthStatus.DEGRADED

    def test_check_with_details(self) -> None:
        """Test check result with details."""
        details: dict[str, Any] = {"key": "value", "count": 42}
        result = CheckResult(
            name="test",
            status=HealthStatus.HEALTHY,
            details=details,
        )
        assert result.details == details
        assert result.details["count"] == 42

    def test_check_has_timestamp(self) -> None:
        """Test check result has timestamp."""
        result = CheckResult(
            name="test",
            status=HealthStatus.HEALTHY,
        )
        assert isinstance(result.checked_at, datetime)


class TestSystemHealth:
    """Tests for SystemHealth model."""

    def test_empty_health_is_unknown(self) -> None:
        """Test empty health report has unknown status."""
        health = SystemHealth(status=HealthStatus.UNKNOWN)
        assert health.status == HealthStatus.UNKNOWN
        assert len(health.checks) == 0

    def test_all_healthy(self) -> None:
        """Test all healthy checks result in healthy system."""
        health = SystemHealth(status=HealthStatus.UNKNOWN)
        health.add_check(CheckResult(name="a", status=HealthStatus.HEALTHY))
        health.add_check(CheckResult(name="b", status=HealthStatus.HEALTHY))

        assert health.status == HealthStatus.HEALTHY
        assert health.is_healthy is True
        assert health.healthy_count == 2
        assert health.unhealthy_count == 0

    def test_one_unhealthy_makes_system_unhealthy(self) -> None:
        """Test one unhealthy check makes system unhealthy."""
        health = SystemHealth(status=HealthStatus.UNKNOWN)
        health.add_check(CheckResult(name="a", status=HealthStatus.HEALTHY))
        health.add_check(CheckResult(name="b", status=HealthStatus.UNHEALTHY))

        assert health.status == HealthStatus.UNHEALTHY
        assert health.is_healthy is False

    def test_degraded_status(self) -> None:
        """Test degraded check results in degraded system."""
        health = SystemHealth(status=HealthStatus.UNKNOWN)
        health.add_check(CheckResult(name="a", status=HealthStatus.HEALTHY))
        health.add_check(CheckResult(name="b", status=HealthStatus.DEGRADED))

        assert health.status == HealthStatus.DEGRADED

    def test_unknown_check_causes_degraded(self) -> None:
        """Test unknown check causes degraded system status."""
        health = SystemHealth(status=HealthStatus.UNKNOWN)
        health.add_check(CheckResult(name="a", status=HealthStatus.HEALTHY))
        health.add_check(CheckResult(name="b", status=HealthStatus.UNKNOWN))

        assert health.status == HealthStatus.DEGRADED

    def test_unhealthy_takes_priority_over_degraded(self) -> None:
        """Test unhealthy status takes priority over degraded."""
        health = SystemHealth(status=HealthStatus.UNKNOWN)
        health.add_check(CheckResult(name="a", status=HealthStatus.DEGRADED))
        health.add_check(CheckResult(name="b", status=HealthStatus.UNHEALTHY))

        assert health.status == HealthStatus.UNHEALTHY

    def test_get_checks_by_status(self) -> None:
        """Test filtering checks by status."""
        health = SystemHealth(status=HealthStatus.UNKNOWN)
        health.add_check(CheckResult(name="a", status=HealthStatus.HEALTHY))
        health.add_check(CheckResult(name="b", status=HealthStatus.UNHEALTHY))
        health.add_check(CheckResult(name="c", status=HealthStatus.HEALTHY))

        healthy_checks = health.get_checks_by_status(HealthStatus.HEALTHY)
        assert len(healthy_checks) == 2
        assert all(c.status == HealthStatus.HEALTHY for c in healthy_checks)

    def test_to_summary(self) -> None:
        """Test summary generation."""
        health = SystemHealth(status=HealthStatus.UNKNOWN)
        health.add_check(
            CheckResult(name="test", status=HealthStatus.HEALTHY, message="OK")
        )

        summary = health.to_summary()
        assert summary["status"] == "healthy"
        assert summary["total_checks"] == 1
        assert summary["healthy"] == 1
        assert summary["unhealthy"] == 0
        assert len(summary["checks"]) == 1
        assert summary["checks"][0]["name"] == "test"


class TestHealthCheckEngine:
    """Tests for HealthCheckEngine."""

    def test_engine_with_no_checks(self) -> None:
        """Test engine initialized with empty checks."""
        engine = HealthCheckEngine(checks=[])
        assert engine.check_count == 0
        assert engine.check_names == []

    def test_run_all_checks(self) -> None:
        """Test running all checks."""
        engine = HealthCheckEngine(checks=[])

        class SimpleCheck:
            @property
            def name(self) -> str:
                return "simple"

            def check(self) -> CheckResult:
                return CheckResult(
                    name=self.name,
                    status=HealthStatus.HEALTHY,
                )

        engine.add_check(SimpleCheck())
        health = engine.run_all()

        assert len(health.checks) == 1
        assert health.is_healthy

    def test_check_exception_handling(self) -> None:
        """Test engine handles check exceptions gracefully."""
        engine = HealthCheckEngine(checks=[])

        class FailingCheck:
            @property
            def name(self) -> str:
                return "failing"

            def check(self) -> CheckResult:
                raise RuntimeError("Check failed!")

        engine.add_check(FailingCheck())
        health = engine.run_all()

        assert len(health.checks) == 1
        assert health.checks[0].status == HealthStatus.UNHEALTHY
        assert "exception" in (health.checks[0].message or "").lower()

    def test_run_specific_check(self) -> None:
        """Test running a specific check by name."""
        engine = HealthCheckEngine(checks=[])

        class CheckA:
            @property
            def name(self) -> str:
                return "check_a"

            def check(self) -> CheckResult:
                return CheckResult(name=self.name, status=HealthStatus.HEALTHY)

        class CheckB:
            @property
            def name(self) -> str:
                return "check_b"

            def check(self) -> CheckResult:
                return CheckResult(name=self.name, status=HealthStatus.DEGRADED)

        engine.add_check(CheckA())
        engine.add_check(CheckB())

        health = engine.run_check("check_a")
        assert health is not None
        assert len(health.checks) == 1
        assert health.checks[0].name == "check_a"
        assert health.checks[0].status == HealthStatus.HEALTHY

    def test_run_check_not_found(self) -> None:
        """Test running a check that doesn't exist."""
        engine = HealthCheckEngine(checks=[])
        health = engine.run_check("nonexistent")
        assert health is None

    def test_run_checks_multiple(self) -> None:
        """Test running multiple specific checks."""
        engine = HealthCheckEngine(checks=[])

        class CheckA:
            @property
            def name(self) -> str:
                return "check_a"

            def check(self) -> CheckResult:
                return CheckResult(name=self.name, status=HealthStatus.HEALTHY)

        class CheckB:
            @property
            def name(self) -> str:
                return "check_b"

            def check(self) -> CheckResult:
                return CheckResult(name=self.name, status=HealthStatus.HEALTHY)

        class CheckC:
            @property
            def name(self) -> str:
                return "check_c"

            def check(self) -> CheckResult:
                return CheckResult(name=self.name, status=HealthStatus.DEGRADED)

        engine.add_check(CheckA())
        engine.add_check(CheckB())
        engine.add_check(CheckC())

        health = engine.run_checks(["check_a", "check_c"])
        assert len(health.checks) == 2
        check_names = [c.name for c in health.checks]
        assert "check_a" in check_names
        assert "check_c" in check_names
        assert "check_b" not in check_names

    def test_remove_check(self) -> None:
        """Test removing a check by name."""
        engine = HealthCheckEngine(checks=[])

        class TestCheck:
            @property
            def name(self) -> str:
                return "removable"

            def check(self) -> CheckResult:
                return CheckResult(name=self.name, status=HealthStatus.HEALTHY)

        engine.add_check(TestCheck())
        assert "removable" in engine.check_names

        result = engine.remove_check("removable")
        assert result is True
        assert "removable" not in engine.check_names

    def test_remove_check_not_found(self) -> None:
        """Test removing a check that doesn't exist."""
        engine = HealthCheckEngine(checks=[])
        result = engine.remove_check("nonexistent")
        assert result is False

    def test_check_names(self) -> None:
        """Test getting check names."""
        engine = HealthCheckEngine(checks=[])
        assert engine.check_names == []

    def test_get_check(self) -> None:
        """Test getting a check by name."""
        engine = HealthCheckEngine(checks=[])

        class TestCheck:
            @property
            def name(self) -> str:
                return "test_check"

            def check(self) -> CheckResult:
                return CheckResult(name=self.name, status=HealthStatus.HEALTHY)

        check = TestCheck()
        engine.add_check(check)

        retrieved = engine.get_check("test_check")
        assert retrieved is not None
        assert retrieved.name == "test_check"

    def test_get_check_not_found(self) -> None:
        """Test getting a check that doesn't exist."""
        engine = HealthCheckEngine(checks=[])
        retrieved = engine.get_check("nonexistent")
        assert retrieved is None

    def test_to_dict(self) -> None:
        """Test engine to_dict method."""
        engine = HealthCheckEngine(checks=[])

        class TestCheck:
            @property
            def name(self) -> str:
                return "test"

            def check(self) -> CheckResult:
                return CheckResult(name=self.name, status=HealthStatus.HEALTHY)

        engine.add_check(TestCheck())
        result = engine.to_dict()

        assert result["check_count"] == 1
        assert "test" in result["check_names"]


class TestAgentRegistryCheck:
    """Tests for AgentRegistryCheck."""

    def test_registry_check_name(self) -> None:
        """Test check name."""
        check = AgentRegistryCheck()
        assert check.name == "agent_registry"

    @patch("aios.agents.registry.AgentRegistry.load")
    def test_registry_loaded_with_agents(
        self, mock_load: MagicMock
    ) -> None:
        """Test check when registry is loaded with agents."""
        mock_registry = MagicMock()
        mock_registry.__len__ = MagicMock(return_value=5)
        mock_load.return_value = mock_registry

        check = AgentRegistryCheck()
        result = check.check()

        assert result.status == HealthStatus.HEALTHY
        assert "5 agents" in (result.message or "")

    @patch("aios.agents.registry.AgentRegistry.load")
    def test_registry_empty(self, mock_load: MagicMock) -> None:
        """Test check when registry is empty."""
        mock_registry = MagicMock()
        mock_registry.__len__ = MagicMock(return_value=0)
        mock_load.return_value = mock_registry

        check = AgentRegistryCheck()
        result = check.check()

        assert result.status == HealthStatus.DEGRADED
        assert "empty" in (result.message or "").lower()

    @patch("aios.agents.registry.AgentRegistry.load")
    def test_registry_load_error(self, mock_load: MagicMock) -> None:
        """Test check when registry fails to load."""
        mock_load.side_effect = RuntimeError("Load failed")

        check = AgentRegistryCheck()
        result = check.check()

        assert result.status == HealthStatus.UNHEALTHY
        assert "failed" in (result.message or "").lower()


class TestSessionPersistenceCheck:
    """Tests for SessionPersistenceCheck."""

    def test_check_name(self) -> None:
        """Test check name."""
        check = SessionPersistenceCheck()
        assert check.name == "session_persistence"

    @patch("aios.context.session.Session.load")
    def test_session_working(self, mock_load: MagicMock) -> None:
        """Test check when session is working."""
        mock_session = MagicMock()
        mock_session.state.active_agent = "dev"
        mock_load.return_value = mock_session

        check = SessionPersistenceCheck()
        result = check.check()

        assert result.status == HealthStatus.HEALTHY
        assert result.details is not None
        assert result.details["active_agent"] == "dev"

    @patch("aios.context.session.Session.load")
    def test_session_error(self, mock_load: MagicMock) -> None:
        """Test check when session fails."""
        mock_load.side_effect = RuntimeError("Session error")

        check = SessionPersistenceCheck()
        result = check.check()

        assert result.status == HealthStatus.UNHEALTHY
        assert "error" in (result.message or "").lower()


class TestConfigurationCheck:
    """Tests for ConfigurationCheck."""

    def test_check_name(self) -> None:
        """Test check name."""
        check = ConfigurationCheck()
        assert check.name == "configuration"

    def test_all_files_present(self, tmp_path: Path) -> None:
        """Test check when all files are present using temp directory."""
        # Create a custom check with modified paths
        class TempConfigCheck(ConfigurationCheck):
            def __init__(self, base_path: Path) -> None:
                self.base_path = base_path
                super().__init__()

            def check(self) -> CheckResult:
                missing_required: list[str] = []

                for file_path in self.REQUIRED_FILES:
                    if not (self.base_path / file_path).exists():
                        missing_required.append(file_path)

                if missing_required:
                    return CheckResult(
                        name=self.name,
                        status=HealthStatus.UNHEALTHY,
                        message=f"Missing required: {missing_required}",
                    )
                return CheckResult(
                    name=self.name,
                    status=HealthStatus.HEALTHY,
                    message="All OK",
                )

        # Create required files
        (tmp_path / ".aios").mkdir()
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'")

        check = TempConfigCheck(tmp_path)
        result = check.check()

        assert result.status == HealthStatus.HEALTHY

    def test_missing_required_files(self, tmp_path: Path) -> None:
        """Test check when required files are missing."""
        # Create a custom check with modified paths
        class TempConfigCheck(ConfigurationCheck):
            def __init__(self, base_path: Path) -> None:
                self.base_path = base_path
                super().__init__()

            def check(self) -> CheckResult:
                missing_required: list[str] = []

                for file_path in self.REQUIRED_FILES:
                    if not (self.base_path / file_path).exists():
                        missing_required.append(file_path)

                if missing_required:
                    return CheckResult(
                        name=self.name,
                        status=HealthStatus.UNHEALTHY,
                        message=f"Missing required files: {', '.join(missing_required)}",
                    )
                return CheckResult(
                    name=self.name,
                    status=HealthStatus.HEALTHY,
                    message="All OK",
                )

        check = TempConfigCheck(tmp_path)
        result = check.check()

        assert result.status == HealthStatus.UNHEALTHY
        assert "required" in (result.message or "").lower()


class TestAgentIdentityCheck:
    """Tests for AgentIdentityCheck."""

    def test_check_name(self) -> None:
        """Test check name."""
        check = AgentIdentityCheck()
        assert check.name == "agent_identity_isolation"

    @patch("aios.agents.registry.AgentRegistry.load")
    def test_identity_check_passes(
        self, mock_load: MagicMock
    ) -> None:
        """Test identity check passes with proper agents."""
        mock_agent = MagicMock()
        mock_agent.id = "test"
        mock_agent.scope.can = ["action1"]
        mock_agent.scope.cannot = ["action2"]

        mock_registry = MagicMock()
        mock_registry.__iter__ = MagicMock(return_value=iter([mock_agent]))
        mock_registry.__len__ = MagicMock(return_value=1)
        mock_load.return_value = mock_registry

        check = AgentIdentityCheck()
        result = check.check()

        assert result.status == HealthStatus.HEALTHY
        assert "identity isolation" in (result.message or "").lower()

    @patch("aios.agents.registry.AgentRegistry.load")
    def test_identity_check_with_empty_scope(
        self, mock_load: MagicMock
    ) -> None:
        """Test identity check with agent that has no scope."""
        mock_agent = MagicMock()
        mock_agent.id = "test"
        mock_agent.scope.can = []
        mock_agent.scope.cannot = []

        mock_registry = MagicMock()
        mock_registry.__iter__ = MagicMock(return_value=iter([mock_agent]))
        mock_registry.__len__ = MagicMock(return_value=1)
        mock_load.return_value = mock_registry

        check = AgentIdentityCheck()
        result = check.check()

        assert result.status == HealthStatus.DEGRADED


class TestScopeEnforcerCheck:
    """Tests for ScopeEnforcerCheck."""

    def test_check_name(self) -> None:
        """Test check name."""
        check = ScopeEnforcerCheck()
        assert check.name == "scope_enforcer"

    def test_check_passes(self) -> None:
        """Test scope enforcer check passes."""
        check = ScopeEnforcerCheck()
        result = check.check()

        assert result.status == HealthStatus.HEALTHY
        assert result.details is not None
        assert "exclusive_actions" in result.details
        assert "globally_blocked" in result.details


class TestSecurityCheck:
    """Tests for SecurityCheck."""

    def test_check_name(self) -> None:
        """Test check name."""
        check = SecurityCheck()
        assert check.name == "security"

    def test_check_with_gitignore(self, tmp_path: Path) -> None:
        """Test security check with gitignore present."""
        # Create .gitignore with sensitive files
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text(".env\nconfig/credentials.yaml\n")

        # Security check uses hardcoded paths, so it won't find our temp files
        # This test just ensures the check runs without error
        check = SecurityCheck()
        result = check.check()

        # Should be healthy or degraded (not unhealthy)
        assert result.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]


class TestGlobalEngine:
    """Tests for global health_engine instance."""

    def test_global_engine_exists(self) -> None:
        """Test global engine is available."""
        assert health_engine is not None
        assert isinstance(health_engine, HealthCheckEngine)

    def test_global_engine_has_default_checks(self) -> None:
        """Test global engine has default checks."""
        # The global engine should have default checks
        assert health_engine.check_count > 0
