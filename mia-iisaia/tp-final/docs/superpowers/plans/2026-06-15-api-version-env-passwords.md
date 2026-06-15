# API version parametrization, env cleanup, dev passwords Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Parametrize the API version in the frontend runtime config, remove the unnecessary `.env.local` convention, and unify dev user passwords to `password`.

**Architecture:** Three independent changes touching config files, compose, and documentation. No new abstractions. Tasks 1–2 form one logical feature (API version); Tasks 3 and 4 are fully independent. All changes are verifiable by running `ng test` (frontend) and inspecting diffs.

**Tech Stack:** Angular 22 (Vitest), Docker Compose, Keycloak realm JSON, Markdown docs.

---

## File map

| File | Task | Change |
|------|------|--------|
| `frontend/public/config.template.json` | 1 | Add `${API_VERSION}` to apiUrl |
| `frontend/public/config.json` | 1 | Update local default to include `/api/v1` |
| `compose.yaml` | 1 | Add `API_VERSION: ${API_VERSION:-v1}` to frontend env |
| `.env.example` | 1 | Add `API_VERSION=v1` |
| `frontend/src/app/app.ts` | 2 | Remove hardcoded `/api/v1` path segment |
| `README.md` | 2, 3, 4 | Runtime config docs; .env.local removal; credentials table |
| `keycloak/realm-export.json` | 4 | alice123 → password, bob123 → password |
| `.claude/CLAUDE.md` | 4 | Update test users line |

---

## Task 1: Parametrize API version in config files

**Files:**
- Modify: `frontend/public/config.template.json`
- Modify: `frontend/public/config.json`
- Modify: `compose.yaml`
- Modify: `.env.example`

- [ ] **Step 1.1: Update config.template.json**

Replace:
```json
{
  "apiUrl": "${API_URL}",
  "auth": {
    "authority": "${KEYCLOAK_AUTHORITY}",
    "clientId": "${KEYCLOAK_CLIENT_ID}",
    "scope": "openid profile email"
  }
}
```
With:
```json
{
  "apiUrl": "${API_URL}/api/${API_VERSION}",
  "auth": {
    "authority": "${KEYCLOAK_AUTHORITY}",
    "clientId": "${KEYCLOAK_CLIENT_ID}",
    "scope": "openid profile email"
  }
}
```

Note: `entrypoint.sh` already detects placeholders dynamically via `grep -o '\${[A-Za-z_][A-Za-z0-9_]*}'`, so `${API_VERSION}` is picked up automatically — no change to `entrypoint.sh` needed.

- [ ] **Step 1.2: Update config.json (local hybrid default)**

Replace:
```json
{
  "apiUrl": "http://localhost:8000",
  "auth": {
    "authority": "http://localhost:8080/realms/expense-app",
    "clientId": "expense-frontend",
    "scope": "openid profile email"
  }
}
```
With:
```json
{
  "apiUrl": "http://localhost:8000/api/v1",
  "auth": {
    "authority": "http://localhost:8080/realms/expense-app",
    "clientId": "expense-frontend",
    "scope": "openid profile email"
  }
}
```

- [ ] **Step 1.3: Add API_VERSION to compose.yaml frontend environment**

In `compose.yaml`, locate the frontend service environment block (around line 118):
```yaml
      API_URL: ${API_URL:-http://localhost:8000}
      KEYCLOAK_AUTHORITY: ${KEYCLOAK_AUTHORITY:-http://localhost:8080/realms/expense-app}
```
Add `API_VERSION` immediately after `API_URL`:
```yaml
      API_URL: ${API_URL:-http://localhost:8000}
      API_VERSION: ${API_VERSION:-v1}
      KEYCLOAK_AUTHORITY: ${KEYCLOAK_AUTHORITY:-http://localhost:8080/realms/expense-app}
```

- [ ] **Step 1.4: Add API_VERSION to .env.example**

In `.env.example`, locate:
```
API_URL=http://localhost:8000

# Image versions (optional)
```
Replace with:
```
API_URL=http://localhost:8000
API_VERSION=v1

# Image versions (optional)
```

