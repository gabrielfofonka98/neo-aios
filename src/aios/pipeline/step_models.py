"""Step execution models for isolated pipeline steps."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003

from pydantic import BaseModel
from pydantic import Field


class StepDefinition(BaseModel, frozen=True):
    """Immutable definition of a pipeline step from registry."""

    id: str
    agent_id: str = Field(validation_alias="agentId")
    model: str = "sonnet"
    max_turns: int = Field(default=10, validation_alias="maxTurns")
    token_budget: int = Field(default=15000, validation_alias="tokenBudget")
    timeout_s: float = Field(default=300.0, validation_alias="timeoutS")
    description: str = ""

    model_config = {"populate_by_name": True}


class StepContext(BaseModel, frozen=True):
    """Immutable context passed to each isolated step."""

    step_id: str = Field(validation_alias="stepId")
    story_id: str = Field(validation_alias="storyId")
    story_path: str = Field(validation_alias="storyPath")
    agent_id: str = Field(validation_alias="agentId")
    model: str
    token_budget: int = Field(validation_alias="tokenBudget")
    previous_outputs: list[str] = Field(
        default_factory=list, validation_alias="previousOutputs"
    )

    model_config = {"populate_by_name": True}


class StepResult(BaseModel):
    """Result of a single step execution."""

    step_id: str = Field(validation_alias="stepId")
    status: str = "completed"
    files_modified: list[str] = Field(
        default_factory=list, validation_alias="filesModified"
    )
    files_created: list[str] = Field(
        default_factory=list, validation_alias="filesCreated"
    )
    output_summary: str = Field(default="", validation_alias="outputSummary")
    tokens_used: int = Field(default=0, validation_alias="tokensUsed")
    model_used: str = Field(default="", validation_alias="modelUsed")
    started_at: datetime | None = Field(default=None, validation_alias="startedAt")
    completed_at: datetime | None = Field(
        default=None, validation_alias="completedAt"
    )
    error: str | None = None

    model_config = {"populate_by_name": True}

    @property
    def duration_ms(self) -> int | None:
        """Duration in milliseconds, or None if not completed."""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return int(delta.total_seconds() * 1000)
        return None

    @property
    def is_success(self) -> bool:
        """Whether the step completed successfully."""
        return self.status == "completed" and self.error is None
