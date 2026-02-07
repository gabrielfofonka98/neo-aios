"""Tests for conflicts CLI commands."""

from __future__ import annotations

from datetime import datetime
from datetime import timedelta
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from aios.cli.commands.conflicts import conflicts_group
from aios.memory.file_evolution import FileEvolutionTracker
from aios.memory.file_evolution import FileModification
from aios.memory.file_evolution import _EvolutionStore
from aios.memory.file_evolution import _FileRecord

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def runner() -> CliRunner:
    """Create a CLI test runner."""
    return CliRunner()


def _make_tracker_with_conflicts(tmp_path: Path) -> FileEvolutionTracker:
    """Create a tracker with 2-agent conflict data for testing."""
    tracker = FileEvolutionTracker(storage_dir=tmp_path / "evolution")
    now = datetime.now()
    data = _EvolutionStore(
        files={
            "src/main.py": _FileRecord(
                modifications=[
                    FileModification(
                        file_path="src/main.py",
                        agent_id="dev",
                        timestamp=now - timedelta(minutes=5),
                    ),
                    FileModification(
                        file_path="src/main.py",
                        agent_id="qa",
                        timestamp=now,
                    ),
                ]
            ),
        }
    )
    tracker._save(data)
    return tracker


class TestConflictsCheck:
    """Tests for conflicts check command."""

    def test_check_no_conflicts(self, runner: CliRunner, tmp_path: Path) -> None:
        """Check with no conflicts shows green message."""
        tracker = FileEvolutionTracker(storage_dir=tmp_path / "evolution")
        with patch(
            "aios.cli.commands.conflicts._get_tracker",
            return_value=tracker,
        ):
            result = runner.invoke(conflicts_group, ["check"])
        assert result.exit_code == 0
        assert "Nenhum conflito" in result.output

    def test_check_with_conflicts(self, runner: CliRunner, tmp_path: Path) -> None:
        """Check with conflicts shows table."""
        tracker = _make_tracker_with_conflicts(tmp_path)
        with patch(
            "aios.cli.commands.conflicts._get_tracker",
            return_value=tracker,
        ):
            result = runner.invoke(conflicts_group, ["check"])
        assert result.exit_code == 0
        assert "src/main.py" in result.output
        assert "dev" in result.output
        assert "qa" in result.output

    def test_check_filter_by_agent(self, runner: CliRunner, tmp_path: Path) -> None:
        """Check filters by agent."""
        tracker = _make_tracker_with_conflicts(tmp_path)
        with patch(
            "aios.cli.commands.conflicts._get_tracker",
            return_value=tracker,
        ):
            result = runner.invoke(conflicts_group, ["check", "--agent", "dev"])
        assert result.exit_code == 0
        assert "src/main.py" in result.output

    def test_check_filter_nonexistent_agent(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        """Check with non-matching agent filter shows no conflicts."""
        tracker = _make_tracker_with_conflicts(tmp_path)
        with patch(
            "aios.cli.commands.conflicts._get_tracker",
            return_value=tracker,
        ):
            result = runner.invoke(
                conflicts_group, ["check", "--agent", "nonexistent"]
            )
        assert result.exit_code == 0
        assert "Nenhum conflito" in result.output


class TestConflictsHistory:
    """Tests for conflicts history command."""

    def test_history_no_data(self, runner: CliRunner, tmp_path: Path) -> None:
        """History with no data shows empty message."""
        tracker = FileEvolutionTracker(storage_dir=tmp_path / "evolution")
        with patch(
            "aios.cli.commands.conflicts._get_tracker",
            return_value=tracker,
        ):
            result = runner.invoke(conflicts_group, ["history"])
        assert result.exit_code == 0
        assert "Nenhum conflito" in result.output

    def test_history_with_data(self, runner: CliRunner, tmp_path: Path) -> None:
        """History shows conflict data."""
        tracker = _make_tracker_with_conflicts(tmp_path)
        with patch(
            "aios.cli.commands.conflicts._get_tracker",
            return_value=tracker,
        ):
            result = runner.invoke(conflicts_group, ["history"])
        assert result.exit_code == 0
        assert "src/main.py" in result.output

    def test_history_custom_days(self, runner: CliRunner, tmp_path: Path) -> None:
        """History accepts --days option."""
        tracker = _make_tracker_with_conflicts(tmp_path)
        with patch(
            "aios.cli.commands.conflicts._get_tracker",
            return_value=tracker,
        ):
            result = runner.invoke(conflicts_group, ["history", "--days", "1"])
        assert result.exit_code == 0


class TestConflictsCleanup:
    """Tests for conflicts cleanup command."""

    def test_cleanup_with_confirmation(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        """Cleanup removes old entries when confirmed."""
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

        with patch(
            "aios.cli.commands.conflicts._get_tracker",
            return_value=tracker,
        ):
            result = runner.invoke(conflicts_group, ["cleanup", "--yes"])
        assert result.exit_code == 0
        assert "1" in result.output
        assert "removida" in result.output

    def test_cleanup_nothing_to_remove(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        """Cleanup with no old entries shows zero message."""
        tracker = FileEvolutionTracker(storage_dir=tmp_path / "evolution")
        tracker.record_modification("src/recent.py", "dev")

        with patch(
            "aios.cli.commands.conflicts._get_tracker",
            return_value=tracker,
        ):
            result = runner.invoke(conflicts_group, ["cleanup", "--yes"])
        assert result.exit_code == 0
        assert "Nenhuma entrada" in result.output

    def test_cleanup_without_confirmation_aborts(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        """Cleanup without --yes prompts and aborts on 'n'."""
        tracker = FileEvolutionTracker(storage_dir=tmp_path / "evolution")
        with patch(
            "aios.cli.commands.conflicts._get_tracker",
            return_value=tracker,
        ):
            result = runner.invoke(conflicts_group, ["cleanup"], input="n\n")
        assert result.exit_code != 0

    def test_cleanup_custom_days(self, runner: CliRunner, tmp_path: Path) -> None:
        """Cleanup accepts --days option."""
        tracker = FileEvolutionTracker(storage_dir=tmp_path / "evolution")

        old = datetime.now() - timedelta(days=3)
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

        with patch(
            "aios.cli.commands.conflicts._get_tracker",
            return_value=tracker,
        ):
            result = runner.invoke(
                conflicts_group, ["cleanup", "--days", "2", "--yes"]
            )
        assert result.exit_code == 0
        assert "1" in result.output


class TestConflictsHelp:
    """Tests for conflicts group help."""

    def test_help(self, runner: CliRunner) -> None:
        """Help shows available subcommands."""
        result = runner.invoke(conflicts_group, ["--help"])
        assert result.exit_code == 0
        assert "check" in result.output
        assert "history" in result.output
        assert "cleanup" in result.output