- [ ] **Step 1.5: Commit**

```bash
git add frontend/public/config.template.json frontend/public/config.json compose.yaml .env.example
git commit -m "feat: parametrize API version in frontend runtime config"
```

---

## Task 2: Remove hardcoded /api/v1 from app.ts + update docs

**Files:**
- Modify: `frontend/src/app/app.ts`
- Modify: `README.md`

- [ ] **Step 2.1: Remove hardcoded /api/v1 from app.ts**

In `frontend/src/app/app.ts`, locate line 23:
```ts
    this.authenticated().isAuthenticated ? `${this.apiUrl()}/api/v1/users/me` : undefined,
```
Replace with:
```ts
    this.authenticated().isAuthenticated ? `${this.apiUrl()}/users/me` : undefined,
```

- [ ] **Step 2.2: Run frontend tests**

```bash
cd frontend
ng test --watch=false
```

Expected: all tests pass. The `config.service.spec.ts` tests pass through whatever value is in config — no changes needed there.

- [ ] **Step 2.3: Update README — Runtime Configuration section**

In `README.md`, make these three targeted edits:

**Edit A** — Update the envsubst placeholder example (around line 340):

Old:
```
2. It reads `config.template.json` and replaces the allowed placeholders (e.g. `${API_URL}`, `${AUTH_AUTHORITY}`).
```
New:
```
2. It reads `config.template.json` and replaces the allowed placeholders (e.g. `${API_URL}`, `${API_VERSION}`, `${KEYCLOAK_AUTHORITY}`).
```

**Edit B** — Update the Hybrid env description (around line 347):

Old:
```
| **Local — Hybrid** (`ng serve`) | The committed `frontend/public/config.json` is served as-is (defaults to `http://localhost:8000`). |
```
New:
```
| **Local — Hybrid** (`ng serve`) | The committed `frontend/public/config.json` is served as-is (defaults to `http://localhost:8000/api/v1`). |
```

**Edit C** — Update config.json file description (around line 353):

Old:
```
- **`config.json`** — committed with the local-dev default (`http://localhost:8000`). Used directly by `ng serve`. In Docker it is **overwritten** at container start by the step below, so the committed value only matters for local hybrid development.
```
New:
```
- **`config.json`** — committed with the local-dev default (`http://localhost:8000/api/v1`). Used directly by `ng serve`. In Docker it is **overwritten** at container start by the step below, so the committed value only matters for local hybrid development.
```

**Edit D** — Update the "Setting it in Docker" line (around line 356) to mention `API_VERSION` and remove `.env.local`:

Old:
```
**Setting it in Docker:** `compose.yaml` passes runtime vars to the frontend service (for example `API_URL: ${API_URL:-http://localhost:8000}`). Override values per environment in the corresponding env file (`.env.local`, `.env.dev`, `.env.prod`) — e.g. `API_URL=https://expense.yourdomain.com`.
```
New:
```
**Setting it in Docker:** `compose.yaml` passes runtime vars to the frontend service (for example `API_URL: ${API_URL:-http://localhost:8000}` and `API_VERSION: ${API_VERSION:-v1}`). Override values per environment in the corresponding env file (`.env.dev`, `.env.prod`) — e.g. `API_URL=https://expense.yourdomain.com`.
```

**Edit E** — Update the code comment in the example shell script (around line 375):

Old:
```
# Build a whitelist like: ${API_URL} ${AUTH_AUTHORITY} ${AUTH_CLIENT_ID}
```
New:
```
# Build a whitelist like: ${API_URL} ${API_VERSION} ${KEYCLOAK_AUTHORITY} ${KEYCLOAK_CLIENT_ID}
```

- [ ] **Step 2.4: Commit**

```bash
git add frontend/src/app/app.ts README.md
git commit -m "feat: remove hardcoded /api/v1 prefix from frontend URL construction"
```

---

## Task 3: Remove .env.local from README

**Files:**
- Modify: `README.md`

- [ ] **Step 3.1: Update environments table**

In `README.md` (around line 185–188), find the environments overview table:

Old:
```
| **Local — Full**         | Developer        | Docker       | Docker                   | `.env.local`  |
```
New:
```
| **Local — Full**         | Developer        | Docker       | Docker                   | *(none)*      |
```

- [ ] **Step 3.2: Update Local — Full Containers section**

Around line 229–258, find the "Local — Full Containers" section. Replace the entire section body:

Old:
```
All five services run in Docker. Uses `.env.local`.

