"""Report formatters for security scan results.

This module provides formatters to convert SecurityReport objects
into various output formats: JSON, Markdown, HTML, Console, and SARIF.

Example:
    >>> from aios.security.reports.formats import MarkdownFormatter
    >>> formatter = MarkdownFormatter()
    >>> markdown = formatter.format(report)
"""

from __future__ import annotations

import html
import json
from abc import ABC
from abc import abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING
from typing import Any
from typing import ClassVar

from aios.security.models import SecurityReport
from aios.security.models import Severity

if TYPE_CHECKING:
    from aios.security.models import SecurityFinding


# Severity ordering for sorting (lower index = higher priority)
SEVERITY_ORDER: dict[Severity, int] = {
    Severity.CRITICAL: 0,
    Severity.HIGH: 1,
    Severity.MEDIUM: 2,
    Severity.LOW: 3,
    Severity.INFO: 4,
}

# Severity display colors and icons
SEVERITY_STYLES: dict[Severity, dict[str, str]] = {
    Severity.CRITICAL: {"color": "#dc2626", "icon": "🔴", "label": "CRITICAL"},
    Severity.HIGH: {"color": "#ea580c", "icon": "🟠", "label": "HIGH"},
    Severity.MEDIUM: {"color": "#ca8a04", "icon": "🟡", "label": "MEDIUM"},
    Severity.LOW: {"color": "#2563eb", "icon": "🔵", "label": "LOW"},
    Severity.INFO: {"color": "#6b7280", "icon": "⚪", "label": "INFO"},
}

# SARIF severity mapping
SARIF_SEVERITY_MAP: dict[Severity, str] = {
    Severity.CRITICAL: "error",
    Severity.HIGH: "error",
    Severity.MEDIUM: "warning",
    Severity.LOW: "note",
    Severity.INFO: "none",
}

# All severities in order for iteration
SEVERITIES_ORDERED: list[Severity] = [
    Severity.CRITICAL,
    Severity.HIGH,
    Severity.MEDIUM,
    Severity.LOW,
    Severity.INFO,
]


def _get_all_findings_sorted(report: SecurityReport) -> list[SecurityFinding]:
    """Get all findings from a report sorted by severity."""
    all_findings: list[SecurityFinding] = []
    for result in report.results:
        all_findings.extend(result.findings)
    all_findings.sort(key=lambda f: SEVERITY_ORDER.get(f.severity, 999))
    return all_findings


def _get_status(report: SecurityReport) -> str:
    """Determine overall scan status."""
    if report.critical_findings > 0 or report.high_findings > 0:
        return "FAIL"
    if report.medium_findings > 0:
        return "WARNING"
    return "PASS"


def _format_duration(duration_ms: int) -> str:
    """Format duration in human-readable form."""
    if duration_ms >= 1000:
        return f"{duration_ms / 1000:.2f}s"
    return f"{duration_ms}ms"


def _calculate_duration_ms(report: SecurityReport) -> int:
    """Calculate duration in milliseconds from report timestamps."""
    if report.completed_at and report.started_at:
        return int((report.completed_at - report.started_at).total_seconds() * 1000)
    return report.total_duration_ms


def _count_by_severity(
    findings: list[SecurityFinding], severity: Severity
) -> int:
    """Count findings of a specific severity."""
    return sum(1 for f in findings if f.severity == severity)


class ReportFormatter(ABC):
    """Abstract base class for report formatters."""

    @property
    @abstractmethod
    def format_name(self) -> str:
        """Return the format name (e.g., 'json', 'markdown')."""
        ...

    @property
    @abstractmethod
    def file_extension(self) -> str:
        """Return the file extension for this format."""
        ...

    @abstractmethod
    def format(
        self,
        report: SecurityReport,
        *,
        min_severity: Severity | None = None,
        include_recommendations: bool = True,
    ) -> str:
        """Format the security report."""
        ...

    def _filter_findings(
        self,
        findings: list[SecurityFinding],
        min_severity: Severity | None,
    ) -> list[SecurityFinding]:
        """Filter findings by minimum severity."""
        if min_severity is None:
            return findings
        min_order = SEVERITY_ORDER.get(min_severity, 999)
        return [f for f in findings if SEVERITY_ORDER.get(f.severity, 999) <= min_order]


