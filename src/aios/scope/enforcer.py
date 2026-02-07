"""Scope enforcement for agent actions.

This module provides runtime enforcement of agent scope rules,
blocking actions that are outside an agent's authorized permissions.

Example:
    >>> from aios.agents.models import AgentDefinition, AgentScope, AgentTier
    >>> from aios.scope.enforcer import scope_enforcer, ActionResult
    >>>
    >>> dev = AgentDefinition(
    ...     name="Dex", id="dev", tier=AgentTier.IC, title="Developer",
    ...     scope=AgentScope(can=["write_code"], cannot=["git_push"])
    ... )
    >>> result = scope_enforcer.check(dev, "git_push")
    >>> result.result == ActionResult.BLOCKED
    True
"""

from dataclasses import dataclass
from enum import Enum
from typing import Final

from aios.agents.models import AgentDefinition


class ActionResult(Enum):
    """Result of scope check.

    Attributes:
        ALLOWED: Action is permitted for the agent.
        BLOCKED: Action is forbidden and will be prevented.
        WARNING: Action is not explicitly allowed but not blocked.
    """

    ALLOWED = "allowed"
    BLOCKED = "blocked"
    WARNING = "warning"


@dataclass(frozen=True)
class ScopeCheckResult:
    """Result of a scope check.

    Attributes:
        result: The ActionResult indicating if action is allowed/blocked.
        agent_id: ID of the agent being checked.
        action: The action being checked.
        reason: Explanation for blocking or warning (None if allowed).
    """

    result: ActionResult
    agent_id: str
    action: str
    reason: str | None = None


class ScopeEnforcer:
    """Enforces scope rules for agents at runtime.

    This class is responsible for checking whether an agent can perform
    a specific action based on:
    1. Globally blocked actions (blocked for everyone)
    2. Exclusive actions (only specific agents can perform)
    3. Agent's explicit cannot list
    4. Agent's explicit can list

    Attributes:
        EXCLUSIVE_ACTIONS: Actions that only specific agents can perform.
        GLOBALLY_BLOCKED: Actions that are blocked for all agents.
    """

    EXCLUSIVE_ACTIONS: Final[dict[str, list[str]]] = {
        "git_push": ["devops"],
        "create_pr": ["devops"],
        "deploy_production": ["devops"],
        "execute_ddl": ["data-engineer"],
        "security_audit": ["qa"],
    }

    GLOBALLY_BLOCKED: Final[list[str]] = [
        "delete_production_data",
        "expose_secrets",
        "bypass_security",
    ]

    def check(self, agent: AgentDefinition, action: str) -> ScopeCheckResult:
        """Check if agent can perform action.

        Args:
            agent: The agent definition to check.
            action: The action to verify.

        Returns:
            ScopeCheckResult with result, agent_id, action, and reason.
        """
        # Check globally blocked actions first
        if action in self.GLOBALLY_BLOCKED:
            return ScopeCheckResult(
                result=ActionResult.BLOCKED,
                agent_id=agent.id,
                action=action,
                reason=f"Action '{action}' is globally blocked",
            )

        # Check exclusive actions
        if action in self.EXCLUSIVE_ACTIONS:
            allowed_agents = self.EXCLUSIVE_ACTIONS[action]
            if agent.id not in allowed_agents:
                return ScopeCheckResult(
                    result=ActionResult.BLOCKED,
                    agent_id=agent.id,
                    action=action,
                    reason=f"Action '{action}' is exclusive to: {', '.join(allowed_agents)}",
                )

        # Check agent's explicit cannot list
        if agent.cannot_do(action):
            return ScopeCheckResult(
                result=ActionResult.BLOCKED,
                agent_id=agent.id,
                action=action,
                reason=f"Action '{action}' is in agent's 'cannot' scope",
            )

        # Check agent's explicit can list (if defined)
        if agent.scope.can and not agent.can_do(action):
            return ScopeCheckResult(
                result=ActionResult.WARNING,
                agent_id=agent.id,
                action=action,
                reason=f"Action '{action}' is not in agent's 'can' scope",
            )

        return ScopeCheckResult(
            result=ActionResult.ALLOWED,
            agent_id=agent.id,
            action=action,
        )

    def is_allowed(self, agent: AgentDefinition, action: str) -> bool:
        """Quick check if action is allowed.

        Args:
            agent: The agent definition to check.
            action: The action to verify.

        Returns:
            True if action is allowed, False otherwise.
        """
        result = self.check(agent, action)
        return result.result == ActionResult.ALLOWED

    def is_blocked(self, agent: AgentDefinition, action: str) -> bool:
        """Quick check if action is blocked.

        Args:
            agent: The agent definition to check.
            action: The action to verify.

        Returns:
            True if action is blocked, False otherwise.
        """
        result = self.check(agent, action)
        return result.result == ActionResult.BLOCKED

    def get_allowed_actions(self, agent: AgentDefinition) -> list[str]:
        """Get list of actions agent can perform.

        Args:
            agent: The agent definition.

        Returns:
            List of action names from agent's can scope.
        """
        return agent.scope.can.copy()

    def get_blocked_actions(self, agent: AgentDefinition) -> list[str]:
        """Get list of actions agent cannot perform.

        This includes both the agent's explicit cannot list and
        exclusive actions not available to this agent.

        Args:
            agent: The agent definition.

        Returns:
            List of blocked action names.
        """
        blocked = agent.scope.cannot.copy()

        # Add exclusive actions not available to this agent
        for action, allowed_agents in self.EXCLUSIVE_ACTIONS.items():
            if agent.id not in allowed_agents and action not in blocked:
                blocked.append(action)

        return blocked


# Global enforcer instance
scope_enforcer = ScopeEnforcer()
