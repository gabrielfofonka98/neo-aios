"""Pattern definitions for regex validators.

This module provides the PatternDefinition dataclass and predefined patterns
for common security issues like CORS misconfigurations, missing headers,
error leaks, and rate limiting issues.

Example:
    >>> from aios.security.validators.regex.patterns import (
    ...     PatternDefinition,
    ...     CORS_PATTERNS,
    ... )
    >>>
    >>> for pattern in CORS_PATTERNS:
    ...     print(f"{pattern.id}: {pattern.title}")
"""

from dataclasses import dataclass
from dataclasses import field

from aios.security.models import FindingCategory
from aios.security.models import Severity


@dataclass(frozen=True)
class PatternDefinition:
    """Definition of a security pattern to match.

    Attributes:
        id: Unique pattern identifier.
        pattern: The regex pattern string.
        title: Short title for findings from this pattern.
        description: Detailed description of the issue.
        severity: Severity level of findings.
        recommendation: How to fix the issue.
        category: Finding category (optional, uses validator default if None).
        confidence: Confidence score (0.0-1.0).
        cwe_id: CWE identifier if applicable.
        owasp_id: OWASP identifier if applicable.
        case_insensitive: Whether to match case-insensitively.
        multiline: Whether to enable multiline mode.
        include_files: Regex patterns for files to include.
        exclude_files: Regex patterns for files to exclude.
        exclude_patterns: Patterns that indicate false positives.
        redact_match: Whether to redact the matched text in reports.
        auto_fixable: Whether this issue can be auto-fixed.
        fix_snippet: Suggested fix code (if auto_fixable).
    """

    id: str
    pattern: str
    title: str
    description: str
    severity: Severity
    recommendation: str
    category: FindingCategory | None = None
    confidence: float = 0.9
    cwe_id: str | None = None
    owasp_id: str | None = None
    case_insensitive: bool = True
    multiline: bool = False
    include_files: list[str] = field(default_factory=list)
    exclude_files: list[str] = field(default_factory=list)
    exclude_patterns: list[str] = field(default_factory=list)
    redact_match: bool = False
    auto_fixable: bool = False
    fix_snippet: str | None = None


# =============================================================================
# CORS Patterns
# =============================================================================

CORS_WILDCARD_ORIGIN = PatternDefinition(
    id="cors-wildcard-origin",
    pattern=r"Access-Control-Allow-Origin.*['\"]?\s*\*\s*['\"]?",
    title="CORS wildcard origin detected",
    description=(
        "Access-Control-Allow-Origin is set to '*', allowing any origin to access "
        "resources. This can expose sensitive data to malicious sites."
    ),
    severity=Severity.HIGH,
    recommendation=(
        "Replace '*' with specific allowed origins. Use a whitelist of trusted "
        "domains instead of allowing all origins."
    ),
    category=FindingCategory.CONFIG,
    cwe_id="CWE-942",
    owasp_id="A05:2021",
    confidence=0.95,
)

CORS_ORIGIN_REFLECTION = PatternDefinition(
    id="cors-origin-reflection",
    pattern=r'(origin|req\.headers\[.origin.\]|request\.origin)',
    title="Potential CORS origin reflection",
    description=(
        "The code appears to reflect the request origin in the CORS response. "
        "This can be exploited by attackers to bypass CORS restrictions."
    ),
    severity=Severity.MEDIUM,
    recommendation=(
        "Validate the origin against a whitelist of allowed domains before "
        "reflecting it in the Access-Control-Allow-Origin header."
    ),
    category=FindingCategory.CONFIG,
    cwe_id="CWE-346",
    confidence=0.7,
    exclude_patterns=[
        r"whitelist",
        r"allowedOrigins",
        r"validOrigins",
        r"originAllowed",
        r"isAllowed",
    ],
)

CORS_CREDENTIALS_TRUE = PatternDefinition(
    id="cors-credentials-true",
    pattern=r'Access-Control-Allow-Credentials["\']?\s*[:\=]\s*["\']?true',
    title="CORS credentials enabled",
    description=(
        "Access-Control-Allow-Credentials is set to true. When combined with "
        "permissive origin settings, this can expose authenticated resources."
    ),
    severity=Severity.MEDIUM,
    recommendation=(
        "Ensure Access-Control-Allow-Origin is set to specific trusted origins "
        "when credentials are enabled. Never use '*' with credentials."
    ),
    category=FindingCategory.CONFIG,
    cwe_id="CWE-942",
    confidence=0.85,
)

