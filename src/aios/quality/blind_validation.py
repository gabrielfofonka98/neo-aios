"""Blind validation for quality gates.

This module provides the BlindValidator class that implements the blind
validation pattern: QA validators receive ONLY source code, requirements,
and quality standards — NEVER the developer's conversation context.

This eliminates confirmation bias by forcing validators to evaluate code
objectively against requirements, not against the developer's explanation
of why something was done a certain way.

Example:
    >>> from aios.quality.blind_validation import BlindValidator
    >>> validator = BlindValidator()
    >>> ctx = validator.prepare_blind_context(
    ...     source_code="def add(a: int, b: int) -> int: return a + b",
    ...     requirements="Implement addition function",
    ... )
    >>> ctx.source_code
    'def add(a: int, b: int) -> int: return a + b'
    >>> "developer_conversation" not in ctx.model_fields
    True
"""

from __future__ import annotations

import logging
from enum import Enum
from pathlib import Path
from typing import Any
from typing import ClassVar

import yaml
from pydantic import BaseModel
from pydantic import Field

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ApprovalDecision(Enum):
    """Final approval decision from a blind validator.

    Attributes:
        APPROVE: Code meets all requirements and standards.
        REQUEST_CHANGES: Code has issues that must be fixed.
        REJECT: Code fundamentally fails to meet requirements.
    """

    APPROVE = "APPROVE"
    REQUEST_CHANGES = "REQUEST_CHANGES"
    REJECT = "REJECT"


class FindingSeverity(Enum):
    """Severity level for a validation finding.

    Attributes:
        CRITICAL: Must fix before merge — security or data loss risk.
        HIGH: Must fix before merge — significant quality issue.
        MEDIUM: Should fix — code quality concern.
        LOW: Nice to have — minor improvement suggestion.
    """

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


# ---------------------------------------------------------------------------
# Configuration models (mirror of blind-validation.yaml)
# ---------------------------------------------------------------------------


class ValidatorContextConfig(BaseModel):
    """Configuration for what context a validator receives.

    Attributes:
        required: Required context items for validation.
        optional: Optional context items that may be included.
        metadata: Non-biasing metadata items.
    """

    required: list[str] = Field(default_factory=lambda: [
        "source_code",
        "requirements",
        "quality_standards",
        "acceptance_criteria",
        "api_contracts",
    ])
    optional: list[str] = Field(default_factory=lambda: [
        "test_results",
        "lint_errors",
        "security_findings",
        "related_files",
    ])
    metadata: list[str] = Field(default_factory=lambda: [
        "file_paths",
        "line_counts",
        "commit_message",
    ])


class TriggersConfig(BaseModel):
    """Configuration for when blind validation is triggered.

    Attributes:
        always: Triggers where blind validation always applies.
        optional: Triggers where blind validation is optional.
        never: Triggers where blind validation never applies.
    """

    always: list[str] = Field(default_factory=lambda: [
        "pr_review",
        "security_audit",
        "code_quality_gate",
        "architecture_review",
    ])
    optional: list[str] = Field(default_factory=lambda: [
        "refactor_review",
        "bug_fix_review",
        "feature_completion",
    ])
    never: list[str] = Field(default_factory=lambda: [
        "hotfix",
        "documentation_only",
        "config_changes",
        "test_creation",
        "dependency_update",
    ])


class ValidatorSpec(BaseModel):
    """Specification for a single validator category.

    Attributes:
        agent: Agent identifier (e.g. ``"qa-code"``).
        model: Model tier for the validator (e.g. ``"opus"``).
        validates: List of aspects this validator checks.
    """

    agent: str
    model: str = "opus"
    validates: list[str] = Field(default_factory=list)


class ValidatorsConfig(BaseModel):
    """Mapping from validation category to its validator spec.

    Attributes:
        code_quality: Validator spec for code quality checks.
        security: Validator spec for security checks.
        functional: Validator spec for functional checks.
        architecture: Validator spec for architecture checks.
    """

    code_quality: ValidatorSpec = Field(
        default_factory=lambda: ValidatorSpec(
            agent="qa-code",
            model="opus",
            validates=[
                "code_style",
                "type_safety",
                "error_handling",
                "performance",
                "maintainability",
            ],
        )
    )
    security: ValidatorSpec = Field(
        default_factory=lambda: ValidatorSpec(
            agent="qa",
            model="opus",
            validates=[
                "vulnerabilities",
                "authentication",
                "authorization",
                "secrets_exposure",
                "input_validation",
            ],
        )
    )
    functional: ValidatorSpec = Field(
        default_factory=lambda: ValidatorSpec(
            agent="qa-functional",
            model="sonnet",
            validates=[
                "acceptance_criteria",
                "edge_cases",
                "error_cases",
                "integration",
                "regression",
            ],
        )
    )
    architecture: ValidatorSpec = Field(
        default_factory=lambda: ValidatorSpec(
            agent="architect",
            model="opus",
            validates=[
                "design_adherence",
                "patterns_compliance",
                "coupling",
                "consistency",
                "future_proofing",
            ],
        )
    )


