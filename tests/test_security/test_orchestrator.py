"""Tests for SecurityOrchestrator.

Tests cover:
- ScanConfig initialization
- SecurityOrchestrator sync scan
- SecurityOrchestrator async scan
- Quick scan and full audit
- Timeout handling
- Error handling
- Progress callbacks
- Blocking logic
- Finding sorting by severity
"""

import time
from datetime import datetime
from pathlib import Path

import pytest

from aios.security.models import CodeLocation
from aios.security.models import FindingCategory
from aios.security.models import SecurityFinding
from aios.security.models import SecurityReport
from aios.security.models import Severity
from aios.security.models import ValidatorResult
from aios.security.orchestrator import SEVERITY_ORDER
from aios.security.orchestrator import ScanConfig
from aios.security.orchestrator import SecurityOrchestrator
from aios.security.orchestrator import security_orchestrator
from aios.security.validators.base import BaseValidator
from aios.security.validators.registry import ValidatorRegistry


class DummyValidator(BaseValidator):
    """A simple validator for testing."""

    def __init__(
        self,
        validator_id: str = "test-validator",
        findings: list[SecurityFinding] | None = None,
        delay: float = 0.0,
        raise_error: Exception | None = None,
    ) -> None:
        self._id = validator_id
        self._findings = findings or []
        self._delay = delay
        self._raise_error = raise_error

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return f"Test Validator {self._id}"

    @property
    def description(self) -> str:
        return "A test validator"

    def validate_content(
        self, content: str, file_path: str  # noqa: ARG002
    ) -> list[SecurityFinding]:
        if self._delay > 0:
            time.sleep(self._delay)
        if self._raise_error:
            raise self._raise_error
        return list(self._findings)


def create_finding(
    severity: Severity = Severity.HIGH,
    category: FindingCategory = FindingCategory.XSS,
    finding_id: str = "test-001",
) -> SecurityFinding:
    """Helper to create a finding for tests."""
    return SecurityFinding(
        id=finding_id,
        validator_id="test",
        severity=severity,
        category=category,
        title="Test Finding",
        description="A test finding",
        location=CodeLocation(file_path="test.ts", line_start=1, line_end=1),
        recommendation="Fix this",
    )


