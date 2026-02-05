"""Regex-based security validators.

This package provides validators that use regex pattern matching to detect
security issues in code. These validators are fast and deterministic.

Validators:
    - CORSValidator: CORS and CSRF misconfigurations
    - HeadersValidator: Security header issues
    - ErrorLeakValidator: Information disclosure through errors
    - RateLimitValidator: Missing rate limiting

Base Classes:
    - RegexValidator: Base class for regex-based validators
    - PatternDefinition: Definition of security patterns

Example:
    >>> from aios.security.validators.regex import CORSValidator, HeadersValidator
    >>> from aios.security.validators import validator_registry
    >>>
    >>> # Register validators
    >>> validator_registry.register(CORSValidator())
    >>> validator_registry.register(HeadersValidator())
    >>>
    >>> # Run validation
    >>> from pathlib import Path
    >>> cors = CORSValidator()
    >>> result = cors.validate(Path("src/"))
"""

from aios.security.validators.regex.base import RegexValidator
from aios.security.validators.regex.cors import CORSValidator
from aios.security.validators.regex.errors import ErrorLeakValidator
from aios.security.validators.regex.headers import HeadersValidator
from aios.security.validators.regex.patterns import ALL_PATTERNS
from aios.security.validators.regex.patterns import CORS_PATTERNS
from aios.security.validators.regex.patterns import ERROR_PATTERNS
from aios.security.validators.regex.patterns import HEADERS_PATTERNS
from aios.security.validators.regex.patterns import RATE_LIMIT_PATTERNS
from aios.security.validators.regex.patterns import PatternDefinition
from aios.security.validators.regex.ratelimit import RateLimitValidator

__all__ = [
    "ALL_PATTERNS",
    "CORS_PATTERNS",
    "ERROR_PATTERNS",
    "HEADERS_PATTERNS",
    "RATE_LIMIT_PATTERNS",
    "CORSValidator",
    "ErrorLeakValidator",
    "HeadersValidator",
    "PatternDefinition",
    "RateLimitValidator",
    "RegexValidator",
]


def register_all_regex_validators() -> None:
    """Register all regex validators in the global registry.

    Convenience function to register all validators at once.

    Example:
        >>> from aios.security.validators.regex import register_all_regex_validators
        >>> register_all_regex_validators()
    """
    from aios.security.validators.registry import validator_registry

    validator_registry.register(CORSValidator())
    validator_registry.register(HeadersValidator())
    validator_registry.register(ErrorLeakValidator())
    validator_registry.register(RateLimitValidator())
