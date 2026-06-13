# Design: Category for Expenses

**Date:** 2026-06-13
**Status:** Schema approved — API design pending

## Context

The `expense` table needed a classification mechanism. This spec covers the DB schema design for a `category` feature. API endpoint design is out of scope for this iteration.

## Decisions made

- Categories are **global** (system-wide, not per-group or per-user).
- Category on an expense is **mandatory** (NOT NULL). Default category: "Gastos genéricos".
- Categories are **administrable via API** (add/deactivate) — not hardcoded.
- **Soft-delete** via `is_active` instead of hard delete, to preserve referential integrity on historical expenses.

## Schema

### New table: `category`

```sql
CREATE TABLE IF NOT EXISTS category (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT        UNIQUE NOT NULL,
    description TEXT,
    is_active   BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
```

- `description` is optional (nullable).
- `is_active = FALSE` means the category is archived; it won't appear in the active list but existing expense references remain valid.

### Change to `expense`

```sql
ALTER TABLE expense
    ADD COLUMN category_id UUID NOT NULL REFERENCES category(id) ON DELETE RESTRICT;

CREATE INDEX IF NOT EXISTS idx_expense_category_id ON expense(category_id);
```

- `ON DELETE RESTRICT` is a second line of defense — the API only soft-deletes, but prevents accidental hard-deletes from psql from breaking expenses.

### Seed

```sql
INSERT INTO category (name, description)
VALUES ('Gastos genéricos', 'Categoría por defecto para expenses sin clasificar');
```

The frontend fetches the active category list via `GET /categories` and can preselect "Gastos genéricos" by name or by marking it as the default in the seed.

## Also applied (init SQL cleanup)

- Removed `CREATE EXTENSION IF NOT EXISTS "uuid-ossp"` — PostgreSQL 18.4 has `gen_random_uuid()` built-in.
- Replaced all `uuid_generate_v4()` with `gen_random_uuid()` across `01-init.sql`.
- Renamed table `"user"` → `app_user` (avoids SQL reserved word, removes mandatory quoting everywhere).
- Updated `db/seeds/01-seed.sql` to use `app_user`.

## Implementation notes

- The `category` table and `expense.category_id` column must be created via **Alembic migration**, not by modifying `01-init.sql` (which only runs on first container start).
- The `01-init.sql` changes above apply only to fresh container starts (dev/CI reset).
