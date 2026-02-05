# db-validate-kiss

KISS Gate validation - REQUIRED before any schema design work.

## Purpose

This task enforces the KISS (Keep It Simple, Stupid) principle before proposing any database schema changes. It prevents over-engineering by validating that changes are truly necessary.

## When to Use

- **MANDATORY** before `*create-schema`
- **MANDATORY** before `*model-domain`
- **MANDATORY** before proposing any ALTER TABLE
- **MANDATORY** before suggesting new tables
- When user asks for database changes

## KISS Gate Validation Steps

### Step 1: Validate Reality

**Question to user:**
> "Does the current system work today for this use case?"

| Answer | Action |
|--------|--------|
| Yes, it works | **STOP** - No change needed |
| No, it doesn't work | Continue to Step 2 |
| Partially works | Continue to Step 2, note limitations |

### Step 2: Validate Pain

**Question to user:**
> "What specific problem are you trying to solve? What breaks or is missing?"

| Answer | Action |
|--------|--------|
| "No specific problem" | **STOP** - Designing for hypotheticals |
| "It would be nice to have..." | **STOP** - Future-proofing without need |
| Clear pain point described | Continue to Step 3 |

### Step 3: Leverage Existing

**Check loaded schema context:**

1. Does a table already exist that could solve this?
2. Is there an existing column that could be used?
3. Is there a junction table (N:M) that handles this relationship?
4. Could a JSONB field in existing table work?
5. Could a view solve the query need without schema change?

**Present findings to user:**
> "Before proposing new structure, I found these existing options:
> 1. [Existing option 1]
> 2. [Existing option 2]
> Would any of these solve your problem?"

### Step 4: Minimum Increment

If new structure is truly needed, propose the **smallest possible change**:

**Hierarchy (prefer top):**
1. **No change** - Use existing structure differently
2. **Add 1 field** - To existing table
3. **Add index** - For performance
4. **Add 1 table** - Simple new entity
5. **Add N:M junction** - For relationships
6. **Multiple tables** - Only if absolutely necessary

### Step 5: Trade-Offs

Present options with clear trade-offs:

```
**Option A: [Smallest change]**
- Pros: Simple, fast, low risk
- Cons: [limitations]
- Migration: [complexity]

**Option B: [Medium change]**
- Pros: More flexible
- Cons: More complexity, migration needed
- Migration: [complexity]

**Option C: [Largest change]**
- Pros: Full solution
- Cons: High complexity, risk
- Migration: [complexity]

Which option do you prefer? (Recommend: Option A unless you have strong reasons)
```

## Red Flags Checklist

If ANY of these are true, **STOP and re-validate with user:**

- [ ] Proposing 3+ new tables without explicit user request
- [ ] Proposing 10+ new fields without validated pain point
- [ ] Assuming analytics/tracking needed without evidence
- [ ] Designing for "future needs" instead of current pain
- [ ] Not checking existing schema first (run *load-schema)
- [ ] Over-engineering beyond stated problem
- [ ] User can't articulate specific problem being solved

## Output Format

After validation, present:

```
✅ KISS Gate Validation Complete

**Problem Statement:** [User's stated problem]
**Current State:** [What exists today]
**Validated Need:** [Yes/No with reasoning]

**Recommendation:**
[Smallest change that solves the problem]

**Alternatives Considered:**
1. [Alternative 1] - Rejected because [reason]
2. [Alternative 2] - Rejected because [reason]

Proceed with implementation? (y/n)
```

## Golden Rules

1. **"If it works today, changing it needs extraordinary justification"**
2. **Ask before assuming** - Never assume user wants complexity
3. **Smallest first** - Always propose minimum viable change
4. **Existing over new** - Prefer using existing structures
5. **Pain over features** - Solve real problems, not hypotheticals

---

**Related Commands:**
- `*load-schema` - Load schema context BEFORE this task
- `*create-schema` - Run AFTER KISS validation passes
- `*model-domain` - Run AFTER KISS validation passes
