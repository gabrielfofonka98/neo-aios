"""Tests for the auto-fix framework.

This module tests the AutoFixFramework, BaseFixer, and related models.
"""

from datetime import datetime
from pathlib import Path

import pytest

from aios.autofix import AutoFixFramework
from aios.autofix import BaseFixer
from aios.autofix import FixBatchResult
from aios.autofix import FixConfidence
from aios.autofix import FixResult
from aios.autofix import FixStatus
from aios.autofix import FixSuggestion
from aios.security.models import CodeLocation
from aios.security.models import FindingCategory
from aios.security.models import SecurityFinding
from aios.security.models import Severity


# =============================================================================
# Test Fixtures
# =============================================================================


class XSSFixer(BaseFixer):
    """Test fixer for XSS findings."""

    @property
    def fixer_id(self) -> str:
        return "xss-sanitizer"

    @property
    def name(self) -> str:
        return "XSS Sanitizer"

    @property
    def description(self) -> str:
        return "Sanitizes user input to prevent XSS"

    @property
    def priority(self) -> int:
        return 200

    @property
    def supported_categories(self) -> list[str]:
        return ["xss"]

    def can_fix(self, finding: SecurityFinding) -> bool:
        return finding.category == FindingCategory.XSS

    def generate_fix(self, finding: SecurityFinding) -> FixSuggestion:
        if finding.fix_snippet:
            old_code = finding.location.snippet or ""
            return FixSuggestion(
                old_code=old_code,
                new_code=finding.fix_snippet,
                explanation="Sanitize user input before rendering",
                confidence=FixConfidence.HIGH,
            )
        return FixSuggestion(
            old_code=finding.location.snippet or "",
            new_code="sanitized_output",
            explanation="Apply XSS sanitization",
            confidence=FixConfidence.MEDIUM,
        )


class InjectionFixer(BaseFixer):
    """Test fixer for injection findings."""

    @property
    def fixer_id(self) -> str:
        return "injection-parameterizer"

    @property
    def name(self) -> str:
        return "Injection Parameterizer"

    @property
    def priority(self) -> int:
        return 100

    @property
    def supported_categories(self) -> list[str]:
        return ["injection"]

    def can_fix(self, finding: SecurityFinding) -> bool:
        return finding.category == FindingCategory.INJECTION

    def generate_fix(self, finding: SecurityFinding) -> FixSuggestion:
        return FixSuggestion(
            old_code=finding.location.snippet or "",
            new_code="parameterized_query",
            explanation="Use parameterized queries",
            confidence=FixConfidence.HIGH,
        )


@pytest.fixture
def xss_finding() -> SecurityFinding:
    """Create a sample XSS finding."""
    return SecurityFinding(
        id="xss-001",
        validator_id="sec-xss",
        severity=Severity.HIGH,
        category=FindingCategory.XSS,
        title="XSS vulnerability detected",
        description="User input passed directly to unsafe render method",
        location=CodeLocation(
            file_path="test_file.tsx",
            line_start=42,
            line_end=42,
            snippet="unsafe_html_render(userInput)",
        ),
        recommendation="Sanitize input before rendering",
        auto_fixable=True,
        fix_snippet="safe_html_render(DOMPurify.sanitize(userInput))",
    )


@pytest.fixture
def injection_finding() -> SecurityFinding:
    """Create a sample injection finding."""
    return SecurityFinding(
        id="injection-001",
        validator_id="sec-injection",
        severity=Severity.CRITICAL,
        category=FindingCategory.INJECTION,
        title="SQL injection vulnerability",
        description="User input concatenated into SQL query",
        location=CodeLocation(
            file_path="test_db.py",
            line_start=100,
            line_end=100,
            snippet="query = f'SELECT * FROM users WHERE id = {user_id}'",
        ),
        recommendation="Use parameterized queries",
        auto_fixable=True,
    )


@pytest.fixture
def non_fixable_finding() -> SecurityFinding:
    """Create a finding that is not auto-fixable."""
    return SecurityFinding(
        id="config-001",
        validator_id="sec-config",
        severity=Severity.MEDIUM,
        category=FindingCategory.CONFIG,
        title="Insecure configuration",
        description="Debug mode enabled in production",
        location=CodeLocation(
            file_path="config.yaml",
            line_start=10,
            line_end=10,
        ),
        recommendation="Disable debug mode",
        auto_fixable=False,
    )


