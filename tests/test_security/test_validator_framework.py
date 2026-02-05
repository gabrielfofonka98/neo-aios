"""Tests for validator framework.

Tests cover:
- Security models (Severity, FindingCategory, CodeLocation, SecurityFinding)
- ValidatorResult and SecurityReport
- BaseValidator abstract class
- ValidatorRegistry
"""

from datetime import datetime
from pathlib import Path

import pytest

from aios.security.models import (
    CodeLocation,
    FindingCategory,
    SecurityFinding,
    SecurityReport,
    Severity,
    ValidatorResult,
)
from aios.security.validators.base import BaseValidator, SecurityValidator
from aios.security.validators.registry import ValidatorRegistry


class TestSeverityEnum:
    """Tests for Severity enum."""

    def test_severity_values(self) -> None:
        """Test all severity values exist."""
        assert Severity.CRITICAL.value == "critical"
        assert Severity.HIGH.value == "high"
        assert Severity.MEDIUM.value == "medium"
        assert Severity.LOW.value == "low"
        assert Severity.INFO.value == "info"

    def test_severity_count(self) -> None:
        """Test there are exactly 5 severity levels."""
        assert len(Severity) == 5


class TestFindingCategoryEnum:
    """Tests for FindingCategory enum."""

    def test_category_values(self) -> None:
        """Test all category values exist."""
        assert FindingCategory.XSS.value == "xss"
        assert FindingCategory.INJECTION.value == "injection"
        assert FindingCategory.AUTH.value == "authentication"
        assert FindingCategory.CRYPTO.value == "cryptography"
        assert FindingCategory.CONFIG.value == "configuration"
        assert FindingCategory.DATA_EXPOSURE.value == "data_exposure"
        assert FindingCategory.INPUT_VALIDATION.value == "input_validation"
        assert FindingCategory.ACCESS_CONTROL.value == "access_control"

    def test_category_count(self) -> None:
        """Test there are exactly 8 categories."""
        assert len(FindingCategory) == 8


class TestCodeLocation:
    """Tests for CodeLocation model."""

    def test_minimal_code_location(self) -> None:
        """Test creating CodeLocation with required fields only."""
        location = CodeLocation(
            file_path="test.ts",
            line_start=10,
            line_end=10,
        )
        assert location.file_path == "test.ts"
        assert location.line_start == 10
        assert location.line_end == 10
        assert location.column_start is None
        assert location.column_end is None
        assert location.snippet is None

    def test_full_code_location(self) -> None:
        """Test creating CodeLocation with all fields."""
        location = CodeLocation(
            file_path="src/app.tsx",
            line_start=42,
            line_end=45,
            column_start=5,
            column_end=20,
            snippet="const x = userInput;",
        )
        assert location.file_path == "src/app.tsx"
        assert location.line_start == 42
        assert location.line_end == 45
        assert location.column_start == 5
        assert location.column_end == 20
        assert location.snippet == "const x = userInput;"


