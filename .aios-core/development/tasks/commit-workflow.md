# Commit Workflow Task (Automated)

## Metadata
```yaml
task_id: commit-workflow
title: Automated Commit Workflow
agent: devops
complexity: medium
elicit: false
trigger: user says "commit"
```

## Description

Automated workflow that triggers when user says "commit". Executes full pipeline without user interaction:

1. **Stage selectively** - Split into multiple commits by category
2. **Run pre-push** - Execute quality gates
3. **Push** - Push to remote
4. **Auto-merge if needed** - Prioritize local data

## Execution Steps

### Step 1: Analyze Changes

```bash
git status --porcelain
```

Categorize files by:
- **Deletions** (`D `) - Files removed
- **Modifications** (`M `) - Files changed
- **Additions** (`A ` or `??`) - New files

### Step 2: Group by Commit Category

**Order of commits:**

1. `chore: cleanup` - All deletions
   - Deleted docs, reports, legacy files
   - Removed directories

2. `chore: config` - Configuration changes
   - `.claude/`, `.aios-core/` config files
   - `package.json`, `tsconfig.json`
   - Environment files

3. `docs:` - Documentation updates
   - `docs/` directory changes
   - READMEs, guides, architecture docs

4. `refactor:` - Code restructuring
   - File moves/renames
   - Directory reorganization
   - Non-functional code changes

5. `feat:` - New features
   - New components, functions
   - New capabilities

6. `fix:` - Bug fixes
   - Error corrections
   - Issue resolutions

### Step 3: Execute Commits

For each category with changes:

```bash
# Stage files for this category
git add <files>

# Commit with appropriate message
git commit -m "<type>: <description>

<details>

Co-Authored-By: Claude <noreply@anthropic.com>"
```

**Commit message format:**
- Type: `chore:`, `docs:`, `refactor:`, `feat:`, `fix:`
- Description: Brief summary (50 chars max)
- Details: Bullet list of changes
- Co-author: Always include Claude attribution

### Step 4: Run Pre-Push Quality Gates

Execute `.aios-core/development/tasks/devops-pre-push-quality-gate.md`:

**Quality checks (in order):**
1. `npm run lint` - Linting (if package.json exists)
2. `npm run typecheck` - Type checking (if TypeScript)
3. `npm test` - Tests (if test suite exists)
4. `npm run build` - Build verification (if build script exists)

**Skip checks if:**
- No `package.json` in repository
- Only documentation/config changes
- Changes don't affect code

### Step 5: Push to Remote

```bash
# Standard push
git push origin <branch>

# Force push (for Vercel repos only)
git push -f origin main
```

### Step 6: Auto-Merge if Needed

If push is rejected due to remote changes:

**Merge Strategy:**
```bash
git fetch origin
git merge origin/<branch> -X ours
git push origin <branch>
```

**Rules:**
- Always prioritize LOCAL changes over remote
- Keep most complete/updated version
- Use `ours` strategy (local wins)
- Never lose local work

### Step 7: Report Summary

```
## Commit Summary

| # | Type | Files | Message |
|---|------|-------|---------|
| 1 | chore | 150 | cleanup - remove obsolete files |
| 2 | chore | 5 | config - update CLAUDE.md |
| 3 | docs | 20 | reorganize documentation |

## Push Status
✅ Pushed 3 commits to origin/main
Branch is up to date with remote.
```

## Error Handling

| Error | Action |
|-------|--------|
| Lint fails | Skip push, report error |
| Test fails | Skip push, report error |
| Merge conflict | Use `ours` strategy (local wins) |
| Push rejected | Fetch, merge, retry |
| Auth failure | Report and abort |

## Configuration

Defined in `.claude/CLAUDE.md` under "Commit Workflow Automation (DevOps)":

```yaml
auto_commit:
  enabled: true
  split_by_category: true
  categories:
    - chore: cleanup
    - chore: config
    - docs
    - refactor
    - feat
    - fix
  pre_push: true
  auto_push: true
  merge_strategy: ours  # local wins
  force_push_repos:
    - lendaria
    - vercel
```

## Related Tasks

- `push.md` - Manual push task
- `devops-pre-push-quality-gate.md` - Quality gates
- `repos.md` - Repository configuration