CSRF_DISABLED = PatternDefinition(
    id="csrf-disabled",
    pattern=r'(csrf\s*[:\=]\s*false|disableCsrf|csrfProtection\s*[:\=]\s*false)',
    title="CSRF protection disabled",
    description=(
        "CSRF protection appears to be explicitly disabled. This leaves the "
        "application vulnerable to cross-site request forgery attacks."
    ),
    severity=Severity.HIGH,
    recommendation=(
        "Enable CSRF protection. Use anti-CSRF tokens for state-changing requests. "
        "Consider using SameSite cookie attribute."
    ),
    category=FindingCategory.CONFIG,
    cwe_id="CWE-352",
    owasp_id="A01:2021",
    confidence=0.9,
)

CORS_PATTERNS: list[PatternDefinition] = [
    CORS_WILDCARD_ORIGIN,
    CORS_ORIGIN_REFLECTION,
    CORS_CREDENTIALS_TRUE,
    CSRF_DISABLED,
]


# =============================================================================
# Security Headers Patterns
# =============================================================================

MISSING_CSP = PatternDefinition(
    id="headers-missing-csp",
    pattern=r'(Content-Security-Policy|helmet\.contentSecurityPolicy)',
    title="Content-Security-Policy configuration found",
    description=(
        "Content-Security-Policy header configuration detected. Verify it's "
        "properly configured to prevent XSS and data injection attacks."
    ),
    severity=Severity.INFO,
    recommendation=(
        "Ensure CSP is properly configured with restrictive directives. "
        "Avoid unsafe directives unless absolutely necessary."
    ),
    category=FindingCategory.CONFIG,
    cwe_id="CWE-1021",
    confidence=0.6,
)

UNSAFE_CSP_INLINE = PatternDefinition(
    id="headers-unsafe-csp-inline",
    pattern=r"'unsafe-inline'",
    title="Unsafe CSP directive: unsafe-inline",
    description=(
        "The Content-Security-Policy contains 'unsafe-inline'. "
        "This directive weakens XSS protection significantly by allowing inline scripts."
    ),
    severity=Severity.MEDIUM,
    recommendation=(
        "Remove 'unsafe-inline' by using nonces or hashes for inline scripts. "
        "Refactor inline scripts to external files where possible."
    ),
    category=FindingCategory.CONFIG,
    cwe_id="CWE-1021",
    owasp_id="A03:2021",
    confidence=0.9,
)

UNSAFE_CSP_DYNAMIC = PatternDefinition(
    id="headers-unsafe-csp-dynamic",
    pattern=r"'unsafe-dynamic'",
    title="Unsafe CSP directive: unsafe-dynamic code execution",
    description=(
        "The Content-Security-Policy contains directives that allow dynamic code execution. "
        "This weakens XSS protection by allowing runtime code generation."
    ),
    severity=Severity.MEDIUM,
    recommendation=(
        "Remove unsafe dynamic code execution by refactoring code that uses "
        "dynamic code generation patterns."
    ),
    category=FindingCategory.CONFIG,
    cwe_id="CWE-1021",
    owasp_id="A03:2021",
    confidence=0.9,
)

MISSING_XFRAME = PatternDefinition(
    id="headers-missing-xframe",
    pattern=r'(X-Frame-Options|frameGuard|frameguard)',
    title="X-Frame-Options configuration found",
    description=(
        "X-Frame-Options header configuration detected. Verify it prevents "
        "clickjacking attacks by denying framing or restricting to same origin."
    ),
    severity=Severity.INFO,
    recommendation=(
        "Set X-Frame-Options to 'DENY' or 'SAMEORIGIN'. Consider also using "
        "Content-Security-Policy frame-ancestors directive."
    ),
    category=FindingCategory.CONFIG,
    cwe_id="CWE-1021",
    confidence=0.6,
)

MISSING_HSTS = PatternDefinition(
    id="headers-missing-hsts",
    pattern=r'(Strict-Transport-Security|hsts)',
    title="HSTS configuration found",
    description=(
        "HTTP Strict Transport Security configuration detected. Verify it's "
        "properly configured to enforce HTTPS connections."
    ),
    severity=Severity.INFO,
    recommendation=(
        "Configure HSTS with a long max-age (at least 1 year). Consider "
        "includeSubDomains and preload directives for stronger protection."
    ),
    category=FindingCategory.CONFIG,
    cwe_id="CWE-319",
    confidence=0.6,
)

HTTP_ONLY_FALSE = PatternDefinition(
    id="headers-httponly-false",
    pattern=r'httpOnly\s*[:\=]\s*false',
    title="Cookie httpOnly disabled",
    description=(
        "Cookie is configured with httpOnly=false, making it accessible to "
        "JavaScript and vulnerable to XSS attacks."
    ),
    severity=Severity.HIGH,
    recommendation=(
        "Set httpOnly to true for session cookies and other sensitive cookies "
        "to prevent JavaScript access."
    ),
    category=FindingCategory.CONFIG,
    cwe_id="CWE-1004",
    owasp_id="A05:2021",
    confidence=0.95,
)

