# Changelog

All notable changes to NEO-AIOS will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added

#### Agent Intelligence System
- **Constitution** (`.claude/rules/constitution.md`) — 7 formal articles with 3 severity levels (NON-NEGOTIABLE, MUST, SHOULD) covering agent identity isolation, authority boundaries, hierarchy, quality gates, language, and behavior
- **Agent Memory System** — Persistent per-agent memory at `.claude/agent-memory/{id}/MEMORY.md` for all 52 agents, tracking key decisions, gotchas, and domain-specific patterns across sessions
- **GotchasMemory** (`src/aios/memory/gotchas.py`) — Tracks recurring issues with SHA-256 keying and auto-promotes to formal rules after configurable threshold (default: 3 occurrences)
- **FileEvolutionTracker** (`src/aios/memory/file_evolution.py`) — Detects multi-agent file conflicts with 4-level severity classification (critical/high/medium/low)
- **Hook Bridge** (`src/aios/memory/hook_bridge.py`) — Click CLI for bash-to-Python integration with 4 subcommands: `record-file-change`, `check-conflicts`, `record-gotcha`, `get-gotchas`
- **`memory_file` references** in 35/52 SKILL.md files (core + persona + security agents) with DOD memory update items
- **119 new tests** for memory system (51 memory + 32 hook bridge + 36 CLI)

#### CLI Memory Commands
- **`aios memory show <id>`** — Display an agent's persistent memory
- **`aios memory list-agents`** — List all agents with memory files and last-modified dates
- **`aios memory clear <id>`** — Reset agent memory to template (with confirmation)
- **`aios gotchas list`** — List recorded gotchas with optional `--agent` and `--min-count` filters
- **`aios gotchas stats`** — Show gotcha statistics (total issues, promoted count, top categories)
- **`aios gotchas reset`** — Clear all gotchas (with confirmation)
- **`aios conflicts check`** — Show active file conflicts with optional `--agent` filter
- **`aios conflicts history`** — File modification history with `--days` filter
- **`aios conflicts cleanup`** — Remove old entries with `--days` filter

#### Context Optimization (SynkraAI-inspired)
- **2-layer SKILL/KB split** — Light SKILL.md (~120-155 lines) for activation, heavy KB.md loaded on demand via `*kb` command
- **70% reduction** in total activation context (3,100 → 926 lines across 6 core agents + CLAUDE.md)
- **KB.md files** for master, qa, dev, devops, data-engineer, architect

#### Enhanced Hooks
- **Greeting level detection** — `pre-prompt-context.sh` now detects new vs existing sessions, injecting appropriate greeting level hint
- **Agent history tracking** — `post-response-update.sh` tracks `agentHistory` (last 5 agents) in session-state.json
- **Previous agent context injection** — When switching agents, hooks inject context about the previous agent
- **Memory reference on compact** — `restore-agent-state.sh` now includes agent memory path after context compaction
- **Agent activation detection** — `pre-prompt-context.sh` auto-detects `/agent` commands and `<command-message>` XML tags

#### Pipeline Module
- **Pipeline module** (`src/aios/pipeline/`) with dependency-aware story execution:
  - `PipelineManager` — State persistence, file-based locking, WaveAnalyzer integration
  - `StepExecutor` — Isolated step execution with checkpoint/recovery
  - `StepRegistry` — YAML-based step definitions per workflow (greenfield, bugfix, refactor)
  - `StoryCostReport` — Token cost tracking with mixed-model savings calculation
  - Model routing per step via `TaskRouter.classify_by_step()`
- **Session pipeline fields** — `currentStep`, `stepsCompleted`, `stepBudget`, `pipelineStoryId` (backward compatible)
- **105 new tests** for pipeline module (96% coverage)

### Changed
- **CLAUDE.md optimized** from 390 to ~145 lines (63% reduction), heavy content moved to `.claude/rules/`
- **6 core SKILL.md files** rewritten with 2-layer split (67-75% reduction each)
- **Agent count** expanded from 36 to 52 (additional persona, utility, and launcher agents)
- **Test count** grew from 757 to 1171+ tests
- **AI Partner** updated to Claude Opus 4.6

### Fixed
- **Hook XML tag detection** — `pre-prompt-context.sh` now correctly detects `<command-message>` tags for skill activation
- **Agent ID normalization** — Comprehensive audit normalized agent IDs, paths, and references across 113 files

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
| Unreleased | - | Agent intelligence, context optimization, pipeline, CLI expansion |
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
