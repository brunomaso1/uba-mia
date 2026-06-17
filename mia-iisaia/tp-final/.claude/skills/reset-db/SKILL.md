---
name: reset-db
description: >-
  Reset the local application database (app_db) to a clean state and re-apply
  the seed data, for this Docker Compose project. Two modes — a full reset that
  destroys the app_db volume so db/init/01-init.sql re-runs, and a soft reset
  that truncates the app tables and re-seeds without a restart. Invoke when the
  user wants to reset / wipe / reinitialize / reseed the dev database, start
  from a clean DB, or recover from corrupted local data. DESTRUCTIVE — always
  confirm first.
---

# Reset the local app database

Restore `app_db` to a clean, seeded state. This is **destructive and
irreversible** for local data — there is no backup step. Confirm with the user
before running anything.

## Critical safety rules

- This project runs **two** PostgreSQL instances with two volumes:
  `app_postgres_data` (the app DB — the only thing this skill touches) and
  `keycloak_postgres_data` (Keycloak's realm/users — must NOT be affected).
- **Never run `docker compose down -v`** — that removes *both* volumes and wipes
  the Keycloak realm. Always target the app volume by name.
- Only ever operate on the `app_db` service and the
  `expense-app_app_postgres_data` volume.

## Connection values (from compose.yaml)

Defaults, overridable by the root `.env`:

| Thing        | Value                              | Env var / source              |
| ------------ | ---------------------------------- | ----------------------------- |
| service      | `app_db`                           | —                             |
| user         | `admin`                            | `POSTGRES_USER`               |
| database     | `expense_db`                       | `POSTGRES_DB`                 |
| volume       | resolve dynamically (see Mode A)   | compose label, not a literal  |
| seed file    | `db/seeds/01-seed.sql` (host path) | —                             |
| init scripts | `db/init/` → `/docker-entrypoint-initdb.d` (auto-run on empty volume only) | |

If the user has a root `.env`, read `POSTGRES_USER` / `POSTGRES_DB` from it and use
those instead of the defaults. (Note: CLAUDE.md and the seed file's comment reference
a `db` service and `expense_user` — those are stale; the real service is `app_db` and
the default user is `admin`.)

Do NOT hardcode the volume name. Although it is normally
`expense-app_app_postgres_data`, a project-name override would change it and turn the
destructive step into a silent no-op. Resolve it by compose label instead (Mode A,
step 2). Likewise the table list for Mode B is derived at runtime, not hardcoded —
the schema uses some singular table names (e.g. `group_member`), so a guessed plural
list would break.

## Mode A — Full reset (default; re-runs schema init)

Use when the schema may be stale/corrupted or the user wants a truly clean slate.
This destroys the volume so `db/init/01-init.sql` runs again on a fresh start.

```bash
# 1. Stop and remove ONLY the app_db container (leaves keycloak untouched)
docker compose stop app_db
docker compose rm -f app_db

# 2. Resolve the app volume by compose label (robust to project-name overrides),
#    then remove ONLY that volume. ABORT if anything fails — never proceed to a
#    recreate that would silently reattach the old, un-reset volume.
VOL=$(docker volume ls -q \
  --filter label=com.docker.compose.project=expense-app \
  --filter label=com.docker.compose.volume=app_postgres_data)
if [ -z "$VOL" ]; then
  echo "ERROR: app_postgres_data volume not found — aborting, nothing reset." >&2
  exit 1
fi
docker volume rm "$VOL" || { echo "ERROR: could not remove $VOL (still in use?) — aborting." >&2; exit 1; }
# Confirm it's actually gone before recreating
docker volume inspect "$VOL" >/dev/null 2>&1 && { echo "ERROR: $VOL still exists — aborting." >&2; exit 1; }

# 3. Recreate app_db — init scripts in db/init/ run automatically on the empty volume
docker compose up -d app_db

# 4. Wait for the compose HEALTHCHECK to pass (more reliable than pg_isready, which
#    can report ready during Postgres's init-script phase, before 01-init.sql finishes)
until [ "$(docker compose ps app_db --format '{{.Health}}')" = "healthy" ]; do
  sleep 1
done

# 5. Apply seeds (db/seeds is NOT mounted, so pipe from the host with -T)
docker compose exec -T app_db psql -U admin -d expense_db < db/seeds/01-seed.sql
```

If any step before 5 aborts, stop and tell the user the DB was left untouched —
do NOT report a successful reset.

**Migrations caveat:** step 3 applies only `db/init/01-init.sql`. If the live schema
has diverged via Alembic migrations beyond that baseline, run
`docker compose exec backend alembic upgrade head` between steps 4 and 5 (requires
the `backend` container running). Check whether `backend/alembic/versions/` holds
migrations not reflected in `01-init.sql`; if unsure, ask the user rather than
guessing — applying `upgrade head` over an already-complete init schema can error on
existing tables.

## Mode B — Soft reset (keeps schema, faster)

Use when the schema is fine and the user just wants fresh data — no container
restart, no volume removal. Truncates the app tables and re-seeds.

Truncate every table in the `public` schema dynamically, rather than hardcoding a
list (the schema mixes singular/plural names like `group_member`, and tables get
added over time). Exclude `alembic_version` so migration state is preserved.

```bash
docker compose exec -T app_db psql -U admin -d expense_db <<'SQL'
DO $$
DECLARE r RECORD;
BEGIN
  FOR r IN
    SELECT tablename FROM pg_tables
    WHERE schemaname = 'public' AND tablename <> 'alembic_version'
  LOOP
    EXECUTE 'TRUNCATE TABLE ' || quote_ident(r.tablename) || ' RESTART IDENTITY CASCADE';
  END LOOP;
END $$;
SQL

docker compose exec -T app_db psql -U admin -d expense_db < db/seeds/01-seed.sql
```

`RESTART IDENTITY CASCADE` clears all rows and FK-dependent rows in one shot
regardless of order.

## Procedure

1. **Confirm intent and mode.** State plainly that this erases local app data and
   cannot be undone. Default to Mode B (soft) if the user only mentions reseeding;
   use Mode A (full) if they mention the schema, init, corruption, or "from scratch".
2. **Check the stack is up.** Mode B needs `app_db` running
   (`docker compose ps app_db`). If it's down, either start it
   (`docker compose up -d app_db`) or switch to Mode A, which starts it anyway.
3. **Run the chosen mode's commands** exactly, substituting any `.env` overrides.
4. **Verify** the reset took:
   ```bash
   docker compose exec -T app_db psql -U admin -d expense_db \
     -c "SELECT 'users' t, count(*) FROM users
         UNION ALL SELECT 'categories', count(*) FROM categories
         UNION ALL SELECT 'groups', count(*) FROM groups;"
   ```
   Expect the seeded counts (e.g. Alice/Bob users, the default category, the seeded
   group), not zero.
5. **Report** to the user: which mode ran, the row counts after reseeding, and
   confirmation that Keycloak's database was left untouched.