@pytest.fixture
def xss_fixer() -> XSSFixer:
    """Create XSS fixer."""
    return XSSFixer()


@pytest.fixture
def injection_fixer() -> InjectionFixer:
    """Create injection fixer."""
    return InjectionFixer()


@pytest.fixture
def framework() -> AutoFixFramework:
    """Create empty framework."""
    return AutoFixFramework()


@pytest.fixture
def framework_with_fixers(xss_fixer: XSSFixer, injection_fixer: InjectionFixer) -> AutoFixFramework:
    """Create framework with registered fixers."""
    fw = AutoFixFramework()
    fw.register_fixer(xss_fixer)
    fw.register_fixer(injection_fixer)
    return fw


# =============================================================================
# Model Tests
# =============================================================================


class TestFixSuggestion:
    """Tests for FixSuggestion model."""

    def test_create_suggestion(self) -> None:
        """Test creating a fix suggestion."""
        suggestion = FixSuggestion(
            old_code="unsafe_code",
            new_code="safe_code",
            explanation="Made it safe",
        )
        assert suggestion.old_code == "unsafe_code"
        assert suggestion.new_code == "safe_code"
        assert suggestion.explanation == "Made it safe"
        assert suggestion.confidence == FixConfidence.HIGH  # default

    def test_suggestion_with_import(self) -> None:
        """Test suggestion with required import."""
        suggestion = FixSuggestion(
            old_code="userInput",
            new_code="DOMPurify.sanitize(userInput)",
            explanation="Sanitize with DOMPurify",
            requires_import="import DOMPurify from 'dompurify'",
        )
        assert suggestion.requires_import is not None
        assert "DOMPurify" in suggestion.requires_import


class TestFixResult:
    """Tests for FixResult model."""

    def test_create_success_result(self) -> None:
        """Test creating a successful fix result."""
        suggestion = FixSuggestion(
            old_code="old",
            new_code="new",
            explanation="Fixed",
        )
        result = FixResult(
            success=True,
            finding_id="test-001",
            suggestion=suggestion,
            status=FixStatus.APPLIED,
            applied_at=datetime.now(),
        )
        assert result.success is True
        assert result.status == FixStatus.APPLIED
        assert result.applied_at is not None

    def test_create_failure_result(self) -> None:
        """Test creating a failed fix result."""
        suggestion = FixSuggestion(
            old_code="",
            new_code="",
            explanation="Failed",
        )
        result = FixResult(
            success=False,
            finding_id="test-002",
            suggestion=suggestion,
            status=FixStatus.FAILED,
            error_message="Could not apply fix",
        )
        assert result.success is False
        assert result.status == FixStatus.FAILED
        assert result.error_message is not None

    def test_can_rollback_property(self, tmp_path: Path) -> None:
        """Test can_rollback property."""
        suggestion = FixSuggestion(old_code="", new_code="", explanation="")

        # Create backup file
        backup_file = tmp_path / "backup.bak"
        backup_file.write_text("backup content")

        result = FixResult(
            success=True,
            finding_id="test-003",
            suggestion=suggestion,
            status=FixStatus.APPLIED,
            backup_path=backup_file,
            file_path=tmp_path / "original.py",
        )
        assert result.can_rollback is True

    def test_cannot_rollback_without_backup(self) -> None:
        """Test can_rollback is False without backup."""
        suggestion = FixSuggestion(old_code="", new_code="", explanation="")
        result = FixResult(
            success=True,
            finding_id="test-004",
            suggestion=suggestion,
            status=FixStatus.APPLIED,
        )
        assert result.can_rollback is False