class JSONFormatter(ReportFormatter):
    """Formats security reports as JSON."""

    @property
    def format_name(self) -> str:
        return "json"

    @property
    def file_extension(self) -> str:
        return ".json"

    def format(
        self,
        report: SecurityReport,
        *,
        min_severity: Severity | None = None,
        include_recommendations: bool = True,
    ) -> str:
        all_findings = _get_all_findings_sorted(report)
        filtered = self._filter_findings(all_findings, min_severity)
        duration_ms = _calculate_duration_ms(report)

        output = self._build_base_output(report, filtered, duration_ms)
        output["findings"] = self._build_findings_list(filtered, include_recommendations)

        return json.dumps(output, indent=2, ensure_ascii=False)

    def _build_base_output(
        self,
        report: SecurityReport,
        findings: list[SecurityFinding],
        duration_ms: int,
    ) -> dict[str, Any]:
        """Build the base output structure."""
        return {
            "scan_id": report.scan_id,
            "target_path": report.target_path,
            "started_at": report.started_at.isoformat(),
            "completed_at": report.completed_at.isoformat() if report.completed_at else None,
            "status": _get_status(report),
            "summary": {
                "total_findings": len(findings),
                "critical": _count_by_severity(findings, Severity.CRITICAL),
                "high": _count_by_severity(findings, Severity.HIGH),
                "medium": _count_by_severity(findings, Severity.MEDIUM),
                "low": _count_by_severity(findings, Severity.LOW),
                "info": _count_by_severity(findings, Severity.INFO),
                "files_scanned": report.files_scanned,
                "validators_run": len(report.results),
                "duration_ms": duration_ms,
                "has_errors": report.has_errors,
            },
            "findings": [],
        }

    def _build_findings_list(
        self,
        findings: list[SecurityFinding],
        include_recommendations: bool,
    ) -> list[dict[str, Any]]:
        """Build the findings list."""
        result: list[dict[str, Any]] = []
        for finding in findings:
            finding_dict = self._serialize_finding(finding, include_recommendations)
            result.append(finding_dict)
        return result

    def _serialize_finding(
        self,
        finding: SecurityFinding,
        include_recommendations: bool,
    ) -> dict[str, Any]:
        """Serialize a single finding to dict."""
        data: dict[str, Any] = {
            "id": finding.id,
            "validator_id": finding.validator_id,
            "severity": finding.severity.value,
            "category": finding.category.value,
            "title": finding.title,
            "description": finding.description,
            "location": {
                "file_path": finding.location.file_path,
                "line_start": finding.location.line_start,
                "line_end": finding.location.line_end,
                "column_start": finding.location.column_start,
                "column_end": finding.location.column_end,
                "snippet": finding.location.snippet,
            },
            "confidence": finding.confidence,
            "auto_fixable": finding.auto_fixable,
            "cwe_id": finding.cwe_id,
            "owasp_id": finding.owasp_id,
            "found_at": finding.found_at.isoformat(),
        }
        if include_recommendations:
            data["recommendation"] = finding.recommendation
            data["fix_snippet"] = finding.fix_snippet
        return data


