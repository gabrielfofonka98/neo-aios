"""Agent registry.

Central registry for all NEO-AIOS agents. Handles loading, lookup,
and scope validation.
"""

from collections.abc import Iterator
from pathlib import Path

import yaml

from aios.agents.models import AgentDefinition
from aios.agents.models import AgentHierarchy
from aios.agents.models import AgentLevel
from aios.agents.models import AgentScope
from aios.agents.models import AgentTier


class AgentNotFoundError(Exception):
    """Raised when requested agent is not in registry."""

    def __init__(self, agent_id: str) -> None:
        self.agent_id = agent_id
        super().__init__(f"Agent '{agent_id}' not found in registry")


class ScopeViolationError(Exception):
    """Raised when agent attempts forbidden action."""

    def __init__(self, agent_id: str, action: str, reason: str = "") -> None:
        self.agent_id = agent_id
        self.action = action
        self.reason = reason
        msg = f"Agent '{agent_id}' cannot perform '{action}'"
        if reason:
            msg += f": {reason}"
        super().__init__(msg)


class DelegationViolationError(Exception):
    """Raised when agent attempts invalid delegation."""

    def __init__(self, from_id: str, to_id: str, reason: str = "") -> None:
        self.from_id = from_id
        self.to_id = to_id
        self.reason = reason
        msg = f"Agent '{from_id}' cannot delegate to '{to_id}'"
        if reason:
            msg += f": {reason}"
        super().__init__(msg)