class TestFixBatchResult:
    """Tests for FixBatchResult model."""

    def test_empty_batch(self) -> None:
        """Test empty batch result."""
        batch = FixBatchResult()
        assert batch.total_findings == 0
        assert batch.successful == 0
        assert batch.failed == 0
        assert batch.all_successful is True

    def test_add_successful_result(self) -> None:
        """Test adding successful result to batch."""
        batch = FixBatchResult()
        suggestion = FixSuggestion(old_code="", new_code="", explanation="")
        result = FixResult(
            success=True,
            finding_id="test-001",
            suggestion=suggestion,
            status=FixStatus.APPLIED,
        )
        batch.add_result(result)

        assert batch.total_findings == 1
        assert batch.successful == 1
        assert batch.failed == 0
        assert batch.all_successful is True

    def test_add_failed_result(self) -> None:
        """Test adding failed result to batch."""
        batch = FixBatchResult()
        suggestion = FixSuggestion(old_code="", new_code="", explanation="")
        result = FixResult(
            success=False,
            finding_id="test-002",
            suggestion=suggestion,
            status=FixStatus.FAILED,
        )
        batch.add_result(result)

        assert batch.total_findings == 1
        assert batch.successful == 0
        assert batch.failed == 1
        assert batch.all_successful is False

    def test_add_skipped_result(self) -> None:
        """Test adding skipped result to batch."""
        batch = FixBatchResult()
        suggestion = FixSuggestion(old_code="", new_code="", explanation="")
        result = FixResult(
            success=False,
            finding_id="test-003",
            suggestion=suggestion,
            status=FixStatus.SKIPPED,
        )
        batch.add_result(result)

        assert batch.total_findings == 1
        assert batch.skipped == 1
        assert batch.all_successful is False

    def test_get_failed_results(self) -> None:
        """Test getting failed results from batch."""
        batch = FixBatchResult()
        suggestion = FixSuggestion(old_code="", new_code="", explanation="")

        # Add mixed results
        batch.add_result(
            FixResult(
                success=True,
                finding_id="ok-001",
                suggestion=suggestion,
                status=FixStatus.APPLIED,
            )
        )
        batch.add_result(
            FixResult(
                success=False,
                finding_id="fail-001",
                suggestion=suggestion,
                status=FixStatus.FAILED,
            )
        )

        failed = batch.get_failed_results()
        assert len(failed) == 1
        assert failed[0].finding_id == "fail-001"


# =============================================================================
# BaseFixer Tests
# =============================================================================