class MarkdownFormatter(ReportFormatter):
    """Formats security reports as Markdown."""

    @property
    def format_name(self) -> str:
        return "markdown"

    @property
    def file_extension(self) -> str:
        return ".md"

    def format(
        self,
        report: SecurityReport,
        *,
        min_severity: Severity | None = None,
        include_recommendations: bool = True,
    ) -> str:
        all_findings = _get_all_findings_sorted(report)
        filtered = self._filter_findings(all_findings, min_severity)
        duration_ms = _calculate_duration_ms(report)

        lines: list[str] = []
        self._add_header(lines, report)
        self._add_summary(lines, report, filtered, duration_ms)
        self._add_top_issues(lines, filtered)
        self._add_detailed_findings(lines, filtered, include_recommendations)
        self._add_errors(lines, report)
        self._add_footer(lines)

        return "\n".join(lines)

    def _add_header(self, lines: list[str], report: SecurityReport) -> None:
        """Add report header."""
        lines.append("# Security Scan Report")
        lines.append("")
        status = _get_status(report)
        status_icons = {"FAIL": "🔴", "WARNING": "🟡", "PASS": "🟢"}
        lines.append(f"**Status:** {status_icons.get(status, '')} {status}")
        lines.append("")

    def _add_summary(
        self,
        lines: list[str],
        report: SecurityReport,
        findings: list[SecurityFinding],
        duration_ms: int,
    ) -> None:
        """Add executive summary section."""
        lines.extend([
            "## Executive Summary",
            "",
            f"- **Scan ID:** `{report.scan_id}`",
            f"- **Target:** `{report.target_path}`",
            f"- **Duration:** {_format_duration(duration_ms)}",
            f"- **Files Scanned:** {report.files_scanned}",
            f"- **Validators Run:** {len(report.results)}",
            "",
            "### Findings by Severity",
            "",
            "| Severity | Count |",
            "|----------|-------|",
        ])
        for severity in SEVERITIES_ORDERED:
            style = SEVERITY_STYLES[severity]
            count = _count_by_severity(findings, severity)
            lines.append(f"| {style['icon']} {style['label']} | {count} |")
        lines.append(f"| **Total** | **{len(findings)}** |")
        lines.append("")

    def _add_top_issues(
        self, lines: list[str], findings: list[SecurityFinding]
    ) -> None:
        """Add top critical issues section."""
        critical = [f for f in findings if f.severity in (Severity.CRITICAL, Severity.HIGH)][:5]
        if not critical:
            return
        lines.extend(["### Top Critical Issues", ""])
        for i, finding in enumerate(critical, 1):
            style = SEVERITY_STYLES[finding.severity]
            lines.append(
                f"{i}. {style['icon']} **{finding.title}** "
                f"- `{finding.location.file_path}:{finding.location.line_start}`"
            )
        lines.append("")

    def _add_detailed_findings(
        self,
        lines: list[str],
        findings: list[SecurityFinding],
        include_recommendations: bool,
    ) -> None:
        """Add detailed findings section."""
        if not findings:
            return
        lines.extend(["## Detailed Findings", ""])
        for severity in SEVERITIES_ORDERED:
            sev_findings = [f for f in findings if f.severity == severity]
            if sev_findings:
                self._add_severity_section(lines, severity, sev_findings, include_recommendations)

    def _add_severity_section(
        self,
        lines: list[str],
        severity: Severity,
        findings: list[SecurityFinding],
        include_recommendations: bool,
    ) -> None:
        """Add a severity section."""
        style = SEVERITY_STYLES[severity]
        lines.append(f"### {style['icon']} {style['label']} ({len(findings)})")
        lines.append("")
        for finding in findings:
            self._add_finding_detail(lines, finding, include_recommendations)

    def _add_finding_detail(
        self,
        lines: list[str],
        finding: SecurityFinding,
        include_recommendations: bool,
    ) -> None:
        """Add a single finding detail."""
        lines.extend([
            f"#### {finding.title}",
            "",
            f"- **ID:** `{finding.id}`",
            f"- **Category:** {finding.category.value}",
            f"- **Location:** `{finding.location.file_path}:{finding.location.line_start}`",
        ])
        if finding.cwe_id:
            lines.append(f"- **CWE:** {finding.cwe_id}")
        if finding.owasp_id:
            lines.append(f"- **OWASP:** {finding.owasp_id}")
        lines.extend([
            f"- **Confidence:** {finding.confidence:.0%}",
            "",
            f"**Description:** {finding.description}",
            "",
        ])
        if finding.location.snippet:
            lines.extend(["**Code:**", "```", finding.location.snippet, "```", ""])
        if include_recommendations:
            lines.append(f"**Recommendation:** {finding.recommendation}")
            lines.append("")
            if finding.fix_snippet:
                lines.extend(["**Suggested Fix:**", "```", finding.fix_snippet, "```", ""])
        lines.extend(["---", ""])

    def _add_errors(self, lines: list[str], report: SecurityReport) -> None:
        """Add errors section if any."""
        if not report.has_errors:
            return
        lines.extend(["## Errors", ""])
        for result in report.results:
            if result.error:
                lines.append(f"- **{result.validator_name}:** {result.error}")
        lines.append("")

    def _add_footer(self, lines: list[str]) -> None:
        """Add footer."""
        lines.extend([
            "---",
            f"*Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} by AIOS Security Scanner*",
        ])


