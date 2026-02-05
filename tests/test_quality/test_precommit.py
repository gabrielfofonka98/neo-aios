"""Tests for the pre-commit gate module.

Tests the PreCommitGate class, configuration, and hook functionality.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from aios.quality.config import CheckResult
from aios.quality.config import CheckStatus
from aios.quality.config import GateConfig
from aios.quality.config import GateResult
from aios.quality.precommit import PreCommitGate
from aios.quality.precommit import precommit_gate

if TYPE_CHECKING:
    from collections.abc import Generator


class TestCheckResult:
    """Tests for CheckResult dataclass."""

    def test_create_passed_result(self) -> None:
        """Test creating a passed check result."""
        result = CheckResult(
            name="ruff",
            status=CheckStatus.PASSED,
            message="No errors",
            duration_ms=100,
            files_checked=5,
        )
        assert result.name == "ruff"
        assert result.status == CheckStatus.PASSED
        assert result.message == "No errors"
        assert result.duration_ms == 100
        assert result.files_checked == 5

    def test_create_failed_result_with_details(self) -> None:
        """Test creating a failed check result with details."""
        result = CheckResult(
            name="mypy",
            status=CheckStatus.FAILED,
            message="Found 3 errors",
            details="src/module.py:10: error: Missing type annotation",
        )
        assert result.status == CheckStatus.FAILED
        assert result.details is not None
        assert "Missing type annotation" in result.details

    def test_check_result_is_frozen(self) -> None:
        """Test that CheckResult is immutable."""
        result = CheckResult(
            name="pytest",
            status=CheckStatus.PASSED,
            message="All tests passed",
        )
        with pytest.raises(AttributeError):
            result.name = "changed"  # type: ignore[misc]


class TestGateResult:
    """Tests for GateResult dataclass."""

    def test_create_passed_gate_result(self) -> None:
        """Test creating a passed gate result."""
        checks = [
            CheckResult(name="ruff", status=CheckStatus.PASSED, message="OK"),
            CheckResult(name="mypy", status=CheckStatus.PASSED, message="OK"),
        ]
        result = GateResult(
            passed=True,
            checks=checks,
            blocked=False,
            total_duration_ms=500,
        )
        assert result.passed is True
        assert result.blocked is False
        assert len(result.checks) == 2

    def test_gate_result_summary(self) -> None:
        """Test gate result summary generation."""
        checks = [
            CheckResult(name="ruff", status=CheckStatus.PASSED, message="OK"),
            CheckResult(name="mypy", status=CheckStatus.FAILED, message="Errors"),
            CheckResult(name="security", status=CheckStatus.WARNING, message="Warn"),
        ]
        result = GateResult(
            passed=False,
            checks=checks,
            blocked=True,
            total_duration_ms=1000,
        )
        summary = result.summary
        assert "FAILED" in summary
        assert "1 passed" in summary
        assert "1 failed" in summary
        assert "1 warnings" in summary
        assert "1000ms" in summary

    def test_gate_result_with_warnings(self) -> None:
        """Test gate result with warnings list."""
        result = GateResult(
            passed=True,
            blocked=False,
            warnings=["Security: Found 2 HIGH issues"],
        )
        assert len(result.warnings) == 1
        assert "HIGH" in result.warnings[0]


class TestGateConfig:
    """Tests for GateConfig."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = GateConfig()
        assert config.block_on_critical is True
        assert config.block_on_ruff_error is True
        assert config.block_on_mypy_error is True
        assert config.block_on_test_failure is True
        assert config.warn_on_high is True
        assert config.run_fast_tests_only is True
        assert config.timeout_seconds == 30.0

    def test_custom_config(self) -> None:
        """Test custom configuration."""
        config = GateConfig(
            block_on_ruff_error=False,
            timeout_seconds=60.0,
        )
        assert config.block_on_ruff_error is False
        assert config.timeout_seconds == 60.0

    def test_should_exclude_pycache(self) -> None:
        """Test that __pycache__ is excluded."""
        config = GateConfig()
        assert config.should_exclude("__pycache__/module.pyc") is True
        assert config.should_exclude("src/__pycache__/") is True

    def test_should_exclude_venv(self) -> None:
        """Test that .venv is excluded."""
        config = GateConfig()
        assert config.should_exclude(".venv/lib/python3.12/site.py") is True

    def test_should_not_exclude_src(self) -> None:
        """Test that src/ is not excluded."""
        config = GateConfig()
        assert config.should_exclude("src/aios/module.py") is False