SECURE_FALSE = PatternDefinition(
    id="headers-secure-false",
    pattern=r'secure\s*[:\=]\s*false',
    title="Cookie secure flag disabled",
    description=(
        "Cookie is configured with secure=false, allowing it to be sent over "
        "unencrypted HTTP connections."
    ),
    severity=Severity.MEDIUM,
    recommendation=(
        "Set secure to true for all cookies in production environments to "
        "ensure they are only sent over HTTPS."
    ),
    category=FindingCategory.CONFIG,
    cwe_id="CWE-614",
    owasp_id="A05:2021",
    confidence=0.9,
)

SAMESITE_NONE = PatternDefinition(
    id="headers-samesite-none",
    pattern=r'sameSite\s*[:\=]\s*["\']?none',
    title="Cookie SameSite set to None",
    description=(
        "Cookie SameSite attribute is set to 'None', allowing cross-site "
        "requests. This may be intentional for legitimate cross-site use cases."
    ),
    severity=Severity.LOW,
    recommendation=(
        "Use SameSite=Lax or SameSite=Strict when possible. If 'None' is "
        "required, ensure the cookie is also marked as Secure."
    ),
    category=FindingCategory.CONFIG,
    cwe_id="CWE-1275",
    confidence=0.8,
)

HEADERS_PATTERNS: list[PatternDefinition] = [
    MISSING_CSP,
    UNSAFE_CSP_INLINE,
    UNSAFE_CSP_DYNAMIC,
    MISSING_XFRAME,
    MISSING_HSTS,
    HTTP_ONLY_FALSE,
    SECURE_FALSE,
    SAMESITE_NONE,
]


# =============================================================================
# Error Leak Patterns
# =============================================================================

STACK_TRACE_EXPOSED = PatternDefinition(
    id="error-stack-trace",
    pattern=r'(\.stack|stackTrace|stack_trace|Error\.stack)',
    title="Stack trace potentially exposed",
    description=(
        "Stack trace information may be exposed to clients. This can reveal "
        "internal implementation details, file paths, and framework versions."
    ),
    severity=Severity.MEDIUM,
    recommendation=(
        "Never send stack traces to clients in production. Log errors "
        "server-side and return generic error messages to users."
    ),
    category=FindingCategory.DATA_EXPOSURE,
    cwe_id="CWE-209",
    owasp_id="A04:2021",
    confidence=0.7,
    exclude_patterns=[
        r"console\.",
        r"logger\.",
        r"log\.",
        r"debug",
        r"process\.env",
    ],
)

VERBOSE_ERROR = PatternDefinition(
    id="error-verbose",
    pattern=r'(res\.send\(err|res\.json\(\{.*error.*\}|response\.json\(.*exception)',
    title="Verbose error response detected",
    description=(
        "Error details appear to be sent directly to the client. This may "
        "expose sensitive information about the application internals."
    ),
    severity=Severity.MEDIUM,
    recommendation=(
        "Use a centralized error handler that returns safe error messages "
        "to clients while logging full details server-side."
    ),
    category=FindingCategory.DATA_EXPOSURE,
    cwe_id="CWE-209",
    confidence=0.75,
    exclude_patterns=[r"production", r"sanitize", r"safe"],
)

DEBUG_MODE = PatternDefinition(
    id="error-debug-mode",
    pattern=r'(DEBUG\s*[:\=]\s*["\']?true|debug\s*[:\=]\s*true|NODE_ENV.*development)',
    title="Debug mode potentially enabled",
    description=(
        "Debug mode appears to be enabled. In production, debug mode can "
        "expose sensitive information and verbose error messages."
    ),
    severity=Severity.LOW,
    recommendation=(
        "Ensure debug mode is disabled in production environments. Use "
        "environment variables to control debug settings."
    ),
    category=FindingCategory.CONFIG,
    cwe_id="CWE-489",
    confidence=0.65,
    exclude_files=[r"\.env\.example", r"\.env\.development", r"\.env\.local"],
)

SQL_ERROR_EXPOSED = PatternDefinition(
    id="error-sql-exposed",
    pattern=r'(sqlMessage|SQL Error|ORA-\d+|PG::|mysql_error)',
    title="SQL error potentially exposed",
    description=(
        "Database error messages may be exposed to clients. This can reveal "
        "database structure, query patterns, and potentially sensitive data."
    ),
    severity=Severity.HIGH,
    recommendation=(
        "Never expose raw database errors to clients. Catch database "
        "exceptions and return generic error messages."
    ),
    category=FindingCategory.DATA_EXPOSURE,
    cwe_id="CWE-209",
    owasp_id="A04:2021",
    confidence=0.85,
)