class HTMLFormatter(ReportFormatter):
    """Formats security reports as HTML with inline CSS."""

    @property
    def format_name(self) -> str:
        return "html"

    @property
    def file_extension(self) -> str:
        return ".html"

    def format(
        self,
        report: SecurityReport,
        *,
        min_severity: Severity | None = None,
        include_recommendations: bool = True,
    ) -> str:
        all_findings = _get_all_findings_sorted(report)
        filtered = self._filter_findings(all_findings, min_severity)
        duration_ms = _calculate_duration_ms(report)
        status = _get_status(report)

        parts: list[str] = []
        self._add_html_head(parts)
        self._add_body_start(parts, status)
        self._add_summary_section(parts, report, duration_ms)
        self._add_severity_cards(parts, filtered)
        self._add_findings_section(parts, filtered, include_recommendations)
        self._add_html_footer(parts)

        return "\n".join(parts)

    def _add_html_head(self, parts: list[str]) -> None:
        """Add HTML head section."""
        parts.extend([
            "<!DOCTYPE html>",
            '<html lang="en">',
            "<head>",
            '<meta charset="UTF-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
            "<title>Security Scan Report</title>",
            "<style>",
            self._get_css(),
            "</style>",
            "</head>",
        ])

    def _add_body_start(self, parts: list[str], status: str) -> None:
        """Add body start with header and status."""
        parts.extend([
            "<body>",
            '<div class="container">',
            '<h1>Security Scan Report</h1>',
            f'<div class="status status-{status.lower()}">Status: {status}</div>',
        ])

    def _add_summary_section(
        self, parts: list[str], report: SecurityReport, duration_ms: int
    ) -> None:
        """Add executive summary section."""
        parts.extend([
            '<div class="summary">',
            "<h2>Executive Summary</h2>",
            "<table>",
            f"<tr><td>Scan ID</td><td><code>{html.escape(report.scan_id)}</code></td></tr>",
            f"<tr><td>Target</td><td><code>{html.escape(report.target_path)}</code></td></tr>",
            f"<tr><td>Duration</td><td>{_format_duration(duration_ms)}</td></tr>",
            f"<tr><td>Files Scanned</td><td>{report.files_scanned}</td></tr>",
            f"<tr><td>Validators Run</td><td>{len(report.results)}</td></tr>",
            "</table>",
            "</div>",
        ])

    def _add_severity_cards(
        self, parts: list[str], findings: list[SecurityFinding]
    ) -> None:
        """Add severity cards section."""
        parts.extend([
            '<div class="severity-breakdown">',
            "<h2>Findings by Severity</h2>",
            '<div class="severity-cards">',
        ])
        for severity in SEVERITIES_ORDERED:
            count = _count_by_severity(findings, severity)
            style = SEVERITY_STYLES[severity]
            parts.extend([
                f'<div class="severity-card" style="border-color: {style["color"]}">',
                f'<span class="severity-icon">{style["icon"]}</span>',
                f'<span class="severity-label">{style["label"]}</span>',
                f'<span class="severity-count">{count}</span>',
                "</div>",
            ])
        parts.extend(["</div>", "</div>"])

    def _add_findings_section(
        self,
        parts: list[str],
        findings: list[SecurityFinding],
        include_recommendations: bool,
    ) -> None:
        """Add findings section."""
        if not findings:
            return
        parts.extend(['<div class="findings">', "<h2>Detailed Findings</h2>"])
        for finding in findings:
            self._add_finding_html(parts, finding, include_recommendations)
        parts.append("</div>")

    def _add_finding_html(
        self,
        parts: list[str],
        finding: SecurityFinding,
        include_recommendations: bool,
    ) -> None:
        """Add a single finding in HTML."""
        style = SEVERITY_STYLES[finding.severity]
        parts.extend([
            f'<div class="finding" style="border-left: 4px solid {style["color"]}">',
            '<div class="finding-header">',
            f'<span class="finding-severity">{style["icon"]} {style["label"]}</span>',
            f'<span class="finding-title">{html.escape(finding.title)}</span>',
            "</div>",
            '<div class="finding-meta">',
            f"<span>ID: <code>{html.escape(finding.id)}</code></span>",
            f"<span>Category: {html.escape(finding.category.value)}</span>",
            f"<span>Location: <code>{html.escape(finding.location.file_path)}:{finding.location.line_start}</code></span>",
        ])
        if finding.cwe_id:
            parts.append(f"<span>CWE: {html.escape(finding.cwe_id)}</span>")
        parts.extend([
            "</div>",
            f'<p class="finding-description">{html.escape(finding.description)}</p>',
        ])
        if finding.location.snippet:
            parts.append(f"<pre><code>{html.escape(finding.location.snippet)}</code></pre>")
        if include_recommendations:
            parts.append(
                f'<p class="recommendation"><strong>Recommendation:</strong> '
                f'{html.escape(finding.recommendation)}</p>'
            )
            if finding.fix_snippet:
                parts.extend([
                    '<p><strong>Suggested Fix:</strong></p>',
                    f"<pre><code>{html.escape(finding.fix_snippet)}</code></pre>",
                ])
        parts.append("</div>")

    def _add_html_footer(self, parts: list[str]) -> None:
        """Add HTML footer."""
        parts.extend([
            '<div class="footer">',
            f"Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} by AIOS Security Scanner",
            "</div>",
            "</div>",
            "</body>",
            "</html>",
        ])

    def _get_css(self) -> str:
        """Return inline CSS styles."""
        return """
            * { box-sizing: border-box; margin: 0; padding: 0; }
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                   line-height: 1.6; color: #1f2937; background: #f3f4f6; }
            .container { max-width: 1000px; margin: 0 auto; padding: 2rem; }
            h1 { font-size: 2rem; margin-bottom: 1rem; color: #111827; }
            h2 { font-size: 1.5rem; margin: 1.5rem 0 1rem; color: #374151; }
            .status { display: inline-block; padding: 0.5rem 1rem; border-radius: 0.5rem;
                      font-weight: 600; margin-bottom: 1.5rem; }
            .status-fail { background: #fee2e2; color: #dc2626; }
            .status-warning { background: #fef3c7; color: #d97706; }
            .status-pass { background: #d1fae5; color: #059669; }
            .summary { background: white; padding: 1.5rem; border-radius: 0.5rem;
                       box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 1.5rem; }
            .summary table { width: 100%; }
            .summary td { padding: 0.5rem; border-bottom: 1px solid #e5e7eb; }
            .summary td:first-child { font-weight: 500; width: 150px; }
            code { background: #f3f4f6; padding: 0.2rem 0.4rem; border-radius: 0.25rem;
                   font-family: 'Menlo', monospace; font-size: 0.875rem; }
            .severity-cards { display: flex; gap: 1rem; flex-wrap: wrap; }
            .severity-card { background: white; padding: 1rem; border-radius: 0.5rem;
                            border: 2px solid; min-width: 100px; text-align: center; }
            .severity-icon { font-size: 1.5rem; display: block; }
            .severity-label { font-size: 0.75rem; text-transform: uppercase; color: #6b7280; }
            .severity-count { font-size: 2rem; font-weight: 700; display: block; }
            .findings { margin-top: 1.5rem; }
            .finding { background: white; padding: 1.5rem; border-radius: 0.5rem;
                       margin-bottom: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
            .finding-header { display: flex; align-items: center; gap: 1rem; margin-bottom: 0.5rem; }
            .finding-severity { font-weight: 600; }
            .finding-title { font-size: 1.125rem; font-weight: 600; }
            .finding-meta { display: flex; gap: 1rem; flex-wrap: wrap; font-size: 0.875rem;
                           color: #6b7280; margin-bottom: 1rem; }
            .finding-description { margin-bottom: 1rem; }
            pre { background: #1f2937; color: #f3f4f6; padding: 1rem; border-radius: 0.5rem;
                  overflow-x: auto; margin: 1rem 0; }
            pre code { background: none; color: inherit; padding: 0; }
            .recommendation { background: #eff6ff; padding: 1rem; border-radius: 0.5rem;
                             border-left: 4px solid #3b82f6; }
            .footer { margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #e5e7eb;
                      text-align: center; color: #6b7280; font-size: 0.875rem; }
        """


