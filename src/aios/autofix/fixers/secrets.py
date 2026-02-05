"""Secrets Fixers.

This module provides fixers for hardcoded secrets and credential exposure.
It handles patterns like API keys, passwords, tokens, and other sensitive
data that should be moved to environment variables.

Example:
    >>> from aios.autofix.fixers.secrets import SecretsFixer
    >>> from aios.security.models import SecurityFinding, FindingCategory
    >>>
    >>> fixer = SecretsFixer()
    >>> if fixer.can_fix(finding):
    ...     suggestion = fixer.generate_fix(finding)
    ...     print(suggestion.new_code)
"""

import re
from collections.abc import Callable
from typing import TYPE_CHECKING

from aios.autofix.base import BaseFixer
from aios.autofix.models import FixConfidence
from aios.autofix.models import FixSuggestion
from aios.security.models import FindingCategory

if TYPE_CHECKING:
    from aios.security.models import SecurityFinding


class SecretsFixer(BaseFixer):
    """Fixer for hardcoded secrets and credential exposure.

    Handles various secret patterns:
    - API keys and tokens
    - Database connection strings
    - Passwords and auth credentials
    - Private keys and certificates
    - NEXT_PUBLIC_ misuse in Next.js

    The fixer generates environment variable references and
    provides .env.example entries for documentation.
    """

    # Pattern for hardcoded API keys
    _API_KEY_PATTERN = re.compile(
        r'(?:const|let|var)\s+(\w*(?:api[_-]?key|apikey|api_token|auth_token|access_token)\w*)\s*=\s*["\']([^"\']+)["\']',
        re.IGNORECASE,
    )

    # Pattern for hardcoded passwords
    _PASSWORD_PATTERN = re.compile(
        r'(?:const|let|var)\s+(\w*(?:password|passwd|pwd|secret)\w*)\s*=\s*["\']([^"\']+)["\']',
        re.IGNORECASE,
    )

    # Pattern for database connection strings (supports camelCase and snake_case)
    _DB_CONNECTION_PATTERN = re.compile(
        r'(?:const|let|var)\s+(\w*(?:database[_]?url|databaseUrl|db[_]?url|dbUrl|connection[_]?string|connectionString|mongo[_]?uri|mongoUri|postgres[_]?url|postgresUrl|mysql[_]?url|mysqlUrl)\w*)\s*=\s*["\']([^"\']+)["\']',
        re.IGNORECASE,
    )

    # Pattern for private keys
    _PRIVATE_KEY_PATTERN = re.compile(
        r'(?:const|let|var)\s+(\w*(?:private_key|privatekey|signing_key|encryption_key)\w*)\s*=\s*["\']([^"\']+)["\']',
        re.IGNORECASE,
    )

    # Pattern for generic secrets
    _GENERIC_SECRET_PATTERN = re.compile(
        r'(?:const|let|var)\s+(\w*(?:secret|credential|token|key)\w*)\s*=\s*["\'](sk[_-][a-zA-Z0-9]{20,}|[a-f0-9]{32,}|[A-Za-z0-9+/]{40,})["\']',
        re.IGNORECASE,
    )

    # Pattern for NEXT_PUBLIC_ with secrets
    _NEXT_PUBLIC_SECRET_PATTERN = re.compile(
        r'process\.env\.NEXT_PUBLIC_(\w*(?:secret|key|token|password|api_key)\w*)',
        re.IGNORECASE,
    )

    # Pattern for inline object secrets
    _OBJECT_SECRET_PATTERN = re.compile(
        r'(\w+):\s*["\']([a-zA-Z0-9_\-]{20,}|sk[_-][a-zA-Z0-9]{20,})["\']',
        re.IGNORECASE,
    )

    # Pattern for AWS credentials
    _AWS_CREDENTIALS_PATTERN = re.compile(
        r'(?:const|let|var)\s+(\w*(?:aws_access_key|aws_secret|aws_key)\w*)\s*=\s*["\']([A-Z0-9]{20})["\']',
        re.IGNORECASE,
    )

    @property
    def fixer_id(self) -> str:
        """Unique identifier for this fixer."""
        return "secrets-fixer"

    @property
    def name(self) -> str:
        """Human-readable name for this fixer."""
        return "Hardcoded Secrets Fixer"

    @property
    def description(self) -> str:
        """Description of what this fixer does."""
        return (
            "Fixes hardcoded secrets by moving them to environment variables. "
            "Handles API keys, passwords, database URLs, private keys, and "
            "other sensitive data. Generates .env.example entries for documentation."
        )

    @property
    def priority(self) -> int:
        """Priority of this fixer (higher = tried first)."""
        return 250  # Very high priority - secrets are critical

    @property
    def supported_categories(self) -> list[str]:
        """List of finding categories this fixer can handle."""
        return [FindingCategory.DATA_EXPOSURE.value, FindingCategory.CONFIG.value]

    @property
    def supported_validators(self) -> list[str]:
        """List of validator IDs this fixer can handle findings from."""
        return [
            "sec-secret-scanner",
            "sec-secrets",
            "hardcoded-secrets-validator",
            "credential-exposure-validator",
        ]

    def can_fix(self, finding: "SecurityFinding") -> bool:
        """Check if this fixer can handle the given finding.

        Args:
            finding: The security finding to check.

        Returns:
            True if this fixer can generate a fix for the finding.
        """
        # Check category
        if finding.category not in [
            FindingCategory.DATA_EXPOSURE,
            FindingCategory.CONFIG,
        ]:
            return False

        # Check if we have a code snippet to work with
        if not finding.location.snippet:
            return False

        snippet = finding.location.snippet

        # Check for known patterns we can fix
        patterns_to_check = [
            self._API_KEY_PATTERN,
            self._PASSWORD_PATTERN,
            self._DB_CONNECTION_PATTERN,
            self._PRIVATE_KEY_PATTERN,
            self._GENERIC_SECRET_PATTERN,
            self._NEXT_PUBLIC_SECRET_PATTERN,
            self._OBJECT_SECRET_PATTERN,
            self._AWS_CREDENTIALS_PATTERN,
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
                f"Cannot fix finding {finding.id}: not a secrets issue"
            )

        snippet = finding.location.snippet
        if snippet is None:
            raise ValueError(f"Cannot fix finding {finding.id}: no code snippet")

        # Try each pattern in order of specificity
        # Define the type for fix methods
        FixMethodType = Callable[[str, re.Match[str]], FixSuggestion]
        fix_methods: list[tuple[re.Pattern[str], FixMethodType]] = [
            (self._NEXT_PUBLIC_SECRET_PATTERN, self._fix_next_public_secret),
            (self._AWS_CREDENTIALS_PATTERN, self._fix_aws_credentials),
            (self._API_KEY_PATTERN, self._fix_api_key),
            (self._PASSWORD_PATTERN, self._fix_password),
            (self._DB_CONNECTION_PATTERN, self._fix_db_connection),
            (self._PRIVATE_KEY_PATTERN, self._fix_private_key),
            (self._GENERIC_SECRET_PATTERN, self._fix_generic_secret),
            (self._OBJECT_SECRET_PATTERN, self._fix_object_secret),
        ]

        for pattern, fix_method in fix_methods:
            match = pattern.search(snippet)
            if match:
                return fix_method(snippet, match)

        # Fallback: generic fix suggestion
        return self._create_generic_fix(snippet)

    def _fix_api_key(
        self,
        _snippet: str,
        match: re.Match[str],
    ) -> FixSuggestion:
        """Fix hardcoded API key by moving to environment variable.

        Args:
            _snippet: The original code snippet (unused, match contains needed data).
            match: The regex match object.

        Returns:
            FixSuggestion with the fix.
        """
        var_name = match.group(1)
        # match.group(2) is secret_value - not used to avoid exposing in output
        old_code = match.group(0)

        # Generate env var name
        env_var_name = self._to_env_var_name(var_name)

        # Generate the fix
        new_code = f'const {var_name} = process.env.{env_var_name} ?? ""'

        # Generate .env.example entry
        env_example = f"{env_var_name}=your_{var_name.lower()}_here"

        return FixSuggestion(
            old_code=old_code,
            new_code=new_code,
            explanation=(
                f"Moved hardcoded API key to environment variable {env_var_name}. "
                f"Add to your .env file: {env_var_name}=<your-key>\n"
                f"Add to .env.example: {env_example}\n"
                "Never commit secrets to version control."
            ),
            confidence=FixConfidence.HIGH,
        )

    def _fix_password(
        self,
        _snippet: str,
        match: re.Match[str],
    ) -> FixSuggestion:
        """Fix hardcoded password by moving to environment variable.

        Args:
            snippet: The original code snippet.
            match: The regex match object.

        Returns:
            FixSuggestion with the fix.
        """
        var_name = match.group(1)
        old_code = match.group(0)

        env_var_name = self._to_env_var_name(var_name)
        new_code = f'const {var_name} = process.env.{env_var_name} ?? ""'

        return FixSuggestion(
            old_code=old_code,
            new_code=new_code,
            explanation=(
                f"Moved hardcoded password to environment variable {env_var_name}. "
                "Passwords should never be hardcoded in source code. "
                "Use environment variables or a secrets manager.\n"
                f"Add to .env: {env_var_name}=<secure-password>"
            ),
            confidence=FixConfidence.HIGH,
        )

    def _fix_db_connection(
        self,
        _snippet: str,
        match: re.Match[str],
    ) -> FixSuggestion:
        """Fix hardcoded database connection string.

        Args:
            snippet: The original code snippet.
            match: The regex match object.

        Returns:
            FixSuggestion with the fix.
        """
        var_name = match.group(1)
        old_code = match.group(0)

        env_var_name = self._to_env_var_name(var_name)
        new_code = f'const {var_name} = process.env.{env_var_name} ?? ""'

        return FixSuggestion(
            old_code=old_code,
            new_code=new_code,
            explanation=(
                f"Moved database connection string to environment variable {env_var_name}. "
                "Connection strings contain sensitive credentials and should never "
                "be hardcoded. They often include passwords and hostnames that "
                "attackers can use to access your database.\n"
                f"Add to .env: {env_var_name}=<connection-string>"
            ),
            confidence=FixConfidence.HIGH,
        )

    def _fix_private_key(
        self,
        _snippet: str,
        match: re.Match[str],
    ) -> FixSuggestion:
        """Fix hardcoded private key.

        Args:
            snippet: The original code snippet.
            match: The regex match object.

        Returns:
            FixSuggestion with the fix.
        """
        var_name = match.group(1)
        old_code = match.group(0)

        env_var_name = self._to_env_var_name(var_name)
        new_code = f'const {var_name} = process.env.{env_var_name} ?? ""'

        return FixSuggestion(
            old_code=old_code,
            new_code=new_code,
            explanation=(
                f"Moved private key to environment variable {env_var_name}. "
                "Private keys are highly sensitive and should never be in code. "
                "Consider using a secrets manager like AWS Secrets Manager, "
                "HashiCorp Vault, or similar for production environments.\n"
                f"Add to .env: {env_var_name}=<private-key>"
            ),
            confidence=FixConfidence.HIGH,
        )

    def _fix_generic_secret(
        self,
        _snippet: str,
        match: re.Match[str],
    ) -> FixSuggestion:
        """Fix generic hardcoded secret.

        Args:
            snippet: The original code snippet.
            match: The regex match object.

        Returns:
            FixSuggestion with the fix.
        """
        var_name = match.group(1)
        old_code = match.group(0)

        env_var_name = self._to_env_var_name(var_name)
        new_code = f'const {var_name} = process.env.{env_var_name} ?? ""'

        return FixSuggestion(
            old_code=old_code,
            new_code=new_code,
            explanation=(
                f"Moved secret to environment variable {env_var_name}. "
                "The detected value appears to be a secret or token. "
                "Move it to environment variables and never commit to git.\n"
                f"Add to .env: {env_var_name}=<your-secret>"
            ),
            confidence=FixConfidence.MEDIUM,
        )

    def _fix_next_public_secret(
        self,
        _snippet: str,
        match: re.Match[str],
    ) -> FixSuggestion:
        """Fix NEXT_PUBLIC_ prefix on secret environment variable.

        Args:
            snippet: The original code snippet.
            match: The regex match object.

        Returns:
            FixSuggestion with the fix.
        """
        var_name = match.group(1)
        old_code = match.group(0)

        # Remove NEXT_PUBLIC_ prefix - secrets should be server-only
        new_env_var = var_name.upper()
        new_code = f"process.env.{new_env_var}"

        return FixSuggestion(
            old_code=old_code,
            new_code=new_code,
            explanation=(
                f"Removed NEXT_PUBLIC_ prefix from {var_name}. "
                "NEXT_PUBLIC_ variables are exposed to the browser and should "
                "NEVER contain secrets. Remove the prefix to keep it server-only. "
                "If this value is needed client-side, it should not be a secret.\n"
                f"Rename in .env: NEXT_PUBLIC_{var_name} -> {new_env_var}"
            ),
            confidence=FixConfidence.HIGH,
        )

    def _fix_object_secret(
        self,
        _snippet: str,
        match: re.Match[str],
    ) -> FixSuggestion:
        """Fix hardcoded secret in object property.

        Args:
            snippet: The original code snippet.
            match: The regex match object.

        Returns:
            FixSuggestion with the fix.
        """
        prop_name = match.group(1)
        old_code = match.group(0)

        env_var_name = self._to_env_var_name(prop_name)
        new_code = f'{prop_name}: process.env.{env_var_name} ?? ""'

        return FixSuggestion(
            old_code=old_code,
            new_code=new_code,
            explanation=(
                f"Moved hardcoded value in {prop_name} to environment variable. "
                "The value appears to be a secret or API key based on its format.\n"
                f"Add to .env: {env_var_name}=<your-value>"
            ),
            confidence=FixConfidence.MEDIUM,
        )

    def _fix_aws_credentials(
        self,
        _snippet: str,
        match: re.Match[str],
    ) -> FixSuggestion:
        """Fix hardcoded AWS credentials.

        Args:
            snippet: The original code snippet.
            match: The regex match object.

        Returns:
            FixSuggestion with the fix.
        """
        var_name = match.group(1)
        old_code = match.group(0)

        env_var_name = self._to_env_var_name(var_name)
        new_code = f'const {var_name} = process.env.{env_var_name} ?? ""'

        return FixSuggestion(
            old_code=old_code,
            new_code=new_code,
            explanation=(
                f"Moved AWS credentials to environment variable {env_var_name}. "
                "AWS credentials should NEVER be hardcoded. Use IAM roles in "
                "production (ECS, Lambda, EC2 instance profiles) or AWS credentials "
                "file (~/.aws/credentials) for local development.\n"
                f"Add to .env: {env_var_name}=<aws-credential>\n"
                "Consider using AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY "
                "as standard environment variable names."
            ),
            confidence=FixConfidence.HIGH,
        )

    def _create_generic_fix(self, snippet: str) -> FixSuggestion:
        """Create a generic fix suggestion for unrecognized secret patterns.

        Args:
            snippet: The original code snippet.

        Returns:
            FixSuggestion with generic guidance.
        """
        return FixSuggestion(
            old_code=snippet,
            new_code=f"/* SECRET FIX REQUIRED: move to environment variable */\n{snippet}",
            explanation=(
                "Potential hardcoded secret detected but automatic fix not available. "
                "Manual review required. Move all secrets to environment variables:\n"
                "1. Create .env file (git-ignored)\n"
                "2. Add SECRET_NAME=value\n"
                "3. Access via process.env.SECRET_NAME\n"
                "4. Document in .env.example with placeholder values"
            ),
            confidence=FixConfidence.LOW,
        )

    def _to_env_var_name(self, var_name: str) -> str:
        """Convert a variable name to environment variable format.

        Args:
            var_name: The original variable name (camelCase, snake_case, etc.)

        Returns:
            Environment variable name in UPPER_SNAKE_CASE.
        """
        # Handle camelCase
        name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", var_name)
        # Handle consecutive capitals
        name = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
        # Convert to uppercase
        return name.upper()
