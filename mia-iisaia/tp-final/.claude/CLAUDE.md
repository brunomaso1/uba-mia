# Project conventions for Claude Code

## Overview

This repository contains a multi-user expense management application built with Angular 22 (frontend), FastAPI 0.136.3 (backend), Keycloak 26.6.0 (authentication), and PostgreSQL 19 (database). The services are orchestrated using Docker Compose for easy local development.

## Architecture

Multi-user expense management app. Services are orchestrated via Docker Compose from `infra/`.

| Component  | Folder    | Technology      | Port | Role                                       |
| ---------- | --------- | --------------- | ---- | ------------------------------------------ |
| `frontend` | /frontend | Angular v22     | 4200 | SPA — delegates auth to Keycloak via PKCE  |
| `backend`  | /backend  | FastAPI 0.136.3 | 8000 | REST API — validates JWT via Keycloak JWKS |
| `keycloak` | /keycloak | Keycloak 26.6.0 | 8080 | Auth server — issues JWT tokens            |
| `db`       | /db       | PostgreSQL 19   | 5432 | Persistence                                |

Auth flow: Angular redirects to Keycloak (PKCE login) → Keycloak returns JWT → Angular HTTP interceptor attaches `Authorization: Bearer <token>` to all API requests → FastAPI validates JWT signature locally via JWKS endpoint (no roundtrip per request).

# Claude code conventions and project structure

- Use `bash` for shell commands, not `sh` or `zsh` or `PowerShell`.
- Don't use `PowerShell` commands on the shell or in documentation.
- Use `docker compose` instead of `docker-compose`.

## Git Conventions
- This project uses only the `mia-iisaia` branch. Do not create new branches or pull requests.
- Do not push to origin directly.
- Commits should be atomic and descriptive of the change.
- Use conventional commit messages (e.g., `feat: add expense form`, `fix: correct JWT validation logic`).

## Development Commands

### Full stack
```bash
docker compose -f infra/docker-compose.yml up --build
```

### Infra only (db + keycloak), developing backend/frontend locally
```bash
docker compose -f infra/docker-compose.yml up db keycloak
```

### Backend
```bash
cd backend
uv sync                                # install all deps (includes dev)
uv run uvicorn app.main:app --reload   # local dev with hot reload
uv run pytest                          # all tests
uv run pytest tests/test_health.py -v  # single file
```

### Frontend
```bash
cd frontend
npm install
ng serve                                # local dev with hot reload
ng test                                 # tests (Angular 22 uses Vitest)
ng build                                # production build
```

### Database migrations (Alembic)
```bash
# Apply all pending migrations
docker compose -f infra/docker-compose.yml exec backend alembic upgrade head

# Generate a new migration from model changes
docker compose -f infra/docker-compose.yml exec backend alembic revision --autogenerate -m "description"
```

### Apply seed data
```bash
docker compose -f infra/docker-compose.yml exec -T db \
  psql -U expense_user -d expense_db < db/seeds/01-seed.sql
```

## Key Design Decisions

- `User.keycloak_sub` stores the JWT `sub` claim. Users are auto-created in the DB on first authenticated request to `GET /users/me` — no separate registration flow.
- Keycloak realm `expense-app` is imported automatically on container start from `keycloak/realm-export.json`. Test users: `alice / alice123` and `bob / bob123`.
- DB schema is initialized from `db/init/01-init.sql` on first PostgreSQL container start. Seeds in `db/seeds/` must be applied manually.
- `BACKEND_CORS_ORIGINS` must be a JSON array string in docker-compose env: `'["http://localhost:4200"]'`; pydantic-settings parses it automatically.
- Angular 22 uses Vitest for testing (not Karma). Run `ng test` without `--browsers ChromeHeadless`.
- Frontend Dockerfile uses `node:24-alpine` — Angular 22 requires Node `>=22.22.3`.
- Keycloak is configured with `KC_HOSTNAME: localhost` for dev. The `iss` claim in JWTs will be `http://localhost:8080/realms/expense-app`. When implementing JWT validation in the backend, validate against `http://localhost:8080` (not `http://keycloak:8080`) to match the issued tokens.
