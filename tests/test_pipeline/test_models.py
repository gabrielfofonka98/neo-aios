"""Tests for pipeline models."""

from datetime import datetime
from datetime import timedelta

from aios.pipeline.models import PipelineState
from aios.pipeline.models import PipelineStory
from aios.pipeline.models import StepRecord
from aios.pipeline.models import StepStatus
from aios.pipeline.models import StoryStatus


class TestStoryStatus:
    def test_all_statuses_exist(self) -> None:
        expected = {"pending", "ready", "in_progress", "in_review", "done", "blocked", "failed"}
        assert {s.value for s in StoryStatus} == expected

    def test_str_enum_values(self) -> None:
        assert StoryStatus.PENDING == "pending"
        assert StoryStatus.DONE == "done"


class TestStepStatus:
    def test_all_statuses_exist(self) -> None:
        expected = {"pending", "in_progress", "completed", "failed", "skipped"}
        assert {s.value for s in StepStatus} == expected


class TestStepRecord:
    def test_create_minimal(self) -> None:
        record = StepRecord(step_id="step-1", status=StepStatus.COMPLETED)
        assert record.step_id == "step-1"
        assert record.status == StepStatus.COMPLETED
        assert record.tokens_used == 0
        assert record.error is None

    def test_create_with_alias(self) -> None:
        record = StepRecord(stepId="step-1", status=StepStatus.COMPLETED)
        assert record.step_id == "step-1"

    def test_frozen(self) -> None:
        record = StepRecord(step_id="step-1", status=StepStatus.COMPLETED)
        try:
            record.step_id = "other"  # type: ignore[misc]
            msg = "Should not allow mutation"
            raise AssertionError(msg)
        except (AttributeError, TypeError, ValueError):
            pass

    def test_duration_ms(self) -> None:
        start = datetime(2026, 1, 1, 12, 0, 0)
        end = start + timedelta(seconds=5)
        record = StepRecord(
            step_id="s1",
            status=StepStatus.COMPLETED,
            started_at=start,
            completed_at=end,
        )
        assert record.duration_ms == 5000

    def test_duration_ms_none_when_incomplete(self) -> None:
        record = StepRecord(step_id="s1", status=StepStatus.IN_PROGRESS)
        assert record.duration_ms is None

    def test_full_record(self) -> None:
        now = datetime.now()
        record = StepRecord(
            step_id="impl",
            status=StepStatus.COMPLETED,
            started_at=now,
            completed_at=now + timedelta(seconds=10),
            agent_id="dev",
            model_used="opus",
            tokens_used=15000,
        )
        assert record.agent_id == "dev"
        assert record.model_used == "opus"
        assert record.tokens_used == 15000


class TestPipelineStory:
    def test_create_minimal(self) -> None:
        story = PipelineStory(id="s1", name="Story 1")
        assert story.status == StoryStatus.PENDING
        assert story.dependencies == []
        assert story.blocks == []
        assert story.steps_completed == []
        assert story.current_step is None

    def test_with_dependencies(self) -> None:
        story = PipelineStory(
            id="s2",
            name="Story 2",
            dependencies=["s1"],
            blocks=["s3"],
            epic="auth",
        )
        assert story.dependencies == ["s1"]
        assert story.blocks == ["s3"]
        assert story.epic == "auth"

    def test_status_mutation(self) -> None:
        story = PipelineStory(id="s1", name="Story 1")
        story.status = StoryStatus.IN_PROGRESS
        assert story.status == StoryStatus.IN_PROGRESS


class TestPipelineState:
    def test_create_empty(self) -> None:
        state = PipelineState()
        assert state.version == "1.0"
        assert state.stories == {}
        assert state.lock_holder is None

    def test_with_stories(self) -> None:
        story = PipelineStory(id="s1", name="S1")
        state = PipelineState(
            project="my-project",
            stories={"s1": story},
        )
        assert state.project == "my-project"
        assert "s1" in state.stories
        assert state.stories["s1"].name == "S1"

    def test_camel_case_alias(self) -> None:
        state = PipelineState(lockHolder="agent-1")
        assert state.lock_holder == "agent-1"
