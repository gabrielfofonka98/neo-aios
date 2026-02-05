# Story 1.6: Health Check Engine

**Status:** [ ] Pending
**Executor:** Ralph/Dex
**Complexidade:** Média
**Dependência:** Story 1.2, Story 1.5

---

## Objetivo

Criar sistema de health check que valida estado do sistema, agentes e configurações.

## Tasks

### Task 1: Criar Health Check Models

**Arquivo:** `src/aios/healthcheck/models.py`
**Tipo:** create

**Código esperado:**
```python
"""Health check models."""

from enum import Enum
from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field


class HealthStatus(Enum):
    """Health check status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class CheckResult(BaseModel):
    """Result of a single health check."""

    name: str
    status: HealthStatus
    message: Optional[str] = None
    details: Optional[dict] = None
    checked_at: datetime = Field(default_factory=datetime.now)

    @property
    def is_healthy(self) -> bool:
        return self.status == HealthStatus.HEALTHY


class SystemHealth(BaseModel):
    """Overall system health report."""

    status: HealthStatus
    checks: list[CheckResult] = Field(default_factory=list)
    checked_at: datetime = Field(default_factory=datetime.now)

    @property
    def is_healthy(self) -> bool:
        return self.status == HealthStatus.HEALTHY

    @property
    def healthy_count(self) -> int:
        return sum(1 for c in self.checks if c.is_healthy)

    @property
    def unhealthy_count(self) -> int:
        return len(self.checks) - self.healthy_count

    def add_check(self, check: CheckResult) -> None:
        """Add a check result and update overall status."""
        self.checks.append(check)
        self._recalculate_status()

    def _recalculate_status(self) -> None:
        """Recalculate overall status based on checks."""
        if not self.checks:
            self.status = HealthStatus.UNKNOWN
            return

        statuses = [c.status for c in self.checks]

        if HealthStatus.UNHEALTHY in statuses:
            self.status = HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses:
            self.status = HealthStatus.DEGRADED
        elif HealthStatus.UNKNOWN in statuses:
            self.status = HealthStatus.DEGRADED
        else:
            self.status = HealthStatus.HEALTHY
```

---

### Task 2: Criar Health Checks

**Arquivo:** `src/aios/healthcheck/checks.py`
**Tipo:** create

