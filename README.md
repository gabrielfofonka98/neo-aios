# NEO-AIOS

```
     _   _ ______ ____            ___  _____ ____   _____
    | \ | |  ____/ __ \          / _ \|_   _/ __ \ / ____|
    |  \| | |__ | |  | |  ___   / /_\ \ | || |  | | (___
    | . ` |  __|| |  | | |___| |  _  | | || |  | |\___ \
    | |\  | |___| |__| |       | | | |_| || |__| |____) |
    |_| \_|______\____/        |_| |_|_____\____/|_____/

    Agent Intelligence Operating System
    Big Tech Hierarchy Edition
```

**Transform Claude Code into a managed multi-agent development environment with Big Tech organizational structure.**

![Python 3.12+](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)
![License MIT](https://img.shields.io/badge/License-MIT-blue)
![Tests 757+](https://img.shields.io/badge/Tests-757+-success)

---

## Table of Contents

- [What is NEO-AIOS?](#what-is-neo-aios)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Agent Catalog](#agent-catalog)
- [Security Validators](#security-validators)
- [Hook System](#hook-system)
- [CLI Reference](#cli-reference)
- [Project Structure](#project-structure)
- [Development](#development)

---

## What is NEO-AIOS?

NEO-AIOS is a Python framework that transforms Claude Code from a single-agent assistant into a fully orchestrated multi-agent operating system, organized like a Big Tech company (Google, Meta, Amazon).

### Key Features

- **36 Agents** organized in 5-tier hierarchy (C-Level → VP → Director → Manager → IC)
- **18 Security Sub-Agents** for comprehensive security auditing
- **Scope Enforcement** at runtime (blocks, not suggestions)
- **18 AST-based Validators** (zero false positives)
- **Auto-Fix Engine** with bounded reflexion (max 3 attempts)
- **3-Layer Quality Gates** (pre-commit, PR, human review)
- **Session Persistence** that survives Claude Code auto-compact
- **Hook System** for automatic agent restoration and scope enforcement

### Core Principles

```
1. DETERMINISTIC    → AST-based, not vibes-based
2. ENFORCED         → Scope violations are blocked, not suggested
3. PERSISTENT       → Session state survives context resets
4. HIERARCHICAL     → Big Tech structure applied to agents
5. BOUNDED          → Reflexion loops with limits (max 3)
```

---

## Installation

### Prerequisites

- Python >= 3.12
- [uv](https://docs.astral.sh/uv/) package manager
- Claude Code CLI

### Step 1: Clone Repository

```bash
git clone https://github.com/gabrielfofonka98/neo-aios.git
cd neo-aios
```

### Step 2: Install Dependencies

```bash
# Install with dev dependencies
uv sync --extra dev
```

### Step 3: Verify Installation

```bash
# Run all checks
uv run ruff check src/ tests/
uv run mypy --strict src/
uv run pytest

# Should show: 757+ tests passing
```

### Step 4: Configure Claude Code

The hooks are already configured in `.claude/settings.json` and will be loaded automatically by Claude Code.

---

## Quick Start

### Activate an Agent

In Claude Code, use slash commands:

```
/dev          # Activate Dex (Developer)
/devops       # Activate Gage (DevOps) - ONLY one who can git push
/architect    # Activate Aria (Architect)
/qa           # Activate Quinn (Security QA)
```

### Agent Commands

Once an agent is active:

```
*help         # Show agent commands
*status       # Show current status
*exit         # Exit agent mode
*task {name}  # Execute specific task
```

### Example Workflow

```
User: /dev
Dex: Developer agent activated. What would you like to build?

User: Create a user authentication module
Dex: [implements the module]

User: /devops
Gage: DevOps agent ready. Let's ship it!

