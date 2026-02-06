"""Tests for doctor CLI commands."""

from click.testing import CliRunner

from aios.cli.commands.doctor import doctor_group


class TestDoctorCLI:
    def test_doctor_run(self) -> None:
        runner = CliRunner()
        result = runner.invoke(doctor_group, ["run"])
        assert result.exit_code == 0

    def test_doctor_run_fix(self) -> None:
        runner = CliRunner()
        result = runner.invoke(doctor_group, ["run", "--fix"])
        assert result.exit_code == 0

    def test_doctor_list(self) -> None:
        runner = CliRunner()
        result = runner.invoke(doctor_group, ["list"])
        assert result.exit_code == 0
        assert "Available checks" in result.output