class ConsoleFormatter(ReportFormatter):
    """Formats security reports for terminal output with ANSI colors."""

    # ANSI color codes
    _COLORS: ClassVar[dict[Severity, str]] = {
        Severity.CRITICAL: "\033[91m",
        Severity.HIGH: "\033[38;5;208m",
        Severity.MEDIUM: "\033[93m",
        Severity.LOW: "\033[94m",
        Severity.INFO: "\033[90m",
    }
    _RESET: ClassVar[str] = "\033[0m"
    _CYAN: ClassVar[str] = "\033[96m"

    @property
    def format_name(self) -> str:
        return "console"

    @property
    def file_extension(self) -> str:
        return ".txt"

    def format(
        self,
        report: SecurityReport,
        *,
        min_severity: Severity | None = None,
        include_recommendations: bool = True,
    ) -> str:
        all_findings = _get_all_findings_sorted(report)
        filtered = self._filter_findings(all_findings, min_severity)
        duration_ms = _calculate_duration_ms(report)

        lines: list[str] = []
        self._add_header_box(lines, report, filtered, duration_ms)
        self._add_detailed_findings(lines, filtered, include_recommendations)
        self._add_footer(lines)

        return "\n".join(lines)

    def _add_header_box(
        self,
        lines: list[str],
        report: SecurityReport,
        findings: list[SecurityFinding],
        duration_ms: int,
    ) -> None:
        """Add the header box with summary."""
        lines.extend([
            "",
            "╔══════════════════════════════════════════════════════════════╗",
            "║              SECURITY SCAN REPORT                            ║",
            "╠══════════════════════════════════════════════════════════════╣",
        ])
        self._add_status_line(lines, report)
        lines.append("╠══════════════════════════════════════════════════════════════╣")
        self._add_info_lines(lines, report, duration_ms)
        lines.append("╠══════════════════════════════════════════════════════════════╣")
        self._add_summary_lines(lines, findings)
        lines.extend([
            "╚══════════════════════════════════════════════════════════════╝",
            "",
        ])

    def _add_status_line(self, lines: list[str], report: SecurityReport) -> None:
        """Add status line."""
        status = _get_status(report)
        status_colors = {"FAIL": "\033[91m", "WARNING": "\033[93m", "PASS": "\033[92m"}
        color = status_colors.get(status, "")
        lines.append(f"║  Status: {color}● {status}{self._RESET}                                            ║"[:66] + "║")

    def _add_info_lines(
        self, lines: list[str], report: SecurityReport, duration_ms: int
    ) -> None:
        """Add info lines."""
        lines.extend([
            f"║  Scan ID:    {report.scan_id:<48}║",
            f"║  Target:     {report.target_path[:48]:<48}║",
            f"║  Duration:   {_format_duration(duration_ms):<48}║",
            f"║  Files:      {report.files_scanned:<48}║",
            f"║  Validators: {len(report.results):<48}║",
        ])

    def _add_summary_lines(
        self, lines: list[str], findings: list[SecurityFinding]
    ) -> None:
        """Add summary lines."""
        lines.append("║  FINDINGS SUMMARY                                            ║")
        for severity in SEVERITIES_ORDERED:
            color = self._COLORS[severity]
            label = severity.name
            count = _count_by_severity(findings, severity)
            label_display = f"{color}{label}{self._RESET}"
            # Calculate padding accounting for ANSI codes
            visible_len = len(label) + len(str(count)) + 2
            padding = 48 - visible_len
            lines.append(f"║    {label_display}: {count}{' ' * padding}║")
        lines.extend([
            f"║    {'─' * 40}                  ║",
            f"║    TOTAL: {len(findings):<51}║",
        ])

    def _add_detailed_findings(
        self,
        lines: list[str],
        findings: list[SecurityFinding],
        include_recommendations: bool,
    ) -> None:
        """Add detailed findings."""
        if not findings:
            return
        lines.extend(["DETAILED FINDINGS", "─" * 64, ""])
        for finding in findings:
            self._add_finding_console(lines, finding, include_recommendations)

    def _add_finding_console(
        self,
        lines: list[str],
        finding: SecurityFinding,
        include_recommendations: bool,
    ) -> None:
        """Add a single finding to console output."""
        color = self._COLORS[finding.severity]
        prefix = f"{color}[{finding.severity.name}]{self._RESET}"
        lines.extend([
            f"{prefix} {finding.title}",
            f"  Location: {finding.location.file_path}:{finding.location.line_start}",
            f"  Category: {finding.category.value}",
            f"  {finding.description}",
        ])
        if finding.location.snippet:
            lines.append("  Code:")
            for snippet_line in finding.location.snippet.split("\n"):
                lines.append(f"    {snippet_line}")
        if include_recommendations:
            lines.append(f"  {self._CYAN}Recommendation:{self._RESET} {finding.recommendation}")
            if finding.fix_snippet:
                lines.append("  Suggested fix:")
                for fix_line in finding.fix_snippet.split("\n"):
                    lines.append(f"    {fix_line}")
        lines.append("")

    def _add_footer(self, lines: list[str]) -> None:
        """Add footer."""
        lines.extend([
            "─" * 64,
            f"Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} by AIOS Security Scanner",
            "",
        ])