class TestPreCommitGate:
    """Tests for PreCommitGate class."""

    @pytest.fixture
    def gate(self) -> PreCommitGate:
        """Create a PreCommitGate instance for testing."""
        return PreCommitGate()

    @pytest.fixture
    def sample_python_file(self, tmp_path: Path) -> Path:
        """Create a sample Python file for testing."""
        file = tmp_path / "sample.py"
        file.write_text('def hello() -> str:\n    return "Hello"\n')
        return file

    def test_gate_initialization(self, gate: PreCommitGate) -> None:
        """Test gate initialization with default config."""
        assert gate.config is not None
        assert gate.config.block_on_critical is True

    def test_gate_with_custom_config(self) -> None:
        """Test gate with custom configuration."""
        config = GateConfig(block_on_ruff_error=False)
        gate = PreCommitGate(config=config)
        assert gate.config.block_on_ruff_error is False

    def test_run_checks_no_files(self, gate: PreCommitGate) -> None:
        """Test run_checks with no files."""
        result = gate.run_checks([])
        assert result.passed is True
        assert result.blocked is False

    def test_run_checks_all_excluded(self, gate: PreCommitGate) -> None:
        """Test run_checks when all files are excluded."""
        files = [Path("__pycache__/module.pyc")]
        result = gate.run_checks(files)
        assert result.passed is True
        assert len(result.checks) == 1
        assert result.checks[0].status == CheckStatus.SKIPPED

    def test_filter_files(self, gate: PreCommitGate) -> None:
        """Test file filtering."""
        files = [
            Path("src/module.py"),
            Path("__pycache__/cache.pyc"),
            Path(".venv/lib.py"),
        ]
        filtered = gate._filter_files(files)
        assert len(filtered) == 1
        assert filtered[0] == Path("src/module.py")

    @patch("subprocess.run")
    def test_run_ruff_passed(
        self, mock_run: MagicMock, gate: PreCommitGate, sample_python_file: Path
    ) -> None:
        """Test ruff check that passes."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        result = gate.run_ruff([sample_python_file])

        assert result.status == CheckStatus.PASSED
        assert result.name == "ruff"
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_run_ruff_failed(
        self, mock_run: MagicMock, gate: PreCommitGate, sample_python_file: Path
    ) -> None:
        """Test ruff check that fails."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="src/module.py:1:1: E999 SyntaxError\n",
            stderr="",
        )

        result = gate.run_ruff([sample_python_file])

        assert result.status == CheckStatus.FAILED
        assert "1 lint error" in result.message

    @patch("subprocess.run")
    def test_run_ruff_not_found(
        self, mock_run: MagicMock, gate: PreCommitGate, sample_python_file: Path
    ) -> None:
        """Test ruff check when ruff is not installed."""
        mock_run.side_effect = FileNotFoundError("ruff not found")

        result = gate.run_ruff([sample_python_file])

        assert result.status == CheckStatus.ERROR
        assert "not found" in result.message

    def test_run_ruff_no_files(self, gate: PreCommitGate) -> None:
        """Test ruff check with no files."""
        result = gate.run_ruff([])
        assert result.status == CheckStatus.SKIPPED

    @patch("subprocess.run")
    def test_run_mypy_passed(
        self, mock_run: MagicMock, gate: PreCommitGate, sample_python_file: Path
    ) -> None:
        """Test mypy check that passes."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        result = gate.run_mypy([sample_python_file])

        assert result.status == CheckStatus.PASSED
        assert result.name == "mypy"

    @patch("subprocess.run")
    def test_run_mypy_failed(
        self, mock_run: MagicMock, gate: PreCommitGate, sample_python_file: Path
    ) -> None:
        """Test mypy check that fails."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="src/module.py:10: error: Incompatible types\n",
            stderr="",
        )

        result = gate.run_mypy([sample_python_file])

        assert result.status == CheckStatus.FAILED
        assert "1 type error" in result.message

    @patch("subprocess.run")
    def test_run_tests_passed(
        self, mock_run: MagicMock, gate: PreCommitGate, sample_python_file: Path
    ) -> None:
        """Test pytest run that passes."""
        mock_run.return_value = MagicMock(returncode=0, stdout="3 passed", stderr="")

        result = gate.run_tests([sample_python_file])

        assert result.status == CheckStatus.PASSED
        assert result.name == "pytest"

    @patch("subprocess.run")
    def test_run_tests_failed(
        self, mock_run: MagicMock, gate: PreCommitGate, sample_python_file: Path
    ) -> None:
        """Test pytest run that fails."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="1 FAILED\ntest_module.py::test_foo FAILED",
            stderr="",
        )

        result = gate.run_tests([sample_python_file])

        assert result.status == CheckStatus.FAILED
        assert "test(s) failed" in result.message

    @patch("subprocess.run")
    def test_run_tests_no_tests(
        self, mock_run: MagicMock, gate: PreCommitGate, sample_python_file: Path
    ) -> None:
        """Test pytest run with no tests collected."""
        mock_run.return_value = MagicMock(
            returncode=5,  # pytest returns 5 for no tests
            stdout="collected 0 items",
            stderr="",
        )

        result = gate.run_tests([sample_python_file])

        assert result.status == CheckStatus.SKIPPED

    def test_should_block_ruff_failure(self, gate: PreCommitGate) -> None:
        """Test that ruff failure blocks commit."""
        checks = [
            CheckResult(name="ruff", status=CheckStatus.FAILED, message="Errors"),
        ]
        assert gate._should_block(checks) is True

    def test_should_block_mypy_failure(self, gate: PreCommitGate) -> None:
        """Test that mypy failure blocks commit."""
        checks = [
            CheckResult(name="mypy", status=CheckStatus.FAILED, message="Errors"),
        ]
        assert gate._should_block(checks) is True

    def test_should_not_block_warning(self, gate: PreCommitGate) -> None:
        """Test that warnings don't block commit."""
        checks = [
            CheckResult(name="security", status=CheckStatus.WARNING, message="Warn"),
        ]
        assert gate._should_block(checks) is False

    def test_should_not_block_with_disabled_config(self) -> None:
        """Test that disabling config prevents blocking."""
        config = GateConfig(block_on_ruff_error=False)
        gate = PreCommitGate(config=config)

        checks = [
            CheckResult(name="ruff", status=CheckStatus.FAILED, message="Errors"),
        ]
        assert gate._should_block(checks) is False


