"""Tests for PR Automation Layer.

Tests cover:
- PRStatus enum
- PRReviewResult dataclass
- PRAutomationGate initialization
- run_full_audit method
- review_pr method
- should_block_merge logic
- generate_pr_comment output
- Error handling
- Blocking findings extraction
"""

from datetime import datetime
from pathlib import Path

from aios.quality.pr_automation import PRAutomationGate
from aios.quality.pr_automation import PRReviewResult
from aios.quality.pr_automation import PRStatus
from aios.quality.pr_automation import pr_automation_gate
from aios.security.models import CodeLocation
from aios.security.models import FindingCategory
from aios.security.models import SecurityFinding
from aios.security.models import SecurityReport
from aios.security.models import Severity
from aios.security.models import ValidatorResult
from aios.security.orchestrator import ScanConfig
from aios.security.validators.base import BaseValidator
from aios.security.validators.registry import ValidatorRegistry


class MockValidator(BaseValidator):
    """Mock validator for testing."""

    def __init__(
        self,
        validator_id: str = "mock-validator",
        findings: list[SecurityFinding] | None = None,
        error: Exception | None = None,
    ) -> None:
        self._id = validator_id
        self._findings = findings or []
        self._error = error

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return f"Mock Validator {self._id}"

    @property
    def description(self) -> str:
        return "A mock validator for testing"

    def validate_content(
        self, content: str, file_path: str  # noqa: ARG002
    ) -> list[SecurityFinding]:
        if self._error:
            raise self._error
        return list(self._findings)


def create_finding(
    finding_id: str = "test-001",
    severity: Severity = Severity.HIGH,
    category: FindingCategory = FindingCategory.XSS,
    title: str = "Test Finding",
    file_path: str = "test.ts",
    line_start: int = 1,
) -> SecurityFinding:
    """Helper to create a finding for tests."""
    return SecurityFinding(
        id=finding_id,
        validator_id="test",
        severity=severity,
        category=category,
        title=title,
        description="A test finding description",
        location=CodeLocation(file_path=file_path, line_start=line_start, line_end=line_start),
        recommendation="Fix this issue",
    )


def create_report(
    findings: list[SecurityFinding] | None = None,
    errors: list[str] | None = None,
) -> SecurityReport:
    """Helper to create a security report for tests."""
    report = SecurityReport(
        scan_id="test-scan",
        started_at=datetime.now(),
        target_path="/test/path",
    )

    if findings:
        result = ValidatorResult(
            validator_id="test-validator",
            validator_name="Test Validator",
            findings=findings,
            files_scanned=10,
            scan_duration_ms=100,
        )
        report.add_result(result)

    if errors:
        for error in errors:
            error_result = ValidatorResult(
                validator_id="error-validator",
                validator_name="Error Validator",
                error=error,
            )
            report.add_result(error_result)

    report.completed_at = datetime.now()
    return report


class TestPRStatus:
    """Tests for PRStatus enum."""

    def test_status_values(self) -> None:
        """Test all status values exist."""
        assert PRStatus.APPROVED.value == "approved"
        assert PRStatus.CHANGES_REQUESTED.value == "changes_requested"
        assert PRStatus.PENDING.value == "pending"
        assert PRStatus.ERROR.value == "error"

    def test_status_comparison(self) -> None:
        """Test status comparison."""
        # Test that different status values are not equal
        approved = PRStatus.APPROVED
        changes_requested = PRStatus.CHANGES_REQUESTED
        error = PRStatus.ERROR
        pending = PRStatus.PENDING
        assert approved.value != changes_requested.value
        assert error.value != pending.value


