"""PR Automation Layer for quality gates.

This module provides the PRAutomationGate class that integrates security
scanning into the PR review workflow. It runs security audits, generates
PR comments, and determines merge blocking status.

Example:
    >>> from pathlib import Path
    >>> from aios.quality.pr_automation import PRAutomationGate
    >>> gate = PRAutomationGate()
    >>> result = gate.run_full_audit(Path("./src"))
    >>> if result.should_block:
    ...     print("PR blocked due to security findings")
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from aios.security.models import SecurityFinding
from aios.security.models import SecurityReport
from aios.security.models import Severity
from aios.security.orchestrator import ProgressCallback
from aios.security.orchestrator import ScanConfig
from aios.security.orchestrator import SecurityOrchestrator
from aios.security.validators.registry import validator_registry

if TYPE_CHECKING:
    from pathlib import Path

    from aios.security.validators.registry import ValidatorRegistry


class PRStatus(Enum):
    """Status of PR review.

    Attributes:
        APPROVED: PR can be merged, no blocking findings.
        CHANGES_REQUESTED: PR has issues that must be fixed before merge.
        PENDING: Review is still in progress.
        ERROR: Review failed due to an error.
    """

    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"
    PENDING = "pending"
    ERROR = "error"


@dataclass
class PRReviewResult:
    """Result of a PR review.

    Contains the security report, generated comment, and merge decision.

    Attributes:
        status: The review status (approved, changes_requested, etc.).
        security_report: The full security scan report.
        pr_comment: Markdown comment for the PR.
        should_block: Whether the PR should be blocked from merging.
        blocking_findings: List of findings that caused the block.
        reviewed_at: When the review was completed.
        error_message: Error message if review failed.
    """

    status: PRStatus
    security_report: SecurityReport | None
    pr_comment: str
    should_block: bool
    blocking_findings: list[SecurityFinding] = field(default_factory=list)
    reviewed_at: datetime = field(default_factory=datetime.now)
    error_message: str | None = None


# Severity order for sorting (lower = higher priority)
_SEVERITY_ORDER: dict[Severity, int] = {
    Severity.CRITICAL: 0,
    Severity.HIGH: 1,
    Severity.MEDIUM: 2,
    Severity.LOW: 3,
    Severity.INFO: 4,
}


class PRAutomationGate:
    """Automated PR review gate using security scanning.

    The PRAutomationGate integrates security scanning into the PR review
    workflow. It runs all security validators, generates a markdown report
    for PR comments, and determines whether the PR should be blocked.

    Attributes:
        orchestrator: The SecurityOrchestrator instance to use.

    Example:
        >>> gate = PRAutomationGate()
        >>> result = gate.run_full_audit(Path("./src"))
        >>> print(result.pr_comment)
    """

    def __init__(
        self,
        registry: ValidatorRegistry | None = None,
        config: ScanConfig | None = None,
    ) -> None:
        """Initialize the PR automation gate.

        Args:
            registry: Optional validator registry. Uses global registry if not provided.
            config: Optional scan configuration.
        """
        self._registry = registry or validator_registry
        self._config = config or ScanConfig()
        self._orchestrator = SecurityOrchestrator(
            registry=self._registry,
            config=self._config,
        )

    @property
    def orchestrator(self) -> SecurityOrchestrator:
        """Get the security orchestrator."""
        return self._orchestrator

    def run_full_audit(
        self,
        path: Path,
        progress_callback: ProgressCallback | None = None,
    ) -> PRReviewResult:
        """Run a full security audit and generate PR review result.

        Executes all registered security validators against the specified
        path and generates a complete PR review result with comment.

        Args:
            path: Path to scan (file or directory).
            progress_callback: Optional callback for progress updates.

        Returns:
            PRReviewResult with status, report, and blocking decision.

        Example:
            >>> result = gate.run_full_audit(Path("./src"))
            >>> if result.should_block:
            ...     print("Merge blocked!")
        """
        try:
            report = self._orchestrator.full_audit(
                path=path,
                progress_callback=progress_callback,
            )

            should_block = self.should_block_merge(report)
            blocking_findings = self._get_blocking_findings(report)
            comment = self.generate_pr_comment(report)

            status = PRStatus.CHANGES_REQUESTED if should_block else PRStatus.APPROVED

            return PRReviewResult(
                status=status,
                security_report=report,
                pr_comment=comment,
                should_block=should_block,
                blocking_findings=blocking_findings,
            )

        except Exception as e:
            error_comment = self._generate_error_comment(str(e))
            return PRReviewResult(
                status=PRStatus.ERROR,
                security_report=None,
                pr_comment=error_comment,
                should_block=True,  # Block on error for safety
                error_message=str(e),
            )

    def review_pr(
        self,
        pr_number: int,
        repo: str,
        local_path: Path,
        progress_callback: ProgressCallback | None = None,
    ) -> PRReviewResult:
        """Review a specific PR by scanning its local checkout.

        This method is designed for CI/CD integration where the PR has
        been checked out locally.

        Args:
            pr_number: The PR number for reference in the comment.
            repo: The repository name (owner/repo format).
            local_path: Local path where PR is checked out.
            progress_callback: Optional callback for progress updates.

        Returns:
            PRReviewResult with PR-specific metadata.

        Example:
            >>> result = gate.review_pr(123, "owner/repo", Path("./checkout"))
        """
        result = self.run_full_audit(
            path=local_path,
            progress_callback=progress_callback,
        )

        # Enhance comment with PR metadata
        if result.security_report is not None:
            result = PRReviewResult(
                status=result.status,
                security_report=result.security_report,
                pr_comment=self._generate_pr_comment_with_metadata(
                    report=result.security_report,
                    pr_number=pr_number,
                    repo=repo,
                ),
                should_block=result.should_block,
                blocking_findings=result.blocking_findings,
                error_message=result.error_message,
            )

        return result

    def should_block_merge(self, report: SecurityReport) -> bool:
        """Determine if the PR should be blocked from merging.

        A PR is blocked if there are any CRITICAL or HIGH severity findings.

        Args:
            report: The security scan report.

        Returns:
            True if the PR should be blocked.
        """
        return report.has_blockers

    def generate_pr_comment(self, report: SecurityReport) -> str:
        """Generate a markdown comment for a PR based on the security report.

        Creates a well-formatted markdown comment suitable for posting
        to a GitHub PR review.

        Args:
            report: The security scan report.

        Returns:
            Markdown formatted string for the PR comment.
        """
        lines: list[str] = []

        # Build comment sections
        lines.extend(self._build_header_section(report))
        lines.extend(self._build_summary_section(report))
        lines.extend(self._build_severity_table(report))

        blocking = self._get_blocking_findings(report)
        lines.extend(self._build_blocking_findings_section(blocking))
        lines.extend(self._build_other_findings_section(report, blocking))
        lines.extend(self._build_errors_section(report))
        lines.extend(self._build_footer_section(report))

        return "\n".join(lines)

    def _build_header_section(self, report: SecurityReport) -> list[str]:
        """Build the header section of the PR comment."""
        lines: list[str] = []
        if report.has_blockers:
            lines.append("## :x: Security Review - Changes Requested")
            lines.append("")
            lines.append(
                "> **This PR cannot be merged** due to CRITICAL or HIGH severity findings."
            )
        elif report.total_findings > 0:
            lines.append("## :white_check_mark: Security Review - Approved")
            lines.append("")
            lines.append(
                "> This PR has some findings but none are blocking. "
                "Consider addressing them before merge."
            )
        else:
            lines.append("## :white_check_mark: Security Review - Approved")
            lines.append("")
            lines.append("> No security issues found.")
        lines.append("")
        return lines

    def _build_summary_section(self, report: SecurityReport) -> list[str]:
        """Build the summary section of the PR comment."""
        return [
            "### Summary",
            "",
            f"- **Files Scanned:** {report.files_scanned}",
            f"- **Validators Run:** {len(report.results)}",
            f"- **Total Findings:** {report.total_findings}",
            f"- **Scan Duration:** {report.total_duration_ms}ms",
            "",
        ]

    def _build_severity_table(self, report: SecurityReport) -> list[str]:
        """Build the severity breakdown table."""
        if report.total_findings == 0:
            return []

        lines = ["### Findings by Severity", "", "| Severity | Count |", "|----------|-------|"]
        severity_data = [
            (report.critical_findings, ":red_circle: CRITICAL"),
            (report.high_findings, ":orange_circle: HIGH"),
            (report.medium_findings, ":yellow_circle: MEDIUM"),
            (report.low_findings, ":large_blue_circle: LOW"),
            (report.info_findings, ":white_circle: INFO"),
        ]
        for count, label in severity_data:
            if count > 0:
                lines.append(f"| {label} | {count} |")
        lines.append("")
        return lines

    def _build_blocking_findings_section(
        self, blocking: list[SecurityFinding]
    ) -> list[str]:
        """Build the blocking findings detail section."""
        if not blocking:
            return []

        lines = [
            "### Blocking Findings",
            "",
            "The following findings must be resolved before this PR can be merged:",
            "",
        ]

        for finding in blocking[:10]:
            lines.extend(self._format_finding_detail(finding))

        if len(blocking) > 10:
            lines.append(f"*... and {len(blocking) - 10} more blocking findings.*")
            lines.append("")

        return lines

    def _format_finding_detail(self, finding: SecurityFinding) -> list[str]:
        """Format a single finding for detailed display."""
        severity_emoji = (
            ":red_circle:" if finding.severity == Severity.CRITICAL else ":orange_circle:"
        )
        lines = [
            f"#### {severity_emoji} {finding.title} ({finding.severity.value.upper()})",
            "",
            f"**File:** `{finding.location.file_path}`",
            f"**Line:** {finding.location.line_start}-{finding.location.line_end}",
            "",
            finding.description,
            "",
            f"**Recommendation:** {finding.recommendation}",
        ]
        if finding.cwe_id:
            lines.append(f"**CWE:** {finding.cwe_id}")
        lines.append("")
        return lines

    def _build_other_findings_section(
        self, report: SecurityReport, blocking: list[SecurityFinding]
    ) -> list[str]:
        """Build the non-blocking findings summary section."""
        non_blocking_count = report.total_findings - len(blocking)
        if non_blocking_count == 0:
            return []

        lines = [
            "### Other Findings",
            "",
            f"There are {non_blocking_count} additional findings (MEDIUM/LOW/INFO) "
            "that should be reviewed but won't block the merge.",
            "",
        ]

        non_blocking = self._get_non_blocking_findings(report)
        for finding in non_blocking[:5]:
            severity_emoji = self._get_severity_emoji(finding.severity)
            lines.append(
                f"- {severity_emoji} **{finding.title}** - "
                f"`{finding.location.file_path}:{finding.location.line_start}`"
            )

        if len(non_blocking) > 5:
            lines.append(f"- *... and {len(non_blocking) - 5} more.*")
        lines.append("")
        return lines

    def _build_errors_section(self, report: SecurityReport) -> list[str]:
        """Build the scan errors section."""
        errors = [r for r in report.results if r.error is not None]
        if not errors:
            return []

        lines = [
            "### :warning: Scan Errors",
            "",
            "Some validators encountered errors during scanning:",
            "",
        ]
        for result in errors:
            lines.append(f"- **{result.validator_name}**: {result.error}")
        lines.append("")
        return lines

    def _build_footer_section(self, report: SecurityReport) -> list[str]:
        """Build the footer section."""
        completed = (
            report.completed_at.strftime("%Y-%m-%d %H:%M:%S")
            if report.completed_at
            else "N/A"
        )
        return [
            "---",
            f"*Scan ID: `{report.scan_id}` | Completed: {completed}*",
            "",
            "*Generated by NEO-AIOS Security Scanner*",
        ]

    def _generate_pr_comment_with_metadata(
        self,
        report: SecurityReport,
        pr_number: int,
        repo: str,
    ) -> str:
        """Generate PR comment with PR metadata.

        Args:
            report: The security report.
            pr_number: The PR number.
            repo: The repository name.

        Returns:
            Enhanced markdown comment with PR metadata.
        """
        base_comment = self.generate_pr_comment(report)

        # Prepend PR info
        header = f"# Security Review for PR #{pr_number}\n\n"
        header += f"**Repository:** `{repo}`\n"
        header += f"**Target Path:** `{report.target_path}`\n\n"

        return header + base_comment

    def _generate_error_comment(self, error: str) -> str:
        """Generate an error comment when review fails.

        Args:
            error: The error message.

        Returns:
            Error markdown comment.
        """
        lines: list[str] = [
            "## :x: Security Review - Error",
            "",
            "> **Security review could not be completed.** "
            "This PR is blocked until the issue is resolved.",
            "",
            "### Error Details",
            "",
            f"```\n{error}\n```",
            "",
            "Please check the CI logs for more information.",
            "",
            "---",
            "*Generated by NEO-AIOS Security Scanner*",
        ]
        return "\n".join(lines)

    def _get_blocking_findings(self, report: SecurityReport) -> list[SecurityFinding]:
        """Get all blocking findings (CRITICAL and HIGH).

        Args:
            report: The security report.

        Returns:
            List of blocking findings sorted by severity.
        """
        findings: list[SecurityFinding] = []

        for result in report.results:
            for finding in result.findings:
                if finding.severity in (Severity.CRITICAL, Severity.HIGH):
                    findings.append(finding)

        # Sort by severity (CRITICAL first, then HIGH)
        findings.sort(key=lambda f: _SEVERITY_ORDER.get(f.severity, 999))

        return findings

    def _get_non_blocking_findings(
        self, report: SecurityReport
    ) -> list[SecurityFinding]:
        """Get all non-blocking findings (MEDIUM, LOW, INFO).

        Args:
            report: The security report.

        Returns:
            List of non-blocking findings sorted by severity.
        """
        findings: list[SecurityFinding] = []

        for result in report.results:
            for finding in result.findings:
                if finding.severity not in (Severity.CRITICAL, Severity.HIGH):
                    findings.append(finding)

        # Sort by severity (MEDIUM first, then LOW, then INFO)
        findings.sort(key=lambda f: _SEVERITY_ORDER.get(f.severity, 999))

        return findings

    def _get_severity_emoji(self, severity: Severity) -> str:
        """Get emoji for severity level.

        Args:
            severity: The severity level.

        Returns:
            Emoji string for the severity.
        """
        emoji_map: dict[Severity, str] = {
            Severity.CRITICAL: ":red_circle:",
            Severity.HIGH: ":orange_circle:",
            Severity.MEDIUM: ":yellow_circle:",
            Severity.LOW: ":large_blue_circle:",
            Severity.INFO: ":white_circle:",
        }
        return emoji_map.get(severity, ":black_circle:")


# Global instance with default configuration
pr_automation_gate = PRAutomationGate()


__all__ = [
    "PRAutomationGate",
    "PRReviewResult",
    "PRStatus",
    "pr_automation_gate",
]
