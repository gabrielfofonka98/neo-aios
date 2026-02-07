"""Tests for step execution models."""

from datetime import datetime
from datetime import timedelta

from aios.pipeline.step_models import StepContext
from aios.pipeline.step_models import StepDefinition
from aios.pipeline.step_models import StepResult


class TestStepDefinition:
    def test_create_minimal(self) -> None:
        step = StepDefinition(id="step-1", agent_id="dev")
        assert step.id == "step-1"
        assert step.agent_id == "dev"
        assert step.model == "sonnet"
        assert step.max_turns == 10
        assert step.token_budget == 15000

    def test_create_with_alias(self) -> None:
        step = StepDefinition(id="step-1", agentId="qa", tokenBudget=5000)
        assert step.agent_id == "qa"
        assert step.token_budget == 5000

    def test_frozen(self) -> None:
        step = StepDefinition(id="step-1", agent_id="dev")
        try:
            step.model = "opus"  # type: ignore[misc]
            msg = "Should not allow mutation"
            raise AssertionError(msg)
        except (AttributeError, TypeError, ValueError):
            pass

    def test_full_definition(self) -> None:
        step = StepDefinition(
            id="code-review",
            agent_id="qa",
            model="opus",
            max_turns=15,
            token_budget=20000,
            timeout_s=600.0,
            description="Deep code review",
        )
        assert step.timeout_s == 600.0
        assert step.description == "Deep code review"


class TestStepContext:
    def test_create_minimal(self) -> None:
        ctx = StepContext(
            step_id="s1",
            story_id="story-1",
            story_path="/path/to/story",
            agent_id="dev",
            model="sonnet",
            token_budget=15000,
        )
        assert ctx.step_id == "s1"
        assert ctx.previous_outputs == []

    def test_create_with_alias(self) -> None:
        ctx = StepContext(
            stepId="s1",
            storyId="story-1",
            storyPath="/path",
            agentId="dev",
            model="opus",
            tokenBudget=25000,
            previousOutputs=["file1.py"],
        )
        assert ctx.step_id == "s1"
        assert ctx.previous_outputs == ["file1.py"]

    def test_frozen(self) -> None:
        ctx = StepContext(
            step_id="s1",
            story_id="story-1",
            story_path="/path",
            agent_id="dev",
            model="sonnet",
            token_budget=15000,
        )
        try:
            ctx.model = "opus"  # type: ignore[misc]
            msg = "Should not allow mutation"
            raise AssertionError(msg)
        except (AttributeError, TypeError, ValueError):
            pass


class TestStepResult:
    def test_create_minimal(self) -> None:
        result = StepResult(step_id="s1")
        assert result.step_id == "s1"
        assert result.status == "completed"
        assert result.is_success is True
        assert result.error is None

    def test_failed_result(self) -> None:
        result = StepResult(
            step_id="s1",
            status="failed",
            error="Something went wrong",
        )
        assert result.is_success is False

    def test_duration_ms(self) -> None:
        start = datetime(2026, 1, 1, 12, 0, 0)
        end = start + timedelta(seconds=3)
        result = StepResult(
            step_id="s1",
            started_at=start,
            completed_at=end,
        )
        assert result.duration_ms == 3000

    def test_duration_ms_none(self) -> None:
        result = StepResult(step_id="s1")
        assert result.duration_ms is None

    def test_full_result(self) -> None:
        now = datetime.now()
        result = StepResult(
            step_id="impl",
            status="completed",
            files_modified=["src/main.py"],
            files_created=["src/new.py"],
            output_summary="Implemented feature X",
            tokens_used=12000,
            model_used="opus",
            started_at=now,
            completed_at=now + timedelta(seconds=30),
        )
        assert len(result.files_modified) == 1
        assert len(result.files_created) == 1
        assert result.tokens_used == 12000
