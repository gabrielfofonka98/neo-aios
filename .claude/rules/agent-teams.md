# Agent Teams (Experimental)

Enabled via `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in user's `~/.claude/settings.json`.

## What It Is

Multiple Claude Code instances working in parallel, coordinated via shared task list and messaging.
One session acts as **team lead**, others are **teammates**.

## Anti-Conflict Rules (CRITICAL)

```
RULE 1: Each teammate MUST own a distinct set of files
        NO two teammates can edit the same file simultaneously

RULE 2: Read-only agents (sec-agents, analysts) are inherently safe
        They only grep/read — zero conflict risk

RULE 3: Write-heavy agents (dev, data-engineer) need explicit file boundaries
        Team lead must assign file ownership BEFORE dispatching

RULE 4: Team lead coordinates via task list, NOT direct file manipulation
        Lead creates tasks → teammates claim → teammates execute → lead collects

RULE 5: If conflict detected → STOP → notify team lead → resolve before continuing
```

## Ideal Use Cases

1. **Quinn's Security Audit** — 18 sec-agents as teammates, all read-only, max parallelism
2. **Research tasks** — Multiple agents investigating different angles simultaneously
3. **Cross-layer coordination** — Frontend + Backend + Database working in parallel with clear file boundaries
4. **Code review** — Multiple reviewers checking different modules

## NOT Ideal For

- Two agents implementing features in the same file
- Tasks that require sequential decision-making
- Short tasks that don't benefit from parallelism overhead

## Known Limitations

- No session resumption for in-process teammates (`/resume` won't restore them)
- Token-intensive — each teammate is a separate Claude instance with full context
- Shutdown behavior can be inconsistent
- If team lead dies, teammates become orphaned — must spawn new ones

## How Quinn Uses Agent Teams

When `*security-audit` is invoked and Agent Teams is available:
1. Quinn spawns team `"security-audit"` via Teammate tool
2. Creates 18 tasks (one per sec-agent scan)
3. Spawns teammates with `model: "haiku"` for each sec-agent
4. All 18 scan in parallel (read-only = zero conflict)
5. Results flow back to Quinn via messages
6. Quinn cross-validates, generates consolidated report
7. Cleanup: shutdown all teammates, remove team
