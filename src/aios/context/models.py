"""Models for context loading."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel
from pydantic import Field


class ContextCategory(StrEnum):
    """Category of context query."""

    IDENTITY = "identity"
    BACKLOG = "backlog"
    ARCHITECTURE = "architecture"
    SESSION = "session"
    AGENT = "agent"
    PROJECT = "project"
    FULL = "full"


class ContextRule(BaseModel):
    """Rule for context matching."""

    category: ContextCategory
    keywords: list[str]
    files: list[str]
    max_tokens: int = 5000
    description: str = ""


class ContextPayload(BaseModel):
    """Loaded context payload."""

    category: ContextCategory
    files_loaded: list[str] = Field(default_factory=list)
    content: str = ""
    token_estimate: int = 0
    deterministic: bool = True

    @property
    def file_count(self) -> int:
        return len(self.files_loaded)
