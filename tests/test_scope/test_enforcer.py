"""Tests for scope enforcer."""

import pytest

from aios.agents.models import AgentDefinition, AgentScope, AgentTier
from aios.scope.enforcer import ActionResult, ScopeCheckResult, ScopeEnforcer


@pytest.fixture
def enforcer() -> ScopeEnforcer:
    """Create a scope enforcer instance."""
    return ScopeEnforcer()


@pytest.fixture
def dev_agent() -> AgentDefinition:
    """Developer agent (Dex) - cannot push."""
    return AgentDefinition(
        name="Dex",
        id="dev",
        tier=AgentTier.IC,
        title="Full Stack Developer",
        scope=AgentScope(
            can=["write_code", "run_tests", "commit"],
            cannot=["git_push", "deploy_production"],
        ),
    )


@pytest.fixture
def devops_agent() -> AgentDefinition:
    """DevOps agent (Gage) - can push."""
    return AgentDefinition(
        name="Gage",
        id="devops",
        tier=AgentTier.IC,
        title="DevOps Engineer",
        scope=AgentScope(
            can=["git_push", "create_pr", "deploy_production"],
            cannot=["write_feature_code"],
        ),
    )


@pytest.fixture
def security_agent() -> AgentDefinition:
    """Security QA agent (Quinn)."""
    return AgentDefinition(
        name="Quinn",
        id="qa-sec",
        tier=AgentTier.IC,
        title="Security QA Lead",
        scope=AgentScope(
            can=["security_audit", "orchestrate_sub_agents"],
            cannot=["write_code", "code_quality_review"],
        ),
    )


@pytest.fixture
def data_engineer_agent() -> AgentDefinition:
    """Data Engineer agent (Dara)."""
    return AgentDefinition(
        name="Dara",
        id="data-eng",
        tier=AgentTier.IC,
        title="Data Engineer",
        scope=AgentScope(
            can=["execute_ddl", "design_schema", "write_migrations"],
            cannot=["write_application_code"],
        ),
    )


@pytest.fixture
def minimal_agent() -> AgentDefinition:
    """Agent with empty scope."""
    return AgentDefinition(
        name="Minimal",
        id="minimal",
        tier=AgentTier.IC,
        title="Minimal Agent",
        scope=AgentScope(can=[], cannot=[]),
    )


class TestScopeCheckResult:
    """Tests for ScopeCheckResult dataclass."""

    def test_result_with_reason(self) -> None:
        """Test creating result with reason."""
        result = ScopeCheckResult(
            result=ActionResult.BLOCKED,
            agent_id="dev",
            action="git_push",
            reason="Not allowed",
        )
        assert result.result == ActionResult.BLOCKED
        assert result.agent_id == "dev"
        assert result.action == "git_push"
        assert result.reason == "Not allowed"

    def test_result_without_reason(self) -> None:
        """Test creating result without reason."""
        result = ScopeCheckResult(
            result=ActionResult.ALLOWED,
            agent_id="devops",
            action="git_push",
        )
        assert result.result == ActionResult.ALLOWED
        assert result.reason is None

    def test_result_is_immutable(self) -> None:
        """Test that result is frozen."""
        result = ScopeCheckResult(
            result=ActionResult.ALLOWED,
            agent_id="dev",
            action="test",
        )
        with pytest.raises(AttributeError):
            result.action = "modified"  # type: ignore[misc]


class TestActionResult:
    """Tests for ActionResult enum."""

    def test_allowed_value(self) -> None:
        """Test ALLOWED value."""
        assert ActionResult.ALLOWED.value == "allowed"

    def test_blocked_value(self) -> None:
        """Test BLOCKED value."""
        assert ActionResult.BLOCKED.value == "blocked"

    def test_warning_value(self) -> None:
        """Test WARNING value."""
        assert ActionResult.WARNING.value == "warning"


