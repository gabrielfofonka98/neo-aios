# Claude Code - File Writing Restrictions

Rules for where agents can and cannot write files.

---

## NEVER Write In

### `.claude/` (System config, read-only at runtime)
- Agent definitions, hooks, rules, setup
- Only modified by `neo update` or framework maintainer

### `.aios-core/` (Framework core, read-only)
- Tasks, workflows, templates, quality gates, checklists
- NEVER touched by any agent at runtime

### `.aios-custom/` (Customization overlay)
- Config, standards, workflows
- Only modified by framework maintainer

---

## Allowed Write Paths

### Documentation
| Path | Agent | Content |
|------|-------|---------|
| `docs/architecture/` | Architect (Aria) | ADRs, system design |
| `docs/product/` | PM (Morgan) | PRDs, epics, stories |
| `docs/api/` | Doc (Sage) | API documentation |
| `docs/database/` | Data Engineer (Dara) | Schema docs, ERDs |
| `docs/design/` | UX (Pixel) | Wireframes, user flows |
| `docs/runbooks/` | SRE (Ops) | SLOs, runbooks |
| `docs/sessions/` | Handoff skill | Session handoffs (YYYY-MM/) |

### Reports
| Path | Agent | Content |
|------|-------|---------|
| `reports/security/` | QA (Quinn) | Security audit reports |
| `reports/code-quality/` | QA Code (Codex) | Code review reports |
| `reports/testing/` | QA Functional (Tess) | Test plans, regression |
| `reports/analytics/` | Analyst (Oracle) | Data analysis, A/B tests |

### Database
| Path | Agent | Content |
|------|-------|---------|
| `database/migrations/` | Data Engineer (Dara) | SQL migrations |
| `database/seeds/` | Data Engineer (Dara) | Seed data |

### Configuration
| Path | Agent | Content |
|------|-------|---------|
| `config/` | Any (auto-save) | Project YAML configs |
| `.env` | Any (auto-save) | Credentials (gitignored) |

### CI/CD
| Path | Agent | Content |
|------|-------|---------|
| `.github/workflows/` | DevOps (Gage) | CI/CD workflows |

### Application Code
| Path | Agent | Content |
|------|-------|---------|
| User's project dirs | Dev (Dex) | Application code only |

---

## Pre-Write Checklist

```
Is the target in .claude/, .aios-core/, or .aios-custom/?
  YES -> STOP. NEVER write there.

Is it a report or analysis?
  YES -> reports/{security|code-quality|testing|analytics}/

Is it documentation?
  YES -> docs/{architecture|product|api|database|design|runbooks|sessions}/

Is it a migration or seed?
  YES -> database/{migrations|seeds}/

Is it application code?
  YES -> User's project structure (src/, app/, pages/, etc.)

Is it a credential?
  YES -> .env (auto-save, gitignored)
```

---

*Version: 2.0*
*Last Updated: 2026-02-06*
