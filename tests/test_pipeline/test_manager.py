"""Tests for PipelineManager."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from aios.pipeline.manager import LockError
from aios.pipeline.manager import PipelineManager
from aios.pipeline.models import PipelineState
from aios.pipeline.models import PipelineStory
from aios.pipeline.models import StoryStatus


class TestPipelineManagerLoadSave:
    def test_load_creates_default_state(self, tmp_path: Path) -> None:
        state_file = tmp_path / "pipeline-state.json"
        manager = PipelineManager(state_file=state_file)
        state = manager.load()

        assert state.version == "1.0"
        assert state_file.exists()

    def test_load_existing_state(self, tmp_path: Path) -> None:
        state_file = tmp_path / "pipeline-state.json"
        data = {
            "version": "1.0",
            "project": "test-project",
            "stories": {
                "s1": {
                    "id": "s1",
                    "name": "Story 1",
                    "path": "",
                    "status": "pending",
                    "dependencies": [],
                    "blocks": [],
                    "stepsCompleted": [],
                    "currentStep": None,
                    "epic": None,
                },
            },
            "createdAt": "2026-01-01T00:00:00",
            "updatedAt": "2026-01-01T00:00:00",
            "lockHolder": None,
        }
        state_file.write_text(json.dumps(data))

        manager = PipelineManager(state_file=state_file)
        state = manager.load()

        assert state.project == "test-project"
        assert "s1" in state.stories
        assert state.stories["s1"].name == "Story 1"

    def test_load_corrupted_file(self, tmp_path: Path) -> None:
        state_file = tmp_path / "pipeline-state.json"
        state_file.write_text("{invalid json")

        manager = PipelineManager(state_file=state_file)
        state = manager.load()

        assert state.version == "1.0"
        assert state.stories == {}

    def test_save_creates_file(self, tmp_path: Path) -> None:
        state_file = tmp_path / "sub" / "pipeline-state.json"
        manager = PipelineManager(state_file=state_file)
        manager.save()

        assert state_file.exists()
        data = json.loads(state_file.read_text())
        assert data["version"] == "1.0"

    def test_save_atomic_write(self, tmp_path: Path) -> None:
        state_file = tmp_path / "pipeline-state.json"
        manager = PipelineManager(state_file=state_file)
        manager.load()
        manager.add_story(PipelineStory(id="s1", name="Story 1"))
        manager.save()

        data = json.loads(state_file.read_text())
        assert "s1" in data["stories"]

    def test_round_trip(self, tmp_path: Path) -> None:
        state_file = tmp_path / "pipeline-state.json"
        manager1 = PipelineManager(state_file=state_file)
        manager1.load()
        manager1.add_story(
            PipelineStory(
                id="s1",
                name="Story 1",
                dependencies=["s0"],
                epic="auth",
            )
        )
        manager1.save()

        manager2 = PipelineManager(state_file=state_file)
        state2 = manager2.load()

        assert "s1" in state2.stories
        assert state2.stories["s1"].dependencies == ["s0"]
        assert state2.stories["s1"].epic == "auth"


class TestPipelineManagerLocking:
    def test_acquire_and_release(self, tmp_path: Path) -> None:
        state_file = tmp_path / "pipeline-state.json"
        manager = PipelineManager(state_file=state_file)

        manager.acquire_lock("agent-1")
        lock_file = Path(str(state_file) + ".lock")
        assert lock_file.exists()

        data = json.loads(lock_file.read_text())
        assert data["holder"] == "agent-1"

        manager.release_lock("agent-1")
        assert not lock_file.exists()

    def test_release_wrong_holder(self, tmp_path: Path) -> None:
        state_file = tmp_path / "pipeline-state.json"
        manager = PipelineManager(state_file=state_file)

        manager.acquire_lock("agent-1")
        manager.release_lock("agent-2")

        lock_file = Path(str(state_file) + ".lock")
        assert lock_file.exists()

        manager.release_lock("agent-1")

    def test_lock_contention_timeout(self, tmp_path: Path) -> None:
        state_file = tmp_path / "pipeline-state.json"
        manager1 = PipelineManager(state_file=state_file)
        manager2 = PipelineManager(state_file=state_file)

        manager1.LOCK_TIMEOUT_S = 1.0
        manager2.LOCK_TIMEOUT_S = 1.0

        manager1.acquire_lock("agent-1")

        with pytest.raises(LockError):
            manager2.acquire_lock("agent-2")

        manager1.release_lock("agent-1")

    def test_release_nonexistent_lock(self, tmp_path: Path) -> None:
        state_file = tmp_path / "pipeline-state.json"
        manager = PipelineManager(state_file=state_file)
        manager.release_lock("agent-1")


class TestPipelineManagerDependencies:
    def _create_manager_with_stories(
        self, tmp_path: Path
    ) -> PipelineManager:
        state_file = tmp_path / "pipeline-state.json"
        manager = PipelineManager(state_file=state_file)
        manager.load()

        manager.add_story(PipelineStory(id="a", name="Story A"))
        manager.add_story(
            PipelineStory(id="b", name="Story B", dependencies=["a"])
        )
        manager.add_story(
            PipelineStory(id="c", name="Story C", dependencies=["b"])
        )
        return manager

    def test_get_ready_stories_returns_wave_1(self, tmp_path: Path) -> None:
        manager = self._create_manager_with_stories(tmp_path)
        ready = manager.get_ready_stories()

        assert len(ready) == 1
        assert ready[0].id == "a"
        assert ready[0].status == StoryStatus.READY

    def test_get_ready_stories_after_completion(self, tmp_path: Path) -> None:
        manager = self._create_manager_with_stories(tmp_path)

        manager.update_story_status("a", StoryStatus.DONE)
        ready = manager.get_ready_stories()

        assert len(ready) == 1
        assert ready[0].id == "b"

    def test_get_ready_stories_parallel(self, tmp_path: Path) -> None:
        state_file = tmp_path / "pipeline-state.json"
        manager = PipelineManager(state_file=state_file)
        manager.load()

        manager.add_story(PipelineStory(id="a", name="A"))
        manager.add_story(PipelineStory(id="b", name="B"))
        manager.add_story(
            PipelineStory(id="c", name="C", dependencies=["a", "b"])
        )

        ready = manager.get_ready_stories()
        ready_ids = {s.id for s in ready}
        assert ready_ids == {"a", "b"}

    def test_get_ready_stories_empty(self, tmp_path: Path) -> None:
        state_file = tmp_path / "pipeline-state.json"
        manager = PipelineManager(state_file=state_file)
        manager.load()

        ready = manager.get_ready_stories()
        assert ready == []

    def test_update_story_status_not_found(self, tmp_path: Path) -> None:
        state_file = tmp_path / "pipeline-state.json"
        manager = PipelineManager(state_file=state_file)
        manager.load()

        with pytest.raises(KeyError, match="not found"):
            manager.update_story_status("nonexistent", StoryStatus.DONE)

    def test_propagate_completion(self, tmp_path: Path) -> None:
        manager = self._create_manager_with_stories(tmp_path)

        manager.update_story_status("a", StoryStatus.DONE)
        assert manager.state.stories["b"].status == StoryStatus.READY

    def test_propagate_failure(self, tmp_path: Path) -> None:
        manager = self._create_manager_with_stories(tmp_path)

        manager.update_story_status("a", StoryStatus.FAILED)
        assert manager.state.stories["b"].status == StoryStatus.BLOCKED

    def test_detect_cycles_no_cycle(self, tmp_path: Path) -> None:
        manager = self._create_manager_with_stories(tmp_path)
        assert manager.detect_cycles() is False

    def test_detect_cycles_with_cycle(self, tmp_path: Path) -> None:
        state_file = tmp_path / "pipeline-state.json"
        manager = PipelineManager(state_file=state_file)
        manager.load()

        manager.add_story(
            PipelineStory(id="x", name="X", dependencies=["z"])
        )
        manager.add_story(
            PipelineStory(id="y", name="Y", dependencies=["x"])
        )
        manager.add_story(
            PipelineStory(id="z", name="Z", dependencies=["y"])
        )

        assert manager.detect_cycles() is True

    def test_analyze_dependencies(self, tmp_path: Path) -> None:
        manager = self._create_manager_with_stories(tmp_path)
        analysis = manager.analyze_dependencies()

        assert analysis.wave_count == 3
        assert analysis.total_tasks == 3

    def test_add_story(self, tmp_path: Path) -> None:
        state_file = tmp_path / "pipeline-state.json"
        manager = PipelineManager(state_file=state_file)
        manager.load()

        story = PipelineStory(id="new", name="New Story")
        manager.add_story(story)

        assert "new" in manager.state.stories
