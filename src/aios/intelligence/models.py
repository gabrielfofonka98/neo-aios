"""Models for LLM routing and task classification."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel
from pydantic import Field


class TaskComplexity(StrEnum):
    """Task complexity levels mapping to model tiers."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    MAX = "max"


class RoutingDecision(BaseModel):
    """Result of routing classification."""

    complexity: TaskComplexity
    model: str
    agent_id: str | None = None
    reason: str = ""
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)

    @property
    def model_tier(self) -> str:
        """Human-readable model tier."""
        tier_map: dict[str, str] = {
            "haiku": "Haiku (fast/cheap)",
            "sonnet": "Sonnet (balanced)",
            "opus": "Opus (max quality)",
        }
        return tier_map.get(self.model, self.model)
