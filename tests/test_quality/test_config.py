"""Tests for quality gates configuration loader.

Tests the ConfigLoader class, Pydantic models, and YAML loading functionality.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from aios.quality.loader import ConfigLoader
from aios.quality.loader import ExclusionsConfig
from aios.quality.loader import HumanReviewConfig
from aios.quality.loader import PRAutomationConfig
from aios.quality.loader import PreCommitConfig
from aios.quality.loader import QualityGatesConfig
from aios.quality.loader import get_default_config
from aios.quality.loader import load_config
from aios.quality.loader import load_config_or_default
from aios.quality.loader import to_yaml
from aios.security.models import Severity


class TestPreCommitConfig:
    """Tests for PreCommitConfig model."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = PreCommitConfig()
        assert config.enabled is True
        assert config.block_on_ruff_error is True
        assert config.block_on_mypy_error is True
        assert config.block_on_test_failure is True
        assert config.block_on_critical_security is True
        assert config.warn_on_high_security is True
        assert config.timeout_seconds == 120
        assert config.run_fast_tests_only is True
        assert config.max_parallel_checks == 4

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = PreCommitConfig(
            enabled=False,
            block_on_ruff_error=False,
            timeout_seconds=60,
            max_parallel_checks=8,
        )
        assert config.enabled is False
        assert config.block_on_ruff_error is False
        assert config.timeout_seconds == 60
        assert config.max_parallel_checks == 8

    def test_timeout_validation_min(self) -> None:
        """Test timeout minimum validation."""
        with pytest.raises(ValueError, match="greater than or equal to 10"):
            PreCommitConfig(timeout_seconds=5)

    def test_timeout_validation_max(self) -> None:
        """Test timeout maximum validation."""
        with pytest.raises(ValueError, match="less than or equal to 600"):
            PreCommitConfig(timeout_seconds=700)

    def test_max_parallel_validation(self) -> None:
        """Test max_parallel_checks validation."""
        with pytest.raises(ValueError):
            PreCommitConfig(max_parallel_checks=0)
        with pytest.raises(ValueError):
            PreCommitConfig(max_parallel_checks=20)


class TestPRAutomationConfig:
    """Tests for PRAutomationConfig model."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = PRAutomationConfig()
        assert config.enabled is True
        assert config.block_severities == ["CRITICAL", "HIGH"]
        assert config.warn_severities == ["MEDIUM"]
        assert config.audit_timeout_seconds == 300
        assert config.auto_approve_clean is False

    def test_custom_severities(self) -> None:
        """Test custom severity configuration."""
        config = PRAutomationConfig(
            block_severities=["CRITICAL"],
            warn_severities=["HIGH", "MEDIUM"],
        )
        assert config.block_severities == ["CRITICAL"]
        assert config.warn_severities == ["HIGH", "MEDIUM"]

    def test_invalid_severity_raises_error(self) -> None:
        """Test that invalid severities raise ValueError."""
        with pytest.raises(ValueError, match="Invalid severity"):
            PRAutomationConfig(block_severities=["INVALID"])

    def test_case_insensitive_severities(self) -> None:
        """Test that severities are normalized to uppercase."""
        config = PRAutomationConfig(
            block_severities=["critical", "High"],
        )
        assert config.block_severities == ["CRITICAL", "HIGH"]

    def test_get_block_severities(self) -> None:
        """Test converting block severities to Severity enum."""
        config = PRAutomationConfig(block_severities=["CRITICAL", "HIGH"])
        severities = config.get_block_severities()
        assert severities == [Severity.CRITICAL, Severity.HIGH]

    def test_get_warn_severities(self) -> None:
        """Test converting warn severities to Severity enum."""
        config = PRAutomationConfig(warn_severities=["MEDIUM", "LOW"])
        severities = config.get_warn_severities()
        assert severities == [Severity.MEDIUM, Severity.LOW]

    def test_audit_timeout_validation(self) -> None:
        """Test audit timeout validation."""
        with pytest.raises(ValueError):
            PRAutomationConfig(audit_timeout_seconds=30)  # Below minimum
        with pytest.raises(ValueError):
            PRAutomationConfig(audit_timeout_seconds=2000)  # Above maximum


class TestHumanReviewConfig:
    """Tests for HumanReviewConfig model."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = HumanReviewConfig()
        assert config.enabled is True
        assert "config/" in config.sensitive_paths
        assert config.large_pr_threshold == 500
        assert config.require_tech_lead is True

    def test_custom_sensitive_paths(self) -> None:
        """Test custom sensitive paths."""
        config = HumanReviewConfig(
            sensitive_paths=[
                "secrets/",
                ".env",
                "credentials.json",
            ]
        )
        assert len(config.sensitive_paths) == 3
        assert "secrets/" in config.sensitive_paths

    def test_large_pr_threshold_validation(self) -> None:
        """Test large_pr_threshold validation."""
        with pytest.raises(ValueError):
            HumanReviewConfig(large_pr_threshold=50)  # Below minimum
        with pytest.raises(ValueError):
            HumanReviewConfig(large_pr_threshold=6000)  # Above maximum