class TestScopeEnforcer:
    """Tests for ScopeEnforcer class."""

    def test_dev_cannot_push(
        self,
        enforcer: ScopeEnforcer,
        dev_agent: AgentDefinition,
    ) -> None:
        """Dev agent should be blocked from pushing."""
        result = enforcer.check(dev_agent, "git_push")

        assert result.result == ActionResult.BLOCKED
        assert result.reason is not None
        assert "exclusive" in result.reason.lower() or "cannot" in result.reason.lower()

    def test_devops_can_push(
        self,
        enforcer: ScopeEnforcer,
        devops_agent: AgentDefinition,
    ) -> None:
        """DevOps agent should be allowed to push."""
        result = enforcer.check(devops_agent, "git_push")

        assert result.result == ActionResult.ALLOWED
        assert result.reason is None

    def test_dev_can_write_code(
        self,
        enforcer: ScopeEnforcer,
        dev_agent: AgentDefinition,
    ) -> None:
        """Dev agent should be allowed to write code."""
        result = enforcer.check(dev_agent, "write_code")

        assert result.result == ActionResult.ALLOWED

    def test_devops_cannot_write_feature_code(
        self,
        enforcer: ScopeEnforcer,
        devops_agent: AgentDefinition,
    ) -> None:
        """DevOps agent cannot write feature code."""
        result = enforcer.check(devops_agent, "write_feature_code")

        assert result.result == ActionResult.BLOCKED
        assert result.reason is not None
        assert "cannot" in result.reason.lower()

    def test_globally_blocked_actions(
        self,
        enforcer: ScopeEnforcer,
        dev_agent: AgentDefinition,
    ) -> None:
        """Globally blocked actions should be blocked for all."""
        result = enforcer.check(dev_agent, "delete_production_data")

        assert result.result == ActionResult.BLOCKED
        assert result.reason is not None
        assert "globally blocked" in result.reason.lower()

    def test_globally_blocked_expose_secrets(
        self,
        enforcer: ScopeEnforcer,
        devops_agent: AgentDefinition,
    ) -> None:
        """Even devops cannot expose secrets."""
        result = enforcer.check(devops_agent, "expose_secrets")

        assert result.result == ActionResult.BLOCKED
        assert "globally blocked" in result.reason.lower()

    def test_globally_blocked_bypass_security(
        self,
        enforcer: ScopeEnforcer,
        security_agent: AgentDefinition,
    ) -> None:
        """Even security agent cannot bypass security."""
        result = enforcer.check(security_agent, "bypass_security")

        assert result.result == ActionResult.BLOCKED

    def test_security_audit_exclusive(
        self,
        enforcer: ScopeEnforcer,
        dev_agent: AgentDefinition,
        security_agent: AgentDefinition,
    ) -> None:
        """Security audit should be exclusive to qa-sec."""
        dev_result = enforcer.check(dev_agent, "security_audit")
        assert dev_result.result == ActionResult.BLOCKED
        assert dev_result.reason is not None
        assert "exclusive" in dev_result.reason.lower()

        sec_result = enforcer.check(security_agent, "security_audit")
        assert sec_result.result == ActionResult.ALLOWED

    def test_execute_ddl_exclusive(
        self,
        enforcer: ScopeEnforcer,
        dev_agent: AgentDefinition,
        data_engineer_agent: AgentDefinition,
    ) -> None:
        """Execute DDL should be exclusive to data-eng."""
        dev_result = enforcer.check(dev_agent, "execute_ddl")
        assert dev_result.result == ActionResult.BLOCKED
        assert "exclusive" in dev_result.reason.lower()

        data_result = enforcer.check(data_engineer_agent, "execute_ddl")
        assert data_result.result == ActionResult.ALLOWED

    def test_create_pr_exclusive_to_devops(
        self,
        enforcer: ScopeEnforcer,
        dev_agent: AgentDefinition,
        devops_agent: AgentDefinition,
    ) -> None:
        """Create PR should be exclusive to devops."""
        dev_result = enforcer.check(dev_agent, "create_pr")
        assert dev_result.result == ActionResult.BLOCKED

        devops_result = enforcer.check(devops_agent, "create_pr")
        assert devops_result.result == ActionResult.ALLOWED

    def test_deploy_production_exclusive(
        self,
        enforcer: ScopeEnforcer,
        dev_agent: AgentDefinition,
        devops_agent: AgentDefinition,
    ) -> None:
        """Deploy production should be exclusive to devops."""
        dev_result = enforcer.check(dev_agent, "deploy_production")
        assert dev_result.result == ActionResult.BLOCKED

        devops_result = enforcer.check(devops_agent, "deploy_production")
        assert devops_result.result == ActionResult.ALLOWED

    def test_is_allowed_helper(
        self,
        enforcer: ScopeEnforcer,
        dev_agent: AgentDefinition,
    ) -> None:
        """Test is_allowed helper method."""
        assert enforcer.is_allowed(dev_agent, "write_code") is True
        assert enforcer.is_allowed(dev_agent, "git_push") is False

    def test_is_blocked_helper(
        self,
        enforcer: ScopeEnforcer,
        dev_agent: AgentDefinition,
    ) -> None:
        """Test is_blocked helper method."""
        assert enforcer.is_blocked(dev_agent, "git_push") is True
        assert enforcer.is_blocked(dev_agent, "write_code") is False

    def test_get_allowed_actions(
        self,
        enforcer: ScopeEnforcer,
        dev_agent: AgentDefinition,
    ) -> None:
        """Test getting list of allowed actions."""
        allowed = enforcer.get_allowed_actions(dev_agent)

        assert "write_code" in allowed
        assert "run_tests" in allowed
        assert "commit" in allowed
        assert "git_push" not in allowed

    def test_get_blocked_actions(
        self,
        enforcer: ScopeEnforcer,
        dev_agent: AgentDefinition,
    ) -> None:
        """Test getting list of blocked actions."""
        blocked = enforcer.get_blocked_actions(dev_agent)

        assert "git_push" in blocked
        assert "deploy_production" in blocked
        assert "create_pr" in blocked  # Exclusive action
        assert "security_audit" in blocked  # Exclusive action
        assert "execute_ddl" in blocked  # Exclusive action

    def test_get_blocked_actions_does_not_duplicate(
        self,
        enforcer: ScopeEnforcer,
        dev_agent: AgentDefinition,
    ) -> None:
        """Blocked actions list should not have duplicates."""
        blocked = enforcer.get_blocked_actions(dev_agent)

        # git_push and deploy_production are both in cannot and exclusive
        assert blocked.count("git_push") == 1
        assert blocked.count("deploy_production") == 1

    def test_warning_for_action_not_in_can_scope(
        self,
        enforcer: ScopeEnforcer,
        dev_agent: AgentDefinition,
    ) -> None:
        """Action not in can scope but not blocked should return warning."""
        result = enforcer.check(dev_agent, "unknown_action")

        assert result.result == ActionResult.WARNING
        assert result.reason is not None
        assert "not in agent's 'can' scope" in result.reason.lower()

    def test_minimal_agent_allows_non_exclusive_actions(
        self,
        enforcer: ScopeEnforcer,
        minimal_agent: AgentDefinition,
    ) -> None:
        """Agent with empty scope allows non-exclusive actions."""
        result = enforcer.check(minimal_agent, "some_random_action")

        # Empty can list means everything is allowed (except exclusive/blocked)
        assert result.result == ActionResult.ALLOWED

    def test_minimal_agent_still_blocked_from_exclusive(
        self,
        enforcer: ScopeEnforcer,
        minimal_agent: AgentDefinition,
    ) -> None:
        """Agent with empty scope is still blocked from exclusive actions."""
        result = enforcer.check(minimal_agent, "git_push")

        assert result.result == ActionResult.BLOCKED

    def test_result_contains_correct_agent_id(
        self,
        enforcer: ScopeEnforcer,
        dev_agent: AgentDefinition,
    ) -> None:
        """Result should contain correct agent_id."""
        result = enforcer.check(dev_agent, "write_code")

        assert result.agent_id == "dev"

    def test_result_contains_correct_action(
        self,
        enforcer: ScopeEnforcer,
        dev_agent: AgentDefinition,
    ) -> None:
        """Result should contain correct action."""
        result = enforcer.check(dev_agent, "write_code")

        assert result.action == "write_code"


