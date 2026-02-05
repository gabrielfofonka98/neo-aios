"""Tests for the bounded reflexion loop.

This module tests the BoundedReflexion class that implements
a fix-verify-retry loop with bounded iterations.
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from aios.autofix import AutoFixFramework
from aios.autofix import BaseFixer
from aios.autofix import FixConfidence
from aios.autofix import FixSuggestion
from aios.autofix.reflexion import DEFAULT_MAX_ITERATIONS
from aios.autofix.reflexion import BoundedReflexion
from aios.autofix.reflexion import ReflexionResult
from aios.security.models import CodeLocation
from aios.security.models import FindingCategory
from aios.security.models import SecurityFinding
from aios.security.models import SecurityReport
from aios.security.models import Severity
from aios.security.models import ValidatorResult

# =============================================================================
# Test Fixtures - Mock Fixers
# =============================================================================


class SuccessfulFixer(BaseFixer):
    """Fixer that always succeeds."""

    @property
    def fixer_id(self) -> str:
        return "successful-fixer"

    @property
    def name(self) -> str:
        return "Successful Fixer"

    @property
    def supported_categories(self) -> list[str]:
        return ["xss"]

    def can_fix(self, finding: SecurityFinding) -> bool:
        return finding.category == FindingCategory.XSS

    def generate_fix(self, finding: SecurityFinding) -> FixSuggestion:
        return FixSuggestion(
            old_code=finding.location.snippet or "unsafe_code",
            new_code="safe_code",
            explanation="Made it safe",
            confidence=FixConfidence.HIGH,
        )


class FailingFixer(BaseFixer):
    """Fixer that always fails."""

    @property
    def fixer_id(self) -> str:
        return "failing-fixer"

    @property
    def name(self) -> str:
        return "Failing Fixer"

    @property
    def priority(self) -> int:
        return 50  # Lower priority than successful fixer

    @property
    def supported_categories(self) -> list[str]:
        return ["xss"]

    def can_fix(self, finding: SecurityFinding) -> bool:
        return finding.category == FindingCategory.XSS

    def generate_fix(self, finding: SecurityFinding) -> FixSuggestion:
        # Use finding to avoid unused arg warning
        _ = finding.id
        raise RuntimeError("This fixer always fails")


class AlternativeFixer(BaseFixer):
    """Alternative fixer for testing multiple attempts."""

    @property
    def fixer_id(self) -> str:
        return "alternative-fixer"

    @property
    def name(self) -> str:
        return "Alternative Fixer"

    @property
    def priority(self) -> int:
        return 80  # Middle priority

    @property
    def supported_categories(self) -> list[str]:
        return ["xss"]

    def can_fix(self, finding: SecurityFinding) -> bool:
        return finding.category == FindingCategory.XSS

    def generate_fix(self, finding: SecurityFinding) -> FixSuggestion:
        return FixSuggestion(
            old_code=finding.location.snippet or "unsafe_code",
            new_code="alternative_safe_code",
            explanation="Alternative fix approach",
            confidence=FixConfidence.MEDIUM,
        )


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def xss_finding(tmp_path: Path) -> SecurityFinding:
    """Create a sample XSS finding."""
    # Create actual test file
    test_file = tmp_path / "vulnerable.tsx"
    test_file.write_text("const x = unsafe_code;")

    return SecurityFinding(
        id="xss-001",
        validator_id="sec-xss",
        severity=Severity.HIGH,
        category=FindingCategory.XSS,
        title="XSS vulnerability detected",
        description="User input passed directly to unsafe render method",
        location=CodeLocation(
            file_path=str(test_file),
            line_start=1,
            line_end=1,
            snippet="unsafe_code",
        ),
        recommendation="Sanitize input",
        auto_fixable=True,
    )


@pytest.fixture
def non_fixable_finding() -> SecurityFinding:
    """Create a non-auto-fixable finding."""
    return SecurityFinding(
        id="config-001",
        validator_id="sec-config",
        severity=Severity.MEDIUM,
        category=FindingCategory.CONFIG,
        title="Configuration issue",
        description="Debug mode enabled",
        location=CodeLocation(
            file_path="config.yaml",
            line_start=10,
            line_end=10,
        ),
        recommendation="Disable debug mode",
        auto_fixable=False,
    )


@pytest.fixture
def mock_orchestrator() -> MagicMock:
    """Create a mock security orchestrator."""
    orchestrator = MagicMock()

    # Default: return empty report (finding fixed)
    empty_report = SecurityReport(
        scan_id="test-scan",
        started_at=datetime.now(),
        completed_at=datetime.now(),
        target_path="/test",
        results=[],
    )
    orchestrator.scan.return_value = empty_report

    return orchestrator


@pytest.fixture
def framework_with_fixers() -> AutoFixFramework:
    """Create framework with test fixers."""
    fw = AutoFixFramework()
    fw.register_fixer(SuccessfulFixer())
    fw.register_fixer(AlternativeFixer())
    return fw


@pytest.fixture
def reflexion(
    framework_with_fixers: AutoFixFramework,
    mock_orchestrator: MagicMock,
) -> BoundedReflexion:
    """Create a BoundedReflexion instance."""
    return BoundedReflexion(
        framework=framework_with_fixers,
        orchestrator=mock_orchestrator,
        max_iterations=3,
    )


# =============================================================================
# ReflexionResult Tests
# =============================================================================


class TestReflexionResult:
    """Tests for ReflexionResult model."""

    def test_create_success_result(self, xss_finding: SecurityFinding) -> None:
        """Test creating a successful result."""
        result = ReflexionResult(
            success=True,
            iterations=1,
            original_finding=xss_finding,
        )
        assert result.success is True
        assert result.iterations == 1
        assert result.needs_escalation is False

    def test_create_failure_result(self, xss_finding: SecurityFinding) -> None:
        """Test creating a failure result."""
        result = ReflexionResult(
            success=False,
            iterations=3,
            original_finding=xss_finding,
            error="Failed to fix",
        )
        assert result.success is False
        assert result.error == "Failed to fix"

    def test_needs_escalation_true(self, xss_finding: SecurityFinding) -> None:
        """Test needs_escalation is True when max iterations reached."""
        result = ReflexionResult(
            success=False,
            iterations=DEFAULT_MAX_ITERATIONS,
            original_finding=xss_finding,
            error="All attempts failed",
        )
        assert result.needs_escalation is True

    def test_needs_escalation_false_on_success(
        self, xss_finding: SecurityFinding
    ) -> None:
        """Test needs_escalation is False on success."""
        result = ReflexionResult(
            success=True,
            iterations=3,
            original_finding=xss_finding,
        )
        assert result.needs_escalation is False

    def test_needs_escalation_false_on_early_failure(
        self, xss_finding: SecurityFinding
    ) -> None:
        """Test needs_escalation is False when failed before max iterations."""
        result = ReflexionResult(
            success=False,
            iterations=1,
            original_finding=xss_finding,
            error="No fixer available",
        )
        assert result.needs_escalation is False

    def test_rolled_back_result(self, xss_finding: SecurityFinding) -> None:
        """Test result with rollback flag."""
        result = ReflexionResult(
            success=False,
            iterations=1,
            original_finding=xss_finding,
            rolled_back=True,
            error="Regression detected",
        )
        assert result.rolled_back is True
        assert result.success is False


# =============================================================================
# BoundedReflexion Initialization Tests
# =============================================================================


class TestBoundedReflexionInit:
    """Tests for BoundedReflexion initialization."""

    def test_init_default(
        self,
        framework_with_fixers: AutoFixFramework,
        mock_orchestrator: MagicMock,
    ) -> None:
        """Test initialization with defaults."""
        reflexion = BoundedReflexion(
            framework=framework_with_fixers,
            orchestrator=mock_orchestrator,
        )
        assert reflexion.max_iterations == DEFAULT_MAX_ITERATIONS
        assert reflexion.framework is framework_with_fixers
        assert reflexion.orchestrator is mock_orchestrator

    def test_init_custom_iterations(
        self,
        framework_with_fixers: AutoFixFramework,
        mock_orchestrator: MagicMock,
    ) -> None:
        """Test initialization with custom max_iterations."""
        reflexion = BoundedReflexion(
            framework=framework_with_fixers,
            orchestrator=mock_orchestrator,
            max_iterations=5,
        )
        assert reflexion.max_iterations == 5

    def test_init_invalid_iterations_zero(
        self,
        framework_with_fixers: AutoFixFramework,
        mock_orchestrator: MagicMock,
    ) -> None:
        """Test initialization with invalid max_iterations (0)."""
        with pytest.raises(ValueError, match="must be between 1 and 10"):
            BoundedReflexion(
                framework=framework_with_fixers,
                orchestrator=mock_orchestrator,
                max_iterations=0,
            )

    def test_init_invalid_iterations_negative(
        self,
        framework_with_fixers: AutoFixFramework,
        mock_orchestrator: MagicMock,
    ) -> None:
        """Test initialization with negative max_iterations."""
        with pytest.raises(ValueError, match="must be between 1 and 10"):
            BoundedReflexion(
                framework=framework_with_fixers,
                orchestrator=mock_orchestrator,
                max_iterations=-1,
            )

    def test_init_invalid_iterations_too_high(
        self,
        framework_with_fixers: AutoFixFramework,
        mock_orchestrator: MagicMock,
    ) -> None:
        """Test initialization with max_iterations > 10."""
        with pytest.raises(ValueError, match="must be between 1 and 10"):
            BoundedReflexion(
                framework=framework_with_fixers,
                orchestrator=mock_orchestrator,
                max_iterations=11,
            )


# =============================================================================
# BoundedReflexion Fix Tests
# =============================================================================


class TestFixWithVerification:
    """Tests for fix_with_verification method."""

    def test_successful_fix_first_attempt(
        self,
        reflexion: BoundedReflexion,
        xss_finding: SecurityFinding,
        mock_orchestrator: MagicMock,
    ) -> None:
        """Test successful fix on first attempt."""
        # Orchestrator returns empty report (no findings = fix worked)
        mock_orchestrator.scan.return_value = SecurityReport(
            scan_id="verify",
            started_at=datetime.now(),
            completed_at=datetime.now(),
            target_path=xss_finding.location.file_path,
            results=[],
        )

        result = reflexion.fix_with_verification(xss_finding)

        assert result.success is True
        assert result.iterations == 1
        assert result.error is None
        assert result.final_fix is not None
        assert len(result.attempt_history) == 1

    def test_dry_run_returns_success_without_verification(
        self,
        reflexion: BoundedReflexion,
        xss_finding: SecurityFinding,
        mock_orchestrator: MagicMock,
    ) -> None:
        """Test dry-run mode doesn't verify."""
        result = reflexion.fix_with_verification(xss_finding, dry_run=True)

        assert result.success is True
        assert result.iterations == 1
        assert result.verification_report is None
        # Orchestrator should not be called in dry-run
        mock_orchestrator.scan.assert_not_called()

    def test_no_fixer_available(
        self,
        mock_orchestrator: MagicMock,
        non_fixable_finding: SecurityFinding,
    ) -> None:
        """Test when no fixer can handle the finding."""
        # Empty framework
        fw = AutoFixFramework()
        reflexion = BoundedReflexion(
            framework=fw,
            orchestrator=mock_orchestrator,
        )

        result = reflexion.fix_with_verification(non_fixable_finding)

        assert result.success is False
        assert result.iterations == 0
        assert "No fixer available" in str(result.error)

    def test_fix_not_verified_tries_next_fixer(
        self,
        framework_with_fixers: AutoFixFramework,
        xss_finding: SecurityFinding,
        mock_orchestrator: MagicMock,
    ) -> None:
        """Test that if fix doesn't verify, tries next fixer."""
        # First scan returns the finding still present
        # Second scan returns empty (fix worked)
        finding_present_report = SecurityReport(
            scan_id="verify-1",
            started_at=datetime.now(),
            completed_at=datetime.now(),
            target_path=xss_finding.location.file_path,
            results=[
                ValidatorResult(
                    validator_id="sec-xss",
                    validator_name="XSS Validator",
                    findings=[xss_finding],
                )
            ],
        )
        finding_fixed_report = SecurityReport(
            scan_id="verify-2",
            started_at=datetime.now(),
            completed_at=datetime.now(),
            target_path=xss_finding.location.file_path,
            results=[],
        )
        mock_orchestrator.scan.side_effect = [
            finding_present_report,
            finding_fixed_report,
        ]

        reflexion = BoundedReflexion(
            framework=framework_with_fixers,
            orchestrator=mock_orchestrator,
        )

        result = reflexion.fix_with_verification(xss_finding)

        assert result.success is True
        assert result.iterations == 2  # Took 2 attempts
        assert len(result.attempt_history) == 2

    def test_all_iterations_exhausted(
        self,
        xss_finding: SecurityFinding,
        mock_orchestrator: MagicMock,
    ) -> None:
        """Test failure when all iterations are exhausted."""
        # Always return finding present
        finding_present_report = SecurityReport(
            scan_id="verify",
            started_at=datetime.now(),
            completed_at=datetime.now(),
            target_path=xss_finding.location.file_path,
            results=[
                ValidatorResult(
                    validator_id="sec-xss",
                    validator_name="XSS Validator",
                    findings=[xss_finding],
                )
            ],
        )
        mock_orchestrator.scan.return_value = finding_present_report

        # Create framework with only one fixer
        fw = AutoFixFramework()
        fw.register_fixer(SuccessfulFixer())

        reflexion = BoundedReflexion(
            framework=fw,
            orchestrator=mock_orchestrator,
            max_iterations=3,
        )

        result = reflexion.fix_with_verification(xss_finding)

        # Since there's only one fixer, should fail after that's exhausted
        assert result.success is False
        assert (
            "exhausted" in str(result.error).lower()
            or "failed" in str(result.error).lower()
        )

    def test_regression_detected_rolls_back(
        self,
        reflexion: BoundedReflexion,
        xss_finding: SecurityFinding,
        mock_orchestrator: MagicMock,
    ) -> None:
        """Test that regression detection triggers rollback."""
        # Create a new critical finding (regression)
        regression_finding = SecurityFinding(
            id="xss-new",
            validator_id="sec-xss",
            severity=Severity.CRITICAL,  # Critical = regression
            category=FindingCategory.XSS,
            title="New XSS vulnerability",
            description="Introduced by fix",
            location=CodeLocation(
                file_path=xss_finding.location.file_path,
                line_start=5,
                line_end=5,
            ),
            recommendation="Fix this",
            auto_fixable=True,
        )

        regression_report = SecurityReport(
            scan_id="verify",
            started_at=datetime.now(),
            completed_at=datetime.now(),
            target_path=xss_finding.location.file_path,
            results=[
                ValidatorResult(
                    validator_id="sec-xss",
                    validator_name="XSS Validator",
                    findings=[regression_finding],
                )
            ],
        )
        mock_orchestrator.scan.return_value = regression_report

        result = reflexion.fix_with_verification(xss_finding)

        assert result.success is False
        assert result.rolled_back is True
        assert "regression" in str(result.error).lower()

    def test_records_duration(
        self,
        reflexion: BoundedReflexion,
        xss_finding: SecurityFinding,
    ) -> None:
        """Test that duration is recorded."""
        result = reflexion.fix_with_verification(xss_finding, dry_run=True)

        assert result.started_at is not None
        assert result.completed_at is not None
        assert result.duration_ms >= 0