class TestPRReviewResult:
    """Tests for PRReviewResult dataclass."""

    def test_result_creation(self) -> None:
        """Test creating a PR review result."""
        report = create_report()
        result = PRReviewResult(
            status=PRStatus.APPROVED,
            security_report=report,
            pr_comment="Test comment",
            should_block=False,
        )

        assert result.status == PRStatus.APPROVED
        assert result.security_report is report
        assert result.pr_comment == "Test comment"
        assert result.should_block is False
        assert result.blocking_findings == []
        assert result.error_message is None
        assert isinstance(result.reviewed_at, datetime)

    def test_result_with_blocking_findings(self) -> None:
        """Test result with blocking findings."""
        finding = create_finding(severity=Severity.CRITICAL)
        result = PRReviewResult(
            status=PRStatus.CHANGES_REQUESTED,
            security_report=None,
            pr_comment="Blocked",
            should_block=True,
            blocking_findings=[finding],
        )

        assert result.should_block is True
        assert len(result.blocking_findings) == 1
        assert result.blocking_findings[0].severity == Severity.CRITICAL

    def test_result_with_error(self) -> None:
        """Test result with error message."""
        result = PRReviewResult(
            status=PRStatus.ERROR,
            security_report=None,
            pr_comment="Error occurred",
            should_block=True,
            error_message="Scan failed",
        )

        assert result.status == PRStatus.ERROR
        assert result.error_message == "Scan failed"


class TestPRAutomationGate:
    """Tests for PRAutomationGate class."""

    def test_init_default(self) -> None:
        """Test default initialization."""
        gate = PRAutomationGate()
        assert gate.orchestrator is not None

    def test_init_with_registry(self) -> None:
        """Test initialization with custom registry."""
        registry = ValidatorRegistry()
        gate = PRAutomationGate(registry=registry)
        # Check registry is used (count matches)
        assert gate.orchestrator.registry.count == registry.count

    def test_init_with_config(self) -> None:
        """Test initialization with custom config."""
        config = ScanConfig(timeout_per_validator=60.0, max_workers=8)
        gate = PRAutomationGate(config=config)
        assert gate.orchestrator.config.timeout_per_validator == 60.0
        assert gate.orchestrator.config.max_workers == 8


class TestShouldBlockMerge:
    """Tests for should_block_merge logic."""

    def test_block_on_critical(self) -> None:
        """Test blocking on CRITICAL findings."""
        gate = PRAutomationGate()
        finding = create_finding(severity=Severity.CRITICAL)
        report = create_report(findings=[finding])

        assert gate.should_block_merge(report) is True

    def test_block_on_high(self) -> None:
        """Test blocking on HIGH findings."""
        gate = PRAutomationGate()
        finding = create_finding(severity=Severity.HIGH)
        report = create_report(findings=[finding])

        assert gate.should_block_merge(report) is True

    def test_no_block_on_medium(self) -> None:
        """Test no blocking on MEDIUM findings."""
        gate = PRAutomationGate()
        finding = create_finding(severity=Severity.MEDIUM)
        report = create_report(findings=[finding])

        assert gate.should_block_merge(report) is False

    def test_no_block_on_low(self) -> None:
        """Test no blocking on LOW findings."""
        gate = PRAutomationGate()
        finding = create_finding(severity=Severity.LOW)
        report = create_report(findings=[finding])

        assert gate.should_block_merge(report) is False

    def test_no_block_on_info(self) -> None:
        """Test no blocking on INFO findings."""
        gate = PRAutomationGate()
        finding = create_finding(severity=Severity.INFO)
        report = create_report(findings=[finding])

        assert gate.should_block_merge(report) is False

    def test_no_block_on_empty_report(self) -> None:
        """Test no blocking when no findings."""
        gate = PRAutomationGate()
        report = create_report(findings=[])

        assert gate.should_block_merge(report) is False


