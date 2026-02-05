# Push Task (Multi-Repo)

## Metadata
```yaml
task_id: push
title: Push to Repository
agent: devops
complexity: simple
elicit: true
config_file: .aios-core/development/config/repos.yaml
```

## Description

Push changes to any configured repository. Supports multiple repos via registry configuration.

**Usage:**
- `*push` - Interactive selection from available repos
- `*push <repo-name>` - Direct push to specific repo
- `*push lendaria` - Push to Vercel (alias: vercel, app)
- `*push mmos` - Push to main repo (alias: main)

## Execution Steps

### Step 1: Load Repository Registry

Read config from `.aios-core/development/config/repos.yaml`

### Step 2: Resolve Repository

**If repo name provided:**
1. Check if name exists in `repos` or `aliases`
2. If not found, show available repos and abort

**If no repo name (interactive):**
1. List all configured repos with status
2. Show numbered options
3. Wait for user selection

Display format:
```
Available Repositories:

1. mmos - Main development repository
   └─ origin → mmos.git

2. lendaria - Vercel deployment (nested repo)
   └─ origin → lendarIA.git [force-push]

3. outputs - Generated artifacts (courses, minds)
   └─ ⚠️ NOT INITIALIZED

Select repo (1-3) or name: _
```

### Step 3: Validate Repository

```bash
cd <repo.path> && git remote get-url <repo.remote>
```

**Checks:**
- Directory exists
- Is a git repository
- Remote is configured
- On correct branch

If `status: not_initialized`, offer to initialize:
> "Repository not initialized. Run `*repo-init <name>` to set up."

### Step 4: Check Working Tree

```bash
cd <repo.path> && git status --porcelain
```

If changes exist:
- Show count of modified/new files
- If `force_push: true`, inform and continue
- If `force_push: false`, ask to commit first or proceed

### Step 5: Execute Push

**If `force_push: true`:**
```bash
cd <repo.path> && git push <repo.remote> <repo.branch> --force
```

**If `force_push: false`:**
```bash
cd <repo.path> && git push <repo.remote> <repo.branch>
```

**If `pre_push_checks: true`:**
- Run quality gates before push (lint, test, typecheck, build)
- Abort if any check fails

### Step 6: Report Result

**Success:**
```
✅ Push Complete

  Repo: <repo-name>
  Path: <repo.path>
  Remote: <repo.remote> → <repo.url>
  Branch: <repo.branch>
  Commit: <short-hash> <message>
  Force: <yes/no>
```

**If lendaria/vercel:**
```
🚀 Vercel auto-deploy triggered
```

## Error Handling

| Error | Action |
|-------|--------|
| Repo not found | Show available repos |
| Not a git repo | Suggest `*repo-init` |
| Remote not configured | Show setup command |
| Push rejected | Show error, suggest force or pull |
| Pre-push checks failed | Show which check failed |

## Quick Reference

```
*push              # Interactive selection
*push mmos         # Main repo
*push lendaria     # Vercel deploy
*push vercel       # Alias for lendaria
*push app          # Alias for lendaria
*push outputs      # Generated artifacts
```

## Related Commands

- `*repos` - List all configured repositories
- `*repo-init <name>` - Initialize a new repository
- `*pre-push` - Run quality checks without pushing