class TestSecurityFinding:
    """Tests for SecurityFinding model."""

    def test_minimal_finding(self) -> None:
        """Test creating finding with required fields."""
        finding = SecurityFinding(
            id="test-001",
            validator_id="test-validator",
            severity=Severity.HIGH,
            category=FindingCategory.XSS,
            title="Test Finding",
            description="Test description",
            location=CodeLocation(file_path="test.ts", line_start=10, line_end=10),
            recommendation="Fix this",
        )

        assert finding.id == "test-001"
        assert finding.validator_id == "test-validator"
        assert finding.severity == Severity.HIGH
        assert finding.category == FindingCategory.XSS
        assert finding.title == "Test Finding"
        assert finding.description == "Test description"
        assert finding.recommendation == "Fix this"
        assert finding.auto_fixable is False
        assert finding.fix_snippet is None
        assert finding.confidence == 1.0
        assert finding.cwe_id is None
        assert finding.owasp_id is None
        assert isinstance(finding.found_at, datetime)

    def test_finding_with_metadata(self) -> None:
        """Test creating finding with all metadata."""
        finding = SecurityFinding(
            id="xss-001",
            validator_id="sec-xss-dom",
            severity=Severity.CRITICAL,
            category=FindingCategory.XSS,
            title="XSS Vulnerability",
            description="User input passed to unsafe method",
            location=CodeLocation(
                file_path="app.tsx",
                line_start=42,
                line_end=42,
                snippet="element.setContent(userInput);",
            ),
            recommendation="Use textContent instead",
            auto_fixable=True,
            fix_snippet="element.textContent = userInput;",
            confidence=0.95,
            cwe_id="CWE-79",
            owasp_id="A03:2021",
        )

        assert finding.auto_fixable is True
        assert finding.fix_snippet == "element.textContent = userInput;"
        assert finding.confidence == 0.95
        assert finding.cwe_id == "CWE-79"
        assert finding.owasp_id == "A03:2021"

    def test_confidence_validation(self) -> None:
        """Test confidence must be between 0 and 1."""
        # Valid confidence
        finding = SecurityFinding(
            id="test",
            validator_id="test",
            severity=Severity.LOW,
            category=FindingCategory.CONFIG,
            title="Test",
            description="Test",
            location=CodeLocation(file_path="test.ts", line_start=1, line_end=1),
            recommendation="Test",
            confidence=0.5,
        )
        assert finding.confidence == 0.5

        # Invalid confidence should raise
        with pytest.raises(ValueError):
            SecurityFinding(
                id="test",
                validator_id="test",
                severity=Severity.LOW,
                category=FindingCategory.CONFIG,
                title="Test",
                description="Test",
                location=CodeLocation(file_path="test.ts", line_start=1, line_end=1),
                recommendation="Test",
                confidence=1.5,  # Invalid
            )


class TestValidatorResult:
    """Tests for ValidatorResult model."""

    def test_empty_result(self) -> None:
        """Test result with no findings."""
        result = ValidatorResult(
            validator_id="test",
            validator_name="Test Validator",
        )

        assert result.validator_id == "test"
        assert result.validator_name == "Test Validator"
        assert result.findings == []
        assert result.files_scanned == 0
        assert result.scan_duration_ms == 0
        assert result.error is None
        assert result.has_findings is False
        assert result.critical_count == 0
        assert result.high_count == 0
        assert result.medium_count == 0
        assert result.low_count == 0
        assert result.info_count == 0

    def test_result_with_findings(self) -> None:
        """Test result with multiple findings."""
        findings = [
            SecurityFinding(
                id="1",
                validator_id="test",
                severity=Severity.CRITICAL,
                category=FindingCategory.XSS,
                title="Critical",
                description="...",
                location=CodeLocation(file_path="a.ts", line_start=1, line_end=1),
                recommendation="...",
            ),
            SecurityFinding(
                id="2",
                validator_id="test",
                severity=Severity.HIGH,
                category=FindingCategory.XSS,
                title="High",
                description="...",
                location=CodeLocation(file_path="b.ts", line_start=1, line_end=1),
                recommendation="...",
            ),
            SecurityFinding(
                id="3",
                validator_id="test",
                severity=Severity.HIGH,
                category=FindingCategory.INJECTION,
                title="High 2",
                description="...",
                location=CodeLocation(file_path="c.ts", line_start=1, line_end=1),
                recommendation="...",
            ),
            SecurityFinding(
                id="4",
                validator_id="test",
                severity=Severity.MEDIUM,
                category=FindingCategory.CONFIG,
                title="Medium",
                description="...",
                location=CodeLocation(file_path="d.ts", line_start=1, line_end=1),
                recommendation="...",
            ),
        ]

        result = ValidatorResult(
            validator_id="test",
            validator_name="Test Validator",
            findings=findings,
            files_scanned=4,
            scan_duration_ms=150,
        )

        assert result.has_findings is True
        assert result.critical_count == 1
        assert result.high_count == 2
        assert result.medium_count == 1
        assert result.low_count == 0
        assert result.info_count == 0
        assert result.files_scanned == 4
        assert result.scan_duration_ms == 150

    def test_result_with_error(self) -> None:
        """Test result with error."""
        result = ValidatorResult(
            validator_id="test",
            validator_name="Test Validator",
            error="File not found",
        )

        assert result.error == "File not found"
        assert result.has_findings is False