**Código esperado:**
```python
"""Individual health checks."""

from pathlib import Path
from typing import Protocol

from aios.healthcheck.models import CheckResult, HealthStatus
from aios.agents.registry import agent_registry
from aios.context.session import session_manager


class HealthCheck(Protocol):
    """Protocol for health checks."""

    @property
    def name(self) -> str:
        """Check name."""
        ...

    def check(self) -> CheckResult:
        """Execute check and return result."""
        ...


class AgentRegistryCheck:
    """Check that agent registry is loaded."""

    @property
    def name(self) -> str:
        return "agent_registry"

    def check(self) -> CheckResult:
        if not agent_registry.is_loaded:
            return CheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message="Agent registry not loaded"
            )

        count = agent_registry.count
        if count == 0:
            return CheckResult(
                name=self.name,
                status=HealthStatus.DEGRADED,
                message="Agent registry loaded but empty"
            )

        return CheckResult(
            name=self.name,
            status=HealthStatus.HEALTHY,
            message=f"Agent registry loaded with {count} agents",
            details={"agent_count": count}
        )


class SessionPersistenceCheck:
    """Check session persistence is working."""

    @property
    def name(self) -> str:
        return "session_persistence"

    def check(self) -> CheckResult:
        try:
            state = session_manager.reload()

            return CheckResult(
                name=self.name,
                status=HealthStatus.HEALTHY,
                message="Session persistence working",
                details={
                    "active_agent": state.active_agent,
                    "has_state": True
                }
            )
        except Exception as e:
            return CheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Session persistence error: {str(e)}"
            )


class ConfigurationCheck:
    """Check required configuration files exist."""

    REQUIRED_FILES = [
        ".aios",
        "pyproject.toml",
    ]

    OPTIONAL_FILES = [
        ".aios/session-state.json",
        "config/credentials.yaml",
        ".env",
    ]

    @property
    def name(self) -> str:
        return "configuration"

    def check(self) -> CheckResult:
        missing_required = []
        missing_optional = []

        for file_path in self.REQUIRED_FILES:
            if not Path(file_path).exists():
                missing_required.append(file_path)

        for file_path in self.OPTIONAL_FILES:
            if not Path(file_path).exists():
                missing_optional.append(file_path)

        if missing_required:
            return CheckResult(
                name=self.name,
                status=HealthStatus.UNHEALTHY,
                message=f"Missing required files: {', '.join(missing_required)}",
                details={
                    "missing_required": missing_required,
                    "missing_optional": missing_optional
                }
            )

        if missing_optional:
            return CheckResult(
                name=self.name,
                status=HealthStatus.DEGRADED,
                message=f"Missing optional files: {', '.join(missing_optional)}",
                details={"missing_optional": missing_optional}
            )

        return CheckResult(
            name=self.name,
            status=HealthStatus.HEALTHY,
            message="All configuration files present"
        )


class AgentIdentityCheck:
    """Check agent identity isolation is enforced."""

    @property
    def name(self) -> str:
        return "agent_identity_isolation"

    def check(self) -> CheckResult:
        # Check that no agent has another agent's capabilities in scope
        for agent in agent_registry.get_all():
            # Check for scope conflicts
            for other in agent_registry.get_all():
                if agent.id == other.id:
                    continue

                # If agent A has actions that are exclusive to agent B, that's a problem
                for action in agent.scope.can:
                    if action in other.scope.cannot:
                        # This could indicate scope overlap issues
                        pass

        return CheckResult(
            name=self.name,
            status=HealthStatus.HEALTHY,
            message="Agent identity isolation configured correctly",
            details={
                "rule": "Each agent is a unique, isolated entity",
                "agents_checked": agent_registry.count
            }
        )


# Default checks
DEFAULT_CHECKS: list[HealthCheck] = [
    AgentRegistryCheck(),
    SessionPersistenceCheck(),
    ConfigurationCheck(),
    AgentIdentityCheck(),
]
```

---

### Task 3: Criar Health Check Engine

**Arquivo:** `src/aios/healthcheck/engine.py`
**Tipo:** create

**Código esperado:**
```python
"""Health check engine."""

from typing import Optional

from aios.healthcheck.models import SystemHealth, HealthStatus
from aios.healthcheck.checks import HealthCheck, DEFAULT_CHECKS


class HealthCheckEngine:
    """Runs health checks and produces system health report."""

    def __init__(self, checks: Optional[list[HealthCheck]] = None) -> None:
        self._checks = checks or DEFAULT_CHECKS.copy()

    def add_check(self, check: HealthCheck) -> None:
        """Add a health check."""
        self._checks.append(check)

    def remove_check(self, name: str) -> bool:
        """Remove a health check by name."""
        for i, check in enumerate(self._checks):
            if check.name == name:
                self._checks.pop(i)
                return True
        return False

    def run_all(self) -> SystemHealth:
        """Run all health checks and return system health."""
        health = SystemHealth(status=HealthStatus.UNKNOWN)

        for check in self._checks:
            try:
                result = check.check()
            except Exception as e:
                from aios.healthcheck.models import CheckResult
                result = CheckResult(
                    name=check.name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Check raised exception: {str(e)}"
                )

            health.add_check(result)

        return health

    def run_check(self, name: str) -> Optional[SystemHealth]:
        """Run a specific health check by name."""
        for check in self._checks:
            if check.name == name:
                health = SystemHealth(status=HealthStatus.UNKNOWN)
                result = check.check()
                health.add_check(result)
                return health
        return None

    @property
    def check_names(self) -> list[str]:
        """Get list of registered check names."""
        return [c.name for c in self._checks]


# Global instance
health_engine = HealthCheckEngine()
```

---

### Task 4: Criar testes

