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
- Schema is defined entirely in `db/init/01-init.sql` (fresh start, no ALTER TABLE, no Alembic migrations needed for the initial schema).

## Schema

### Init SQL (`db/init/01-init.sql`)

Full schema in creation order. `category` must be created before `expense` due to the FK dependency.

```sql
CREATE TABLE IF NOT EXISTS category (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT        UNIQUE NOT NULL,
    description TEXT,
    is_active   BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS expense (
    id          UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    group_id    UUID          NOT NULL REFERENCES "group"(id) ON DELETE CASCADE,
    paid_by     UUID          NOT NULL REFERENCES app_user(id) ON DELETE RESTRICT,
    category_id UUID          NOT NULL REFERENCES category(id) ON DELETE RESTRICT,
    amount      NUMERIC(12,2) NOT NULL CHECK (amount > 0),
    description TEXT,
    date        DATE          NOT NULL,
    created_at  TIMESTAMPTZ   DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_expense_category_id ON expense(category_id);
```

- `description` on `category` is optional (nullable).
- `is_active = FALSE` means archived; won't appear in the active list but existing expense references remain valid.
- `ON DELETE RESTRICT` on `category_id` is a second line of defense against hard-deletes from psql.

### Seed (`db/seeds/01-seed.sql`)

```sql
INSERT INTO category (name, description) VALUES
    ('Gastos genéricos', 'Categoría por defecto para expenses sin clasificar')
ON CONFLICT DO NOTHING;
```

The frontend fetches the active category list via `GET /categories` and preselects "Gastos genéricos" by name.

## Also applied (init SQL cleanup)

- Removed `CREATE EXTENSION IF NOT EXISTS "uuid-ossp"` — PostgreSQL 18.4 has `gen_random_uuid()` built-in.
- Replaced all `uuid_generate_v4()` with `gen_random_uuid()` across `01-init.sql`.
- Renamed table `"user"` → `app_user` (avoids SQL reserved word, removes mandatory quoting everywhere).
- Updated `db/seeds/01-seed.sql` to use `app_user`.

## API design (future)

Out of scope for this spec. Will cover:
- `GET /api/v1/categories` — list active categories
- `POST /api/v1/categories` — create category
- `DELETE /api/v1/categories/{id}` — soft-delete (set `is_active = false`)
