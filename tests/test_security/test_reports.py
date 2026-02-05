"""Tests for Security Report Generation.

Tests cover:
- ReportFormatter base class and implementations
- JSONFormatter output
- MarkdownFormatter output
- HTMLFormatter output
- ConsoleFormatter output
- SARIFFormatter output
- ReportGenerator class
- Severity filtering
- File output with format inference
"""

import json
from datetime import datetime
from pathlib import Path

import pytest

from aios.security.models import CodeLocation
from aios.security.models import FindingCategory
from aios.security.models import SecurityFinding
from aios.security.models import SecurityReport
from aios.security.models import Severity
from aios.security.models import ValidatorResult
from aios.security.reports import ConsoleFormatter
from aios.security.reports import EXTENSION_TO_FORMAT
from aios.security.reports import FORMATTERS
from aios.security.reports import HTMLFormatter
from aios.security.reports import JSONFormatter
from aios.security.reports import MarkdownFormatter
from aios.security.reports import ReportGenerator
from aios.security.reports import SARIFFormatter
from aios.security.reports import SEVERITY_ORDER
from aios.security.reports import SEVERITY_STYLES
from aios.security.reports import get_formatter
from aios.security.reports import report_generator


def create_finding(
    severity: Severity = Severity.HIGH,
    category: FindingCategory = FindingCategory.XSS,
    finding_id: str = "test-001",
    title: str = "Test Finding",
    description: str = "A test finding description",
    file_path: str = "src/app.tsx",
    line_start: int = 42,
    recommendation: str = "Fix this issue",
    snippet: str | None = "const x = unsafeRender(input);",
    cwe_id: str | None = "CWE-79",
    owasp_id: str | None = "A03:2021",
    auto_fixable: bool = False,
    fix_snippet: str | None = None,
) -> SecurityFinding:
    """Helper to create a finding for tests."""
    return SecurityFinding(
        id=finding_id,
        validator_id="test-validator",
        severity=severity,
        category=category,
        title=title,
        description=description,
        location=CodeLocation(
            file_path=file_path,
            line_start=line_start,
            line_end=line_start,
            snippet=snippet,
        ),
        recommendation=recommendation,
        cwe_id=cwe_id,
        owasp_id=owasp_id,
        auto_fixable=auto_fixable,
        fix_snippet=fix_snippet,
    )


def create_report(
    findings: list[SecurityFinding] | None = None,
    scan_id: str = "test-scan",
    target_path: str = "/src",
    files_scanned: int = 100,
) -> SecurityReport:
    """Helper to create a report for tests."""
    report = SecurityReport(
        scan_id=scan_id,
        started_at=datetime(2024, 1, 15, 10, 0, 0),
        completed_at=datetime(2024, 1, 15, 10, 0, 5),
        target_path=target_path,
    )

    if findings:
        report.add_result(
            ValidatorResult(
                validator_id="test-validator",
                validator_name="Test Validator",
                findings=findings,
                files_scanned=files_scanned,
                scan_duration_ms=5000,
            )
        )

    return report


class TestSeverityConstants:
    """Tests for severity-related constants."""

    def test_severity_order_values(self) -> None:
        """Test severity order mapping."""
        assert SEVERITY_ORDER[Severity.CRITICAL] == 0
        assert SEVERITY_ORDER[Severity.HIGH] == 1
        assert SEVERITY_ORDER[Severity.MEDIUM] == 2
        assert SEVERITY_ORDER[Severity.LOW] == 3
        assert SEVERITY_ORDER[Severity.INFO] == 4

    def test_severity_styles_all_severities(self) -> None:
        """Test all severities have styles defined."""
        for severity in Severity:
            assert severity in SEVERITY_STYLES
            style = SEVERITY_STYLES[severity]
            assert "color" in style
            assert "icon" in style
            assert "label" in style