class TestBaseFixer:
    """Tests for BaseFixer base class."""

    def test_fixer_properties(self, xss_fixer: XSSFixer) -> None:
        """Test fixer properties."""
        assert xss_fixer.fixer_id == "xss-sanitizer"
        assert xss_fixer.name == "XSS Sanitizer"
        assert xss_fixer.priority == 200
        assert "xss" in xss_fixer.supported_categories

    def test_can_fix_matching(
        self, xss_fixer: XSSFixer, xss_finding: SecurityFinding
    ) -> None:
        """Test can_fix returns True for matching finding."""
        assert xss_fixer.can_fix(xss_finding) is True

    def test_can_fix_non_matching(
        self, xss_fixer: XSSFixer, injection_finding: SecurityFinding
    ) -> None:
        """Test can_fix returns False for non-matching finding."""
        assert xss_fixer.can_fix(injection_finding) is False

    def test_generate_fix(
        self, xss_fixer: XSSFixer, xss_finding: SecurityFinding
    ) -> None:
        """Test generating a fix suggestion."""
        suggestion = xss_fixer.generate_fix(xss_finding)
        assert isinstance(suggestion, FixSuggestion)
        assert "DOMPurify" in suggestion.new_code

    def test_get_capability(self, xss_fixer: XSSFixer) -> None:
        """Test getting fixer capability."""
        capability = xss_fixer.get_capability()
        assert capability.fixer_id == "xss-sanitizer"
        assert capability.name == "XSS Sanitizer"
        assert capability.priority == 200

    def test_apply_fix_dry_run(
        self, xss_fixer: XSSFixer, xss_finding: SecurityFinding, tmp_path: Path
    ) -> None:
        """Test applying fix in dry-run mode."""
        # Create a test file
        test_file = tmp_path / "test_file.tsx"
        test_file.write_text(
            "const Component = () => {\n"
            "  return <div>{unsafe_html_render(userInput)}</div>;\n"
            "};\n"
        )

        # Update finding location to use temp file
        xss_finding.location.file_path = str(test_file)
        xss_finding.location.snippet = "unsafe_html_render(userInput)"

        result = xss_fixer.apply_fix(xss_finding, dry_run=True)

        assert result.success is True
        assert result.status == FixStatus.PENDING  # Not applied in dry-run
        assert result.diff is not None
        assert result.applied_at is None
        # File should be unchanged
        assert "userInput)" in test_file.read_text()

    def test_apply_fix_actual(
        self, xss_fixer: XSSFixer, xss_finding: SecurityFinding, tmp_path: Path
    ) -> None:
        """Test applying fix for real."""
        # Create a test file
        test_file = tmp_path / "test_file.tsx"
        original_content = (
            "const Component = () => {\n"
            "  return <div>{unsafe_html_render(userInput)}</div>;\n"
            "};\n"
        )
        test_file.write_text(original_content)

        # Create backup directory
        backup_dir = tmp_path / ".aios" / "backups"
        xss_fixer._backup_dir = backup_dir

        # Update finding location
        xss_finding.location.file_path = str(test_file)
        xss_finding.location.snippet = "unsafe_html_render(userInput)"

        result = xss_fixer.apply_fix(xss_finding, dry_run=False)

        assert result.success is True
        assert result.status == FixStatus.APPLIED
        assert result.applied_at is not None
        assert result.backup_path is not None
        assert result.backup_path.exists()
        # File should be modified
        assert "DOMPurify.sanitize" in test_file.read_text()

    def test_apply_fix_file_not_found(
        self, xss_fixer: XSSFixer, xss_finding: SecurityFinding
    ) -> None:
        """Test applying fix when file doesn't exist."""
        xss_finding.location.file_path = "/nonexistent/file.tsx"

        result = xss_fixer.apply_fix(xss_finding, dry_run=True)

        assert result.success is False
        assert result.status == FixStatus.FAILED
        assert result.error_message is not None
        assert "not found" in result.error_message.lower()

    def test_apply_fix_cannot_fix(
        self, xss_fixer: XSSFixer, injection_finding: SecurityFinding, tmp_path: Path
    ) -> None:
        """Test applying fix when fixer cannot handle finding."""
        test_file = tmp_path / "test_db.py"
        test_file.write_text("query = 'SELECT * FROM users'")
        injection_finding.location.file_path = str(test_file)

        result = xss_fixer.apply_fix(injection_finding, dry_run=True)

        assert result.success is False
        assert result.status == FixStatus.SKIPPED

    def test_rollback(
        self, xss_fixer: XSSFixer, xss_finding: SecurityFinding, tmp_path: Path
    ) -> None:
        """Test rolling back a fix."""
        # Create test file
        test_file = tmp_path / "test_file.tsx"
        original_content = "unsafe_html_render(userInput)"
        test_file.write_text(original_content)

        # Setup backup dir
        backup_dir = tmp_path / ".aios" / "backups"
        xss_fixer._backup_dir = backup_dir

        # Update finding
        xss_finding.location.file_path = str(test_file)
        xss_finding.location.snippet = original_content

        # Apply fix
        result = xss_fixer.apply_fix(xss_finding, dry_run=False)
        assert result.success is True
        assert "DOMPurify" in test_file.read_text()

        # Rollback
        rollback_success = xss_fixer.rollback(result)
        assert rollback_success is True
        assert test_file.read_text() == original_content
        assert result.status == FixStatus.ROLLED_BACK


# =============================================================================
# AutoFixFramework Tests
# =============================================================================


