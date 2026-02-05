"""CORS and CSRF security validator.

This module provides the CORSValidator that detects CORS misconfigurations
and CSRF vulnerabilities in code.

Detects:
- Access-Control-Allow-Origin: * (wildcard)
- Origin reflection without validation
- Credentials with permissive origins
- CSRF protection disabled

Example:
    >>> from aios.security.validators.regex.cors import CORSValidator
    >>> from pathlib import Path
    >>>
    >>> validator = CORSValidator()
    >>> result = validator.validate(Path("src/"))
    >>> print(f"Found {len(result.findings)} CORS issues")
"""

from aios.security.models import FindingCategory
from aios.security.validators.regex.base import RegexValidator
from aios.security.validators.regex.patterns import CORS_PATTERNS
from aios.security.validators.regex.patterns import PatternDefinition


class CORSValidator(RegexValidator):
    """Validator for CORS and CSRF security issues.

    Checks for common CORS misconfigurations that can lead to
    cross-origin attacks and data exposure.

    Patterns detected:
    - Wildcard Access-Control-Allow-Origin (*)
    - Unvalidated origin reflection
    - Credentials enabled with permissive origins
    - CSRF protection explicitly disabled
    """

    @property
    def id(self) -> str:
        """Return validator ID."""
        return "sec-cors-csrf-checker"

    @property
    def name(self) -> str:
        """Return validator name."""
        return "CORS & CSRF Checker"

    @property
    def description(self) -> str:
        """Return validator description."""
        return (
            "Detects CORS misconfigurations (wildcard origins, origin reflection, "
            "credentials with permissive settings) and CSRF protection issues."
        )

    @property
    def category(self) -> FindingCategory:
        """Return default finding category."""
        return FindingCategory.CONFIG

    @property
    def patterns(self) -> list[PatternDefinition]:
        """Return CORS-related patterns."""
        return CORS_PATTERNS

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
        ]
