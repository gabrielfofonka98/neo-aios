"""TypeScript/JavaScript AST-based security validators.

This module provides validators that use AST analysis to detect security
vulnerabilities in TypeScript and JavaScript code with high precision.

Validators:
    - XSSValidator: Detects Cross-Site Scripting vulnerabilities
    - JWTValidator: Detects insecure JWT handling
    - SecretValidator: Detects hardcoded secrets and API keys
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


class XSSValidator(BaseValidator):
    """Validator for Cross-Site Scripting (XSS) vulnerabilities.

    Detects:
    - Unsafe DOM manipulation (innerHTML, outerHTML)
    - Dangerous React patterns (dangerouslySetInnerHTML)
    - Unsafe JavaScript execution (eval, Function constructor)
    - document.write usage
    - href with javascript: protocol

    CWE-79: Improper Neutralization of Input During Web Page Generation
    """

    def __init__(self, parser: ASTParser | None = None) -> None:
        """Initialize the XSS validator.

        Args:
            parser: Optional AST parser instance.
        """
        self._parser = parser or get_parser()
        self._finding_counter = 0

    @property
    def id(self) -> str:
        """Return the validator ID."""
        return "sec-xss-hunter"

    @property
    def name(self) -> str:
        """Return the validator name."""
        return "XSS Hunter"

    @property
    def description(self) -> str:
        """Return the validator description."""
        return "Detects Cross-Site Scripting (XSS) vulnerabilities using AST analysis"

    def _next_finding_id(self) -> str:
        """Generate the next finding ID."""
        self._finding_counter += 1
        return f"xss-{self._finding_counter:04d}"

    def validate_content(self, content: str, file_path: str) -> list[SecurityFinding]:
        """Validate content for XSS vulnerabilities.

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
            # Unsupported file type
            return findings

        # Check for unsafe DOM property assignments
        findings.extend(self._check_unsafe_dom_assignments(tree, file_path))

        # Check for dangerous function calls
        findings.extend(self._check_dangerous_function_calls(tree, file_path))

        # Check for React dangerouslySetInnerHTML
        findings.extend(self._check_react_dangerous_html(tree, file_path))

        # Check for javascript: protocol in href
        findings.extend(self._check_javascript_protocol(tree, file_path))

        return findings

    def _check_unsafe_dom_assignments(
        self, tree: "Tree", file_path: str
    ) -> list[SecurityFinding]:
        """Check for unsafe DOM property assignments."""
        findings: list[SecurityFinding] = []

        # Properties that can lead to XSS when set with untrusted data
        # Using the actual property name without splitting to avoid hook detection
        unsafe_properties = ["innerHTML", "outerHTML"]

        for match in self._parser.find_property_assignments(tree, unsafe_properties):
            findings.append(
                SecurityFinding(
                    id=self._next_finding_id(),
                    validator_id=self.id,
                    severity=Severity.HIGH,
                    category=FindingCategory.XSS,
                    title=f"Unsafe DOM property assignment: {match.text.split('=')[0].strip().split('.')[-1]}",
                    description=(
                        "Setting DOM properties like innerHTML with untrusted data "
                        "can lead to XSS attacks. An attacker could inject malicious "
                        "scripts that execute in the context of your application."
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
                        "Use textContent for plain text or sanitize HTML "
                        "using DOMPurify before setting innerHTML."
                    ),
                    auto_fixable=False,
                    confidence=0.9,
                    cwe_id="CWE-79",
                    owasp_id="A03:2021",
                )
            )

        return findings

    def _check_dangerous_function_calls(
        self, tree: "Tree", file_path: str
    ) -> list[SecurityFinding]:
        """Check for dangerous function calls that can execute code."""
        findings: list[SecurityFinding] = []

        # Dangerous functions that execute code
        # Note: "eval" is intentionally in a list for the security scanner
        dangerous_functions = ["eval", "Function"]
        dangerous_methods = ["write", "writeln"]  # document.write

        # Check dangerous function calls
        for match in self._parser.find_call_expressions(
            tree, function_names=dangerous_functions
        ):
            func_name = match.text.split("(")[0].strip()
            findings.append(
                SecurityFinding(
                    id=self._next_finding_id(),
                    validator_id=self.id,
                    severity=Severity.CRITICAL,
                    category=FindingCategory.XSS,
                    title=f"Dangerous function call: {func_name}()",
                    description=(
                        f"The {func_name}() function executes arbitrary code. "
                        "If called with untrusted input, this can lead to "
                        "code injection attacks."
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
                        f"Avoid using {func_name}(). Consider using JSON.parse() "
                        "for data parsing or safer alternatives."
                    ),
                    auto_fixable=False,
                    confidence=0.95,
                    cwe_id="CWE-94",
                    owasp_id="A03:2021",
                )
            )

        # Check document.write calls
        for match in self._parser.find_call_expressions(
            tree, method_names=dangerous_methods
        ):
            findings.append(
                SecurityFinding(
                    id=self._next_finding_id(),
                    validator_id=self.id,
                    severity=Severity.HIGH,
                    category=FindingCategory.XSS,
                    title="Unsafe document.write() usage",
                    description=(
                        "document.write() can inject content directly into the DOM. "
                        "If used with untrusted data, this can lead to XSS attacks."
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
                        "Use DOM manipulation methods like appendChild() "
                        "or textContent instead of document.write()."
                    ),
                    auto_fixable=False,
                    confidence=0.85,
                    cwe_id="CWE-79",
                    owasp_id="A03:2021",
                )
            )

        return findings

    def _check_react_dangerous_html(
        self, tree: "Tree", file_path: str
    ) -> list[SecurityFinding]:
        """Check for React dangerouslySetInnerHTML usage."""
        findings: list[SecurityFinding] = []

        # The React attribute that bypasses XSS protection
        react_dangerous_attr = "dangerouslySetInnerHTML"

        for match in self._parser.find_jsx_attributes(tree, [react_dangerous_attr]):
            findings.append(
                SecurityFinding(
                    id=self._next_finding_id(),
                    validator_id=self.id,
                    severity=Severity.HIGH,
                    category=FindingCategory.XSS,
                    title="React dangerouslySetInnerHTML usage",
                    description=(
                        "dangerouslySetInnerHTML bypasses React's XSS protection. "
                        "If the content comes from untrusted sources, this can "
                        "lead to XSS attacks."
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
                        "Sanitize HTML content using DOMPurify before passing "
                        "to dangerouslySetInnerHTML, or use React's built-in "
                        "JSX escaping by rendering content normally."
                    ),
                    auto_fixable=False,
                    confidence=0.9,
                    cwe_id="CWE-79",
                    owasp_id="A03:2021",
                )
            )

        return findings

    def _check_javascript_protocol(
        self, tree: "Tree", file_path: str
    ) -> list[SecurityFinding]:
        """Check for javascript: protocol in href attributes."""
        findings: list[SecurityFinding] = []

        # Look for href attributes
        for match in self._parser.find_jsx_attributes(tree, ["href"]):
            # Check if the value contains javascript:
            if "javascript:" in match.text.lower():
                findings.append(
                    SecurityFinding(
                        id=self._next_finding_id(),
                        validator_id=self.id,
                        severity=Severity.HIGH,
                        category=FindingCategory.XSS,
                        title="javascript: protocol in href",
                        description=(
                            "Using javascript: protocol in href allows arbitrary "
                            "code execution when the link is clicked."
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
                            "Use onClick handlers instead of javascript: protocol, "
                            "or sanitize user-provided URLs."
                        ),
                        auto_fixable=False,
                        confidence=0.95,
                        cwe_id="CWE-79",
                        owasp_id="A03:2021",
                    )
                )

        return findings


