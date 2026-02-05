"""Tests for regex-based security validators.

Tests cover:
- RegexValidator base class
- PatternDefinition dataclass
- CORSValidator
- HeadersValidator
- ErrorLeakValidator
- RateLimitValidator
"""

from pathlib import Path

import pytest

from aios.security.models import FindingCategory, Severity
from aios.security.validators.regex import (
    ALL_PATTERNS,
    CORS_PATTERNS,
    ERROR_PATTERNS,
    HEADERS_PATTERNS,
    RATE_LIMIT_PATTERNS,
    CORSValidator,
    ErrorLeakValidator,
    HeadersValidator,
    PatternDefinition,
    RateLimitValidator,
    RegexValidator,
    register_all_regex_validators,
)
from aios.security.validators.registry import ValidatorRegistry


class TestPatternDefinition:
    """Tests for PatternDefinition dataclass."""

    def test_minimal_pattern(self) -> None:
        """Test creating pattern with required fields only."""
        pattern = PatternDefinition(
            id="test-pattern",
            pattern=r"test",
            title="Test Pattern",
            description="A test pattern",
            severity=Severity.LOW,
            recommendation="Fix it",
        )

        assert pattern.id == "test-pattern"
        assert pattern.pattern == r"test"
        assert pattern.title == "Test Pattern"
        assert pattern.severity == Severity.LOW
        assert pattern.category is None
        assert pattern.confidence == 0.9
        assert pattern.case_insensitive is True
        assert pattern.multiline is False
        assert pattern.include_files == []
        assert pattern.exclude_files == []
        assert pattern.exclude_patterns == []
        assert pattern.redact_match is False
        assert pattern.auto_fixable is False
        assert pattern.fix_snippet is None

    def test_full_pattern(self) -> None:
        """Test creating pattern with all fields."""
        pattern = PatternDefinition(
            id="full-pattern",
            pattern=r"secret.*key",
            title="Secret Key Detected",
            description="A secret key was found",
            severity=Severity.CRITICAL,
            recommendation="Remove the secret",
            category=FindingCategory.DATA_EXPOSURE,
            confidence=0.95,
            cwe_id="CWE-798",
            owasp_id="A02:2021",
            case_insensitive=False,
            multiline=True,
            include_files=[r"\.ts$", r"\.js$"],
            exclude_files=[r"test", r"spec"],
            exclude_patterns=[r"example", r"placeholder"],
            redact_match=True,
            auto_fixable=True,
            fix_snippet="const key = process.env.SECRET_KEY;",
        )

        assert pattern.id == "full-pattern"
        assert pattern.severity == Severity.CRITICAL
        assert pattern.category == FindingCategory.DATA_EXPOSURE
        assert pattern.confidence == 0.95
        assert pattern.cwe_id == "CWE-798"
        assert pattern.owasp_id == "A02:2021"
        assert pattern.case_insensitive is False
        assert pattern.multiline is True
        assert len(pattern.include_files) == 2
        assert len(pattern.exclude_files) == 2
        assert len(pattern.exclude_patterns) == 2
        assert pattern.redact_match is True
        assert pattern.auto_fixable is True
        assert pattern.fix_snippet is not None

    def test_pattern_is_frozen(self) -> None:
        """Test that PatternDefinition is immutable."""
        pattern = PatternDefinition(
            id="frozen",
            pattern=r"test",
            title="Frozen",
            description="Cannot modify",
            severity=Severity.LOW,
            recommendation="...",
        )

        with pytest.raises(AttributeError):
            pattern.id = "modified"  # type: ignore[misc]


