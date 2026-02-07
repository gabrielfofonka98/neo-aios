"""Pipeline state models for dependency-aware story execution."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel
from pydantic import Field


class StoryStatus(StrEnum):
    """Status of a pipeline story."""

    PENDING = "pending"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    DONE = "done"
    BLOCKED = "blocked"
    FAILED = "failed"


class StepStatus(StrEnum):
    """Status of a pipeline step."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class StepRecord(BaseModel, frozen=True):
    """Immutable record of a completed step execution."""

    step_id: str = Field(validation_alias="stepId")
    status: StepStatus
    started_at: datetime | None = Field(default=None, validation_alias="startedAt")
    completed_at: datetime | None = Field(
        default=None, validation_alias="completedAt"
    )
    agent_id: str | None = Field(default=None, validation_alias="agentId")
    model_used: str | None = Field(default=None, validation_alias="modelUsed")
    tokens_used: int = Field(default=0, validation_alias="tokensUsed")
    error: str | None = None

    model_config = {"populate_by_name": True}

    @property
    def duration_ms(self) -> int | None:
        """Duration in milliseconds, or None if not completed."""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return int(delta.total_seconds() * 1000)
        return None


class PipelineStory(BaseModel):
    """A story in the pipeline with dependency tracking."""

    id: str
    name: str
    path: str = ""
    status: StoryStatus = StoryStatus.PENDING
    dependencies: list[str] = Field(default_factory=list)
    blocks: list[str] = Field(default_factory=list)
    steps_completed: list[StepRecord] = Field(
        default_factory=list, validation_alias="stepsCompleted"
    )
    current_step: str | None = Field(default=None, validation_alias="currentStep")
    epic: str | None = None

    model_config = {"populate_by_name": True}


class PipelineState(BaseModel):
    """Top-level pipeline state persisted to JSON."""

    version: str = "1.0"
    project: str = ""
    stories: dict[str, PipelineStory] = Field(default_factory=dict)
    created_at: datetime = Field(
        default_factory=datetime.now, validation_alias="createdAt"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now, validation_alias="updatedAt"
    )
    lock_holder: str | None = Field(default=None, validation_alias="lockHolder")

    model_config = {"populate_by_name": True}
