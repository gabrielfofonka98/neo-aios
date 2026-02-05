"""Security report generation module.

This package provides report generation capabilities for security scan results,
supporting multiple output formats including JSON, Markdown, HTML, Console, and SARIF.

The main entry point is the ReportGenerator class, which coordinates
format selection, filtering, and output.

Formats:
    - **JSON**: Structured data for programmatic access
    - **Markdown**: Human-readable documentation
    - **HTML**: Visual reports with inline CSS
    - **Console**: Terminal output with ANSI colors
    - **SARIF**: IDE integration (VS Code, GitHub Security)

Example:
    >>> from aios.security.reports import ReportGenerator, report_generator
    >>> # Use global instance
    >>> markdown = report_generator.generate(report, "markdown")
    >>> # Or create custom instance
    >>> generator = ReportGenerator(default_format="html")
    >>> generator.save_to_file(report, "/path/to/report.html")

Example with filtering:
    >>> from aios.security.models import Severity
    >>> # Only include HIGH and CRITICAL findings
    >>> filtered = generator.generate(report, "json", min_severity=Severity.HIGH)
"""

from aios.security.reports.formats import FORMATTERS
from aios.security.reports.formats import SEVERITY_ORDER
from aios.security.reports.formats import SEVERITY_STYLES
from aios.security.reports.formats import ConsoleFormatter
from aios.security.reports.formats import HTMLFormatter
from aios.security.reports.formats import JSONFormatter
from aios.security.reports.formats import MarkdownFormatter
from aios.security.reports.formats import ReportFormatter
from aios.security.reports.formats import SARIFFormatter
from aios.security.reports.formats import get_formatter
from aios.security.reports.generator import EXTENSION_TO_FORMAT
from aios.security.reports.generator import ReportGenerator
from aios.security.reports.generator import report_generator

__all__ = [
    "EXTENSION_TO_FORMAT",
    "FORMATTERS",
    "SEVERITY_ORDER",
    "SEVERITY_STYLES",
    "ConsoleFormatter",
    "HTMLFormatter",
    "JSONFormatter",
    "MarkdownFormatter",
    "ReportFormatter",
    "ReportGenerator",
    "SARIFFormatter",
    "get_formatter",
    "report_generator",
]
