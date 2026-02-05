# Story 2.1: Validator Framework

**Status:** [ ] Pending
**Executor:** Ralph/Dex
**Complexidade:** Alta
**Dependência:** Epic 1

---

## Objetivo

Criar o framework base para validators de segurança com suporte a AST e regex.

## Tasks

### Task 1: Criar Validator Base Models

**Arquivo:** `src/aios/security/models.py`
**Tipo:** create

**Código esperado:**
```python
"""Security validator models."""

from enum import Enum
from typing import Optional
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field


class Severity(Enum):
    """Finding severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class FindingCategory(Enum):
    """Categories of security findings."""
    XSS = "xss"
    INJECTION = "injection"
    AUTH = "authentication"
    CRYPTO = "cryptography"
    CONFIG = "configuration"
    DATA_EXPOSURE = "data_exposure"
    INPUT_VALIDATION = "input_validation"
    ACCESS_CONTROL = "access_control"


class CodeLocation(BaseModel):
    """Location of finding in code."""
    file_path: str
    line_start: int
    line_end: int
    column_start: Optional[int] = None
    column_end: Optional[int] = None
    snippet: Optional[str] = None


class SecurityFinding(BaseModel):
    """A single security finding."""

    # Identification
    id: str
    validator_id: str

    # Classification
    severity: Severity
    category: FindingCategory

    # Description
    title: str
    description: str

    # Location
    location: CodeLocation

    # Remediation
    recommendation: str
    auto_fixable: bool = False
    fix_snippet: Optional[str] = None

    # Metadata
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    cwe_id: Optional[str] = None
    owasp_id: Optional[str] = None

    # Timestamp
    found_at: datetime = Field(default_factory=datetime.now)


class ValidatorResult(BaseModel):
    """Result from a single validator run."""

    validator_id: str
    validator_name: str

    findings: list[SecurityFinding] = Field(default_factory=list)

    files_scanned: int = 0
    scan_duration_ms: int = 0

    error: Optional[str] = None

    @property
    def has_findings(self) -> bool:
        return len(self.findings) > 0

    @property
    def critical_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.CRITICAL)

    @property
    def high_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.HIGH)


class SecurityReport(BaseModel):
    """Complete security scan report."""

    scan_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None

    results: list[ValidatorResult] = Field(default_factory=list)

    target_path: str

    @property
    def total_findings(self) -> int:
        return sum(len(r.findings) for r in self.results)

    @property
    def critical_findings(self) -> int:
        return sum(r.critical_count for r in self.results)

    @property
    def high_findings(self) -> int:
        return sum(r.high_count for r in self.results)

    @property
    def has_blockers(self) -> bool:
        """Check if there are any CRITICAL or HIGH findings."""
        return self.critical_findings > 0 or self.high_findings > 0

    def add_result(self, result: ValidatorResult) -> None:
        self.results.append(result)
```

---

### Task 2: Criar Validator Protocol

**Arquivo:** `src/aios/security/validators/base.py`
**Tipo:** create

