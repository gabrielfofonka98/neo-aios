"""Security validators package.

This package provides the framework for creating and managing security validators.

Exports:
    - BaseValidator: Abstract base class for validators
    - SecurityValidator: Protocol defining validator interface
    - ValidatorRegistry: Registry for managing validators
    - validator_registry: Global registry instance

For AST-based validators, import from aios.security.ast:
    - XSSValidator, JWTValidator, SecretValidator, InjectionValidator

Example:
    >>> from aios.security.validators import BaseValidator, validator_registry
    >>> from aios.security.models import SecurityFinding
    >>>
    >>> class MyValidator(BaseValidator):
    ...     @property
    ...     def id(self) -> str:
    ...         return "my-validator"
    ...
    ...     @property
    ...     def name(self) -> str:
    ...         return "My Validator"
    ...
    ...     @property
    ...     def description(self) -> str:
    ...         return "Checks for something"
    ...
    ...     def validate_content(self, content: str, file_path: str) -> list[SecurityFinding]:
    ...         return []
    >>>
    >>> validator_registry.register(MyValidator())
"""

from aios.security.validators.base import BaseValidator
from aios.security.validators.base import SecurityValidator
from aios.security.validators.registry import ValidatorRegistry
from aios.security.validators.registry import validator_registry

__all__ = [
    "BaseValidator",
    "SecurityValidator",
    "ValidatorRegistry",
    "register_default_validators",
    "validator_registry",
]


def register_default_validators() -> None:
    """Register all default AST validators in the global registry.

    This function registers the following validators:
    - XSSValidator (sec-xss-hunter)
    - JWTValidator (sec-jwt-auditor)
    - SecretValidator (sec-secret-scanner)
    - InjectionValidator (sec-injection-detector)

    Example:
        >>> from aios.security.validators import register_default_validators, validator_registry
        >>> register_default_validators()
        >>> print(validator_registry.count)
        4
    """
    # Import here to avoid circular imports
    from aios.security.ast.sql import InjectionValidator
    from aios.security.ast.typescript import JWTValidator
    from aios.security.ast.typescript import SecretValidator
    from aios.security.ast.typescript import XSSValidator

    validator_registry.register(XSSValidator())
    validator_registry.register(JWTValidator())
    validator_registry.register(SecretValidator())
    validator_registry.register(InjectionValidator())
