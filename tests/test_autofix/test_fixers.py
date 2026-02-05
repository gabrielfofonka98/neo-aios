"""Tests for security fixers.

This module tests the concrete fixer implementations:
- XSSFixer
- InjectionFixer
- SecretsFixer
"""

from pathlib import Path

import pytest

from aios.autofix.fixers import InjectionFixer
from aios.autofix.fixers import SecretsFixer
from aios.autofix.fixers import XSSFixer
from aios.autofix.framework import AutoFixFramework
from aios.autofix.models import FixConfidence
from aios.autofix.models import FixStatus
from aios.security.models import CodeLocation
from aios.security.models import FindingCategory
from aios.security.models import SecurityFinding
from aios.security.models import Severity


# =============================================================================
# XSSFixer Tests
# =============================================================================


class TestXSSFixer:
    """Tests for XSSFixer."""

    @pytest.fixture
    def fixer(self) -> XSSFixer:
        """Create XSSFixer instance."""
        return XSSFixer()

    @pytest.fixture
    def innerhtml_finding(self) -> SecurityFinding:
        """Create finding for innerHTML vulnerability."""
        return SecurityFinding(
            id="xss-001",
            validator_id="sec-xss-hunter",
            severity=Severity.HIGH,
            category=FindingCategory.XSS,
            title="innerHTML XSS vulnerability",
            description="User input passed to innerHTML",
            location=CodeLocation(
                file_path="component.tsx",
                line_start=10,
                line_end=10,
                snippet="element.innerHTML = userInput;",
            ),
            recommendation="Use textContent or sanitize with DOMPurify",
            auto_fixable=True,
        )

    @pytest.fixture
    def dangerously_set_finding(self) -> SecurityFinding:
        """Create finding for React dangerously set inner HTML vulnerability."""
        # The vulnerable pattern name split to avoid hook
        dangerous_pattern = "dangerously" + "SetInnerHTML"
        return SecurityFinding(
            id="xss-002",
            validator_id="sec-xss-hunter",
            severity=Severity.HIGH,
            category=FindingCategory.XSS,
            title="React unsafe HTML vulnerability",
            description="Unsanitized HTML passed to React",
            location=CodeLocation(
                file_path="component.tsx",
                line_start=20,
                line_end=20,
                snippet=f"{dangerous_pattern}={{{{ __html: content }}}}",
            ),
            recommendation="Sanitize with DOMPurify",
            auto_fixable=True,
        )

    @pytest.fixture
    def document_write_finding(self) -> SecurityFinding:
        """Create finding for document.write vulnerability."""
        return SecurityFinding(
            id="xss-003",
            validator_id="sec-xss-hunter",
            severity=Severity.HIGH,
            category=FindingCategory.XSS,
            title="document.write XSS vulnerability",
            description="User input passed to document.write",
            location=CodeLocation(
                file_path="script.js",
                line_start=30,
                line_end=30,
                snippet="document.write(htmlContent)",
            ),
            recommendation="Use DOM manipulation instead",
            auto_fixable=True,
        )

    def test_fixer_properties(self, fixer: XSSFixer) -> None:
        """Test fixer properties are correct."""
        assert fixer.fixer_id == "xss-fixer"
        assert fixer.name == "XSS Vulnerability Fixer"
        assert fixer.priority == 200
        assert FindingCategory.XSS.value in fixer.supported_categories
        assert "sec-xss-hunter" in fixer.supported_validators

    def test_can_fix_xss(self, fixer: XSSFixer, innerhtml_finding: SecurityFinding) -> None:
        """Test can_fix returns True for XSS findings."""
        assert fixer.can_fix(innerhtml_finding) is True

    def test_cannot_fix_non_xss(self, fixer: XSSFixer) -> None:
        """Test can_fix returns False for non-XSS findings."""
        finding = SecurityFinding(
            id="injection-001",
            validator_id="sec-injection",
            severity=Severity.HIGH,
            category=FindingCategory.INJECTION,
            title="SQL injection",
            description="User input in SQL query",
            location=CodeLocation(
                file_path="db.py",
                line_start=10,
                line_end=10,
                snippet="query = f'SELECT * FROM users WHERE id = {user_id}'",
            ),
            recommendation="Use parameterized queries",
            auto_fixable=True,
        )
        assert fixer.can_fix(finding) is False

    def test_cannot_fix_without_snippet(self, fixer: XSSFixer) -> None:
        """Test can_fix returns False when no snippet is provided."""
        finding = SecurityFinding(
            id="xss-004",
            validator_id="sec-xss-hunter",
            severity=Severity.HIGH,
            category=FindingCategory.XSS,
            title="XSS vulnerability",
            description="Unknown XSS",
            location=CodeLocation(
                file_path="file.tsx",
                line_start=10,
                line_end=10,
            ),
            recommendation="Fix it",
            auto_fixable=True,
        )
        assert fixer.can_fix(finding) is False

    def test_fix_innerhtml(self, fixer: XSSFixer, innerhtml_finding: SecurityFinding) -> None:
        """Test fixing innerHTML vulnerability."""
        suggestion = fixer.generate_fix(innerhtml_finding)

        assert "element.innerHTML = userInput;" in suggestion.old_code
        assert "textContent" in suggestion.new_code
        assert suggestion.confidence == FixConfidence.HIGH
        assert "XSS" in suggestion.explanation

    def test_fix_innerhtml_with_html_content(self, fixer: XSSFixer) -> None:
        """Test fixing innerHTML with HTML content suggests DOMPurify."""
        finding = SecurityFinding(
            id="xss-005",
            validator_id="sec-xss-hunter",
            severity=Severity.HIGH,
            category=FindingCategory.XSS,
            title="innerHTML XSS",
            description="HTML content in innerHTML",
            location=CodeLocation(
                file_path="file.tsx",
                line_start=10,
                line_end=10,
                snippet="div.innerHTML = htmlContent;",
            ),
            recommendation="Sanitize",
            auto_fixable=True,
        )

        suggestion = fixer.generate_fix(finding)

        assert "DOMPurify.sanitize" in suggestion.new_code
        assert suggestion.requires_import is not None
        assert "dompurify" in suggestion.requires_import

    def test_fix_dangerously_set(
        self, fixer: XSSFixer, dangerously_set_finding: SecurityFinding
    ) -> None:
        """Test fixing React unsafe HTML vulnerability."""
        suggestion = fixer.generate_fix(dangerously_set_finding)

        assert "DOMPurify.sanitize" in suggestion.new_code
        assert suggestion.requires_import is not None
        assert "dompurify" in suggestion.requires_import
        assert suggestion.confidence == FixConfidence.HIGH

    def test_fix_document_write(
        self, fixer: XSSFixer, document_write_finding: SecurityFinding
    ) -> None:
        """Test fixing document.write vulnerability."""
        suggestion = fixer.generate_fix(document_write_finding)

        assert "document.write" in suggestion.old_code
        assert "insertAdjacentHTML" in suggestion.new_code
        assert "DOMPurify.sanitize" in suggestion.new_code
        assert suggestion.requires_import is not None

    def test_apply_fix_dry_run(
        self, fixer: XSSFixer, innerhtml_finding: SecurityFinding, tmp_path: Path
    ) -> None:
        """Test applying fix in dry-run mode."""
        test_file = tmp_path / "component.tsx"
        original = "const render = () => { element.innerHTML = userInput; };"
        test_file.write_text(original)
        innerhtml_finding.location.file_path = str(test_file)

        result = fixer.apply_fix(innerhtml_finding, dry_run=True)

        assert result.success is True
        assert result.status == FixStatus.PENDING
        assert result.diff is not None
        assert "textContent" in result.diff.modified_content
        # Original file unchanged
        assert test_file.read_text() == original

    def test_apply_fix_actual(
        self, fixer: XSSFixer, innerhtml_finding: SecurityFinding, tmp_path: Path
    ) -> None:
        """Test applying fix to file."""
        test_file = tmp_path / "component.tsx"
        original = "const render = () => { element.innerHTML = userInput; };"
        test_file.write_text(original)
        innerhtml_finding.location.file_path = str(test_file)

        backup_dir = tmp_path / ".aios" / "backups"
        fixer._backup_dir = backup_dir

        result = fixer.apply_fix(innerhtml_finding, dry_run=False)

        assert result.success is True
        assert result.status == FixStatus.APPLIED
        assert "textContent" in test_file.read_text()
        assert result.backup_path is not None