class TestGetFormatter:
    """Tests for get_formatter function."""

    def test_get_json_formatter(self) -> None:
        """Test getting JSON formatter."""
        formatter = get_formatter("json")
        assert isinstance(formatter, JSONFormatter)

    def test_get_markdown_formatter(self) -> None:
        """Test getting Markdown formatter."""
        formatter = get_formatter("markdown")
        assert isinstance(formatter, MarkdownFormatter)

    def test_get_md_alias(self) -> None:
        """Test 'md' alias for Markdown."""
        formatter = get_formatter("md")
        assert isinstance(formatter, MarkdownFormatter)

    def test_get_html_formatter(self) -> None:
        """Test getting HTML formatter."""
        formatter = get_formatter("html")
        assert isinstance(formatter, HTMLFormatter)

    def test_get_console_formatter(self) -> None:
        """Test getting Console formatter."""
        formatter = get_formatter("console")
        assert isinstance(formatter, ConsoleFormatter)

    def test_get_sarif_formatter(self) -> None:
        """Test getting SARIF formatter."""
        formatter = get_formatter("sarif")
        assert isinstance(formatter, SARIFFormatter)

    def test_case_insensitive(self) -> None:
        """Test format names are case insensitive."""
        assert isinstance(get_formatter("JSON"), JSONFormatter)
        assert isinstance(get_formatter("Markdown"), MarkdownFormatter)
        assert isinstance(get_formatter("HTML"), HTMLFormatter)

    def test_unknown_format_raises(self) -> None:
        """Test unknown format raises ValueError."""
        with pytest.raises(ValueError, match="Unknown format"):
            get_formatter("unknown")


class TestJSONFormatter:
    """Tests for JSONFormatter."""

    def test_format_name(self) -> None:
        """Test format name property."""
        formatter = JSONFormatter()
        assert formatter.format_name == "json"

    def test_file_extension(self) -> None:
        """Test file extension property."""
        formatter = JSONFormatter()
        assert formatter.file_extension == ".json"

    def test_empty_report(self) -> None:
        """Test formatting empty report."""
        formatter = JSONFormatter()
        report = create_report()
        output = formatter.format(report)

        data = json.loads(output)
        assert data["scan_id"] == "test-scan"
        assert data["summary"]["total_findings"] == 0
        assert data["findings"] == []

    def test_report_with_findings(self) -> None:
        """Test formatting report with findings."""
        formatter = JSONFormatter()
        findings = [
            create_finding(Severity.CRITICAL, finding_id="c1"),
            create_finding(Severity.HIGH, finding_id="h1"),
        ]
        report = create_report(findings=findings)
        output = formatter.format(report)

        data = json.loads(output)
        assert data["summary"]["total_findings"] == 2
        assert data["summary"]["critical"] == 1
        assert data["summary"]["high"] == 1
        assert len(data["findings"]) == 2

    def test_finding_structure(self) -> None:
        """Test finding structure in JSON output."""
        formatter = JSONFormatter()
        finding = create_finding(
            severity=Severity.HIGH,
            title="XSS Vulnerability",
            cwe_id="CWE-79",
        )
        report = create_report(findings=[finding])
        output = formatter.format(report)

        data = json.loads(output)
        f = data["findings"][0]
        assert f["severity"] == "high"
        assert f["title"] == "XSS Vulnerability"
        assert f["cwe_id"] == "CWE-79"
        assert "location" in f
        assert f["location"]["file_path"] == "src/app.tsx"

    def test_status_fail(self) -> None:
        """Test FAIL status with critical findings."""
        formatter = JSONFormatter()
        report = create_report(findings=[create_finding(Severity.CRITICAL)])
        output = formatter.format(report)

        data = json.loads(output)
        assert data["status"] == "FAIL"

    def test_status_warning(self) -> None:
        """Test WARNING status with medium findings only."""
        formatter = JSONFormatter()
        report = create_report(findings=[create_finding(Severity.MEDIUM)])
        output = formatter.format(report)

        data = json.loads(output)
        assert data["status"] == "WARNING"

    def test_status_pass(self) -> None:
        """Test PASS status with low findings only."""
        formatter = JSONFormatter()
        report = create_report(findings=[create_finding(Severity.LOW)])
        output = formatter.format(report)

        data = json.loads(output)
        assert data["status"] == "PASS"

    def test_exclude_recommendations(self) -> None:
        """Test excluding recommendations from output."""
        formatter = JSONFormatter()
        report = create_report(findings=[create_finding()])
        output = formatter.format(report, include_recommendations=False)

        data = json.loads(output)
        assert "recommendation" not in data["findings"][0]
        assert "fix_snippet" not in data["findings"][0]


