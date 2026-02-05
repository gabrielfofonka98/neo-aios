# Story 1.5: Agent Loader

**Status:** [ ] Pending
**Executor:** Ralph/Dex
**Complexidade:** Média
**Dependência:** Story 1.2, Story 1.3

---

## Objetivo

Criar sistema que carrega agente, injeta contexto e garante isolamento de identidade.

## Tasks

### Task 1: Criar Agent Loader

**Arquivo:** `src/aios/agents/loader.py`
**Tipo:** create

**Código esperado:**
```python
"""Agent loader with identity isolation."""

from pathlib import Path
from typing import Optional

from aios.models.agent import AgentDefinition
from aios.agents.registry import agent_registry
from aios.context.session import session_manager


class AgentIdentityError(Exception):
    """Raised when agent identity isolation is violated."""
    pass


class AgentLoader:
    """Loads agents with strict identity isolation.

    CRITICAL RULE: Each agent is a unique, isolated entity.
    An agent can NEVER simulate or integrate another agent's behavior.
    """

    def __init__(self) -> None:
        self._current_agent: Optional[AgentDefinition] = None

    @property
    def current_agent(self) -> Optional[AgentDefinition]:
        """Get currently loaded agent."""
        return self._current_agent

    @property
    def is_agent_active(self) -> bool:
        """Check if an agent is currently active."""
        return self._current_agent is not None

    def load(self, agent_id: str) -> AgentDefinition:
        """Load an agent by ID.

        Args:
            agent_id: The agent identifier

        Returns:
            The loaded AgentDefinition

        Raises:
            AgentIdentityError: If trying to load while another agent is active
            ValueError: If agent not found
        """
        # CRITICAL: Check for identity isolation violation
        if self._current_agent is not None:
            raise AgentIdentityError(
                f"Cannot load '{agent_id}' while '{self._current_agent.id}' is active. "
                f"Each agent is a unique entity - deactivate first with unload()."
            )

        agent = agent_registry.get(agent_id)
        if agent is None:
            raise ValueError(f"Agent '{agent_id}' not found in registry")

        self._current_agent = agent

        # Persist to session
        if agent.skill_path:
            session_manager.activate_agent(agent_id, agent.skill_path)

        return agent

    def unload(self) -> None:
        """Unload current agent."""
        if self._current_agent is not None:
            session_manager.deactivate_agent()
            self._current_agent = None

    def reload_from_session(self) -> Optional[AgentDefinition]:
        """Reload agent from persisted session state.

        Used for recovery after auto-compact.
        """
        state = session_manager.reload()

        if state.active_agent:
            agent = agent_registry.get(state.active_agent)
            if agent:
                self._current_agent = agent
                return agent

        return None

    def get_agent_prompt(self) -> str:
        """Get system prompt for current agent.

        CRITICAL: The prompt reinforces identity isolation.
        """
        if self._current_agent is None:
            return ""

        agent = self._current_agent

        # Build identity-enforced prompt
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
            f"**Pode fazer:** {', '.join(agent.scope.can) or 'Não especificado'}",
            f"**NÃO pode fazer:** {', '.join(agent.scope.cannot) or 'Nenhuma restrição específica'}",
        ]

        if agent.behavioral_rules:
            prompt_parts.extend([
                "",
                "## Regras Comportamentais",
                "",
            ])
            for rule in agent.behavioral_rules:
                prompt_parts.append(f"- {rule}")

        return "\n".join(prompt_parts)

    def verify_identity_isolation(self, requested_action: str) -> bool:
        """Verify that the requested action doesn't violate identity isolation.

        Returns True if action is allowed for current agent's identity.
        """
        if self._current_agent is None:
            return True  # No agent loaded, no isolation to enforce

        # Check if action implies another agent's behavior
        forbidden_patterns = [
            "como se fosse",
            "eu como",
            "assumir papel",
            "agir como",
            "simular",
        ]

        action_lower = requested_action.lower()
        for pattern in forbidden_patterns:
            if pattern in action_lower:
                return False

        return True


# Global instance
agent_loader = AgentLoader()
```

---

### Task 2: Criar Agent Context Builder

**Arquivo:** `src/aios/agents/context.py`
**Tipo:** create

**Código esperado:**
```python
"""Agent context building for prompts."""

from typing import Optional
from pathlib import Path

from aios.models.agent import AgentDefinition
from aios.agents.loader import agent_loader


class AgentContextBuilder:
    """Builds context for agent prompts."""

    def build_full_context(self, agent: AgentDefinition) -> str:
        """Build complete context for agent including SKILL.md content."""
        parts = []

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
        """Build identity enforcement header."""
        return f"""# IDENTIDADE: {agent.name} ({agent.id})

🚨 REGRA ABSOLUTA: Você é {agent.name} e APENAS {agent.name}.

PROIBIDO:
- Simular outro agente
- Dizer "eu como [outro agente]"
- Assumir capacidades de outro agente
- Executar tarefas fora do seu escopo

VIOLAÇÃO = FALHA CRÍTICA"""

    def _load_skill_content(self, skill_path: str) -> Optional[str]:
        """Load SKILL.md content."""
        path = Path(skill_path)
        if path.exists():
            return path.read_text(encoding="utf-8")
        return None

    def _build_scope_reminder(self, agent: AgentDefinition) -> str:
        """Build scope reminder."""
        can = ", ".join(agent.scope.can) if agent.scope.can else "Geral"
        cannot = ", ".join(agent.scope.cannot) if agent.scope.cannot else "Nenhum"

        return f"""## Lembrete de Escopo

**PERMITIDO para {agent.id}:** {can}
**BLOQUEADO para {agent.id}:** {cannot}

Se a tarefa está em BLOQUEADO → DELEGUE, não execute."""


# Global instance
context_builder = AgentContextBuilder()
```