class TestPatternCollections:
    """Tests for predefined pattern collections."""

    def test_cors_patterns_exist(self) -> None:
        """Test CORS patterns are defined."""
        assert len(CORS_PATTERNS) > 0
        for pattern in CORS_PATTERNS:
            assert isinstance(pattern, PatternDefinition)
            assert pattern.id.startswith("cors") or pattern.id.startswith("csrf")

    def test_headers_patterns_exist(self) -> None:
        """Test header patterns are defined."""
        assert len(HEADERS_PATTERNS) > 0
        for pattern in HEADERS_PATTERNS:
            assert isinstance(pattern, PatternDefinition)
            assert pattern.id.startswith("headers")

    def test_error_patterns_exist(self) -> None:
        """Test error patterns are defined."""
        assert len(ERROR_PATTERNS) > 0
        for pattern in ERROR_PATTERNS:
            assert isinstance(pattern, PatternDefinition)
            assert pattern.id.startswith("error")

    def test_ratelimit_patterns_exist(self) -> None:
        """Test rate limit patterns are defined."""
        assert len(RATE_LIMIT_PATTERNS) > 0
        for pattern in RATE_LIMIT_PATTERNS:
            assert isinstance(pattern, PatternDefinition)
            assert pattern.id.startswith("ratelimit")

    def test_all_patterns_combined(self) -> None:
        """Test ALL_PATTERNS contains all pattern collections."""
        expected_count = (
            len(CORS_PATTERNS)
            + len(HEADERS_PATTERNS)
            + len(ERROR_PATTERNS)
            + len(RATE_LIMIT_PATTERNS)
        )
        assert len(ALL_PATTERNS) == expected_count


class TestRegexValidatorBase:
    """Tests for RegexValidator base class."""

    def test_custom_regex_validator(self, tmp_path: Path) -> None:
        """Test implementing a custom regex validator."""

        class CustomValidator(RegexValidator):
            @property
            def id(self) -> str:
                return "custom-validator"

            @property
            def name(self) -> str:
                return "Custom Validator"

            @property
            def description(self) -> str:
                return "A custom validator"

            @property
            def patterns(self) -> list[PatternDefinition]:
                return [
                    PatternDefinition(
                        id="custom-pattern",
                        pattern=r"DANGEROUS_PATTERN",
                        title="Dangerous pattern found",
                        description="Found something dangerous",
                        severity=Severity.HIGH,
                        recommendation="Remove it",
                    )
                ]

        # Create test file with dangerous pattern
        test_file = tmp_path / "test.ts"
        test_file.write_text("const x = DANGEROUS_PATTERN;")

        validator = CustomValidator()
        result = validator.validate(test_file)

        assert result.has_findings is True
        assert len(result.findings) == 1
        assert result.findings[0].severity == Severity.HIGH
        assert result.findings[0].title == "Dangerous pattern found"

    def test_pattern_compilation_cached(self) -> None:
        """Test that patterns are compiled and cached."""

        class CachingValidator(RegexValidator):
            @property
            def id(self) -> str:
                return "caching"

            @property
            def name(self) -> str:
                return "Caching"

            @property
            def description(self) -> str:
                return "Tests caching"

            @property
            def patterns(self) -> list[PatternDefinition]:
                return [
                    PatternDefinition(
                        id="p1",
                        pattern=r"test",
                        title="Test",
                        description="...",
                        severity=Severity.LOW,
                        recommendation="...",
                    )
                ]

        validator = CachingValidator()

        # First call compiles patterns
        patterns1 = validator.get_compiled_patterns()
        # Second call returns cached
        patterns2 = validator.get_compiled_patterns()

        assert patterns1 is patterns2

    def test_false_positive_detection(self, tmp_path: Path) -> None:
        """Test that false positives are filtered."""

        class FPValidator(RegexValidator):
            @property
            def id(self) -> str:
                return "fp-validator"

            @property
            def name(self) -> str:
                return "FP Validator"

            @property
            def description(self) -> str:
                return "Tests false positives"

            @property
            def patterns(self) -> list[PatternDefinition]:
                return [
                    PatternDefinition(
                        id="secret",
                        pattern=r"api_key\s*=",
                        title="API key detected",
                        description="...",
                        severity=Severity.HIGH,
                        recommendation="...",
                    )
                ]

        # Create file with real issue
        real_file = tmp_path / "real.ts"
        real_file.write_text('const api_key = "sk_live_abc123";')

        # Create file with example (false positive)
        example_file = tmp_path / "example.ts"
        example_file.write_text('const api_key = "your_api_key_here";')

        validator = FPValidator()

        # Real issue should be found
        real_result = validator.validate(real_file)
        assert real_result.has_findings is True

        # Example should be filtered
        example_result = validator.validate(example_file)
        assert example_result.has_findings is False

    def test_redaction(self, tmp_path: Path) -> None:
        """Test that sensitive data is redacted."""

        class RedactValidator(RegexValidator):
            @property
            def id(self) -> str:
                return "redact"

            @property
            def name(self) -> str:
                return "Redact"

            @property
            def description(self) -> str:
                return "Tests redaction"

            @property
            def patterns(self) -> list[PatternDefinition]:
                return [
                    PatternDefinition(
                        id="secret",
                        pattern=r"sk_live_[a-zA-Z0-9]+",
                        title="Secret key detected",
                        description="...",
                        severity=Severity.CRITICAL,
                        recommendation="...",
                        redact_match=True,
                    )
                ]

        test_file = tmp_path / "secrets.ts"
        test_file.write_text('const key = "sk_live_abcdefgh12345678";')

        validator = RedactValidator()
        result = validator.validate(test_file)

        assert result.has_findings is True
        # Check that the snippet is redacted
        snippet = result.findings[0].location.snippet
        assert snippet is not None
        assert "sk_l" in snippet  # First 4 chars visible
        assert "*" in snippet  # Middle redacted
        assert "78" in snippet  # Last 2 chars visible
        assert "abcdefgh12345678" not in snippet  # Full secret not visible


