# Story 1.3: Session Persistence

**Status:** [ ] Pending
**Executor:** Ralph/Dex
**Complexidade:** Média
**Dependência:** Story 1.1

---

## Objetivo

Criar sistema de persistência de sessão que sobrevive auto-compact do Claude Code.

## Tasks

### Task 1: Criar modelo SessionState

**Arquivo:** `src/aios/models/session.py`
**Tipo:** create

**Código esperado:**
```python
"""Session state models."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ProjectContext(BaseModel):
    """Current project context."""

    project: Optional[str] = None
    epic: Optional[str] = None
    story: Optional[str] = None


class SessionState(BaseModel):
    """Persistent session state that survives auto-compact."""

    # Active agent
    active_agent: Optional[str] = Field(default=None, alias="activeAgent")
    agent_file: Optional[str] = Field(default=None, alias="agentFile")

    # Timestamps
    activated_at: Optional[datetime] = Field(default=None, alias="activatedAt")
    last_activity: Optional[datetime] = Field(default=None, alias="lastActivity")

    # Current work
    current_task: Optional[str] = Field(default=None, alias="currentTask")
    project_context: ProjectContext = Field(
        default_factory=ProjectContext,
        alias="projectContext"
    )

    class Config:
        populate_by_name = True

    def is_agent_active(self) -> bool:
        """Check if an agent is currently active."""
        return self.active_agent is not None

    def activate_agent(self, agent_id: str, agent_file: str) -> None:
        """Activate an agent."""
        self.active_agent = agent_id
        self.agent_file = agent_file
        self.activated_at = datetime.now()
        self.last_activity = datetime.now()

    def deactivate_agent(self) -> None:
        """Deactivate current agent."""
        self.active_agent = None
        self.agent_file = None
        self.activated_at = None
        self.current_task = None

    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.now()

    def set_task(self, task: Optional[str]) -> None:
        """Set current task."""
        self.current_task = task
        self.update_activity()
```

**Acceptance Criteria:**
- [ ] Modelo criado com aliases JSON (camelCase)
- [ ] Métodos de ativação/desativação funcionando
- [ ] Serialização JSON funciona

---

### Task 2: Criar Session Persistence

**Arquivo:** `src/aios/context/persistence.py`
**Tipo:** create

**Código esperado:**
```python
"""Session persistence to survive auto-compact."""

import json
from pathlib import Path
from typing import Optional

from aios.models.session import SessionState


class SessionPersistence:
    """Handles reading and writing session state to disk."""

    DEFAULT_PATH = Path(".aios/session-state.json")

    def __init__(self, file_path: Optional[Path] = None) -> None:
        self.file_path = file_path or self.DEFAULT_PATH

    def load(self) -> SessionState:
        """Load session state from file. Returns empty state if not found."""
        if not self.file_path.exists():
            return SessionState()

        try:
            content = self.file_path.read_text(encoding="utf-8")
            data = json.loads(content)
            return SessionState(**data)
        except (json.JSONDecodeError, Exception):
            return SessionState()

    def save(self, state: SessionState) -> bool:
        """Save session state to file. Returns True on success."""
        try:
            # Ensure directory exists
            self.file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write with pretty formatting
            content = state.model_dump_json(
                by_alias=True,
                indent=2,
                exclude_none=False
            )
            self.file_path.write_text(content, encoding="utf-8")
            return True
        except Exception:
            return False

    def clear(self) -> bool:
        """Clear session state (delete file)."""
        try:
            if self.file_path.exists():
                self.file_path.unlink()
            return True
        except Exception:
            return False

    def exists(self) -> bool:
        """Check if session file exists."""
        return self.file_path.exists()


# Default instance
session_persistence = SessionPersistence()
```

**Acceptance Criteria:**
- [ ] Load funciona com arquivo existente
- [ ] Load retorna estado vazio se arquivo não existe
- [ ] Save cria diretório se necessário
- [ ] JSON usa camelCase (por_alias=True)

---

### Task 3: Criar Session Manager

**Arquivo:** `src/aios/context/session.py`
**Tipo:** create