class AgentRegistry:
    """Central registry of all agents.

    Example:
        >>> registry = AgentRegistry.load()
        >>> dev = registry.get("dev")
        >>> registry.validate_action("dev", "write_code")
        True
        >>> registry.validate_action("dev", "git_push")
        ScopeViolationError: Agent 'dev' cannot perform 'git_push'
    """

    def __init__(self, agents: dict[str, AgentDefinition] | None = None) -> None:
        """Initialize registry with optional pre-loaded agents."""
        self._agents: dict[str, AgentDefinition] = agents or {}

    @classmethod
    def load(cls, agents_dir: Path | None = None) -> "AgentRegistry":
        """Load registry from agents directory.

        Args:
            agents_dir: Path to agents/ directory. Defaults to ./agents/

        Returns:
            Populated AgentRegistry instance.
        """
        if agents_dir is None:
            agents_dir = Path("agents")

        registry = cls()

        if not agents_dir.exists():
            return registry

        # Walk through all tier directories
        for tier_dir in agents_dir.iterdir():
            if not tier_dir.is_dir():
                continue

            # Walk through agent directories
            for agent_dir in tier_dir.iterdir():
                skill_file = agent_dir / "SKILL.md"
                if skill_file.exists():
                    agent = registry._load_agent_from_skill(skill_file)
                    if agent:
                        registry._agents[agent.id] = agent

        return registry

    def _load_agent_from_skill(self, skill_path: Path) -> AgentDefinition | None:
        """Load agent definition from SKILL.md file."""
        try:
            content = skill_path.read_text()

            # Extract YAML block from markdown
            yaml_start = content.find("```yaml")
            yaml_end = content.find("```", yaml_start + 7)

            if yaml_start == -1 or yaml_end == -1:
                return None

            yaml_content = content[yaml_start + 7 : yaml_end].strip()
            data = yaml.safe_load(yaml_content)

            if not data or "agent" not in data:
                return None

            agent_data = data["agent"]
            scope_data = data.get("scope", {})
            hierarchy_data = data.get("hierarchy", {})

            return AgentDefinition(
                name=agent_data["name"],
                id=agent_data["id"],
                tier=AgentTier(agent_data["tier"]),
                level=AgentLevel(agent_data.get("level", "core")),
                title=agent_data["title"],
                icon=agent_data.get("icon", "🤖"),
                scope=AgentScope(
                    can=scope_data.get("can", []),
                    cannot=scope_data.get("cannot", []),
                ),
                hierarchy=AgentHierarchy(
                    tier=AgentTier(hierarchy_data.get("tier", agent_data["tier"])),
                    reports_to=hierarchy_data.get("reports_to"),
                    approves=hierarchy_data.get("approves", []),
                    delegates_to=hierarchy_data.get("delegates_to", []),
                    collaborates_with=hierarchy_data.get("collaborates_with", []),
                )
                if hierarchy_data
                else None,
                skill_path=skill_path,
                when_to_use=agent_data.get("whenToUse", ""),
            )
        except Exception:
            return None

    def get(self, agent_id: str) -> AgentDefinition | None:
        """Get agent by ID.

        Args:
            agent_id: Agent's unique identifier.

        Returns:
            AgentDefinition if found, None otherwise.
        """
        return self._agents.get(agent_id)

    def get_or_raise(self, agent_id: str) -> AgentDefinition:
        """Get agent by ID, raising if not found.

        Args:
            agent_id: Agent's unique identifier.

        Returns:
            AgentDefinition.

        Raises:
            AgentNotFoundError: If agent not in registry.
        """
        agent = self.get(agent_id)
        if agent is None:
            raise AgentNotFoundError(agent_id)
        return agent

    def get_by_tier(self, tier: AgentTier) -> list[AgentDefinition]:
        """Get all agents in a tier.

        Args:
            tier: The tier to filter by.

        Returns:
            List of agents in the tier.
        """
        return [a for a in self._agents.values() if a.tier == tier]

    def get_by_level(self, level: AgentLevel) -> list[AgentDefinition]:
        """Get all agents at a level.

        Args:
            level: The level to filter by.

        Returns:
            List of agents at the level.
        """
        return [a for a in self._agents.values() if a.level == level]

    def all(self) -> list[AgentDefinition]:
        """Get all registered agents."""
        return list(self._agents.values())

    def __iter__(self) -> Iterator[AgentDefinition]:
        """Iterate over all agents."""
        return iter(self._agents.values())

    def __len__(self) -> int:
        """Return number of registered agents."""
        return len(self._agents)

    def __contains__(self, agent_id: str) -> bool:
        """Check if agent is registered."""
        return agent_id in self._agents

    # =========================================================================
    # Validation Methods
    # =========================================================================

    def validate_action(
        self, agent_id: str, action: str, *, raise_on_violation: bool = True
    ) -> bool:
        """Validate if agent can perform action.

        Args:
            agent_id: Agent's unique identifier.
            action: The action to validate.
            raise_on_violation: If True, raise on violation.

        Returns:
            True if allowed, False if not (when raise_on_violation=False).

        Raises:
            AgentNotFoundError: If agent not in registry.
            ScopeViolationError: If action forbidden and raise_on_violation=True.
        """
        agent = self.get_or_raise(agent_id)

        if agent.cannot_do(action):
            if raise_on_violation:
                raise ScopeViolationError(
                    agent_id, action, "Action is in agent's 'cannot' list"
                )
            return False

        if not agent.can_do(action):
            if raise_on_violation:
                raise ScopeViolationError(
                    agent_id, action, "Action is not in agent's 'can' list"
                )
            return False

        return True

    def validate_delegation(
        self, from_id: str, to_id: str, *, raise_on_violation: bool = True
    ) -> bool:
        """Validate if agent can delegate to another.

        Args:
            from_id: Delegating agent's ID.
            to_id: Target agent's ID.
            raise_on_violation: If True, raise on violation.

        Returns:
            True if allowed.

        Raises:
            AgentNotFoundError: If either agent not in registry.
            DelegationViolationError: If delegation not allowed.
        """
        from_agent = self.get_or_raise(from_id)
        to_agent = self.get_or_raise(to_id)

        if not from_agent.can_delegate_to(to_agent):
            if raise_on_violation:
                raise DelegationViolationError(
                    from_id,
                    to_id,
                    f"Cannot delegate from {from_agent.tier.value} to {to_agent.tier.value}",
                )
            return False

        return True

    # =========================================================================
    # Special Rules
    # =========================================================================

    def can_git_push(self, agent_id: str) -> bool:
        """Check if agent can perform git push.

        Only DevOps (Gage) can push to remote.

        Args:
            agent_id: Agent's unique identifier.

        Returns:
            True only if agent is devops.
        """
        return agent_id == "devops"

    def can_write_code(self, agent_id: str) -> bool:
        """Check if agent can write code.

        C-Level, VP, and Director tiers cannot write code.

        Args:
            agent_id: Agent's unique identifier.

        Returns:
            True if agent can write code.
        """
        agent = self.get(agent_id)
        if agent is None:
            return False

        no_code_tiers = {AgentTier.C_LEVEL, AgentTier.VP, AgentTier.DIRECTOR}
        return agent.tier not in no_code_tiers
