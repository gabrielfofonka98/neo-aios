# Output Paths — Where Each Agent Writes

All workspace folders are pre-created by neo-init. Agents MUST use these paths.
NEVER create new top-level folders. NEVER mkdir — folders already exist.

## Documentation (docs/)

| Path | Who Writes | Content |
|------|-----------|---------|
| `docs/architecture/` | Architect (Aria) | ADRs, system design, tech decisions |
| `docs/product/` | PM (Morgan) | PRDs, epics, stories |
| `docs/api/` | Doc (Sage) | API docs, endpoint reference |
| `docs/database/` | Data Engineer (Dara) | Schema docs, ERDs, data dictionary |
| `docs/design/` | UX (Pixel) | Wireframes, user flows, design specs |
| `docs/runbooks/` | SRE (Ops) | SLOs, incident runbooks, postmortems |
| `docs/sessions/` | Handoff skill | Session handoffs (YYYY-MM/ subdirs) |

## Reports (reports/)

| Path | Who Writes | Content |
|------|-----------|---------|
| `reports/security/` | QA Security (Quinn) | Security audit reports |
| `reports/code-quality/` | QA Code (Codex) | Code review, lint reports |
| `reports/testing/` | QA Functional (Tess) | Test plans, regression, bug reports |
| `reports/analytics/` | Analyst | Data analysis, dashboards, A/B tests |

## Database (database/)

| Path | Who Writes | Content |
|------|-----------|---------|
| `database/migrations/` | Data Engineer (Dara) | SQL migrations |
| `database/seeds/` | Data Engineer (Dara) | Seed data |

## Configuration (config/)

| Path | Who Writes | Content |
|------|-----------|---------|
| `config/neo-aios.yaml` | neo-init (auto) | Main system config |
| `config/credentials.yaml` | Any agent (auto-save) | Structured credentials (gitignored) |

## CI/CD (.github/)

| Path | Who Writes | Content |
|------|-----------|---------|
| `.github/workflows/` | DevOps (Gage) | CI/CD workflows (generated on demand) |

## Rules

1. **Dev (Dex)** writes application code in the USER's project structure (src/, app/, pages/, etc.) — not in any neo-aios folder
2. **DevOps (Gage)** generates `.github/workflows/` on demand from templates in `.aios-core/`
3. **Handoff** always creates in `docs/sessions/YYYY-MM/` with date prefix
4. **Reports** use date prefix: `YYYY-MM-DD-{name}.md`
5. **Migrations** use sequential prefix: `001-{name}.sql`, `002-{name}.sql`
