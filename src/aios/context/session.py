"""Session management.

Handles session state persistence that survives Claude Code auto-compact.
"""

import json
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel
from pydantic import Field


class ProjectContext(BaseModel):
    """Project context within session."""

    project: str | None = None
    epic: str | None = None
    story: str | None = None


class SessionState(BaseModel):
    """Session state that persists to file.

    This state survives Claude Code's automatic context compaction.
    It's read at the start of every turn to recover agent context.
    """

    active_agent: str | None = Field(default=None, alias="activeAgent")
    agent_file: str | None = Field(default=None, alias="agentFile")
    activated_at: datetime | None = Field(default=None, alias="activatedAt")
    last_activity: datetime | None = Field(default=None, alias="lastActivity")
    current_task: str | None = Field(default=None, alias="currentTask")
    project_context: ProjectContext = Field(
        default_factory=ProjectContext, alias="projectContext"
    )

    model_config = {
        "populate_by_name": True,
        "json_encoders": {datetime: lambda v: v.isoformat() if v else None},
    }

    def __init__(self, **data: object) -> None:
        """Initialize with support for both alias and field names."""
        super().__init__(**data)


class Session:
    """Session manager for NEO-AIOS.

    Handles reading and writing session state to ensure agent context
    survives Claude Code's automatic context compaction.

    Example:
        >>> session = Session.load()
        >>> session.activate_agent("dev", ".claude/skills/dev/SKILL.md")
        >>> session.save()

        # After auto-compact, on next turn:
        >>> session = Session.load()
        >>> session.state.active_agent
        'dev'
    """

    DEFAULT_STATE_FILE = Path(".aios/session-state.json")

    def __init__(
        self, state: SessionState | None = None, state_file: Path | None = None
    ) -> None:
        """Initialize session.

        Args:
            state: Initial state (defaults to empty).
            state_file: Path to state file (defaults to .aios/session-state.json).
        """
        self.state = state or SessionState()
        self.state_file = state_file or self.DEFAULT_STATE_FILE

    @classmethod
    def load(cls, state_file: Path | None = None) -> "Session":
        """Load session from file.

        Args:
            state_file: Path to state file.

        Returns:
            Session instance with loaded state.
        """
        file_path = state_file or cls.DEFAULT_STATE_FILE

        if not file_path.exists():
            # Create default state file
            file_path.parent.mkdir(parents=True, exist_ok=True)
            session = cls(state_file=file_path)
            session.save()
            return session

        try:
            data = json.loads(file_path.read_text())
            state = SessionState(**data)
            return cls(state=state, state_file=file_path)
        except (json.JSONDecodeError, ValueError):
            # Corrupted file, reset
            return cls(state_file=file_path)

    def save(self) -> None:
        """Save session state to file."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict with camelCase keys
        data = {
            "activeAgent": self.state.active_agent,
            "agentFile": self.state.agent_file,
            "activatedAt": (
                self.state.activated_at.isoformat() if self.state.activated_at else None
            ),
            "lastActivity": (
                self.state.last_activity.isoformat()
                if self.state.last_activity
                else None
            ),
            "currentTask": self.state.current_task,
            "projectContext": {
                "project": self.state.project_context.project,
                "epic": self.state.project_context.epic,
                "story": self.state.project_context.story,
            },
        }

        self.state_file.write_text(json.dumps(data, indent=2))

    def activate_agent(self, agent_id: str, agent_file: str) -> None:
        """Activate an agent.

        Args:
            agent_id: Agent's unique identifier.
            agent_file: Path to agent's SKILL.md file.
        """
        now = datetime.now()
        self.state.active_agent = agent_id
        self.state.agent_file = agent_file
        self.state.activated_at = now
        self.state.last_activity = now

    def deactivate_agent(self) -> None:
        """Deactivate current agent."""
        self.state.active_agent = None
        self.state.agent_file = None
        self.state.activated_at = None
        self.state.current_task = None

    def update_activity(self, task: str | None = None) -> None:
        """Update last activity timestamp.

        Args:
            task: Optional current task description.
        """
        self.state.last_activity = datetime.now()
        if task is not None:
            self.state.current_task = task

    def set_project_context(
        self,
        project: str | None = None,
        epic: str | None = None,
        story: str | None = None,
    ) -> None:
        """Set project context.

        Args:
            project: Project name.
            epic: Epic name.
            story: Story name.
        """
        if project is not None:
            self.state.project_context.project = project
        if epic is not None:
            self.state.project_context.epic = epic
        if story is not None:
            self.state.project_context.story = story

    @property
    def is_agent_active(self) -> bool:
        """Check if an agent is currently active."""
        return self.state.active_agent is not None

    @property
    def active_agent_id(self) -> str | None:
        """Get the active agent's ID."""
        return self.state.active_agent
