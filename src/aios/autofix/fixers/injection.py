"""Injection Fixers.

This module provides fixers for SQL and NoSQL injection vulnerabilities.
It handles common injection patterns including string concatenation in SQL,
unsafe Prisma queries, and Supabase client-side trust issues.

Example:
    >>> from aios.autofix.fixers.injection import InjectionFixer
    >>> from aios.security.models import SecurityFinding, FindingCategory
    >>>
    >>> fixer = InjectionFixer()
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


class InjectionFixer(BaseFixer):
    """Fixer for SQL/NoSQL injection vulnerabilities.

    Handles various injection patterns:
    - SQL string concatenation -> parameterized queries
    - Prisma $queryRaw -> Prisma.sql`` tagged template
    - Prisma $executeRaw -> Prisma.sql`` with validation
    - Template literal SQL -> parameterized alternatives

    Attributes:
        _patterns: Dictionary mapping pattern names to their fix strategies.
    """

    # SQL concatenation patterns
    _SQL_CONCAT_PATTERN = re.compile(
        r'(["\'])SELECT\s+.+?\s+FROM\s+.+?\s+WHERE\s+(.+?)\s*\+\s*(\w+)',
        re.IGNORECASE | re.DOTALL,
    )

    # Template literal SQL pattern
    _TEMPLATE_SQL_PATTERN = re.compile(
        r"`SELECT\s+.+?\s+FROM\s+.+?\s+WHERE\s+.+?\$\{(\w+)\}",
        re.IGNORECASE | re.DOTALL,
    )

    # Prisma $queryRaw pattern
    _PRISMA_QUERY_RAW_PATTERN = re.compile(
        r"prisma\.\$queryRaw\s*\(\s*`([^`]+)`\s*\)",
        re.IGNORECASE | re.DOTALL,
    )

    # Prisma $executeRaw pattern
    _PRISMA_EXECUTE_RAW_PATTERN = re.compile(
        r"prisma\.\$executeRaw\s*\(\s*`([^`]+)`\s*\)",
        re.IGNORECASE | re.DOTALL,
    )

    # Generic SQL with user input
    _SQL_USER_INPUT_PATTERN = re.compile(
        r"(query|execute|sql)\s*\(\s*[`'\"](.+?)[`'\"]\s*\+\s*(\w+)",
        re.IGNORECASE,
    )

    # Supabase RPC without validation
    _SUPABASE_RPC_PATTERN = re.compile(
        r"supabase\.rpc\s*\(\s*['\"](\w+)['\"]\s*,\s*\{([^}]+)\}\s*\)",
        re.IGNORECASE,
    )

    @property
    def fixer_id(self) -> str:
        """Unique identifier for this fixer."""
        return "injection-fixer"

    @property
    def name(self) -> str:
        """Human-readable name for this fixer."""
        return "SQL/NoSQL Injection Fixer"

    @property
    def description(self) -> str:
        """Description of what this fixer does."""
        return (
            "Fixes SQL and NoSQL injection vulnerabilities by replacing unsafe "
            "string concatenation with parameterized queries, adding Prisma.sql "
            "tagged templates, and implementing proper input validation."
        )

    @property
    def priority(self) -> int:
        """Priority of this fixer (higher = tried first)."""
        return 200  # High priority for security fixes

    @property
    def supported_categories(self) -> list[str]:
        """List of finding categories this fixer can handle."""
        return [FindingCategory.INJECTION.value]

    @property
    def supported_validators(self) -> list[str]:
        """List of validator IDs this fixer can handle findings from."""
        return [
            "sec-injection-detector",
            "sec-injection",
            "sql-injection-validator",
            "nosql-injection-validator",
        ]

    def can_fix(self, finding: "SecurityFinding") -> bool:
        """Check if this fixer can handle the given finding.

        Args:
            finding: The security finding to check.

        Returns:
            True if this fixer can generate a fix for the finding.
        """
        # Check category
        if finding.category != FindingCategory.INJECTION:
            return False

        # Check if we have a code snippet to work with
        if not finding.location.snippet:
            return False

        snippet = finding.location.snippet

        # Check for known patterns we can fix
        patterns_to_check = [
            self._SQL_CONCAT_PATTERN,
            self._TEMPLATE_SQL_PATTERN,
            self._PRISMA_QUERY_RAW_PATTERN,
            self._PRISMA_EXECUTE_RAW_PATTERN,
            self._SQL_USER_INPUT_PATTERN,
            self._SUPABASE_RPC_PATTERN,
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
            raise ValueError(
                f"Cannot fix finding {finding.id}: not an injection issue"
            )

        snippet = finding.location.snippet
        if snippet is None:
            raise ValueError(f"Cannot fix finding {finding.id}: no code snippet")

        # Try each pattern in order of specificity
        fix_methods = [
            (self._PRISMA_QUERY_RAW_PATTERN, self._fix_prisma_query_raw),
            (self._PRISMA_EXECUTE_RAW_PATTERN, self._fix_prisma_execute_raw),
            (self._TEMPLATE_SQL_PATTERN, self._fix_template_sql),
            (self._SQL_CONCAT_PATTERN, self._fix_sql_concat),
            (self._SQL_USER_INPUT_PATTERN, self._fix_sql_user_input),
            (self._SUPABASE_RPC_PATTERN, self._fix_supabase_rpc),
        ]

        for pattern, fix_method in fix_methods:
            match = pattern.search(snippet)
            if match:
                return fix_method(snippet, match)

        # Fallback: generic fix suggestion
        return self._create_generic_fix(snippet)

    def _fix_prisma_query_raw(
        self,
        _snippet: str,
        match: re.Match[str],
    ) -> FixSuggestion:
        """Fix Prisma $queryRaw with template literal by using Prisma.sql.

        Args:
            snippet: The original code snippet.
            match: The regex match object.

        Returns:
            FixSuggestion with the fix.
        """
        query_content = match.group(1)
        old_code = match.group(0)

        # Extract variables from the template literal
        var_pattern = re.compile(r"\$\{(\w+)\}")
        variables = var_pattern.findall(query_content)

        # Replace ${var} with Prisma placeholder syntax
        safe_query = query_content
        for var in variables:
            safe_query = safe_query.replace(f"${{{var}}}", f"${{Prisma.sql`${{{var}}}`}}")

        new_code = f"prisma.$queryRaw(Prisma.sql`{safe_query}`)"

        return FixSuggestion(
            old_code=old_code,
            new_code=new_code,
            explanation=(
                "Wrapped query with Prisma.sql tagged template for safe parameterization. "
                "Prisma.sql automatically escapes parameters and prevents SQL injection. "
                "Variables are now safely interpolated without string concatenation risks."
            ),
            confidence=FixConfidence.HIGH,
            requires_import="import { Prisma } from '@prisma/client';",
        )

    def _fix_prisma_execute_raw(
        self,
        _snippet: str,
        match: re.Match[str],
    ) -> FixSuggestion:
        """Fix Prisma $executeRaw with template literal by using Prisma.sql.

        Args:
            snippet: The original code snippet.
            match: The regex match object.

        Returns:
            FixSuggestion with the fix.
        """
        query_content = match.group(1)
        old_code = match.group(0)

        # Extract variables from the template literal
        var_pattern = re.compile(r"\$\{(\w+)\}")
        variables = var_pattern.findall(query_content)

        # Replace ${var} with Prisma placeholder syntax
        safe_query = query_content
        for var in variables:
            safe_query = safe_query.replace(f"${{{var}}}", f"${{Prisma.sql`${{{var}}}`}}")

        new_code = f"prisma.$executeRaw(Prisma.sql`{safe_query}`)"

        return FixSuggestion(
            old_code=old_code,
            new_code=new_code,
            explanation=(
                "Wrapped execute statement with Prisma.sql tagged template. "
                "$executeRaw with string templates is vulnerable to SQL injection. "
                "Using Prisma.sql ensures all parameters are properly escaped."
            ),
            confidence=FixConfidence.HIGH,
            requires_import="import { Prisma } from '@prisma/client';",
        )

    def _fix_template_sql(
        self,
        _snippet: str,
        match: re.Match[str],
    ) -> FixSuggestion:
        """Fix template literal SQL by using parameterized query.

        Args:
            snippet: The original code snippet.
            match: The regex match object.

        Returns:
            FixSuggestion with the fix.
        """
        var_name = match.group(1)
        old_code = match.group(0)

        # Create parameterized version
        # Replace ${var} with ? placeholder
        new_query = re.sub(
            r"\$\{(\w+)\}",
            "?",
            old_code,
        )

        # Build the fix with parameter array
        new_code = f'{new_query[:-1]}`, [{var_name}])'

        return FixSuggestion(
            old_code=old_code,
            new_code=new_code,
            explanation=(
                "Converted template literal to parameterized query with placeholder. "
                "The variable is now passed as a parameter instead of being "
                "interpolated into the query string, preventing SQL injection."
            ),
            confidence=FixConfidence.MEDIUM,
        )

    def _fix_sql_concat(
        self,
        _snippet: str,
        match: re.Match[str],
    ) -> FixSuggestion:
        """Fix SQL string concatenation by using parameterized query.

        Args:
            _snippet: The original code snippet (unused, match contains needed data).
            match: The regex match object.

        Returns:
            FixSuggestion with the fix.
        """
        quote_char = match.group(1)
        # match.group(2) is where_clause - not used in this fix strategy
        var_name = match.group(3)
        old_code = match.group(0)

        # Create parameterized version
        # Find where the concatenation happens and replace with placeholder
        new_code = old_code.replace(
            f"+ {var_name}",
            f"= ?{quote_char}, [{var_name}])",
        )

        return FixSuggestion(
            old_code=old_code,
            new_code=new_code,
            explanation=(
                "Replaced string concatenation with parameterized query placeholder. "
                "String concatenation in SQL queries is the primary cause of SQL injection. "
                "Using parameterized queries ensures user input is treated as data, not code."
            ),
            confidence=FixConfidence.MEDIUM,
        )

    def _fix_sql_user_input(
        self,
        _snippet: str,
        match: re.Match[str],
    ) -> FixSuggestion:
        """Fix generic SQL with user input concatenation.

        Args:
            snippet: The original code snippet.
            match: The regex match object.

        Returns:
            FixSuggestion with the fix.
        """
        func_name = match.group(1)
        query = match.group(2)
        var_name = match.group(3)
        old_code = match.group(0)

        # Create parameterized version
        new_code = f"{func_name}('{query}?', [{var_name}])"

        return FixSuggestion(
            old_code=old_code,
            new_code=new_code,
            explanation=(
                f"Converted {func_name}() call to use parameterized query. "
                "User input is now passed as a parameter array instead of being "
                "concatenated into the query string."
            ),
            confidence=FixConfidence.MEDIUM,
        )

    def _fix_supabase_rpc(
        self,
        _snippet: str,
        match: re.Match[str],
    ) -> FixSuggestion:
        """Fix Supabase RPC call by adding input validation.

        Args:
            snippet: The original code snippet.
            match: The regex match object.

        Returns:
            FixSuggestion with the fix.
        """
        func_name = match.group(1)
        params = match.group(2)
        old_code = match.group(0)

        # Add Zod validation wrapper
        param_names = re.findall(r"(\w+)\s*:", params)
        schema_fields = ", ".join([f"{p}: z.string()" for p in param_names])

        validation_code = f"""const schema = z.object({{ {schema_fields} }});
const validated = schema.parse({{ {params} }});
supabase.rpc('{func_name}', validated)"""

        return FixSuggestion(
            old_code=old_code,
            new_code=validation_code,
            explanation=(
                "Added Zod schema validation before Supabase RPC call. "
                "This ensures all parameters are validated and sanitized "
                "before being passed to the database function, preventing "
                "injection attacks through malformed input."
            ),
            confidence=FixConfidence.MEDIUM,
            requires_import="import { z } from 'zod';",
        )

    def _create_generic_fix(self, snippet: str) -> FixSuggestion:
        """Create a generic fix suggestion for unrecognized injection patterns.

        Args:
            snippet: The original code snippet.

        Returns:
            FixSuggestion with generic guidance.
        """
        return FixSuggestion(
            old_code=snippet,
            new_code=f"/* INJECTION FIX REQUIRED: use parameterized query */\n{snippet}",
            explanation=(
                "SQL/NoSQL injection vulnerability detected but automatic fix "
                "not available. Manual review required. Replace string concatenation "
                "with parameterized queries. Use ORM features like Prisma.sql or "
                "prepared statements. Always validate and sanitize user input."
            ),
            confidence=FixConfidence.LOW,
        )