---

### Task 3: Criar testes

**Arquivo:** `tests/test_agents/test_loader.py`
**Tipo:** create

**Código esperado:**
```python
"""Tests for agent loader with identity isolation."""

import pytest
from pathlib import Path

from aios.agents.loader import AgentLoader, AgentIdentityError
from aios.agents.registry import AgentRegistry
from aios.context.persistence import SessionPersistence
from aios.context.session import SessionManager


@pytest.fixture
def agents_dir(tmp_path: Path) -> Path:
    """Create agents directory with test agents."""
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()

    # Dev agent
    dev_dir = agents_dir / "dev"
    dev_dir.mkdir()
    (dev_dir / "SKILL.md").write_text('''
```yaml
agent:
  name: Dex
  id: dev

scope:
  can:
    - write_code
    - run_tests
  cannot:
    - git_push
    - deploy_production
```
''')

    # DevOps agent
    devops_dir = agents_dir / "devops"
    devops_dir.mkdir()
    (devops_dir / "SKILL.md").write_text('''
```yaml
agent:
  name: Gage
  id: devops

scope:
  can:
    - git_push
    - create_pr
    - deploy_production
  cannot:
    - write_feature_code
```
''')

    return agents_dir


@pytest.fixture
def registry(agents_dir: Path) -> AgentRegistry:
    """Create and load registry."""
    reg = AgentRegistry()
    reg.load_from_directory(agents_dir)
    return reg


@pytest.fixture
def session_file(tmp_path: Path) -> Path:
    return tmp_path / ".aios" / "session-state.json"


@pytest.fixture
def loader(
    registry: AgentRegistry,
    session_file: Path,
    monkeypatch: pytest.MonkeyPatch
) -> AgentLoader:
    """Create agent loader with mocked dependencies."""
    from aios.agents import registry as reg_module
    from aios.context import session as session_module

    # Mock registry
    monkeypatch.setattr(reg_module, "agent_registry", registry)

    # Mock session manager
    persistence = SessionPersistence(session_file)
    manager = SessionManager(persistence)
    monkeypatch.setattr(session_module, "session_manager", manager)

    return AgentLoader()


class TestAgentIdentityIsolation:
    """Tests for CRITICAL identity isolation rule."""

    def test_cannot_load_agent_while_another_active(
        self, loader: AgentLoader
    ) -> None:
        """CRITICAL: Cannot load agent while another is active."""
        loader.load("dev")

        with pytest.raises(AgentIdentityError) as exc_info:
            loader.load("devops")

        assert "unique entity" in str(exc_info.value).lower()
        assert "deactivate" in str(exc_info.value).lower()

    def test_must_unload_before_loading_new(
        self, loader: AgentLoader
    ) -> None:
        """Must explicitly unload before loading different agent."""
        loader.load("dev")
        loader.unload()

        # Now can load different agent
        agent = loader.load("devops")
        assert agent.id == "devops"

    def test_identity_isolation_in_prompt(
        self, loader: AgentLoader
    ) -> None:
        """Agent prompt must enforce identity isolation."""
        loader.load("dev")
        prompt = loader.get_agent_prompt()

        assert "APENAS" in prompt or "apenas" in prompt.lower()
        assert "simular" in prompt.lower()
        assert "Dex" in prompt

    def test_verify_identity_violation_patterns(
        self, loader: AgentLoader
    ) -> None:
        """Detect identity violation patterns."""
        loader.load("dev")

        # These should be detected as violations
        assert loader.verify_identity_isolation("eu como Gage vou fazer push") is False
        assert loader.verify_identity_isolation("vou simular o comportamento do DevOps") is False
        assert loader.verify_identity_isolation("agir como Quinn") is False

        # These should be allowed
        assert loader.verify_identity_isolation("vou escrever código") is True
        assert loader.verify_identity_isolation("rodar os testes") is True


class TestAgentLoader:
    """Tests for agent loader functionality."""

    def test_load_agent(self, loader: AgentLoader) -> None:
        """Test loading an agent."""
        agent = loader.load("dev")

        assert agent.id == "dev"
        assert agent.name == "Dex"
        assert loader.is_agent_active is True

    def test_load_nonexistent_agent(self, loader: AgentLoader) -> None:
        """Test loading non-existent agent."""
        with pytest.raises(ValueError) as exc_info:
            loader.load("nonexistent")

        assert "not found" in str(exc_info.value)

    def test_unload_agent(self, loader: AgentLoader) -> None:
        """Test unloading an agent."""
        loader.load("dev")
        loader.unload()

        assert loader.is_agent_active is False
        assert loader.current_agent is None

    def test_reload_from_session(
        self,
        loader: AgentLoader,
        session_file: Path
    ) -> None:
        """Test reloading agent from persisted session."""
        # Load and persist
        loader.load("dev")

        # Create new loader (simulating restart)
        new_loader = AgentLoader()

        # Reload from session
        agent = new_loader.reload_from_session()

        assert agent is not None
        assert agent.id == "dev"
```

---

## Validação Final

- [ ] Load/unload funciona corretamente
- [ ] Identity isolation é enforçada
- [ ] Prompts reforçam identidade
- [ ] Session persistence funciona
- [ ] Testes com 90%+ coverage

## Notas para Ralph

- **CRÍTICO:** Identity isolation é a regra mais importante
- Nunca permitir carregar agente enquanto outro está ativo
- Prompts devem SEMPRE reforçar a identidade única
- Testar padrões de violação de identidade