class TestMarkdownFormatter:
    """Tests for MarkdownFormatter."""

    def test_format_name(self) -> None:
        """Test format name property."""
        formatter = MarkdownFormatter()
        assert formatter.format_name == "markdown"

    def test_file_extension(self) -> None:
        """Test file extension property."""
        formatter = MarkdownFormatter()
        assert formatter.file_extension == ".md"

    def test_header(self) -> None:
        """Test markdown header."""
        formatter = MarkdownFormatter()
        report = create_report()
        output = formatter.format(report)

        assert "# Security Scan Report" in output

    def test_executive_summary(self) -> None:
        """Test executive summary section."""
        formatter = MarkdownFormatter()
        report = create_report(scan_id="abc123", target_path="/my/path")
        output = formatter.format(report)

        assert "## Executive Summary" in output
        assert "abc123" in output
        assert "/my/path" in output

    def test_severity_table(self) -> None:
        """Test severity breakdown table."""
        formatter = MarkdownFormatter()
        findings = [
            create_finding(Severity.CRITICAL),
            create_finding(Severity.HIGH),
            create_finding(Severity.MEDIUM),
        ]
        report = create_report(findings=findings)
        output = formatter.format(report)

        assert "| Severity | Count |" in output
        assert "CRITICAL" in output
        assert "HIGH" in output

    def test_top_critical_issues(self) -> None:
        """Test top critical issues section."""
        formatter = MarkdownFormatter()
        findings = [
            create_finding(Severity.CRITICAL, title="Critical Bug"),
            create_finding(Severity.HIGH, title="High Bug"),
        ]
        report = create_report(findings=findings)
        output = formatter.format(report)

        assert "### Top Critical Issues" in output
        assert "Critical Bug" in output

    def test_detailed_findings(self) -> None:
        """Test detailed findings section."""
        formatter = MarkdownFormatter()
        finding = create_finding(
            title="Test XSS",
            description="XSS vulnerability found",
            recommendation="Sanitize input",
        )
        report = create_report(findings=[finding])
        output = formatter.format(report)

        assert "## Detailed Findings" in output
        assert "Test XSS" in output
        assert "XSS vulnerability found" in output
        assert "Sanitize input" in output

    def test_code_snippet(self) -> None:
        """Test code snippet formatting."""
        formatter = MarkdownFormatter()
        finding = create_finding(snippet="const x = 1;")
        report = create_report(findings=[finding])
        output = formatter.format(report)

        assert "```" in output
        assert "const x = 1;" in output