INTERNAL_PATH_EXPOSED = PatternDefinition(
    id="error-internal-path",
    pattern=r'(/Users/|/home/|C:\\\\Users|/var/www/|/app/src/)',
    title="Internal file path potentially exposed",
    description=(
        "Internal file system paths may be exposed in error messages. This "
        "reveals server configuration and can aid attackers in exploitation."
    ),
    severity=Severity.MEDIUM,
    recommendation=(
        "Sanitize error messages to remove file system paths. Use relative "
        "paths in logs and never expose absolute paths to clients."
    ),
    category=FindingCategory.DATA_EXPOSURE,
    cwe_id="CWE-200",
    confidence=0.8,
    exclude_files=[r"\.md$", r"README", r"CHANGELOG"],
)

ERROR_PATTERNS: list[PatternDefinition] = [
    STACK_TRACE_EXPOSED,
    VERBOSE_ERROR,
    DEBUG_MODE,
    SQL_ERROR_EXPOSED,
    INTERNAL_PATH_EXPOSED,
]


# =============================================================================
# Rate Limiting Patterns
# =============================================================================

NO_RATE_LIMIT_AUTH = PatternDefinition(
    id="ratelimit-auth-missing",
    pattern=r'(\/login|\/signin|\/auth|\/api\/auth)',
    title="Authentication endpoint - verify rate limiting",
    description=(
        "Authentication endpoint detected. These endpoints are prime targets "
        "for brute force attacks and should have strict rate limiting."
    ),
    severity=Severity.INFO,
    recommendation=(
        "Implement rate limiting on authentication endpoints. Consider "
        "progressive delays, account lockouts, and CAPTCHA for repeated failures."
    ),
    category=FindingCategory.ACCESS_CONTROL,
    cwe_id="CWE-307",
    owasp_id="A07:2021",
    confidence=0.6,
    exclude_patterns=[r"rateLimit", r"throttle", r"limiter"],
)

NO_RATE_LIMIT_API = PatternDefinition(
    id="ratelimit-api-missing",
    pattern=r'(\/api\/.*POST|router\.post|app\.post)',
    title="POST endpoint - verify rate limiting",
    description=(
        "POST endpoint detected without obvious rate limiting. APIs accepting "
        "data should be protected against abuse and DoS attacks."
    ),
    severity=Severity.LOW,
    recommendation=(
        "Implement rate limiting middleware for API endpoints. Use different "
        "limits based on endpoint sensitivity and expected usage patterns."
    ),
    category=FindingCategory.ACCESS_CONTROL,
    cwe_id="CWE-770",
    confidence=0.5,
    exclude_patterns=[r"rateLimit", r"throttle", r"limiter"],
)

NO_RATE_LIMIT_PASSWORD = PatternDefinition(
    id="ratelimit-password-reset",
    pattern=r'(\/forgot-password|\/reset-password|\/password\/reset)',
    title="Password reset endpoint - verify rate limiting",
    description=(
        "Password reset endpoint detected. These should be rate limited to "
        "prevent enumeration attacks and email flooding."
    ),
    severity=Severity.MEDIUM,
    recommendation=(
        "Implement strict rate limiting on password reset endpoints. Limit "
        "by IP and email address to prevent abuse."
    ),
    category=FindingCategory.ACCESS_CONTROL,
    cwe_id="CWE-307",
    owasp_id="A07:2021",
    confidence=0.75,
    exclude_patterns=[r"rateLimit", r"throttle", r"limiter"],
)

NO_RATE_LIMIT_SIGNUP = PatternDefinition(
    id="ratelimit-signup-missing",
    pattern=r'(\/signup|\/register|\/create-account)',
    title="Signup endpoint - verify rate limiting",
    description=(
        "User registration endpoint detected. These should be rate limited "
        "to prevent spam accounts and automated abuse."
    ),
    severity=Severity.MEDIUM,
    recommendation=(
        "Implement rate limiting on registration endpoints. Consider CAPTCHA "
        "and email verification to prevent automated signups."
    ),
    category=FindingCategory.ACCESS_CONTROL,
    cwe_id="CWE-770",
    confidence=0.7,
    exclude_patterns=[r"rateLimit", r"throttle", r"limiter", r"captcha"],
)

RATE_LIMIT_PATTERNS: list[PatternDefinition] = [
    NO_RATE_LIMIT_AUTH,
    NO_RATE_LIMIT_API,
    NO_RATE_LIMIT_PASSWORD,
    NO_RATE_LIMIT_SIGNUP,
]


# =============================================================================
# All Patterns
# =============================================================================

ALL_PATTERNS: list[PatternDefinition] = (
    CORS_PATTERNS + HEADERS_PATTERNS + ERROR_PATTERNS + RATE_LIMIT_PATTERNS
)