User: *push
Gage: [runs quality gates, pushes to remote]
```

---

## Agent Catalog

### Hierarchy Overview

```
┌─────────────────────────────────────────────────────────────┐
│ C-LEVEL (1)                                                 │
│   CTO (Fofonka) - Strategy, vision, NEVER codes             │
├─────────────────────────────────────────────────────────────┤
│ VP LEVEL (5)                                                │
│   Aria (Engineering), Morgan (Product), Pixel (Design)      │
│   Oracle (Data), Ops (Operations)                           │
├─────────────────────────────────────────────────────────────┤
│ IC LEVEL - CORE (10)                                        │
│   Dex (Dev), Gage (DevOps), Dara (Data), Quinn (QA)        │
│   Codex (Code QA), Sage (Docs), Rune (Specs), Ralph (Auto)  │
│   Orion (Master), Tess (Test), Professor (Learning)         │
├─────────────────────────────────────────────────────────────┤
│ IC LEVEL - SECURITY (18)                                    │
│   Specialized security sub-agents (see below)               │
└─────────────────────────────────────────────────────────────┘
```

### Core Agents

| ID | Name | Title | Scope |
|----|------|-------|-------|
| `aria` | Aria | VP Engineering / System Architect | Architecture decisions, technical direction |
| `morgan` | Morgan | VP Product / Product Manager | Product strategy, PRDs, roadmaps |
| `pixel` | Pixel | VP Design / UX Lead | Design direction, UI/UX decisions |
| `oracle` | Oracle | VP Data / Data Strategist | Data strategy, analytics |
| `ops` | Ops | VP Operations | Operational excellence |
| `dex` | Dex | Full Stack Developer | Code implementation, debugging |
| `gage` | Gage | DevOps Engineer | **ONLY agent that can git push** |
| `dara` | Dara | Data Engineer | Database, SQL, migrations |
| `quinn` | Quinn | Security QA Leader | Security auditing, orchestrates 18 sub-agents |
| `codex` | Codex | Code Quality QA | Code review, quality gates |
| `sage` | Sage | Technical Writer | Documentation, guides |
| `rune` | Rune | Spec Architect | Ultra-detailed specs for Ralph |
| `ralph` | Ralph | Autonomous Agent | Self-driving development |
| `orion` | Orion | Master Orchestrator | Multi-agent coordination |
| `tess` | Tess | Test Engineer | Test strategy, coverage |
| `professor` | Professor | Learning Agent | Explanations, tutorials |

### Security Sub-Agents (18)

Quinn (Security QA Leader) orchestrates these specialized security validators:

| ID | Focus Area | Detects |
|----|------------|---------|
| `sec-xss-hunter` | XSS | Unsafe innerHTML, href injection |
| `sec-injection-detector` | SQL/ORM Injection | Raw queries, operator injection |
| `sec-secret-scanner` | Secrets | Hardcoded keys, env misuse |
| `sec-jwt-auditor` | JWT | Decode without verify, algorithm none |
| `sec-cors-csrf-checker` | CORS/CSRF | Origin reflection, SameSite issues |
| `sec-rls-guardian` | Supabase RLS | Missing policies, service_role exposure |
| `sec-api-access-tester` | API Security | BOLA, BFLA, missing auth |
| `sec-header-inspector` | Security Headers | CSP, HSTS, X-Frame-Options |
| `sec-rate-limit-tester` | Rate Limiting | Missing limits on auth endpoints |
| `sec-redirect-checker` | Open Redirects | Unvalidated redirects |
| `sec-upload-validator` | File Upload | Missing magic bytes, unsafe paths |
| `sec-validation-enforcer` | Input Validation | Missing Zod, any type abuse |
| `sec-error-leak-detector` | Error Leaks | Verbose errors, stack traces |
| `sec-client-exposure-scanner` | Client-Side | localStorage tokens, source maps |
| `sec-framework-scanner` | Framework CVEs | Vulnerable versions |
| `sec-supply-chain-monitor` | npm Security | Unpinned deps, audit failures |
| `sec-deploy-auditor` | Deployment | Vercel security, env vars |
| `sec-ai-code-reviewer` | AI Code | Vibecoding patterns, AI vulnerabilities |

### Scope Enforcement

| Agent | Can Do | Cannot Do |
|-------|--------|-----------|
| CTO | Strategy, approve VPs | Code, design, deploy |
| VP | Area decisions | Code, implementation |
| Dex (Dev) | Write code, tests | **Git push** |
| Gage (DevOps) | Git push, deploy | **ONLY one who can push** |
| Dara (Data) | Database, SQL | Application code |
| Quinn (QA) | Security audit | Write fixes |

---

## Security Validators

NEO-AIOS includes 18 AST-based security validators with zero false positives.

### AST Validators (TypeScript/JavaScript)

- **XSS Hunter**: Unsafe HTML rendering, href injection, SVG injection
- **Injection Detector**: Prisma raw queries, SQL template strings
- **Secret Scanner**: AWS keys, Stripe keys, JWT tokens, env exposure
- **JWT Auditor**: Decode without verify, algorithm confusion

### Regex Validators

- **CORS/CSRF Checker**: Wildcard origins, missing CSRF tokens
- **Header Inspector**: Missing CSP, HSTS, X-Frame-Options
- **Rate Limit Tester**: Auth endpoints without rate limiting
- **Error Leak Detector**: Stack traces in responses

### Running Security Audit

```bash
# Full audit
uv run python -m aios.cli security audit ./src