class TestHTMLFormatter:
    """Tests for HTMLFormatter."""

    def test_format_name(self) -> None:
        """Test format name property."""
        formatter = HTMLFormatter()
        assert formatter.format_name == "html"

    def test_file_extension(self) -> None:
        """Test file extension property."""
        formatter = HTMLFormatter()
        assert formatter.file_extension == ".html"

    def test_valid_html_structure(self) -> None:
        """Test output is valid HTML structure."""
        formatter = HTMLFormatter()
        report = create_report()
        output = formatter.format(report)

        assert "<!DOCTYPE html>" in output
        assert "<html" in output
        assert "</html>" in output
        assert "<head>" in output
        assert "</head>" in output
        assert "<body>" in output
        assert "</body>" in output

    def test_inline_css(self) -> None:
        """Test CSS is included inline."""
        formatter = HTMLFormatter()
        report = create_report()
        output = formatter.format(report)

        assert "<style>" in output
        assert "</style>" in output
        assert ".container" in output

    def test_title(self) -> None:
        """Test page title."""
        formatter = HTMLFormatter()
        report = create_report()
        output = formatter.format(report)

        assert "<title>Security Scan Report</title>" in output

    def test_status_badge(self) -> None:
        """Test status badge classes."""
        formatter = HTMLFormatter()

        # FAIL status
        fail_report = create_report(findings=[create_finding(Severity.CRITICAL)])
        fail_output = formatter.format(fail_report)
        assert "status-fail" in fail_output

        # PASS status
        pass_report = create_report()
        pass_output = formatter.format(pass_report)
        assert "status-pass" in pass_output

    def test_severity_cards(self) -> None:
        """Test severity cards in HTML."""
        formatter = HTMLFormatter()
        report = create_report(findings=[create_finding(Severity.HIGH)])
        output = formatter.format(report)

        assert "severity-card" in output
        assert "severity-count" in output

    def test_html_escaping(self) -> None:
        """Test HTML special characters are escaped."""
        formatter = HTMLFormatter()
        finding = create_finding(
            title="<script>alert('test')</script>",
            description="Test <b>bold</b>",
        )
        report = create_report(findings=[finding])
        output = formatter.format(report)

        assert "&lt;script&gt;" in output
        assert "&lt;b&gt;" in output


class TestConsoleFormatter:
    """Tests for ConsoleFormatter."""

    def test_format_name(self) -> None:
        """Test format name property."""
        formatter = ConsoleFormatter()
        assert formatter.format_name == "console"

    def test_file_extension(self) -> None:
        """Test file extension property."""
        formatter = ConsoleFormatter()
        assert formatter.file_extension == ".txt"

    def test_box_drawing(self) -> None:
        """Test box drawing characters are used."""
        formatter = ConsoleFormatter()
        report = create_report()
        output = formatter.format(report)

        assert "╔" in output
        assert "╗" in output
        assert "╚" in output
        assert "╝" in output

    def test_header(self) -> None:
        """Test header text."""
        formatter = ConsoleFormatter()
        report = create_report()
        output = formatter.format(report)

        assert "SECURITY SCAN REPORT" in output

    def test_ansi_colors_critical(self) -> None:
        """Test ANSI colors for critical severity."""
        formatter = ConsoleFormatter()
        report = create_report(findings=[create_finding(Severity.CRITICAL)])
        output = formatter.format(report)

        # Check for red color code
        assert "\033[91m" in output
        assert "[CRITICAL]" in output

    def test_summary_section(self) -> None:
        """Test summary section."""
        formatter = ConsoleFormatter()
        report = create_report(scan_id="abc123")
        output = formatter.format(report)

        assert "Scan ID:" in output
        assert "abc123" in output
        assert "FINDINGS SUMMARY" in output