class TrivialChangeConfig(BaseModel):
    """Configuration for trivial changes that can be auto-approved.

    Attributes:
        max_lines: Maximum number of changed lines to qualify.
        types: Types of changes considered trivial.
    """

    max_lines: int = 10
    types: list[str] = Field(default_factory=lambda: [
        "typo_fix",
        "comment_update",
        "formatting",
    ])


class DependencyUpdateConfig(BaseModel):
    """Configuration for dependency updates.

    Attributes:
        automated: Whether update was automated.
        pre_approved: Whether it is pre-approved.
    """

    automated: bool = True
    pre_approved: bool = True


class ExemptionsConfig(BaseModel):
    """Exemption rules for blind validation.

    Attributes:
        auto_approve: List of auto-approve scenario configs.
        relaxed: List of relaxed validation scenarios.
        manual_skip: Manual skip configuration.
    """

    auto_approve: list[dict[str, Any]] = Field(default_factory=list)
    relaxed: list[dict[str, Any]] = Field(default_factory=list)
    manual_skip: dict[str, Any] = Field(default_factory=lambda: {
        "require_manager_approval": True,
        "require_justification": True,
        "log_to": ".aios/validation-skips.log",
    })


class QualityGateIntegrationConfig(BaseModel):
    """How blind validation integrates with quality gates.

    Attributes:
        layer_2_component: Whether it runs as part of Layer 2.
        blocks_merge: Whether findings can block merge.
        severity_threshold: Minimum severity to block merge.
        human_review_input: Whether results feed into Layer 3.
    """

    layer_2_component: bool = True
    blocks_merge: bool = True
    severity_threshold: str = "HIGH"
    human_review_input: bool = True


class ReportingConfig(BaseModel):
    """Reporting configuration for validation results.

    Attributes:
        format: Report format type.
        location: Where reports are saved.
        filename_pattern: Pattern for report filenames.
        include_in_report: Items to include.
        exclude_from_report: Items to exclude.
    """

    format: str = "structured"
    location: str = "reports/code-quality/"
    filename_pattern: str = "YYYY-MM-DD-{pr_number}-blind-validation.md"
    include_in_report: list[str] = Field(default_factory=lambda: [
        "findings",
        "severity_breakdown",
        "requirements_check",
        "standards_adherence",
        "approval_decision",
    ])
    exclude_from_report: list[str] = Field(default_factory=lambda: [
        "validator_reasoning",
        "comparative_analysis",
        "subjective_opinions",
    ])


class BlindValidationConfig(BaseModel):
    """Root configuration for blind validation, mirrors blind-validation.yaml.

    Attributes:
        enabled: Global toggle for blind validation.
        validator_context: What context validators receive.
        excluded_context: What context is always excluded.
        triggers: When blind validation is applied.
        validators: Which agent validates each category.
        exemptions: When validation can be skipped.
        quality_gate_integration: Quality gate integration settings.
        reporting: Reporting settings.
    """

    enabled: bool = True
    validator_context: ValidatorContextConfig = Field(
        default_factory=ValidatorContextConfig
    )
    excluded_context: list[str] = Field(default_factory=lambda: [
        "developer_conversation",
        "intermediate_decisions",
        "previous_attempts",
        "developer_reasoning",
        "implementation_notes",
        "design_alternatives",
        "subjective_explanations",
    ])
    triggers: TriggersConfig = Field(default_factory=TriggersConfig)
    validators: ValidatorsConfig = Field(default_factory=ValidatorsConfig)
    exemptions: ExemptionsConfig = Field(default_factory=ExemptionsConfig)
    quality_gate_integration: QualityGateIntegrationConfig = Field(
        default_factory=QualityGateIntegrationConfig
    )
    reporting: ReportingConfig = Field(default_factory=ReportingConfig)


