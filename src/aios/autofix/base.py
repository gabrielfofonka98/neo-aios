"""Base fixer abstract class.

This module provides the abstract base class for all auto-fixers in the
framework. Concrete fixers must implement the abstract methods to handle
specific types of security findings.

Example:
    >>> from aios.autofix.base import BaseFixer
    >>> from aios.security.models import SecurityFinding
    >>>
    >>> class MyFixer(BaseFixer):
    ...     @property
    ...     def fixer_id(self) -> str:
    ...         return "my-fixer"
    ...
    ...     @property
    ...     def name(self) -> str:
    ...         return "My Custom Fixer"
    ...
    ...     def can_fix(self, finding: SecurityFinding) -> bool:
    ...         return finding.category.value == "xss"
    ...
    ...     def generate_fix(self, finding: SecurityFinding) -> FixSuggestion:
    ...         # Generate fix logic
    ...         pass
"""

import difflib
import shutil
from abc import ABC
from abc import abstractmethod
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from aios.autofix.models import FileDiff
from aios.autofix.models import FixConfidence
from aios.autofix.models import FixerCapability
from aios.autofix.models import FixResult
from aios.autofix.models import FixStatus
from aios.autofix.models import FixSuggestion

if TYPE_CHECKING:
    from aios.security.models import SecurityFinding


