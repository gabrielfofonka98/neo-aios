# DevOps — Extended Knowledge Base

Loaded on demand via `*kb` command. Not part of activation context.

---

## Full Command Reference

### Core
| Command | Description |
|---------|-------------|
| `*help` | Show all commands |
| `*detect-repo` | Detect repository context (framework-dev vs project-dev) |
| `*session-info` | Current session details |
| `*guide` | Comprehensive usage guide |
| `*exit` | Exit DevOps mode |

### Quality & Push
| Command | Description |
|---------|-------------|
| `*version-check` | Analyze version and recommend next |
| `*pre-push` | Run all quality checks before push |
| `*push` | Push to any configured repo |
| `*repos` | List configured repositories with status |

### GitHub Operations
| Command | Description |
|---------|-------------|
| `*create-pr` | Create pull request |
| `*configure-ci` | Setup/update GitHub Actions |
| `*release` | Create versioned release with changelog |

### Repository Management
| Command | Description |
|---------|-------------|
| `*cleanup` | Remove stale branches/files |
| `*init-project-status` | Initialize dynamic project status tracking |

### Reporting & Diagnostics
| Command | Description |
|---------|-------------|
| `*report` | Git activity report (daily, period, custom range) |
| `*diagnose` | Analyze engineering practices |

### Environment Setup
| Command | Description |
|---------|-------------|
| `*environment-bootstrap` | Complete environment setup (CLIs, auth, Git/GitHub) |
| `*setup-github` | Configure DevOps infrastructure (workflows, CodeRabbit, branch protection) |

### MCP Management
| Command | Description |
|---------|-------------|
| `*search-mcp` | Search available MCPs |
| `*add-mcp` | Add MCP server |
| `*list-mcps` | List enabled MCPs |
| `*remove-mcp` | Remove MCP server |
| `*setup-mcp-docker` | Initial Docker MCP Toolkit config |

---

## Dependencies

### Config
- repos.yaml (multi-repo registry)

### Tasks
- environment-bootstrap.md, setup-github.md, devops-version-management.md
- devops-pre-push-quality-gate.md, devops-github-pr-automation.md
- devops-git-report.md, devops-git-diagnose.md, ci-cd-configuration.md
- devops-repository-cleanup.md, release-management.md
- push.md, repos.md, search-mcp.md, add-mcp.md, setup-mcp-docker.md

### Templates
- github-pr-template.md, github-actions-ci.yml, github-actions-cd.yml
- changelog-template.md, git-report-prompt-v3.md, git-diagnose-prompt-v1.md

### Checklists
- pre-push-checklist.md, release-checklist.md

### Utils
- branch-manager, git, gitignore-manager, version-tracker, git-wrapper

---

## CodeRabbit Integration

Usage: Pre-PR quality gate, pre-push validation, security scanning.

### Commands
- `coderabbit --prompt-only -t uncommitted` (pre-push)
- `coderabbit --prompt-only --base main` (pre-PR)
- `coderabbit --prompt-only -t committed` (pre-commit)

### Gate Rules
| Severity | Action |
|----------|--------|
| CRITICAL | Block PR creation |
| HIGH | Warn, recommend fix |
| MEDIUM | Document in PR, follow-up issue |
| LOW | Optional, note in comments |

Timeout: 15 minutes (900000ms)

---

## Git Authority

### Exclusive Operations (ONLY this agent)
- git push (all variants)
- gh pr create / merge
- gh release create

### Standard Operations
- git status, log, diff, tag, branch -a

### Enforcement
Git pre-push hook at .git/hooks/pre-push checks $AIOS_ACTIVE_AGENT, blocks if != "devops".

---

## Repository Detection

Gage never assumes a specific repository — detects dynamically:
1. `git remote -v` for URL
2. config/neo-aios.yaml for project config
3. package.json name field
4. Interactive prompt if ambiguous

Modes: framework-development (skills are source) vs project-development (neo-init installed)

---

## Version Management

| Type | When |
|------|------|
| MAJOR | Breaking changes, API redesign |
| MINOR | New features, backward compatible |
| PATCH | Bug fixes only |

Detection: Analyze git diff since last tag, check breaking change keywords.

---

## Workflow Examples

### Standard Push
1. Detect repository context
2. `*pre-push` (quality gates)
3. Present summary, user confirms
4. Execute git push
5. Create PR if on feature branch

### Release Creation
1. `*version-check` (analyze changes)
2. Confirm version bump
3. `*pre-push` (quality gates)
4. Generate changelog
5. Create git tag + push tag
6. Create GitHub release

---

## Reporting

### Report Formats
- `--format=executive` — High-level for management (default)
- `--format=detailed` — Full technical breakdown
- `--format=minimal` — Quick one-liner summary

### Diagnostics
Analyzes: commit message quality, code review patterns, test coverage trends, documentation practices.

---

## Agent Collaboration

**Receives from:** @dev (push requests), @sm (sprint workflow), @architect (repo operations)
**When to use others:** Code -> @dev | Stories -> @sm | Architecture -> @architect

---

## Usage Guide

### Typical Workflow
1. Quality gates: `*pre-push`
2. Version check: `*version-check`
3. Push: `*push` after gates pass
4. PR creation: `*create-pr`
5. Release: `*release` with changelog

### Common Pitfalls
- Pushing without pre-push quality gates
- Force pushing to main/master
- Not confirming version bump
- Creating PR before gates pass
- Skipping CodeRabbit CRITICAL issues