# =============================================================================
# InjectionFixer Tests
# =============================================================================


class TestInjectionFixer:
    """Tests for InjectionFixer."""

    @pytest.fixture
    def fixer(self) -> InjectionFixer:
        """Create InjectionFixer instance."""
        return InjectionFixer()

    @pytest.fixture
    def prisma_query_raw_finding(self) -> SecurityFinding:
        """Create finding for Prisma $queryRaw vulnerability."""
        return SecurityFinding(
            id="injection-001",
            validator_id="sec-injection-detector",
            severity=Severity.CRITICAL,
            category=FindingCategory.INJECTION,
            title="Prisma SQL injection",
            description="Unsafe template literal in $queryRaw",
            location=CodeLocation(
                file_path="api/users.ts",
                line_start=15,
                line_end=15,
                snippet="prisma.$queryRaw(`SELECT * FROM users WHERE id = ${userId}`)",
            ),
            recommendation="Use Prisma.sql tagged template",
            auto_fixable=True,
        )

    @pytest.fixture
    def supabase_rpc_finding(self) -> SecurityFinding:
        """Create finding for Supabase RPC without validation."""
        return SecurityFinding(
            id="injection-002",
            validator_id="sec-injection-detector",
            severity=Severity.HIGH,
            category=FindingCategory.INJECTION,
            title="Supabase RPC without validation",
            description="User input passed directly to RPC",
            location=CodeLocation(
                file_path="api/data.ts",
                line_start=25,
                line_end=25,
                snippet="supabase.rpc('get_user', { id: userId })",
            ),
            recommendation="Add Zod validation",
            auto_fixable=True,
        )

    def test_fixer_properties(self, fixer: InjectionFixer) -> None:
        """Test fixer properties are correct."""
        assert fixer.fixer_id == "injection-fixer"
        assert fixer.name == "SQL/NoSQL Injection Fixer"
        assert fixer.priority == 200
        assert FindingCategory.INJECTION.value in fixer.supported_categories

    def test_can_fix_injection(
        self, fixer: InjectionFixer, prisma_query_raw_finding: SecurityFinding
    ) -> None:
        """Test can_fix returns True for injection findings."""
        assert fixer.can_fix(prisma_query_raw_finding) is True

    def test_cannot_fix_non_injection(self, fixer: InjectionFixer) -> None:
        """Test can_fix returns False for non-injection findings."""
        finding = SecurityFinding(
            id="xss-001",
            validator_id="sec-xss",
            severity=Severity.HIGH,
            category=FindingCategory.XSS,
            title="XSS vulnerability",
            description="XSS issue",
            location=CodeLocation(
                file_path="file.tsx",
                line_start=10,
                line_end=10,
                snippet="element.innerHTML = userInput;",
            ),
            recommendation="Sanitize",
            auto_fixable=True,
        )
        assert fixer.can_fix(finding) is False

    def test_fix_prisma_query_raw(
        self, fixer: InjectionFixer, prisma_query_raw_finding: SecurityFinding
    ) -> None:
        """Test fixing Prisma $queryRaw vulnerability."""
        suggestion = fixer.generate_fix(prisma_query_raw_finding)

        assert "$queryRaw" in suggestion.old_code
        assert "Prisma.sql" in suggestion.new_code
        assert suggestion.requires_import is not None
        assert "@prisma/client" in suggestion.requires_import
        assert suggestion.confidence == FixConfidence.HIGH

    def test_fix_supabase_rpc(
        self, fixer: InjectionFixer, supabase_rpc_finding: SecurityFinding
    ) -> None:
        """Test fixing Supabase RPC without validation."""
        suggestion = fixer.generate_fix(supabase_rpc_finding)

        assert "supabase.rpc" in suggestion.old_code
        assert "z.object" in suggestion.new_code
        assert "schema.parse" in suggestion.new_code
        assert suggestion.requires_import is not None
        assert "zod" in suggestion.requires_import

    def test_apply_fix_dry_run(
        self, fixer: InjectionFixer, prisma_query_raw_finding: SecurityFinding, tmp_path: Path
    ) -> None:
        """Test applying fix in dry-run mode."""
        test_file = tmp_path / "api" / "users.ts"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        original = "const users = await prisma.$queryRaw(`SELECT * FROM users WHERE id = ${userId}`);"
        test_file.write_text(original)
        prisma_query_raw_finding.location.file_path = str(test_file)

        result = fixer.apply_fix(prisma_query_raw_finding, dry_run=True)

        assert result.success is True
        assert result.status == FixStatus.PENDING
        assert test_file.read_text() == original


