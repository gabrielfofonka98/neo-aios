"""Tests for route CLI commands."""

from click.testing import CliRunner

from aios.cli.commands.route import route_group


class TestRouteCLI:
    def test_route_classify(self) -> None:
        runner = CliRunner()
        result = runner.invoke(route_group, ["classify", "run security audit"])
        assert result.exit_code == 0
        assert "max" in result.output.lower() or "Complexity" in result.output

    def test_route_agent(self) -> None:
        runner = CliRunner()
        result = runner.invoke(route_group, ["agent", "dev"])
        assert result.exit_code == 0

    def test_route_map(self) -> None:
        runner = CliRunner()
        result = runner.invoke(route_group, ["map"])
        assert result.exit_code == 0