class TestAutoFixFramework:
    """Tests for AutoFixFramework."""

    def test_empty_framework(self, framework: AutoFixFramework) -> None:
        """Test empty framework."""
        assert framework.fixer_count == 0
        assert framework.fixers == {}

    def test_register_fixer(
        self, framework: AutoFixFramework, xss_fixer: XSSFixer
    ) -> None:
        """Test registering a fixer."""
        framework.register_fixer(xss_fixer)
        assert framework.fixer_count == 1
        assert "xss-sanitizer" in framework.fixers

    def test_register_duplicate_fixer(
        self, framework: AutoFixFramework, xss_fixer: XSSFixer
    ) -> None:
        """Test registering duplicate fixer raises error."""
        framework.register_fixer(xss_fixer)
        with pytest.raises(ValueError, match="already registered"):
            framework.register_fixer(xss_fixer)

    def test_unregister_fixer(
        self, framework: AutoFixFramework, xss_fixer: XSSFixer
    ) -> None:
        """Test unregistering a fixer."""
        framework.register_fixer(xss_fixer)
        result = framework.unregister_fixer("xss-sanitizer")
        assert result is True
        assert framework.fixer_count == 0

    def test_unregister_nonexistent(self, framework: AutoFixFramework) -> None:
        """Test unregistering nonexistent fixer."""
        result = framework.unregister_fixer("nonexistent")
        assert result is False

    def test_get_fixer(
        self, framework_with_fixers: AutoFixFramework
    ) -> None:
        """Test getting a fixer by ID."""
        fixer = framework_with_fixers.get_fixer("xss-sanitizer")
        assert fixer is not None
        assert fixer.fixer_id == "xss-sanitizer"

    def test_get_fixer_not_found(self, framework: AutoFixFramework) -> None:
        """Test getting nonexistent fixer returns None."""
        fixer = framework.get_fixer("nonexistent")
        assert fixer is None

    def test_get_fixer_for(
        self,
        framework_with_fixers: AutoFixFramework,
        xss_finding: SecurityFinding,
        injection_finding: SecurityFinding,
    ) -> None:
        """Test finding appropriate fixer for a finding."""
        xss_fixer = framework_with_fixers.get_fixer_for(xss_finding)
        assert xss_fixer is not None
        assert xss_fixer.fixer_id == "xss-sanitizer"

        injection_fixer = framework_with_fixers.get_fixer_for(injection_finding)
        assert injection_fixer is not None
        assert injection_fixer.fixer_id == "injection-parameterizer"

    def test_get_fixer_for_no_match(
        self,
        framework_with_fixers: AutoFixFramework,
        non_fixable_finding: SecurityFinding,
    ) -> None:
        """Test no fixer found for unhandled category."""
        fixer = framework_with_fixers.get_fixer_for(non_fixable_finding)
        assert fixer is None

    def test_get_all_fixers_for(
        self,
        framework_with_fixers: AutoFixFramework,
        xss_finding: SecurityFinding,
    ) -> None:
        """Test getting all matching fixers."""
        fixers = framework_with_fixers.get_all_fixers_for(xss_finding)
        assert len(fixers) == 1
        assert fixers[0].fixer_id == "xss-sanitizer"

    def test_get_capabilities(self, framework_with_fixers: AutoFixFramework) -> None:
        """Test getting all fixer capabilities."""
        capabilities = framework_with_fixers.get_capabilities()
        assert len(capabilities) == 2
        ids = [c.fixer_id for c in capabilities]
        assert "xss-sanitizer" in ids
        assert "injection-parameterizer" in ids

    def test_fixer_priority_order(
        self, framework_with_fixers: AutoFixFramework
    ) -> None:
        """Test fixers are ordered by priority."""
        # XSS fixer has priority 200, Injection has 100
        order = framework_with_fixers._fixer_order
        assert order[0] == "xss-sanitizer"  # Higher priority first
        assert order[1] == "injection-parameterizer"

    def test_fix_finding_dry_run(
        self,
        framework_with_fixers: AutoFixFramework,
        xss_finding: SecurityFinding,
        tmp_path: Path,
    ) -> None:
        """Test fixing a single finding in dry-run mode."""
        # Create test file
        test_file = tmp_path / "test_file.tsx"
        test_file.write_text("unsafe_html_render(userInput)")
        xss_finding.location.file_path = str(test_file)
        xss_finding.location.snippet = "unsafe_html_render(userInput)"

        result = framework_with_fixers.fix_finding(xss_finding, dry_run=True)

        assert result.success is True
        assert result.status == FixStatus.PENDING

    def test_fix_finding_no_fixer(
        self,
        framework_with_fixers: AutoFixFramework,
        non_fixable_finding: SecurityFinding,
    ) -> None:
        """Test fixing finding with no available fixer."""
        result = framework_with_fixers.fix_finding(non_fixable_finding)

        assert result.success is False
        assert result.error_message is not None
        assert "No fixer available" in result.error_message

    def test_fix_finding_specific_fixer(
        self,
        framework_with_fixers: AutoFixFramework,
        xss_finding: SecurityFinding,
        tmp_path: Path,
    ) -> None:
        """Test fixing with specific fixer ID."""
        test_file = tmp_path / "test_file.tsx"
        test_file.write_text("unsafe_html_render(userInput)")
        xss_finding.location.file_path = str(test_file)
        xss_finding.location.snippet = "unsafe_html_render(userInput)"

        result = framework_with_fixers.fix_finding(
            xss_finding, dry_run=True, fixer_id="xss-sanitizer"
        )

        assert result.success is True

    def test_fix_finding_wrong_fixer(
        self,
        framework_with_fixers: AutoFixFramework,
        xss_finding: SecurityFinding,
    ) -> None:
        """Test fixing with wrong fixer ID."""
        result = framework_with_fixers.fix_finding(
            xss_finding, dry_run=True, fixer_id="injection-parameterizer"
        )

        assert result.success is False
        assert result.error_message is not None
        assert "cannot fix" in result.error_message.lower()

    def test_fix_finding_nonexistent_fixer(
        self,
        framework_with_fixers: AutoFixFramework,
        xss_finding: SecurityFinding,
    ) -> None:
        """Test fixing with nonexistent fixer ID."""
        result = framework_with_fixers.fix_finding(
            xss_finding, dry_run=True, fixer_id="nonexistent"
        )

        assert result.success is False
        assert result.error_message is not None
        assert "not found" in result.error_message.lower()

    def test_fix_all(
        self,
        framework_with_fixers: AutoFixFramework,
        xss_finding: SecurityFinding,
        injection_finding: SecurityFinding,
        tmp_path: Path,
    ) -> None:
        """Test fixing multiple findings."""
        # Create test files
        xss_file = tmp_path / "test_file.tsx"
        xss_file.write_text("unsafe_html_render(userInput)")
        xss_finding.location.file_path = str(xss_file)
        xss_finding.location.snippet = "unsafe_html_render(userInput)"

        injection_file = tmp_path / "test_db.py"
        injection_file.write_text("query = f'SELECT * FROM users WHERE id = {user_id}'")
        injection_finding.location.file_path = str(injection_file)
        injection_finding.location.snippet = "query = f'SELECT * FROM users WHERE id = {user_id}'"

        batch_result = framework_with_fixers.fix_all(
            [xss_finding, injection_finding], dry_run=True
        )

        assert batch_result.total_findings == 2
        assert batch_result.successful == 2
        assert batch_result.dry_run is True

    def test_fix_all_with_non_fixable(
        self,
        framework_with_fixers: AutoFixFramework,
        xss_finding: SecurityFinding,
        non_fixable_finding: SecurityFinding,
        tmp_path: Path,
    ) -> None:
        """Test fix_all skips non-fixable findings."""
        xss_file = tmp_path / "test_file.tsx"
        xss_file.write_text("unsafe_html_render(userInput)")
        xss_finding.location.file_path = str(xss_file)
        xss_finding.location.snippet = "unsafe_html_render(userInput)"

        batch_result = framework_with_fixers.fix_all(
            [xss_finding, non_fixable_finding], dry_run=True
        )

        assert batch_result.total_findings == 2
        assert batch_result.successful == 1
        assert batch_result.skipped == 1

    def test_fix_all_stop_on_error(
        self,
        framework_with_fixers: AutoFixFramework,
        xss_finding: SecurityFinding,
        injection_finding: SecurityFinding,
    ) -> None:
        """Test fix_all with stop_on_error."""
        # First finding will fail (file doesn't exist)
        xss_finding.location.file_path = "/nonexistent.tsx"

        batch_result = framework_with_fixers.fix_all(
            [xss_finding, injection_finding], dry_run=True, stop_on_error=True
        )

        # Should stop after first failure
        assert batch_result.total_findings == 1
        assert batch_result.failed == 1

    def test_fix_auto_fixable(
        self,
        framework_with_fixers: AutoFixFramework,
        xss_finding: SecurityFinding,
        non_fixable_finding: SecurityFinding,
        tmp_path: Path,
    ) -> None:
        """Test fix_auto_fixable filters correctly."""
        xss_file = tmp_path / "test_file.tsx"
        xss_file.write_text("unsafe_html_render(userInput)")
        xss_finding.location.file_path = str(xss_file)
        xss_finding.location.snippet = "unsafe_html_render(userInput)"

        batch_result = framework_with_fixers.fix_auto_fixable(
            [xss_finding, non_fixable_finding], dry_run=True
        )

        # Should only process the auto-fixable one
        assert batch_result.total_findings == 1
        assert batch_result.successful == 1
