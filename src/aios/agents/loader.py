"""Agent loader with identity isolation.

Provides agent loading with strict identity isolation guarantees.
Each agent is a unique, isolated entity that cannot simulate or
integrate another agent's behavior.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from aios.agents.models import AgentDefinition
    from aios.agents.registry import AgentRegistry
    from aios.context.session import Session


class AgentIdentityError(Exception):
    """Raised when agent identity isolation is violated.

    This error indicates a critical violation of the identity isolation
    principle: each agent is a unique entity that cannot be combined
    or simulated alongside another agent.
    """

    def __init__(self, current_agent: str, requested_agent: str) -> None:
        """Initialize error.

        Args:
            current_agent: Currently active agent ID.
            requested_agent: Agent ID that was requested.
        """
        self.current_agent = current_agent
        self.requested_agent = requested_agent
        super().__init__(
            f"Cannot load '{requested_agent}' while '{current_agent}' is active. "
            f"Each agent is a unique entity - deactivate first with unload()."
        )


class AgentNotFoundError(Exception):
    """Raised when requested agent is not found."""

    def __init__(self, agent_id: str) -> None:
        """Initialize error.

        Args:
            agent_id: The agent ID that was not found.
        """
        self.agent_id = agent_id
        super().__init__(f"Agent '{agent_id}' not found in registry")


class AgentLoader:
    """Loads agents with strict identity isolation.

    CRITICAL RULE: Each agent is a unique, isolated entity.
    An agent can NEVER simulate or integrate another agent's behavior.

    This loader ensures:
    1. Only one agent can be active at a time
    2. Agent must be explicitly unloaded before loading another
    3. Session state persists for recovery after auto-compact

    Example:
        >>> registry = AgentRegistry.load()
        >>> session = Session.load()
        >>> loader = AgentLoader(registry, session)
        >>> agent = loader.load("dev")
        >>> print(agent.name)
        'Dex'
        >>> loader.load("devops")  # Raises AgentIdentityError
        >>> loader.unload()
        >>> loader.load("devops")  # Now OK
    """

    # Patterns that indicate identity violation in actions
    _FORBIDDEN_PATTERNS: tuple[str, ...] = (
        "como se fosse",
        "eu como",
        "assumir papel",
        "agir como",
        "simular",
        "fingir que sou",
        "me passar por",
        "comportar como",
    )

    def __init__(
        self,
        registry: AgentRegistry,
        session: Session,
    ) -> None:
        """Initialize agent loader.

        Args:
            registry: Agent registry for lookups.
            session: Session manager for persistence.
        """
        self._registry = registry
        self._session = session
        self._current_agent: AgentDefinition | None = None

    @property
    def current_agent(self) -> AgentDefinition | None:
        """Get currently loaded agent."""
        return self._current_agent

    @property
    def is_agent_active(self) -> bool:
        """Check if an agent is currently active."""
        return self._current_agent is not None

    def load(self, agent_id: str) -> AgentDefinition:
        """Load an agent by ID.

        Args:
            agent_id: The agent identifier.

        Returns:
            The loaded AgentDefinition.

        Raises:
            AgentIdentityError: If trying to load while another agent is active.
            AgentNotFoundError: If agent not found in registry.
        """
        # CRITICAL: Check for identity isolation violation
        if self._current_agent is not None:
            raise AgentIdentityError(self._current_agent.id, agent_id)

        agent = self._registry.get(agent_id)
        if agent is None:
            raise AgentNotFoundError(agent_id)

        self._current_agent = agent

        # Persist to session
        skill_path = str(agent.skill_path) if agent.skill_path else ""
        self._session.activate_agent(agent_id, skill_path)
        self._session.save()

        return agent

    def unload(self) -> None:
        """Unload current agent.

        After unloading, a new agent can be loaded. This is the only
        valid way to switch between agents.
        """
        if self._current_agent is not None:
            self._session.deactivate_agent()
            self._session.save()
            self._current_agent = None

    def reload_from_session(self) -> AgentDefinition | None:
        """Reload agent from persisted session state.

        Used for recovery after auto-compact. Reads the session file
        and restores the active agent if one was active.

        Returns:
            The restored AgentDefinition, or None if no agent was active.
        """
        active_id = self._session.state.active_agent
        if active_id is None:
            return None

        agent = self._registry.get(active_id)
        if agent is not None:
            self._current_agent = agent
            return agent

        # Agent was in session but not in registry - clear stale state
        self._session.deactivate_agent()
        self._session.save()
        return None

    def get_agent_prompt(self) -> str:
        """Get system prompt for current agent.

        CRITICAL: The prompt reinforces identity isolation.

        Returns:
            System prompt string, or empty string if no agent active.
        """
        if self._current_agent is None:
            return ""

        agent = self._current_agent

        # Build identity-enforced prompt
        can_list = ", ".join(agent.scope.can) if agent.scope.can else "Não especificado"
        cannot_list = (
            ", ".join(agent.scope.cannot)
            if agent.scope.cannot
            else "Nenhuma restrição específica"
        )

        prompt_parts = [
            f"# Você é {agent.name} ({agent.id})",
            "",
            "## REGRA CRÍTICA: IDENTIDADE ISOLADA",
            "",
            f"Você é APENAS {agent.name}. Você NÃO PODE:",
            "- Simular o comportamento de outro agente",
            "- Dizer 'eu como [outro agente]'",
            "- Executar tarefas fora do seu escopo",
            "",
            "Se uma tarefa não é do seu escopo, DELEGUE.",
            "",
            "## Seu Escopo",
            "",
            f"**Pode fazer:** {can_list}",
            f"**NÃO pode fazer:** {cannot_list}",
        ]

        # Add behavioral rules if present
        if hasattr(agent, "behavioral_rules") and agent.behavioral_rules:
            prompt_parts.extend(
                [
                    "",
                    "## Regras Comportamentais",
                    "",
                ]
            )
            for rule in agent.behavioral_rules:
                prompt_parts.append(f"- {rule}")

        return "\n".join(prompt_parts)

    def verify_identity_isolation(self, requested_action: str) -> bool:
        """Verify that the requested action doesn't violate identity isolation.

        Checks if the action text contains patterns that suggest the agent
        is trying to assume another agent's identity or behavior.

        Args:
            requested_action: The action text to verify.

        Returns:
            True if action is allowed for current agent's identity.
        """
        if self._current_agent is None:
            return True  # No agent loaded, no isolation to enforce

        # Check if action implies another agent's behavior
        action_lower = requested_action.lower()
        return all(pattern not in action_lower for pattern in self._FORBIDDEN_PATTERNS)


class AgentContextBuilder:
    """Builds context for agent prompts.

    Creates comprehensive context including identity enforcement,
    SKILL.md content, and scope reminders.
    """

    def build_full_context(self, agent: AgentDefinition) -> str:
        """Build complete context for agent including SKILL.md content.

        Args:
            agent: The agent to build context for.

        Returns:
            Complete context string with identity enforcement.
        """
        parts: list[str] = []

        # 1. Identity enforcement header
        parts.append(self._build_identity_header(agent))

        # 2. Skill file content (if exists)
        if agent.skill_path:
            skill_content = self._load_skill_content(agent.skill_path)
            if skill_content:
                parts.append(skill_content)

        # 3. Scope enforcement reminder
        parts.append(self._build_scope_reminder(agent))

        return "\n\n---\n\n".join(parts)

    def _build_identity_header(self, agent: AgentDefinition) -> str:
        """Build identity enforcement header.

        Args:
            agent: The agent to build header for.

        Returns:
            Identity header string.
        """
        return f"""# IDENTIDADE: {agent.name} ({agent.id})

REGRA ABSOLUTA: Você é {agent.name} e APENAS {agent.name}.

PROIBIDO:
- Simular outro agente
- Dizer "eu como [outro agente]"
- Assumir capacidades de outro agente
- Executar tarefas fora do seu escopo

VIOLAÇÃO = FALHA CRÍTICA"""

    def _load_skill_content(self, skill_path: Path) -> str | None:
        """Load SKILL.md content.

        Args:
            skill_path: Path to the SKILL.md file.

        Returns:
            File content, or None if file doesn't exist.
        """
        if skill_path.exists():
            return skill_path.read_text(encoding="utf-8")
        return None

    def _build_scope_reminder(self, agent: AgentDefinition) -> str:
        """Build scope reminder.

        Args:
            agent: The agent to build reminder for.

        Returns:
            Scope reminder string.
        """
        can = ", ".join(agent.scope.can) if agent.scope.can else "Geral"
        cannot = ", ".join(agent.scope.cannot) if agent.scope.cannot else "Nenhum"

        return f"""## Lembrete de Escopo

**PERMITIDO para {agent.id}:** {can}
**BLOQUEADO para {agent.id}:** {cannot}

Se a tarefa está em BLOQUEADO → DELEGUE, não execute."""