class TestExclusionsConfig:
    """Tests for ExclusionsConfig model."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = ExclusionsConfig()
        assert "tests/fixtures/" in config.paths
        assert "__pycache__/" in config.paths
        assert config.validators == []
        assert "*.min.js" in config.file_patterns

    def test_custom_exclusions(self) -> None:
        """Test custom exclusions."""
        config = ExclusionsConfig(
            paths=["vendor/", "third_party/"],
            validators=["sec-rate-limit-tester"],
            file_patterns=["*.generated.ts"],
        )
        assert "vendor/" in config.paths
        assert "sec-rate-limit-tester" in config.validators
        assert "*.generated.ts" in config.file_patterns


class TestQualityGatesConfig:
    """Tests for QualityGatesConfig root model."""

    def test_default_values(self) -> None:
        """Test default configuration creates all sub-configs."""
        config = QualityGatesConfig()
        assert isinstance(config.precommit, PreCommitConfig)
        assert isinstance(config.pr_automation, PRAutomationConfig)
        assert isinstance(config.human_review, HumanReviewConfig)
        assert isinstance(config.exclusions, ExclusionsConfig)
        assert config.version == "1.0"

    def test_nested_configuration(self) -> None:
        """Test nested configuration works correctly."""
        config = QualityGatesConfig(
            precommit=PreCommitConfig(timeout_seconds=60),
            pr_automation=PRAutomationConfig(auto_approve_clean=True),
        )
        assert config.precommit.timeout_seconds == 60
        assert config.pr_automation.auto_approve_clean is True


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_nonexistent_file_returns_defaults(self, tmp_path: Path) -> None:
        """Test loading nonexistent file returns defaults."""
        config = load_config(tmp_path / "nonexistent.yaml")
        assert isinstance(config, QualityGatesConfig)
        assert config.precommit.enabled is True

    def test_load_empty_file_returns_defaults(self, tmp_path: Path) -> None:
        """Test loading empty file returns defaults."""
        config_file = tmp_path / "empty.yaml"
        config_file.write_text("")

        config = load_config(config_file)
        assert isinstance(config, QualityGatesConfig)
        assert config.precommit.enabled is True

    def test_load_valid_config(self, tmp_path: Path) -> None:
        """Test loading valid configuration file."""
        config_file = tmp_path / "quality-gates.yaml"
        config_file.write_text("""
quality_gates:
  precommit:
    enabled: true
    timeout_seconds: 60
  pr_automation:
    block_severities:
      - CRITICAL
  human_review:
    large_pr_threshold: 300
  exclusions:
    paths:
      - custom/path/
version: "1.1"
""")

        config = load_config(config_file)

        assert config.precommit.timeout_seconds == 60
        assert config.pr_automation.block_severities == ["CRITICAL"]
        assert config.human_review.large_pr_threshold == 300
        assert "custom/path/" in config.exclusions.paths
        assert config.version == "1.1"

    def test_load_config_without_quality_gates_key(self, tmp_path: Path) -> None:
        """Test loading config without quality_gates wrapper."""
        config_file = tmp_path / "flat.yaml"
        config_file.write_text("""
precommit:
  timeout_seconds: 90
pr_automation:
  enabled: false
""")

        config = load_config(config_file)

        assert config.precommit.timeout_seconds == 90
        assert config.pr_automation.enabled is False

    def test_load_invalid_yaml_raises_error(self, tmp_path: Path) -> None:
        """Test loading invalid YAML raises ValueError."""
        config_file = tmp_path / "invalid.yaml"
        config_file.write_text("""