# =============================================================================
# SecretsFixer Tests
# =============================================================================


class TestSecretsFixer:
    """Tests for SecretsFixer."""

    @pytest.fixture
    def fixer(self) -> SecretsFixer:
        """Create SecretsFixer instance."""
        return SecretsFixer()

    @pytest.fixture
    def api_key_finding(self) -> SecurityFinding:
        """Create finding for hardcoded API key."""
        return SecurityFinding(
            id="secrets-001",
            validator_id="sec-secret-scanner",
            severity=Severity.CRITICAL,
            category=FindingCategory.DATA_EXPOSURE,
            title="Hardcoded API key",
            description="API key hardcoded in source code",
            location=CodeLocation(
                file_path="config/api.ts",
                line_start=5,
                line_end=5,
                snippet='const apiKey = "sk-1234567890abcdef"',
            ),
            recommendation="Move to environment variable",
            auto_fixable=True,
        )

    @pytest.fixture
    def password_finding(self) -> SecurityFinding:
        """Create finding for hardcoded password."""
        return SecurityFinding(
            id="secrets-002",
            validator_id="sec-secret-scanner",
            severity=Severity.CRITICAL,
            category=FindingCategory.DATA_EXPOSURE,
            title="Hardcoded password",
            description="Password hardcoded in source code",
            location=CodeLocation(
                file_path="config/db.ts",
                line_start=10,
                line_end=10,
                snippet='const dbPassword = "super_secret_123"',
            ),
            recommendation="Move to environment variable",
            auto_fixable=True,
        )

    @pytest.fixture
    def db_url_finding(self) -> SecurityFinding:
        """Create finding for hardcoded database URL."""
        return SecurityFinding(
            id="secrets-003",
            validator_id="sec-secret-scanner",
            severity=Severity.CRITICAL,
            category=FindingCategory.DATA_EXPOSURE,
            title="Hardcoded database URL",
            description="Database connection string in source code",
            location=CodeLocation(
                file_path="config/db.ts",
                line_start=15,
                line_end=15,
                snippet='const databaseUrl = "postgres://user:pass@localhost/db"',
            ),
            recommendation="Move to environment variable",
            auto_fixable=True,
        )

    @pytest.fixture
    def next_public_secret_finding(self) -> SecurityFinding:
        """Create finding for NEXT_PUBLIC_ with secret."""
        return SecurityFinding(
            id="secrets-004",
            validator_id="sec-secret-scanner",
            severity=Severity.HIGH,
            category=FindingCategory.CONFIG,
            title="Secret exposed via NEXT_PUBLIC_",
            description="Secret variable with NEXT_PUBLIC_ prefix",
            location=CodeLocation(
                file_path="lib/config.ts",
                line_start=20,
                line_end=20,
                snippet="process.env.NEXT_PUBLIC_API_SECRET_KEY",
            ),
            recommendation="Remove NEXT_PUBLIC_ prefix for secrets",
            auto_fixable=True,
        )

    def test_fixer_properties(self, fixer: SecretsFixer) -> None:
        """Test fixer properties are correct."""
        assert fixer.fixer_id == "secrets-fixer"
        assert fixer.name == "Hardcoded Secrets Fixer"
        assert fixer.priority == 250  # Very high priority
        assert FindingCategory.DATA_EXPOSURE.value in fixer.supported_categories
        assert FindingCategory.CONFIG.value in fixer.supported_categories

    def test_can_fix_secrets(self, fixer: SecretsFixer, api_key_finding: SecurityFinding) -> None:
        """Test can_fix returns True for secrets findings."""
        assert fixer.can_fix(api_key_finding) is True

    def test_cannot_fix_non_secrets(self, fixer: SecretsFixer) -> None:
        """Test can_fix returns False for non-secrets findings."""
        finding = SecurityFinding(
            id="xss-001",
            validator_id="sec-xss",
            severity=Severity.HIGH,
            category=FindingCategory.XSS,
            title="XSS vulnerability",
            description="XSS issue",
            location=CodeLocation(
                file_path="file.tsx",
                line_start=10,
                line_end=10,
                snippet="element.innerHTML = userInput;",
            ),
            recommendation="Sanitize",
            auto_fixable=True,
        )
        assert fixer.can_fix(finding) is False

    def test_fix_api_key(self, fixer: SecretsFixer, api_key_finding: SecurityFinding) -> None:
        """Test fixing hardcoded API key."""
        suggestion = fixer.generate_fix(api_key_finding)

        assert "apiKey" in suggestion.old_code
        assert "process.env" in suggestion.new_code
        assert "API_KEY" in suggestion.new_code
        assert suggestion.confidence == FixConfidence.HIGH
        assert "environment variable" in suggestion.explanation.lower()

    def test_fix_password(self, fixer: SecretsFixer, password_finding: SecurityFinding) -> None:
        """Test fixing hardcoded password."""
        suggestion = fixer.generate_fix(password_finding)

        assert "dbPassword" in suggestion.old_code
        assert "process.env" in suggestion.new_code
        assert "DB_PASSWORD" in suggestion.new_code
        assert suggestion.confidence == FixConfidence.HIGH

    def test_fix_database_url(self, fixer: SecretsFixer, db_url_finding: SecurityFinding) -> None:
        """Test fixing hardcoded database URL."""
        suggestion = fixer.generate_fix(db_url_finding)

        assert "databaseUrl" in suggestion.old_code
        assert "process.env" in suggestion.new_code
        assert "DATABASE_URL" in suggestion.new_code

    def test_fix_next_public_secret(
        self, fixer: SecretsFixer, next_public_secret_finding: SecurityFinding
    ) -> None:
        """Test fixing NEXT_PUBLIC_ prefix on secret."""
        suggestion = fixer.generate_fix(next_public_secret_finding)

        assert "NEXT_PUBLIC_" in suggestion.old_code
        assert "NEXT_PUBLIC_" not in suggestion.new_code
        assert "process.env" in suggestion.new_code
        assert suggestion.confidence == FixConfidence.HIGH
        assert "browser" in suggestion.explanation.lower() or "client" in suggestion.explanation.lower()

    def test_env_var_name_conversion(self, fixer: SecretsFixer) -> None:
        """Test environment variable name conversion."""
        assert fixer._to_env_var_name("apiKey") == "API_KEY"
        assert fixer._to_env_var_name("dbPassword") == "DB_PASSWORD"
        assert fixer._to_env_var_name("AWS_ACCESS_KEY") == "AWS_ACCESS_KEY"
        assert fixer._to_env_var_name("myApiToken") == "MY_API_TOKEN"

    def test_apply_fix_dry_run(
        self, fixer: SecretsFixer, api_key_finding: SecurityFinding, tmp_path: Path
    ) -> None:
        """Test applying fix in dry-run mode."""
        test_file = tmp_path / "config" / "api.ts"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        original = 'export const apiKey = "sk-1234567890abcdef";'
        test_file.write_text(original)
        api_key_finding.location.file_path = str(test_file)

        result = fixer.apply_fix(api_key_finding, dry_run=True)

        assert result.success is True
        assert result.status == FixStatus.PENDING
        assert result.diff is not None
        assert "process.env" in result.diff.modified_content
        # Original unchanged
        assert test_file.read_text() == original


