"""Tests for StepExecutor."""

from __future__ import annotations

import json
from datetime import datetime
from datetime import timedelta
from pathlib import Path

from aios.pipeline.executor import StepExecutor
from aios.pipeline.manager import PipelineManager
from aios.pipeline.models import PipelineStory
from aios.pipeline.models import StepStatus
from aios.pipeline.models import StoryStatus
from aios.pipeline.step_models import StepContext
from aios.pipeline.step_models import StepDefinition
from aios.pipeline.step_models import StepResult


class DummyRunner:
    """Test runner that returns configurable results."""

    def __init__(self, results: list[StepResult] | None = None) -> None:
        self.calls: list[tuple[StepContext, StepDefinition]] = []
        self._results = results or []
        self._call_idx = 0

    def run(self, context: StepContext, definition: StepDefinition) -> StepResult:
        self.calls.append((context, definition))
        if self._call_idx < len(self._results):
            result = self._results[self._call_idx]
            self._call_idx += 1
            return result
        self._call_idx += 1
        return StepResult(
            step_id=definition.id,
            status="completed",
            files_modified=[f"src/{definition.id}.py"],
            tokens_used=1000,
            model_used=definition.model,
            started_at=datetime.now(),
            completed_at=datetime.now() + timedelta(seconds=1),
        )


class FailingRunner:
    """Test runner that raises exceptions."""

    def run(self, context: StepContext, definition: StepDefinition) -> StepResult:
        msg = "Runner exploded"
        raise RuntimeError(msg)


def _make_steps(count: int = 3) -> list[StepDefinition]:
    models = ["haiku", "sonnet", "opus"]
    return [
        StepDefinition(
            id=f"step-{i}",
            agent_id="dev",
            model=models[i % len(models)],
            token_budget=10000,
        )
        for i in range(count)
    ]


