"""Tests for memory agent-memory CLI commands (show, list-agents, clear)."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from aios.cli.commands.memory import MEMORY_TEMPLATE
from aios.cli.commands.memory import memory_group

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def runner() -> CliRunner:
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def agent_memory_dir(tmp_path: Path) -> Path:
    """Create a temporary agent memory directory with sample data."""
    mem_dir = tmp_path / "agent-memory"

    # Create dev agent memory
    dev_dir = mem_dir / "dev"
    dev_dir.mkdir(parents=True)
    (dev_dir / "MEMORY.md").write_text(
        "# Dev Memory\n\n- Always run tests before commit\n",
        encoding="utf-8",
    )

    # Create architect agent memory
    arch_dir = mem_dir / "architect"
    arch_dir.mkdir(parents=True)
    (arch_dir / "MEMORY.md").write_text(
        "# Architect Memory\n\n- Review ADRs weekly\n",
        encoding="utf-8",
    )

    return mem_dir


class TestMemoryShow:
    """Tests for memory show command."""

    def test_show_existing_agent(
        self, runner: CliRunner, agent_memory_dir: Path
    ) -> None:
        """Show displays agent memory content."""
        with patch(
            "aios.cli.commands.memory.AGENT_MEMORY_DIR",
            agent_memory_dir,
        ):
            result = runner.invoke(memory_group, ["show", "dev"])
        assert result.exit_code == 0
        assert "dev" in result.output
        assert "Always run tests" in result.output

    def test_show_nonexistent_agent(
        self, runner: CliRunner, agent_memory_dir: Path
    ) -> None:
        """Show for non-existent agent shows 'nenhuma' message."""
        with patch(
            "aios.cli.commands.memory.AGENT_MEMORY_DIR",
            agent_memory_dir,
        ):
            result = runner.invoke(memory_group, ["show", "nonexistent"])
        assert result.exit_code == 0
        assert "Nenhuma memoria" in result.output or "nenhuma" in result.output.lower()

    def test_show_requires_agent_id(self, runner: CliRunner) -> None:
        """Show without agent_id argument fails."""
        result = runner.invoke(memory_group, ["show"])
        assert result.exit_code != 0


class TestMemoryListAgents:
    """Tests for memory list-agents command."""

    def test_list_agents_with_data(
        self, runner: CliRunner, agent_memory_dir: Path
    ) -> None:
        """List-agents shows agents with memory files."""
        with patch(
            "aios.cli.commands.memory.AGENT_MEMORY_DIR",
            agent_memory_dir,
        ):
            result = runner.invoke(memory_group, ["list-agents"])
        assert result.exit_code == 0
        assert "dev" in result.output
        assert "architect" in result.output

    def test_list_agents_empty_dir(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        """List-agents with empty directory shows message."""
        empty_dir = tmp_path / "empty-agents"
        empty_dir.mkdir()
        with patch(
            "aios.cli.commands.memory.AGENT_MEMORY_DIR",
            empty_dir,
        ):
            result = runner.invoke(memory_group, ["list-agents"])
        assert result.exit_code == 0
        assert "Nenhum agente" in result.output

    def test_list_agents_dir_not_exist(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        """List-agents when directory doesn't exist shows message."""
        with patch(
            "aios.cli.commands.memory.AGENT_MEMORY_DIR",
            tmp_path / "nonexistent",
        ):
            result = runner.invoke(memory_group, ["list-agents"])
        assert result.exit_code == 0
        assert "nao encontrado" in result.output

    def test_list_agents_ignores_files(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        """List-agents ignores non-directory entries."""
        mem_dir = tmp_path / "agents"
        mem_dir.mkdir()
        (mem_dir / "stray-file.txt").write_text("not an agent dir")

        agent_dir = mem_dir / "dev"
        agent_dir.mkdir()
        (agent_dir / "MEMORY.md").write_text("# Dev\n")

        with patch(
            "aios.cli.commands.memory.AGENT_MEMORY_DIR",
            mem_dir,
        ):
            result = runner.invoke(memory_group, ["list-agents"])
        assert result.exit_code == 0
        assert "dev" in result.output
        assert "stray-file" not in result.output


class TestMemoryClear:
    """Tests for memory clear command."""

    def test_clear_with_confirmation(
        self, runner: CliRunner, agent_memory_dir: Path
    ) -> None:
        """Clear resets agent memory to template."""
        memory_file = agent_memory_dir / "dev" / "MEMORY.md"
        original = memory_file.read_text()
        assert "Always run tests" in original

        with patch(
            "aios.cli.commands.memory.AGENT_MEMORY_DIR",
            agent_memory_dir,
        ):
            result = runner.invoke(memory_group, ["clear", "dev", "--yes"])
        assert result.exit_code == 0
        assert "resetada" in result.output

        content = memory_file.read_text()
        assert content == MEMORY_TEMPLATE

    def test_clear_without_confirmation_aborts(
        self, runner: CliRunner, agent_memory_dir: Path
    ) -> None:
        """Clear without --yes prompts and aborts on 'n'."""
        with patch(
            "aios.cli.commands.memory.AGENT_MEMORY_DIR",
            agent_memory_dir,
        ):
            result = runner.invoke(memory_group, ["clear", "dev"], input="n\n")
        assert result.exit_code != 0

        # File should still have original content
        memory_file = agent_memory_dir / "dev" / "MEMORY.md"
        content = memory_file.read_text()
        assert "Always run tests" in content

    def test_clear_nonexistent_agent(
        self, runner: CliRunner, agent_memory_dir: Path
    ) -> None:
        """Clear for non-existent agent shows message."""
        with patch(
            "aios.cli.commands.memory.AGENT_MEMORY_DIR",
            agent_memory_dir,
        ):
            result = runner.invoke(
                memory_group, ["clear", "nonexistent", "--yes"]
            )
        assert result.exit_code == 0
        assert "Nenhuma memoria" in result.output or "nenhuma" in result.output.lower()


class TestMemoryHelp:
    """Tests for updated memory group help."""

    def test_help_shows_new_commands(self, runner: CliRunner) -> None:
        """Help shows the new agent-memory subcommands."""
        result = runner.invoke(memory_group, ["--help"])
        assert result.exit_code == 0
        assert "show" in result.output
        assert "list-agents" in result.output
        assert "clear" in result.output

    def test_help_shows_original_commands(self, runner: CliRunner) -> None:
        """Help still shows the original memory commands."""
        result = runner.invoke(memory_group, ["--help"])
        assert result.exit_code == 0
        assert "list" in result.output
        assert "search" in result.output
        assert "add" in result.output
        assert "digest" in result.output
        assert "prune" in result.output
