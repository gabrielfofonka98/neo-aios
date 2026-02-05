"""Base class for regex-based security validators.

This module provides the RegexValidator abstract base class that handles
pattern compilation and matching. Concrete validators inherit from this
and define their specific patterns.

Example:
    >>> from aios.security.validators.regex.base import RegexValidator
    >>> from aios.security.validators.regex.patterns import PatternDefinition
    >>>
    >>> class MyValidator(RegexValidator):
    ...     @property
    ...     def id(self) -> str:
    ...         return "sec-my-validator"
    ...
    ...     @property
    ...     def name(self) -> str:
    ...         return "My Validator"
    ...
    ...     @property
    ...     def description(self) -> str:
    ...         return "Checks for something"
    ...
    ...     @property
    ...     def patterns(self) -> list[PatternDefinition]:
    ...         return [...]
"""

import re
from abc import abstractmethod
from re import Pattern

from aios.security.models import CodeLocation
from aios.security.models import FindingCategory
from aios.security.models import SecurityFinding
from aios.security.validators.base import BaseValidator
from aios.security.validators.regex.patterns import PatternDefinition


class RegexValidator(BaseValidator):
    """Abstract base class for regex-based validators.

    Provides common functionality for pattern compilation and matching.
    Subclasses define their patterns via the `patterns` property.

    Attributes:
        _compiled_patterns: Cached compiled regex patterns.
    """

    _compiled_patterns: list[tuple[PatternDefinition, Pattern[str]]] | None = None

    @property
    @abstractmethod
    def patterns(self) -> list[PatternDefinition]:
        """Return list of pattern definitions for this validator.

        Override this property to define the patterns to match.

        Returns:
            List of PatternDefinition objects.
        """
        pass

    @property
    def category(self) -> FindingCategory:
        """Default finding category for this validator.

        Override to change the default category.

        Returns:
            FindingCategory for findings from this validator.
        """
        return FindingCategory.CONFIG

    def get_compiled_patterns(self) -> list[tuple[PatternDefinition, Pattern[str]]]:
        """Get compiled patterns, caching them for reuse.

        Returns:
            List of tuples (PatternDefinition, compiled Pattern).
        """
        if self._compiled_patterns is None:
            self._compiled_patterns = []
            for pattern_def in self.patterns:
                flags = re.IGNORECASE if pattern_def.case_insensitive else 0
                if pattern_def.multiline:
                    flags |= re.MULTILINE
                compiled = re.compile(pattern_def.pattern, flags)
                self._compiled_patterns.append((pattern_def, compiled))
        return self._compiled_patterns

    def validate_content(
        self, content: str, file_path: str
    ) -> list[SecurityFinding]:
        """Validate content against all patterns.

        Args:
            content: The file content to validate.
            file_path: Path to the file (for reporting).

        Returns:
            List of SecurityFinding objects for any matches.
        """
        findings: list[SecurityFinding] = []
        lines = content.split("\n")

        for pattern_def, compiled in self.get_compiled_patterns():
            # Skip if file doesn't match include pattern
            if pattern_def.include_files and not any(
                re.search(inc, file_path) for inc in pattern_def.include_files
            ):
                continue

            # Skip if file matches exclude pattern
            if pattern_def.exclude_files and any(
                re.search(exc, file_path) for exc in pattern_def.exclude_files
            ):
                continue

            # Search for matches
            for line_num, line in enumerate(lines, start=1):
                match = compiled.search(line)
                if match:
                    # Check for false positive patterns
                    if self._is_false_positive(line, pattern_def):
                        continue

                    # Create finding
                    finding = self._create_finding(
                        pattern_def=pattern_def,
                        match=match,
                        line=line,
                        line_num=line_num,
                        file_path=file_path,
                    )
                    findings.append(finding)

        return findings

    def _is_false_positive(self, line: str, pattern_def: PatternDefinition) -> bool:
        """Check if a match is a false positive.

        Args:
            line: The matched line.
            pattern_def: The pattern definition.

        Returns:
            True if this is likely a false positive.
        """
        # Check exclude patterns
        if pattern_def.exclude_patterns:
            for exclude in pattern_def.exclude_patterns:
                if re.search(exclude, line, re.IGNORECASE):
                    return True

        # Common false positive indicators
        false_positive_indicators = [
            r"example",
            r"sample",
            r"test",
            r"demo",
            r"placeholder",
            r"your[-_]?api[-_]?key",
            r"xxx+",
            r"\.\.\.+",
            r"<.*>",  # Template placeholders
        ]

        for indicator in false_positive_indicators:
            if re.search(indicator, line, re.IGNORECASE):
                return True

        return False

    def _create_finding(
        self,
        pattern_def: PatternDefinition,
        match: re.Match[str],
        line: str,
        line_num: int,
        file_path: str,
    ) -> SecurityFinding:
        """Create a SecurityFinding from a regex match.

        Args:
            pattern_def: The pattern definition that matched.
            match: The regex match object.
            line: The matched line.
            line_num: Line number in the file.
            file_path: Path to the file.

        Returns:
            SecurityFinding for this match.
        """
        # Redact sensitive data in snippet if needed
        snippet = line.strip()
        if pattern_def.redact_match:
            snippet = self._redact_sensitive(snippet, match)

        return SecurityFinding(
            id=f"{self.id}-{line_num}",
            validator_id=self.id,
            severity=pattern_def.severity,
            category=pattern_def.category or self.category,
            title=pattern_def.title,
            description=pattern_def.description,
            location=CodeLocation(
                file_path=file_path,
                line_start=line_num,
                line_end=line_num,
                column_start=match.start() + 1,
                column_end=match.end() + 1,
                snippet=snippet,
            ),
            recommendation=pattern_def.recommendation,
            confidence=pattern_def.confidence,
            cwe_id=pattern_def.cwe_id,
            owasp_id=pattern_def.owasp_id,
            auto_fixable=pattern_def.auto_fixable,
            fix_snippet=pattern_def.fix_snippet,
        )

    def _redact_sensitive(self, text: str, match: re.Match[str]) -> str:
        """Redact sensitive data from text.

        Args:
            text: The text to redact.
            match: The match containing sensitive data.

        Returns:
            Text with sensitive data redacted.
        """
        matched = match.group(0)
        if len(matched) > 8:
            # Show first 4 and last 2 characters
            redacted = f"{matched[:4]}{'*' * (len(matched) - 6)}{matched[-2:]}"
        else:
            # For short matches, just show asterisks
            redacted = "*" * len(matched)
        return text.replace(matched, redacted, 1)
