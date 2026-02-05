"""Registry for security validators.

This module provides a central registry for managing security validators.
Validators can be registered, retrieved, and queried by ID or category.

Example:
    >>> from aios.security.validators.registry import ValidatorRegistry, validator_registry
    >>> from aios.security.validators.base import BaseValidator
    >>>
    >>> # Use the global registry
    >>> validator_registry.register(my_validator)
    >>> xss_validators = validator_registry.get_by_category("sec-xss")
    >>>
    >>> # Or create a custom registry
    >>> custom_registry = ValidatorRegistry()
    >>> custom_registry.register(my_validator)
"""


from aios.security.validators.base import SecurityValidator


class ValidatorRegistry:
    """Central registry for all security validators.

    Provides methods to register, unregister, and query validators.
    Supports filtering by ID prefix (category).

    Attributes:
        _validators: Internal dictionary mapping validator IDs to validators.
    """

    def __init__(self) -> None:
        """Initialize an empty validator registry."""
        self._validators: dict[str, SecurityValidator] = {}

    def register(self, validator: SecurityValidator) -> None:
        """Register a validator.

        If a validator with the same ID already exists, it will be replaced.

        Args:
            validator: The validator to register.
        """
        self._validators[validator.id] = validator

    def unregister(self, validator_id: str) -> bool:
        """Unregister a validator.

        Args:
            validator_id: ID of the validator to remove.

        Returns:
            True if validator was found and removed, False otherwise.
        """
        if validator_id in self._validators:
            del self._validators[validator_id]
            return True
        return False

    def get(self, validator_id: str) -> SecurityValidator | None:
        """Get validator by ID.

        Args:
            validator_id: The validator ID to look up.

        Returns:
            The validator if found, None otherwise.
        """
        return self._validators.get(validator_id)

    def get_all(self) -> list[SecurityValidator]:
        """Get all registered validators.

        Returns:
            List of all validators (not a copy, but a new list).
        """
        return list(self._validators.values())

    def get_by_category(self, category: str) -> list[SecurityValidator]:
        """Get validators by category prefix.

        Validators are categorized by their ID prefix.
        For example, 'sec-xss' matches validators like 'sec-xss-innerHTML'.

        Args:
            category: Category prefix to match (e.g., 'sec-xss').

        Returns:
            List of validators matching the category.
        """
        return [v for v in self._validators.values() if v.id.startswith(category)]

    def has(self, validator_id: str) -> bool:
        """Check if a validator is registered.

        Args:
            validator_id: The validator ID to check.

        Returns:
            True if validator is registered, False otherwise.
        """
        return validator_id in self._validators

    def clear(self) -> None:
        """Remove all registered validators."""
        self._validators.clear()

    @property
    def count(self) -> int:
        """Number of registered validators.

        Returns:
            Count of validators in the registry.
        """
        return len(self._validators)

    @property
    def ids(self) -> list[str]:
        """List of all validator IDs.

        Returns:
            List of validator ID strings.
        """
        return list(self._validators.keys())

    @property
    def categories(self) -> list[str]:
        """Get unique category prefixes.

        Extracts categories from validator IDs.
        Assumes IDs follow pattern: category-subcategory-name

        Returns:
            List of unique category prefixes.
        """
        categories: set[str] = set()
        for validator_id in self._validators:
            # Extract first two parts as category (e.g., 'sec-xss' from 'sec-xss-innerHTML')
            parts = validator_id.split("-")
            if len(parts) >= 2:
                categories.add(f"{parts[0]}-{parts[1]}")
            elif len(parts) == 1:
                categories.add(parts[0])
        return sorted(categories)

    def __repr__(self) -> str:
        """String representation of the registry."""
        return f"ValidatorRegistry(count={self.count})"

    def __len__(self) -> int:
        """Return number of validators."""
        return self.count

    def __contains__(self, validator_id: str) -> bool:
        """Check if validator ID is in registry."""
        return self.has(validator_id)

    def __iter__(self) -> "ValidatorRegistryIterator":
        """Iterate over validators."""
        return ValidatorRegistryIterator(self.get_all())


class ValidatorRegistryIterator:
    """Iterator for ValidatorRegistry."""

    def __init__(self, validators: list[SecurityValidator]) -> None:
        """Initialize iterator.

        Args:
            validators: List of validators to iterate.
        """
        self._validators = validators
        self._index = 0

    def __iter__(self) -> "ValidatorRegistryIterator":
        """Return self as iterator."""
        return self

    def __next__(self) -> SecurityValidator:
        """Get next validator.

        Returns:
            Next validator in the list.

        Raises:
            StopIteration: When no more validators.
        """
        if self._index >= len(self._validators):
            raise StopIteration
        validator = self._validators[self._index]
        self._index += 1
        return validator


# Global registry instance
validator_registry = ValidatorRegistry()