class TestSecurityReport:
    """Tests for SecurityReport model."""

    def test_empty_report(self) -> None:
        """Test report with no results."""
        report = SecurityReport(
            scan_id="scan-001",
            started_at=datetime.now(),
            target_path="/test",
        )

        assert report.scan_id == "scan-001"
        assert report.target_path == "/test"
        assert report.completed_at is None
        assert report.results == []
        assert report.total_findings == 0
        assert report.critical_findings == 0
        assert report.high_findings == 0
        assert report.has_blockers is False
        assert report.files_scanned == 0
        assert report.total_duration_ms == 0
        assert report.has_errors is False

    def test_report_with_results(self) -> None:
        """Test report aggregation."""
        report = SecurityReport(
            scan_id="scan-001",
            started_at=datetime.now(),
            target_path="/test",
        )

        # Add first result
        result1 = ValidatorResult(
            validator_id="test1",
            validator_name="Test 1",
            findings=[
                SecurityFinding(
                    id="1",
                    validator_id="test1",
                    severity=Severity.CRITICAL,
                    category=FindingCategory.INJECTION,
                    title="SQL Injection",
                    description="...",
                    location=CodeLocation(file_path="a.ts", line_start=1, line_end=1),
                    recommendation="...",
                )
            ],
            files_scanned=10,
            scan_duration_ms=100,
        )
        report.add_result(result1)

        # Add second result
        result2 = ValidatorResult(
            validator_id="test2",
            validator_name="Test 2",
            findings=[
                SecurityFinding(
                    id="2",
                    validator_id="test2",
                    severity=Severity.HIGH,
                    category=FindingCategory.XSS,
                    title="XSS",
                    description="...",
                    location=CodeLocation(file_path="b.ts", line_start=1, line_end=1),
                    recommendation="...",
                ),
                SecurityFinding(
                    id="3",
                    validator_id="test2",
                    severity=Severity.MEDIUM,
                    category=FindingCategory.CONFIG,
                    title="Config",
                    description="...",
                    location=CodeLocation(file_path="c.ts", line_start=1, line_end=1),
                    recommendation="...",
                ),
            ],
            files_scanned=5,
            scan_duration_ms=50,
        )
        report.add_result(result2)

        assert report.total_findings == 3
        assert report.critical_findings == 1
        assert report.high_findings == 1
        assert report.medium_findings == 1
        assert report.has_blockers is True
        assert report.files_scanned == 15
        assert report.total_duration_ms == 150
        assert report.has_errors is False

    def test_report_has_blockers(self) -> None:
        """Test has_blockers property."""
        report = SecurityReport(
            scan_id="scan-001",
            started_at=datetime.now(),
            target_path="/test",
        )

        # No findings - no blockers
        assert report.has_blockers is False

        # Add LOW finding - still no blockers
        result_low = ValidatorResult(
            validator_id="test",
            validator_name="Test",
            findings=[
                SecurityFinding(
                    id="1",
                    validator_id="test",
                    severity=Severity.LOW,
                    category=FindingCategory.CONFIG,
                    title="Low",
                    description="...",
                    location=CodeLocation(file_path="a.ts", line_start=1, line_end=1),
                    recommendation="...",
                )
            ],
        )
        report.add_result(result_low)
        assert report.has_blockers is False

        # Add HIGH finding - now has blockers
        result_high = ValidatorResult(
            validator_id="test2",
            validator_name="Test 2",
            findings=[
                SecurityFinding(
                    id="2",
                    validator_id="test2",
                    severity=Severity.HIGH,
                    category=FindingCategory.XSS,
                    title="High",
                    description="...",
                    location=CodeLocation(file_path="b.ts", line_start=1, line_end=1),
                    recommendation="...",
                )
            ],
        )
        report.add_result(result_high)
        assert report.has_blockers is True

    def test_report_with_errors(self) -> None:
        """Test report error detection."""
        report = SecurityReport(
            scan_id="scan-001",
            started_at=datetime.now(),
            target_path="/test",
        )

        # Add result without error
        result_ok = ValidatorResult(
            validator_id="test1",
            validator_name="Test 1",
        )
        report.add_result(result_ok)
        assert report.has_errors is False

        # Add result with error
        result_err = ValidatorResult(
            validator_id="test2",
            validator_name="Test 2",
            error="Something went wrong",
        )
        report.add_result(result_err)
        assert report.has_errors is True

    def test_get_findings_by_severity(self) -> None:
        """Test filtering findings by severity."""
        report = SecurityReport(
            scan_id="scan-001",
            started_at=datetime.now(),
            target_path="/test",
        )

        result = ValidatorResult(
            validator_id="test",
            validator_name="Test",
            findings=[
                SecurityFinding(
                    id="1",
                    validator_id="test",
                    severity=Severity.CRITICAL,
                    category=FindingCategory.XSS,
                    title="Critical",
                    description="...",
                    location=CodeLocation(file_path="a.ts", line_start=1, line_end=1),
                    recommendation="...",
                ),
                SecurityFinding(
                    id="2",
                    validator_id="test",
                    severity=Severity.HIGH,
                    category=FindingCategory.XSS,
                    title="High",
                    description="...",
                    location=CodeLocation(file_path="b.ts", line_start=1, line_end=1),
                    recommendation="...",
                ),
                SecurityFinding(
                    id="3",
                    validator_id="test",
                    severity=Severity.HIGH,
                    category=FindingCategory.INJECTION,
                    title="High 2",
                    description="...",
                    location=CodeLocation(file_path="c.ts", line_start=1, line_end=1),
                    recommendation="...",
                ),
            ],
        )
        report.add_result(result)

        critical = report.get_findings_by_severity(Severity.CRITICAL)
        assert len(critical) == 1
        assert critical[0].id == "1"

        high = report.get_findings_by_severity(Severity.HIGH)
        assert len(high) == 2

        medium = report.get_findings_by_severity(Severity.MEDIUM)
        assert len(medium) == 0

    def test_get_findings_by_category(self) -> None:
        """Test filtering findings by category."""
        report = SecurityReport(
            scan_id="scan-001",
            started_at=datetime.now(),
            target_path="/test",
        )

        result = ValidatorResult(
            validator_id="test",
            validator_name="Test",
            findings=[
                SecurityFinding(
                    id="1",
                    validator_id="test",
                    severity=Severity.HIGH,
                    category=FindingCategory.XSS,
                    title="XSS 1",
                    description="...",
                    location=CodeLocation(file_path="a.ts", line_start=1, line_end=1),
                    recommendation="...",
                ),
                SecurityFinding(
                    id="2",
                    validator_id="test",
                    severity=Severity.HIGH,
                    category=FindingCategory.XSS,
                    title="XSS 2",
                    description="...",
                    location=CodeLocation(file_path="b.ts", line_start=1, line_end=1),
                    recommendation="...",
                ),
                SecurityFinding(
                    id="3",
                    validator_id="test",
                    severity=Severity.MEDIUM,
                    category=FindingCategory.INJECTION,
                    title="Injection",
                    description="...",
                    location=CodeLocation(file_path="c.ts", line_start=1, line_end=1),
                    recommendation="...",
                ),
            ],
        )
        report.add_result(result)

        xss = report.get_findings_by_category(FindingCategory.XSS)
        assert len(xss) == 2

        injection = report.get_findings_by_category(FindingCategory.INJECTION)
        assert len(injection) == 1
        assert injection[0].id == "3"

        auth = report.get_findings_by_category(FindingCategory.AUTH)
        assert len(auth) == 0