class BaseFixer(ABC):
    """Abstract base class for security finding fixers.

    All concrete fixers must inherit from this class and implement
    the abstract methods. The base class provides common functionality
    for applying fixes, generating diffs, and rollback support.

    Attributes:
        backup_dir: Directory for storing backup files.
    """

    def __init__(self, backup_dir: Path | None = None) -> None:
        """Initialize the fixer.

        Args:
            backup_dir: Optional directory for backup files.
                       Defaults to .aios/backups in current directory.
        """
        self._backup_dir = backup_dir or Path(".aios/backups")

    @property
    @abstractmethod
    def fixer_id(self) -> str:
        """Unique identifier for this fixer.

        Returns:
            A unique string identifier (e.g., "xss-sanitizer").
        """
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name for this fixer.

        Returns:
            A descriptive name (e.g., "XSS Sanitizer Fixer").
        """
        ...

    @property
    def description(self) -> str:
        """Description of what this fixer does.

        Returns:
            A description string. Defaults to empty string.
        """
        return ""

    @property
    def priority(self) -> int:
        """Priority of this fixer (higher = tried first).

        Returns:
            Priority value. Defaults to 100.
        """
        return 100

    @property
    def supported_categories(self) -> list[str]:
        """List of finding categories this fixer can handle.

        Returns:
            List of category strings. Empty list means any category.
        """
        return []

    @property
    def supported_validators(self) -> list[str]:
        """List of validator IDs this fixer can handle findings from.

        Returns:
            List of validator IDs. Empty list means any validator.
        """
        return []

    def get_capability(self) -> FixerCapability:
        """Get the capability descriptor for this fixer.

        Returns:
            FixerCapability describing what this fixer can do.
        """
        return FixerCapability(
            fixer_id=self.fixer_id,
            name=self.name,
            description=self.description,
            supported_categories=self.supported_categories,
            supported_validators=self.supported_validators,
            priority=self.priority,
        )

    @abstractmethod
    def can_fix(self, finding: "SecurityFinding") -> bool:
        """Check if this fixer can handle the given finding.

        Args:
            finding: The security finding to check.

        Returns:
            True if this fixer can generate a fix for the finding.
        """
        ...

    @abstractmethod
    def generate_fix(self, finding: "SecurityFinding") -> FixSuggestion:
        """Generate a fix suggestion for the finding.

        Args:
            finding: The security finding to fix.

        Returns:
            A FixSuggestion with the proposed fix.

        Raises:
            ValueError: If the fixer cannot handle this finding.
        """
        ...

    def apply_fix(
        self,
        finding: "SecurityFinding",
        dry_run: bool = True,
    ) -> FixResult:
        """Apply a fix to the source code.

        This method generates a fix suggestion and optionally applies it
        to the source file. In dry-run mode (default), no actual changes
        are made to the filesystem.

        Args:
            finding: The security finding to fix.
            dry_run: If True, only generate the diff without applying.
                    Defaults to True for safety.

        Returns:
            FixResult with the outcome of the fix operation.
        """
        # Validate and prepare fix
        prep_result = self._prepare_fix(finding)
        if prep_result is not None:
            return prep_result

        # Generate the fix suggestion (validated in _prepare_fix, so safe here)
        suggestion = self.generate_fix(finding)
        file_path = Path(finding.location.file_path)

        # Read and process file
        read_result = self._read_and_process(finding.id, suggestion, file_path)
        if isinstance(read_result, FixResult):
            return read_result

        _original_content, modified_content, diff = read_result

        # Dry-run mode: return without applying
        if dry_run:
            return FixResult(
                success=True,
                finding_id=finding.id,
                suggestion=suggestion,
                status=FixStatus.PENDING,
                diff=diff,
                file_path=file_path,
            )

        # Apply the fix to filesystem
        return self._write_fix(finding.id, suggestion, file_path, modified_content, diff)

    def _prepare_fix(
        self,
        finding: "SecurityFinding",
    ) -> FixResult | None:
        """Validate that the fix can be applied.

        Args:
            finding: The security finding to validate.

        Returns:
            FixResult if validation fails, None if validation passes.
        """
        if not self.can_fix(finding):
            return FixResult(
                success=False,
                finding_id=finding.id,
                suggestion=FixSuggestion(
                    old_code="",
                    new_code="",
                    explanation="Fixer cannot handle this finding",
                    confidence=FixConfidence.LOW,
                ),
                status=FixStatus.SKIPPED,
                error_message=f"Fixer {self.fixer_id} cannot fix finding {finding.id}",
            )

        # Try generating fix to validate it works
        try:
            self.generate_fix(finding)
        except Exception as e:
            return FixResult(
                success=False,
                finding_id=finding.id,
                suggestion=FixSuggestion(
                    old_code="",
                    new_code="",
                    explanation=f"Failed to generate fix: {e}",
                    confidence=FixConfidence.LOW,
                ),
                status=FixStatus.FAILED,
                error_message=str(e),
            )

        return None

    def _read_and_process(
        self,
        finding_id: str,
        suggestion: FixSuggestion,
        file_path: Path,
    ) -> FixResult | tuple[str, str, FileDiff]:
        """Read file and generate the modified content.

        Args:
            finding_id: ID of the finding being fixed.
            suggestion: The fix suggestion to apply.
            file_path: Path to the file.

        Returns:
            Either a FixResult (on error) or tuple of (original, modified, diff).
        """
        if not file_path.exists():
            return FixResult(
                success=False,
                finding_id=finding_id,
                suggestion=suggestion,
                status=FixStatus.FAILED,
                error_message=f"File not found: {file_path}",
                file_path=file_path,
            )

        try:
            original_content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            return FixResult(
                success=False,
                finding_id=finding_id,
                suggestion=suggestion,
                status=FixStatus.FAILED,
                error_message=f"Failed to read file: {e}",
                file_path=file_path,
            )

        modified_content = self._apply_suggestion(original_content, suggestion)
        diff = self._generate_diff(file_path, original_content, modified_content)

        return original_content, modified_content, diff

    def _write_fix(
        self,
        finding_id: str,
        suggestion: FixSuggestion,
        file_path: Path,
        modified_content: str,
        diff: FileDiff,
    ) -> FixResult:
        """Write the fix to the filesystem.

        Args:
            finding_id: ID of the finding being fixed.
            suggestion: The fix suggestion applied.
            file_path: Path to the file.
            modified_content: The modified file content.
            diff: The generated diff.

        Returns:
            FixResult indicating success or failure.
        """
        backup_path = self._create_backup(file_path)

        try:
            file_path.write_text(modified_content, encoding="utf-8")
            return FixResult(
                success=True,
                finding_id=finding_id,
                suggestion=suggestion,
                status=FixStatus.APPLIED,
                diff=diff,
                applied_at=datetime.now(),
                file_path=file_path,
                backup_path=backup_path,
            )
        except Exception as e:
            # Restore from backup on failure
            if backup_path and backup_path.exists():
                shutil.copy2(backup_path, file_path)
            return FixResult(
                success=False,
                finding_id=finding_id,
                suggestion=suggestion,
                status=FixStatus.FAILED,
                diff=diff,
                error_message=f"Failed to write file: {e}",
                file_path=file_path,
                backup_path=backup_path,
            )

    def rollback(self, result: FixResult) -> bool:
        """Rollback a previously applied fix.

        Args:
            result: The FixResult from a previous apply_fix call.

        Returns:
            True if rollback was successful, False otherwise.
        """
        if not result.can_rollback:
            return False

        if result.backup_path is None or result.file_path is None:
            return False

        try:
            shutil.copy2(result.backup_path, result.file_path)
            result.status = FixStatus.ROLLED_BACK
            return True
        except Exception:
            return False

    def _apply_suggestion(self, content: str, suggestion: FixSuggestion) -> str:
        """Apply a fix suggestion to content.

        Args:
            content: Original file content.
            suggestion: The fix suggestion to apply.

        Returns:
            Modified content with the fix applied.
        """
        # Simple string replacement
        # More sophisticated fixers can override this method
        return content.replace(suggestion.old_code, suggestion.new_code)

    def _generate_diff(
        self,
        file_path: Path,
        original: str,
        modified: str,
    ) -> FileDiff:
        """Generate a unified diff between original and modified content.

        Args:
            file_path: Path to the file.
            original: Original content.
            modified: Modified content.

        Returns:
            FileDiff with the diff information.
        """
        original_lines = original.splitlines(keepends=True)
        modified_lines = modified.splitlines(keepends=True)

        diff_lines = list(
            difflib.unified_diff(
                original_lines,
                modified_lines,
                fromfile=f"a/{file_path}",
                tofile=f"b/{file_path}",
            )
        )

        diff_text = "".join(diff_lines)

        # Count changed lines (lines starting with + or - but not ++ or --)
        line_changes = sum(
            1
            for line in diff_lines
            if (line.startswith("+") or line.startswith("-"))
            and not line.startswith("+++")
            and not line.startswith("---")
        )

        return FileDiff(
            file_path=file_path,
            original_content=original,
            modified_content=modified,
            diff_text=diff_text,
            line_changes=line_changes,
        )

    def _create_backup(self, file_path: Path) -> Path | None:
        """Create a backup of a file before modifying it.

        Args:
            file_path: Path to the file to backup.

        Returns:
            Path to the backup file, or None if backup failed.
        """
        try:
            self._backup_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{file_path.name}.{timestamp}.bak"
            backup_path = self._backup_dir / backup_name
            shutil.copy2(file_path, backup_path)
            return backup_path
        except Exception:
            return None
