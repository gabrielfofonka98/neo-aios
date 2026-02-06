"""Models for the Incremental Development System (IDS)."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel
from pydantic import Field


class IDSAction(StrEnum):
    """IDS recommended action."""

    REUSE = "reuse"
    ADAPT = "adapt"
    CREATE = "create"


class IDSMatch(BaseModel):
    """A similarity match found by IDS."""

    path: str
    similarity: float = Field(ge=0.0, le=1.0)
    match_type: str  # "filename", "module_path", "structural"
    reason: str = ""


class IDSDecision(BaseModel):
    """IDS analysis decision."""

    action: IDSAction
    target_path: str
    matches: list[IDSMatch] = Field(default_factory=list)
    reason: str = ""

    @property
    def best_match(self) -> IDSMatch | None:
        if not self.matches:
            return None
        return max(self.matches, key=lambda m: m.similarity)


class IDSStats(BaseModel):
    """IDS tracking statistics."""

    total_checks: int = 0
    reuse_count: int = 0
    adapt_count: int = 0
    create_count: int = 0
    last_updated: datetime = Field(default_factory=datetime.now)

    @property
    def create_rate(self) -> float:
        if self.total_checks == 0:
            return 0.0
        return self.create_count / self.total_checks

    def record(self, action: IDSAction) -> None:
        self.total_checks += 1
        if action == IDSAction.REUSE:
            self.reuse_count += 1
        elif action == IDSAction.ADAPT:
            self.adapt_count += 1
        else:
            self.create_count += 1
        self.last_updated = datetime.now()
