"""Error and information leak validator.

This module provides the ErrorLeakValidator that detects potential
information leakage through error messages and debug output.

Detects:
- Stack traces exposed to clients
- Verbose error responses
- Debug mode enabled
- SQL error messages exposed
- Internal file paths exposed

Example:
    >>> from aios.security.validators.regex.errors import ErrorLeakValidator
    >>> from pathlib import Path
    >>>
    >>> validator = ErrorLeakValidator()
    >>> result = validator.validate(Path("src/"))
    >>> print(f"Found {len(result.findings)} error leak issues")
"""

from aios.security.models import FindingCategory
from aios.security.validators.regex.base import RegexValidator
from aios.security.validators.regex.patterns import ERROR_PATTERNS
from aios.security.validators.regex.patterns import PatternDefinition


class ErrorLeakValidator(RegexValidator):
    """Validator for error and information leak issues.

    Checks for patterns that may expose sensitive information
    through error messages, debug output, or verbose responses.

    Patterns detected:
    - Stack trace exposure
    - Verbose error responses
    - Debug mode enabled
    - SQL error messages
    - Internal file paths
    """

    @property
    def id(self) -> str:
        """Return validator ID."""
        return "sec-error-leak-detector"

    @property
    def name(self) -> str:
        """Return validator name."""
        return "Error & Info Leak Detector"

    @property
    def description(self) -> str:
        """Return validator description."""
        return (
            "Detects verbose errors returned to clients, stack traces in responses, "
            "SQL error exposure, and internal path disclosure."
        )

    @property
    def category(self) -> FindingCategory:
        """Return default finding category."""
        return FindingCategory.DATA_EXPOSURE

    @property
    def patterns(self) -> list[PatternDefinition]:
        """Return error leak patterns."""
        return ERROR_PATTERNS

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
            ".py",
            ".json",
            ".yaml",
            ".yml",
            ".env",
        ]