quality_gates:
  precommit:
    timeout: [unclosed bracket
""")

        with pytest.raises(ValueError, match="Invalid YAML"):
            load_config(config_file)

    def test_load_invalid_values_raises_error(self, tmp_path: Path) -> None:
        """Test loading invalid values raises ValueError."""
        config_file = tmp_path / "invalid_values.yaml"
        config_file.write_text("""
quality_gates:
  precommit:
    timeout_seconds: 5000
""")

        with pytest.raises(ValueError):
            load_config(config_file)


class TestLoadConfigOrDefault:
    """Tests for load_config_or_default function."""

    def test_none_path_returns_defaults(self) -> None:
        """Test None path returns default config."""
        config = load_config_or_default(None)
        assert isinstance(config, QualityGatesConfig)
        assert config.precommit.enabled is True

    def test_valid_path_loads_config(self, tmp_path: Path) -> None:
        """Test valid path loads config."""
        config_file = tmp_path / "test.yaml"
        config_file.write_text("""
precommit:
  timeout_seconds: 45
""")

        config = load_config_or_default(config_file)
        assert config.precommit.timeout_seconds == 45


class TestConfigLoader:
    """Tests for ConfigLoader class."""

    def test_init_with_path(self, tmp_path: Path) -> None:
        """Test initialization with path."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("precommit:\n  enabled: false")

        loader = ConfigLoader(config_file)
        assert loader.path == config_file

    def test_load_caches_config(self, tmp_path: Path) -> None:
        """Test that load() caches the configuration."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("precommit:\n  timeout_seconds: 100")

        loader = ConfigLoader(config_file)
        config1 = loader.load()
        config2 = loader.load()

        assert config1 is config2  # Same object reference

    def test_load_with_reload_reloads_config(self, tmp_path: Path) -> None:
        """Test that load(reload=True) reloads from file."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("precommit:\n  timeout_seconds: 100")

        loader = ConfigLoader(config_file)
        _ = loader.load()  # Initial load

        # Modify file
        config_file.write_text("precommit:\n  timeout_seconds: 200")

        # Without reload - same cached value
        config2 = loader.load()
        assert config2.precommit.timeout_seconds == 100

        # With reload - new value
        config3 = loader.load(reload=True)
        assert config3.precommit.timeout_seconds == 200

    def test_reload_shortcut(self, tmp_path: Path) -> None:
        """Test reload() method."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("precommit:\n  timeout_seconds: 100")

        loader = ConfigLoader(config_file)
        loader.load()

        config_file.write_text("precommit:\n  timeout_seconds: 150")
        config = loader.reload()

        assert config.precommit.timeout_seconds == 150

    def test_to_gate_config_conversion(self, tmp_path: Path) -> None:
        """Test conversion to legacy GateConfig."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
precommit:
  block_on_ruff_error: false
  block_on_mypy_error: true
  timeout_seconds: 90
  run_fast_tests_only: false
exclusions:
  paths:
    - custom/
""")

        loader = ConfigLoader(config_file)
        gate_config = loader.to_gate_config()

        assert gate_config.block_on_ruff_error is False
        assert gate_config.block_on_mypy_error is True
        assert gate_config.timeout_seconds == 90.0
        assert gate_config.run_fast_tests_only is False
        assert "custom/" in gate_config.excluded_paths


class TestGetDefaultConfig:
    """Tests for get_default_config function."""

    def test_returns_config_instance(self) -> None:
        """Test that get_default_config returns a valid config."""
        config = get_default_config()
        assert isinstance(config, QualityGatesConfig)


class TestToYaml:
    """Tests for to_yaml function."""

    def test_serializes_to_valid_yaml(self) -> None:
        """Test that to_yaml produces valid YAML."""
        config = QualityGatesConfig()
        yaml_str = to_yaml(config)

        # Verify it's valid YAML by parsing it
        parsed = yaml.safe_load(yaml_str)
        assert "quality_gates" in parsed
        assert "version" in parsed

    def test_serialized_yaml_contains_all_sections(self) -> None:
        """Test that serialized YAML contains all config sections."""
        config = QualityGatesConfig()
        yaml_str = to_yaml(config)

        parsed = yaml.safe_load(yaml_str)
        quality_gates = parsed["quality_gates"]

        assert "precommit" in quality_gates
        assert "pr_automation" in quality_gates
        assert "human_review" in quality_gates
        assert "exclusions" in quality_gates

    def test_roundtrip_serialization(self, tmp_path: Path) -> None:
        """Test config survives YAML roundtrip."""
        original = QualityGatesConfig(
            precommit=PreCommitConfig(timeout_seconds=99),
            pr_automation=PRAutomationConfig(auto_approve_clean=True),
        )

        yaml_str = to_yaml(original)

        # Write to file and reload
        config_file = tmp_path / "roundtrip.yaml"
        config_file.write_text(yaml_str)

        loaded = load_config(config_file)

        assert loaded.precommit.timeout_seconds == 99
        assert loaded.pr_automation.auto_approve_clean is True


class TestRealConfigFile:
    """Tests using the actual config file if it exists."""

    @pytest.fixture
    def real_config_path(self) -> Path:
        """Get path to real config file."""
        return Path("config/quality-gates.yaml")

    def test_load_real_config_if_exists(self, real_config_path: Path) -> None:
        """Test loading the real config file if it exists."""
        if not real_config_path.exists():
            pytest.skip("Real config file does not exist")

        config = load_config(real_config_path)

        # Verify basic structure
        assert config.precommit.enabled is True
        assert len(config.exclusions.paths) > 0