class TestBaseValidator:
    """Tests for BaseValidator abstract class."""

    def test_custom_validator(self, tmp_path: Path) -> None:
        """Test implementing a custom validator."""

        class TestValidator(BaseValidator):
            @property
            def id(self) -> str:
                return "test-validator"

            @property
            def name(self) -> str:
                return "Test Validator"

            @property
            def description(self) -> str:
                return "A test validator"

            def validate_content(
                self, content: str, file_path: str
            ) -> list[SecurityFinding]:
                findings: list[SecurityFinding] = []
                if "DANGEROUS" in content:
                    findings.append(
                        SecurityFinding(
                            id=f"test-{file_path}",
                            validator_id=self.id,
                            severity=Severity.HIGH,
                            category=FindingCategory.CONFIG,
                            title="Dangerous content found",
                            description="Content contains DANGEROUS",
                            location=CodeLocation(
                                file_path=file_path, line_start=1, line_end=1
                            ),
                            recommendation="Remove DANGEROUS",
                        )
                    )
                return findings

        # Create test file
        test_file = tmp_path / "test.ts"
        test_file.write_text("const x = 'DANGEROUS';")

        validator = TestValidator()
        result = validator.validate(test_file)

        assert result.has_findings is True
        assert len(result.findings) == 1
        assert result.findings[0].severity == Severity.HIGH
        assert result.files_scanned == 1
        assert result.error is None

    def test_validator_on_directory(self, tmp_path: Path) -> None:
        """Test validator scanning a directory."""

        class CountingValidator(BaseValidator):
            @property
            def id(self) -> str:
                return "counting-validator"

            @property
            def name(self) -> str:
                return "Counting Validator"

            @property
            def description(self) -> str:
                return "Counts files"

            def validate_content(
                self, content: str, file_path: str
            ) -> list[SecurityFinding]:
                return []

        # Create test files
        (tmp_path / "file1.ts").write_text("content1")
        (tmp_path / "file2.tsx").write_text("content2")
        (tmp_path / "file3.py").write_text("content3")  # Not scanned
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "file4.js").write_text("content4")

        validator = CountingValidator()
        result = validator.validate(tmp_path)

        assert result.files_scanned == 3  # .ts, .tsx, .js (not .py)
        assert result.error is None

    def test_validator_custom_extensions(self, tmp_path: Path) -> None:
        """Test validator with custom file extensions."""

        class PythonValidator(BaseValidator):
            @property
            def id(self) -> str:
                return "python-validator"

            @property
            def name(self) -> str:
                return "Python Validator"

            @property
            def description(self) -> str:
                return "Scans Python files"

            @property
            def file_extensions(self) -> list[str]:
                return [".py"]

            def validate_content(
                self, content: str, file_path: str
            ) -> list[SecurityFinding]:
                return []

        # Create test files
        (tmp_path / "file1.py").write_text("content1")
        (tmp_path / "file2.ts").write_text("content2")

        validator = PythonValidator()
        result = validator.validate(tmp_path)

        assert result.files_scanned == 1  # Only .py

    def test_validator_on_nonexistent_file(self, tmp_path: Path) -> None:
        """Test validator handles missing files gracefully."""

        class SimpleValidator(BaseValidator):
            @property
            def id(self) -> str:
                return "simple"

            @property
            def name(self) -> str:
                return "Simple"

            @property
            def description(self) -> str:
                return "Simple validator"

            def validate_content(
                self, content: str, file_path: str
            ) -> list[SecurityFinding]:
                return []

        validator = SimpleValidator()
        result = validator.validate(tmp_path / "nonexistent.ts")

        # File doesn't exist, so nothing to scan
        assert result.files_scanned == 0
        assert result.error is None

    def test_validator_repr(self) -> None:
        """Test validator string representation."""

        class TestValidator(BaseValidator):
            @property
            def id(self) -> str:
                return "test-repr"

            @property
            def name(self) -> str:
                return "Test"

            @property
            def description(self) -> str:
                return "Test"

            def validate_content(
                self, content: str, file_path: str
            ) -> list[SecurityFinding]:
                return []

        validator = TestValidator()
        assert repr(validator) == "TestValidator(id='test-repr')"


