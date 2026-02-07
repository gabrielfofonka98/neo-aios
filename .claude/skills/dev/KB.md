# Developer — Extended Knowledge Base

Loaded on demand via `*kb` command. Not part of activation context.

---

## Full Command Reference

### Story Development
| Command | Description |
|---------|-------------|
| `*help` | Show all commands |
| `*develop` | Implement story tasks (modes: yolo, interactive, preflight) |
| `*develop-yolo` | Autonomous development mode |
| `*develop-interactive` | Interactive development mode (default) |
| `*develop-preflight` | Planning mode before implementation |
| `*create-service` | Create service from Handlebars template |

### Workflow Intelligence
| Command | Description |
|---------|-------------|
| `*waves` | Analyze workflow for parallel execution (--visual for ASCII art) |

### Quality & Debt
| Command | Description |
|---------|-------------|
| `*apply-qa-fixes` | Apply QA feedback and fixes |
| `*run-tests` | Execute linting and all tests |
| `*backlog-debt` | Register technical debt item |

### Context & Performance
| Command | Description |
|---------|-------------|
| `*load-full` | Load complete file from devLoadAlwaysFiles |
| `*clear-cache` | Clear dev context cache |
| `*session-info` | Current session details |

### Learning & Utilities
| Command | Description |
|---------|-------------|
| `*explain` | Explain what I just did in teaching detail |
| `*guide` | Comprehensive usage guide |
| `*exit` | Exit developer mode |

---

## Dependencies

### Checklists
- story-dod-checklist.md

### Tasks
- apply-qa-fixes.md, create-service.md, dev-develop-story.md
- execute-checklist.md, dev-improve-code-quality.md
- po-manage-story-backlog.md, dev-optimize-performance.md
- dev-suggest-refactoring.md, sync-documentation.md
- validate-next-story.md, waves.md

### Tools
- coderabbit, git (local only), context7, supabase, n8n, browser, ffmpeg

---

## CodeRabbit Integration (Self-Healing)

Before marking story "Ready for Review":

```
iteration = 0, max = 2

WHILE iteration < max:
  1. Run: coderabbit --prompt-only -t uncommitted
  2. Parse for CRITICAL issues

  IF no CRITICAL: document HIGH in Dev Notes, BREAK
  IF CRITICAL: auto-fix, iteration++

IF max reached AND CRITICAL remain:
  HALT and report to user
  DO NOT mark story complete
```

### Severity Handling
| Severity | Action |
|----------|--------|
| CRITICAL | Auto-fix immediately (max 2 iterations) |
| HIGH | Document in story Dev Notes |
| MEDIUM | Ignore |
| LOW | Ignore |

Timeout: 15 minutes (900000ms)

---

## Decision Logging (Yolo Mode)

When executing in autonomous (yolo) mode:
1. Initialize tracking context at start
2. Record all autonomous decisions with rationale
3. Track files modified, tests run, performance metrics
4. Generate decision log at `.ai/decision-log-{story-id}.md`
5. Include rollback info (commit hash before execution)

---

## Git Restrictions

### Allowed
- git add, commit, status, diff, log, branch, checkout, merge

### Blocked
- git push, git push --force, gh pr create, gh pr merge
- Redirect: "For git push, activate @devops"

---

## Story Development Workflow

### Order of Execution
1. Read (first or next) task
2. Implement task and subtasks
3. Write tests
4. Execute validations
5. If ALL pass, mark task [x]
6. Update File List with new/modified/deleted files
7. Repeat until all tasks complete

### Story File Updates (ONLY authorized sections)
- Tasks/Subtasks checkboxes
- Dev Agent Record and all subsections
- Agent Model Used
- Debug Log References
- Completion Notes List
- File List
- Change Log
- Status

### Blocking Conditions
- Unapproved deps needed (confirm with user)
- Ambiguous after story check
- 3 failures attempting same fix
- Missing config
- Failing regression

---

## Agent Collaboration

**Collaborates with:** @qa (code review), @sm (stories)
**Delegates to:** @devops (push/PR)
**When to use others:** Stories -> @sm | Code review -> @qa | Push -> @devops

---

## Usage Guide

### Typical Workflow
1. Story assigned by @sm -> `*develop story-X.Y.Z`
2. Implementation -> Code + Tests (follow story tasks)
3. Validation -> `*run-tests` (must pass)
4. QA feedback -> `*apply-qa-fixes`
5. Mark complete -> Status "Ready for Review"
6. Handoff to @devops for push

### Common Pitfalls
- Starting before story is approved
- Skipping tests
- Not updating File List
- Pushing directly (use @devops)
- Modifying non-authorized story sections
- Forgetting CodeRabbit pre-commit review
