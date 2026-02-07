"""Tests for file evolution tracker."""

from datetime import datetime
from datetime import timedelta
from pathlib import Path

from aios.memory.file_evolution import ConflictInfo
from aios.memory.file_evolution import DriftReport
from aios.memory.file_evolution import FileEvolutionTracker
from aios.memory.file_evolution import FileModification
from aios.memory.file_evolution import _EvolutionStore
from aios.memory.file_evolution import _FileRecord


class TestFileModification:
    def test_create_minimal(self) -> None:
        mod = FileModification(file_path="src/main.py", agent_id="dev")
        assert mod.file_path == "src/main.py"
        assert mod.agent_id == "dev"
        assert mod.task_id is None

    def test_create_with_task(self) -> None:
        mod = FileModification(
            file_path="src/main.py",
            agent_id="dev",
            task_id="task-123",
        )
        assert mod.task_id == "task-123"


class TestConflictInfo:
    def test_create(self) -> None:
        info = ConflictInfo(
            file_path="src/main.py",
            agents=["dev", "qa"],
            modifications=[],
            severity="medium",
        )
        assert info.severity == "medium"
        assert len(info.agents) == 2


class TestDriftReport:
    def test_create(self) -> None:
        now = datetime.now()
        report = DriftReport(
            file_path="src/app.py",
            agents=["dev", "data-engineer"],
            first_modification=now - timedelta(minutes=5),
            last_modification=now,
            total_modifications=4,
            severity="high",
        )
        assert report.total_modifications == 4
        assert report.severity == "high"