class TestRunChecksIntegration:
    """Integration tests for run_checks."""

    @pytest.fixture
    def gate(self) -> PreCommitGate:
        """Create a PreCommitGate for integration tests."""
        return PreCommitGate()

    @patch("subprocess.run")
    def test_run_checks_all_pass(
        self, mock_run: MagicMock, gate: PreCommitGate, tmp_path: Path
    ) -> None:
        """Test run_checks when all checks pass."""
        # Create test file
        test_file = tmp_path / "module.py"
        test_file.write_text("def foo() -> None:\n    pass\n")

        # Mock all subprocess calls to pass
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        # Mock security scan
        with patch(
            "aios.security.orchestrator.security_orchestrator"
        ) as mock_security:
            mock_report = MagicMock()
            mock_report.critical_findings = 0
            mock_report.high_findings = 0
            mock_security.quick_scan.return_value = mock_report

            result = gate.run_checks([test_file])

        assert result.passed is True
        assert result.blocked is False
        assert len(result.errors) == 0

    @patch("subprocess.run")
    def test_run_checks_ruff_fails(
        self, mock_run: MagicMock, gate: PreCommitGate, tmp_path: Path
    ) -> None:
        """Test run_checks when ruff fails."""
        test_file = tmp_path / "module.py"
        test_file.write_text("def foo():\n    pass\n")

        # Mock ruff to fail, others to pass
        def mock_subprocess(cmd: list[str], **kwargs: object) -> MagicMock:
            if "ruff" in cmd:
                return MagicMock(returncode=1, stdout="Error found\n", stderr="")
            return MagicMock(returncode=0, stdout="", stderr="")

        mock_run.side_effect = mock_subprocess

        with patch(
            "aios.security.orchestrator.security_orchestrator"
        ) as mock_security:
            mock_report = MagicMock()
            mock_report.critical_findings = 0
            mock_report.high_findings = 0
            mock_security.quick_scan.return_value = mock_report

            result = gate.run_checks([test_file])

        assert result.passed is False
        assert result.blocked is True
        assert any("Ruff" in e for e in result.errors)

    @patch("subprocess.run")
    def test_run_checks_security_critical(
        self, mock_run: MagicMock, gate: PreCommitGate, tmp_path: Path
    ) -> None:
        """Test run_checks when security finds CRITICAL issues."""
        test_file = tmp_path / "module.py"
        test_file.write_text("SECRET = 'password123'\n")

        # Mock subprocess to pass
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        with patch(
            "aios.security.orchestrator.security_orchestrator"
        ) as mock_security:
            mock_report = MagicMock()
            mock_report.critical_findings = 1
            mock_report.high_findings = 0
            mock_security.quick_scan.return_value = mock_report

            result = gate.run_checks([test_file])

        assert result.passed is False
        assert result.blocked is True
        assert any("Security" in e for e in result.errors)

    @patch("subprocess.run")
    def test_run_checks_security_high_warning(
        self, mock_run: MagicMock, gate: PreCommitGate, tmp_path: Path
    ) -> None:
        """Test run_checks when security finds HIGH issues (warning only)."""
        test_file = tmp_path / "module.py"
        test_file.write_text("data = input()\n")

        # Mock subprocess to pass
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        with patch(
            "aios.security.orchestrator.security_orchestrator"
        ) as mock_security:
            mock_report = MagicMock()
            mock_report.critical_findings = 0
            mock_report.high_findings = 2
            mock_security.quick_scan.return_value = mock_report

            result = gate.run_checks([test_file])

        # HIGH findings are warnings, not blockers
        assert result.blocked is False
        assert len(result.warnings) == 1
        assert "Security" in result.warnings[0]

    def test_run_checks_skip_individual(
        self, gate: PreCommitGate, tmp_path: Path
    ) -> None:
        """Test skipping individual checks."""
        test_file = tmp_path / "module.py"
        test_file.write_text("x = 1\n")

        result = gate.run_checks(
            [test_file],
            run_ruff=False,
            run_mypy=False,
            run_tests=False,
            run_security=False,
        )

        # With all checks skipped, should pass with no checks
        assert result.passed is True
        assert len(result.checks) == 0