class TestGeneratePRComment:
    """Tests for generate_pr_comment method."""

    def test_approved_comment_no_findings(self) -> None:
        """Test approved comment with no findings."""
        gate = PRAutomationGate()
        report = create_report(findings=[])

        comment = gate.generate_pr_comment(report)

        assert ":white_check_mark: Security Review - Approved" in comment
        assert "No security issues found" in comment
        assert "Total Findings:** 0" in comment

    def test_approved_comment_with_low_findings(self) -> None:
        """Test approved comment with non-blocking findings."""
        gate = PRAutomationGate()
        finding = create_finding(severity=Severity.LOW, title="Low Issue")
        report = create_report(findings=[finding])

        comment = gate.generate_pr_comment(report)

        assert ":white_check_mark: Security Review - Approved" in comment
        assert "some findings but none are blocking" in comment
        assert "Total Findings:** 1" in comment

    def test_blocked_comment_critical(self) -> None:
        """Test blocked comment with CRITICAL findings."""
        gate = PRAutomationGate()
        finding = create_finding(
            severity=Severity.CRITICAL,
            title="Critical XSS",
            file_path="app.tsx",
            line_start=42,
        )
        report = create_report(findings=[finding])

        comment = gate.generate_pr_comment(report)

        assert ":x: Security Review - Changes Requested" in comment
        assert "cannot be merged" in comment
        assert "CRITICAL" in comment
        assert "Blocking Findings" in comment
        assert "Critical XSS" in comment
        assert "app.tsx" in comment
        assert ":red_circle:" in comment

    def test_blocked_comment_high(self) -> None:
        """Test blocked comment with HIGH findings."""
        gate = PRAutomationGate()
        finding = create_finding(severity=Severity.HIGH, title="High Severity Issue")
        report = create_report(findings=[finding])

        comment = gate.generate_pr_comment(report)

        assert ":x: Security Review - Changes Requested" in comment
        assert ":orange_circle:" in comment
        assert "High Severity Issue" in comment

    def test_comment_with_mixed_findings(self) -> None:
        """Test comment with mixed severity findings."""
        gate = PRAutomationGate()
        findings = [
            create_finding(finding_id="c1", severity=Severity.CRITICAL, title="Critical"),
            create_finding(finding_id="h1", severity=Severity.HIGH, title="High"),
            create_finding(finding_id="m1", severity=Severity.MEDIUM, title="Medium"),
            create_finding(finding_id="l1", severity=Severity.LOW, title="Low"),
        ]
        report = create_report(findings=findings)

        comment = gate.generate_pr_comment(report)

        assert ":x: Security Review - Changes Requested" in comment
        assert "Blocking Findings" in comment
        assert "Other Findings" in comment
        assert "Total Findings:** 4" in comment

    def test_comment_with_scan_errors(self) -> None:
        """Test comment includes scan errors."""
        gate = PRAutomationGate()
        report = create_report(findings=[], errors=["Validator timeout"])

        comment = gate.generate_pr_comment(report)

        assert "Scan Errors" in comment
        assert "Validator timeout" in comment
        assert ":warning:" in comment

    def test_comment_has_scan_metadata(self) -> None:
        """Test comment includes scan metadata."""
        gate = PRAutomationGate()
        report = create_report(findings=[])

        comment = gate.generate_pr_comment(report)

        assert "Scan ID:" in comment
        assert "test-scan" in comment
        assert "NEO-AIOS Security Scanner" in comment

    def test_comment_limits_blocking_findings_display(self) -> None:
        """Test that blocking findings display is limited to 10."""
        gate = PRAutomationGate()
        findings = [
            create_finding(
                finding_id=f"critical-{i}",
                severity=Severity.CRITICAL,
                title=f"Critical Issue {i}",
            )
            for i in range(15)
        ]
        report = create_report(findings=findings)

        comment = gate.generate_pr_comment(report)

        # Should show first 10 and indicate more
        assert "Critical Issue 0" in comment
        assert "Critical Issue 9" in comment
        assert "and 5 more blocking findings" in comment

    def test_comment_severity_table(self) -> None:
        """Test severity breakdown table in comment."""
        gate = PRAutomationGate()
        findings = [
            create_finding(finding_id="c1", severity=Severity.CRITICAL),
            create_finding(finding_id="h1", severity=Severity.HIGH),
            create_finding(finding_id="h2", severity=Severity.HIGH),
            create_finding(finding_id="m1", severity=Severity.MEDIUM),
        ]
        report = create_report(findings=findings)

        comment = gate.generate_pr_comment(report)

        assert "Findings by Severity" in comment
        assert "| :red_circle: CRITICAL | 1 |" in comment
        assert "| :orange_circle: HIGH | 2 |" in comment
        assert "| :yellow_circle: MEDIUM | 1 |" in comment