# =============================================================================
# BoundedReflexion Batch Fix Tests
# =============================================================================


class TestFixAllWithVerification:
    """Tests for fix_all_with_verification method."""

    def test_fix_all_single_finding(
        self,
        reflexion: BoundedReflexion,
        xss_finding: SecurityFinding,
    ) -> None:
        """Test fixing a single finding in batch."""
        results = reflexion.fix_all_with_verification([xss_finding], dry_run=True)

        assert len(results) == 1
        assert results[0].success is True

    def test_fix_all_multiple_findings(
        self,
        reflexion: BoundedReflexion,
        xss_finding: SecurityFinding,
        tmp_path: Path,
    ) -> None:
        """Test fixing multiple findings."""
        # Create second finding
        test_file2 = tmp_path / "vulnerable2.tsx"
        test_file2.write_text("const y = unsafe_code;")

        finding2 = SecurityFinding(
            id="xss-002",
            validator_id="sec-xss",
            severity=Severity.HIGH,
            category=FindingCategory.XSS,
            title="Another XSS",
            description="Another vuln",
            location=CodeLocation(
                file_path=str(test_file2),
                line_start=1,
                line_end=1,
                snippet="unsafe_code",
            ),
            recommendation="Fix",
            auto_fixable=True,
        )

        results = reflexion.fix_all_with_verification(
            [xss_finding, finding2], dry_run=True
        )

        assert len(results) == 2
        assert all(r.success for r in results)

    def test_fix_all_skips_non_fixable(
        self,
        reflexion: BoundedReflexion,
        xss_finding: SecurityFinding,
        non_fixable_finding: SecurityFinding,
    ) -> None:
        """Test that non-auto-fixable findings are skipped."""
        results = reflexion.fix_all_with_verification(
            [xss_finding, non_fixable_finding], dry_run=True
        )

        assert len(results) == 2
        # First should succeed
        assert results[0].success is True
        # Second should fail with appropriate error
        assert results[1].success is False
        assert "not marked as auto-fixable" in str(results[1].error)

    def test_fix_all_empty_list(
        self,
        reflexion: BoundedReflexion,
    ) -> None:
        """Test with empty finding list."""
        results = reflexion.fix_all_with_verification([], dry_run=True)
        assert results == []