class TestSARIFFormatter:
    """Tests for SARIFFormatter."""

    def test_format_name(self) -> None:
        """Test format name property."""
        formatter = SARIFFormatter()
        assert formatter.format_name == "sarif"

    def test_file_extension(self) -> None:
        """Test file extension property."""
        formatter = SARIFFormatter()
        assert formatter.file_extension == ".sarif"

    def test_sarif_structure(self) -> None:
        """Test SARIF JSON structure."""
        formatter = SARIFFormatter()
        report = create_report()
        output = formatter.format(report)

        data = json.loads(output)
        assert "$schema" in data
        assert "version" in data
        assert data["version"] == "2.1.0"
        assert "runs" in data
        assert len(data["runs"]) == 1

    def test_tool_info(self) -> None:
        """Test tool information in SARIF."""
        formatter = SARIFFormatter()
        report = create_report()
        output = formatter.format(report)

        data = json.loads(output)
        tool = data["runs"][0]["tool"]["driver"]
        assert tool["name"] == "AIOS Security Scanner"
        assert "version" in tool

    def test_rules_from_findings(self) -> None:
        """Test rules are created from findings."""
        formatter = SARIFFormatter()
        finding = create_finding(
            finding_id="xss-001",
            title="XSS Detected",
            cwe_id="CWE-79",
        )
        report = create_report(findings=[finding])
        output = formatter.format(report)

        data = json.loads(output)
        rules = data["runs"][0]["tool"]["driver"]["rules"]
        assert len(rules) == 1
        assert "xss-001" in rules[0]["id"]

    def test_results_structure(self) -> None:
        """Test results structure in SARIF."""
        formatter = SARIFFormatter()
        finding = create_finding(
            file_path="src/app.tsx",
            line_start=42,
        )
        report = create_report(findings=[finding])
        output = formatter.format(report)

        data = json.loads(output)
        results = data["runs"][0]["results"]
        assert len(results) == 1

        result = results[0]
        assert "ruleId" in result
        assert "level" in result
        assert "message" in result
        assert "locations" in result

        location = result["locations"][0]["physicalLocation"]
        assert location["artifactLocation"]["uri"] == "src/app.tsx"
        assert location["region"]["startLine"] == 42

    def test_severity_mapping(self) -> None:
        """Test severity is mapped correctly to SARIF levels."""
        formatter = SARIFFormatter()

        # CRITICAL -> error
        critical_report = create_report(findings=[create_finding(Severity.CRITICAL)])
        critical_output = formatter.format(critical_report)
        critical_data = json.loads(critical_output)
        assert critical_data["runs"][0]["results"][0]["level"] == "error"

        # MEDIUM -> warning
        medium_report = create_report(findings=[create_finding(Severity.MEDIUM)])
        medium_output = formatter.format(medium_report)
        medium_data = json.loads(medium_output)
        assert medium_data["runs"][0]["results"][0]["level"] == "warning"

        # INFO -> none
        info_report = create_report(findings=[create_finding(Severity.INFO)])
        info_output = formatter.format(info_report)
        info_data = json.loads(info_output)
        assert info_data["runs"][0]["results"][0]["level"] == "none"


class TestSeverityFiltering:
    """Tests for severity filtering across formatters."""

    def test_filter_by_severity_json(self) -> None:
        """Test severity filtering in JSON formatter."""
        formatter = JSONFormatter()
        findings = [
            create_finding(Severity.CRITICAL, finding_id="c1"),
            create_finding(Severity.HIGH, finding_id="h1"),
            create_finding(Severity.MEDIUM, finding_id="m1"),
            create_finding(Severity.LOW, finding_id="l1"),
            create_finding(Severity.INFO, finding_id="i1"),
        ]
        report = create_report(findings=findings)

        # Filter to HIGH and above
        output = formatter.format(report, min_severity=Severity.HIGH)
        data = json.loads(output)

        assert data["summary"]["total_findings"] == 2
        severities = [f["severity"] for f in data["findings"]]
        assert "critical" in severities
        assert "high" in severities
        assert "medium" not in severities
        assert "low" not in severities
        assert "info" not in severities

    def test_filter_by_severity_markdown(self) -> None:
        """Test severity filtering in Markdown formatter."""
        formatter = MarkdownFormatter()
        findings = [
            create_finding(Severity.CRITICAL, finding_id="c1", title="Critical Issue"),
            create_finding(Severity.LOW, finding_id="l1", title="Low Issue"),
        ]
        report = create_report(findings=findings)

        output = formatter.format(report, min_severity=Severity.HIGH)

        assert "Critical Issue" in output
        assert "Low Issue" not in output

    def test_no_filter(self) -> None:
        """Test no filtering when min_severity is None."""
        formatter = JSONFormatter()
        findings = [
            create_finding(Severity.CRITICAL),
            create_finding(Severity.INFO),
        ]
        report = create_report(findings=findings)

        output = formatter.format(report, min_severity=None)
        data = json.loads(output)

        assert data["summary"]["total_findings"] == 2