class TestRunFullAudit:
    """Tests for run_full_audit method."""

    def test_full_audit_approved(self, tmp_path: Path) -> None:
        """Test full audit with no blocking findings."""
        # Create a test file
        test_file = tmp_path / "test.py"
        test_file.write_text("print('hello')")

        # Create gate with empty registry (no findings)
        registry = ValidatorRegistry()
        gate = PRAutomationGate(registry=registry)

        result = gate.run_full_audit(tmp_path)

        assert result.status == PRStatus.APPROVED
        assert result.should_block is False
        assert result.security_report is not None
        assert ":white_check_mark:" in result.pr_comment

    def test_full_audit_with_findings(self, tmp_path: Path) -> None:
        """Test full audit with blocking findings."""
        # Use .ts file since MockValidator inherits default file_extensions from BaseValidator
        test_file = tmp_path / "test.ts"
        test_file.write_text("console.log('hello');")

        # Create validator with CRITICAL finding
        finding = create_finding(severity=Severity.CRITICAL)
        validator = MockValidator(findings=[finding])

        registry = ValidatorRegistry()
        registry.register(validator)

        gate = PRAutomationGate(registry=registry)
        result = gate.run_full_audit(tmp_path)

        assert result.status == PRStatus.CHANGES_REQUESTED
        assert result.should_block is True
        assert len(result.blocking_findings) == 1
        assert ":x:" in result.pr_comment


class TestReviewPR:
    """Tests for review_pr method."""

    def test_review_pr_adds_metadata(self, tmp_path: Path) -> None:
        """Test that review_pr adds PR metadata to comment."""
        test_file = tmp_path / "test.py"
        test_file.write_text("print('hello')")

        registry = ValidatorRegistry()
        gate = PRAutomationGate(registry=registry)

        result = gate.review_pr(
            pr_number=123,
            repo="owner/repo",
            local_path=tmp_path,
        )

        assert "PR #123" in result.pr_comment
        assert "owner/repo" in result.pr_comment

    def test_review_pr_with_findings(self, tmp_path: Path) -> None:
        """Test review_pr with findings."""
        # Use .ts file since MockValidator inherits default file_extensions from BaseValidator
        test_file = tmp_path / "test.ts"
        test_file.write_text("console.log('hello');")

        finding = create_finding(severity=Severity.HIGH)
        validator = MockValidator(findings=[finding])

        registry = ValidatorRegistry()
        registry.register(validator)

        gate = PRAutomationGate(registry=registry)
        result = gate.review_pr(
            pr_number=456,
            repo="test/repo",
            local_path=tmp_path,
        )

        assert result.status == PRStatus.CHANGES_REQUESTED
        assert "PR #456" in result.pr_comment
        assert "test/repo" in result.pr_comment


class TestErrorHandling:
    """Tests for error handling."""

    def test_audit_error_returns_error_result(self, tmp_path: Path) -> None:
        """Test that errors return ERROR status."""
        # Use a path that doesn't exist
        nonexistent = tmp_path / "nonexistent"

        registry = ValidatorRegistry()
        # Register a validator that will fail
        validator = MockValidator(error=RuntimeError("Test error"))
        registry.register(validator)

        gate = PRAutomationGate(registry=registry)

        # Create the path so scan starts, but validator will error
        nonexistent.mkdir()
        # Use .ts file since MockValidator inherits default file_extensions from BaseValidator
        test_file = nonexistent / "test.ts"
        test_file.write_text("console.log('hello');")

        result = gate.run_full_audit(nonexistent)

        # The result should still be valid, errors are captured in the report
        assert result.security_report is not None
        assert result.security_report.has_errors is True


class TestGlobalInstance:
    """Tests for global instance."""

    def test_global_instance_exists(self) -> None:
        """Test that global instance is created."""
        assert pr_automation_gate is not None
        assert isinstance(pr_automation_gate, PRAutomationGate)

    def test_global_instance_has_orchestrator(self) -> None:
        """Test that global instance has orchestrator."""
        assert pr_automation_gate.orchestrator is not None


