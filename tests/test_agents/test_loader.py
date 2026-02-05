"""Tests for agent loader with identity isolation."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from aios.agents.loader import (
    AgentContextBuilder,
    AgentIdentityError,
    AgentLoader,
    AgentNotFoundError,
)
from aios.agents.registry import AgentRegistry
from aios.context.session import Session

if TYPE_CHECKING:
    pass


@pytest.fixture
def agents_dir(tmp_path: Path) -> Path:
    """Create agents directory with test agents."""
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()

    # Create tier directory
    ic_dir = agents_dir / "ic"
    ic_dir.mkdir()

    # Dev agent
    dev_dir = ic_dir / "dev"
    dev_dir.mkdir()
    (dev_dir / "SKILL.md").write_text(
        """# Dev Agent

```yaml
agent:
  name: Dex
  id: dev
  tier: ic
  title: Full Stack Developer

scope:
  can:
    - write_code
    - run_tests
    - debug
  cannot:
    - git_push
    - deploy_production
```
"""
    )

    # DevOps agent
    devops_dir = ic_dir / "devops"
    devops_dir.mkdir()
    (devops_dir / "SKILL.md").write_text(
        """# DevOps Agent

```yaml
agent:
  name: Gage
  id: devops
  tier: ic
  title: DevOps Engineer

scope:
  can:
    - git_push
    - create_pr
    - deploy_production
  cannot:
    - write_feature_code
```
"""
    )

    return agents_dir


@pytest.fixture
def registry(agents_dir: Path) -> AgentRegistry:
    """Create and load registry."""
    return AgentRegistry.load(agents_dir)


@pytest.fixture
def session_file(tmp_path: Path) -> Path:
    """Create session file path."""
    return tmp_path / ".aios" / "session-state.json"


@pytest.fixture
def session(session_file: Path) -> Session:
    """Create session manager."""
    return Session.load(session_file)


@pytest.fixture
def loader(registry: AgentRegistry, session: Session) -> AgentLoader:
    """Create agent loader."""
    return AgentLoader(registry, session)


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

    def test_error_contains_both_agent_ids(self, loader: AgentLoader) -> None:
        """Error should contain both current and requested agent IDs."""
        loader.load("dev")

        with pytest.raises(AgentIdentityError) as exc_info:
            loader.load("devops")

        error = exc_info.value
        assert error.current_agent == "dev"
        assert error.requested_agent == "devops"

    def test_must_unload_before_loading_new(self, loader: AgentLoader) -> None:
        """Must explicitly unload before loading different agent."""
        loader.load("dev")
        loader.unload()

        # Now can load different agent
        agent = loader.load("devops")
        assert agent.id == "devops"

    def test_identity_isolation_in_prompt(self, loader: AgentLoader) -> None:
        """Agent prompt must enforce identity isolation."""
        loader.load("dev")
        prompt = loader.get_agent_prompt()

        assert "APENAS" in prompt
        assert "simular" in prompt.lower()
        assert "Dex" in prompt

    def test_verify_identity_violation_patterns(self, loader: AgentLoader) -> None:
        """Detect identity violation patterns."""
        loader.load("dev")

        # These should be detected as violations
        assert loader.verify_identity_isolation("eu como Gage vou fazer push") is False
        assert (
            loader.verify_identity_isolation("vou simular o comportamento do DevOps")
            is False
        )
        assert loader.verify_identity_isolation("agir como Quinn") is False
        assert loader.verify_identity_isolation("como se fosse o arquiteto") is False
        assert loader.verify_identity_isolation("fingir que sou outro agente") is False

        # These should be allowed
        assert loader.verify_identity_isolation("vou escrever código") is True
        assert loader.verify_identity_isolation("rodar os testes") is True

    def test_verify_returns_true_when_no_agent(self, loader: AgentLoader) -> None:
        """When no agent is loaded, all actions are allowed."""
        # No agent loaded
        assert loader.verify_identity_isolation("qualquer ação") is True
        assert loader.verify_identity_isolation("eu como Gage") is True


class TestAgentLoader:
    """Tests for agent loader functionality."""

    def test_load_agent(self, loader: AgentLoader) -> None:
        """Test loading an agent."""
        agent = loader.load("dev")

        assert agent.id == "dev"
        assert agent.name == "Dex"
        assert loader.is_agent_active is True

    def test_current_agent_property(self, loader: AgentLoader) -> None:
        """Test current_agent property."""
        assert loader.current_agent is None

        loader.load("dev")
        assert loader.current_agent is not None
        assert loader.current_agent.id == "dev"

    def test_load_nonexistent_agent(self, loader: AgentLoader) -> None:
        """Test loading non-existent agent."""
        with pytest.raises(AgentNotFoundError) as exc_info:
            loader.load("nonexistent")

        assert "not found" in str(exc_info.value)
        assert exc_info.value.agent_id == "nonexistent"

    def test_unload_agent(self, loader: AgentLoader) -> None:
        """Test unloading an agent."""
        loader.load("dev")
        loader.unload()

        assert loader.is_agent_active is False
        assert loader.current_agent is None

    def test_unload_when_no_agent(self, loader: AgentLoader) -> None:
        """Unload should be safe when no agent is loaded."""
        # Should not raise
        loader.unload()
        assert loader.current_agent is None

    def test_reload_from_session(
        self,
        registry: AgentRegistry,
        session: Session,
    ) -> None:
        """Test reloading agent from persisted session."""
        # Load and persist
        loader1 = AgentLoader(registry, session)
        loader1.load("dev")

        # Create new loader (simulating restart)
        # Note: need to reload session from file to simulate restart
        reloaded_session = Session.load(session.state_file)
        loader2 = AgentLoader(registry, reloaded_session)

        # Reload from session
        agent = loader2.reload_from_session()

        assert agent is not None
        assert agent.id == "dev"
        assert loader2.is_agent_active is True

    def test_reload_returns_none_when_no_agent(
        self,
        registry: AgentRegistry,
        session: Session,
    ) -> None:
        """Reload should return None when no agent was active."""
        loader = AgentLoader(registry, session)

        agent = loader.reload_from_session()

        assert agent is None
        assert loader.is_agent_active is False

    def test_reload_clears_stale_session(
        self,
        registry: AgentRegistry,
        session: Session,
    ) -> None:
        """Reload should clear session if agent not in registry."""
        # Manually set a non-existent agent in session
        session.activate_agent("nonexistent", "/fake/path")
        session.save()

        loader = AgentLoader(registry, session)
        agent = loader.reload_from_session()

        assert agent is None
        # Session should be cleared
        reloaded_session = Session.load(session.state_file)
        assert reloaded_session.state.active_agent is None


class TestAgentPrompt:
    """Tests for agent prompt generation."""

    def test_prompt_empty_when_no_agent(self, loader: AgentLoader) -> None:
        """Prompt should be empty when no agent is loaded."""
        prompt = loader.get_agent_prompt()
        assert prompt == ""

    def test_prompt_contains_agent_name(self, loader: AgentLoader) -> None:
        """Prompt should contain agent name."""
        loader.load("dev")
        prompt = loader.get_agent_prompt()

        assert "Dex" in prompt
        assert "dev" in prompt

    def test_prompt_contains_scope(self, loader: AgentLoader) -> None:
        """Prompt should contain scope information."""
        loader.load("dev")
        prompt = loader.get_agent_prompt()

        assert "write_code" in prompt
        assert "git_push" in prompt

    def test_prompt_contains_identity_rules(self, loader: AgentLoader) -> None:
        """Prompt should contain identity isolation rules."""
        loader.load("dev")
        prompt = loader.get_agent_prompt()

        assert "IDENTIDADE ISOLADA" in prompt or "APENAS" in prompt
        assert "DELEGUE" in prompt


class TestAgentContextBuilder:
    """Tests for AgentContextBuilder."""

    def test_build_full_context(
        self, registry: AgentRegistry, agents_dir: Path
    ) -> None:
        """Test building full context for agent."""
        agent = registry.get("dev")
        assert agent is not None

        builder = AgentContextBuilder()
        context = builder.build_full_context(agent)

        assert "IDENTIDADE" in context
        assert "Dex" in context
        assert agent.id in context

    def test_identity_header_format(self, registry: AgentRegistry) -> None:
        """Test identity header format."""
        agent = registry.get("dev")
        assert agent is not None

        builder = AgentContextBuilder()
        header = builder._build_identity_header(agent)

        assert "REGRA ABSOLUTA" in header
        assert "APENAS" in header
        assert "PROIBIDO" in header
        assert "FALHA CRÍTICA" in header

    def test_scope_reminder_format(self, registry: AgentRegistry) -> None:
        """Test scope reminder format."""
        agent = registry.get("dev")
        assert agent is not None

        builder = AgentContextBuilder()
        reminder = builder._build_scope_reminder(agent)

        assert "PERMITIDO" in reminder
        assert "BLOQUEADO" in reminder
        assert "DELEGUE" in reminder

    def test_skill_content_loaded(
        self, registry: AgentRegistry, agents_dir: Path
    ) -> None:
        """Test that SKILL.md content is loaded."""
        agent = registry.get("dev")
        assert agent is not None
        assert agent.skill_path is not None

        builder = AgentContextBuilder()
        content = builder._load_skill_content(agent.skill_path)

        assert content is not None
        assert "Dev Agent" in content

    def test_skill_content_none_for_missing_file(self) -> None:
        """Test that missing file returns None."""
        builder = AgentContextBuilder()
        content = builder._load_skill_content(Path("/nonexistent/path/SKILL.md"))

        assert content is None


class TestSessionPersistence:
    """Tests for session persistence integration."""

    def test_load_persists_to_session(
        self,
        registry: AgentRegistry,
        session: Session,
        session_file: Path,
    ) -> None:
        """Loading agent should persist to session file."""
        loader = AgentLoader(registry, session)
        loader.load("dev")

        # Read session file directly
        reloaded = Session.load(session_file)
        assert reloaded.state.active_agent == "dev"

    def test_unload_clears_session(
        self,
        registry: AgentRegistry,
        session: Session,
        session_file: Path,
    ) -> None:
        """Unloading agent should clear session file."""
        loader = AgentLoader(registry, session)
        loader.load("dev")
        loader.unload()

        # Read session file directly
        reloaded = Session.load(session_file)
        assert reloaded.state.active_agent is None