# ---------------------------------------------------------------------------
# Blind context (the sanitised context sent to validators)
# ---------------------------------------------------------------------------


class BlindContext(BaseModel):
    """Sanitised context for blind validation.

    Contains ONLY the information a validator needs to evaluate code
    objectively.  Developer conversation, reasoning, and intermediate
    decisions are explicitly excluded.

    Attributes:
        source_code: The source code to validate.
        requirements: Original story/task/spec requirements.
        quality_standards: Content of STANDARDS.md.
        acceptance_criteria: Acceptance criteria from the story.
        api_contracts: Expected interfaces/types.
        file_paths: Paths of changed files (metadata).
        line_counts: Number of changed lines (metadata).
        commit_message: High-level summary (metadata).
        test_results: Optional test pass/fail status.
        lint_errors: Optional ruff/mypy output.
        security_findings: Optional prior security report.
        related_files: Optional files that import/use this code.
    """

    source_code: str
    requirements: str | None = None
    quality_standards: str | None = None
    acceptance_criteria: str | None = None
    api_contracts: str | None = None
    file_paths: list[str] = Field(default_factory=list)
    line_counts: int = 0
    commit_message: str | None = None
    test_results: str | None = None
    lint_errors: str | None = None
    security_findings: str | None = None
    related_files: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Validation result
# ---------------------------------------------------------------------------


class ValidationFinding(BaseModel):
    """A single finding from blind validation.

    Attributes:
        title: Short title describing the issue.
        severity: Severity level of the finding.
        description: Detailed description of the issue.
        file_path: File where the issue was found.
        line_start: Starting line of the issue.
        line_end: Ending line of the issue.
        recommendation: Suggested fix.
    """

    title: str
    severity: FindingSeverity
    description: str
    file_path: str | None = None
    line_start: int | None = None
    line_end: int | None = None
    recommendation: str | None = None


class ValidationResult(BaseModel):
    """Result of a blind validation run.

    Attributes:
        approval_status: Final approval decision.
        validator_agent: Agent that performed the validation.
        validator_category: Category of validation performed.
        findings: List of findings discovered.
        requirements_gaps: Unmet acceptance criteria.
        standards_violations: STANDARDS.md deviations.
        severity_counts: Count of findings by severity.
    """

    approval_status: ApprovalDecision
    validator_agent: str
    validator_category: str
    findings: list[ValidationFinding] = Field(default_factory=list)
    requirements_gaps: list[str] = Field(default_factory=list)
    standards_violations: list[str] = Field(default_factory=list)
    severity_counts: dict[str, int] = Field(default_factory=lambda: {
        "CRITICAL": 0,
        "HIGH": 0,
        "MEDIUM": 0,
        "LOW": 0,
    })

    @property
    def has_blockers(self) -> bool:
        """Whether there are CRITICAL or HIGH findings."""
        return (
            self.severity_counts.get("CRITICAL", 0) > 0
            or self.severity_counts.get("HIGH", 0) > 0
        )


# ---------------------------------------------------------------------------
# Validator category to config key mapping
# ---------------------------------------------------------------------------

_TRIGGER_TO_VALIDATOR: dict[str, str] = {
    "pr_review": "code_quality",
    "code_quality_gate": "code_quality",
    "security_audit": "security",
    "architecture_review": "architecture",
    "refactor_review": "code_quality",
    "bug_fix_review": "functional",
    "feature_completion": "functional",
}


# ---------------------------------------------------------------------------
# BlindValidator — the main class
# ---------------------------------------------------------------------------


