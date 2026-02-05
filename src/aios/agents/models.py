"""Agent data models.

Defines the core data structures for agents, scopes, and hierarchy.
"""

from enum import StrEnum
from pathlib import Path
from typing import Self

from pydantic import BaseModel
from pydantic import Field


class AgentTier(StrEnum):
    """Agent hierarchy tier."""

    C_LEVEL = "c-level"
    VP = "vp"
    DIRECTOR = "director"
    MANAGER = "manager"
    IC = "ic"

    @property
    def level(self) -> int:
        """Return numeric level (0 = highest, 4 = lowest)."""
        levels = {
            self.C_LEVEL: 0,
            self.VP: 1,
            self.DIRECTOR: 2,
            self.MANAGER: 3,
            self.IC: 4,
        }
        return levels[self]

    def can_delegate_to(self, other: Self) -> bool:
        """Check if this tier can delegate to another."""
        return other.level > self.level


class AgentLevel(StrEnum):
    """Agent level within tier."""

    EXECUTIVE = "executive"
    CORE = "core"
    SECURITY = "security"
    SPECIALIST = "specialist"
    CONTENT = "content"
    AUTOMATION = "automation"


class AgentScope(BaseModel):
    """Agent permission scope."""

    can: list[str] = Field(default_factory=list, description="Allowed actions")
    cannot: list[str] = Field(default_factory=list, description="Forbidden actions")

    def allows(self, action: str) -> bool:
        """Check if action is allowed."""
        if action in self.cannot:
            return False
        return action in self.can or not self.can

    def forbids(self, action: str) -> bool:
        """Check if action is forbidden."""
        return action in self.cannot


class AgentHierarchy(BaseModel):
    """Agent hierarchy relationships."""

    tier: AgentTier
    reports_to: str | None = None
    approves: list[str] = Field(default_factory=list)
    delegates_to: list[str] = Field(default_factory=list)
    collaborates_with: list[str] = Field(default_factory=list)


class AgentDefinition(BaseModel):
    """Complete agent definition."""

    # Identity
    name: str = Field(..., description="Human-readable name")
    id: str = Field(..., description="Unique identifier")
    tier: AgentTier = Field(..., description="Hierarchy tier")
    level: AgentLevel = Field(default=AgentLevel.CORE, description="Level within tier")
    title: str = Field(..., description="Job title")
    icon: str = Field(default="🤖", description="Agent icon")

    # Capabilities
    scope: AgentScope = Field(default_factory=AgentScope, description="Permission scope")
    hierarchy: AgentHierarchy | None = None

    # Metadata
    skill_path: Path | None = None
    when_to_use: str = ""

    model_config = {"frozen": True}

    def can_do(self, action: str) -> bool:
        """Check if agent can perform action."""
        return self.scope.allows(action)

    def cannot_do(self, action: str) -> bool:
        """Check if agent is forbidden from action."""
        return self.scope.forbids(action)

    def can_delegate_to(self, other: "AgentDefinition") -> bool:
        """Check if this agent can delegate to another."""
        return self.tier.can_delegate_to(other.tier)
