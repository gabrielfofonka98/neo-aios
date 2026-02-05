# Model & Thinking Configuration (Opus 4.6)

**Model:** `claude-opus-4-6` (default)
**Thinking:** Adaptive — model decides when to think deeply based on task complexity
**Context:** 1M tokens (beta) — premium pricing above 200K ($10/$37.50 per M input/output)
**Output:** Up to 128K tokens (requires streaming above 64K)

## Adaptive Thinking

- `alwaysThinkingEnabled` is **DEPRECATED** — do NOT use in settings
- Opus 4.6 uses `thinking: {type: "adaptive"}` natively
- At `high`/`max` effort: Claude almost always thinks deeply
- At `low`/`medium` effort: Claude may skip thinking for simpler tasks
- No configuration needed — this is the model's default behavior

## Key Rules

- NEVER use `budget_tokens` on Opus 4.6 (deprecated, will be removed)
- NEVER prefill assistant messages (returns 400 error on Opus 4.6)
- `output_format` moved to `output_config.format` (old param deprecated)
- Use streaming for requests with `max_tokens` > 64K to avoid HTTP timeouts
