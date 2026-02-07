"""Tests for blind validation quality gate.

Tests the BlindValidator class, Pydantic config models,
BlindContext sanitisation, trigger resolution, and validator mapping.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from aios.quality.blind_validation import ApprovalDecision
from aios.quality.blind_validation import BlindContext
from aios.quality.blind_validation import BlindValidationConfig
from aios.quality.blind_validation import BlindValidator
from aios.quality.blind_validation import FindingSeverity
from aios.quality.blind_validation import QualityGateIntegrationConfig
from aios.quality.blind_validation import ReportingConfig
from aios.quality.blind_validation import TriggersConfig
from aios.quality.blind_validation import ValidationFinding
from aios.quality.blind_validation import ValidationResult
from aios.quality.blind_validation import ValidatorContextConfig
from aios.quality.blind_validation import ValidatorsConfig
from aios.quality.blind_validation import ValidatorSpec

if TYPE_CHECKING:
    from pathlib import Path


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def default_config() -> BlindValidationConfig:
    """Return a default BlindValidationConfig."""
    return BlindValidationConfig()


@pytest.fixture()
def disabled_config() -> BlindValidationConfig:
    """Return a disabled BlindValidationConfig."""
    return BlindValidationConfig(enabled=False)


@pytest.fixture()
def validator(default_config: BlindValidationConfig) -> BlindValidator:
    """Return a BlindValidator with default config."""
    return BlindValidator(config=default_config)


@pytest.fixture()
def disabled_validator(disabled_config: BlindValidationConfig) -> BlindValidator:
    """Return a BlindValidator that is globally disabled."""
    return BlindValidator(config=disabled_config)


@pytest.fixture()
def sample_source_code() -> str:
    """Return sample source code for tests."""
    return 'def add(a: int, b: int) -> int:\n    """Add two numbers."""\n    return a + b\n'


@pytest.fixture()
def sample_requirements() -> str:
    """Return sample requirements text."""
    return "Implement a function that adds two integers and returns the result."


# ---------------------------------------------------------------------------
# BlindContext — sanitisation guarantees
# ---------------------------------------------------------------------------


class TestBlindContextSanitisation:
    """Verify that BlindContext does NOT contain biasing information."""

    def test_context_does_not_have_developer_conversation(self) -> None:
        """BlindContext must never contain developer_conversation."""
        field_names = set(BlindContext.model_fields.keys())
        assert "developer_conversation" not in field_names

    def test_context_does_not_have_intermediate_decisions(self) -> None:
        """BlindContext must never contain intermediate_decisions."""
        field_names = set(BlindContext.model_fields.keys())
        assert "intermediate_decisions" not in field_names

    def test_context_does_not_have_developer_reasoning(self) -> None:
        """BlindContext must never contain developer_reasoning."""
        field_names = set(BlindContext.model_fields.keys())
        assert "developer_reasoning" not in field_names

    def test_context_does_not_have_previous_attempts(self) -> None:
        """BlindContext must never contain previous_attempts."""
        field_names = set(BlindContext.model_fields.keys())
        assert "previous_attempts" not in field_names

    def test_context_does_not_have_implementation_notes(self) -> None:
        """BlindContext must never contain implementation_notes."""
        field_names = set(BlindContext.model_fields.keys())
        assert "implementation_notes" not in field_names

    def test_context_does_not_have_design_alternatives(self) -> None:
        """BlindContext must never contain design_alternatives."""
        field_names = set(BlindContext.model_fields.keys())
        assert "design_alternatives" not in field_names

    def test_context_does_not_have_subjective_explanations(self) -> None:
        """BlindContext must never contain subjective_explanations."""
        field_names = set(BlindContext.model_fields.keys())
        assert "subjective_explanations" not in field_names

    def test_context_contains_source_code(
        self,
        sample_source_code: str,
    ) -> None:
        """BlindContext must contain source_code."""
        ctx = BlindContext(source_code=sample_source_code)
        assert ctx.source_code == sample_source_code

    def test_context_contains_requirements(
        self,
        sample_source_code: str,
        sample_requirements: str,
    ) -> None:
        """BlindContext must contain requirements."""
        ctx = BlindContext(
            source_code=sample_source_code,
            requirements=sample_requirements,
        )
        assert ctx.requirements == sample_requirements

    def test_context_allows_quality_standards(
        self,
        sample_source_code: str,
    ) -> None:
        """BlindContext must allow quality_standards."""
        standards = "# Standards\n- Use type hints\n"
        ctx = BlindContext(
            source_code=sample_source_code,
            quality_standards=standards,
        )
        assert ctx.quality_standards == standards


# ---------------------------------------------------------------------------
# prepare_blind_context
# ---------------------------------------------------------------------------


class TestPrepareBlindContext:
    """Tests for BlindValidator.prepare_blind_context."""

    def test_returns_blind_context(
        self,
        validator: BlindValidator,
        sample_source_code: str,
    ) -> None:
        """prepare_blind_context returns a BlindContext instance."""
        ctx = validator.prepare_blind_context(source_code=sample_source_code)
        assert isinstance(ctx, BlindContext)

    def test_source_code_is_passed_through(
        self,
        validator: BlindValidator,
        sample_source_code: str,
    ) -> None:
        """Source code is included verbatim."""
        ctx = validator.prepare_blind_context(source_code=sample_source_code)
        assert ctx.source_code == sample_source_code

    def test_requirements_are_passed_through(
        self,
        validator: BlindValidator,
        sample_source_code: str,
        sample_requirements: str,
    ) -> None:
        """Requirements are included verbatim."""
        ctx = validator.prepare_blind_context(
            source_code=sample_source_code,
            requirements=sample_requirements,
        )
        assert ctx.requirements == sample_requirements

    def test_quality_standards_loaded_from_disk(
        self,
        tmp_path: Path,
    ) -> None:
        """quality_standards is populated from STANDARDS.md when present."""
        standards_dir = tmp_path / ".aios-custom"
        standards_dir.mkdir()
        standards_file = standards_dir / "STANDARDS.md"
        standards_content = "# Test Standards\nAlways use type hints.\n"
        standards_file.write_text(standards_content, encoding="utf-8")

        bv = BlindValidator(
            config=BlindValidationConfig(),
            project_root=tmp_path,
        )
        ctx = bv.prepare_blind_context(source_code="x = 1")
        assert ctx.quality_standards == standards_content

    def test_quality_standards_none_when_missing(
        self,
        tmp_path: Path,
    ) -> None:
        """quality_standards is None when STANDARDS.md does not exist."""
        bv = BlindValidator(
            config=BlindValidationConfig(),
            project_root=tmp_path,
        )
        ctx = bv.prepare_blind_context(source_code="x = 1")
        assert ctx.quality_standards is None

    def test_optional_fields_passed_through(
        self,
        validator: BlindValidator,
        sample_source_code: str,
    ) -> None:
        """Optional context fields are included when provided."""
        ctx = validator.prepare_blind_context(
            source_code=sample_source_code,
            acceptance_criteria="User can add numbers",
            file_paths=["src/math.py"],
            line_counts=15,
            commit_message="feat: add math module",
            test_results="10 passed",
            lint_errors="no errors",
            security_findings="clean",
            related_files=["src/utils.py"],
        )
        assert ctx.acceptance_criteria == "User can add numbers"
        assert ctx.file_paths == ["src/math.py"]
        assert ctx.line_counts == 15
        assert ctx.commit_message == "feat: add math module"
        assert ctx.test_results == "10 passed"
        assert ctx.lint_errors == "no errors"
        assert ctx.security_findings == "clean"
        assert ctx.related_files == ["src/utils.py"]


# ---------------------------------------------------------------------------
# should_apply
# ---------------------------------------------------------------------------


class TestShouldApply:
    """Tests for BlindValidator.should_apply."""

    def test_pr_review_always_applies(self, validator: BlindValidator) -> None:
        """pr_review is in the 'always' list."""
        assert validator.should_apply("pr_review") is True

    def test_security_audit_always_applies(self, validator: BlindValidator) -> None:
        """security_audit is in the 'always' list."""
        assert validator.should_apply("security_audit") is True

    def test_code_quality_gate_always_applies(self, validator: BlindValidator) -> None:
        """code_quality_gate is in the 'always' list."""
        assert validator.should_apply("code_quality_gate") is True

    def test_architecture_review_always_applies(self, validator: BlindValidator) -> None:
        """architecture_review is in the 'always' list."""
        assert validator.should_apply("architecture_review") is True

    def test_hotfix_never_applies(self, validator: BlindValidator) -> None:
        """hotfix is in the 'never' list."""
        assert validator.should_apply("hotfix") is False

    def test_documentation_only_never_applies(self, validator: BlindValidator) -> None:
        """documentation_only is in the 'never' list."""
        assert validator.should_apply("documentation_only") is False

    def test_config_changes_never_applies(self, validator: BlindValidator) -> None:
        """config_changes is in the 'never' list."""
        assert validator.should_apply("config_changes") is False

    def test_test_creation_never_applies(self, validator: BlindValidator) -> None:
        """test_creation is in the 'never' list."""
        assert validator.should_apply("test_creation") is False

    def test_dependency_update_never_applies(self, validator: BlindValidator) -> None:
        """dependency_update is in the 'never' list."""
        assert validator.should_apply("dependency_update") is False

    def test_optional_trigger_applies(self, validator: BlindValidator) -> None:
        """Optional triggers also return True."""
        assert validator.should_apply("refactor_review") is True
        assert validator.should_apply("bug_fix_review") is True
        assert validator.should_apply("feature_completion") is True

    def test_unknown_trigger_does_not_apply(self, validator: BlindValidator) -> None:
        """Unknown triggers return False."""
        assert validator.should_apply("unknown_trigger") is False

    def test_disabled_always_returns_false(
        self,
        disabled_validator: BlindValidator,
    ) -> None:
        """When disabled, should_apply returns False for everything."""
        assert disabled_validator.should_apply("pr_review") is False
        assert disabled_validator.should_apply("security_audit") is False
        assert disabled_validator.should_apply("hotfix") is False

    def test_disabled_for_always_triggers(
        self,
        disabled_validator: BlindValidator,
    ) -> None:
        """Disabled overrides even 'always' triggers."""
        for trigger in ["pr_review", "security_audit", "code_quality_gate", "architecture_review"]:
            assert disabled_validator.should_apply(trigger) is False


# ---------------------------------------------------------------------------
# get_validator
# ---------------------------------------------------------------------------


class TestGetValidator:
    """Tests for BlindValidator.get_validator."""

    def test_security_maps_to_qa(self, validator: BlindValidator) -> None:
        """security_audit trigger maps to 'qa' agent."""
        assert validator.get_validator("security_audit") == "qa"

    def test_pr_review_maps_to_qa_code(self, validator: BlindValidator) -> None:
        """pr_review trigger maps to 'qa-code' agent."""
        assert validator.get_validator("pr_review") == "qa-code"

    def test_code_quality_gate_maps_to_qa_code(self, validator: BlindValidator) -> None:
        """code_quality_gate trigger maps to 'qa-code' agent."""
        assert validator.get_validator("code_quality_gate") == "qa-code"

    def test_architecture_review_maps_to_architect(self, validator: BlindValidator) -> None:
        """architecture_review trigger maps to 'architect' agent."""
        assert validator.get_validator("architecture_review") == "architect"

    def test_bug_fix_review_maps_to_qa_functional(self, validator: BlindValidator) -> None:
        """bug_fix_review trigger maps to 'qa-functional' agent."""
        assert validator.get_validator("bug_fix_review") == "qa-functional"

    def test_feature_completion_maps_to_qa_functional(self, validator: BlindValidator) -> None:
        """feature_completion trigger maps to 'qa-functional' agent."""
        assert validator.get_validator("feature_completion") == "qa-functional"

    def test_unknown_trigger_raises(self, validator: BlindValidator) -> None:
        """Unknown trigger raises ValueError."""
        with pytest.raises(ValueError, match="No validator mapped"):
            validator.get_validator("unknown_trigger")

    def test_hotfix_raises(self, validator: BlindValidator) -> None:
        """hotfix has no validator mapping and raises ValueError."""
        with pytest.raises(ValueError, match="No validator mapped"):
            validator.get_validator("hotfix")


# ---------------------------------------------------------------------------
# get_validator_spec
# ---------------------------------------------------------------------------


class TestGetValidatorSpec:
    """Tests for BlindValidator.get_validator_spec."""

    def test_security_spec_has_opus_model(self, validator: BlindValidator) -> None:
        """Security validator spec uses opus model."""
        spec = validator.get_validator_spec("security_audit")
        assert spec.model == "opus"

    def test_functional_spec_has_sonnet_model(self, validator: BlindValidator) -> None:
        """Functional validator spec uses sonnet model."""
        spec = validator.get_validator_spec("bug_fix_review")
        assert spec.model == "sonnet"

    def test_spec_validates_list_is_populated(self, validator: BlindValidator) -> None:
        """Validator spec has a non-empty validates list."""
        spec = validator.get_validator_spec("pr_review")
        assert len(spec.validates) > 0

    def test_unknown_trigger_raises(self, validator: BlindValidator) -> None:
        """Unknown trigger raises ValueError."""
        with pytest.raises(ValueError, match="No validator mapped"):
            validator.get_validator_spec("hotfix")


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------


class TestConfigLoading:
    """Tests for configuration loading from YAML."""

    def test_default_config_is_valid(self) -> None:
        """Default config loads without errors."""
        config = BlindValidationConfig()
        assert config.enabled is True

    def test_default_has_excluded_context(self) -> None:
        """Default config has the expected excluded context keys."""
        config = BlindValidationConfig()
        assert "developer_conversation" in config.excluded_context
        assert "intermediate_decisions" in config.excluded_context
        assert "developer_reasoning" in config.excluded_context

    def test_load_from_yaml_file(self, tmp_path: Path) -> None:
        """Config loads correctly from a YAML file."""
        yaml_content = """