# Quick scan
uv run python -m aios.cli security audit --quick ./src
```

---

## Hook System

NEO-AIOS uses Claude Code hooks for automatic agent management:

### Available Hooks

| Hook | Event | Function |
|------|-------|----------|
| `restore-agent-state.sh` | SessionStart (compact) | Restores active agent after context compaction |
| `pre-prompt-context.sh` | UserPromptSubmit | Injects minimal context before each prompt |
| `post-response-update.sh` | Stop | Auto-updates lastActivity timestamp |
| `scope-enforcer.sh` | PreToolUse (Bash) | **Blocks scope violations** |
| `agent-delegation-tracker.sh` | SubagentStart | Logs delegation chains |

### Scope Enforcement Example

When a non-DevOps agent tries to `git push`:

```
🚫 SCOPE VIOLATION: git push

Only @devops (Gage) can push to remote repositories.
Current agent: @dev

To push changes, activate DevOps:
  /devops
  *push
```

---

## CLI Reference

```bash
aios
├── agent
│   ├── activate <agent-id>    # Activate agent
│   ├── deactivate             # Deactivate current
│   ├── list                   # List all agents
│   └── status                 # Current status
│
├── security
│   ├── audit <path>           # Full security audit
│   └── findings <severity>    # Show findings
│
├── quality
│   ├── check                  # Run all quality gates
│   └── gate --layer <1|2|3>   # Run specific gate
│
├── fix
│   ├── auto <finding-id>      # Auto-fix finding
│   └── all                    # Auto-fix all fixable
│
├── session
│   ├── status                 # Session info
│   └── handoff                # Generate handoff doc
│
└── healthcheck
    ├── run                    # All health checks
    └── heal                   # Attempt self-healing
```

---

## Project Structure

```
neo-aios/
├── src/aios/                 # Python source
│   ├── agents/               # Agent registry, models
│   ├── scope/                # Scope enforcement
│   ├── security/             # Security validators
│   ├── autofix/              # Auto-fix engine
│   ├── quality/              # Quality gates
│   ├── healthcheck/          # Health monitoring
│   ├── context/              # Session persistence
│   └── cli/                  # Click CLI
│
├── agents/                   # Agent SKILL.md definitions (36)
│   ├── aria/, dex/, gage/    # Core agents
│   └── sec-*/                # Security sub-agents (18)
│
├── .claude/                  # Claude Code integration
│   ├── hooks/                # Hook scripts (5)
│   ├── settings.json         # Hook configuration
│   └── CLAUDE.md             # Agent instructions
│
├── tests/                    # Test suite (757+ tests)
└── docs/                     # Documentation
```

---

## Development

### Setup

```bash
git clone https://github.com/gabrielfofonka98/neo-aios.git
cd neo-aios
uv sync --extra dev
```

### Running Checks

```bash
# Lint
uv run ruff check src/ tests/

# Type check
uv run mypy --strict src/

# Test
uv run pytest

# All at once
uv run ruff check && uv run mypy --strict src/ && uv run pytest
```

### Quality Gates

| Gate | Tools | Blocks |
|------|-------|--------|
| Layer 1 (pre-commit) | ruff, mypy, pytest | Commit if CRITICAL |
| Layer 2 (PR) | CodeRabbit, QA agent | Merge if CRITICAL/HIGH |
| Layer 3 (human) | Tech Lead review | Production deploy |

---

## License

MIT License - see [LICENSE](LICENSE)

---

## Credits

- **Author:** Gabriel Fofonka
- **AI Partner:** Claude Opus 4.5
- **Inspiration:** Big Tech organizational structures

---

*NEO-AIOS: Agent Intelligence Operating System*
*"Never take the lazy path. Do the hard work now."*