class BlindValidator:
    """Orchestrates blind validation for quality gates.

    Reads ``blind-validation.yaml``, prepares sanitised contexts for
    validators, and determines which validator to invoke for each
    trigger type.

    Attributes:
        config: The loaded BlindValidationConfig.

    Example:
        >>> validator = BlindValidator()
        >>> validator.should_apply("pr_review")
        True
        >>> validator.get_validator("security_audit")
        'qa'
    """

    # Standard locations for the config file (searched in order).
    _CONFIG_SEARCH_PATHS: ClassVar[list[str]] = [
        ".aios-custom/config/blind-validation.yaml",
        "config/blind-validation.yaml",
        "blind-validation.yaml",
    ]

    # Standard location for quality standards.
    _STANDARDS_PATH: ClassVar[str] = ".aios-custom/STANDARDS.md"

    def __init__(
        self,
        config: BlindValidationConfig | None = None,
        *,
        config_path: Path | None = None,
        project_root: Path | None = None,
    ) -> None:
        """Initialise the BlindValidator.

        Args:
            config: Optional pre-built config. Takes precedence.
            config_path: Optional explicit path to the YAML config.
            project_root: Optional project root for resolving paths.
        """
        self._project_root = project_root or Path.cwd()

        if config is not None:
            self._config = config
        elif config_path is not None:
            self._config = self._load_config(config_path)
        else:
            self._config = self._discover_and_load_config()

    # -- Public properties ---------------------------------------------------

    @property
    def config(self) -> BlindValidationConfig:
        """Get the active blind validation configuration."""
        return self._config

    @property
    def enabled(self) -> bool:
        """Whether blind validation is globally enabled."""
        return self._config.enabled

    # -- Public methods ------------------------------------------------------

    def prepare_blind_context(
        self,
        source_code: str,
        requirements: str | None = None,
        *,
        acceptance_criteria: str | None = None,
        api_contracts: str | None = None,
        file_paths: list[str] | None = None,
        line_counts: int = 0,
        commit_message: str | None = None,
        test_results: str | None = None,
        lint_errors: str | None = None,
        security_findings: str | None = None,
        related_files: list[str] | None = None,
    ) -> BlindContext:
        """Prepare a sanitised context for a blind validator.

        Loads quality standards from ``STANDARDS.md`` and builds a
        :class:`BlindContext` that contains ONLY what the validator
        needs.  Developer conversation, reasoning, and intermediate
        decisions are never included.

        Args:
            source_code: The source code to validate.
            requirements: Original story/task/spec requirements.
            acceptance_criteria: Acceptance criteria from the story.
            api_contracts: Expected interfaces/types.
            file_paths: Changed file paths.
            line_counts: Number of changed lines.
            commit_message: High-level summary.
            test_results: Optional test pass/fail status.
            lint_errors: Optional ruff/mypy output.
            security_findings: Optional prior security report.
            related_files: Optional files importing this code.

        Returns:
            BlindContext with sanitised data for the validator.
        """
        quality_standards = self._load_quality_standards()

        return BlindContext(
            source_code=source_code,
            requirements=requirements,
            quality_standards=quality_standards,
            acceptance_criteria=acceptance_criteria,
            api_contracts=api_contracts,
            file_paths=file_paths or [],
            line_counts=line_counts,
            commit_message=commit_message,
            test_results=test_results,
            lint_errors=lint_errors,
            security_findings=security_findings,
            related_files=related_files or [],
        )

    def should_apply(self, trigger: str) -> bool:
        """Whether blind validation should apply for the given trigger.

        Checks the ``always`` and ``optional`` trigger lists in the
        config.  Returns ``False`` if the feature is globally disabled
        or if the trigger is in the ``never`` list.

        Args:
            trigger: Trigger identifier (e.g. ``"pr_review"``).

        Returns:
            True if blind validation should be applied.
        """
        if not self._config.enabled:
            return False

        if trigger in self._config.triggers.never:
            return False

        if trigger in self._config.triggers.always:
            return True

        return trigger in self._config.triggers.optional

    def get_validator(self, trigger: str) -> str:
        """Get the agent identifier for the validator responsible for a trigger.

        Uses the ``_TRIGGER_TO_VALIDATOR`` mapping to resolve the
        validator category, then looks up the agent from the config.

        Args:
            trigger: Trigger identifier (e.g. ``"security_audit"``).

        Returns:
            Agent identifier string (e.g. ``"qa"``, ``"qa-code"``).

        Raises:
            ValueError: If the trigger has no mapped validator.
        """
        category = _TRIGGER_TO_VALIDATOR.get(trigger)
        if category is None:
            raise ValueError(
                f"No validator mapped for trigger '{trigger}'. "
                f"Known triggers: {sorted(_TRIGGER_TO_VALIDATOR.keys())}"
            )

        spec = self._get_validator_spec(category)
        return spec.agent

    def get_validator_spec(self, trigger: str) -> ValidatorSpec:
        """Get the full validator spec for a trigger.

        Args:
            trigger: Trigger identifier.

        Returns:
            ValidatorSpec with agent, model, and validation aspects.

        Raises:
            ValueError: If the trigger has no mapped validator.
        """
        category = _TRIGGER_TO_VALIDATOR.get(trigger)
        if category is None:
            raise ValueError(
                f"No validator mapped for trigger '{trigger}'. "
                f"Known triggers: {sorted(_TRIGGER_TO_VALIDATOR.keys())}"
            )
        return self._get_validator_spec(category)

    def get_excluded_context_keys(self) -> list[str]:
        """Get the list of context keys that are always excluded.

        Returns:
            List of excluded context key names.
        """
        return list(self._config.excluded_context)

    def is_trigger_always(self, trigger: str) -> bool:
        """Whether a trigger is in the ``always`` blind-validate list.

        Args:
            trigger: Trigger identifier.

        Returns:
            True if the trigger always requires blind validation.
        """
        return trigger in self._config.triggers.always

    def is_trigger_never(self, trigger: str) -> bool:
        """Whether a trigger is in the ``never`` blind-validate list.

        Args:
            trigger: Trigger identifier.

        Returns:
            True if the trigger should never be blind-validated.
        """
        return trigger in self._config.triggers.never

    # -- Private helpers -----------------------------------------------------

    def _get_validator_spec(self, category: str) -> ValidatorSpec:
        """Resolve a validator spec from the validators config.

        Args:
            category: Validator category (e.g. ``"code_quality"``).

        Returns:
            The ValidatorSpec for the category.

        Raises:
            ValueError: If the category is unknown.
        """
        validators = self._config.validators
        spec_map: dict[str, ValidatorSpec] = {
            "code_quality": validators.code_quality,
            "security": validators.security,
            "functional": validators.functional,
            "architecture": validators.architecture,
        }
        spec = spec_map.get(category)
        if spec is None:
            raise ValueError(
                f"Unknown validator category '{category}'. "
                f"Known: {sorted(spec_map.keys())}"
            )
        return spec

    def _load_quality_standards(self) -> str | None:
        """Load quality standards from STANDARDS.md.

        Returns:
            File contents as string, or None if not found.
        """
        standards_path = self._project_root / self._STANDARDS_PATH
        if not standards_path.exists():
            logger.debug("STANDARDS.md not found at %s", standards_path)
            return None

        try:
            return standards_path.read_text(encoding="utf-8")
        except OSError as exc:
            logger.warning("Failed to read STANDARDS.md: %s", exc)
            return None

    def _discover_and_load_config(self) -> BlindValidationConfig:
        """Search standard locations and load config.

        Returns:
            Loaded config, or defaults if no file is found.
        """
        for relative_path in self._CONFIG_SEARCH_PATHS:
            candidate = self._project_root / relative_path
            if candidate.exists():
                logger.debug("Found blind-validation config at %s", candidate)
                return self._load_config(candidate)

        logger.debug(
            "No blind-validation config found, using defaults"
        )
        return BlindValidationConfig()

    def _load_config(self, path: Path) -> BlindValidationConfig:
        """Load and validate config from a YAML file.

        Args:
            path: Path to the YAML file.

        Returns:
            Validated BlindValidationConfig.

        Raises:
            ValueError: If YAML is invalid or cannot be parsed.
        """
        try:
            with path.open("r", encoding="utf-8") as f:
                raw: Any = yaml.safe_load(f)

            if raw is None:
                logger.warning("Empty config at %s, using defaults", path)
                return BlindValidationConfig()

            # The YAML uses ``blind_validation:`` as the root key.
            if isinstance(raw, dict) and "blind_validation" in raw:
                raw = raw["blind_validation"]

            return BlindValidationConfig.model_validate(raw)

        except yaml.YAMLError as exc:
            raise ValueError(
                f"Invalid YAML in {path}: {exc}"
            ) from exc
        except Exception as exc:
            raise ValueError(
                f"Failed to load blind validation config from {path}: {exc}"
            ) from exc


# ---------------------------------------------------------------------------
# Module-level exports
# ---------------------------------------------------------------------------

__all__ = [
    "ApprovalDecision",
    "BlindContext",
    "BlindValidationConfig",
    "BlindValidator",
    "ExemptionsConfig",
    "FindingSeverity",
    "QualityGateIntegrationConfig",
    "ReportingConfig",
    "TriggersConfig",
    "ValidationFinding",
    "ValidationResult",
    "ValidatorContextConfig",
    "ValidatorSpec",
    "ValidatorsConfig",
]
