"""Models for persistent memory layer."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel
from pydantic import Field


class MemoryType(StrEnum):
    """Types of memories."""

    INCIDENT = "incident"
    RULE = "rule"
    DECISION = "decision"
    PATTERN = "pattern"
    LESSON = "lesson"


class MemoryPriority(StrEnum):
    """Memory priority levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Memory(BaseModel):
    """A single memory entry."""

    id: str
    content: str
    memory_type: MemoryType
    priority: MemoryPriority = MemoryPriority.MEDIUM
    tags: list[str] = Field(default_factory=list)
    agent_id: str | None = None
    project: str | None = None
    epic: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: datetime | None = None
    access_count: int = 0

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at


class MemoryDigest(BaseModel):
    """Summary of memories from a session."""

    session_id: str
    memories: list[Memory] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)

    @property
    def count(self) -> int:
        return len(self.memories)

    def by_type(self, memory_type: MemoryType) -> list[Memory]:
        return [m for m in self.memories if m.memory_type == memory_type]
