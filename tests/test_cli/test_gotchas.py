"""Tests for gotchas CLI commands."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from aios.cli.commands.gotchas import gotchas_group
from aios.memory.gotchas import GotchasMemory

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def runner() -> CliRunner:
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def gotchas_mem(tmp_path: Path) -> GotchasMemory:
    """Create a GotchasMemory instance with temp storage."""
    return GotchasMemory(storage_path=tmp_path / "gotchas.json")


class TestGotchasList:
    """Tests for gotchas list command."""

    def test_list_empty(self, runner: CliRunner, tmp_path: Path) -> None:
        """Empty gotchas shows 'nenhum' message."""
        storage = tmp_path / "gotchas.json"
        with patch(
            "aios.cli.commands.gotchas._get_memory",
            return_value=GotchasMemory(storage_path=storage),
        ):
            result = runner.invoke(gotchas_group, ["list"])
        assert result.exit_code == 0
        assert "Nenhum" in result.output or "nenhum" in result.output.lower()

    def test_list_with_gotchas(self, runner: CliRunner, tmp_path: Path) -> None:
        """List command shows promoted gotchas."""
        storage = tmp_path / "gotchas.json"
        mem = GotchasMemory(storage_path=storage, threshold=1)
        mem.record_issue("auth", "token-expired")

        with patch(
            "aios.cli.commands.gotchas._get_memory",
            return_value=mem,
        ):
            result = runner.invoke(gotchas_group, ["list"])
        assert result.exit_code == 0
        assert "auth" in result.output
        assert "token-expired" in result.output

    def test_list_with_issues(self, runner: CliRunner, tmp_path: Path) -> None:
        """List command shows tracked issues."""
        storage = tmp_path / "gotchas.json"
        mem = GotchasMemory(storage_path=storage)
        mem.record_issue("db", "connection pool exhausted")

        with patch(
            "aios.cli.commands.gotchas._get_memory",
            return_value=mem,
        ):
            result = runner.invoke(gotchas_group, ["list"])
        assert result.exit_code == 0
        assert "db" in result.output
        assert "connection pool" in result.output

    def test_list_filter_by_agent(self, runner: CliRunner, tmp_path: Path) -> None:
        """List command filters by agent category."""
        storage = tmp_path / "gotchas.json"
        mem = GotchasMemory(storage_path=storage, threshold=1)
        mem.record_issue("auth", "issue A")
        mem.record_issue("db", "issue B")

        with patch(
            "aios.cli.commands.gotchas._get_memory",
            return_value=mem,
        ):
            result = runner.invoke(gotchas_group, ["list", "--agent", "auth"])
        assert result.exit_code == 0
        assert "auth" in result.output

    def test_list_filter_by_min_count(self, runner: CliRunner, tmp_path: Path) -> None:
        """List command filters by min-count."""
        storage = tmp_path / "gotchas.json"
        mem = GotchasMemory(storage_path=storage)
        mem.record_issue("auth", "issue A")
        mem.record_issue("auth", "issue A")
        mem.record_issue("db", "issue B")

        with patch(
            "aios.cli.commands.gotchas._get_memory",
            return_value=mem,
        ):
            result = runner.invoke(gotchas_group, ["list", "--min-count", "2"])
        assert result.exit_code == 0
        assert "auth" in result.output


class TestGotchasStats:
    """Tests for gotchas stats command."""

    def test_stats_empty(self, runner: CliRunner, tmp_path: Path) -> None:
        """Stats on empty memory shows zeros."""
        storage = tmp_path / "gotchas.json"
        with patch(
            "aios.cli.commands.gotchas._get_memory",
            return_value=GotchasMemory(storage_path=storage),
        ):
            result = runner.invoke(gotchas_group, ["stats"])
        assert result.exit_code == 0
        assert "0" in result.output

    def test_stats_with_data(self, runner: CliRunner, tmp_path: Path) -> None:
        """Stats shows correct counts."""
        storage = tmp_path / "gotchas.json"
        mem = GotchasMemory(storage_path=storage, threshold=1)
        mem.record_issue("auth", "issue A")
        mem.record_issue("db", "issue B")
        mem.record_issue("auth", "issue C")

        with patch(
            "aios.cli.commands.gotchas._get_memory",
            return_value=mem,
        ):
            result = runner.invoke(gotchas_group, ["stats"])
        assert result.exit_code == 0
        assert "3" in result.output  # total gotchas
        assert "auth" in result.output

    def test_stats_shows_threshold(self, runner: CliRunner, tmp_path: Path) -> None:
        """Stats shows the threshold value."""
        storage = tmp_path / "gotchas.json"
        mem = GotchasMemory(storage_path=storage, threshold=5)

        with patch(
            "aios.cli.commands.gotchas._get_memory",
            return_value=mem,
        ):
            result = runner.invoke(gotchas_group, ["stats"])
        assert result.exit_code == 0
        assert "5" in result.output


class TestGotchasReset:
    """Tests for gotchas reset command."""

    def test_reset_with_confirmation(self, runner: CliRunner, tmp_path: Path) -> None:
        """Reset clears all data when confirmed."""
        storage = tmp_path / "gotchas.json"
        mem = GotchasMemory(storage_path=storage, threshold=1)
        mem.record_issue("auth", "issue A")
        assert storage.exists()

        with patch(
            "aios.cli.commands.gotchas._get_memory",
            return_value=mem,
        ):
            result = runner.invoke(gotchas_group, ["reset", "--yes"])
        assert result.exit_code == 0
        assert "removidos" in result.output
        assert not storage.exists()

    def test_reset_without_confirmation_aborts(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        """Reset without --yes prompts and aborts on 'n'."""
        storage = tmp_path / "gotchas.json"
        mem = GotchasMemory(storage_path=storage, threshold=1)
        mem.record_issue("auth", "issue A")

        with patch(
            "aios.cli.commands.gotchas._get_memory",
            return_value=mem,
        ):
            result = runner.invoke(gotchas_group, ["reset"], input="n\n")
        assert result.exit_code != 0
        assert storage.exists()

    def test_reset_removes_markdown_too(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        """Reset also removes the .md companion file."""
        storage = tmp_path / "gotchas.json"
        md_path = tmp_path / "gotchas.md"
        mem = GotchasMemory(storage_path=storage, threshold=1)
        mem.record_issue("auth", "issue A")
        assert md_path.exists()

        with patch(
            "aios.cli.commands.gotchas._get_memory",
            return_value=mem,
        ):
            result = runner.invoke(gotchas_group, ["reset", "--yes"])
        assert result.exit_code == 0
        assert not md_path.exists()


class TestGotchasHelp:
    """Tests for gotchas group help."""

    def test_help(self, runner: CliRunner) -> None:
        """Help shows available subcommands."""
        result = runner.invoke(gotchas_group, ["--help"])
        assert result.exit_code == 0
        assert "list" in result.output
        assert "stats" in result.output
        assert "reset" in result.output