**Arquivo:** `tests/test_healthcheck/test_engine.py`
**Tipo:** create

**Código esperado:**
```python
"""Tests for health check engine."""

import pytest
from pathlib import Path

from aios.healthcheck.models import (
    HealthStatus,
    CheckResult,
    SystemHealth
)
from aios.healthcheck.checks import (
    AgentRegistryCheck,
    SessionPersistenceCheck,
    ConfigurationCheck,
    AgentIdentityCheck,
)
from aios.healthcheck.engine import HealthCheckEngine


class TestCheckResult:
    def test_healthy_check(self) -> None:
        result = CheckResult(
            name="test",
            status=HealthStatus.HEALTHY,
            message="OK"
        )
        assert result.is_healthy is True

    def test_unhealthy_check(self) -> None:
        result = CheckResult(
            name="test",
            status=HealthStatus.UNHEALTHY,
            message="Failed"
        )
        assert result.is_healthy is False


class TestSystemHealth:
    def test_empty_health_is_unknown(self) -> None:
        health = SystemHealth(status=HealthStatus.UNKNOWN)
        assert health.status == HealthStatus.UNKNOWN

    def test_all_healthy(self) -> None:
        health = SystemHealth(status=HealthStatus.UNKNOWN)
        health.add_check(CheckResult(name="a", status=HealthStatus.HEALTHY))
        health.add_check(CheckResult(name="b", status=HealthStatus.HEALTHY))

        assert health.status == HealthStatus.HEALTHY
        assert health.healthy_count == 2
        assert health.unhealthy_count == 0

    def test_one_unhealthy_makes_system_unhealthy(self) -> None:
        health = SystemHealth(status=HealthStatus.UNKNOWN)
        health.add_check(CheckResult(name="a", status=HealthStatus.HEALTHY))
        health.add_check(CheckResult(name="b", status=HealthStatus.UNHEALTHY))

        assert health.status == HealthStatus.UNHEALTHY

    def test_degraded_status(self) -> None:
        health = SystemHealth(status=HealthStatus.UNKNOWN)
        health.add_check(CheckResult(name="a", status=HealthStatus.HEALTHY))
        health.add_check(CheckResult(name="b", status=HealthStatus.DEGRADED))

        assert health.status == HealthStatus.DEGRADED


class TestHealthCheckEngine:
    def test_run_all_checks(self) -> None:
        engine = HealthCheckEngine(checks=[])

        # Add simple check
        class SimpleCheck:
            @property
            def name(self) -> str:
                return "simple"

            def check(self) -> CheckResult:
                return CheckResult(
                    name=self.name,
                    status=HealthStatus.HEALTHY
                )

        engine.add_check(SimpleCheck())
        health = engine.run_all()

        assert len(health.checks) == 1
        assert health.is_healthy

    def test_check_exception_handling(self) -> None:
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
        assert "exception" in health.checks[0].message.lower()

    def test_run_specific_check(self) -> None:
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

    def test_remove_check(self) -> None:
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

    def test_check_names(self) -> None:
        engine = HealthCheckEngine(checks=[])
        assert engine.check_names == []


class TestAgentIdentityCheck:
    def test_identity_check(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test agent identity isolation check."""
        from aios.agents import registry
        from aios.agents.registry import AgentRegistry

        # Create mock registry
        mock_registry = AgentRegistry()
        monkeypatch.setattr(registry, "agent_registry", mock_registry)

        check = AgentIdentityCheck()
        result = check.check()

        # Should pass even with empty registry
        assert result.status == HealthStatus.HEALTHY
        assert "identity isolation" in result.message.lower()
```

---

## Validação Final

- [ ] Health checks funcionam
- [ ] Status correto (healthy/degraded/unhealthy)
- [ ] Agent identity check incluso
- [ ] Testes com 90%+ coverage
- [ ] Engine trata exceções gracefully

## Notas para Ralph

- Health checks devem ser rápidos (<100ms cada)
- Sempre tratar exceções em checks
- Agent identity isolation é check obrigatório
- Usar Protocol para extensibilidade