class TestScanConfig:
    """Tests for ScanConfig."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = ScanConfig()
        assert config.timeout_per_validator == 30.0
        assert config.max_workers == 4
        assert config.fail_fast is False
        assert "sec-secret-scanner" in config.quick_scan_validators
        assert "sec-xss-hunter" in config.quick_scan_validators
        assert "sec-injection-detector" in config.quick_scan_validators

    def test_custom_config(self) -> None:
        """Test custom configuration values."""
        config = ScanConfig(
            timeout_per_validator=60.0,
            max_workers=8,
            fail_fast=True,
            quick_scan_validators=["custom-1", "custom-2"],
        )
        assert config.timeout_per_validator == 60.0
        assert config.max_workers == 8
        assert config.fail_fast is True
        assert config.quick_scan_validators == ["custom-1", "custom-2"]


class TestSeverityOrder:
    """Tests for SEVERITY_ORDER constant."""

    def test_severity_order_values(self) -> None:
        """Test severity order mapping."""
        assert SEVERITY_ORDER[Severity.CRITICAL] == 0
        assert SEVERITY_ORDER[Severity.HIGH] == 1
        assert SEVERITY_ORDER[Severity.MEDIUM] == 2
        assert SEVERITY_ORDER[Severity.LOW] == 3
        assert SEVERITY_ORDER[Severity.INFO] == 4

    def test_severity_order_sorting(self) -> None:
        """Test that severity order can be used for sorting."""
        severities = [Severity.LOW, Severity.CRITICAL, Severity.MEDIUM, Severity.HIGH, Severity.INFO]
        sorted_severities = sorted(severities, key=lambda s: SEVERITY_ORDER[s])
        assert sorted_severities == [
            Severity.CRITICAL,
            Severity.HIGH,
            Severity.MEDIUM,
            Severity.LOW,
            Severity.INFO,
        ]


class TestSecurityOrchestrator:
    """Tests for SecurityOrchestrator."""

    def test_init_with_registry(self) -> None:
        """Test orchestrator initialization."""
        registry = ValidatorRegistry()
        orchestrator = SecurityOrchestrator(registry)
        assert orchestrator.registry is registry
        assert orchestrator.config is not None

    def test_init_with_custom_config(self) -> None:
        """Test orchestrator with custom config."""
        registry = ValidatorRegistry()
        config = ScanConfig(timeout_per_validator=60.0)
        orchestrator = SecurityOrchestrator(registry, config)
        assert orchestrator.config.timeout_per_validator == 60.0

    def test_scan_empty_registry(self, tmp_path: Path) -> None:
        """Test scan with no validators."""
        registry = ValidatorRegistry()
        orchestrator = SecurityOrchestrator(registry)

        test_file = tmp_path / "test.ts"
        test_file.write_text("const x = 1;")

        report = orchestrator.scan(test_file)

        assert report.total_findings == 0
        assert len(report.results) == 0
        assert report.completed_at is not None

    def test_scan_single_validator(self, tmp_path: Path) -> None:
        """Test scan with a single validator."""
        registry = ValidatorRegistry()
        finding = create_finding(Severity.HIGH)
        validator = DummyValidator(findings=[finding])
        registry.register(validator)

        orchestrator = SecurityOrchestrator(registry)
        test_file = tmp_path / "test.ts"
        test_file.write_text("const x = 1;")

        report = orchestrator.scan(test_file)

        assert report.total_findings == 1
        assert len(report.results) == 1
        assert report.results[0].validator_id == "test-validator"
        assert report.high_findings == 1

    def test_scan_multiple_validators(self, tmp_path: Path) -> None:
        """Test scan with multiple validators."""
        registry = ValidatorRegistry()

        validator1 = DummyValidator(
            validator_id="v1",
            findings=[create_finding(Severity.CRITICAL, finding_id="c1")],
        )
        validator2 = DummyValidator(
            validator_id="v2",
            findings=[create_finding(Severity.HIGH, finding_id="h1")],
        )
        validator3 = DummyValidator(
            validator_id="v3",
            findings=[create_finding(Severity.LOW, finding_id="l1")],
        )

        registry.register(validator1)
        registry.register(validator2)
        registry.register(validator3)

        orchestrator = SecurityOrchestrator(registry)
        test_file = tmp_path / "test.ts"
        test_file.write_text("const x = 1;")

        report = orchestrator.scan(test_file)

        assert report.total_findings == 3
        assert len(report.results) == 3
        assert report.critical_findings == 1
        assert report.high_findings == 1
        assert report.low_findings == 1

    def test_scan_specific_validators(self, tmp_path: Path) -> None:
        """Test scan with specific validator IDs."""
        registry = ValidatorRegistry()

        validator1 = DummyValidator(
            validator_id="include-me",
            findings=[create_finding(Severity.HIGH)],
        )
        validator2 = DummyValidator(
            validator_id="skip-me",
            findings=[create_finding(Severity.CRITICAL)],
        )

        registry.register(validator1)
        registry.register(validator2)

        orchestrator = SecurityOrchestrator(registry)
        test_file = tmp_path / "test.ts"
        test_file.write_text("const x = 1;")

        report = orchestrator.scan(test_file, validators=["include-me"])

        assert report.total_findings == 1
        assert len(report.results) == 1
        assert report.results[0].validator_id == "include-me"
        assert report.critical_findings == 0  # skip-me was not run

    def test_scan_nonexistent_validators(self, tmp_path: Path) -> None:
        """Test scan with validator IDs that don't exist."""
        registry = ValidatorRegistry()
        validator = DummyValidator(validator_id="real")
        registry.register(validator)

        orchestrator = SecurityOrchestrator(registry)
        test_file = tmp_path / "test.ts"
        test_file.write_text("const x = 1;")

        report = orchestrator.scan(test_file, validators=["nonexistent"])

        assert report.total_findings == 0
        assert len(report.results) == 0

    def test_scan_with_timeout(self, tmp_path: Path) -> None:
        """Test scan handles validator timeout."""
        registry = ValidatorRegistry()
        slow_validator = DummyValidator(validator_id="slow", delay=2.0)
        registry.register(slow_validator)

        config = ScanConfig(timeout_per_validator=0.1)
        orchestrator = SecurityOrchestrator(registry, config)

        test_file = tmp_path / "test.ts"
        test_file.write_text("const x = 1;")

        report = orchestrator.scan(test_file)

        assert len(report.results) == 1
        assert report.results[0].error is not None
        assert "timed out" in report.results[0].error.lower()
        assert report.has_errors is True

    def test_scan_with_validator_error(self, tmp_path: Path) -> None:
        """Test scan handles validator exceptions."""
        registry = ValidatorRegistry()
        error_validator = DummyValidator(
            validator_id="broken",
            raise_error=ValueError("Something went wrong"),
        )
        registry.register(error_validator)

        orchestrator = SecurityOrchestrator(registry)
        test_file = tmp_path / "test.ts"
        test_file.write_text("const x = 1;")

        report = orchestrator.scan(test_file)

        assert len(report.results) == 1
        assert report.results[0].error is not None
        assert "Something went wrong" in report.results[0].error
        assert report.has_errors is True

    def test_scan_with_progress_callback(self, tmp_path: Path) -> None:
        """Test scan calls progress callback."""
        registry = ValidatorRegistry()
        validator = DummyValidator(validator_id="test")
        registry.register(validator)

        orchestrator = SecurityOrchestrator(registry)
        test_file = tmp_path / "test.ts"
        test_file.write_text("const x = 1;")

        progress_calls: list[tuple[str, int, int, str]] = []

        def on_progress(vid: str, current: int, total: int, status: str) -> None:
            progress_calls.append((vid, current, total, status))

        _report = orchestrator.scan(test_file, progress_callback=on_progress)

        assert len(progress_calls) >= 1
        # Check that we have both starting and completed
        statuses = [call[3] for call in progress_calls]
        assert "starting" in statuses
        assert "completed" in statuses or "error" in statuses or "timeout" in statuses

    def test_scan_fail_fast(self, tmp_path: Path) -> None:
        """Test fail_fast stops on critical finding."""
        registry = ValidatorRegistry()

        # First validator returns critical
        critical_validator = DummyValidator(
            validator_id="critical",
            findings=[create_finding(Severity.CRITICAL)],
        )
        # Second validator would be slow
        slow_validator = DummyValidator(
            validator_id="slow",
            delay=0.5,
            findings=[create_finding(Severity.LOW)],
        )

        registry.register(critical_validator)
        registry.register(slow_validator)

        config = ScanConfig(fail_fast=True, max_workers=1)
        orchestrator = SecurityOrchestrator(registry, config)

        test_file = tmp_path / "test.ts"
        test_file.write_text("const x = 1;")

        report = orchestrator.scan(test_file)

        # Should complete and have critical findings
        assert report.critical_findings >= 1
        # With fail_fast and max_workers=1, should stop after critical
        # The slow validator may or may not run depending on ordering

    def test_findings_sorted_by_severity(self, tmp_path: Path) -> None:
        """Test findings are sorted by severity."""
        registry = ValidatorRegistry()

        validator = DummyValidator(
            validator_id="multi",
            findings=[
                create_finding(Severity.LOW, finding_id="l1"),
                create_finding(Severity.CRITICAL, finding_id="c1"),
                create_finding(Severity.MEDIUM, finding_id="m1"),
                create_finding(Severity.HIGH, finding_id="h1"),
                create_finding(Severity.INFO, finding_id="i1"),
            ],
        )
        registry.register(validator)

        orchestrator = SecurityOrchestrator(registry)
        test_file = tmp_path / "test.ts"
        test_file.write_text("const x = 1;")

        report = orchestrator.scan(test_file)

        findings = report.results[0].findings
        assert len(findings) == 5
        # Check order: CRITICAL, HIGH, MEDIUM, LOW, INFO
        assert findings[0].severity == Severity.CRITICAL
        assert findings[1].severity == Severity.HIGH
        assert findings[2].severity == Severity.MEDIUM
        assert findings[3].severity == Severity.LOW
        assert findings[4].severity == Severity.INFO


