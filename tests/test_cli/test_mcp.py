"""Tests for MCP CLI commands."""

from click.testing import CliRunner

from aios.cli.commands.mcp import mcp_group


class TestMCPCLI:
    def test_mcp_list(self) -> None:
        runner = CliRunner()
        result = runner.invoke(mcp_group, ["list"])
        assert result.exit_code == 0

    def test_mcp_install_unknown(self) -> None:
        runner = CliRunner()
        result = runner.invoke(mcp_group, ["install", "nonexistent"])
        assert result.exit_code != 0