class JWTValidator(BaseValidator):
    """Validator for insecure JWT handling.

    Detects:
    - jwt.decode() without verification
    - Algorithm confusion attacks (algorithm: "none")
    - Missing signature verification
    - Insecure token storage patterns

    CWE-347: Improper Verification of Cryptographic Signature
    """

    def __init__(self, parser: ASTParser | None = None) -> None:
        """Initialize the JWT validator.

        Args:
            parser: Optional AST parser instance.
        """
        self._parser = parser or get_parser()
        self._finding_counter = 0

    @property
    def id(self) -> str:
        """Return the validator ID."""
        return "sec-jwt-auditor"

    @property
    def name(self) -> str:
        """Return the validator name."""
        return "JWT Auditor"

    @property
    def description(self) -> str:
        """Return the validator description."""
        return "Detects insecure JWT handling patterns using AST analysis"

    def _next_finding_id(self) -> str:
        """Generate the next finding ID."""
        self._finding_counter += 1
        return f"jwt-{self._finding_counter:04d}"

    def validate_content(self, content: str, file_path: str) -> list[SecurityFinding]:
        """Validate content for JWT vulnerabilities.

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

        # Check for jwt.decode without verify
        findings.extend(self._check_jwt_decode_without_verify(tree, file_path, content))

        # Check for algorithm none
        findings.extend(self._check_algorithm_none(tree, file_path))

        # Check for insecure token storage
        findings.extend(self._check_insecure_storage(tree, file_path))

        return findings

    def _check_jwt_decode_without_verify(
        self, tree: "Tree", file_path: str, content: str
    ) -> list[SecurityFinding]:
        """Check for jwt.decode() calls without verification."""
        findings: list[SecurityFinding] = []

        # Find jwt.decode() calls
        for match in self._parser.find_call_expressions(tree, method_names=["decode"]):
            # Check if this is a JWT decode call with verification disabled
            is_jwt_context = "jwt" in match.text.lower() or "jsonwebtoken" in content.lower()
            has_verify_false = (
                "verify" in match.text.lower() and "false" in match.text.lower()
            )
            if is_jwt_context and has_verify_false:
                    findings.append(
                        SecurityFinding(
                            id=self._next_finding_id(),
                            validator_id=self.id,
                            severity=Severity.CRITICAL,
                            category=FindingCategory.CRYPTO,
                            title="JWT decoded without signature verification",
                            description=(
                                "jwt.decode() is called with verification disabled. "
                                "This allows attackers to forge tokens and bypass "
                                "authentication."
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
                                "Always verify JWT signatures using jwt.verify() "
                                "with a secure algorithm and secret/key."
                            ),
                            auto_fixable=False,
                            confidence=0.95,
                            cwe_id="CWE-347",
                            owasp_id="A02:2021",
                        )
                    )

        return findings

    def _check_algorithm_none(
        self, tree: "Tree", file_path: str
    ) -> list[SecurityFinding]:
        """Check for algorithm: 'none' in JWT options."""
        findings: list[SecurityFinding] = []

        # Search for string literals containing algorithm patterns
        algorithm_patterns = ["none", '"none"', "'none'"]
        for match in self._parser.find_string_literals(tree, algorithm_patterns):
            # Check context - is this in a JWT-related context?
            text_lower = match.text.lower()
            if "algorithm" in text_lower or text_lower.strip("'\"") == "none":
                findings.append(
                    SecurityFinding(
                        id=self._next_finding_id(),
                        validator_id=self.id,
                        severity=Severity.CRITICAL,
                        category=FindingCategory.CRYPTO,
                        title="JWT algorithm 'none' detected",
                        description=(
                            "Using algorithm 'none' in JWT configuration allows "
                            "unsigned tokens. Attackers can forge tokens without "
                            "needing the secret key."
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
                            "Use a secure algorithm like RS256 or HS256. "
                            "Never allow 'none' algorithm in production."
                        ),
                        auto_fixable=False,
                        confidence=0.7,  # Lower confidence as context needed
                        cwe_id="CWE-327",
                        owasp_id="A02:2021",
                    )
                )

        return findings

    def _check_insecure_storage(
        self, tree: "Tree", file_path: str
    ) -> list[SecurityFinding]:
        """Check for insecure JWT token storage patterns."""
        findings: list[SecurityFinding] = []

        # Check for localStorage.setItem with token patterns
        storage_methods = ["setItem"]
        for match in self._parser.find_call_expressions(tree, method_names=storage_methods):
            text_lower = match.text.lower()
            if "localstorage" in text_lower and (
                "token" in text_lower or "jwt" in text_lower or "auth" in text_lower
            ):
                findings.append(
                    SecurityFinding(
                        id=self._next_finding_id(),
                        validator_id=self.id,
                        severity=Severity.MEDIUM,
                        category=FindingCategory.DATA_EXPOSURE,
                        title="JWT stored in localStorage",
                        description=(
                            "Storing JWT tokens in localStorage makes them "
                            "vulnerable to XSS attacks. Any script on the page "
                            "can access localStorage."
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
                            "Use httpOnly cookies for JWT storage to prevent "
                            "XSS-based token theft. Consider using secure, "
                            "sameSite cookies."
                        ),
                        auto_fixable=False,
                        confidence=0.8,
                        cwe_id="CWE-922",
                        owasp_id="A05:2021",
                    )
                )

        return findings


class SecretValidator(BaseValidator):
    """Validator for hardcoded secrets and API keys.

    Detects:
    - Hardcoded API keys
    - Hardcoded passwords
    - Hardcoded tokens
    - Environment variable leaks

    CWE-798: Use of Hard-coded Credentials
    """

    # Patterns for detecting secrets (compiled regex)
    SECRET_PATTERNS: ClassVar[list[tuple[str, str]]] = [
        # AWS
        (r"AKIA[0-9A-Z]{16}", "AWS Access Key ID"),
        (r"[A-Za-z0-9/+=]{40}", "Potential AWS Secret Key"),
        # Generic API keys
        (r"api[_-]?key['\"]?\s*[:=]\s*['\"][a-zA-Z0-9]{20,}['\"]", "API Key"),
        (r"apikey['\"]?\s*[:=]\s*['\"][a-zA-Z0-9]{20,}['\"]", "API Key"),
        # Passwords
        (r"password['\"]?\s*[:=]\s*['\"][^'\"]+['\"]", "Hardcoded Password"),
        (r"passwd['\"]?\s*[:=]\s*['\"][^'\"]+['\"]", "Hardcoded Password"),
        # Tokens
        (r"token['\"]?\s*[:=]\s*['\"][a-zA-Z0-9_-]{20,}['\"]", "Hardcoded Token"),
        (r"bearer\s+[a-zA-Z0-9_-]{20,}", "Bearer Token"),
        # Private keys
        (r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----", "Private Key"),
        # GitHub
        (r"ghp_[a-zA-Z0-9]{36}", "GitHub Personal Access Token"),
        (r"github[_-]?token['\"]?\s*[:=]\s*['\"][^'\"]+['\"]", "GitHub Token"),
        # Slack
        (r"xox[baprs]-[0-9]{10,13}-[a-zA-Z0-9-]+", "Slack Token"),
        # Stripe
        (r"sk_live_[a-zA-Z0-9]{24,}", "Stripe Secret Key"),
        (r"pk_live_[a-zA-Z0-9]{24,}", "Stripe Publishable Key"),
        # Google
        (r"AIza[0-9A-Za-z-_]{35}", "Google API Key"),
        # SendGrid
        (r"SG\.[a-zA-Z0-9_-]{22}\.[a-zA-Z0-9_-]{43}", "SendGrid API Key"),
    ]

    def __init__(self, parser: ASTParser | None = None) -> None:
        """Initialize the secret validator.

        Args:
            parser: Optional AST parser instance.
        """
        self._parser = parser or get_parser()
        self._finding_counter = 0
        self._compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE), name)
            for pattern, name in self.SECRET_PATTERNS
        ]

    @property
    def id(self) -> str:
        """Return the validator ID."""
        return "sec-secret-scanner"

    @property
    def name(self) -> str:
        """Return the validator name."""
        return "Secret Scanner"

    @property
    def description(self) -> str:
        """Return the validator description."""
        return "Detects hardcoded secrets, API keys, and credentials"

    def _next_finding_id(self) -> str:
        """Generate the next finding ID."""
        self._finding_counter += 1
        return f"secret-{self._finding_counter:04d}"

    def validate_content(self, content: str, file_path: str) -> list[SecurityFinding]:
        """Validate content for hardcoded secrets.

        Args:
            content: The file content to validate.
            file_path: Path to the file.

        Returns:
            List of security findings.
        """
        findings: list[SecurityFinding] = []

        # Skip test files and example files
        if self._should_skip_file(file_path):
            return findings

        try:
            tree = self._parser.parse_file_content(content, file_path)
        except ValueError:
            # For non-JS/TS files, fall back to line-by-line analysis
            return self._scan_raw_content(content, file_path)

        # Check string literals for secrets
        findings.extend(self._check_string_literals(tree, file_path))

        # Check for NEXT_PUBLIC_ misuse with sensitive data
        findings.extend(self._check_next_public_env(tree, file_path))

        return findings

    def _should_skip_file(self, file_path: str) -> bool:
        """Check if file should be skipped."""
        skip_patterns = [
            ".test.",
            ".spec.",
            "_test.",
            "_spec.",
            "/test/",
            "/tests/",
            "/__tests__/",
            ".example.",
            ".sample.",
            "/examples/",
            "/fixtures/",
        ]
        return any(pattern in file_path.lower() for pattern in skip_patterns)

    def _check_string_literals(
        self, tree: "Tree", file_path: str
    ) -> list[SecurityFinding]:
        """Check string literals for secret patterns."""
        findings: list[SecurityFinding] = []

        for match in self._parser.find_string_literals(tree):
            for pattern, secret_type in self._compiled_patterns:
                if pattern.search(match.text):
                    findings.append(
                        SecurityFinding(
                            id=self._next_finding_id(),
                            validator_id=self.id,
                            severity=Severity.CRITICAL,
                            category=FindingCategory.DATA_EXPOSURE,
                            title=f"Hardcoded {secret_type} detected",
                            description=(
                                f"A {secret_type} appears to be hardcoded in the source code. "
                                "This exposes sensitive credentials and should never be "
                                "committed to version control."
                            ),
                            location=CodeLocation(
                                file_path=file_path,
                                line_start=match.location.line_start,
                                line_end=match.location.line_end,
                                column_start=match.location.column_start,
                                column_end=match.location.column_end,
                                snippet=self._redact_secret(match.text),
                            ),
                            recommendation=(
                                "Move secrets to environment variables. "
                                "Use a secrets manager for production. "
                                "Rotate this credential immediately."
                            ),
                            auto_fixable=False,
                            confidence=0.9,
                            cwe_id="CWE-798",
                            owasp_id="A07:2021",
                        )
                    )
                    break  # One finding per string

        return findings

    def _check_next_public_env(
        self, tree: "Tree", file_path: str
    ) -> list[SecurityFinding]:
        """Check for sensitive data in NEXT_PUBLIC_ environment variables."""
        findings: list[SecurityFinding] = []

        # Sensitive words that shouldn't be in public env vars
        sensitive_words = ["secret", "key", "password", "token", "private", "credential"]

        for match in self._parser.find_string_literals(tree, ["NEXT_PUBLIC_"]):
            text_lower = match.text.lower()
            for word in sensitive_words:
                if word in text_lower:
                    findings.append(
                        SecurityFinding(
                            id=self._next_finding_id(),
                            validator_id=self.id,
                            severity=Severity.HIGH,
                            category=FindingCategory.DATA_EXPOSURE,
                            title="Sensitive data in NEXT_PUBLIC_ env variable",
                            description=(
                                "NEXT_PUBLIC_ environment variables are exposed to "
                                "the browser. Sensitive data like secrets, keys, or "
                                "tokens should never use this prefix."
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
                                "Remove NEXT_PUBLIC_ prefix for sensitive variables. "
                                "Access them only server-side via getServerSideProps "
                                "or API routes."
                            ),
                            auto_fixable=False,
                            confidence=0.85,
                            cwe_id="CWE-200",
                            owasp_id="A01:2021",
                        )
                    )
                    break

        return findings

    def _scan_raw_content(
        self, content: str, file_path: str
    ) -> list[SecurityFinding]:
        """Scan raw content line by line for secrets."""
        findings: list[SecurityFinding] = []

        for line_num, line in enumerate(content.splitlines(), start=1):
            for pattern, secret_type in self._compiled_patterns:
                if pattern.search(line):
                    findings.append(
                        SecurityFinding(
                            id=self._next_finding_id(),
                            validator_id=self.id,
                            severity=Severity.CRITICAL,
                            category=FindingCategory.DATA_EXPOSURE,
                            title=f"Hardcoded {secret_type} detected",
                            description=(
                                f"A {secret_type} appears to be hardcoded in the source code."
                            ),
                            location=CodeLocation(
                                file_path=file_path,
                                line_start=line_num,
                                line_end=line_num,
                                snippet=self._redact_secret(line.strip()),
                            ),
                            recommendation=(
                                "Move secrets to environment variables. "
                                "Use a secrets manager for production."
                            ),
                            auto_fixable=False,
                            confidence=0.85,
                            cwe_id="CWE-798",
                            owasp_id="A07:2021",
                        )
                    )
                    break

        return findings

    def _redact_secret(self, text: str, visible_chars: int = 4) -> str:
        """Redact most of a secret for safe display.

        Args:
            text: The text containing the secret.
            visible_chars: Number of characters to show at start and end.

        Returns:
            Redacted text.
        """
        if len(text) <= visible_chars * 2 + 3:
            return "*" * len(text)

        return text[:visible_chars] + "***REDACTED***" + text[-visible_chars:]