class TestValidatorRegistry:
    """Tests for ValidatorRegistry."""

    def test_register_and_get(self) -> None:
        """Test registering and retrieving validators."""
        registry = ValidatorRegistry()

        class DummyValidator:
            @property
            def id(self) -> str:
                return "dummy"

            @property
            def name(self) -> str:
                return "Dummy"

            @property
            def description(self) -> str:
                return "Dummy validator"

            def validate(self, path: Path) -> ValidatorResult:
                return ValidatorResult(validator_id=self.id, validator_name=self.name)

            def validate_content(
                self, content: str, file_path: str
            ) -> list[SecurityFinding]:
                return []

        validator = DummyValidator()
        registry.register(validator)

        assert registry.count == 1
        assert registry.get("dummy") is not None
        assert registry.get("dummy") is validator
        assert "dummy" in registry.ids
        assert registry.has("dummy") is True
        assert registry.has("nonexistent") is False

    def test_unregister(self) -> None:
        """Test unregistering validators."""
        registry = ValidatorRegistry()

        class DummyValidator:
            @property
            def id(self) -> str:
                return "to-remove"

            @property
            def name(self) -> str:
                return "Remove Me"

            @property
            def description(self) -> str:
                return "..."

            def validate(self, path: Path) -> ValidatorResult:
                return ValidatorResult(validator_id=self.id, validator_name=self.name)

            def validate_content(
                self, content: str, file_path: str
            ) -> list[SecurityFinding]:
                return []

        registry.register(DummyValidator())
        assert registry.count == 1

        result = registry.unregister("to-remove")
        assert result is True
        assert registry.count == 0

        # Try to unregister again
        result = registry.unregister("to-remove")
        assert result is False

    def test_get_all(self) -> None:
        """Test getting all validators."""
        registry = ValidatorRegistry()

        class Validator1:
            @property
            def id(self) -> str:
                return "v1"

            @property
            def name(self) -> str:
                return "V1"

            @property
            def description(self) -> str:
                return "..."

            def validate(self, path: Path) -> ValidatorResult:
                return ValidatorResult(validator_id=self.id, validator_name=self.name)

            def validate_content(
                self, content: str, file_path: str
            ) -> list[SecurityFinding]:
                return []

        class Validator2:
            @property
            def id(self) -> str:
                return "v2"

            @property
            def name(self) -> str:
                return "V2"

            @property
            def description(self) -> str:
                return "..."

            def validate(self, path: Path) -> ValidatorResult:
                return ValidatorResult(validator_id=self.id, validator_name=self.name)

            def validate_content(
                self, content: str, file_path: str
            ) -> list[SecurityFinding]:
                return []

        registry.register(Validator1())
        registry.register(Validator2())

        all_validators = registry.get_all()
        assert len(all_validators) == 2

    def test_get_by_category(self) -> None:
        """Test getting validators by category."""
        registry = ValidatorRegistry()

        class XSSValidator1:
            @property
            def id(self) -> str:
                return "sec-xss-dom"

            @property
            def name(self) -> str:
                return "XSS 1"

            @property
            def description(self) -> str:
                return "..."

            def validate(self, path: Path) -> ValidatorResult:
                return ValidatorResult(validator_id=self.id, validator_name=self.name)

            def validate_content(
                self, content: str, file_path: str
            ) -> list[SecurityFinding]:
                return []

        class XSSValidator2:
            @property
            def id(self) -> str:
                return "sec-xss-eval"

            @property
            def name(self) -> str:
                return "XSS 2"

            @property
            def description(self) -> str:
                return "..."

            def validate(self, path: Path) -> ValidatorResult:
                return ValidatorResult(validator_id=self.id, validator_name=self.name)

            def validate_content(
                self, content: str, file_path: str
            ) -> list[SecurityFinding]:
                return []

        class InjectionValidator:
            @property
            def id(self) -> str:
                return "sec-injection-sql"

            @property
            def name(self) -> str:
                return "Injection"

            @property
            def description(self) -> str:
                return "..."

            def validate(self, path: Path) -> ValidatorResult:
                return ValidatorResult(validator_id=self.id, validator_name=self.name)

            def validate_content(
                self, content: str, file_path: str
            ) -> list[SecurityFinding]:
                return []

        registry.register(XSSValidator1())
        registry.register(XSSValidator2())
        registry.register(InjectionValidator())

        xss_validators = registry.get_by_category("sec-xss")
        assert len(xss_validators) == 2

        injection_validators = registry.get_by_category("sec-injection")
        assert len(injection_validators) == 1

    def test_clear(self) -> None:
        """Test clearing the registry."""
        registry = ValidatorRegistry()

        class DummyValidator:
            @property
            def id(self) -> str:
                return "dummy"

            @property
            def name(self) -> str:
                return "Dummy"

            @property
            def description(self) -> str:
                return "..."

            def validate(self, path: Path) -> ValidatorResult:
                return ValidatorResult(validator_id=self.id, validator_name=self.name)

            def validate_content(
                self, content: str, file_path: str
            ) -> list[SecurityFinding]:
                return []

        registry.register(DummyValidator())
        assert registry.count == 1

        registry.clear()
        assert registry.count == 0

    def test_categories(self) -> None:
        """Test getting unique categories."""
        registry = ValidatorRegistry()

        class V1:
            @property
            def id(self) -> str:
                return "sec-xss-a"

            @property
            def name(self) -> str:
                return "V1"

            @property
            def description(self) -> str:
                return "..."

            def validate(self, path: Path) -> ValidatorResult:
                return ValidatorResult(validator_id=self.id, validator_name=self.name)

            def validate_content(
                self, content: str, file_path: str
            ) -> list[SecurityFinding]:
                return []

        class V2:
            @property
            def id(self) -> str:
                return "sec-xss-b"

            @property
            def name(self) -> str:
                return "V2"

            @property
            def description(self) -> str:
                return "..."

            def validate(self, path: Path) -> ValidatorResult:
                return ValidatorResult(validator_id=self.id, validator_name=self.name)

            def validate_content(
                self, content: str, file_path: str
            ) -> list[SecurityFinding]:
                return []

        class V3:
            @property
            def id(self) -> str:
                return "sec-injection-sql"

            @property
            def name(self) -> str:
                return "V3"

            @property
            def description(self) -> str:
                return "..."

            def validate(self, path: Path) -> ValidatorResult:
                return ValidatorResult(validator_id=self.id, validator_name=self.name)

            def validate_content(
                self, content: str, file_path: str
            ) -> list[SecurityFinding]:
                return []

        registry.register(V1())
        registry.register(V2())
        registry.register(V3())

        categories = registry.categories
        assert len(categories) == 2
        assert "sec-xss" in categories
        assert "sec-injection" in categories

    def test_dunder_methods(self) -> None:
        """Test __len__, __contains__, __repr__."""
        registry = ValidatorRegistry()

        class DummyValidator:
            @property
            def id(self) -> str:
                return "dummy"

            @property
            def name(self) -> str:
                return "Dummy"

            @property
            def description(self) -> str:
                return "..."

            def validate(self, path: Path) -> ValidatorResult:
                return ValidatorResult(validator_id=self.id, validator_name=self.name)

            def validate_content(
                self, content: str, file_path: str
            ) -> list[SecurityFinding]:
                return []

        registry.register(DummyValidator())

        assert len(registry) == 1
        assert "dummy" in registry
        assert "nonexistent" not in registry
        assert repr(registry) == "ValidatorRegistry(count=1)"

    def test_iteration(self) -> None:
        """Test iterating over registry."""
        registry = ValidatorRegistry()

        class V1:
            @property
            def id(self) -> str:
                return "v1"

            @property
            def name(self) -> str:
                return "V1"

            @property
            def description(self) -> str:
                return "..."

            def validate(self, path: Path) -> ValidatorResult:
                return ValidatorResult(validator_id=self.id, validator_name=self.name)

            def validate_content(
                self, content: str, file_path: str
            ) -> list[SecurityFinding]:
                return []

        class V2:
            @property
            def id(self) -> str:
                return "v2"

            @property
            def name(self) -> str:
                return "V2"

            @property
            def description(self) -> str:
                return "..."

            def validate(self, path: Path) -> ValidatorResult:
                return ValidatorResult(validator_id=self.id, validator_name=self.name)

            def validate_content(
                self, content: str, file_path: str
            ) -> list[SecurityFinding]:
                return []

        registry.register(V1())
        registry.register(V2())

        ids = [v.id for v in registry]
        assert len(ids) == 2
        assert "v1" in ids
        assert "v2" in ids


class TestSecurityValidatorProtocol:
    """Tests for SecurityValidator protocol."""

    def test_protocol_check(self) -> None:
        """Test that classes implementing the protocol are recognized."""

        class ImplementsProtocol:
            @property
            def id(self) -> str:
                return "impl"

            @property
            def name(self) -> str:
                return "Impl"

            @property
            def description(self) -> str:
                return "..."

            def validate(self, path: Path) -> ValidatorResult:
                return ValidatorResult(validator_id=self.id, validator_name=self.name)

            def validate_content(
                self, content: str, file_path: str
            ) -> list[SecurityFinding]:
                return []

        impl = ImplementsProtocol()
        assert isinstance(impl, SecurityValidator)

    def test_base_validator_implements_protocol(self) -> None:
        """Test that BaseValidator subclasses implement protocol."""

        class ConcreteValidator(BaseValidator):
            @property
            def id(self) -> str:
                return "concrete"

            @property
            def name(self) -> str:
                return "Concrete"

            @property
            def description(self) -> str:
                return "..."

            def validate_content(
                self, content: str, file_path: str
            ) -> list[SecurityFinding]:
                return []

        validator = ConcreteValidator()
        assert isinstance(validator, SecurityValidator)
