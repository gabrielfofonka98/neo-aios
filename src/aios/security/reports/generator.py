"""Report generator for security scan results.

This module provides the ReportGenerator class that coordinates
report generation in multiple formats with support for filtering,
customization, and file output.

Example:
    >>> from aios.security.reports import ReportGenerator
    >>> generator = ReportGenerator()
    >>> markdown = generator.generate(report, "markdown")
    >>> generator.save_to_file(report, "/path/to/report.md")
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from aios.security.reports.formats import FORMATTERS
from aios.security.reports.formats import ReportFormatter
from aios.security.reports.formats import get_formatter

if TYPE_CHECKING:
    from aios.security.models import SecurityReport
    from aios.security.models import Severity


# File extension to format mapping
EXTENSION_TO_FORMAT: dict[str, str] = {
    ".json": "json",
    ".md": "markdown",
    ".markdown": "markdown",
    ".html": "html",
    ".htm": "html",
    ".txt": "console",
    ".sarif": "sarif",
    ".sarif.json": "sarif",
}


class ReportGenerator:
    """Generates security reports in various formats.

    The ReportGenerator provides a high-level interface for generating
    formatted reports from SecurityReport objects. It supports multiple
    output formats, severity filtering, and file output with automatic
    format detection.

    Attributes:
        default_format: The default output format.

    Example:
        >>> from aios.security.reports import ReportGenerator
        >>> generator = ReportGenerator(default_format="markdown")
        >>> # Generate as string
        >>> markdown = generator.generate(report, "markdown")
        >>> # Save to file with auto-detected format
        >>> generator.save_to_file(report, "/path/to/report.html")
    """

    def __init__(
        self,
        default_format: str = "json",
    ) -> None:
        """Initialize the report generator.

        Args:
            default_format: Default format when none is specified.

        Raises:
            ValueError: If the default format is not recognized.
        """
        if default_format.lower() not in FORMATTERS:
            available = ", ".join(sorted(FORMATTERS.keys()))
            raise ValueError(
                f"Unknown format '{default_format}'. Available: {available}"
            )
        self._default_format = default_format.lower()

    @property
    def default_format(self) -> str:
        """Return the default output format."""
        return self._default_format

    @property
    def available_formats(self) -> list[str]:
        """Return list of available format names."""
        return sorted(FORMATTERS.keys())

    def generate(
        self,
        report: SecurityReport,
        format_name: str | None = None,
        *,
        min_severity: Severity | None = None,
        include_recommendations: bool = True,
    ) -> str:
        """Generate a formatted report.

        Args:
            report: The security report to format.
            format_name: Output format (json, markdown, html, console, sarif).
                        If None, uses the default format.
            min_severity: Minimum severity to include in the report.
                         Findings with lower severity are filtered out.
            include_recommendations: Whether to include fix recommendations.

        Returns:
            The formatted report as a string.

        Raises:
            ValueError: If the format name is not recognized.

        Example:
            >>> markdown = generator.generate(report, "markdown")
            >>> # Filter to only critical and high
            >>> critical_only = generator.generate(
            ...     report, "json", min_severity=Severity.HIGH
            ... )
        """
        format_key = (format_name or self._default_format).lower()
        formatter = get_formatter(format_key)

        return formatter.format(
            report,
            min_severity=min_severity,
            include_recommendations=include_recommendations,
        )

    def generate_json(
        self,
        report: SecurityReport,
        *,
        min_severity: Severity | None = None,
        include_recommendations: bool = True,
    ) -> str:
        """Generate a JSON report.

        Convenience method for JSON output.

        Args:
            report: The security report.
            min_severity: Minimum severity to include.
            include_recommendations: Whether to include recommendations.

        Returns:
            JSON string representation.
        """
        return self.generate(
            report,
            "json",
            min_severity=min_severity,
            include_recommendations=include_recommendations,
        )

    def generate_markdown(
        self,
        report: SecurityReport,
        *,
        min_severity: Severity | None = None,
        include_recommendations: bool = True,
    ) -> str:
        """Generate a Markdown report.

        Convenience method for Markdown output.

        Args:
            report: The security report.
            min_severity: Minimum severity to include.
            include_recommendations: Whether to include recommendations.

        Returns:
            Markdown string representation.
        """
        return self.generate(
            report,
            "markdown",
            min_severity=min_severity,
            include_recommendations=include_recommendations,
        )

    def generate_html(
        self,
        report: SecurityReport,
        *,
        min_severity: Severity | None = None,
        include_recommendations: bool = True,
    ) -> str:
        """Generate an HTML report.

        Convenience method for HTML output.

        Args:
            report: The security report.
            min_severity: Minimum severity to include.
            include_recommendations: Whether to include recommendations.

        Returns:
            HTML string representation.
        """
        return self.generate(
            report,
            "html",
            min_severity=min_severity,
            include_recommendations=include_recommendations,
        )

    def generate_console(
        self,
        report: SecurityReport,
        *,
        min_severity: Severity | None = None,
        include_recommendations: bool = True,
    ) -> str:
        """Generate a console report.

        Convenience method for terminal output with ANSI colors.

        Args:
            report: The security report.
            min_severity: Minimum severity to include.
            include_recommendations: Whether to include recommendations.

        Returns:
            Console-formatted string.
        """
        return self.generate(
            report,
            "console",
            min_severity=min_severity,
            include_recommendations=include_recommendations,
        )

    def generate_sarif(
        self,
        report: SecurityReport,
        *,
        min_severity: Severity | None = None,
    ) -> str:
        """Generate a SARIF report.

        Convenience method for SARIF output (IDE integration).

        Args:
            report: The security report.
            min_severity: Minimum severity to include.

        Returns:
            SARIF JSON string.
        """
        return self.generate(
            report,
            "sarif",
            min_severity=min_severity,
            include_recommendations=True,  # SARIF always includes recommendations
        )

    def save_to_file(
        self,
        report: SecurityReport,
        file_path: str | Path,
        format_name: str | None = None,
        *,
        min_severity: Severity | None = None,
        include_recommendations: bool = True,
    ) -> Path:
        """Save a formatted report to a file.

        The format can be specified explicitly or inferred from the
        file extension. If the format cannot be determined, uses
        the default format.

        Args:
            report: The security report.
            file_path: Path to save the report to.
            format_name: Output format. If None, inferred from extension.
            min_severity: Minimum severity to include.
            include_recommendations: Whether to include recommendations.

        Returns:
            The Path to the saved file.

        Raises:
            ValueError: If the format cannot be determined.
            OSError: If the file cannot be written.

        Example:
            >>> # Format inferred from extension
            >>> generator.save_to_file(report, "/path/to/report.html")
            >>> # Explicit format
            >>> generator.save_to_file(report, "/path/to/output", format_name="json")
        """
        path = Path(file_path)

        # Determine format
        if format_name is None:
            format_name = self._infer_format_from_path(path)
            if format_name is None:
                format_name = self._default_format

        # Generate content
        content = self.generate(
            report,
            format_name,
            min_severity=min_severity,
            include_recommendations=include_recommendations,
        )

        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        path.write_text(content, encoding="utf-8")

        return path

    def _infer_format_from_path(self, path: Path) -> str | None:
        """Infer format from file path extension.

        Args:
            path: The file path.

        Returns:
            The format name, or None if cannot be inferred.
        """
        # Check for compound extensions like .sarif.json
        name = path.name.lower()
        for ext, fmt in EXTENSION_TO_FORMAT.items():
            if name.endswith(ext):
                return fmt

        # Check single extension
        suffix = path.suffix.lower()
        return EXTENSION_TO_FORMAT.get(suffix)

    def get_formatter(self, format_name: str) -> ReportFormatter:
        """Get a formatter instance by name.

        Useful for advanced customization or direct formatter access.

        Args:
            format_name: The format name.

        Returns:
            A ReportFormatter instance.

        Raises:
            ValueError: If the format is not recognized.
        """
        return get_formatter(format_name)


# Global generator instance with default configuration
report_generator = ReportGenerator()


__all__ = [
    "EXTENSION_TO_FORMAT",
    "ReportGenerator",
    "report_generator",
]
