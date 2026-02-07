# Data Engineer — Extended Knowledge Base

Loaded on demand via `*kb` command. Not part of activation context.

---

## Full Command Reference

### Core
| Command | Description |
|---------|-------------|
| `*help` | Show all commands |
| `*guide` | Comprehensive usage guide |
| `*yolo` | Toggle confirmation skipping |
| `*exit` | Exit data-engineer mode |
| `*doc-out` | Output complete document |
| `*execute-checklist {name}` | Run DBA checklist |

### Architecture & Design
| Command | Description |
|---------|-------------|
| `*create-schema` | Design database schema |
| `*create-rls-policies` | Design RLS policies |
| `*create-migration-plan` | Create migration strategy |
| `*design-indexes` | Design indexing strategy |
| `*model-domain` | Domain modeling session |

### Operations & DBA
| Command | Description |
|---------|-------------|
| `*env-check` | Validate DB environment variables |
| `*bootstrap` | Scaffold database project structure |
| `*apply-migration {path}` | Run migration with safety snapshot |
| `*dry-run {path}` | Test migration without committing |
| `*seed {path}` | Apply seed data (idempotent) |
| `*snapshot {label}` | Create schema snapshot |
| `*rollback {snapshot}` | Restore snapshot or run rollback |
| `*smoke-test {version}` | Comprehensive database tests |

### Security & Performance
| Command | Description |
|---------|-------------|
| `*security-audit {scope}` | Database audit (rls, schema, full) |
| `*analyze-performance {type}` | Query analysis (query, hotpaths, interactive) |
| `*policy-apply {table} {mode}` | Install RLS (KISS or granular) |
| `*test-as-user {user_id}` | Emulate user for RLS testing |
| `*verify-order {path}` | Lint DDL ordering |

### Data Operations
| Command | Description |
|---------|-------------|
| `*load-csv {table} {file}` | Safe CSV loader (staging then merge) |
| `*run-sql {file_or_inline}` | Execute raw SQL with transaction |

### Setup & Documentation
| Command | Description |
|---------|-------------|
| `*setup-database [type]` | Interactive setup (supabase, postgresql, mongodb, mysql, sqlite) |
| `*research {topic}` | Deep research prompt for DB topics |

---

## Dependencies

### Tasks
- create-doc.md, db-domain-modeling.md, setup-database.md
- db-env-check.md, db-bootstrap.md, db-apply-migration.md
- db-dry-run.md, db-seed.md, db-snapshot.md, db-rollback.md, db-smoke-test.md
- security-audit.md, analyze-performance.md, db-policy-apply.md
- test-as-user.md, db-verify-order.md, db-load-csv.md, db-run-sql.md
- execute-checklist.md, create-deep-research-prompt.md

### Templates
- schema-design-tmpl.yaml, rls-policies-tmpl.yaml, migration-plan-tmpl.yaml
- index-strategy-tmpl.yaml, tmpl-migration-script.sql, tmpl-rollback-script.sql
- tmpl-smoke-test.sql, tmpl-rls-kiss-policy.sql, tmpl-rls-granular-policies.sql
- tmpl-staging-copy-merge.sql, tmpl-seed-data.sql, tmpl-comment-on-examples.sql

### Checklists
- dba-predeploy-checklist.md, dba-rollback-checklist.md, database-design-checklist.md

### Data
- database-best-practices.md, supabase-patterns.md, postgres-tuning-guide.md
- rls-security-patterns.md, migration-safety-guide.md

---

## CodeRabbit Integration

Focus: SQL quality, schema design, query performance, RLS security, migration safety.

### When to Use
- Before applying migrations (review DDL changes)
- After creating RLS policies (check policy logic)
- When adding database access code (review query patterns)
- During schema refactoring (validate changes)

### Severity Handling
| Severity | Action | Examples |
|----------|--------|---------|
| CRITICAL | Block migration | SQL injection, RLS bypass, data exposure, DROP without safeguards |
| HIGH | Fix before migration | N+1 queries, missing indexes, missing NOT NULL |
| MEDIUM | Document as tech debt | Denormalization without justification, inconsistent naming |
| LOW | Note for future | SQL style, readability |

### Execution
- Run: `coderabbit --prompt-only -t uncommitted` on migration files
- Timeout: 15 minutes (900000ms)
- CRITICAL issues MUST be fixed before migration
- HIGH issues require rollback script

---

## Security Notes

- Never echo full secrets — redact passwords/tokens automatically
- Prefer Pooler connection (project-ref.supabase.co:6543) with sslmode=require
- When no Auth layer present, warn that auth.uid() returns NULL
- RLS must be validated with positive/negative test cases
- Service role key bypasses RLS — use with extreme caution

---

## Agent Collaboration

**Collaborates with:** @architect (system requirements), @dev (migrations/schema handoff)
**Delegation from @architect:** Database schema, query optimization, RLS policies
**When to use others:** System architecture -> @architect | App code -> @dev | Frontend -> @dev

---

## Usage Guide

### Typical Workflow
1. Design: `*create-schema` or `*model-domain`
2. Bootstrap: `*bootstrap` to scaffold structure
3. Migrate: `*apply-migration {path}` with snapshot
4. Secure: `*security-audit` and `*policy-apply`
5. Optimize: `*analyze-performance` for queries
6. Test: `*smoke-test` before deployment

### Common Pitfalls
- Applying migrations without dry-run
- Skipping RLS policy coverage
- Not creating rollback scripts
- Forgetting to snapshot before migrations
- Over-normalizing or under-normalizing schema