class TestBlockingFindingsExtraction:
    """Tests for _get_blocking_findings method."""

    def test_get_blocking_findings_sorted(self) -> None:
        """Test blocking findings are sorted by severity."""
        gate = PRAutomationGate()
        findings = [
            create_finding(finding_id="h1", severity=Severity.HIGH, title="High 1"),
            create_finding(finding_id="c1", severity=Severity.CRITICAL, title="Critical 1"),
            create_finding(finding_id="h2", severity=Severity.HIGH, title="High 2"),
        ]
        report = create_report(findings=findings)

        blocking = gate._get_blocking_findings(report)

        assert len(blocking) == 3
        # CRITICAL should come first
        assert blocking[0].severity == Severity.CRITICAL
        assert blocking[1].severity == Severity.HIGH
        assert blocking[2].severity == Severity.HIGH

    def test_get_blocking_excludes_medium_low_info(self) -> None:
        """Test that MEDIUM, LOW, INFO are excluded from blocking."""
        gate = PRAutomationGate()
        findings = [
            create_finding(finding_id="c1", severity=Severity.CRITICAL),
            create_finding(finding_id="m1", severity=Severity.MEDIUM),
            create_finding(finding_id="l1", severity=Severity.LOW),
            create_finding(finding_id="i1", severity=Severity.INFO),
        ]
        report = create_report(findings=findings)

        blocking = gate._get_blocking_findings(report)

        assert len(blocking) == 1
        assert blocking[0].severity == Severity.CRITICAL


class TestNonBlockingFindingsExtraction:
    """Tests for _get_non_blocking_findings method."""

    def test_get_non_blocking_findings(self) -> None:
        """Test extraction of non-blocking findings."""
        gate = PRAutomationGate()
        findings = [
            create_finding(finding_id="c1", severity=Severity.CRITICAL),
            create_finding(finding_id="h1", severity=Severity.HIGH),
            create_finding(finding_id="m1", severity=Severity.MEDIUM),
            create_finding(finding_id="l1", severity=Severity.LOW),
            create_finding(finding_id="i1", severity=Severity.INFO),
        ]
        report = create_report(findings=findings)

        non_blocking = gate._get_non_blocking_findings(report)

        assert len(non_blocking) == 3
        severities = [f.severity for f in non_blocking]
        assert Severity.CRITICAL not in severities
        assert Severity.HIGH not in severities
        assert Severity.MEDIUM in severities
        assert Severity.LOW in severities
        assert Severity.INFO in severities

    def test_non_blocking_sorted_by_severity(self) -> None:
        """Test non-blocking findings are sorted by severity."""
        gate = PRAutomationGate()
        findings = [
            create_finding(finding_id="i1", severity=Severity.INFO),
            create_finding(finding_id="m1", severity=Severity.MEDIUM),
            create_finding(finding_id="l1", severity=Severity.LOW),
        ]
        report = create_report(findings=findings)

        non_blocking = gate._get_non_blocking_findings(report)

        assert len(non_blocking) == 3
        # MEDIUM should come first, then LOW, then INFO
        assert non_blocking[0].severity == Severity.MEDIUM
        assert non_blocking[1].severity == Severity.LOW
        assert non_blocking[2].severity == Severity.INFO


class TestSeverityEmoji:
    """Tests for _get_severity_emoji method."""

    def test_all_severity_emojis(self) -> None:
        """Test emoji mapping for all severities."""
        gate = PRAutomationGate()

        assert gate._get_severity_emoji(Severity.CRITICAL) == ":red_circle:"
        assert gate._get_severity_emoji(Severity.HIGH) == ":orange_circle:"
        assert gate._get_severity_emoji(Severity.MEDIUM) == ":yellow_circle:"
        assert gate._get_severity_emoji(Severity.LOW) == ":large_blue_circle:"
        assert gate._get_severity_emoji(Severity.INFO) == ":white_circle:"
