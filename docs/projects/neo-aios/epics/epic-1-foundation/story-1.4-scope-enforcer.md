# Story 1.4: Scope Enforcer

**Status:** [ ] Pending
**Executor:** Ralph/Dex
**Complexidade:** Alta
**Dependência:** Story 1.2

---

## Objetivo

Criar sistema que BLOQUEIA (não apenas avisa) ações fora do escopo do agente ativo.

## Tasks

### Task 1: Criar Scope Enforcer

**Arquivo:** `src/aios/scope/enforcer.py`
**Tipo:** create

**Código esperado:**
```python
"""Scope enforcement for agent actions."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from aios.models.agent import AgentDefinition


class ActionResult(Enum):
    """Result of scope check."""
    ALLOWED = "allowed"
    BLOCKED = "blocked"
    WARNING = "warning"


@dataclass
class ScopeCheckResult:
    """Result of a scope check."""
    result: ActionResult
    agent_id: str
    action: str
    reason: Optional[str] = None


class ScopeEnforcer:
    """Enforces scope rules for agents at runtime."""

    # Actions that only specific agents can perform
    EXCLUSIVE_ACTIONS: dict[str, list[str]] = {
        "git_push": ["devops"],
        "create_pr": ["devops"],
        "deploy_production": ["devops"],
        "execute_ddl": ["data-eng"],
        "security_audit": ["qa-sec"],
    }

    # Actions blocked for all agents
    GLOBALLY_BLOCKED: list[str] = [
        "delete_production_data",
        "expose_secrets",
        "bypass_security",
    ]

    def check(
        self,
        agent: AgentDefinition,
        action: str
    ) -> ScopeCheckResult:
        """Check if agent can perform action."""
        # Check globally blocked actions
        if action in self.GLOBALLY_BLOCKED:
            return ScopeCheckResult(
                result=ActionResult.BLOCKED,
                agent_id=agent.id,
                action=action,
                reason=f"Action '{action}' is globally blocked"
            )

        # Check exclusive actions
        if action in self.EXCLUSIVE_ACTIONS:
            allowed_agents = self.EXCLUSIVE_ACTIONS[action]
            if agent.id not in allowed_agents:
                return ScopeCheckResult(
                    result=ActionResult.BLOCKED,
                    agent_id=agent.id,
                    action=action,
                    reason=f"Action '{action}' is exclusive to: {', '.join(allowed_agents)}"
                )

        # Check agent's explicit cannot list
        if agent.cannot_do(action):
            return ScopeCheckResult(
                result=ActionResult.BLOCKED,
                agent_id=agent.id,
                action=action,
                reason=f"Action '{action}' is in agent's 'cannot' scope"
            )

        # Check agent's explicit can list (if defined)
        if agent.scope.can and not agent.can_do(action):
            return ScopeCheckResult(
                result=ActionResult.WARNING,
                agent_id=agent.id,
                action=action,
                reason=f"Action '{action}' is not in agent's 'can' scope"
            )

        return ScopeCheckResult(
            result=ActionResult.ALLOWED,
            agent_id=agent.id,
            action=action
        )

    def is_allowed(self, agent: AgentDefinition, action: str) -> bool:
        """Quick check if action is allowed."""
        result = self.check(agent, action)
        return result.result == ActionResult.ALLOWED

    def is_blocked(self, agent: AgentDefinition, action: str) -> bool:
        """Quick check if action is blocked."""
        result = self.check(agent, action)
        return result.result == ActionResult.BLOCKED

    def get_allowed_actions(self, agent: AgentDefinition) -> list[str]:
        """Get list of actions agent can perform."""
        return agent.scope.can.copy()

    def get_blocked_actions(self, agent: AgentDefinition) -> list[str]:
        """Get list of actions agent cannot perform."""
        blocked = agent.scope.cannot.copy()

        # Add exclusive actions not available to this agent
        for action, allowed_agents in self.EXCLUSIVE_ACTIONS.items():
            if agent.id not in allowed_agents:
                if action not in blocked:
                    blocked.append(action)

        return blocked


# Global enforcer instance
scope_enforcer = ScopeEnforcer()
```

---

### Task 2: Criar Action Mapper

**Arquivo:** `src/aios/scope/actions.py`
**Tipo:** create

**O que fazer:**
1. Mapear comandos/operações para actions
2. Normalizar nomes de ações

**Código esperado:**
```python
"""Action mapping and normalization."""

from typing import Optional


class ActionMapper:
    """Maps operations to normalized action names."""

    # Map of operation patterns to action names
    OPERATION_MAP: dict[str, str] = {
        # Git operations
        "git push": "git_push",
        "git_push": "git_push",
        "push": "git_push",

        # PR operations
        "gh pr create": "create_pr",
        "create_pr": "create_pr",
        "create pr": "create_pr",

        # Deploy operations
        "deploy": "deploy_production",
        "vercel deploy": "deploy_production",
        "deploy --prod": "deploy_production",

        # Database operations
        "create table": "execute_ddl",
        "alter table": "execute_ddl",
        "drop table": "execute_ddl",
        "execute_ddl": "execute_ddl",

        # Security operations
        "security audit": "security_audit",
        "security_audit": "security_audit",
        "scan security": "security_audit",

        # Code operations
        "write_code": "write_code",
        "write code": "write_code",
        "implement": "write_code",

        # Review operations
        "code_review": "code_review",
        "review code": "code_review",
        "review": "code_review",
    }

    def map(self, operation: str) -> str:
        """Map an operation to its normalized action name."""
        # Normalize: lowercase and strip
        normalized = operation.lower().strip()

        # Direct match
        if normalized in self.OPERATION_MAP:
            return self.OPERATION_MAP[normalized]

        # Partial match
        for pattern, action in self.OPERATION_MAP.items():
            if pattern in normalized:
                return action

        # Return original if no mapping found
        return normalized

    def get_action_for_command(self, command: str) -> Optional[str]:
        """Get action name for a bash command."""
        command_lower = command.lower()

        if "git push" in command_lower:
            return "git_push"
        if "gh pr create" in command_lower:
            return "create_pr"
        if any(kw in command_lower for kw in ["create table", "alter table", "drop table"]):
            return "execute_ddl"
        if "vercel" in command_lower and ("deploy" in command_lower or "--prod" in command_lower):
            return "deploy_production"

        return None


# Global instance
action_mapper = ActionMapper()
```