class TestGlobalPrecommitGate:
    """Tests for global precommit_gate instance."""

    def test_global_instance_exists(self) -> None:
        """Test that global instance is available."""
        assert precommit_gate is not None
        assert isinstance(precommit_gate, PreCommitGate)

    def test_global_instance_has_default_config(self) -> None:
        """Test that global instance has default config."""
        assert precommit_gate.config.block_on_critical is True
        assert precommit_gate.config.block_on_ruff_error is True


class TestRunPrecommitHook:
    """Tests for run_precommit_hook function."""

    @patch("aios.quality.precommit._get_staged_files")
    def test_hook_no_staged_files(self, mock_get_staged: MagicMock) -> None:
        """Test hook with no staged files."""
        from aios.quality.precommit import run_precommit_hook

        mock_get_staged.return_value = []
        exit_code = run_precommit_hook()
        assert exit_code == 0

    @patch("aios.quality.precommit._get_staged_files")
    @patch.object(PreCommitGate, "run_checks")
    def test_hook_with_files_passed(
        self, mock_run: MagicMock, mock_get_staged: MagicMock
    ) -> None:
        """Test hook when checks pass."""
        from aios.quality.precommit import run_precommit_hook

        mock_get_staged.return_value = ["src/module.py"]
        mock_run.return_value = GateResult(
            passed=True,
            checks=[CheckResult(name="ruff", status=CheckStatus.PASSED, message="OK")],
            blocked=False,
        )

        exit_code = run_precommit_hook()
        assert exit_code == 0

    @patch("aios.quality.precommit._get_staged_files")
    @patch.object(PreCommitGate, "run_checks")
    def test_hook_with_files_blocked(
        self, mock_run: MagicMock, mock_get_staged: MagicMock
    ) -> None:
        """Test hook when checks fail and block."""
        from aios.quality.precommit import run_precommit_hook

        mock_get_staged.return_value = ["src/module.py"]
        mock_run.return_value = GateResult(
            passed=False,
            checks=[
                CheckResult(name="ruff", status=CheckStatus.FAILED, message="Errors")
            ],
            blocked=True,
            errors=["Ruff: Errors"],
        )

        exit_code = run_precommit_hook()
        assert exit_code == 1

    def test_hook_with_explicit_files(self) -> None:
        """Test hook with explicitly provided files."""
        from aios.quality.precommit import run_precommit_hook

        # Non-existent files should still work (filtered/skipped)
        exit_code = run_precommit_hook(files=["__pycache__/cache.pyc"])
        assert exit_code == 0