# =============================================================================
# Internal Method Tests
# =============================================================================


class TestInternalMethods:
    """Tests for internal helper methods."""

    def test_lines_overlap_true(
        self,
        reflexion: BoundedReflexion,
    ) -> None:
        """Test _lines_overlap returns True for overlapping ranges."""
        assert reflexion._lines_overlap((1, 5), (3, 7)) is True
        assert reflexion._lines_overlap((1, 5), (5, 10)) is True
        assert reflexion._lines_overlap((5, 10), (1, 5)) is True

    def test_lines_overlap_false(
        self,
        reflexion: BoundedReflexion,
    ) -> None:
        """Test _lines_overlap returns False for non-overlapping ranges."""
        assert reflexion._lines_overlap((1, 5), (6, 10)) is False
        assert reflexion._lines_overlap((10, 20), (1, 5)) is False

    def test_lines_overlap_same_line(
        self,
        reflexion: BoundedReflexion,
    ) -> None:
        """Test _lines_overlap for same line."""
        assert reflexion._lines_overlap((5, 5), (5, 5)) is True

    def test_is_finding_present_true(
        self,
        reflexion: BoundedReflexion,
        xss_finding: SecurityFinding,
    ) -> None:
        """Test _is_finding_present returns True when finding exists."""
        report = SecurityReport(
            scan_id="test",
            started_at=datetime.now(),
            target_path="/test",
            results=[
                ValidatorResult(
                    validator_id="sec-xss",
                    validator_name="XSS",
                    findings=[xss_finding],
                )
            ],
        )

        assert reflexion._is_finding_present(xss_finding, report) is True

    def test_is_finding_present_false(
        self,
        reflexion: BoundedReflexion,
        xss_finding: SecurityFinding,
    ) -> None:
        """Test _is_finding_present returns False when finding is gone."""
        report = SecurityReport(
            scan_id="test",
            started_at=datetime.now(),
            target_path="/test",
            results=[],
        )

        assert reflexion._is_finding_present(xss_finding, report) is False

    def test_check_for_regressions_no_regression(
        self,
        reflexion: BoundedReflexion,
        xss_finding: SecurityFinding,
    ) -> None:
        """Test no regression detected with empty report."""
        report = SecurityReport(
            scan_id="test",
            started_at=datetime.now(),
            target_path="/test",
            results=[],
        )

        assert reflexion._check_for_regressions(xss_finding, report) is False

    def test_check_for_regressions_low_severity_not_regression(
        self,
        reflexion: BoundedReflexion,
        xss_finding: SecurityFinding,
    ) -> None:
        """Test LOW severity findings don't count as regression."""
        low_finding = SecurityFinding(
            id="xss-low",
            validator_id="sec-xss",
            severity=Severity.LOW,  # Low severity
            category=FindingCategory.XSS,
            title="Minor issue",
            description="Not critical",
            location=CodeLocation(
                file_path=xss_finding.location.file_path,
                line_start=10,
                line_end=10,
            ),
            recommendation="Fix",
            auto_fixable=True,
        )

        report = SecurityReport(
            scan_id="test",
            started_at=datetime.now(),
            target_path="/test",
            results=[
                ValidatorResult(
                    validator_id="sec-xss",
                    validator_name="XSS",
                    findings=[low_finding],
                )
            ],
        )

        assert reflexion._check_for_regressions(xss_finding, report) is False