class TestCORSValidator:
    """Tests for CORSValidator."""

    def test_validator_properties(self) -> None:
        """Test validator has correct properties."""
        validator = CORSValidator()
        assert validator.id == "sec-cors-csrf-checker"
        assert validator.name == "CORS & CSRF Checker"
        assert len(validator.description) > 0
        assert validator.category == FindingCategory.CONFIG

    def test_detects_wildcard_origin(self, tmp_path: Path) -> None:
        """Test detection of Access-Control-Allow-Origin: *."""
        test_file = tmp_path / "cors.ts"
        test_file.write_text(
            """
            res.setHeader('Access-Control-Allow-Origin', '*');
            """
        )

        validator = CORSValidator()
        result = validator.validate(test_file)

        assert result.has_findings is True
        assert any("wildcard" in f.title.lower() for f in result.findings)

    def test_detects_csrf_disabled(self, tmp_path: Path) -> None:
        """Test detection of CSRF protection disabled."""
        test_file = tmp_path / "config.ts"
        test_file.write_text(
            """
            const config = {
                csrf: false,
                other: true
            };
            """
        )

        validator = CORSValidator()
        result = validator.validate(test_file)

        assert result.has_findings is True
        assert any("csrf" in f.title.lower() for f in result.findings)

    def test_safe_cors_not_flagged(self, tmp_path: Path) -> None:
        """Test that proper CORS config is not flagged."""
        test_file = tmp_path / "safe.ts"
        test_file.write_text(
            """
            res.setHeader('Access-Control-Allow-Origin', 'https://myapp.com');
            """
        )

        validator = CORSValidator()
        result = validator.validate(test_file)

        # Should not find wildcard issue
        wildcard_findings = [f for f in result.findings if "wildcard" in f.title.lower()]
        assert len(wildcard_findings) == 0


