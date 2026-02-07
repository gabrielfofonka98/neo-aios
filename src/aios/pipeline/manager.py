"""Pipeline manager — load/save state, locking, dependency resolution."""

from __future__ import annotations

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from aios.core.waves import CycleDetectedError
from aios.core.waves import WaveAnalyzer
from aios.core.waves_models import Task as WaveTask
from aios.pipeline.models import PipelineState
from aios.pipeline.models import PipelineStory
from aios.pipeline.models import StoryStatus

if TYPE_CHECKING:
    from aios.core.waves_models import WaveAnalysis


class LockError(Exception):
    """Raised when lock cannot be acquired."""


class PipelineManager:
    """Manages pipeline state with file-based locking and dependency resolution.

    Example:
        >>> manager = PipelineManager()
        >>> manager.load()
        >>> ready = manager.get_ready_stories()
        >>> manager.update_story_status("story-1", StoryStatus.IN_PROGRESS)
        >>> manager.save()
    """

    DEFAULT_STATE_FILE = Path(".aios/pipeline-state.json")
    DEFAULT_LOCK_FILE = Path(".aios/pipeline-state.lock")

    LOCK_TIMEOUT_S = 30.0
    LOCK_RETRY_INTERVAL_S = 0.5
    STALE_LOCK_THRESHOLD_S = 60.0

    def __init__(
        self,
        state_file: Path | None = None,
        lock_file: Path | None = None,
    ) -> None:
        self._state_file = state_file or self.DEFAULT_STATE_FILE
        self._lock_file = lock_file or Path(str(self._state_file) + ".lock")
        self._state = PipelineState()
        self._wave_analyzer = WaveAnalyzer()
        self._lock_fd: int | None = None

    @property
    def state(self) -> PipelineState:
        """Get current pipeline state."""
        return self._state

    def load(self) -> PipelineState:
        """Load pipeline state from file.

        Returns:
            Loaded PipelineState.
        """
        if not self._state_file.exists():
            self._state_file.parent.mkdir(parents=True, exist_ok=True)
            self._state = PipelineState()
            self.save()
            return self._state

        try:
            data = json.loads(self._state_file.read_text())
            self._state = PipelineState(**data)
        except (json.JSONDecodeError, ValueError):
            self._state = PipelineState()

        return self._state

    def save(self) -> None:
        """Save pipeline state to file atomically (write tmp + rename)."""
        self._state.updated_at = datetime.now()
        self._state_file.parent.mkdir(parents=True, exist_ok=True)

        data = self._serialize_state()
        tmp_path = self._state_file.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(data, indent=2, default=str))
        tmp_path.replace(self._state_file)

    def acquire_lock(self, holder_id: str) -> None:
        """Acquire file-based lock using atomic O_CREAT | O_EXCL.

        Args:
            holder_id: Identifier for the lock holder.

        Raises:
            LockError: If lock cannot be acquired within timeout.
        """
        deadline = time.monotonic() + self.LOCK_TIMEOUT_S

        while time.monotonic() < deadline:
            try:
                fd = os.open(
                    str(self._lock_file),
                    os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                    0o644,
                )
                lock_data = json.dumps(
                    {"holder": holder_id, "acquired_at": datetime.now().isoformat()}
                )
                os.write(fd, lock_data.encode())
                os.close(fd)
                self._lock_fd = fd
                return
            except FileExistsError:
                if self._break_stale_lock():
                    continue
                time.sleep(self.LOCK_RETRY_INTERVAL_S)

        msg = f"Could not acquire lock within {self.LOCK_TIMEOUT_S}s"
        raise LockError(msg)

    def release_lock(self, holder_id: str) -> None:
        """Release the pipeline lock.

        Args:
            holder_id: Must match the lock holder.
        """
        if not self._lock_file.exists():
            return

        try:
            data = json.loads(self._lock_file.read_text())
            if data.get("holder") == holder_id:
                self._lock_file.unlink(missing_ok=True)
        except (json.JSONDecodeError, ValueError, OSError):
            self._lock_file.unlink(missing_ok=True)

        self._lock_fd = None

    def get_ready_stories(self) -> list[PipelineStory]:
        """Get stories ready for execution (wave 1 of dependency graph).

        Converts stories to WaveTasks, runs WaveAnalyzer, returns first wave.

        Returns:
            List of stories with all dependencies satisfied.
        """
        eligible = {
            sid: s
            for sid, s in self._state.stories.items()
            if s.status in (StoryStatus.PENDING, StoryStatus.READY)
        }

        if not eligible:
            return []

        wave_tasks = [
            WaveTask(
                id=sid,
                name=s.name,
                depends_on=[
                    d for d in s.dependencies if d in self._state.stories
                ],
            )
            for sid, s in eligible.items()
        ]

        try:
            analysis = self._wave_analyzer.analyze(wave_tasks)
        except CycleDetectedError:
            return []

        if not analysis.waves:
            return []

        first_wave_ids = {t.id for t in analysis.waves[0].tasks}

        ready: list[PipelineStory] = []
        for sid in first_wave_ids:
            story = self._state.stories[sid]
            deps_done = all(
                self._state.stories.get(d, PipelineStory(id=d, name=d)).status
                == StoryStatus.DONE
                for d in story.dependencies
                if d in self._state.stories
            )
            if deps_done:
                story.status = StoryStatus.READY
                ready.append(story)

        return ready

    def analyze_dependencies(self) -> WaveAnalysis:
        """Run full wave analysis on all non-done stories.

        Returns:
            WaveAnalysis with waves, critical path, and parallelism metrics.
        """
        active = {
            sid: s
            for sid, s in self._state.stories.items()
            if s.status != StoryStatus.DONE
        }

        wave_tasks = [
            WaveTask(
                id=sid,
                name=s.name,
                depends_on=[d for d in s.dependencies if d in active],
            )
            for sid, s in active.items()
        ]

        return self._wave_analyzer.analyze(wave_tasks)

    def update_story_status(
        self,
        story_id: str,
        new_status: StoryStatus,
    ) -> None:
        """Update a story's status and propagate dependency effects.

        Args:
            story_id: ID of the story to update.
            new_status: New status to set.

        Raises:
            KeyError: If story_id not found.
        """
        if story_id not in self._state.stories:
            msg = f"Story '{story_id}' not found in pipeline state"
            raise KeyError(msg)

        story = self._state.stories[story_id]
        story.status = new_status
        self._state.updated_at = datetime.now()

        if new_status == StoryStatus.DONE:
            self._propagate_completion(story_id)
        elif new_status == StoryStatus.FAILED:
            self._propagate_failure(story_id)

    def add_story(self, story: PipelineStory) -> None:
        """Add a story to the pipeline.

        Args:
            story: Story to add.
        """
        self._state.stories[story.id] = story
        self._state.updated_at = datetime.now()

    def detect_cycles(self) -> bool:
        """Check for dependency cycles.

        Returns:
            True if cycles exist, False otherwise.
        """
        wave_tasks = [
            WaveTask(
                id=sid,
                name=s.name,
                depends_on=[
                    d for d in s.dependencies if d in self._state.stories
                ],
            )
            for sid, s in self._state.stories.items()
        ]

        try:
            self._wave_analyzer.analyze(wave_tasks)
        except CycleDetectedError:
            return True
        return False

    def _propagate_completion(self, completed_id: str) -> None:
        """Mark dependent stories as READY if all their deps are DONE."""
        for story in self._state.stories.values():
            if completed_id not in story.dependencies:
                continue
            if story.status not in (StoryStatus.PENDING, StoryStatus.BLOCKED):
                continue

            all_deps_done = all(
                self._state.stories.get(d, PipelineStory(id=d, name=d)).status
                == StoryStatus.DONE
                for d in story.dependencies
                if d in self._state.stories
            )
            if all_deps_done:
                story.status = StoryStatus.READY

    def _propagate_failure(self, failed_id: str) -> None:
        """Mark stories that depend on a failed story as BLOCKED."""
        for story in self._state.stories.values():
            if failed_id in story.dependencies and story.status in (
                StoryStatus.PENDING,
                StoryStatus.READY,
            ):
                story.status = StoryStatus.BLOCKED

    def _break_stale_lock(self) -> bool:
        """Remove lock file if older than stale threshold.

        Returns:
            True if stale lock was removed.
        """
        try:
            stat = self._lock_file.stat()
            age = time.time() - stat.st_mtime
            if age > self.STALE_LOCK_THRESHOLD_S:
                self._lock_file.unlink(missing_ok=True)
                return True
        except OSError:
            return False
        return False

    def _serialize_state(self) -> dict[str, object]:
        """Serialize state to dict with camelCase keys."""
        stories_data: dict[str, object] = {}
        for sid, story in self._state.stories.items():
            steps = [
                {
                    "stepId": sr.step_id,
                    "status": sr.status.value,
                    "startedAt": sr.started_at.isoformat() if sr.started_at else None,
                    "completedAt": (
                        sr.completed_at.isoformat() if sr.completed_at else None
                    ),
                    "agentId": sr.agent_id,
                    "modelUsed": sr.model_used,
                    "tokensUsed": sr.tokens_used,
                    "error": sr.error,
                }
                for sr in story.steps_completed
            ]

            stories_data[sid] = {
                "id": story.id,
                "name": story.name,
                "path": story.path,
                "status": story.status.value,
                "dependencies": story.dependencies,
                "blocks": story.blocks,
                "stepsCompleted": steps,
                "currentStep": story.current_step,
                "epic": story.epic,
            }

        return {
            "version": self._state.version,
            "project": self._state.project,
            "stories": stories_data,
            "createdAt": self._state.created_at.isoformat(),
            "updatedAt": self._state.updated_at.isoformat(),
            "lockHolder": self._state.lock_holder,
        }
