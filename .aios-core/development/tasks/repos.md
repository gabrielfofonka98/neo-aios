# Repos Task

## Metadata
```yaml
task_id: repos
title: List Configured Repositories
agent: devops
complexity: simple
elicit: false
config_file: .aios-core/development/config/repos.yaml
```

## Description

Display all configured repositories with their status, remotes, and quick actions.

**Usage:** `*repos`

## Execution Steps

### Step 1: Load Repository Registry

Read config from `.aios-core/development/config/repos.yaml`

### Step 2: Check Each Repository Status

For each repo in config:

```bash
cd <repo.path> && git remote get-url <repo.remote> 2>/dev/null
cd <repo.path> && git status --porcelain 2>/dev/null | wc -l
cd <repo.path> && git log -1 --oneline 2>/dev/null
```

### Step 3: Display Repository Table

```
📦 Repository Registry

┌─────────────┬────────────────────────────────────┬──────────┬───────────┐
│ Name        │ Description                        │ Status   │ Changes   │
├─────────────┼────────────────────────────────────┼──────────┼───────────┤
│ mmos        │ Main development repository        │ ✅ Ready │ 5 files   │
│ lendaria    │ Vercel deployment (nested repo)    │ ✅ Ready │ 142 files │
│ outputs     │ Generated artifacts                │ ⚠️ N/A   │ -         │
└─────────────┴────────────────────────────────────┴──────────┴───────────┘

Aliases: vercel → lendaria, app → lendaria, main → mmos

Quick Commands:
  *push <name>     Push to specific repo
  *push            Interactive repo selection
  *repo-init <n>   Initialize unconfigured repo
```

### Step 4: Show Details (Optional)

If user requests details for specific repo:

```
📦 mmos (Main development repository)

  Path:    /Users/alan/Code/mmos
  Remote:  origin → https://github.com/oalanicolas/mmos.git
  Branch:  main
  Status:  ✅ Ready

  Last Commit: 7c568fb feat: add Vercel push task
  Changes:     5 modified, 2 untracked

  Options:
    force_push:       false
    pre_push_checks:  true

  Commands:
    *push mmos        Push changes
    *pre-push         Run quality checks
```

## Status Indicators

| Status | Meaning |
|--------|---------|
| ✅ Ready | Git repo configured, remote accessible |
| ⚠️ N/A | Not initialized (needs `*repo-init`) |
| ❌ Error | Path missing or remote unreachable |
| 🔄 Ahead | Local commits not pushed |
| 📥 Behind | Remote has new commits |

## Related Commands

- `*push` - Push to repository
- `*push <name>` - Push to specific repo
- `*repo-init <name>` - Initialize repository
