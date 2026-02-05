"""SQL AST-based security validators.

This module provides validators that use sqlglot for SQL parsing
to detect injection vulnerabilities with high precision.

Validators:
    - InjectionValidator: Detects SQL/ORM injection vulnerabilities
"""

import re
from typing import TYPE_CHECKING
from typing import ClassVar

from aios.security.ast.parser import ASTParser
from aios.security.ast.parser import get_parser
from aios.security.models import CodeLocation
from aios.security.models import FindingCategory
from aios.security.models import SecurityFinding
from aios.security.models import Severity
from aios.security.validators.base import BaseValidator

if TYPE_CHECKING:
    from tree_sitter import Tree


class InjectionValidator(BaseValidator):
    """Validator for SQL and ORM injection vulnerabilities.

    Detects:
    - Prisma $queryRaw and $executeRaw with string interpolation
    - Template strings containing SQL with variables
    - Supabase queries with unsanitized input
    - Dynamic SQL construction patterns

    CWE-89: Improper Neutralization of Special Elements used in an SQL Command
    """

    # SQL keywords that indicate a SQL query
    SQL_KEYWORDS: ClassVar[list[str]] = [
        "SELECT",
        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "CREATE",
        "ALTER",
        "TRUNCATE",
        "UNION",
        "JOIN",
        "WHERE",
        "FROM",
    ]

    # Dangerous Prisma methods
    PRISMA_RAW_METHODS: ClassVar[list[str]] = [
        "$queryRaw",
        "$executeRaw",
        "$queryRawUnsafe",
        "$executeRawUnsafe",
    ]

    def __init__(self, parser: ASTParser | None = None) -> None:
        """Initialize the injection validator.

        Args:
            parser: Optional AST parser instance.
        """
        self._parser = parser or get_parser()
        self._finding_counter = 0
        self._sql_pattern = re.compile(
            r"\b(" + "|".join(self.SQL_KEYWORDS) + r")\b",
            re.IGNORECASE,
        )

    @property
    def id(self) -> str:
        """Return the validator ID."""
        return "sec-injection-detector"

    @property
    def name(self) -> str:
        """Return the validator name."""
        return "SQL/ORM Injection Detector"

    @property
    def description(self) -> str:
        """Return the validator description."""
        return "Detects SQL injection and ORM injection vulnerabilities"

    def _next_finding_id(self) -> str:
        """Generate the next finding ID."""
        self._finding_counter += 1
        return f"injection-{self._finding_counter:04d}"

    def validate_content(self, content: str, file_path: str) -> list[SecurityFinding]:
        """Validate content for injection vulnerabilities.

        Args:
            content: The file content to validate.
            file_path: Path to the file.

        Returns:
            List of security findings.
        """
        findings: list[SecurityFinding] = []

        try:
            tree = self._parser.parse_file_content(content, file_path)
        except ValueError:
            return findings

        # Check for Prisma raw queries
        findings.extend(self._check_prisma_raw_queries(tree, file_path))

        # Check for template strings with SQL
        findings.extend(self._check_sql_template_strings(tree, file_path))

        # Check for Supabase query patterns
        findings.extend(self._check_supabase_patterns(tree, file_path))

        # Check for dynamic SQL construction
        findings.extend(self._check_dynamic_sql(tree, file_path))

        return findings

    def _check_prisma_raw_queries(
        self, tree: "Tree", file_path: str
    ) -> list[SecurityFinding]:
        """Check for unsafe Prisma raw query patterns."""
        findings: list[SecurityFinding] = []

        # Find calls to Prisma raw methods
        for match in self._parser.find_call_expressions(
            tree, method_names=self.PRISMA_RAW_METHODS
        ):
            # Check if using template literal (which is safe with Prisma.sql)
            # vs string concatenation (unsafe)
            is_unsafe = self._is_unsafe_raw_query(match.text)

            if is_unsafe:
                method_name = self._extract_method_name(match.text)
                is_explicit_unsafe = "Unsafe" in method_name

                findings.append(
                    SecurityFinding(
                        id=self._next_finding_id(),
                        validator_id=self.id,
                        severity=Severity.CRITICAL if is_explicit_unsafe else Severity.HIGH,
                        category=FindingCategory.INJECTION,
                        title=f"Unsafe Prisma {method_name} usage",
                        description=(
                            f"Prisma {method_name} is used with string interpolation "
                            "or concatenation. This bypasses parameterization and "
                            "can lead to SQL injection attacks."
                        ),
                        location=CodeLocation(
                            file_path=file_path,
                            line_start=match.location.line_start,
                            line_end=match.location.line_end,
                            column_start=match.location.column_start,
                            column_end=match.location.column_end,
                            snippet=match.text,
                        ),
                        recommendation=(
                            "Use Prisma.sql tagged template literal for safe "
                            "parameterization: prisma.$queryRaw(Prisma.sql`...`). "
                            "Never use string concatenation with raw queries."
                        ),
                        auto_fixable=False,
                        confidence=0.95,
                        cwe_id="CWE-89",
                        owasp_id="A03:2021",
                    )
                )

        return findings

    def _check_sql_template_strings(
        self, tree: "Tree", file_path: str
    ) -> list[SecurityFinding]:
        """Check for SQL in template strings with variable interpolation."""
        findings: list[SecurityFinding] = []

        # Find template strings
        for match in self._parser.find_nodes(tree, ["template_string"]):
            text = match.text

            # Check if it contains SQL
            if not self._sql_pattern.search(text):
                continue

            # Check if it has interpolation (${...})
            if "${" in text:
                findings.append(
                    SecurityFinding(
                        id=self._next_finding_id(),
                        validator_id=self.id,
                        severity=Severity.HIGH,
                        category=FindingCategory.INJECTION,
                        title="SQL query with string interpolation",
                        description=(
                            "SQL query uses template string interpolation which "
                            "can lead to SQL injection. User input could be "
                            "injected directly into the query."
                        ),
                        location=CodeLocation(
                            file_path=file_path,
                            line_start=match.location.line_start,
                            line_end=match.location.line_end,
                            column_start=match.location.column_start,
                            column_end=match.location.column_end,
                            snippet=text[:200] + ("..." if len(text) > 200 else ""),
                        ),
                        recommendation=(
                            "Use parameterized queries instead of string interpolation. "
                            "For Prisma, use Prisma.sql``. For other ORMs, use their "
                            "built-in parameterization."
                        ),
                        auto_fixable=False,
                        confidence=0.85,
                        cwe_id="CWE-89",
                        owasp_id="A03:2021",
                    )
                )

        return findings

    def _check_supabase_patterns(
        self, tree: "Tree", file_path: str
    ) -> list[SecurityFinding]:
        """Check for unsafe Supabase query patterns."""
        findings: list[SecurityFinding] = []

        # Look for supabase.rpc calls with potential injection
        for match in self._parser.find_call_expressions(tree, method_names=["rpc"]):
            # Check if the call has dynamic parameters
            if self._has_dynamic_input(match.text):
                findings.append(
                    SecurityFinding(
                        id=self._next_finding_id(),
                        validator_id=self.id,
                        severity=Severity.MEDIUM,
                        category=FindingCategory.INJECTION,
                        title="Supabase RPC with dynamic parameters",
                        description=(
                            "Supabase RPC function called with dynamic parameters. "
                            "Ensure the RPC function properly sanitizes input and "
                            "uses parameterized queries."
                        ),
                        location=CodeLocation(
                            file_path=file_path,
                            line_start=match.location.line_start,
                            line_end=match.location.line_end,
                            column_start=match.location.column_start,
                            column_end=match.location.column_end,
                            snippet=match.text,
                        ),
                        recommendation=(
                            "Review the RPC function for SQL injection vulnerabilities. "
                            "Ensure it uses parameterized queries and validates input."
                        ),
                        auto_fixable=False,
                        confidence=0.6,  # Lower confidence - needs manual review
                        cwe_id="CWE-89",
                        owasp_id="A03:2021",
                    )
                )

        # Look for .filter() with string values that might be SQL
        for match in self._parser.find_call_expressions(tree, method_names=["filter", "or"]):
            if self._sql_pattern.search(match.text):
                findings.append(
                    SecurityFinding(
                        id=self._next_finding_id(),
                        validator_id=self.id,
                        severity=Severity.MEDIUM,
                        category=FindingCategory.INJECTION,
                        title="Potential SQL in Supabase filter",
                        description=(
                            "Supabase filter method appears to contain raw SQL. "
                            "If this includes user input, it could be vulnerable "
                            "to injection attacks."
                        ),
                        location=CodeLocation(
                            file_path=file_path,
                            line_start=match.location.line_start,
                            line_end=match.location.line_end,
                            column_start=match.location.column_start,
                            column_end=match.location.column_end,
                            snippet=match.text,
                        ),
                        recommendation=(
                            "Use Supabase's query builder methods instead of "
                            "raw SQL strings in filters."
                        ),
                        auto_fixable=False,
                        confidence=0.7,
                        cwe_id="CWE-89",
                        owasp_id="A03:2021",
                    )
                )

        return findings

    def _check_dynamic_sql(
        self, tree: "Tree", file_path: str
    ) -> list[SecurityFinding]:
        """Check for dynamic SQL construction patterns."""
        findings: list[SecurityFinding] = []

        # Look for string concatenation with SQL keywords
        for match in self._parser.find_nodes(tree, ["binary_expression"]):
            text = match.text

            # Check for string concatenation (+) with SQL
            if "+" in text and self._sql_pattern.search(text):
                findings.append(
                    SecurityFinding(
                        id=self._next_finding_id(),
                        validator_id=self.id,
                        severity=Severity.HIGH,
                        category=FindingCategory.INJECTION,
                        title="Dynamic SQL construction via concatenation",
                        description=(
                            "SQL query is constructed using string concatenation. "
                            "This is a common SQL injection vulnerability pattern."
                        ),
                        location=CodeLocation(
                            file_path=file_path,
                            line_start=match.location.line_start,
                            line_end=match.location.line_end,
                            column_start=match.location.column_start,
                            column_end=match.location.column_end,
                            snippet=text[:200] + ("..." if len(text) > 200 else ""),
                        ),
                        recommendation=(
                            "Use parameterized queries instead of string concatenation. "
                            "Never build SQL queries by concatenating user input."
                        ),
                        auto_fixable=False,
                        confidence=0.8,
                        cwe_id="CWE-89",
                        owasp_id="A03:2021",
                    )
                )

        return findings

    def _is_unsafe_raw_query(self, text: str) -> bool:
        """Check if a Prisma raw query is unsafe.

        Safe: prisma.$queryRaw(Prisma.sql`SELECT * FROM users WHERE id = ${id}`)
        Unsafe: prisma.$queryRaw(`SELECT * FROM users WHERE id = ${id}`)
        Unsafe: prisma.$queryRaw("SELECT * FROM users WHERE id = " + id)
        """
        # Check for Prisma.sql tagged template (safe)
        if "Prisma.sql" in text or "Prisma.join" in text:
            return False

        # Check for string concatenation (unsafe)
        if "+" in text:
            return True

        # Check for template literal without tag (unsafe)
        if "`" in text and "${" in text:
            return True

        # Check for string with variables (unsafe)
        return ("'" in text or '"' in text) and "+" in text

    def _extract_method_name(self, text: str) -> str:
        """Extract the method name from a call expression."""
        for method in self.PRISMA_RAW_METHODS:
            if method in text:
                return method
        return "rawQuery"

    def _has_dynamic_input(self, text: str) -> bool:
        """Check if a call has dynamic input (variables, not just literals)."""
        # Check for variable references
        if "${" in text:
            return True

        # Check for identifiers that aren't literals
        # This is a simplified check
        non_literal_patterns = [
            r"[a-zA-Z_][a-zA-Z0-9_]*\s*[,)]",  # Variable as argument
            r"\.{3}",  # Spread operator
        ]

        return any(re.search(pattern, text) for pattern in non_literal_patterns)