class TestReportGenerator:
    """Tests for ReportGenerator class."""

    def test_default_format(self) -> None:
        """Test default format is json."""
        generator = ReportGenerator()
        assert generator.default_format == "json"

    def test_custom_default_format(self) -> None:
        """Test custom default format."""
        generator = ReportGenerator(default_format="markdown")
        assert generator.default_format == "markdown"

    def test_invalid_default_format(self) -> None:
        """Test invalid default format raises error."""
        with pytest.raises(ValueError, match="Unknown format"):
            ReportGenerator(default_format="invalid")

    def test_available_formats(self) -> None:
        """Test available formats list."""
        generator = ReportGenerator()
        formats = generator.available_formats

        assert "json" in formats
        assert "markdown" in formats
        assert "html" in formats
        assert "console" in formats
        assert "sarif" in formats

    def test_generate_with_format(self) -> None:
        """Test generate with explicit format."""
        generator = ReportGenerator()
        report = create_report()

        json_output = generator.generate(report, "json")
        md_output = generator.generate(report, "markdown")

        # JSON output should be parseable
        data = json.loads(json_output)
        assert "scan_id" in data

        # Markdown should have header
        assert "# Security Scan Report" in md_output

    def test_generate_uses_default(self) -> None:
        """Test generate uses default format when none specified."""
        generator = ReportGenerator(default_format="markdown")
        report = create_report()

        output = generator.generate(report)

        assert "# Security Scan Report" in output

    def test_generate_json_convenience(self) -> None:
        """Test generate_json convenience method."""
        generator = ReportGenerator()
        report = create_report()

        output = generator.generate_json(report)
        data = json.loads(output)

        assert "scan_id" in data

    def test_generate_markdown_convenience(self) -> None:
        """Test generate_markdown convenience method."""
        generator = ReportGenerator()
        report = create_report()

        output = generator.generate_markdown(report)

        assert "# Security Scan Report" in output

    def test_generate_html_convenience(self) -> None:
        """Test generate_html convenience method."""
        generator = ReportGenerator()
        report = create_report()

        output = generator.generate_html(report)

        assert "<!DOCTYPE html>" in output

    def test_generate_console_convenience(self) -> None:
        """Test generate_console convenience method."""
        generator = ReportGenerator()
        report = create_report()

        output = generator.generate_console(report)

        assert "SECURITY SCAN REPORT" in output

    def test_generate_sarif_convenience(self) -> None:
        """Test generate_sarif convenience method."""
        generator = ReportGenerator()
        report = create_report()

        output = generator.generate_sarif(report)
        data = json.loads(output)

        assert data["version"] == "2.1.0"

    def test_save_to_file_json(self, tmp_path: Path) -> None:
        """Test saving report to JSON file."""
        generator = ReportGenerator()
        report = create_report()
        file_path = tmp_path / "report.json"

        result = generator.save_to_file(report, file_path)

        assert result == file_path
        assert file_path.exists()
        content = file_path.read_text()
        data = json.loads(content)
        assert data["scan_id"] == "test-scan"

    def test_save_to_file_markdown(self, tmp_path: Path) -> None:
        """Test saving report to Markdown file."""
        generator = ReportGenerator()
        report = create_report()
        file_path = tmp_path / "report.md"

        generator.save_to_file(report, file_path)

        content = file_path.read_text()
        assert "# Security Scan Report" in content

    def test_save_to_file_html(self, tmp_path: Path) -> None:
        """Test saving report to HTML file."""
        generator = ReportGenerator()
        report = create_report()
        file_path = tmp_path / "report.html"

        generator.save_to_file(report, file_path)

        content = file_path.read_text()
        assert "<!DOCTYPE html>" in content

    def test_save_to_file_sarif(self, tmp_path: Path) -> None:
        """Test saving report to SARIF file."""
        generator = ReportGenerator()
        report = create_report()
        file_path = tmp_path / "report.sarif"

        generator.save_to_file(report, file_path)

        content = file_path.read_text()
        data = json.loads(content)
        assert data["version"] == "2.1.0"

    def test_save_to_file_explicit_format(self, tmp_path: Path) -> None:
        """Test saving with explicit format overrides extension."""
        generator = ReportGenerator()
        report = create_report()
        file_path = tmp_path / "report.txt"

        # Save as JSON despite .txt extension
        generator.save_to_file(report, file_path, format_name="json")

        content = file_path.read_text()
        data = json.loads(content)
        assert "scan_id" in data

    def test_save_to_file_creates_directory(self, tmp_path: Path) -> None:
        """Test save_to_file creates parent directories."""
        generator = ReportGenerator()
        report = create_report()
        file_path = tmp_path / "subdir" / "nested" / "report.json"

        generator.save_to_file(report, file_path)

        assert file_path.exists()

    def test_save_to_file_with_filtering(self, tmp_path: Path) -> None:
        """Test save_to_file respects severity filtering."""
        generator = ReportGenerator()
        findings = [
            create_finding(Severity.CRITICAL, finding_id="c1"),
            create_finding(Severity.LOW, finding_id="l1"),
        ]
        report = create_report(findings=findings)
        file_path = tmp_path / "report.json"

        generator.save_to_file(
            report, file_path, min_severity=Severity.HIGH
        )

        content = file_path.read_text()
        data = json.loads(content)
        assert data["summary"]["total_findings"] == 1
        assert data["findings"][0]["severity"] == "critical"

    def test_get_formatter(self) -> None:
        """Test get_formatter method."""
        generator = ReportGenerator()

        formatter = generator.get_formatter("markdown")

        assert isinstance(formatter, MarkdownFormatter)