class SARIFFormatter(ReportFormatter):
    """Formats security reports as SARIF for IDE integration."""

    @property
    def format_name(self) -> str:
        return "sarif"

    @property
    def file_extension(self) -> str:
        return ".sarif"

    def format(
        self,
        report: SecurityReport,
        *,
        min_severity: Severity | None = None,
        include_recommendations: bool = True,  # noqa: ARG002
    ) -> str:
        all_findings = _get_all_findings_sorted(report)
        filtered = self._filter_findings(all_findings, min_severity)

        rules = self._build_rules(filtered)
        results = self._build_results(filtered)

        sarif = self._build_sarif_document(report, rules, results)
        return json.dumps(sarif, indent=2, ensure_ascii=False)

    def _build_rules(self, findings: list[SecurityFinding]) -> list[dict[str, Any]]:
        """Build SARIF rules from findings."""
        rules: list[dict[str, Any]] = []
        rule_ids: set[str] = set()

        for finding in findings:
            rule_id = f"{finding.validator_id}/{finding.id}"
            if rule_id in rule_ids:
                continue
            rule_ids.add(rule_id)
            rule = self._create_rule(finding, rule_id)
            rules.append(rule)
        return rules

    def _create_rule(self, finding: SecurityFinding, rule_id: str) -> dict[str, Any]:
        """Create a single SARIF rule."""
        rule: dict[str, Any] = {
            "id": rule_id,
            "name": finding.title,
            "shortDescription": {"text": finding.title},
            "fullDescription": {"text": finding.description},
            "helpUri": (
                f"https://cwe.mitre.org/data/definitions/{finding.cwe_id.split('-')[1]}.html"
                if finding.cwe_id
                else None
            ),
            "defaultConfiguration": {
                "level": SARIF_SEVERITY_MAP.get(finding.severity, "note")
            },
            "properties": {
                "category": finding.category.value,
                "security-severity": str(10.0 - SEVERITY_ORDER.get(finding.severity, 4) * 2),
            },
        }
        if finding.cwe_id:
            rule["properties"]["cwe"] = finding.cwe_id
        if finding.owasp_id:
            rule["properties"]["owasp"] = finding.owasp_id
        return rule

    def _build_results(self, findings: list[SecurityFinding]) -> list[dict[str, Any]]:
        """Build SARIF results from findings."""
        return [self._create_result(f) for f in findings]

    def _create_result(self, finding: SecurityFinding) -> dict[str, Any]:
        """Create a single SARIF result."""
        result: dict[str, Any] = {
            "ruleId": f"{finding.validator_id}/{finding.id}",
            "level": SARIF_SEVERITY_MAP.get(finding.severity, "note"),
            "message": {"text": finding.description},
            "locations": [{
                "physicalLocation": {
                    "artifactLocation": {
                        "uri": finding.location.file_path,
                        "uriBaseId": "%SRCROOT%",
                    },
                    "region": {
                        "startLine": finding.location.line_start,
                        "endLine": finding.location.line_end,
                        "startColumn": finding.location.column_start or 1,
                        "endColumn": finding.location.column_end,
                        "snippet": {"text": finding.location.snippet or ""},
                    },
                }
            }],
            "fixes": [],
        }
        if finding.fix_snippet:
            result["fixes"].append({
                "description": {"text": finding.recommendation},
                "artifactChanges": [{
                    "artifactLocation": {"uri": finding.location.file_path},
                    "replacements": [{
                        "deletedRegion": {
                            "startLine": finding.location.line_start,
                            "endLine": finding.location.line_end,
                        },
                        "insertedContent": {"text": finding.fix_snippet},
                    }],
                }],
            })
        return result

    def _build_sarif_document(
        self,
        report: SecurityReport,
        rules: list[dict[str, Any]],
        results: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Build the complete SARIF document."""
        return {
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "version": "2.1.0",
            "runs": [{
                "tool": {
                    "driver": {
                        "name": "AIOS Security Scanner",
                        "version": "1.0.0",
                        "informationUri": "https://github.com/fofonka/aios",
                        "rules": rules,
                    }
                },
                "results": results,
                "invocations": [{
                    "executionSuccessful": not report.has_errors,
                    "startTimeUtc": report.started_at.isoformat() + "Z",
                    "endTimeUtc": (
                        report.completed_at.isoformat() + "Z"
                        if report.completed_at
                        else None
                    ),
                }],
            }],
        }


# Registry of available formatters
FORMATTERS: dict[str, type[ReportFormatter]] = {
    "console": ConsoleFormatter,
    "html": HTMLFormatter,
    "json": JSONFormatter,
    "markdown": MarkdownFormatter,
    "md": MarkdownFormatter,
    "sarif": SARIFFormatter,
}


def get_formatter(format_name: str) -> ReportFormatter:
    """Get a formatter instance by name."""
    format_key = format_name.lower()
    if format_key not in FORMATTERS:
        available = ", ".join(sorted(FORMATTERS.keys()))
        raise ValueError(f"Unknown format '{format_name}'. Available: {available}")
    return FORMATTERS[format_key]()


__all__ = [
    "FORMATTERS",
    "SARIF_SEVERITY_MAP",
    "SEVERITY_ORDER",
    "SEVERITY_STYLES",
    "ConsoleFormatter",
    "HTMLFormatter",
    "JSONFormatter",
    "MarkdownFormatter",
    "ReportFormatter",
    "SARIFFormatter",
    "get_formatter",
]  # sorted by ruff
