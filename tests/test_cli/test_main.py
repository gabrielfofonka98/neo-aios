"""Tests for the main CLI entry point."""

import pytest
from click.testing import CliRunner

import aios
from aios.cli.app import cli
from aios.cli.app import create_app


@pytest.fixture
def runner() -> CliRunner:
    """Create a CLI test runner."""
    return CliRunner()


class TestCLIEntryPoint:
    """Tests for the main CLI entry point."""

    def test_cli_exists(self) -> None:
        """Test that CLI is importable."""
        from aios.cli.main import cli as main_cli

        assert main_cli is not None

    def test_cli_is_click_group(self) -> None:
        """Test that CLI is a Click group."""
        import click

        assert isinstance(cli, click.Group)


class TestVersionCommand:
    """Tests for the version command."""

    def test_version_command_exists(self, runner: CliRunner) -> None:
        """Test that version command is registered."""
        result = runner.invoke(cli, ["version"])
        assert result.exit_code == 0

    def test_version_shows_correct_version(self, runner: CliRunner) -> None:
        """Test that version command shows the correct version."""
        result = runner.invoke(cli, ["version"])
        assert aios.__version__ in result.output

    def test_version_shows_neo_aios(self, runner: CliRunner) -> None:
        """Test that version command shows NEO-AIOS branding."""
        result = runner.invoke(cli, ["version"])
        assert "NEO-AIOS" in result.output


class TestHelpCommand:
    """Tests for the help command."""

    def test_help_flag(self, runner: CliRunner) -> None:
        """Test --help flag."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "NEO-AIOS" in result.output

    def test_help_shows_commands(self, runner: CliRunner) -> None:
        """Test that help shows available commands."""
        result = runner.invoke(cli, ["--help"])
        assert "agent" in result.output
        assert "scan" in result.output
        assert "health" in result.output
        assert "gate" in result.output
        assert "version" in result.output


class TestAgentGroup:
    """Tests for the agent command group."""

    def test_agent_help(self, runner: CliRunner) -> None:
        """Test agent group help."""
        result = runner.invoke(cli, ["agent", "--help"])
        assert result.exit_code == 0
        assert "list" in result.output
        assert "activate" in result.output
        assert "deactivate" in result.output
        assert "status" in result.output

    def test_agent_list(self, runner: CliRunner) -> None:
        """Test agent list command."""
        result = runner.invoke(cli, ["agent", "list"])
        assert result.exit_code == 0
        # Should show available agents
        assert "dev" in result.output or "Dex" in result.output

    def test_agent_activate(self, runner: CliRunner) -> None:
        """Test agent activate command."""
        result = runner.invoke(cli, ["agent", "activate", "dev"])
        assert result.exit_code == 0
        assert "dev" in result.output.lower()

    def test_agent_deactivate(self, runner: CliRunner) -> None:
        """Test agent deactivate command."""
        result = runner.invoke(cli, ["agent", "deactivate"])
        assert result.exit_code == 0

    def test_agent_status(self, runner: CliRunner) -> None:
        """Test agent status command."""
        result = runner.invoke(cli, ["agent", "status"])
        assert result.exit_code == 0


class TestScanGroup:
    """Tests for the scan command group."""

    def test_scan_help(self, runner: CliRunner) -> None:
        """Test scan group help."""
        result = runner.invoke(cli, ["scan", "--help"])
        assert result.exit_code == 0
        assert "quick" in result.output
        assert "full" in result.output

    def test_scan_quick(self, runner: CliRunner) -> None:
        """Test scan quick command."""
        result = runner.invoke(cli, ["scan", "quick"])
        assert result.exit_code == 0

    def test_scan_quick_with_path(self, runner: CliRunner) -> None:
        """Test scan quick command with path option."""
        result = runner.invoke(cli, ["scan", "quick", "--path", "/tmp"])
        assert result.exit_code == 0
        assert "/tmp" in result.output

    def test_scan_full(self, runner: CliRunner) -> None:
        """Test scan full command."""
        result = runner.invoke(cli, ["scan", "full"])
        assert result.exit_code == 0

    def test_scan_full_with_validator(self, runner: CliRunner) -> None:
        """Test scan full command with validator option."""
        result = runner.invoke(cli, ["scan", "full", "--validator", "xss"])
        assert result.exit_code == 0
        assert "xss" in result.output


class TestHealthGroup:
    """Tests for the health command group."""

    def test_health_help(self, runner: CliRunner) -> None:
        """Test health group help."""
        result = runner.invoke(cli, ["health", "--help"])
        assert result.exit_code == 0
        assert "check" in result.output

    def test_health_check(self, runner: CliRunner) -> None:
        """Test health check command."""
        result = runner.invoke(cli, ["health", "check"])
        assert result.exit_code == 0

    def test_health_check_with_name(self, runner: CliRunner) -> None:
        """Test health check command with name option."""
        result = runner.invoke(cli, ["health", "check", "--name", "agents"])
        assert result.exit_code == 0
        assert "agents" in result.output


class TestGateGroup:
    """Tests for the gate command group."""

    def test_gate_help(self, runner: CliRunner) -> None:
        """Test gate group help."""
        result = runner.invoke(cli, ["gate", "--help"])
        assert result.exit_code == 0
        assert "precommit" in result.output
        assert "pr" in result.output

    def test_gate_precommit(self, runner: CliRunner) -> None:
        """Test gate precommit command."""
        result = runner.invoke(cli, ["gate", "precommit"])
        assert result.exit_code == 0

    def test_gate_precommit_with_fix(self, runner: CliRunner) -> None:
        """Test gate precommit command with fix flag."""
        result = runner.invoke(cli, ["gate", "precommit", "--fix"])
        assert result.exit_code == 0
        assert "fix" in result.output.lower()

    def test_gate_pr(self, runner: CliRunner) -> None:
        """Test gate pr command."""
        result = runner.invoke(cli, ["gate", "pr"])
        assert result.exit_code == 0

    def test_gate_pr_with_number(self, runner: CliRunner) -> None:
        """Test gate pr command with PR number."""
        result = runner.invoke(cli, ["gate", "pr", "--pr-number", "123"])
        assert result.exit_code == 0
        assert "123" in result.output


class TestGlobalOptions:
    """Tests for global CLI options."""

    def test_verbose_flag(self, runner: CliRunner) -> None:
        """Test --verbose flag is accepted."""
        result = runner.invoke(cli, ["--verbose", "version"])
        assert result.exit_code == 0

    def test_quiet_flag(self, runner: CliRunner) -> None:
        """Test --quiet flag is accepted."""
        result = runner.invoke(cli, ["--quiet", "version"])
        assert result.exit_code == 0

    def test_short_verbose_flag(self, runner: CliRunner) -> None:
        """Test -v flag is accepted."""
        result = runner.invoke(cli, ["-v", "version"])
        assert result.exit_code == 0

    def test_short_quiet_flag(self, runner: CliRunner) -> None:
        """Test -q flag is accepted."""
        result = runner.invoke(cli, ["-q", "version"])
        assert result.exit_code == 0


class TestCreateApp:
    """Tests for the create_app factory function."""

    def test_create_app_returns_group(self) -> None:
        """Test that create_app returns a Click group."""
        import click

        app = create_app()
        assert isinstance(app, click.Group)

    def test_create_app_returns_new_instance(self) -> None:
        """Test that create_app returns a new instance each time."""
        app1 = create_app()
        app2 = create_app()
        assert app1 is not app2