class TestExtensionMapping:
    """Tests for file extension to format mapping."""

    def test_json_extension(self) -> None:
        """Test .json maps to json format."""
        assert EXTENSION_TO_FORMAT[".json"] == "json"

    def test_md_extension(self) -> None:
        """Test .md maps to markdown format."""
        assert EXTENSION_TO_FORMAT[".md"] == "markdown"

    def test_markdown_extension(self) -> None:
        """Test .markdown maps to markdown format."""
        assert EXTENSION_TO_FORMAT[".markdown"] == "markdown"

    def test_html_extension(self) -> None:
        """Test .html maps to html format."""
        assert EXTENSION_TO_FORMAT[".html"] == "html"

    def test_htm_extension(self) -> None:
        """Test .htm maps to html format."""
        assert EXTENSION_TO_FORMAT[".htm"] == "html"

    def test_txt_extension(self) -> None:
        """Test .txt maps to console format."""
        assert EXTENSION_TO_FORMAT[".txt"] == "console"

    def test_sarif_extension(self) -> None:
        """Test .sarif maps to sarif format."""
        assert EXTENSION_TO_FORMAT[".sarif"] == "sarif"

    def test_sarif_json_extension(self) -> None:
        """Test .sarif.json maps to sarif format."""
        assert EXTENSION_TO_FORMAT[".sarif.json"] == "sarif"


class TestGlobalReportGenerator:
    """Tests for global report_generator instance."""

    def test_global_instance_exists(self) -> None:
        """Test global instance is available."""
        assert report_generator is not None

    def test_global_instance_type(self) -> None:
        """Test global instance is ReportGenerator."""
        assert isinstance(report_generator, ReportGenerator)

    def test_global_instance_default_format(self) -> None:
        """Test global instance has json default format."""
        assert report_generator.default_format == "json"


class TestFormatterRegistry:
    """Tests for FORMATTERS registry."""

    def test_all_formats_registered(self) -> None:
        """Test all expected formats are in registry."""
        expected = {"json", "markdown", "md", "html", "console", "sarif"}
        assert expected.issubset(set(FORMATTERS.keys()))

    def test_formatter_classes(self) -> None:
        """Test correct formatter classes are registered."""
        assert FORMATTERS["json"] == JSONFormatter
        assert FORMATTERS["markdown"] == MarkdownFormatter
        assert FORMATTERS["md"] == MarkdownFormatter
        assert FORMATTERS["html"] == HTMLFormatter
        assert FORMATTERS["console"] == ConsoleFormatter
        assert FORMATTERS["sarif"] == SARIFFormatter
