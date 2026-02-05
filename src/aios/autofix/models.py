"""Auto-fix models.

This module provides data models for the auto-fix framework, including
fix suggestions, results, and diff representations.

Example:
    >>> from aios.autofix.models import FixSuggestion, FixResult
    >>> suggestion = FixSuggestion(
    ...     old_code="user_input",
    ...     new_code="sanitize(user_input)",
    ...     explanation="Sanitize user input before use"
    ... )
    >>> result = FixResult(
    ...     success=True,
    ...     finding_id="xss-001",
    ...     suggestion=suggestion,
    ...     diff="- user_input\\n+ sanitize(user_input)"
    ... )
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from pydantic import Field


class FixStatus(Enum):
    """Status of a fix operation.

    Values:
        PENDING: Fix not yet applied.
        APPLIED: Fix successfully applied.
        FAILED: Fix application failed.
        ROLLED_BACK: Fix was rolled back.
        SKIPPED: Fix was skipped (e.g., manual intervention needed).
    """

    PENDING = "pending"
    APPLIED = "applied"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    SKIPPED = "skipped"


class FixConfidence(Enum):
    """Confidence level for a fix suggestion.

    Values:
        HIGH: Very confident fix will work correctly.
        MEDIUM: Reasonably confident, manual review recommended.
        LOW: Low confidence, requires careful review.
    """

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class FixSuggestion(BaseModel):
    """A suggested fix for a security finding.

    Contains the old code to replace, the new code to insert,
    and an explanation of why this fix addresses the issue.

    Attributes:
        old_code: The original code that should be replaced.
        new_code: The new code to insert.
        explanation: Human-readable explanation of the fix.
        confidence: How confident we are in this fix.
        requires_import: Optional import statement needed.
        context_lines_before: Lines of context before the change.
        context_lines_after: Lines of context after the change.
    """

    old_code: str
    new_code: str
    explanation: str
    confidence: FixConfidence = FixConfidence.HIGH
    requires_import: str | None = None
    context_lines_before: int = 3
    context_lines_after: int = 3


class FileDiff(BaseModel):
    """Represents a diff for a single file.

    Attributes:
        file_path: Path to the file being modified.
        original_content: The original file content.
        modified_content: The modified file content.
        diff_text: Unified diff text representation.
        line_changes: Number of lines changed (added + removed).
    """

    file_path: Path
    original_content: str
    modified_content: str
    diff_text: str
    line_changes: int = 0


class FixResult(BaseModel):
    """Result of applying a fix.

    Contains the outcome of a fix operation, including whether it
    succeeded, the diff of changes, and any error messages.

    Attributes:
        success: Whether the fix was successfully applied.
        finding_id: ID of the finding that was fixed.
        suggestion: The fix suggestion that was applied.
        status: Current status of the fix.
        diff: Optional diff showing the changes.
        error_message: Error message if fix failed.
        applied_at: When the fix was applied (None if not applied).
        file_path: Path to the file that was modified.
        backup_path: Path to backup file (for rollback support).
    """

    success: bool
    finding_id: str
    suggestion: FixSuggestion
    status: FixStatus = FixStatus.PENDING
    diff: FileDiff | None = None
    error_message: str | None = None
    applied_at: datetime | None = None
    file_path: Path | None = None
    backup_path: Path | None = None

    @property
    def can_rollback(self) -> bool:
        """Check if this fix can be rolled back."""
        return (
            self.status == FixStatus.APPLIED
            and self.backup_path is not None
            and self.backup_path.exists()
        )


class FixBatchResult(BaseModel):
    """Result of applying multiple fixes.

    Aggregates results from fixing multiple findings in a single operation.

    Attributes:
        total_findings: Total number of findings processed.
        successful: Number of fixes successfully applied.
        failed: Number of fixes that failed.
        skipped: Number of fixes that were skipped.
        results: Individual fix results.
        dry_run: Whether this was a dry-run (no actual changes).
        started_at: When the batch operation started.
        completed_at: When the batch operation completed.
    """

    total_findings: int = 0
    successful: int = 0
    failed: int = 0
    skipped: int = 0
    results: list[FixResult] = Field(default_factory=list)
    dry_run: bool = True
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: datetime | None = None

    def add_result(self, result: FixResult) -> None:
        """Add a fix result to the batch.

        Updates counters and appends the result to the list.

        Args:
            result: The fix result to add.
        """
        self.results.append(result)
        self.total_findings += 1

        if result.success:
            self.successful += 1
        elif result.status == FixStatus.SKIPPED:
            self.skipped += 1
        else:
            self.failed += 1

    @property
    def all_successful(self) -> bool:
        """Check if all fixes were successful."""
        return self.failed == 0 and self.skipped == 0

    def get_failed_results(self) -> list[FixResult]:
        """Get all failed fix results."""
        return [r for r in self.results if r.status == FixStatus.FAILED]

    def get_successful_results(self) -> list[FixResult]:
        """Get all successful fix results."""
        return [r for r in self.results if r.status == FixStatus.APPLIED]


class FixerCapability(BaseModel):
    """Describes what a fixer can handle.

    Used for fixer registration and matching.

    Attributes:
        fixer_id: Unique identifier for the fixer.
        name: Human-readable name.
        description: What this fixer does.
        supported_categories: Finding categories this fixer handles.
        supported_validators: Validator IDs this fixer can fix findings from.
        priority: Higher priority fixers are tried first (default 100).
        metadata: Additional fixer-specific metadata.
    """

    fixer_id: str
    name: str
    description: str
    supported_categories: list[str] = Field(default_factory=list)
    supported_validators: list[str] = Field(default_factory=list)
    priority: int = 100
    metadata: dict[str, Any] = Field(default_factory=dict)
