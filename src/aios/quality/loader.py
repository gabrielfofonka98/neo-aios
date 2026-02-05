"""Quality gates configuration loader.

This module provides the ConfigLoader class and Pydantic models for loading
and validating quality gate configuration from YAML files.

Example:
    >>> from pathlib import Path
    >>> from aios.quality.loader import load_config, QualityGatesConfig
    >>> config = load_config(Path("config/quality-gates.yaml"))
    >>> config.precommit.block_on_ruff_error
    True
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any

import yaml
from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator

from aios.security.models import Severity

if TYPE_CHECKING:
    from aios.quality.config import GateConfig


logger = logging.getLogger(__name__)


class PreCommitConfig(BaseModel):
    """Configuration for the pre-commit gate.

    Attributes:
        enabled: Whether the pre-commit gate is enabled.
        block_on_ruff_error: Block commit on ruff lint errors.
        block_on_mypy_error: Block commit on mypy type errors.
        block_on_test_failure: Block commit on test failures.
        block_on_critical_security: Block commit on CRITICAL security findings.
        warn_on_high_security: Show warning for HIGH severity findings.
        timeout_seconds: Timeout for each check in seconds.
        run_fast_tests_only: Only run tests not marked as 'slow'.
        max_parallel_checks: Maximum concurrent checks.
    """

    enabled: bool = True
    block_on_ruff_error: bool = True
    block_on_mypy_error: bool = True
    block_on_test_failure: bool = True
    block_on_critical_security: bool = True
    warn_on_high_security: bool = True
    timeout_seconds: int = Field(default=120, ge=10, le=600)
    run_fast_tests_only: bool = True
    max_parallel_checks: int = Field(default=4, ge=1, le=16)


class PRAutomationConfig(BaseModel):
    """Configuration for the PR automation gate.

    Attributes:
        enabled: Whether the PR automation gate is enabled.
        block_severities: List of severities that block PR merge.
        warn_severities: List of severities that show warnings.
        audit_timeout_seconds: Timeout for full security audit.
        auto_approve_clean: Auto-approve PRs with no findings.
    """

    enabled: bool = True
    block_severities: list[str] = Field(default_factory=lambda: ["CRITICAL", "HIGH"])
    warn_severities: list[str] = Field(default_factory=lambda: ["MEDIUM"])
    audit_timeout_seconds: int = Field(default=300, ge=60, le=1800)
    auto_approve_clean: bool = False

    @field_validator("block_severities", "warn_severities")
    @classmethod
    def validate_severities(cls, v: list[str]) -> list[str]:
        """Validate that all severities are valid."""
        valid_severities = {s.value.upper() for s in Severity}
        for sev in v:
            if sev.upper() not in valid_severities:
                raise ValueError(
                    f"Invalid severity '{sev}'. "
                    f"Valid values: {sorted(valid_severities)}"
                )
        return [s.upper() for s in v]

    def get_block_severities(self) -> list[Severity]:
        """Get block severities as Severity enum values."""
        return [Severity(s.lower()) for s in self.block_severities]

    def get_warn_severities(self) -> list[Severity]:
        """Get warn severities as Severity enum values."""
        return [Severity(s.lower()) for s in self.warn_severities]


class HumanReviewConfig(BaseModel):
    """Configuration for the human review gate.

    Attributes:
        enabled: Whether the human review gate is enabled.
        sensitive_paths: Paths that require manager approval.
        architecture_paths: Paths that require architect review.
        security_paths: Paths that require security lead review.
        large_pr_threshold: Lines changed that trigger 2-approver requirement.
        require_tech_lead: Whether tech lead approval is always required.
    """

    enabled: bool = True
    sensitive_paths: list[str] = Field(
        default_factory=lambda: [
            "config/",
            ".env",
            "credentials",
            "pyproject.toml",
        ]
    )
    architecture_paths: list[str] = Field(
        default_factory=lambda: [
            "src/aios/agents/",
            "src/aios/core/",
            ".aios-core/",
            "agents/",
        ]
    )
    security_paths: list[str] = Field(
        default_factory=lambda: [
            "src/aios/security/",
            "security/",
            "auth/",
        ]
    )
    large_pr_threshold: int = Field(default=500, ge=100, le=5000)
    require_tech_lead: bool = True


class ExclusionsConfig(BaseModel):
    """Configuration for exclusions from quality checks.

    Attributes:
        paths: Paths to exclude from all quality checks.
        validators: Validator IDs to disable.
        file_patterns: File patterns to exclude (glob patterns).
    """

    paths: list[str] = Field(
        default_factory=lambda: [
            "tests/fixtures/",
            "docs/",
            "__pycache__/",
            ".git/",
            ".venv/",
            "node_modules/",
        ]
    )
    validators: list[str] = Field(default_factory=list)
    file_patterns: list[str] = Field(
        default_factory=lambda: [
            "*.min.js",
            "*.bundle.js",
        ]
    )


class QualityGatesConfig(BaseModel):
    """Root configuration for all quality gates.

    Attributes:
        precommit: Pre-commit gate configuration.
        pr_automation: PR automation gate configuration.
        human_review: Human review gate configuration.
        exclusions: Exclusions configuration.
        version: Configuration schema version.
    """

    precommit: PreCommitConfig = Field(default_factory=PreCommitConfig)
    pr_automation: PRAutomationConfig = Field(default_factory=PRAutomationConfig)
    human_review: HumanReviewConfig = Field(default_factory=HumanReviewConfig)
    exclusions: ExclusionsConfig = Field(default_factory=ExclusionsConfig)
    version: str = "1.0"


def load_config(path: Path) -> QualityGatesConfig:
    """Load quality gates configuration from a YAML file.

    Args:
        path: Path to the YAML configuration file.

    Returns:
        QualityGatesConfig with loaded or default values.

    Raises:
        ValueError: If the YAML structure is invalid.

    Example:
        >>> config = load_config(Path("config/quality-gates.yaml"))
        >>> config.precommit.enabled
        True
    """
    if not path.exists():
        logger.warning("Config file not found at %s, using defaults", path)
        return QualityGatesConfig()

    try:
        with path.open("r", encoding="utf-8") as f:
            raw_config = yaml.safe_load(f)

        if raw_config is None:
            logger.warning("Empty config file at %s, using defaults", path)
            return QualityGatesConfig()

        # Extract quality_gates section if present
        if "quality_gates" in raw_config:
            config_data = raw_config["quality_gates"]
            # Preserve version from root
            if "version" in raw_config:
                config_data["version"] = raw_config["version"]
        else:
            config_data = raw_config

        return QualityGatesConfig.model_validate(config_data)

    except yaml.YAMLError as e:
        logger.error("Failed to parse YAML at %s: %s", path, e)
        raise ValueError(f"Invalid YAML in config file: {e}") from e
    except Exception as e:
        logger.error("Failed to load config from %s: %s", path, e)
        raise ValueError(f"Failed to load config: {e}") from e


def load_config_or_default(path: Path | None = None) -> QualityGatesConfig:
    """Load config from path or return default config.

    A convenience function that handles missing paths gracefully.

    Args:
        path: Optional path to config file. If None, returns defaults.

    Returns:
        QualityGatesConfig with loaded or default values.

    Example:
        >>> config = load_config_or_default()
        >>> config.precommit.block_on_ruff_error
        True
    """
    if path is None:
        return QualityGatesConfig()

    return load_config(path)


def _find_config_file() -> Path | None:
    """Find the quality gates config file in standard locations.

    Searches in order:
    1. config/quality-gates.yaml
    2. .aios-custom/config/quality-gates.yaml
    3. quality-gates.yaml

    Returns:
        Path to config file if found, None otherwise.
    """
    search_paths = [
        Path("config/quality-gates.yaml"),
        Path(".aios-custom/config/quality-gates.yaml"),
        Path("quality-gates.yaml"),
    ]

    for path in search_paths:
        if path.exists():
            logger.debug("Found config at %s", path)
            return path

    return None


def get_default_config() -> QualityGatesConfig:
    """Get the default quality gates configuration.

    Tries to load from standard locations, falls back to defaults.

    Returns:
        QualityGatesConfig with loaded or default values.

    Example:
        >>> config = get_default_config()
        >>> isinstance(config, QualityGatesConfig)
        True
    """
    config_path = _find_config_file()
    return load_config_or_default(config_path)


class ConfigLoader:
    """Loader class for quality gates configuration.

    Provides caching and reload functionality for configuration.

    Attributes:
        path: Path to the configuration file.

    Example:
        >>> loader = ConfigLoader(Path("config/quality-gates.yaml"))
        >>> config = loader.load()
        >>> config.precommit.enabled
        True
    """

    _instance: ConfigLoader | None = None

    def __init__(self, path: Path | None = None) -> None:
        """Initialize the config loader.

        Args:
            path: Optional path to config file. If None, searches standard locations.
        """
        self._path = path or _find_config_file()
        self._config: QualityGatesConfig | None = None

    @property
    def path(self) -> Path | None:
        """Get the configuration file path."""
        return self._path

    def load(self, *, reload: bool = False) -> QualityGatesConfig:
        """Load the configuration.

        Args:
            reload: If True, force reload from file even if cached.

        Returns:
            QualityGatesConfig with loaded values.

        Example:
            >>> loader = ConfigLoader()
            >>> config = loader.load()
            >>> updated_config = loader.load(reload=True)
        """
        if self._config is not None and not reload:
            return self._config

        self._config = load_config_or_default(self._path)
        return self._config

    def reload(self) -> QualityGatesConfig:
        """Force reload configuration from file.

        Returns:
            QualityGatesConfig with freshly loaded values.
        """
        return self.load(reload=True)

    def to_gate_config(self) -> GateConfig:
        """Convert to legacy GateConfig for backwards compatibility.

        Returns:
            GateConfig instance with values from loaded config.
        """
        from aios.quality.config import GateConfig as LegacyGateConfig

        config = self.load()

        return LegacyGateConfig(
            block_on_critical=config.precommit.block_on_critical_security,
            block_on_ruff_error=config.precommit.block_on_ruff_error,
            block_on_mypy_error=config.precommit.block_on_mypy_error,
            block_on_test_failure=config.precommit.block_on_test_failure,
            warn_on_high=config.precommit.warn_on_high_security,
            run_fast_tests_only=config.precommit.run_fast_tests_only,
            timeout_seconds=float(config.precommit.timeout_seconds),
            max_parallel_checks=config.precommit.max_parallel_checks,
            excluded_paths=config.exclusions.paths,
        )


def get_loader() -> ConfigLoader:
    """Get the default config loader instance (singleton).

    Returns:
        The default ConfigLoader instance.
    """
    if ConfigLoader._instance is None:
        ConfigLoader._instance = ConfigLoader()
    return ConfigLoader._instance


def to_yaml(config: QualityGatesConfig) -> str:
    """Serialize configuration to YAML string.

    Args:
        config: Configuration to serialize.

    Returns:
        YAML string representation.

    Example:
        >>> config = QualityGatesConfig()
        >>> yaml_str = to_yaml(config)
        >>> "precommit:" in yaml_str
        True
    """
    data: dict[str, Any] = {
        "quality_gates": config.model_dump(exclude_defaults=False),
        "version": config.version,
    }
    # Remove version from nested quality_gates since it's at root
    if "version" in data["quality_gates"]:
        del data["quality_gates"]["version"]

    return yaml.dump(data, default_flow_style=False, sort_keys=False)


__all__ = [
    "ConfigLoader",
    "ExclusionsConfig",
    "HumanReviewConfig",
    "PRAutomationConfig",
    "PreCommitConfig",
    "QualityGatesConfig",
    "get_default_config",
    "get_loader",
    "load_config",
    "load_config_or_default",
    "to_yaml",
]
