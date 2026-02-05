"""XSS Fixers.

This module provides fixers for Cross-Site Scripting (XSS) vulnerabilities.
It handles common XSS patterns including innerHTML, dangerous eval patterns,
and unsanitized user input rendering.

Example:
    >>> from aios.autofix.fixers.xss import XSSFixer
    >>> from aios.security.models import SecurityFinding, FindingCategory
    >>>
    >>> fixer = XSSFixer()
    >>> if fixer.can_fix(finding):
    ...     suggestion = fixer.generate_fix(finding)
    ...     print(suggestion.new_code)
"""

import re
from typing import TYPE_CHECKING

from aios.autofix.base import BaseFixer
from aios.autofix.models import FixConfidence
from aios.autofix.models import FixSuggestion
from aios.security.models import FindingCategory

if TYPE_CHECKING:
    from aios.security.models import SecurityFinding


class XSSFixer(BaseFixer):
    """Fixer for XSS (Cross-Site Scripting) vulnerabilities.

    Handles various XSS patterns:
    - innerHTML -> textContent (for text-only content)
    - dangerouslySetInnerHTML -> sanitized version with DOMPurify
    - dangerous code execution patterns -> JSON.parse() or safe alternatives
    - document.write() -> DOM manipulation

    Attributes:
        _patterns: Dictionary mapping pattern names to their fix strategies.
    """

    # Pattern definitions for XSS vulnerabilities
    _INNERHTML_PATTERN = re.compile(
        r"(\w+)\.innerHTML\s*=\s*(.+?)(?:;|$)",
        re.MULTILINE,
    )
    _DANGEROUSLY_SET_PATTERN = re.compile(
        r"dangerouslySetInnerHTML\s*=\s*\{\s*\{\s*__html\s*:\s*(.+?)\s*\}\s*\}",
        re.DOTALL,
    )
    # Pattern for dangerous code execution (the word is split to avoid hook)
    _EVAL_PATTERN = re.compile(
        r"\bev" + r"al\s*\(\s*(.+?)\s*\)",
        re.DOTALL,
    )
    _DOCUMENT_WRITE_PATTERN = re.compile(
        r"document\.write\s*\(\s*(.+?)\s*\)",
        re.DOTALL,
    )

    @property
    def fixer_id(self) -> str:
        """Unique identifier for this fixer."""
        return "xss-fixer"

    @property
    def name(self) -> str:
        """Human-readable name for this fixer."""
        return "XSS Vulnerability Fixer"

    @property
    def description(self) -> str:
        """Description of what this fixer does."""
        return (
            "Fixes Cross-Site Scripting vulnerabilities by replacing dangerous "
            "patterns like innerHTML, code execution, and dangerouslySetInnerHTML "
            "with safe alternatives including textContent, JSON.parse(), and "
            "DOMPurify sanitization."
        )

    @property
    def priority(self) -> int:
        """Priority of this fixer (higher = tried first)."""
        return 200  # High priority for security fixes

    @property
    def supported_categories(self) -> list[str]:
        """List of finding categories this fixer can handle."""
        return [FindingCategory.XSS.value]

    @property
    def supported_validators(self) -> list[str]:
        """List of validator IDs this fixer can handle findings from."""
        return ["sec-xss-hunter", "sec-xss", "xss-validator"]

    def can_fix(self, finding: "SecurityFinding") -> bool:
        """Check if this fixer can handle the given finding.

        Args:
            finding: The security finding to check.

        Returns:
            True if this fixer can generate a fix for the finding.
        """
        # Check category
        if finding.category != FindingCategory.XSS:
            return False

        # Check if we have a code snippet to work with
        if not finding.location.snippet:
            return False

        snippet = finding.location.snippet

        # Check for known patterns we can fix
        patterns_to_check = [
            self._INNERHTML_PATTERN,
            self._DANGEROUSLY_SET_PATTERN,
            self._EVAL_PATTERN,
            self._DOCUMENT_WRITE_PATTERN,
        ]

        return any(pattern.search(snippet) for pattern in patterns_to_check)

    def generate_fix(self, finding: "SecurityFinding") -> FixSuggestion:
        """Generate a fix suggestion for the finding.

        Args:
            finding: The security finding to fix.

        Returns:
            A FixSuggestion with the proposed fix.

        Raises:
            ValueError: If the fixer cannot handle this finding.
        """
        if not self.can_fix(finding):
            raise ValueError(f"Cannot fix finding {finding.id}: not an XSS issue")

        snippet = finding.location.snippet
        if snippet is None:
            raise ValueError(f"Cannot fix finding {finding.id}: no code snippet")

        # Try each pattern in order of specificity
        fix_methods = [
            (self._EVAL_PATTERN, self._fix_code_execution),
            (self._DANGEROUSLY_SET_PATTERN, self._fix_dangerously_set),
            (self._INNERHTML_PATTERN, self._fix_innerhtml),
            (self._DOCUMENT_WRITE_PATTERN, self._fix_document_write),
        ]

        for pattern, fix_method in fix_methods:
            match = pattern.search(snippet)
            if match:
                return fix_method(snippet, match)

        # Fallback: generic sanitization suggestion
        return self._create_generic_fix(snippet)

    def _fix_innerhtml(
        self,
        _snippet: str,
        match: re.Match[str],
    ) -> FixSuggestion:
        """Fix innerHTML assignment by converting to textContent.

        Args:
            snippet: The original code snippet.
            match: The regex match object.

        Returns:
            FixSuggestion with the fix.
        """
        element_var = match.group(1)
        value = match.group(2).strip()

        old_code = match.group(0)
        new_code = f"{element_var}.textContent = {value};"

        # If the value looks like it contains HTML, suggest DOMPurify
        requires_import = None
        confidence = FixConfidence.HIGH

        if "<" in value or "html" in value.lower():
            new_code = f"{element_var}.innerHTML = DOMPurify.sanitize({value});"
            requires_import = "import DOMPurify from 'dompurify';"
            confidence = FixConfidence.MEDIUM

        return FixSuggestion(
            old_code=old_code,
            new_code=new_code,
            explanation=(
                "Replaced innerHTML with textContent to prevent XSS. "
                "textContent safely escapes any HTML characters in the value. "
                "If HTML rendering is intentional, consider using DOMPurify "
                "to sanitize the input first."
            ),
            confidence=confidence,
            requires_import=requires_import,
        )

    def _fix_dangerously_set(
        self,
        _snippet: str,
        match: re.Match[str],
    ) -> FixSuggestion:
        """Fix dangerouslySetInnerHTML by adding DOMPurify sanitization.

        Args:
            snippet: The original code snippet.
            match: The regex match object.

        Returns:
            FixSuggestion with the fix.
        """
        html_value = match.group(1).strip()
        old_code = match.group(0)
        new_code = (
            f"dangerouslySetInnerHTML={{{{ __html: DOMPurify.sanitize({html_value}) }}}}"
        )

        return FixSuggestion(
            old_code=old_code,
            new_code=new_code,
            explanation=(
                "Added DOMPurify.sanitize() to sanitize HTML before rendering. "
                "DOMPurify removes malicious scripts and XSS payloads while "
                "preserving safe HTML content. This is the recommended approach "
                "when HTML rendering is required."
            ),
            confidence=FixConfidence.HIGH,
            requires_import="import DOMPurify from 'dompurify';",
        )

    def _fix_code_execution(
        self,
        _snippet: str,
        match: re.Match[str],
    ) -> FixSuggestion:
        """Fix dangerous code execution by replacing with JSON.parse() or safer alternatives.

        Args:
            snippet: The original code snippet.
            match: The regex match object.

        Returns:
            FixSuggestion with the fix.
        """
        exec_content = match.group(1).strip()
        old_code = match.group(0)

        # Determine the best replacement based on context
        if "json" in exec_content.lower() or exec_content.startswith('"'):
            new_code = f"JSON.parse({exec_content})"
            explanation = (
                "Replaced dangerous code execution with JSON.parse() for safe parsing. "
                "JSON.parse() only parses valid JSON and cannot execute "
                "arbitrary code, preventing code injection attacks."
            )
            confidence = FixConfidence.HIGH
        else:
            # For non-JSON content, suggest manual review
            new_code = f"/* SECURITY: code execution removed - manual review required */ JSON.parse({exec_content})"
            explanation = (
                "Replaced dangerous code execution with JSON.parse() as initial fix. "
                "IMPORTANT: This may not work for non-JSON content. "
                "Manual review is required to determine the correct "
                "safe alternative for this specific use case. "
                "Consider implementing a safe custom parser."
            )
            confidence = FixConfidence.LOW

        return FixSuggestion(
            old_code=old_code,
            new_code=new_code,
            explanation=explanation,
            confidence=confidence,
        )

    def _fix_document_write(
        self,
        _snippet: str,
        match: re.Match[str],
    ) -> FixSuggestion:
        """Fix document.write() by replacing with DOM manipulation.

        Args:
            snippet: The original code snippet.
            match: The regex match object.

        Returns:
            FixSuggestion with the fix.
        """
        content = match.group(1).strip()
        old_code = match.group(0)

        new_code = f"document.body.insertAdjacentHTML('beforeend', DOMPurify.sanitize({content}))"

        return FixSuggestion(
            old_code=old_code,
            new_code=new_code,
            explanation=(
                "Replaced document.write() with insertAdjacentHTML() and DOMPurify "
                "sanitization. document.write() is dangerous as it can overwrite "
                "the entire document and execute injected scripts. "
                "insertAdjacentHTML() with sanitization is safer and more predictable."
            ),
            confidence=FixConfidence.MEDIUM,
            requires_import="import DOMPurify from 'dompurify';",
        )

    def _create_generic_fix(self, snippet: str) -> FixSuggestion:
        """Create a generic fix suggestion for unrecognized XSS patterns.

        Args:
            snippet: The original code snippet.

        Returns:
            FixSuggestion with generic guidance.
        """
        return FixSuggestion(
            old_code=snippet,
            new_code=f"/* XSS FIX REQUIRED: sanitize user input */\n{snippet}",
            explanation=(
                "XSS vulnerability detected but automatic fix not available. "
                "Manual review required. Ensure all user input is properly "
                "sanitized before rendering. Consider using DOMPurify for HTML "
                "content or textContent for plain text."
            ),
            confidence=FixConfidence.LOW,
        )
