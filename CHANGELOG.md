# Changelog

All notable changes to NEO-AIOS will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- Nothing yet

### Changed
- Nothing yet

### Fixed
- Nothing yet

---

## [0.1.0] - 2026-02-05

Initial release of NEO-AIOS - Agent Intelligence Operating System.

### Added

#### Core Architecture
- **5-tier agent hierarchy** inspired by Big Tech organizations:
  - C-Level: CTO (Fofonka) - Strategic direction
  - VP Level: Engineering (Aria), Product (Morgan), Design (Pixel), Data (Oracle), Platform (Atlas)
  - Director Level: Cross-team coordination
  - Manager/Lead Level: Squad management
  - IC Level: Dex, Gage, Dara, Quinn, Codex, Sage, Rune, Ralph + 18 security agents

#### Security Validators
- **18 specialized security sub-agents** under Quinn (QA Lead):
  - `sec-ai-code-reviewer`: AI-generated code vulnerability detection
  - `sec-api-access-tester`: BOLA, BFLA, auth testing
  - `sec-client-exposure-scanner`: localStorage, source maps, client-side secrets
  - `sec-cors-csrf-checker`: CORS misconfig, CSRF detection
  - `sec-deploy-auditor`: Vercel deployment security
  - `sec-error-leak-detector`: Verbose error detection
  - `sec-framework-scanner`: CVE detection for Next.js/React
  - `sec-header-inspector`: CSP and security headers validation
  - `sec-injection-detector`: SQL/ORM injection patterns
  - `sec-jwt-auditor`: JWT misuse detection
  - `sec-rate-limit-tester`: Rate limiting verification
  - `sec-redirect-checker`: Open redirect detection
  - `sec-rls-guardian`: Supabase RLS validation
  - `sec-secret-scanner`: Hardcoded secrets detection
  - `sec-supply-chain-monitor`: npm supply chain security
  - `sec-upload-validator`: File upload security
  - `sec-validation-enforcer`: Zod validation enforcement
  - `sec-xss-hunter`: Cross-site scripting detection

#### Scope Enforcement
- **Runtime scope validation** for all agents:
  - C-Level/VP/Director cannot write code
  - Only Gage (DevOps) can execute `git push`
  - Database DDL requires explicit approval
  - Violations are blocked, not warned

#### Agent Identity System
- **Strict identity isolation**: Each agent is a unique, isolated entity
- **Session persistence** via `.aios/session-state.json`
- **Survives context compaction**: State restored from file on each turn
- **Clear delegation rules**: Down only, never up or sideways

#### CLI Interface
- `neo-aios` / `aios` command-line interface
- Agent activation commands: `/dev`, `/architect`, `/devops`, etc.
- Agent control: `*help`, `*status`, `*exit`, `*task`
- Quality gate commands

#### Quality Gates (3-Layer)
- **Layer 1 (Pre-Commit)**: ruff, mypy, pytest, quick security scan
- **Layer 2 (PR Automation)**: CodeRabbit, QA agent review, full security audit
- **Layer 3 (Human Review)**: Tech Lead sign-off, manager approval

#### Development Tools
- **Python 3.12+** with full type hints
- **uv** for fast package management
- **ruff** for linting and formatting
- **mypy --strict** for type checking
- **pytest** with coverage enforcement (>80%)

#### Claude Code Integration
- Custom skills for each agent role
- Pre-commit hooks for enforcement
- Session state management
- Agent activation via slash commands

### Technical Details

- **Package structure**: `src/aios/` with proper Python packaging
- **Build system**: hatchling
- **Dependencies**: click, pydantic v2, pyyaml, rich, tree-sitter, sqlglot
- **Test framework**: pytest with pytest-cov, pytest-asyncio

### Documentation

- Comprehensive README with quick start guide
- Agent catalog with roles and responsibilities
- Architecture documentation
- Release checklist and procedures

---

## Version History

| Version | Date | Highlights |
|---------|------|------------|
| 0.1.0 | 2026-02-05 | Initial release with full agent hierarchy |

---

## Upgrade Notes

### From Pre-Release to 0.1.0

If you were using development versions:

1. Remove any `.aios/` session state files
2. Update your `.claude/CLAUDE.md` to match new format
3. Reinstall: `pip install neo-aios==0.1.0`

---

## Links

- [Repository](https://github.com/gabrielfofonka98/neo-aios)
- [Documentation](https://github.com/gabrielfofonka98/neo-aios#readme)
- [Issues](https://github.com/gabrielfofonka98/neo-aios/issues)

[Unreleased]: https://github.com/gabrielfofonka98/neo-aios/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/gabrielfofonka98/neo-aios/releases/tag/v0.1.0
