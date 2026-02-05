"""Security headers validator.

This module provides the HeadersValidator that checks for missing or
misconfigured security headers.

Detects:
- Content-Security-Policy issues
- Missing X-Frame-Options
- Missing/misconfigured HSTS
- Cookie security flags (httpOnly, secure, SameSite)

Example:
    >>> from aios.security.validators.regex.headers import HeadersValidator
    >>> from pathlib import Path
    >>>
    >>> validator = HeadersValidator()
    >>> result = validator.validate(Path("src/"))
    >>> print(f"Found {len(result.findings)} header issues")
"""

from aios.security.models import FindingCategory
from aios.security.validators.regex.base import RegexValidator
from aios.security.validators.regex.patterns import HEADERS_PATTERNS
from aios.security.validators.regex.patterns import PatternDefinition


class HeadersValidator(RegexValidator):
    """Validator for security header issues.

    Checks for missing or misconfigured security headers that can
    lead to various attacks like XSS, clickjacking, and session hijacking.

    Patterns detected:
    - Unsafe CSP directives (unsafe-inline, unsafe-dynamic)
    - X-Frame-Options configuration
    - HSTS configuration
    - Cookie flags (httpOnly, secure, SameSite)
    """

    @property
    def id(self) -> str:
        """Return validator ID."""
        return "sec-header-inspector"

    @property
    def name(self) -> str:
        """Return validator name."""
        return "Security Headers Inspector"

    @property
    def description(self) -> str:
        """Return validator description."""
        return (
            "Validates Content-Security-Policy, X-Frame-Options, HSTS, and "
            "cookie security attributes (httpOnly, secure, SameSite)."
        )

    @property
    def category(self) -> FindingCategory:
        """Return default finding category."""
        return FindingCategory.CONFIG

    @property
    def patterns(self) -> list[PatternDefinition]:
        """Return security header patterns."""
        return HEADERS_PATTERNS

    @property
    def file_extensions(self) -> list[str]:
        """Return file extensions to scan.

        Includes TypeScript/JavaScript and config files.
        """
        return [
            ".ts",
            ".tsx",
            ".js",
            ".jsx",
            ".mjs",
            ".cjs",
            ".json",
            ".yaml",
            ".yml",
            ".conf",
            ".config",
        ]