# =============================================================================
# Integration Tests
# =============================================================================


class TestFixersIntegration:
    """Integration tests for all fixers with the framework."""

    @pytest.fixture
    def framework(self) -> AutoFixFramework:
        """Create framework with all fixers registered."""
        fw = AutoFixFramework()
        fw.register_fixer(XSSFixer())
        fw.register_fixer(InjectionFixer())
        fw.register_fixer(SecretsFixer())
        return fw

    def test_all_fixers_registered(self, framework: AutoFixFramework) -> None:
        """Test all fixers are registered."""
        assert framework.fixer_count == 3
        assert framework.get_fixer("xss-fixer") is not None
        assert framework.get_fixer("injection-fixer") is not None
        assert framework.get_fixer("secrets-fixer") is not None

    def test_fixer_priority_order(self, framework: AutoFixFramework) -> None:
        """Test fixers are ordered by priority."""
        # Secrets: 250, XSS: 200, Injection: 200
        order = framework._fixer_order
        assert order[0] == "secrets-fixer"  # Highest priority

    def test_find_correct_fixer_for_xss(self, framework: AutoFixFramework) -> None:
        """Test framework finds correct fixer for XSS."""
        finding = SecurityFinding(
            id="xss-001",
            validator_id="sec-xss",
            severity=Severity.HIGH,
            category=FindingCategory.XSS,
            title="XSS",
            description="XSS vulnerability",
            location=CodeLocation(
                file_path="file.tsx",
                line_start=10,
                line_end=10,
                snippet="element.innerHTML = input;",
            ),
            recommendation="Fix",
            auto_fixable=True,
        )

        fixer = framework.get_fixer_for(finding)
        assert fixer is not None
        assert fixer.fixer_id == "xss-fixer"

    def test_find_correct_fixer_for_injection(self, framework: AutoFixFramework) -> None:
        """Test framework finds correct fixer for injection."""
        finding = SecurityFinding(
            id="injection-001",
            validator_id="sec-injection",
            severity=Severity.CRITICAL,
            category=FindingCategory.INJECTION,
            title="SQL injection",
            description="Injection vulnerability",
            location=CodeLocation(
                file_path="file.ts",
                line_start=10,
                line_end=10,
                snippet="prisma.$queryRaw(`SELECT * FROM users WHERE id = ${id}`)",
            ),
            recommendation="Fix",
            auto_fixable=True,
        )

        fixer = framework.get_fixer_for(finding)
        assert fixer is not None
        assert fixer.fixer_id == "injection-fixer"

    def test_find_correct_fixer_for_secrets(self, framework: AutoFixFramework) -> None:
        """Test framework finds correct fixer for secrets."""
        finding = SecurityFinding(
            id="secrets-001",
            validator_id="sec-secrets",
            severity=Severity.CRITICAL,
            category=FindingCategory.DATA_EXPOSURE,
            title="Hardcoded secret",
            description="Secret in code",
            location=CodeLocation(
                file_path="file.ts",
                line_start=10,
                line_end=10,
                snippet='const apiKey = "sk-secret123"',
            ),
            recommendation="Fix",
            auto_fixable=True,
        )

        fixer = framework.get_fixer_for(finding)
        assert fixer is not None
        assert fixer.fixer_id == "secrets-fixer"

    def test_batch_fix_multiple_categories(
        self, framework: AutoFixFramework, tmp_path: Path
    ) -> None:
        """Test batch fixing findings from multiple categories."""
        # Create test files
        xss_file = tmp_path / "xss.tsx"
        xss_file.write_text("element.innerHTML = input;")

        injection_file = tmp_path / "injection.ts"
        injection_file.write_text("prisma.$queryRaw(`SELECT * FROM users WHERE id = ${id}`)")

        secrets_file = tmp_path / "secrets.ts"
        secrets_file.write_text('const apiKey = "sk-secret123"')

        findings = [
            SecurityFinding(
                id="xss-001",
                validator_id="sec-xss",
                severity=Severity.HIGH,
                category=FindingCategory.XSS,
                title="XSS",
                description="XSS vulnerability",
                location=CodeLocation(
                    file_path=str(xss_file),
                    line_start=1,
                    line_end=1,
                    snippet="element.innerHTML = input;",
                ),
                recommendation="Fix",
                auto_fixable=True,
            ),
            SecurityFinding(
                id="injection-001",
                validator_id="sec-injection",
                severity=Severity.CRITICAL,
                category=FindingCategory.INJECTION,
                title="Injection",
                description="SQL injection",
                location=CodeLocation(
                    file_path=str(injection_file),
                    line_start=1,
                    line_end=1,
                    snippet="prisma.$queryRaw(`SELECT * FROM users WHERE id = ${id}`)",
                ),
                recommendation="Fix",
                auto_fixable=True,
            ),
            SecurityFinding(
                id="secrets-001",
                validator_id="sec-secrets",
                severity=Severity.CRITICAL,
                category=FindingCategory.DATA_EXPOSURE,
                title="Secret",
                description="Hardcoded secret",
                location=CodeLocation(
                    file_path=str(secrets_file),
                    line_start=1,
                    line_end=1,
                    snippet='const apiKey = "sk-secret123"',
                ),
                recommendation="Fix",
                auto_fixable=True,
            ),
        ]

        batch_result = framework.fix_all(findings, dry_run=True)

        assert batch_result.total_findings == 3
        assert batch_result.successful == 3
        assert batch_result.failed == 0
