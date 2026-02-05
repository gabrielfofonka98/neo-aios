# Task: KISS Schema Check

## Purpose
Analyze a PRD's proposed database schema against existing tables to maximize reuse and minimize new table creation.

## Trigger
- Command: `*kiss-schema-check {prd_path}`
- Or: `*kiss-schema-check` (will prompt for PRD path)

## Philosophy
> "The best table is the one you don't create."

Before creating ANY new table, this task validates:
1. Does an existing table serve the same purpose?
2. Can an existing table be extended (JSONB, nullable columns)?
3. Can existing relationships handle new requirements?

## Algorithm

```
KISS-FIRST SCHEMA ANALYSIS
==========================

INPUT: PRD document with proposed schema
OUTPUT: KISS Report with reuse recommendations

STEP 1: INVENTORY CURRENT DATABASE
───────────────────────────────────
Query all existing tables:
- Table names
- Row counts (tables with data = higher reuse value)
- JSONB columns (extensibility points)
- Nullable columns (extension candidates)

SQL:
```sql
SELECT
  t.table_name,
  (SELECT COUNT(*) FROM information_schema.columns c
   WHERE c.table_name = t.table_name
   AND c.data_type = 'jsonb') as jsonb_columns,
  pg_stat_user_tables.n_live_tup as row_count
FROM information_schema.tables t
LEFT JOIN pg_stat_user_tables
  ON t.table_name = pg_stat_user_tables.relname
WHERE t.table_schema = 'public'
  AND t.table_type = 'BASE TABLE'
ORDER BY row_count DESC;
```

STEP 2: EXTRACT PRD TABLES
──────────────────────────
Parse PRD for:
- Table names (look for "Tabela:", "CREATE TABLE", "#### Tabela:")
- Column definitions
- Relationships (REFERENCES, FK)

STEP 3: SEMANTIC MAPPING
────────────────────────
Map PRD tables to existing using semantic similarity:

| PRD Entity | Existing Candidates | Match Score |
|------------|---------------------|-------------|
| customers  | minds, user_profiles, auth.users | Check fields |
| products   | offers, content_projects | Check purpose |
| sales      | course_enrollments | Check fields |
| surveys    | forms, form_submissions | Exact match |
| users      | auth.users + user_profiles | Exact match |

Mapping rules:
- "customer" ≈ "mind" ≈ "user" ≈ "profile" (pessoa)
- "product" ≈ "offer" ≈ "course" ≈ "content_project"
- "sale" ≈ "enrollment" ≈ "subscription" ≈ "purchase"
- "survey" ≈ "form" ≈ "questionnaire" ≈ "feedback"
- "activity" ≈ "interaction" ≈ "event" ≈ "log"

STEP 4: REUSE ANALYSIS
──────────────────────
For each PRD table, determine:

A) FULL REUSE (0 changes)
   - Existing table serves exact purpose
   - Fields match or subset matches
   → Recommendation: Use existing table as-is

B) EXTEND (add columns/JSONB)
   - Existing table serves similar purpose
   - Missing fields can be added via:
     * JSONB metadata column
     * New nullable columns
   → Recommendation: ALTER TABLE or use JSONB

C) CREATE NEW (last resort)
   - No existing table serves purpose
   - Cannot extend existing tables
   - Functionality is truly novel
   → Recommendation: Create minimal table

STEP 5: GENERATE REPORT
───────────────────────
Output format:

## KISS Schema Check Report

### Executive Summary
- PRD Tables Proposed: N
- Can Reuse As-Is: X (Y%)
- Can Extend: Z (W%)
- Must Create: M (P%)
- **KISS Score: (X+Z)/(N) * 100%**

### Table-by-Table Analysis

| PRD Table | Recommendation | Existing Table | Strategy |
|-----------|----------------|----------------|----------|
| customers | REUSE | minds | Use directly |
| sales | EXTEND | course_enrollments | Add payment_metadata JSONB |
| pipelines | CREATE | - | New functionality |

### Recommended Schema Changes

1. **Tables to REUSE (0 migrations)**
   - `minds` as `customers`
   - `offers` as `products`

2. **Tables to EXTEND (1 migration each)**
   - `course_enrollments`: ADD COLUMN payment_metadata JSONB
   - `minds`: ADD COLUMN crm_status TEXT

3. **Tables to CREATE (minimum)**
   - `crm_pipelines` (new functionality)
   - `crm_pipeline_stages`
   - `crm_pipeline_cards`

### JSONB Extension Points

Existing tables with JSONB that can absorb new fields:
- `minds.metadata` → customer health_score, crm_status
- `offers.metadata` → product attributes
- `user_profiles.metadata` → team preferences

### Migration Complexity Score
- Original PRD: ~43 migrations
- After KISS: ~5 migrations
- **Reduction: 88%**
```

## Execution Steps

1. **Read PRD** (or receive path)
2. **Query current schema** (inventory)
3. **Parse PRD tables** (grep/regex)
4. **Semantic mapping** (table-to-table)
5. **Reuse analysis** (categorize each)
6. **Generate report** (markdown)
7. **Present recommendations**

## Integration with db-sage

This task is called by:
- `*kiss-schema-check {prd_path}` - Full analysis
- `*validate-kiss` - Quick gate check (calls this internally)

## Success Criteria

- KISS Score > 70% = Good (most reuse)
- KISS Score 50-70% = Acceptable (some new tables justified)
- KISS Score < 50% = Review PRD (over-engineering detected)

## Examples

### Example 1: CRM PRD
```
PRD proposes: 43 tables
After KISS analysis:
- Reuse: 20 tables (use existing)
- Extend: 18 tables (add JSONB/columns)
- Create: 5 tables (truly new)
KISS Score: 88%
```

### Example 2: Analytics PRD
```
PRD proposes: 12 tables
After KISS analysis:
- Reuse: 3 tables
- Extend: 5 tables
- Create: 4 tables (analytics-specific)
KISS Score: 67%
```

## Meta-Process

This task embodies the principle:
> "Query first, design second, create last"

The thought process:
1. What exists? (inventory)
2. What do I need? (PRD requirements)
3. Can I reuse? (mapping)
4. Can I extend? (JSONB, nullable)
5. Must I create? (last resort)

---

## Related Tasks
- `*validate-kiss` - Gate validation before any schema work
- `*create-schema` - Use AFTER kiss-schema-check approves
- `*audit-migration` - Validate any new tables proposed

## Version
- Created: 2026-01-16
- Author: DB Sage (extracted from CRM PRD analysis)
