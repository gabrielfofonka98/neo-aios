"""Base validator protocol and abstract class.

This module provides the base class and protocol for security validators.
All security validators should inherit from BaseValidator and implement
the validate_content method.

Example:
    >>> from aios.security.validators.base import BaseValidator
    >>> from aios.security.models import SecurityFinding, Severity, FindingCategory
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
    ...         # Implementation here
    ...         return []
"""

import time
from abc import ABC
from abc import abstractmethod
from pathlib import Path
from typing import Protocol
from typing import runtime_checkable

from aios.security.models import SecurityFinding
from aios.security.models import ValidatorResult


@runtime_checkable
class SecurityValidator(Protocol):
    """Protocol for security validators.

    This protocol defines the interface that all security validators must implement.
    Using Protocol allows for duck typing while still having type checking support.
    """

    @property
    def id(self) -> str:
        """Unique validator identifier."""
        ...

    @property
    def name(self) -> str:
        """Human-readable name."""
        ...

    @property
    def description(self) -> str:
        """What this validator checks for."""
        ...

    def validate(self, path: Path) -> ValidatorResult:
        """Run validation on path (file or directory)."""
        ...

    def validate_content(self, content: str, file_path: str) -> list[SecurityFinding]:
        """Validate content directly."""
        ...


class BaseValidator(ABC):
    """Abstract base class for validators.

    Provides common functionality for file traversal and result creation.
    Subclasses only need to implement the validate_content method.

    Attributes:
        id: Unique identifier for this validator (abstract).
        name: Human-readable name (abstract).
        description: What this validator checks for (abstract).
        file_extensions: File extensions this validator applies to.
    """

    @property
    @abstractmethod
    def id(self) -> str:
        """Unique validator identifier.

        Should be in the format: sec-{category}-{name}
        Example: sec-xss-innerHTML, sec-injection-sql
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable validator name."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Description of what this validator checks for."""
        pass

    @property
    def file_extensions(self) -> list[str]:
        """File extensions this validator applies to.

        Override this property to change which files are scanned.
        Default is TypeScript/JavaScript files.

        Returns:
            List of file extensions (including the dot).
        """
        return [".ts", ".tsx", ".js", ".jsx"]

    def validate(self, path: Path) -> ValidatorResult:
        """Run validation on path.

        Handles both single files and directories. For directories,
        recursively scans all files matching the file_extensions.

        Args:
            path: File or directory path to validate.

        Returns:
            ValidatorResult with findings and execution metadata.
        """
        start_time = time.time()

        findings: list[SecurityFinding] = []
        files_scanned = 0

        try:
            if path.is_file():
                if self._should_scan_file(path):
                    content = path.read_text(encoding="utf-8")
                    findings.extend(self.validate_content(content, str(path)))
                    files_scanned = 1
            elif path.is_dir():
                for file_path in self._get_files(path):
                    try:
                        content = file_path.read_text(encoding="utf-8")
                        findings.extend(self.validate_content(content, str(file_path)))
                        files_scanned += 1
                    except (OSError, UnicodeDecodeError):
                        # Skip files that can't be read
                        continue

        except Exception as e:
            return ValidatorResult(
                validator_id=self.id,
                validator_name=self.name,
                error=str(e),
                files_scanned=files_scanned,
                scan_duration_ms=int((time.time() - start_time) * 1000),
            )

        return ValidatorResult(
            validator_id=self.id,
            validator_name=self.name,
            findings=findings,
            files_scanned=files_scanned,
            scan_duration_ms=int((time.time() - start_time) * 1000),
        )

    @abstractmethod
    def validate_content(self, content: str, file_path: str) -> list[SecurityFinding]:
        """Validate content - must be implemented by subclasses.

        This is the core method where the actual security check logic lives.
        Implementations should analyze the content and return any findings.

        Args:
            content: The file content to validate.
            file_path: Path to the file (for reporting).

        Returns:
            List of SecurityFinding objects for any issues found.
        """
        pass

    def _should_scan_file(self, path: Path) -> bool:
        """Check if file should be scanned.

        Args:
            path: Path to the file.

        Returns:
            True if file extension matches, False otherwise.
        """
        return path.suffix in self.file_extensions

    def _get_files(self, directory: Path) -> list[Path]:
        """Get all scannable files in directory.

        Recursively finds all files matching the file_extensions.

        Args:
            directory: Directory to search.

        Returns:
            List of file paths to scan.
        """
        files: list[Path] = []
        for ext in self.file_extensions:
            files.extend(directory.rglob(f"*{ext}"))
        return files

    def __repr__(self) -> str:
        """String representation of the validator."""
        return f"{self.__class__.__name__}(id={self.id!r})"
