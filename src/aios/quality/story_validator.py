"""Story validation enforcement."""

from __future__ import annotations

import re
from dataclasses import dataclass
from dataclasses import field
from enum import StrEnum
from pathlib import Path


class ValidationSeverity(StrEnum):
    """Severity of validation issues."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True)
class ValidationIssue:
    """A single validation issue."""

    severity: ValidationSeverity
    rule: str
    message: str
    line: int | None = None


@dataclass
class ValidationResult:
    """Result of story validation."""

    path: str
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not any(i.severity == ValidationSeverity.ERROR for i in self.issues)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == ValidationSeverity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == ValidationSeverity.WARNING)

    @property
    def summary(self) -> str:
        return f"{self.error_count} errors, {self.warning_count} warnings"


# Patterns
USER_STORY_PATTERN = re.compile(
    r"[Cc]omo\s+.+,\s+(?:eu\s+)?quero\s+.+",
    re.IGNORECASE,
)
ACCEPTANCE_CRITERIA_PATTERN = re.compile(
    r"##?\s*(?:[Cc]rit[eé]rios?\s+de\s+[Aa]ceita[cç][aã]o|[Aa]cceptance\s+[Cc]riteria)",
    re.IGNORECASE,
)
DOD_PATTERN = re.compile(
    r"##?\s*(?:[Dd]efini[cç][aã]o\s+de\s+[Dd]one|[Dd]efinition\s+of\s+[Dd]one|DoD)",
    re.IGNORECASE,
)
PRIORITY_PATTERN = re.compile(
    r"(?:[Pp]rioridade|[Pp]riority)\s*:\s*(must|should|could|wont|high|medium|low|critical)",
    re.IGNORECASE,
)


class StoryValidator:
    """Validates user story format and content."""

    def validate(self, path: str) -> ValidationResult:
        """Validate a story file."""
        story_path = Path(path)
        result = ValidationResult(path=path)

        if not story_path.exists():
            result.issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    rule="file_exists",
                    message=f"Story file not found: {path}",
                )
            )
            return result

        try:
            content = story_path.read_text()
        except OSError as e:
            result.issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    rule="file_readable",
                    message=f"Cannot read story file: {e}",
                )
            )
            return result

        lines = content.split("\n")

        # Rule 1: User story format
        self._check_user_story_format(content, result)

        # Rule 2: Acceptance criteria
        self._check_acceptance_criteria(content, lines, result)

        # Rule 3: Definition of Done
        self._check_dod(content, result)

        # Rule 4: Priority defined
        self._check_priority(content, result)

        # Rule 5: Title (H1 heading)
        self._check_title(lines, result)

        # Rule 6: Not empty
        self._check_not_empty(content, result)

        return result

    def validate_directory(self, directory: str) -> list[ValidationResult]:
        """Validate all story files in a directory."""
        dir_path = Path(directory)
        results: list[ValidationResult] = []

        for story_file in sorted(dir_path.glob("story-*.md")):
            results.append(self.validate(str(story_file)))

        return results

    def _check_user_story_format(
        self, content: str, result: ValidationResult
    ) -> None:
        """Check for 'Como [persona], quero [acao]' format."""
        if not USER_STORY_PATTERN.search(content):
            result.issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    rule="user_story_format",
                    message="Missing user story format: 'Como [persona], quero [acao]'",
                )
            )

    def _check_acceptance_criteria(
        self, content: str, lines: list[str], result: ValidationResult
    ) -> None:
        """Check for acceptance criteria section."""
        if not ACCEPTANCE_CRITERIA_PATTERN.search(content):
            result.issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    rule="acceptance_criteria",
                    message="Missing acceptance criteria section",
                )
            )
            return

        # Check for at least one criterion (checkbox or bullet)
        in_ac = False
        has_criteria = False
        for line in lines:
            if ACCEPTANCE_CRITERIA_PATTERN.search(line):
                in_ac = True
                continue
            if in_ac:
                if line.startswith("#"):
                    break
                if re.match(r"\s*[-*]\s+\[[ x]\]", line) or re.match(
                    r"\s*[-*]\s+", line
                ):
                    has_criteria = True
                    break

        if not has_criteria:
            result.issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    rule="acceptance_criteria_items",
                    message="Acceptance criteria section has no items",
                )
            )

    def _check_dod(self, content: str, result: ValidationResult) -> None:
        """Check for Definition of Done section."""
        if not DOD_PATTERN.search(content):
            result.issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    rule="definition_of_done",
                    message="Missing Definition of Done section",
                )
            )

    def _check_priority(self, content: str, result: ValidationResult) -> None:
        """Check for priority field."""
        if not PRIORITY_PATTERN.search(content):
            result.issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    rule="priority",
                    message="Missing priority field",
                )
            )

    def _check_title(self, lines: list[str], result: ValidationResult) -> None:
        """Check for H1 title."""
        has_title = any(line.startswith("# ") for line in lines[:5])
        if not has_title:
            result.issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    rule="title",
                    message="Missing H1 title in first 5 lines",
                )
            )

    def _check_not_empty(self, content: str, result: ValidationResult) -> None:
        """Check file is not empty."""
        if len(content.strip()) < 20:
            result.issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    rule="not_empty",
                    message="Story file is too short (< 20 chars)",
                )
            )
