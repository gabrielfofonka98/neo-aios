# db-load-schema

Load LIVE database schema into session context for informed decision-making.

## Purpose

This task queries the connected database to load the current schema structure into the session context. This enables the data-engineer agent to make informed decisions about schema changes by understanding what already exists.

## When to Use

- **Before any schema design work** (`*create-schema`, `*model-domain`)
- **When starting a new database session**
- **When you need to understand existing table structure**
- **Before proposing any ALTER TABLE operations**

## Prerequisites

- Database connection configured (SUPABASE_DB_URL or DATABASE_URL in .env)
- psql or appropriate database client available

## Execution Steps

### Step 1: Detect Database Connection

Try to find database connection in this order:

1. `SUPABASE_DB_URL` → PostgreSQL (Supabase)
2. `DATABASE_URL` → PostgreSQL (generic)
3. `MYSQL_CONNECTION_URL` → MySQL
4. `MONGODB_URI` → MongoDB
5. SQLite file in `outputs/database/` or `data/` → SQLite

If none found, inform user to set database connection.

### Step 2: Query Schema (PostgreSQL/Supabase)

Execute single comprehensive query:

```bash
psql "$SUPABASE_DB_URL" -t -A -c "
SELECT json_build_object(
  'tables', (SELECT json_agg(table_name) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE'),
  'table_count', (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE'),
  'fk_count', (SELECT COUNT(*) FROM information_schema.table_constraints WHERE constraint_type='FOREIGN KEY' AND table_schema='public'),
  'views_count', (SELECT COUNT(*) FROM information_schema.views WHERE table_schema='public')
)
"
```

### Step 3: Get Column Details (if needed)

For detailed schema context:

```bash
psql "$SUPABASE_DB_URL" -t -A -c "
SELECT table_name, column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema='public'
ORDER BY table_name, ordinal_position
"
```

### Step 4: Get Foreign Key Relationships

```bash
psql "$SUPABASE_DB_URL" -t -A -c "
SELECT
  tc.table_name as from_table,
  kcu.column_name as from_column,
  ccu.table_name as to_table,
  ccu.column_name as to_column
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu ON tc.constraint_name = ccu.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = 'public'
"
```

## Output Format

Present schema context summary:

```
📊 Database Schema Loaded

**Connection:** [Database type detected]
**Tables:** [count] tables
**Views:** [count] views
**Relationships:** [count] foreign keys

**Sample Tables:**
- table1 (col1, col2, col3...)
- table2 (col1, col2, col3...)
- ...

Schema context is now in session. Ready for design work.
Use *validate-kiss before proposing schema changes.
```

## Error Handling

| Error | Resolution |
|-------|------------|
| Connection refused | Check database is running, verify URL |
| Authentication failed | Verify password in connection string |
| No env var found | Ask user to configure SUPABASE_DB_URL |
| Timeout | Database may be under load, retry |

## Session Context

After successful execution, the agent should remember:
- List of all tables
- Column structure per table
- Foreign key relationships
- Junction tables (N:M relationships)
- Approximate row counts

This context informs all subsequent schema decisions.

---

**Related Commands:**
- `*validate-kiss` - Run after loading schema, before design work
- `*create-schema` - Design new schema (uses loaded context)
- `*model-domain` - Domain modeling (uses loaded context)