---

### Task 3: Criar testes

**Arquivo:** `tests/test_scope/test_enforcer.py`
**Tipo:** create

**Código esperado:**
```python
"""Tests for scope enforcer."""

import pytest

from aios.models.agent import AgentDefinition, AgentScope
from aios.scope.enforcer import ScopeEnforcer, ActionResult


@pytest.fixture
def enforcer() -> ScopeEnforcer:
    return ScopeEnforcer()


@pytest.fixture
def dev_agent() -> AgentDefinition:
    """Developer agent (Dex) - cannot push."""
    return AgentDefinition(
        name="Dex",
        id="dev",
        scope=AgentScope(
            can=["write_code", "run_tests", "commit"],
            cannot=["git_push", "deploy_production"]
        )
    )


@pytest.fixture
def devops_agent() -> AgentDefinition:
    """DevOps agent (Gage) - can push."""
    return AgentDefinition(
        name="Gage",
        id="devops",
        scope=AgentScope(
            can=["git_push", "create_pr", "deploy_production"],
            cannot=["write_feature_code"]
        )
    )


@pytest.fixture
def security_agent() -> AgentDefinition:
    """Security QA agent (Quinn)."""
    return AgentDefinition(
        name="Quinn",
        id="qa-sec",
        scope=AgentScope(
            can=["security_audit", "orchestrate_sub_agents"],
            cannot=["write_code", "code_quality_review"]
        )
    )


class TestScopeEnforcer:
    def test_dev_cannot_push(
        self,
        enforcer: ScopeEnforcer,
        dev_agent: AgentDefinition
    ) -> None:
        """Dev agent should be blocked from pushing."""
        result = enforcer.check(dev_agent, "git_push")

        assert result.result == ActionResult.BLOCKED
        assert "exclusive" in result.reason.lower() or "cannot" in result.reason.lower()

    def test_devops_can_push(
        self,
        enforcer: ScopeEnforcer,
        devops_agent: AgentDefinition
    ) -> None:
        """DevOps agent should be allowed to push."""
        result = enforcer.check(devops_agent, "git_push")

        assert result.result == ActionResult.ALLOWED

    def test_dev_can_write_code(
        self,
        enforcer: ScopeEnforcer,
        dev_agent: AgentDefinition
    ) -> None:
        """Dev agent should be allowed to write code."""
        result = enforcer.check(dev_agent, "write_code")

        assert result.result == ActionResult.ALLOWED

    def test_devops_cannot_write_feature_code(
        self,
        enforcer: ScopeEnforcer,
        devops_agent: AgentDefinition
    ) -> None:
        """DevOps agent cannot write feature code."""
        result = enforcer.check(devops_agent, "write_feature_code")

        assert result.result == ActionResult.BLOCKED

    def test_globally_blocked_actions(
        self,
        enforcer: ScopeEnforcer,
        dev_agent: AgentDefinition
    ) -> None:
        """Globally blocked actions should be blocked for all."""
        result = enforcer.check(dev_agent, "delete_production_data")

        assert result.result == ActionResult.BLOCKED
        assert "globally blocked" in result.reason.lower()

    def test_security_audit_exclusive(
        self,
        enforcer: ScopeEnforcer,
        dev_agent: AgentDefinition,
        security_agent: AgentDefinition
    ) -> None:
        """Security audit should be exclusive to qa-sec."""
        dev_result = enforcer.check(dev_agent, "security_audit")
        assert dev_result.result == ActionResult.BLOCKED

        sec_result = enforcer.check(security_agent, "security_audit")
        assert sec_result.result == ActionResult.ALLOWED

    def test_is_allowed_helper(
        self,
        enforcer: ScopeEnforcer,
        dev_agent: AgentDefinition
    ) -> None:
        """Test is_allowed helper method."""
        assert enforcer.is_allowed(dev_agent, "write_code") is True
        assert enforcer.is_allowed(dev_agent, "git_push") is False

    def test_is_blocked_helper(
        self,
        enforcer: ScopeEnforcer,
        dev_agent: AgentDefinition
    ) -> None:
        """Test is_blocked helper method."""
        assert enforcer.is_blocked(dev_agent, "git_push") is True
        assert enforcer.is_blocked(dev_agent, "write_code") is False

    def test_get_blocked_actions(
        self,
        enforcer: ScopeEnforcer,
        dev_agent: AgentDefinition
    ) -> None:
        """Test getting list of blocked actions."""
        blocked = enforcer.get_blocked_actions(dev_agent)

        assert "git_push" in blocked
        assert "deploy_production" in blocked
        assert "create_pr" in blocked  # Exclusive action
```

---

## Validação Final

- [ ] Dev (Dex) não consegue fazer git push
- [ ] DevOps (Gage) consegue fazer git push
- [ ] Ações globalmente bloqueadas são bloqueadas para todos
- [ ] Testes com 95%+ coverage

## Notas para Ralph

- **CRÍTICO:** git_push DEVE ser exclusivo do devops
- Usar ActionResult enum para resultados claros
- Incluir reason em todos os bloqueios
- Testar com agentes reais do sistema