class TestHeadersValidator:
    """Tests for HeadersValidator."""

    def test_validator_properties(self) -> None:
        """Test validator has correct properties."""
        validator = HeadersValidator()
        assert validator.id == "sec-header-inspector"
        assert validator.name == "Security Headers Inspector"
        assert len(validator.description) > 0

    def test_detects_unsafe_csp(self, tmp_path: Path) -> None:
        """Test detection of unsafe CSP directives."""
        test_file = tmp_path / "csp.ts"
        test_file.write_text(
            """
            const csp = "default-src 'self'; script-src 'unsafe-inline'";
            """
        )

        validator = HeadersValidator()
        result = validator.validate(test_file)

        assert result.has_findings is True
        assert any("unsafe" in f.title.lower() for f in result.findings)

    def test_detects_httponly_false(self, tmp_path: Path) -> None:
        """Test detection of httpOnly: false."""
        test_file = tmp_path / "cookie.ts"
        test_file.write_text(
            """
            res.cookie('session', token, {
                httpOnly: false,
                secure: true
            });
            """
        )

        validator = HeadersValidator()
        result = validator.validate(test_file)

        assert result.has_findings is True
        assert any("httponly" in f.title.lower() for f in result.findings)

    def test_detects_secure_false(self, tmp_path: Path) -> None:
        """Test detection of secure: false."""
        test_file = tmp_path / "cookie.ts"
        test_file.write_text(
            """
            res.cookie('session', token, {
                httpOnly: true,
                secure: false
            });
            """
        )

        validator = HeadersValidator()
        result = validator.validate(test_file)

        assert result.has_findings is True
        assert any("secure" in f.title.lower() for f in result.findings)


class TestErrorLeakValidator:
    """Tests for ErrorLeakValidator."""

    def test_validator_properties(self) -> None:
        """Test validator has correct properties."""
        validator = ErrorLeakValidator()
        assert validator.id == "sec-error-leak-detector"
        assert validator.name == "Error & Info Leak Detector"
        assert validator.category == FindingCategory.DATA_EXPOSURE

    def test_detects_stack_trace(self, tmp_path: Path) -> None:
        """Test detection of stack trace exposure."""
        test_file = tmp_path / "error.ts"
        test_file.write_text(
            """
            catch (err) {
                res.json({ error: err.stack });
            }
            """
        )

        validator = ErrorLeakValidator()
        result = validator.validate(test_file)

        assert result.has_findings is True
        assert any("stack" in f.title.lower() for f in result.findings)

    def test_detects_sql_error(self, tmp_path: Path) -> None:
        """Test detection of SQL error exposure."""
        test_file = tmp_path / "db.ts"
        test_file.write_text(
            """
            catch (err) {
                res.json({ error: err.sqlMessage });
            }
            """
        )

        validator = ErrorLeakValidator()
        result = validator.validate(test_file)

        assert result.has_findings is True
        assert any("sql" in f.title.lower() for f in result.findings)

    def test_logging_not_flagged(self, tmp_path: Path) -> None:
        """Test that logging stack traces is not flagged."""
        test_file = tmp_path / "logging.ts"
        test_file.write_text(
            """
            catch (err) {
                console.error(err.stack);
                res.json({ error: 'Internal error' });
            }
            """
        )

        validator = ErrorLeakValidator()
        result = validator.validate(test_file)

        # Stack trace to console should be filtered (false positive)
        # Only verbose error to response should be potentially flagged
        stack_findings = [
            f for f in result.findings if "stack" in f.title.lower()
        ]
        assert len(stack_findings) == 0


class TestRateLimitValidator:
    """Tests for RateLimitValidator."""

    def test_validator_properties(self) -> None:
        """Test validator has correct properties."""
        validator = RateLimitValidator()
        assert validator.id == "sec-rate-limit-tester"
        assert validator.name == "Rate Limiting Tester"
        assert validator.category == FindingCategory.ACCESS_CONTROL

    def test_detects_auth_endpoint(self, tmp_path: Path) -> None:
        """Test detection of auth endpoints."""
        test_file = tmp_path / "routes.ts"
        test_file.write_text(
            """
            router.post('/login', async (req, res) => {
                // handle login
            });
            """
        )

        validator = RateLimitValidator()
        result = validator.validate(test_file)

        assert result.has_findings is True
        assert any("auth" in f.title.lower() for f in result.findings)

    def test_detects_password_reset(self, tmp_path: Path) -> None:
        """Test detection of password reset endpoints."""
        test_file = tmp_path / "routes.ts"
        test_file.write_text(
            """
            router.post('/forgot-password', async (req, res) => {
                // send reset email
            });
            """
        )

        validator = RateLimitValidator()
        result = validator.validate(test_file)

        assert result.has_findings is True
        assert any("password" in f.title.lower() for f in result.findings)

    def test_rate_limited_not_flagged(self, tmp_path: Path) -> None:
        """Test that rate-limited endpoints are not flagged."""
        test_file = tmp_path / "routes.ts"
        test_file.write_text(
            """
            router.post('/login', rateLimit({ max: 5 }), async (req, res) => {
                // handle login
            });
            """
        )

        validator = RateLimitValidator()
        result = validator.validate(test_file)

        # Should be filtered due to rateLimit in context
        auth_findings = [
            f for f in result.findings if "auth" in f.title.lower()
        ]
        assert len(auth_findings) == 0


