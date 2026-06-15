# Design: API version parametrization, env file cleanup, dev passwords unification

**Date:** 2026-06-15
**Branch:** mia-iisaia

---

## Scope

Three independent improvements to developer experience and configurability:

1. Parametrize the API version in the frontend runtime config (currently hardcoded as `/api/v1`).
2. Remove the `.env.local` convention for "Local — Full Containers" — no env file needed, compose defaults suffice.
3. Unify Alice and Bob's Keycloak dev passwords to `password`.

---

## Task 1 — Parametrize API version in frontend

### Problem

`app.ts` hardcodes the API path prefix:
```ts
`${this.apiUrl()}/api/v1/users/me`
```
The backend already exposes `api_version` as a configurable env var (`API_VERSION`, default `v1`). The frontend has no equivalent — adding or changing the version requires a code change.

### Design

`apiUrl` absorbs the versioned prefix. Its value becomes `http://localhost:8000/api/v1` instead of `http://localhost:8000`. The template builds it by combining two env vars:

```json
// config.template.json
{ "apiUrl": "${API_URL}/api/${API_VERSION}" }
```

```json
// config.json (local hybrid default, used by ng serve)
{ "apiUrl": "http://localhost:8000/api/v1" }
```

`entrypoint.sh` already detects placeholders dynamically, so `${API_VERSION}` is picked up automatically — no whitelist change needed.

`secureRoutes: [cfg.apiUrl]` in `app.config.ts` remains correct: the OIDC interceptor attaches the Bearer token to all requests whose URL starts with `http://localhost:8000/api/v1`, which covers every versioned API endpoint.

### Files changed

| File | Change |
|------|--------|
| `frontend/public/config.template.json` | `"apiUrl": "${API_URL}/api/${API_VERSION}"` |
| `frontend/public/config.json` | `"apiUrl": "http://localhost:8000/api/v1"` |
| `frontend/src/app/app.ts` | Remove `/api/v1` from the URL path |
| `compose.yaml` | Add `API_VERSION: ${API_VERSION:-v1}` to frontend service environment |
| `.env.example` | Add `API_VERSION=v1` |
| `README.md` | Mention `API_VERSION` in Runtime Configuration section |
| `.claude/rules/frontend-rules.md` | Update runtime config section to include `API_VERSION` in compose.yaml step |

**Not changed:** `config.service.ts` (signal `apiUrl` already exists), `app.config.ts` (no change needed), `config.service.spec.ts` (test passes through whatever value is configured).

---

## Task 2 — Remove `.env.local` convention

### Problem

The README describes a "Local — Full Containers" environment that requires:
```bash
cp .env.example .env.local
docker compose --env-file .env.local up --build
```
This is unnecessary. `compose.yaml` already provides inline defaults for every variable (`${VAR:-default}`), so the stack starts correctly with plain `docker compose up --build` and no env file at all.

### Design

Remove the `.env.local` convention entirely. "Local — Full Containers" becomes:
```bash
docker compose up --build
```
No setup step. No env file. Compose defaults handle everything.

`.env.dev` and `.env.prod` keep their `--env-file` flags since they require environment-specific overrides.

### Files changed

| File | Change |
|------|--------|
| `README.md` | Environments table: "Local — Full" env file column → `*(none)*`. Remove "First-time setup" subsection. Remove `--env-file .env.local` from all commands. |

---

## Task 3 — Unify dev passwords to "password"

### Problem

Alice has password `alice123` and Bob has `bob123`. Having different passwords adds unnecessary cognitive load when testing.

### Design

Change both Keycloak test user passwords to `password`. Update all documentation that references the old values.

### Files changed

| File | Change |
|------|--------|
| `keycloak/realm-export.json` | `alice123` → `password`, `bob123` → `password` |
| `README.md` | Credentials table: update both passwords |
| `CLAUDE.md` | Update test user line |

---

## Out of scope

- No changes to `config.service.spec.ts` tests (values are pass-through; semantics of the URL is irrelevant to the test).
- No changes to backend `api_version` handling (already correct).
- No new `.env` files created or documented.
