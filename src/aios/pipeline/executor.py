"""Step executor — orchestrates isolated step execution for stories."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from typing import Protocol

from aios.pipeline.models import StepRecord
from aios.pipeline.models import StepStatus
from aios.pipeline.models import StoryStatus
from aios.pipeline.step_models import StepContext
from aios.pipeline.step_models import StepDefinition
from aios.pipeline.step_models import StepResult

if TYPE_CHECKING:
    from aios.pipeline.manager import PipelineManager


class StepRunner(Protocol):
    """Protocol for step execution backends."""

    def run(self, context: StepContext, definition: StepDefinition) -> StepResult:
        """Execute a single step.

        Args:
            context: Isolated context for this step.
            definition: Step definition from registry.

        Returns:
            StepResult with execution details.
        """
        ...


class ProgressCallback(Protocol):
    """Protocol for step execution progress callbacks."""

    def __call__(
        self,
        step_id: str,
        current: int,
        total: int,
        status: str,
    ) -> None:
        """Called when a step starts or completes.

        Args:
            step_id: ID of the step.
            current: Current step index (1-based).
            total: Total number of steps.
            status: Status message.
        """
        ...


class StepExecutor:
    """Orchestrates sequential execution of isolated steps for a story.

    Each step receives only its own context (no accumulated state).
    Progress is checkpointed to PipelineState after each step.

    Example:
        >>> executor = StepExecutor(manager, runner)
        >>> results = executor.execute_story("story-1", steps)
    """

    def __init__(
        self,
        manager: PipelineManager,
        runner: StepRunner,
        *,
        fail_fast: bool = True,
    ) -> None:
        self._manager = manager
        self._runner = runner
        self._fail_fast = fail_fast

    def execute_story(
        self,
        story_id: str,
        steps: list[StepDefinition],
        story_path: str = "",
        progress_callback: ProgressCallback | None = None,
    ) -> list[StepResult]:
        """Execute all steps for a story sequentially.

        Args:
            story_id: ID of the story being executed.
            steps: Ordered list of step definitions.
            story_path: Path to the story file.
            progress_callback: Optional callback for progress updates.

        Returns:
            List of StepResults (one per step attempted).
        """
        results: list[StepResult] = []
        total = len(steps)
        previous_outputs: list[str] = []

        self._manager.update_story_status(story_id, StoryStatus.IN_PROGRESS)

        for idx, step_def in enumerate(steps):
            current = idx + 1

            if progress_callback:
                progress_callback(step_def.id, current, total, "starting")

            context = self._build_step_context(
                step_def=step_def,
                story_id=story_id,
                story_path=story_path,
                previous_outputs=previous_outputs,
            )

            result = self._execute_step(step_def, context)
            results.append(result)
            self._checkpoint(story_id, step_def.id, result)

            if result.is_success:
                if progress_callback:
                    progress_callback(step_def.id, current, total, "completed")
                output_paths = result.files_modified + result.files_created
                previous_outputs.extend(output_paths)
            else:
                if progress_callback:
                    progress_callback(step_def.id, current, total, "failed")
                if self._fail_fast:
                    self._manager.update_story_status(
                        story_id, StoryStatus.FAILED
                    )
                    break

        all_success = all(r.is_success for r in results)
        if all_success and len(results) == total:
            self._manager.update_story_status(story_id, StoryStatus.IN_REVIEW)

        return results

    def resume_story(
        self,
        story_id: str,
        steps: list[StepDefinition],
        story_path: str = "",
        progress_callback: ProgressCallback | None = None,
    ) -> list[StepResult]:
        """Resume execution from the last completed step.

        Args:
            story_id: ID of the story to resume.
            steps: Full ordered list of step definitions.
            story_path: Path to the story file.
            progress_callback: Optional callback for progress updates.

        Returns:
            List of StepResults for newly executed steps.
        """
        story = self._manager.state.stories.get(story_id)
        if story is None:
            msg = f"Story '{story_id}' not found"
            raise KeyError(msg)

        completed_ids = {sr.step_id for sr in story.steps_completed}
        remaining = [s for s in steps if s.id not in completed_ids]

        if not remaining:
            return []

        previous_outputs: list[str] = []
        for sr in story.steps_completed:
            if sr.status == StepStatus.COMPLETED:
                previous_outputs.append(sr.step_id)

        return self.execute_story(
            story_id=story_id,
            steps=remaining,
            story_path=story_path,
            progress_callback=progress_callback,
        )

    def _build_step_context(
        self,
        step_def: StepDefinition,
        story_id: str,
        story_path: str,
        previous_outputs: list[str],
    ) -> StepContext:
        """Build isolated context for a single step."""
        return StepContext(
            step_id=step_def.id,
            story_id=story_id,
            story_path=story_path,
            agent_id=step_def.agent_id,
            model=step_def.model,
            token_budget=step_def.token_budget,
            previous_outputs=list(previous_outputs),
        )

    def _execute_step(
        self,
        step_def: StepDefinition,
        context: StepContext,
    ) -> StepResult:
        """Execute a single step via the runner."""
        started_at = datetime.now()
        try:
            result = self._runner.run(context, step_def)
            if not result.started_at:
                result.started_at = started_at
            if not result.completed_at:
                result.completed_at = datetime.now()
            return result
        except Exception as e:
            return StepResult(
                step_id=step_def.id,
                status="failed",
                error=str(e),
                started_at=started_at,
                completed_at=datetime.now(),
            )

    def _checkpoint(
        self,
        story_id: str,
        step_id: str,
        result: StepResult,
    ) -> None:
        """Record step result in pipeline state and save."""
        story = self._manager.state.stories.get(story_id)
        if story is None:
            return

        record = StepRecord(
            step_id=step_id,
            status=StepStatus.COMPLETED if result.is_success else StepStatus.FAILED,
            started_at=result.started_at,
            completed_at=result.completed_at,
            agent_id=result.model_used or None,
            model_used=result.model_used or None,
            tokens_used=result.tokens_used,
            error=result.error,
        )

        story.steps_completed = [*story.steps_completed, record]
        story.current_step = step_id if not result.is_success else None
        self._manager.save()
