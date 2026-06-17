---
name: reset-all-db
description: >-
  Fully reset ALL local Docker Compose data for this project — destroys every
  named volume (both the app DB and Keycloak's DB), recreates the containers
  from scratch so db/init/01-init.sql re-runs and the Keycloak realm is
  re-imported, then re-applies the seed data. Unlike reset-db (which protects
  Keycloak), this wipes everything. Invoke when the user wants to reset / wipe /
  nuke the entire stack, clear all volumes, start completely from scratch, or
  recover from a fully corrupted local environment. DESTRUCTIVE — always confirm
  first.
---

# Reset ALL local Docker Compose data

Restore the **entire** stack to a clean state by destroying every named volume
and recreating it. This is **destructive and irreversible** for all local data
— both the app database *and* Keycloak's realm/users/sessions. There is no
backup step. Confirm with the user before running anything.

## What this touches (and how it differs from `reset-db`)

This project defines two named volumes (`compose.yaml`):

- `app_postgres_data` — the application DB (`app_db`)
- `keycloak_postgres_data` — Keycloak's DB (realm config, users, sessions)

`reset-db` deliberately removes **only** the app volume and leaves Keycloak
intact. **This skill removes BOTH.** That means after running it, Keycloak
re-imports its realm from `keycloak/realm-export.json` on next start — any
manual changes made in the Keycloak admin console (extra users, client tweaks,
etc.) are lost and revert to the committed realm export. Make sure the user
actually wants that before proceeding; if they only want fresh app data, use
`reset-db` instead.

## Connection values (from compose.yaml)

Defaults, overridable by the root `.env`:

| Thing        | Value                                | Env var / source             |
| ------------ | ------------------------------------ | ---------------------------- |
| app service  | `app_db`                             | —                            |
| app user     | `admin`                              | `POSTGRES_USER`              |
| app database | `expense_db`                         | `POSTGRES_DB`                |
| seed file    | `db/seeds/01-seed.sql` (host path)   | —                            |
| init scripts | `db/init/` → `/docker-entrypoint-initdb.d` (auto-run on empty volume only) | |
| realm import | `keycloak/realm-export.json` (auto-imported via `--import-realm` on start) | |

If the user has a root `.env`, read `POSTGRES_USER` / `POSTGRES_DB` from it and
use those instead of the defaults.

## Procedure

1. **Confirm intent.** State plainly that this erases *all* local data — the app
   DB **and** Keycloak's realm/users/sessions — and cannot be undone. Make sure
   the user understands this is broader than `reset-db`. If they hesitate or only
   want app data, point them to `reset-db`.

2. **Tear down the whole stack and remove every volume.** `docker compose down
   -v` removes all containers and *all* named volumes for the project in one
   shot. Include every profile so nothing is left running with a stale volume
   attached.

   ```bash
   docker compose --profile all --profile infra down -v
   ```

3. **Verify both volumes are actually gone** before recreating — abort if either
   still exists, so we never silently reattach un-reset data.

   ```bash
   for vol in app_postgres_data keycloak_postgres_data; do
     V=$(docker volume ls -q \
       --filter label=com.docker.compose.project=expense-app \
       --filter label=com.docker.compose.volume=$vol)
     if [ -n "$V" ]; then
       echo "ERROR: volume $V still exists — aborting, nothing reset." >&2
       exit 1
     fi
   done
   ```

4. **Recreate the infra.** On the now-empty volumes, `app_db` re-runs the scripts
   in `db/init/` and Keycloak re-imports its realm. Bring up the infra profile
   (app_db + keycloak_db + keycloak); add `backend`/`frontend` or use the `all`
   profile if the user wants the full stack.

   ```bash
   docker compose --profile infra up -d
   ```

5. **Wait for `app_db` to be healthy** before seeding (the healthcheck is more
   reliable than `pg_isready`, which can report ready mid-init before
   `01-init.sql` finishes).

   ```bash
   until [ "$(docker compose ps app_db --format '{{.Health}}')" = "healthy" ]; do
     sleep 1
   done
   ```

   **Migrations caveat:** step 4 applies only `db/init/01-init.sql`. If the live
   schema has diverged via Alembic migrations beyond that baseline, run
   `docker compose exec backend alembic upgrade head` before seeding (requires the
   `backend` container running). If unsure whether `backend/alembic/versions/`
   holds migrations not reflected in `01-init.sql`, ask the user rather than
   guessing.

6. **Apply seeds** (db/seeds is NOT mounted, so pipe from the host with `-T`).

   ```bash
   docker compose exec -T app_db psql -U admin -d expense_db < db/seeds/01-seed.sql
   ```

7. **Verify** the reset took:

   ```bash
   docker compose exec -T app_db psql -U admin -d expense_db \
     -c "SELECT 'users' t, count(*) FROM users
         UNION ALL SELECT 'categories', count(*) FROM categories
         UNION ALL SELECT 'groups', count(*) FROM groups;"
   ```

   Expect the seeded counts (Alice/Bob users, the default category, the seeded
   group), not zero.

8. **Report** to the user: that the whole stack was wiped and recreated, the row
   counts after reseeding, and a reminder that Keycloak was re-imported from
   `keycloak/realm-export.json` (so the test users `alice / password` and
   `bob / password` are available again, and any manual Keycloak changes are gone).