**Código esperado:**
```python
"""Session management for agent context."""

from typing import Optional

from aios.models.session import SessionState
from aios.context.persistence import SessionPersistence, session_persistence


class SessionManager:
    """Manages the current session state."""

    def __init__(self, persistence: Optional[SessionPersistence] = None) -> None:
        self._persistence = persistence or session_persistence
        self._state: Optional[SessionState] = None

    @property
    def state(self) -> SessionState:
        """Get current session state, loading from disk if needed."""
        if self._state is None:
            self._state = self._persistence.load()
        return self._state

    def reload(self) -> SessionState:
        """Force reload from disk."""
        self._state = self._persistence.load()
        return self._state

    def save(self) -> bool:
        """Save current state to disk."""
        if self._state is None:
            return False
        return self._persistence.save(self._state)

    def activate_agent(self, agent_id: str, agent_file: str) -> bool:
        """Activate an agent and persist."""
        self.state.activate_agent(agent_id, agent_file)
        return self.save()

    def deactivate_agent(self) -> bool:
        """Deactivate current agent and persist."""
        self.state.deactivate_agent()
        return self.save()

    def update_activity(self) -> bool:
        """Update last activity timestamp and persist."""
        self.state.update_activity()
        return self.save()

    def set_task(self, task: Optional[str]) -> bool:
        """Set current task and persist."""
        self.state.set_task(task)
        return self.save()

    @property
    def active_agent(self) -> Optional[str]:
        """Get currently active agent ID."""
        return self.state.active_agent

    @property
    def is_agent_active(self) -> bool:
        """Check if an agent is active."""
        return self.state.is_agent_active()

    def clear(self) -> bool:
        """Clear session state."""
        self._state = SessionState()
        return self._persistence.clear()


# Global session manager
session_manager = SessionManager()
```

---

### Task 4: Criar testes

**Arquivo:** `tests/test_context/test_session.py`
**Tipo:** create

**Código esperado:**
```python
"""Tests for session management."""

import pytest
from pathlib import Path

from aios.models.session import SessionState
from aios.context.persistence import SessionPersistence
from aios.context.session import SessionManager


@pytest.fixture
def session_file(tmp_path: Path) -> Path:
    return tmp_path / ".aios" / "session-state.json"


@pytest.fixture
def persistence(session_file: Path) -> SessionPersistence:
    return SessionPersistence(session_file)


@pytest.fixture
def manager(persistence: SessionPersistence) -> SessionManager:
    return SessionManager(persistence)


class TestSessionState:
    def test_activate_agent(self) -> None:
        state = SessionState()
        state.activate_agent("dev", "agents/dex/SKILL.md")

        assert state.active_agent == "dev"
        assert state.agent_file == "agents/dex/SKILL.md"
        assert state.activated_at is not None
        assert state.is_agent_active() is True

    def test_deactivate_agent(self) -> None:
        state = SessionState()
        state.activate_agent("dev", "agents/dex/SKILL.md")
        state.deactivate_agent()

        assert state.active_agent is None
        assert state.is_agent_active() is False


class TestSessionPersistence:
    def test_save_and_load(self, persistence: SessionPersistence) -> None:
        state = SessionState()
        state.activate_agent("dev", "agents/dex/SKILL.md")

        assert persistence.save(state) is True
        assert persistence.exists() is True

        loaded = persistence.load()
        assert loaded.active_agent == "dev"

    def test_load_nonexistent(self, persistence: SessionPersistence) -> None:
        state = persistence.load()
        assert state.active_agent is None

    def test_clear(self, persistence: SessionPersistence) -> None:
        state = SessionState()
        state.activate_agent("dev", "test")
        persistence.save(state)

        assert persistence.clear() is True
        assert persistence.exists() is False


class TestSessionManager:
    def test_activate_and_save(self, manager: SessionManager) -> None:
        result = manager.activate_agent("dev", "agents/dex/SKILL.md")

        assert result is True
        assert manager.active_agent == "dev"
        assert manager.is_agent_active is True

    def test_reload_persisted_state(
        self,
        manager: SessionManager,
        persistence: SessionPersistence
    ) -> None:
        manager.activate_agent("architect", "agents/aria/SKILL.md")

        # Create new manager with same persistence
        new_manager = SessionManager(persistence)
        assert new_manager.active_agent == "architect"

    def test_deactivate(self, manager: SessionManager) -> None:
        manager.activate_agent("dev", "test")
        manager.deactivate_agent()

        assert manager.active_agent is None
        assert manager.is_agent_active is False
```

---

## Validação Final

- [ ] Session persiste entre restarts
- [ ] JSON usa camelCase para compatibilidade
- [ ] Testes com 90%+ coverage
- [ ] Funciona com .aios/session-state.json real

## Notas para Ralph

- Arquivo deve ser `.aios/session-state.json` (padrão do CLAUDE.md)
- Usar camelCase no JSON (alias do Pydantic)
- Criar diretório .aios se não existir
- Graceful handling se arquivo corrompido
