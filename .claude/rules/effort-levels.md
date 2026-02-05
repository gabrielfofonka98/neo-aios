# Effort Levels for Subagents

When spawning subagents via the Task tool, match effort to agent complexity.

## Mapping

| Effort | Model Param | Agents | Rationale |
|--------|-------------|--------|-----------|
| **max** | `model: "opus"` | Quinn (QA), Architect (Aria), Spec (Rune) | Deep reasoning, cross-validation, zero-ambiguity |
| **high** | `model: "opus"` | Dev (Dex), Data-Engineer (Dara), Ralph, Master (Orion) | Complex implementation, autonomous execution |
| **medium** | `model: "sonnet"` | PM (Morgan), PO, SM, Doc (Sage) | Text-heavy, specs, documentation |
| **low** | `model: "haiku"` | 18x sec-agents, fixer, clear-agent, test, handoff | Focused single-task — speed over depth |

## Rules

- `max` effort is **exclusive to Opus 4.6** — returns error on other models
- Team lead always uses `opus` regardless of effort level
- When Quinn dispatches sec-agents as subagents, use `model: "haiku"`
- Default effort when no explicit mapping: `high`
- Effort affects text, tool calls, AND thinking simultaneously
- Lower effort = fewer tool calls, less preamble, terse confirmations

## When to Override

- If a normally `low` agent encounters a complex edge case, escalate to `high`
- If a `max` agent is doing a trivial lookup, it will auto-adjust (adaptive thinking)
- Never force `max` on utility tasks (handoff, clear-agent) — waste of tokens