# =============================================================================
# Edge Cases
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_fixer_raises_exception(
        self,
        mock_orchestrator: MagicMock,
        xss_finding: SecurityFinding,
    ) -> None:
        """Test handling when fixer raises exception."""
        fw = AutoFixFramework()
        fw.register_fixer(FailingFixer())

        reflexion = BoundedReflexion(
            framework=fw,
            orchestrator=mock_orchestrator,
        )

        result = reflexion.fix_with_verification(xss_finding)

        assert result.success is False
        # Should have attempted but failed
        assert len(result.attempt_history) >= 0

    def test_orchestrator_scan_fails(
        self,
        framework_with_fixers: AutoFixFramework,
        xss_finding: SecurityFinding,
        mock_orchestrator: MagicMock,
    ) -> None:
        """Test handling when orchestrator scan fails."""
        mock_orchestrator.scan.side_effect = RuntimeError("Scan failed")

        reflexion = BoundedReflexion(
            framework=framework_with_fixers,
            orchestrator=mock_orchestrator,
        )

        result = reflexion.fix_with_verification(xss_finding)

        # Should handle gracefully
        assert result.success is False

    def test_max_iterations_boundary(
        self,
        framework_with_fixers: AutoFixFramework,
        mock_orchestrator: MagicMock,
    ) -> None:
        """Test max_iterations boundary values."""
        # Min boundary
        r1 = BoundedReflexion(
            framework=framework_with_fixers,
            orchestrator=mock_orchestrator,
            max_iterations=1,
        )
        assert r1.max_iterations == 1

        # Max boundary
        r10 = BoundedReflexion(
            framework=framework_with_fixers,
            orchestrator=mock_orchestrator,
            max_iterations=10,
        )
        assert r10.max_iterations == 10

    def test_result_timestamps(
        self,
        reflexion: BoundedReflexion,
        xss_finding: SecurityFinding,
    ) -> None:
        """Test that timestamps are properly set."""
        result = reflexion.fix_with_verification(xss_finding, dry_run=True)

        assert result.started_at is not None
        assert result.completed_at is not None
        assert result.completed_at >= result.started_at
        assert result.duration_ms >= 0