class TestScopeEnforcerPriority:
    """Tests for priority ordering of scope checks."""

    def test_globally_blocked_takes_priority_over_can(
        self,
        enforcer: ScopeEnforcer,
    ) -> None:
        """Globally blocked should override even if in can scope."""
        # Create agent that explicitly has blocked action in can scope
        agent = AgentDefinition(
            name="Hacker",
            id="hacker",
            tier=AgentTier.IC,
            title="Hacker Agent",
            scope=AgentScope(
                can=["delete_production_data"],  # Trying to allow blocked action
                cannot=[],
            ),
        )
        result = enforcer.check(agent, "delete_production_data")

        assert result.result == ActionResult.BLOCKED
        assert "globally blocked" in result.reason.lower()

    def test_exclusive_takes_priority_over_can(
        self,
        enforcer: ScopeEnforcer,
    ) -> None:
        """Exclusive check should override even if in can scope."""
        # Create agent that explicitly has exclusive action in can scope
        agent = AgentDefinition(
            name="Wannabe",
            id="wannabe",
            tier=AgentTier.IC,
            title="Wannabe DevOps",
            scope=AgentScope(
                can=["git_push"],  # Trying to allow exclusive action
                cannot=[],
            ),
        )
        result = enforcer.check(agent, "git_push")

        assert result.result == ActionResult.BLOCKED
        assert "exclusive" in result.reason.lower()


class TestGlobalEnforcerInstance:
    """Tests for the global scope_enforcer instance."""

    def test_global_instance_exists(self) -> None:
        """Global scope_enforcer instance should exist."""
        from aios.scope.enforcer import scope_enforcer

        assert scope_enforcer is not None
        assert isinstance(scope_enforcer, ScopeEnforcer)

    def test_global_instance_is_functional(
        self,
        dev_agent: AgentDefinition,
    ) -> None:
        """Global instance should be functional."""
        from aios.scope.enforcer import scope_enforcer

        result = scope_enforcer.check(dev_agent, "git_push")
        assert result.result == ActionResult.BLOCKED