**Best for:** verifying that the full containerized stack works before pushing.

**Prerequisites:** Docker

```bash
docker compose --env-file .env.local up --build
```

| Service   | URL                           |
| --------- | ----------------------------- |
| Frontend  | http://localhost:4200         |
| Backend   | http://localhost:8000         |
| Keycloak  | http://localhost:8080         |

**First-time setup:**

```bash
# Copy the template (only once)
cp .env.example .env.local
# Review .env.local — defaults are safe for local use, no changes required
```

To also start pgadmin at `:5050`:

```bash
docker compose --env-file .env.local -f compose.yaml -f compose.dev.yaml up --build
```
```

New:
```
All five services run in Docker. No env file needed — `compose.yaml` defaults cover local use.

**Best for:** verifying that the full containerized stack works before pushing.

**Prerequisites:** Docker

```bash
docker compose up --build
```

| Service   | URL                           |
| --------- | ----------------------------- |
| Frontend  | http://localhost:4200         |
| Backend   | http://localhost:8000         |
| Keycloak  | http://localhost:8080         |

To also start pgadmin at `:5050`:

```bash
docker compose -f compose.yaml -f compose.dev.yaml up --build
```
```

- [ ] **Step 3.3: Update Appendix command reference**

Around line 442–443, find:
```
# Start with a specific env file
docker compose --env-file .env.local up --build
```
Replace with:
```
# Start with a specific env file (dev/prod environments)
docker compose --env-file .env.dev up --build
```

- [ ] **Step 3.4: Commit**

```bash
git add README.md
git commit -m "docs: remove .env.local convention — compose defaults suffice for local full stack"
```

---

## Task 4: Unify dev passwords to "password"

**Files:**
- Modify: `keycloak/realm-export.json`
- Modify: `README.md`
- Modify: `.claude/CLAUDE.md`

- [ ] **Step 4.1: Update Keycloak realm-export.json**

In `keycloak/realm-export.json`, replace alice's credential value:

Old:
```json
          "value": "alice123",
```
New:
```json
          "value": "password",
```

Then replace bob's credential value (same change):

Old:
```json
          "value": "bob123",
```
New:
```json
          "value": "password",
```

Verify with:
```bash
grep -n "alice123\|bob123" keycloak/realm-export.json
```
Expected: no output (both replaced).

- [ ] **Step 4.2: Update README credentials table**

In `README.md`, around line 39–42, find:
```
| `alice`  | `alice123` | alice@example.com   |
| `bob`    | `bob123`   | bob@example.com     |
```
Replace with:
```
| `alice`  | `password` | alice@example.com   |
| `bob`    | `password` | bob@example.com     |
```

- [ ] **Step 4.3: Update CLAUDE.md test users line**

In `.claude/CLAUDE.md`, around line 89, find:
```
- Keycloak realm `expense-app` is imported automatically on container start from `keycloak/realm-export.json`. Test users: `alice / alice123` and `bob / bob123`.
```
Replace with:
```
- Keycloak realm `expense-app` is imported automatically on container start from `keycloak/realm-export.json`. Test users: `alice / password` and `bob / password`.
```

- [ ] **Step 4.4: Commit**

```bash
git add keycloak/realm-export.json README.md .claude/CLAUDE.md
git commit -m "chore: unify dev user passwords to 'password' for alice and bob"
```

> **Note:** Keycloak imports the realm on first container start. If the `keycloak_db` volume already exists with old credentials, run `docker compose down -v` then `docker compose up` to re-import the realm with the new passwords.