**Código esperado:**
```python
"""Base validator protocol and abstract class."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Protocol, Optional, runtime_checkable

from aios.security.models import ValidatorResult, SecurityFinding


@runtime_checkable
class SecurityValidator(Protocol):
    """Protocol for security validators."""

    @property
    def id(self) -> str:
        """Unique validator identifier."""
        ...

    @property
    def name(self) -> str:
        """Human-readable name."""
        ...

    @property
    def description(self) -> str:
        """What this validator checks for."""
        ...

    def validate(self, path: Path) -> ValidatorResult:
        """Run validation on path (file or directory)."""
        ...

    def validate_content(self, content: str, file_path: str) -> list[SecurityFinding]:
        """Validate content directly."""
        ...


class BaseValidator(ABC):
    """Abstract base class for validators."""

    @property
    @abstractmethod
    def id(self) -> str:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @property
    def file_extensions(self) -> list[str]:
        """File extensions this validator applies to."""
        return [".ts", ".tsx", ".js", ".jsx"]

    def validate(self, path: Path) -> ValidatorResult:
        """Run validation on path."""
        import time
        start_time = time.time()

        findings: list[SecurityFinding] = []
        files_scanned = 0

        try:
            if path.is_file():
                if self._should_scan_file(path):
                    content = path.read_text(encoding="utf-8")
                    findings.extend(self.validate_content(content, str(path)))
                    files_scanned = 1
            elif path.is_dir():
                for file_path in self._get_files(path):
                    content = file_path.read_text(encoding="utf-8")
                    findings.extend(self.validate_content(content, str(file_path)))
                    files_scanned += 1

        except Exception as e:
            return ValidatorResult(
                validator_id=self.id,
                validator_name=self.name,
                error=str(e),
                files_scanned=files_scanned,
                scan_duration_ms=int((time.time() - start_time) * 1000)
            )

        return ValidatorResult(
            validator_id=self.id,
            validator_name=self.name,
            findings=findings,
            files_scanned=files_scanned,
            scan_duration_ms=int((time.time() - start_time) * 1000)
        )

    @abstractmethod
    def validate_content(self, content: str, file_path: str) -> list[SecurityFinding]:
        """Validate content - must be implemented by subclasses."""
        pass

    def _should_scan_file(self, path: Path) -> bool:
        """Check if file should be scanned."""
        return path.suffix in self.file_extensions

    def _get_files(self, directory: Path) -> list[Path]:
        """Get all scannable files in directory."""
        files = []
        for ext in self.file_extensions:
            files.extend(directory.rglob(f"*{ext}"))
        return files
```

---

### Task 3: Criar Validator Registry

**Arquivo:** `src/aios/security/validators/registry.py`
**Tipo:** create

**Código esperado:**
```python
"""Registry for security validators."""

from typing import Optional

from aios.security.validators.base import SecurityValidator


class ValidatorRegistry:
    """Central registry for all security validators."""

    def __init__(self) -> None:
        self._validators: dict[str, SecurityValidator] = {}

    def register(self, validator: SecurityValidator) -> None:
        """Register a validator."""
        self._validators[validator.id] = validator

    def unregister(self, validator_id: str) -> bool:
        """Unregister a validator."""
        if validator_id in self._validators:
            del self._validators[validator_id]
            return True
        return False

    def get(self, validator_id: str) -> Optional[SecurityValidator]:
        """Get validator by ID."""
        return self._validators.get(validator_id)

    def get_all(self) -> list[SecurityValidator]:
        """Get all registered validators."""
        return list(self._validators.values())

    def get_by_category(self, category: str) -> list[SecurityValidator]:
        """Get validators by category prefix (e.g., 'sec-xss')."""
        return [
            v for v in self._validators.values()
            if v.id.startswith(category)
        ]

    @property
    def count(self) -> int:
        """Number of registered validators."""
        return len(self._validators)

    @property
    def ids(self) -> list[str]:
        """List of all validator IDs."""
        return list(self._validators.keys())


# Global registry
validator_registry = ValidatorRegistry()
```

---

### Task 4: Criar testes

**Arquivo:** `tests/test_security/test_validator_framework.py`
**Tipo:** create