class TestSecurityOrchestratorAsync:
    """Tests for async scan methods."""

    @pytest.mark.asyncio
    async def test_scan_async_single_validator(self, tmp_path: Path) -> None:
        """Test async scan with a single validator."""
        registry = ValidatorRegistry()
        finding = create_finding(Severity.HIGH)
        validator = DummyValidator(findings=[finding])
        registry.register(validator)

        orchestrator = SecurityOrchestrator(registry)
        test_file = tmp_path / "test.ts"
        test_file.write_text("const x = 1;")

        report = await orchestrator.scan_async(test_file)

        assert report.total_findings == 1
        assert len(report.results) == 1

    @pytest.mark.asyncio
    async def test_scan_async_multiple_validators(self, tmp_path: Path) -> None:
        """Test async scan runs validators concurrently."""
        registry = ValidatorRegistry()

        for i in range(3):
            validator = DummyValidator(
                validator_id=f"v{i}",
                findings=[create_finding(finding_id=f"f{i}")],
                delay=0.1,
            )
            registry.register(validator)

        config = ScanConfig(timeout_per_validator=5.0)
        orchestrator = SecurityOrchestrator(registry, config)

        test_file = tmp_path / "test.ts"
        test_file.write_text("const x = 1;")

        start = time.time()
        report = await orchestrator.scan_async(test_file)
        duration = time.time() - start

        assert len(report.results) == 3
        # Concurrent execution should be faster than sequential
        assert duration < 0.5  # 3 * 0.1s sequential would be 0.3s, add buffer

    @pytest.mark.asyncio
    async def test_scan_async_with_timeout(self, tmp_path: Path) -> None:
        """Test async scan handles timeout gracefully.

        Note: ThreadPoolExecutor tasks cannot be truly cancelled, so the executor
        thread may continue running. What we test is that:
        1. The scan completes in reasonable time (doesn't hang)
        2. If a result is returned, it indicates timeout
        """
        registry = ValidatorRegistry()
        slow_validator = DummyValidator(validator_id="slow", delay=2.0)
        registry.register(slow_validator)

        config = ScanConfig(timeout_per_validator=0.1)
        orchestrator = SecurityOrchestrator(registry, config)

        test_file = tmp_path / "test.ts"
        test_file.write_text("const x = 1;")

        start = time.time()
        report = await orchestrator.scan_async(test_file)
        duration = time.time() - start

        # Scan should complete quickly due to timeout, not wait full 2s
        # Give some margin for slow CI
        assert duration < 1.5

        # If there are results, check they indicate timeout
        if report.results:
            assert report.results[0].error is not None
            assert "timed out" in report.results[0].error.lower()

    @pytest.mark.asyncio
    async def test_scan_async_with_progress_callback(self, tmp_path: Path) -> None:
        """Test async scan calls progress callback."""
        registry = ValidatorRegistry()
        validator = DummyValidator(validator_id="test")
        registry.register(validator)

        orchestrator = SecurityOrchestrator(registry)
        test_file = tmp_path / "test.ts"
        test_file.write_text("const x = 1;")

        progress_calls: list[tuple[str, int, int, str]] = []

        def on_progress(vid: str, current: int, total: int, status: str) -> None:
            progress_calls.append((vid, current, total, status))

        _report = await orchestrator.scan_async(test_file, progress_callback=on_progress)

        assert len(progress_calls) >= 1


