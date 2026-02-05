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

---

## What is NEO-AIOS?

NEO-AIOS is a Python framework that transforms Claude Code from a single-agent assistant into a fully orchestrated multi-agent operating system, organized like a Big Tech company (Google, Meta, Amazon).

### Key Features

- **50+ Agents** organized in 5-tier hierarchy (C-Level → VP → Director → Manager → IC)
- **Scope Enforcement** at runtime (not suggestions, actual blocks)
- **18 Security Validators** with AST-based detection (zero false positives)
- **Auto-Fix Engine** with bounded reflexion (max 3 attempts)
- **3-Layer Quality Gates** (pre-commit, PR, human review)
- **Session Persistence** that survives Claude Code auto-compact
- **Delegation Rules** enforced (only delegate down the hierarchy)

### Core Principles

```
1. DETERMINISTIC    → AST-based, not vibes-based
2. ENFORCED         → Scope violations are blocked, not suggested
3. PERSISTENT       → Session state survives context resets
4. HIERARCHICAL     → Big Tech structure applied to agents
5. BOUNDED          → Reflexion loops with limits (max 3)
```

---

## Agent Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│ C-LEVEL (1)                                                 │
│   CTO (Fofonka) - Strategy, vision, NEVER codes             │
├─────────────────────────────────────────────────────────────┤
│ VP LEVEL (5)                                                │
│   Aria (Engineering), Morgan (Product), Pixel (Design)      │
│   Oracle (Data), Atlas (Platform)                           │
├─────────────────────────────────────────────────────────────┤
│ DIRECTOR LEVEL (8)                                          │
│   Frontend, Backend, Mobile, Product, Design, Data, Infra   │
├─────────────────────────────────────────────────────────────┤
│ MANAGER/LEAD LEVEL (12)                                     │
│   Engineering Managers, Tech Leads, PM/Design/Data Leads    │
├─────────────────────────────────────────────────────────────┤
│ IC LEVEL (30+)                                              │
│   Core: Dex (Dev), Gage (DevOps), Dara (DB), Quinn (QA)     │
│   Security: 18 specialized validators                        │
│   Specialists: Frontend, Mobile, Performance, SRE, ML       │
└─────────────────────────────────────────────────────────────┘
```

### Scope Enforcement

| Agent | Can Do | Cannot Do |
|-------|--------|-----------|
| CTO | Strategy, approve VPs | Code, design, deploy |
| VP | Area decisions | Code, implementation |
| Director | Cross-team decisions | Direct coding |
| Manager/TL | Squad decisions, review | Production deploy |
| Dex (Dev) | Write code, tests | Git push |
| Gage (DevOps) | Git push, deploy | **ONLY one who can push** |
| Dara (Data) | Database, SQL | Application code |
| Quinn (QA) | Security audit | Write fixes |

---

## Quick Start

### Prerequisites

- Python >= 3.12
- [uv](https://docs.astral.sh/uv/) package manager

### Installation

```bash
cd neo-aios
uv sync --extra dev
```

### Verify Installation

```bash
# List all agents
aios agents list

# Run health checks
aios healthcheck run

# Run security scan
aios security audit ./src

# Check quality gates
aios quality check
```

---

## CLI Reference

```bash
aios
├── agent
│   ├── activate <agent-id>    # Activate agent
│   ├── deactivate             # Deactivate current
│   ├── list                   # List all agents
│   ├── status                 # Current status
│   └── hierarchy              # Show hierarchy tree
│
├── security
│   ├── audit                  # Full security audit
│   ├── audit --quick          # Quick scan
│   └── findings <severity>    # Show findings
│
├── quality
│   ├── check                  # Run all checks
│   └── gate --layer <1|2|3>   # Run specific gate
│
├── fix
│   ├── auto <finding-id>      # Auto-fix finding
│   └── all                    # Auto-fix all fixable
│
├── session
│   ├── status                 # Session info
│   └── handoff                # Generate handoff
│
└── healthcheck
    ├── run                    # All health checks
    └── heal                   # Attempt self-healing
```

---

## Project Structure

```
neo-aios/
├── src/aios/                 # Python source (24 modules)
│   ├── agents/               # Agent registry + scope
│   ├── hierarchy/            # Big Tech hierarchy
│   ├── governance/           # Approval chains
│   ├── validators/           # 18 security validators
│   ├── fixers/               # Auto-fix engine
│   ├── quality/              # 3-layer gates
│   ├── healthcheck/          # 5-domain monitoring
│   ├── context/              # Session persistence
│   └── cli/                  # Click CLI
│
├── agents/                   # Agent SKILL.md definitions
│   ├── c-level/              # CTO
│   ├── vp-level/             # VPs (5)
│   ├── directors/            # Directors (8)
│   ├── managers/             # Managers/Leads (12)
│   ├── core/                 # Core ICs (8)
│   ├── security/             # Security sub-agents (18)
│   └── specialists/          # Specialist ICs (10+)
│
├── .aios-core/               # Framework (read-only)
├── .aios-custom/             # Project overlay
├── .claude/                  # Claude Code integration
├── .aios/                    # Runtime state
├── config/                   # YAML configs
├── tests/                    # Test suite
└── docs/                     # Documentation
    └── PRD.md                # Product Requirements
```

---

## Documentation

- [PRD (Product Requirements)](docs/PRD.md) - Complete system specification
- [ANALYSIS](ANALYSIS.md) - Analysis of base systems
- [STANDARDS](.aios-custom/STANDARDS.md) - Technical standards

---

## Development

```bash
# Setup
uv sync --extra dev

# Lint
uv run ruff check src/ tests/

# Type check
uv run mypy --strict src/

# Test
uv run pytest

# All checks
uv run ruff check && uv run mypy --strict src/ && uv run pytest
```

---

## License

MIT

---

*NEO-AIOS: Agent Intelligence Operating System*
*"Never take the lazy path. Do the hard work now."*