**Código esperado:**
```python
"""Tests for validator framework."""

import pytest
from pathlib import Path

from aios.security.models import (
    Severity,
    FindingCategory,
    CodeLocation,
    SecurityFinding,
    ValidatorResult,
    SecurityReport,
)
from aios.security.validators.base import BaseValidator
from aios.security.validators.registry import ValidatorRegistry


class TestSecurityModels:
    def test_security_finding(self) -> None:
        finding = SecurityFinding(
            id="test-001",
            validator_id="test-validator",
            severity=Severity.HIGH,
            category=FindingCategory.XSS,
            title="Test Finding",
            description="Test description",
            location=CodeLocation(
                file_path="test.ts",
                line_start=10,
                line_end=10
            ),
            recommendation="Fix this"
        )

        assert finding.severity == Severity.HIGH
        assert finding.auto_fixable is False

    def test_validator_result(self) -> None:
        result = ValidatorResult(
            validator_id="test",
            validator_name="Test Validator",
            findings=[
                SecurityFinding(
                    id="1",
                    validator_id="test",
                    severity=Severity.CRITICAL,
                    category=FindingCategory.XSS,
                    title="Critical",
                    description="...",
                    location=CodeLocation(file_path="a.ts", line_start=1, line_end=1),
                    recommendation="..."
                ),
                SecurityFinding(
                    id="2",
                    validator_id="test",
                    severity=Severity.HIGH,
                    category=FindingCategory.XSS,
                    title="High",
                    description="...",
                    location=CodeLocation(file_path="b.ts", line_start=1, line_end=1),
                    recommendation="..."
                ),
            ]
        )

        assert result.has_findings is True
        assert result.critical_count == 1
        assert result.high_count == 1

    def test_security_report(self) -> None:
        from datetime import datetime

        report = SecurityReport(
            scan_id="scan-001",
            started_at=datetime.now(),
            target_path="/test"
        )

        result = ValidatorResult(
            validator_id="test",
            validator_name="Test",
            findings=[
                SecurityFinding(
                    id="1",
                    validator_id="test",
                    severity=Severity.CRITICAL,
                    category=FindingCategory.INJECTION,
                    title="SQL Injection",
                    description="...",
                    location=CodeLocation(file_path="a.ts", line_start=1, line_end=1),
                    recommendation="..."
                )
            ]
        )

        report.add_result(result)

        assert report.total_findings == 1
        assert report.critical_findings == 1
        assert report.has_blockers is True


class TestBaseValidator:
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
                findings = []
                if "DANGEROUS" in content:
                    findings.append(SecurityFinding(
                        id=f"test-{file_path}",
                        validator_id=self.id,
                        severity=Severity.HIGH,
                        category=FindingCategory.CONFIG,
                        title="Dangerous content found",
                        description="Content contains DANGEROUS",
                        location=CodeLocation(
                            file_path=file_path,
                            line_start=1,
                            line_end=1
                        ),
                        recommendation="Remove DANGEROUS"
                    ))
                return findings

        # Create test file
        test_file = tmp_path / "test.ts"
        test_file.write_text("const x = 'DANGEROUS';")

        validator = TestValidator()
        result = validator.validate(test_file)

        assert result.has_findings is True
        assert result.findings[0].severity == Severity.HIGH


class TestValidatorRegistry:
    def test_register_and_get(self) -> None:
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
                return ValidatorResult(
                    validator_id=self.id,
                    validator_name=self.name
                )

            def validate_content(
                self, content: str, file_path: str
            ) -> list[SecurityFinding]:
                return []

        validator = DummyValidator()
        registry.register(validator)

        assert registry.count == 1
        assert registry.get("dummy") is not None
        assert "dummy" in registry.ids

    def test_unregister(self) -> None:
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
                return ValidatorResult(
                    validator_id=self.id,
                    validator_name=self.name
                )

            def validate_content(
                self, content: str, file_path: str
            ) -> list[SecurityFinding]:
                return []

        registry.register(DummyValidator())
        assert registry.count == 1

        result = registry.unregister("to-remove")
        assert result is True
        assert registry.count == 0
```

---

## Validação Final

- [ ] Models completos
- [ ] BaseValidator funcionando
- [ ] Registry funcionando
- [ ] Testes com 90%+ coverage
- [ ] Type hints completos

## Notas para Ralph

- Usar Protocol para validators extensíveis
- Severidade: CRITICAL, HIGH, MEDIUM, LOW, INFO
- Sempre incluir CWE/OWASP IDs quando relevante
- Confidence score para reduzir false positives