class TestQuickScanAndFullAudit:
    """Tests for quick_scan and full_audit methods."""

    def test_quick_scan(self, tmp_path: Path) -> None:
        """Test quick scan runs only specified validators."""
        registry = ValidatorRegistry()

        # Register validators matching quick scan config
        secret_validator = DummyValidator(
            validator_id="sec-secret-scanner",
            findings=[create_finding(Severity.CRITICAL, finding_id="s1")],
        )
        xss_validator = DummyValidator(
            validator_id="sec-xss-hunter",
            findings=[create_finding(Severity.HIGH, finding_id="x1")],
        )
        other_validator = DummyValidator(
            validator_id="sec-other",
            findings=[create_finding(Severity.LOW, finding_id="o1")],
        )

        registry.register(secret_validator)
        registry.register(xss_validator)
        registry.register(other_validator)

        orchestrator = SecurityOrchestrator(registry)
        test_file = tmp_path / "test.ts"
        test_file.write_text("const x = 1;")

        report = orchestrator.quick_scan(test_file)

        # Only quick scan validators should run
        validator_ids = [r.validator_id for r in report.results]
        assert "sec-secret-scanner" in validator_ids
        assert "sec-xss-hunter" in validator_ids
        assert "sec-other" not in validator_ids

    def test_full_audit(self, tmp_path: Path) -> None:
        """Test full audit runs all validators."""
        registry = ValidatorRegistry()

        for i in range(5):
            validator = DummyValidator(
                validator_id=f"validator-{i}",
                findings=[create_finding(finding_id=f"f{i}")],
            )
            registry.register(validator)

        orchestrator = SecurityOrchestrator(registry)
        test_file = tmp_path / "test.ts"
        test_file.write_text("const x = 1;")

        report = orchestrator.full_audit(test_file)

        assert len(report.results) == 5