class TestValidatorRegistration:
    """Tests for validator registration."""

    def test_register_all_regex_validators(self) -> None:
        """Test registering all validators at once."""
        registry = ValidatorRegistry()

        # Import and use the function
        from aios.security.validators.regex import (
            CORSValidator,
            ErrorLeakValidator,
            HeadersValidator,
            RateLimitValidator,
        )

        registry.register(CORSValidator())
        registry.register(HeadersValidator())
        registry.register(ErrorLeakValidator())
        registry.register(RateLimitValidator())

        assert registry.count == 4
        assert registry.has("sec-cors-csrf-checker")
        assert registry.has("sec-header-inspector")
        assert registry.has("sec-error-leak-detector")
        assert registry.has("sec-rate-limit-tester")

    def test_register_all_convenience_function(self) -> None:
        """Test the convenience registration function."""
        from aios.security.validators.registry import validator_registry

        # Clear first to ensure clean state
        validator_registry.clear()

        register_all_regex_validators()

        assert validator_registry.count == 4
        assert validator_registry.has("sec-cors-csrf-checker")
        assert validator_registry.has("sec-header-inspector")
        assert validator_registry.has("sec-error-leak-detector")
        assert validator_registry.has("sec-rate-limit-tester")

        # Cleanup
        validator_registry.clear()


class TestIntegration:
    """Integration tests for regex validators."""

    def test_scan_directory(self, tmp_path: Path) -> None:
        """Test scanning a directory with multiple files."""
        # Create a mini project structure
        src = tmp_path / "src"
        src.mkdir()

        # File with CORS issue
        (src / "cors.ts").write_text(
            """
            res.setHeader('Access-Control-Allow-Origin', '*');
            """
        )

        # File with header issue
        (src / "cookie.ts").write_text(
            """
            res.cookie('session', token, { httpOnly: false });
            """
        )

        # File with error leak
        (src / "error.ts").write_text(
            """
            res.json({ error: err.stack });
            """
        )

        # Run all validators
        validators = [
            CORSValidator(),
            HeadersValidator(),
            ErrorLeakValidator(),
            RateLimitValidator(),
        ]

        total_findings = 0
        for validator in validators:
            result = validator.validate(src)
            total_findings += len(result.findings)

        # Should find at least 3 issues (one per file)
        assert total_findings >= 3

    def test_no_findings_in_clean_code(self, tmp_path: Path) -> None:
        """Test that clean code has minimal findings."""
        clean_file = tmp_path / "clean.ts"
        clean_file.write_text(
            """
            // Secure configuration
            const config = {
                cors: {
                    origin: 'https://example.com',
                    credentials: true
                },
                cookie: {
                    httpOnly: true,
                    secure: true,
                    sameSite: 'strict'
                }
            };

            // Proper error handling
            try {
                await doSomething();
            } catch (err) {
                console.error('Error occurred:', err);
                res.status(500).json({ error: 'Internal server error' });
            }
            """
        )

        validators = [
            CORSValidator(),
            HeadersValidator(),
            ErrorLeakValidator(),
        ]

        for validator in validators:
            result = validator.validate(clean_file)
            # Clean code should have minimal or no HIGH/CRITICAL findings
            high_critical = [
                f
                for f in result.findings
                if f.severity in (Severity.CRITICAL, Severity.HIGH)
            ]
            assert len(high_critical) == 0, f"{validator.name} found: {high_critical}"
