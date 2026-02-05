"""Rate limiting validator.

This module provides the RateLimitValidator that detects endpoints
that may be missing rate limiting protection.

Detects:
- Authentication endpoints without rate limiting
- POST endpoints without throttling
- Password reset endpoints
- Signup/registration endpoints

Example:
    >>> from aios.security.validators.regex.ratelimit import RateLimitValidator
    >>> from pathlib import Path
    >>>
    >>> validator = RateLimitValidator()
    >>> result = validator.validate(Path("src/"))
    >>> print(f"Found {len(result.findings)} rate limit issues")
"""

from aios.security.models import FindingCategory
from aios.security.validators.regex.base import RegexValidator
from aios.security.validators.regex.patterns import RATE_LIMIT_PATTERNS
from aios.security.validators.regex.patterns import PatternDefinition


class RateLimitValidator(RegexValidator):
    """Validator for missing rate limiting.

    Checks for endpoints that are commonly targeted by brute force
    or denial of service attacks and should have rate limiting.

    Patterns detected:
    - Authentication endpoints (/login, /signin, /auth)
    - POST API endpoints
    - Password reset endpoints
    - Signup/registration endpoints

    Note: This validator has lower confidence as it cannot determine
    if rate limiting is applied at a different layer (e.g., middleware,
    reverse proxy, or cloud provider).
    """

    @property
    def id(self) -> str:
        """Return validator ID."""
        return "sec-rate-limit-tester"

    @property
    def name(self) -> str:
        """Return validator name."""
        return "Rate Limiting Tester"

    @property
    def description(self) -> str:
        """Return validator description."""
        return (
            "Identifies endpoints that may lack rate limiting protection, "
            "including authentication, password reset, and registration endpoints."
        )

    @property
    def category(self) -> FindingCategory:
        """Return default finding category."""
        return FindingCategory.ACCESS_CONTROL

    @property
    def patterns(self) -> list[PatternDefinition]:
        """Return rate limiting patterns."""
        return RATE_LIMIT_PATTERNS

    @property
    def file_extensions(self) -> list[str]:
        """Return file extensions to scan.

        Focuses on route definition files.
        """
        return [
            ".ts",
            ".tsx",
            ".js",
            ".jsx",
            ".mjs",
            ".cjs",
            ".py",
        ]
