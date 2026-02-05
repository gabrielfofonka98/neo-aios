"""Security validator models.

This module provides the core data models for the security validation framework,
including severity levels, finding categories, security findings, and reports.

Example:
    >>> from aios.security.models import SecurityFinding, Severity, FindingCategory
    >>> finding = SecurityFinding(
    ...     id="xss-001",
    ...     validator_id="sec-xss",
    ...     severity=Severity.HIGH,
    ...     category=FindingCategory.XSS,
    ...     title="XSS vulnerability detected",
    ...     description="User input passed directly to unsafe render method",
    ...     location=CodeLocation(file_path="app.tsx", line_start=42, line_end=42),
    ...     recommendation="Sanitize input before rendering"
    ... )
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel
from pydantic import Field


class Severity(Enum):
    """Finding severity levels.

    Ordered from most to least severe:
    - CRITICAL: Immediate exploitation risk, must fix before deploy
    - HIGH: Significant security risk, blocks PR merge
    - MEDIUM: Security concern, should fix soon
    - LOW: Minor security issue, can be scheduled
    - INFO: Informational, best practice suggestion
    """

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class FindingCategory(Enum):
    """Categories of security findings.

    Maps to common vulnerability categories from OWASP and CWE.
    """

    XSS = "xss"
    INJECTION = "injection"
    AUTH = "authentication"
    CRYPTO = "cryptography"
    CONFIG = "configuration"
    DATA_EXPOSURE = "data_exposure"
    INPUT_VALIDATION = "input_validation"
    ACCESS_CONTROL = "access_control"


class CodeLocation(BaseModel):
    """Location of finding in code.

    Provides precise source code location for a finding,
    including optional column positions and code snippet.

    Attributes:
        file_path: Relative or absolute path to the file.
        line_start: Starting line number (1-indexed).
        line_end: Ending line number (1-indexed).
        column_start: Optional starting column (1-indexed).
        column_end: Optional ending column (1-indexed).
        snippet: Optional code snippet showing the issue.
    """

    file_path: str
    line_start: int
    line_end: int
    column_start: int | None = None
    column_end: int | None = None
    snippet: str | None = None


class SecurityFinding(BaseModel):
    """A single security finding.

    Represents one security issue found during validation,
    with complete information for triage and remediation.

    Attributes:
        id: Unique finding identifier (e.g., "xss-001").
        validator_id: ID of validator that found this.
        severity: How severe the finding is.
        category: What type of vulnerability.
        title: Short, descriptive title.
        description: Detailed explanation of the issue.
        location: Where in the code the issue is.
        recommendation: How to fix the issue.
        auto_fixable: Whether this can be auto-fixed.
        fix_snippet: Optional suggested fix code.
        confidence: Confidence score (0.0-1.0).
        cwe_id: Optional CWE identifier (e.g., "CWE-79").
        owasp_id: Optional OWASP identifier (e.g., "A03:2021").
        found_at: When this finding was discovered.
    """

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
    fix_snippet: str | None = None

    # Metadata
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    cwe_id: str | None = None
    owasp_id: str | None = None

    # Timestamp
    found_at: datetime = Field(default_factory=datetime.now)


class ValidatorResult(BaseModel):
    """Result from a single validator run.

    Contains all findings from one validator, along with metadata
    about the scan execution.

    Attributes:
        validator_id: ID of the validator that ran.
        validator_name: Human-readable validator name.
        findings: List of security findings.
        files_scanned: Number of files processed.
        scan_duration_ms: How long the scan took in milliseconds.
        error: Error message if scan failed.
    """

    validator_id: str
    validator_name: str

    findings: list[SecurityFinding] = Field(default_factory=list)

    files_scanned: int = 0
    scan_duration_ms: int = 0

    error: str | None = None

    @property
    def has_findings(self) -> bool:
        """Check if there are any findings."""
        return len(self.findings) > 0

    @property
    def critical_count(self) -> int:
        """Count of CRITICAL severity findings."""
        return sum(1 for f in self.findings if f.severity == Severity.CRITICAL)

    @property
    def high_count(self) -> int:
        """Count of HIGH severity findings."""
        return sum(1 for f in self.findings if f.severity == Severity.HIGH)

    @property
    def medium_count(self) -> int:
        """Count of MEDIUM severity findings."""
        return sum(1 for f in self.findings if f.severity == Severity.MEDIUM)

    @property
    def low_count(self) -> int:
        """Count of LOW severity findings."""
        return sum(1 for f in self.findings if f.severity == Severity.LOW)

    @property
    def info_count(self) -> int:
        """Count of INFO severity findings."""
        return sum(1 for f in self.findings if f.severity == Severity.INFO)


class SecurityReport(BaseModel):
    """Complete security scan report.

    Aggregates results from multiple validators into a single report,
    providing summary statistics and blocking checks.

    Attributes:
        scan_id: Unique identifier for this scan.
        started_at: When the scan started.
        completed_at: When the scan finished (None if still running).
        results: List of results from each validator.
        target_path: Path that was scanned.
    """

    scan_id: str
    started_at: datetime
    completed_at: datetime | None = None

    results: list[ValidatorResult] = Field(default_factory=list)

    target_path: str

    @property
    def total_findings(self) -> int:
        """Total number of findings across all validators."""
        return sum(len(r.findings) for r in self.results)

    @property
    def critical_findings(self) -> int:
        """Total CRITICAL findings."""
        return sum(r.critical_count for r in self.results)

    @property
    def high_findings(self) -> int:
        """Total HIGH findings."""
        return sum(r.high_count for r in self.results)

    @property
    def medium_findings(self) -> int:
        """Total MEDIUM findings."""
        return sum(r.medium_count for r in self.results)

    @property
    def low_findings(self) -> int:
        """Total LOW findings."""
        return sum(r.low_count for r in self.results)

    @property
    def info_findings(self) -> int:
        """Total INFO findings."""
        return sum(r.info_count for r in self.results)

    @property
    def has_blockers(self) -> bool:
        """Check if there are any CRITICAL or HIGH findings.

        These findings should block PR merge and deployment.
        """
        return self.critical_findings > 0 or self.high_findings > 0

    @property
    def files_scanned(self) -> int:
        """Total files scanned across all validators."""
        return sum(r.files_scanned for r in self.results)

    @property
    def total_duration_ms(self) -> int:
        """Total scan duration in milliseconds."""
        return sum(r.scan_duration_ms for r in self.results)

    @property
    def has_errors(self) -> bool:
        """Check if any validator had errors."""
        return any(r.error is not None for r in self.results)

    def add_result(self, result: ValidatorResult) -> None:
        """Add a validator result to the report.

        Args:
            result: The validator result to add.
        """
        self.results.append(result)

    def get_findings_by_severity(self, severity: Severity) -> list[SecurityFinding]:
        """Get all findings of a specific severity.

        Args:
            severity: The severity level to filter by.

        Returns:
            List of findings matching the severity.
        """
        findings: list[SecurityFinding] = []
        for result in self.results:
            findings.extend(f for f in result.findings if f.severity == severity)
        return findings

    def get_findings_by_category(
        self, category: FindingCategory
    ) -> list[SecurityFinding]:
        """Get all findings of a specific category.

        Args:
            category: The category to filter by.

        Returns:
            List of findings matching the category.
        """
        findings: list[SecurityFinding] = []
        for result in self.results:
            findings.extend(f for f in result.findings if f.category == category)
        return findings