blind_validation:
  enabled: true
  triggers:
    always:
      - pr_review
    optional: []
    never:
      - hotfix
  excluded_context:
    - developer_conversation
"""
        config_file = tmp_path / "blind-validation.yaml"
        config_file.write_text(yaml_content, encoding="utf-8")

        bv = BlindValidator(config_path=config_file)
        assert bv.config.enabled is True
        assert "pr_review" in bv.config.triggers.always
        assert "hotfix" in bv.config.triggers.never

    def test_load_empty_yaml_returns_defaults(self, tmp_path: Path) -> None:
        """Empty YAML file returns default config."""
        config_file = tmp_path / "blind-validation.yaml"
        config_file.write_text("", encoding="utf-8")

        bv = BlindValidator(config_path=config_file)
        assert bv.config.enabled is True

    def test_load_invalid_yaml_raises(self, tmp_path: Path) -> None:
        """Invalid YAML raises ValueError."""
        config_file = tmp_path / "blind-validation.yaml"
        config_file.write_text("{{bad: yaml: [", encoding="utf-8")

        with pytest.raises(ValueError, match="Invalid YAML"):
            BlindValidator(config_path=config_file)

    def test_discover_config_in_aios_custom(self, tmp_path: Path) -> None:
        """Config is discovered from .aios-custom/config/ path."""
        config_dir = tmp_path / ".aios-custom" / "config"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "blind-validation.yaml"
        config_file.write_text(
            "blind_validation:\n  enabled: false\n",
            encoding="utf-8",
        )

        bv = BlindValidator(project_root=tmp_path)
        assert bv.config.enabled is False

    def test_missing_config_uses_defaults(self, tmp_path: Path) -> None:
        """When no config file exists, defaults are used."""
        bv = BlindValidator(project_root=tmp_path)
        assert bv.config.enabled is True
        assert len(bv.config.excluded_context) > 0


# ---------------------------------------------------------------------------
# Pydantic model tests
# ---------------------------------------------------------------------------


class TestPydanticModels:
    """Tests for the Pydantic configuration and result models."""

    def test_validator_context_config_defaults(self) -> None:
        """ValidatorContextConfig has sensible defaults."""
        cfg = ValidatorContextConfig()
        assert "source_code" in cfg.required
        assert "requirements" in cfg.required
        assert "quality_standards" in cfg.required
        assert "test_results" in cfg.optional
        assert "file_paths" in cfg.metadata

    def test_triggers_config_defaults(self) -> None:
        """TriggersConfig has the expected default lists."""
        cfg = TriggersConfig()
        assert "pr_review" in cfg.always
        assert "hotfix" in cfg.never
        assert "refactor_review" in cfg.optional

    def test_validator_spec_fields(self) -> None:
        """ValidatorSpec stores agent, model, and validates."""
        spec = ValidatorSpec(agent="qa-code", model="opus", validates=["style"])
        assert spec.agent == "qa-code"
        assert spec.model == "opus"
        assert spec.validates == ["style"]

    def test_validators_config_has_all_categories(self) -> None:
        """ValidatorsConfig has code_quality, security, functional, architecture."""
        cfg = ValidatorsConfig()
        assert cfg.code_quality.agent == "qa-code"
        assert cfg.security.agent == "qa"
        assert cfg.functional.agent == "qa-functional"
        assert cfg.architecture.agent == "architect"

    def test_quality_gate_integration_defaults(self) -> None:
        """QualityGateIntegrationConfig defaults are correct."""
        cfg = QualityGateIntegrationConfig()
        assert cfg.layer_2_component is True
        assert cfg.blocks_merge is True
        assert cfg.severity_threshold == "HIGH"
        assert cfg.human_review_input is True

    def test_reporting_config_defaults(self) -> None:
        """ReportingConfig defaults are correct."""
        cfg = ReportingConfig()
        assert cfg.format == "structured"
        assert cfg.location == "reports/code-quality/"
        assert "findings" in cfg.include_in_report
        assert "validator_reasoning" in cfg.exclude_from_report


# ---------------------------------------------------------------------------
# ValidationResult
# ---------------------------------------------------------------------------


class TestValidationResult:
    """Tests for the ValidationResult model."""

    def test_has_blockers_with_critical(self) -> None:
        """has_blockers is True when CRITICAL count > 0."""
        result = ValidationResult(
            approval_status=ApprovalDecision.REJECT,
            validator_agent="qa",
            validator_category="security",
            severity_counts={"CRITICAL": 1, "HIGH": 0, "MEDIUM": 0, "LOW": 0},
        )
        assert result.has_blockers is True

    def test_has_blockers_with_high(self) -> None:
        """has_blockers is True when HIGH count > 0."""
        result = ValidationResult(
            approval_status=ApprovalDecision.REQUEST_CHANGES,
            validator_agent="qa-code",
            validator_category="code_quality",
            severity_counts={"CRITICAL": 0, "HIGH": 2, "MEDIUM": 0, "LOW": 0},
        )
        assert result.has_blockers is True

    def test_no_blockers_with_medium_only(self) -> None:
        """has_blockers is False when only MEDIUM/LOW findings exist."""
        result = ValidationResult(
            approval_status=ApprovalDecision.APPROVE,
            validator_agent="qa-code",
            validator_category="code_quality",
            severity_counts={"CRITICAL": 0, "HIGH": 0, "MEDIUM": 3, "LOW": 1},
        )
        assert result.has_blockers is False

    def test_no_blockers_with_zero_counts(self) -> None:
        """has_blockers is False when all counts are zero."""
        result = ValidationResult(
            approval_status=ApprovalDecision.APPROVE,
            validator_agent="qa-code",
            validator_category="code_quality",
            severity_counts={"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0},
        )
        assert result.has_blockers is False

    def test_findings_list(self) -> None:
        """ValidationResult can hold ValidationFinding instances."""
        finding = ValidationFinding(
            title="Missing input validation",
            severity=FindingSeverity.HIGH,
            description="No validation on user input",
            file_path="src/handler.py",
            line_start=42,
            line_end=45,
            recommendation="Add input sanitisation",
        )
        result = ValidationResult(
            approval_status=ApprovalDecision.REQUEST_CHANGES,
            validator_agent="qa",
            validator_category="security",
            findings=[finding],
            severity_counts={"CRITICAL": 0, "HIGH": 1, "MEDIUM": 0, "LOW": 0},
        )
        assert len(result.findings) == 1
        assert result.findings[0].title == "Missing input validation"
        assert result.findings[0].severity == FindingSeverity.HIGH


# ---------------------------------------------------------------------------
# Excluded context keys
# ---------------------------------------------------------------------------


class TestExcludedContextKeys:
    """Tests for get_excluded_context_keys."""

    def test_returns_all_excluded_keys(self, validator: BlindValidator) -> None:
        """get_excluded_context_keys returns the full exclusion list."""
        keys = validator.get_excluded_context_keys()
        assert "developer_conversation" in keys
        assert "intermediate_decisions" in keys
        assert "previous_attempts" in keys
        assert "developer_reasoning" in keys
        assert "implementation_notes" in keys
        assert "design_alternatives" in keys
        assert "subjective_explanations" in keys

    def test_excluded_keys_match_config(self, validator: BlindValidator) -> None:
        """Excluded keys match what is in the config."""
        keys = validator.get_excluded_context_keys()
        assert keys == validator.config.excluded_context


# ---------------------------------------------------------------------------
# Trigger classification helpers
# ---------------------------------------------------------------------------


class TestTriggerClassification:
    """Tests for is_trigger_always and is_trigger_never."""

    def test_pr_review_is_always(self, validator: BlindValidator) -> None:
        """pr_review is classified as 'always'."""
        assert validator.is_trigger_always("pr_review") is True

    def test_hotfix_is_never(self, validator: BlindValidator) -> None:
        """hotfix is classified as 'never'."""
        assert validator.is_trigger_never("hotfix") is True

    def test_optional_is_neither_always_nor_never(self, validator: BlindValidator) -> None:
        """Optional triggers are not in 'always' or 'never'."""
        assert validator.is_trigger_always("refactor_review") is False
        assert validator.is_trigger_never("refactor_review") is False


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class TestEnums:
    """Tests for enum values."""

    def test_approval_decision_values(self) -> None:
        """ApprovalDecision has the expected members."""
        assert ApprovalDecision.APPROVE.value == "APPROVE"
        assert ApprovalDecision.REQUEST_CHANGES.value == "REQUEST_CHANGES"
        assert ApprovalDecision.REJECT.value == "REJECT"

    def test_finding_severity_values(self) -> None:
        """FindingSeverity has the expected members."""
        assert FindingSeverity.CRITICAL.value == "CRITICAL"
        assert FindingSeverity.HIGH.value == "HIGH"
        assert FindingSeverity.MEDIUM.value == "MEDIUM"
        assert FindingSeverity.LOW.value == "LOW"