class TestFileEvolutionTracker:
    def test_record_modification(self, tmp_path: Path) -> None:
        tracker = FileEvolutionTracker(storage_dir=tmp_path / "evolution")
        tracker.record_modification("src/main.py", "dev")

        files = tracker.get_agent_files("dev")
        assert "src/main.py" in files

    def test_record_multiple_agents(self, tmp_path: Path) -> None:
        tracker = FileEvolutionTracker(storage_dir=tmp_path / "evolution")
        tracker.record_modification("src/main.py", "dev")
        tracker.record_modification("src/main.py", "qa")

        conflicts = tracker.check_conflicts("src/main.py")
        assert len(conflicts) == 1
        assert "dev" in conflicts[0].agents
        assert "qa" in conflicts[0].agents

    def test_no_conflict_single_agent(self, tmp_path: Path) -> None:
        tracker = FileEvolutionTracker(storage_dir=tmp_path / "evolution")
        tracker.record_modification("src/main.py", "dev")
        tracker.record_modification("src/main.py", "dev")

        conflicts = tracker.check_conflicts("src/main.py")
        assert len(conflicts) == 0

    def test_no_conflict_unknown_file(self, tmp_path: Path) -> None:
        tracker = FileEvolutionTracker(storage_dir=tmp_path / "evolution")
        conflicts = tracker.check_conflicts("nonexistent.py")
        assert len(conflicts) == 0

    def test_get_agent_files(self, tmp_path: Path) -> None:
        tracker = FileEvolutionTracker(storage_dir=tmp_path / "evolution")
        tracker.record_modification("src/a.py", "dev")
        tracker.record_modification("src/b.py", "dev")
        tracker.record_modification("src/c.py", "qa")

        dev_files = tracker.get_agent_files("dev")
        assert dev_files == ["src/a.py", "src/b.py"]

        qa_files = tracker.get_agent_files("qa")
        assert qa_files == ["src/c.py"]

    def test_get_agent_files_empty(self, tmp_path: Path) -> None:
        tracker = FileEvolutionTracker(storage_dir=tmp_path / "evolution")
        assert tracker.get_agent_files("nonexistent") == []

    def test_severity_low_far_apart(self, tmp_path: Path) -> None:
        """2 agents, same file, >10min apart = low."""
        tracker = FileEvolutionTracker(storage_dir=tmp_path / "evolution")

        now = datetime.now()
        data = _EvolutionStore(
            files={
                "src/app.py": _FileRecord(
                    modifications=[
                        FileModification(
                            file_path="src/app.py",
                            agent_id="dev",
                            timestamp=now - timedelta(minutes=20),
                        ),
                        FileModification(
                            file_path="src/app.py",
                            agent_id="qa",
                            timestamp=now,
                        ),
                    ]
                )
            }
        )
        tracker._save(data)

        conflicts = tracker.check_conflicts("src/app.py")
        assert len(conflicts) == 1
        assert conflicts[0].severity == "low"

    def test_severity_medium_close_together(self, tmp_path: Path) -> None:
        """2 agents, same file, <10min apart = medium."""
        tracker = FileEvolutionTracker(storage_dir=tmp_path / "evolution")

        now = datetime.now()
        data = _EvolutionStore(
            files={
                "src/app.py": _FileRecord(
                    modifications=[
                        FileModification(
                            file_path="src/app.py",
                            agent_id="dev",
                            timestamp=now - timedelta(minutes=3),
                        ),
                        FileModification(
                            file_path="src/app.py",
                            agent_id="qa",
                            timestamp=now,
                        ),
                    ]
                )
            }
        )
        tracker._save(data)

        conflicts = tracker.check_conflicts("src/app.py")
        assert len(conflicts) == 1
        assert conflicts[0].severity == "medium"

    def test_severity_high_three_agents(self, tmp_path: Path) -> None:
        """3+ agents, same file = high."""
        tracker = FileEvolutionTracker(storage_dir=tmp_path / "evolution")
        tracker.record_modification("src/app.py", "dev")
        tracker.record_modification("src/app.py", "qa")
        tracker.record_modification("src/app.py", "data-engineer")

        conflicts = tracker.check_conflicts("src/app.py")
        assert len(conflicts) == 1
        assert conflicts[0].severity == "high"

    def test_severity_critical_claude_path(self, tmp_path: Path) -> None:
        """Any agent + file in .claude/ = critical."""
        tracker = FileEvolutionTracker(storage_dir=tmp_path / "evolution")
        tracker.record_modification(".claude/hooks/test.py", "dev")
        tracker.record_modification(".claude/hooks/test.py", "qa")

        conflicts = tracker.check_conflicts(".claude/hooks/test.py")
        assert len(conflicts) == 1
        assert conflicts[0].severity == "critical"

    def test_severity_critical_src_aios_path(self, tmp_path: Path) -> None:
        """Any agent + file in src/aios/ = critical."""
        tracker = FileEvolutionTracker(storage_dir=tmp_path / "evolution")
        tracker.record_modification("src/aios/core/cache.py", "dev")
        tracker.record_modification("src/aios/core/cache.py", "data-engineer")

        conflicts = tracker.check_conflicts("src/aios/core/cache.py")
        assert len(conflicts) == 1
        assert conflicts[0].severity == "critical"

    def test_detect_drift_within_window(self, tmp_path: Path) -> None:
        tracker = FileEvolutionTracker(storage_dir=tmp_path / "evolution")
        tracker.record_modification("src/app.py", "dev")
        tracker.record_modification("src/app.py", "qa")

        reports = tracker.detect_drift(window_minutes=60)
        assert len(reports) == 1
        assert reports[0].file_path == "src/app.py"
        assert reports[0].total_modifications == 2

    def test_detect_drift_outside_window(self, tmp_path: Path) -> None:
        """Modifications outside the window are not reported."""
        tracker = FileEvolutionTracker(storage_dir=tmp_path / "evolution")

        old = datetime.now() - timedelta(hours=2)
        data = _EvolutionStore(
            files={
                "src/old.py": _FileRecord(
                    modifications=[
                        FileModification(
                            file_path="src/old.py",
                            agent_id="dev",
                            timestamp=old,
                        ),
                        FileModification(
                            file_path="src/old.py",
                            agent_id="qa",
                            timestamp=old + timedelta(minutes=1),
                        ),
                    ]
                )
            }
        )
        tracker._save(data)

        reports = tracker.detect_drift(window_minutes=30)
        assert len(reports) == 0

    def test_detect_drift_single_agent_not_reported(self, tmp_path: Path) -> None:
        tracker = FileEvolutionTracker(storage_dir=tmp_path / "evolution")
        tracker.record_modification("src/app.py", "dev")
        tracker.record_modification("src/app.py", "dev")

        reports = tracker.detect_drift(window_minutes=60)
        assert len(reports) == 0

    def test_detect_drift_sorted_by_severity(self, tmp_path: Path) -> None:
        tracker = FileEvolutionTracker(storage_dir=tmp_path / "evolution")

        now = datetime.now()
        data = _EvolutionStore(
            files={
                ".claude/config.py": _FileRecord(
                    modifications=[
                        FileModification(
                            file_path=".claude/config.py",
                            agent_id="dev",
                            timestamp=now,
                        ),
                        FileModification(
                            file_path=".claude/config.py",
                            agent_id="qa",
                            timestamp=now - timedelta(minutes=5),
                        ),
                    ]
                ),
                "src/utils.py": _FileRecord(
                    modifications=[
                        FileModification(
                            file_path="src/utils.py",
                            agent_id="dev",
                            timestamp=now - timedelta(minutes=15),
                        ),
                        FileModification(
                            file_path="src/utils.py",
                            agent_id="qa",
                            timestamp=now,
                        ),
                    ]
                ),
            }
        )
        tracker._save(data)

        reports = tracker.detect_drift(window_minutes=60)
        assert len(reports) == 2
        assert reports[0].severity == "critical"
        assert reports[1].severity == "low"

    def test_cleanup_removes_old_entries(self, tmp_path: Path) -> None:
        tracker = FileEvolutionTracker(storage_dir=tmp_path / "evolution")

        old = datetime.now() - timedelta(days=10)
        data = _EvolutionStore(
            files={
                "src/old.py": _FileRecord(
                    modifications=[
                        FileModification(
                            file_path="src/old.py",
                            agent_id="dev",
                            timestamp=old,
                        ),
                    ]
                )
            }
        )
        tracker._save(data)

        removed = tracker.cleanup(max_age_days=7)
        assert removed == 1

        files = tracker.get_agent_files("dev")
        assert files == []

    def test_cleanup_keeps_recent(self, tmp_path: Path) -> None:
        tracker = FileEvolutionTracker(storage_dir=tmp_path / "evolution")
        tracker.record_modification("src/recent.py", "dev")

        removed = tracker.cleanup(max_age_days=7)
        assert removed == 0

        files = tracker.get_agent_files("dev")
        assert "src/recent.py" in files

    def test_cleanup_partial_removal(self, tmp_path: Path) -> None:
        """Cleanup removes only old entries from a file, keeps recent ones."""
        tracker = FileEvolutionTracker(storage_dir=tmp_path / "evolution")

        old = datetime.now() - timedelta(days=10)
        now = datetime.now()
        data = _EvolutionStore(
            files={
                "src/mixed.py": _FileRecord(
                    modifications=[
                        FileModification(
                            file_path="src/mixed.py",
                            agent_id="dev",
                            timestamp=old,
                        ),
                        FileModification(
                            file_path="src/mixed.py",
                            agent_id="qa",
                            timestamp=now,
                        ),
                    ]
                )
            }
        )
        tracker._save(data)

        removed = tracker.cleanup(max_age_days=7)
        assert removed == 1

        files = tracker.get_agent_files("qa")
        assert "src/mixed.py" in files

    def test_persistence_across_instances(self, tmp_path: Path) -> None:
        storage = tmp_path / "evolution"
        tracker1 = FileEvolutionTracker(storage_dir=storage)
        tracker1.record_modification("src/a.py", "dev")

        tracker2 = FileEvolutionTracker(storage_dir=storage)
        tracker2.record_modification("src/a.py", "qa")

        conflicts = tracker2.check_conflicts("src/a.py")
        assert len(conflicts) == 1

    def test_storage_dir_property(self, tmp_path: Path) -> None:
        storage = tmp_path / "evolution"
        tracker = FileEvolutionTracker(storage_dir=storage)
        assert tracker.storage_dir == storage

    def test_corrupted_json_handled(self, tmp_path: Path) -> None:
        storage = tmp_path / "evolution"
        storage.mkdir(parents=True)
        (storage / "evolution.json").write_text("{invalid json")

        tracker = FileEvolutionTracker(storage_dir=storage)
        files = tracker.get_agent_files("dev")
        assert files == []

    def test_record_with_task_id(self, tmp_path: Path) -> None:
        tracker = FileEvolutionTracker(storage_dir=tmp_path / "evolution")
        tracker.record_modification("src/main.py", "dev", task_id="TASK-42")

        files = tracker.get_agent_files("dev")
        assert "src/main.py" in files

    def test_storage_directory_created(self, tmp_path: Path) -> None:
        storage = tmp_path / "subdir" / "deep" / "evolution"
        FileEvolutionTracker(storage_dir=storage)
        assert storage.exists()