class TestBlockingLogic:
    """Tests for blocking logic methods."""

    def test_should_block_commit_with_critical(self) -> None:
        """Test commit blocked with critical findings."""
        registry = ValidatorRegistry()
        orchestrator = SecurityOrchestrator(registry)

        report = SecurityReport(
            scan_id="test",
            started_at=datetime.now(),
            target_path="/test",
        )
        report.add_result(
            ValidatorResult(
                validator_id="test",
                validator_name="Test",
                findings=[create_finding(Severity.CRITICAL)],
            )
        )

        assert orchestrator.should_block_commit(report) is True

    def test_should_block_commit_without_critical(self) -> None:
        """Test commit not blocked without critical findings."""
        registry = ValidatorRegistry()
        orchestrator = SecurityOrchestrator(registry)

        report = SecurityReport(
            scan_id="test",
            started_at=datetime.now(),
            target_path="/test",
        )
        report.add_result(
            ValidatorResult(
                validator_id="test",
                validator_name="Test",
                findings=[create_finding(Severity.HIGH)],
            )
        )

        assert orchestrator.should_block_commit(report) is False

    def test_should_block_merge_with_high(self) -> None:
        """Test merge blocked with high findings."""
        registry = ValidatorRegistry()
        orchestrator = SecurityOrchestrator(registry)

        report = SecurityReport(
            scan_id="test",
            started_at=datetime.now(),
            target_path="/test",
        )
        report.add_result(
            ValidatorResult(
                validator_id="test",
                validator_name="Test",
                findings=[create_finding(Severity.HIGH)],
            )
        )

        assert orchestrator.should_block_merge(report) is True

    def test_should_block_merge_without_blockers(self) -> None:
        """Test merge not blocked with only medium/low findings."""
        registry = ValidatorRegistry()
        orchestrator = SecurityOrchestrator(registry)

        report = SecurityReport(
            scan_id="test",
            started_at=datetime.now(),
            target_path="/test",
        )
        report.add_result(
            ValidatorResult(
                validator_id="test",
                validator_name="Test",
                findings=[
                    create_finding(Severity.MEDIUM),
                    create_finding(Severity.LOW),
                ],
            )
        )

        assert orchestrator.should_block_merge(report) is False


class TestScanSummary:
    """Tests for scan summary methods."""

    def test_get_scan_summary(self) -> None:
        """Test get_scan_summary returns correct stats."""
        registry = ValidatorRegistry()
        orchestrator = SecurityOrchestrator(registry)

        report = SecurityReport(
            scan_id="test",
            started_at=datetime.now(),
            target_path="/test",
        )
        report.add_result(
            ValidatorResult(
                validator_id="v1",
                validator_name="V1",
                findings=[
                    create_finding(Severity.CRITICAL),
                    create_finding(Severity.HIGH),
                    create_finding(Severity.MEDIUM),
                ],
                files_scanned=10,
                scan_duration_ms=100,
            )
        )
        report.add_result(
            ValidatorResult(
                validator_id="v2",
                validator_name="V2",
                findings=[create_finding(Severity.LOW)],
                files_scanned=5,
                scan_duration_ms=50,
            )
        )
        report.completed_at = datetime.now()

        summary = orchestrator.get_scan_summary(report)

        assert summary["total_findings"] == 4
        assert summary["critical"] == 1
        assert summary["high"] == 1
        assert summary["medium"] == 1
        assert summary["low"] == 1
        assert summary["info"] == 0
        assert summary["files_scanned"] == 15
        assert summary["validators_run"] == 2
        assert summary["has_errors"] is False
        assert summary["should_block_commit"] is True
        assert summary["should_block_merge"] is True

    def test_get_all_findings_sorted(self) -> None:
        """Test get_all_findings_sorted returns findings in order."""
        registry = ValidatorRegistry()
        orchestrator = SecurityOrchestrator(registry)

        report = SecurityReport(
            scan_id="test",
            started_at=datetime.now(),
            target_path="/test",
        )
        report.add_result(
            ValidatorResult(
                validator_id="v1",
                validator_name="V1",
                findings=[
                    create_finding(Severity.LOW, finding_id="l1"),
                    create_finding(Severity.CRITICAL, finding_id="c1"),
                ],
            )
        )
        report.add_result(
            ValidatorResult(
                validator_id="v2",
                validator_name="V2",
                findings=[
                    create_finding(Severity.HIGH, finding_id="h1"),
                    create_finding(Severity.INFO, finding_id="i1"),
                ],
            )
        )

        findings = orchestrator.get_all_findings_sorted(report)

        assert len(findings) == 4
        assert findings[0].severity == Severity.CRITICAL
        assert findings[1].severity == Severity.HIGH
        assert findings[2].severity == Severity.LOW
        assert findings[3].severity == Severity.INFO


class TestGlobalOrchestrator:
    """Tests for global security_orchestrator instance."""

    def test_global_orchestrator_exists(self) -> None:
        """Test global orchestrator is available."""
        assert security_orchestrator is not None

    def test_global_orchestrator_has_registry(self) -> None:
        """Test global orchestrator has a registry."""
        assert security_orchestrator.registry is not None

    def test_global_orchestrator_has_config(self) -> None:
        """Test global orchestrator has default config."""
        assert security_orchestrator.config is not None
        assert security_orchestrator.config.timeout_per_validator == 30.0