class TestStepExecutor:
    def _setup_manager(self, tmp_path: Path) -> PipelineManager:
        state_file = tmp_path / "pipeline-state.json"
        manager = PipelineManager(state_file=state_file)
        manager.load()
        manager.add_story(PipelineStory(id="story-1", name="Test Story"))
        manager.save()
        return manager

    def test_execute_all_steps_success(self, tmp_path: Path) -> None:
        manager = self._setup_manager(tmp_path)
        runner = DummyRunner()
        executor = StepExecutor(manager, runner)

        steps = _make_steps(3)
        results = executor.execute_story("story-1", steps)

        assert len(results) == 3
        assert all(r.is_success for r in results)
        assert len(runner.calls) == 3
        assert manager.state.stories["story-1"].status == StoryStatus.IN_REVIEW

    def test_execute_checkpoints_after_each_step(self, tmp_path: Path) -> None:
        manager = self._setup_manager(tmp_path)
        runner = DummyRunner()
        executor = StepExecutor(manager, runner)

        steps = _make_steps(3)
        executor.execute_story("story-1", steps)

        story = manager.state.stories["story-1"]
        assert len(story.steps_completed) == 3
        assert story.steps_completed[0].step_id == "step-0"
        assert story.steps_completed[2].step_id == "step-2"

    def test_fail_fast_stops_on_failure(self, tmp_path: Path) -> None:
        manager = self._setup_manager(tmp_path)
        results_list = [
            StepResult(step_id="step-0", status="completed", tokens_used=100),
            StepResult(step_id="step-1", status="failed", error="Test failure"),
        ]
        runner = DummyRunner(results=results_list)
        executor = StepExecutor(manager, runner, fail_fast=True)

        steps = _make_steps(3)
        results = executor.execute_story("story-1", steps)

        assert len(results) == 2
        assert results[0].is_success
        assert not results[1].is_success
        assert manager.state.stories["story-1"].status == StoryStatus.FAILED

    def test_no_fail_fast_continues(self, tmp_path: Path) -> None:
        manager = self._setup_manager(tmp_path)
        results_list = [
            StepResult(step_id="step-0", status="completed", tokens_used=100),
            StepResult(step_id="step-1", status="failed", error="Oops"),
            StepResult(step_id="step-2", status="completed", tokens_used=200),
        ]
        runner = DummyRunner(results=results_list)
        executor = StepExecutor(manager, runner, fail_fast=False)

        steps = _make_steps(3)
        results = executor.execute_story("story-1", steps)

        assert len(results) == 3

    def test_runner_exception_handled(self, tmp_path: Path) -> None:
        manager = self._setup_manager(tmp_path)
        runner = FailingRunner()
        executor = StepExecutor(manager, runner, fail_fast=True)

        steps = _make_steps(1)
        results = executor.execute_story("story-1", steps)

        assert len(results) == 1
        assert not results[0].is_success
        assert "exploded" in (results[0].error or "")
        assert manager.state.stories["story-1"].status == StoryStatus.FAILED

    def test_progress_callback_called(self, tmp_path: Path) -> None:
        manager = self._setup_manager(tmp_path)
        runner = DummyRunner()
        executor = StepExecutor(manager, runner)

        events: list[tuple[str, int, int, str]] = []

        def callback(step_id: str, current: int, total: int, status: str) -> None:
            events.append((step_id, current, total, status))

        steps = _make_steps(2)
        executor.execute_story("story-1", steps, progress_callback=callback)

        assert len(events) == 4
        assert events[0] == ("step-0", 1, 2, "starting")
        assert events[1] == ("step-0", 1, 2, "completed")
        assert events[2] == ("step-1", 2, 2, "starting")
        assert events[3] == ("step-1", 2, 2, "completed")

    def test_previous_outputs_accumulate(self, tmp_path: Path) -> None:
        manager = self._setup_manager(tmp_path)
        runner = DummyRunner()
        executor = StepExecutor(manager, runner)

        steps = _make_steps(3)
        executor.execute_story("story-1", steps)

        # Step 0: no previous outputs
        assert runner.calls[0][0].previous_outputs == []
        # Step 1: has step 0's output
        assert len(runner.calls[1][0].previous_outputs) == 1
        # Step 2: has step 0 + step 1 outputs
        assert len(runner.calls[2][0].previous_outputs) == 2

    def test_story_path_passed(self, tmp_path: Path) -> None:
        manager = self._setup_manager(tmp_path)
        runner = DummyRunner()
        executor = StepExecutor(manager, runner)

        steps = _make_steps(1)
        executor.execute_story("story-1", steps, story_path="/docs/story.md")

        assert runner.calls[0][0].story_path == "/docs/story.md"

    def test_state_persisted_to_disk(self, tmp_path: Path) -> None:
        manager = self._setup_manager(tmp_path)
        runner = DummyRunner()
        executor = StepExecutor(manager, runner)

        steps = _make_steps(2)
        executor.execute_story("story-1", steps)

        # Reload from disk
        state_file = tmp_path / "pipeline-state.json"
        data = json.loads(state_file.read_text())
        story_data = data["stories"]["story-1"]
        assert len(story_data["stepsCompleted"]) == 2


class TestStepExecutorResume:
    def test_resume_skips_completed(self, tmp_path: Path) -> None:
        state_file = tmp_path / "pipeline-state.json"
        manager = PipelineManager(state_file=state_file)
        manager.load()
        manager.add_story(PipelineStory(id="story-1", name="Test"))
        manager.save()

        # Execute first 2 steps
        runner1 = DummyRunner()
        executor1 = StepExecutor(manager, runner1)
        steps = _make_steps(3)
        executor1.execute_story("story-1", steps[:2])

        # Reset story status for resume
        manager.state.stories["story-1"].status = StoryStatus.IN_PROGRESS

        # Resume should only run step-2
        runner2 = DummyRunner()
        executor2 = StepExecutor(manager, runner2)
        results = executor2.resume_story("story-1", steps)

        assert len(runner2.calls) == 1
        assert runner2.calls[0][1].id == "step-2"

    def test_resume_nonexistent_story(self, tmp_path: Path) -> None:
        state_file = tmp_path / "pipeline-state.json"
        manager = PipelineManager(state_file=state_file)
        manager.load()

        runner = DummyRunner()
        executor = StepExecutor(manager, runner)

        import pytest

        with pytest.raises(KeyError, match="not found"):
            executor.resume_story("missing", _make_steps(1))
