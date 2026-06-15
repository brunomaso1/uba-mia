# Project conventions for Claude Code

## Overview

This repository contains a multi-user expense management application built with Angular 22 (frontend), FastAPI 0.136.3 (backend), Keycloak 26.6.3 (authentication), and PostgreSQL 18.4 (database). The services are orchestrated using Docker Compose for easy local development.

## Architecture

Multi-user expense management app. Services are orchestrated via Docker Compose (`compose.yaml` at the project root).

| Component     | Folder    | Technology      | Port | Role                                       |
| ------------- | --------- | --------------- | ---- | ------------------------------------------ |
| `frontend`    | /frontend | Angular v22     | 4200 | SPA — delegates auth to Keycloak via PKCE  |
| `backend`     | /backend  | FastAPI 0.136.3 | 8000 | REST API — validates JWT via Keycloak JWKS |
| `keycloak`    | /keycloak | Keycloak 26.6.3 | 8080 | Auth server — issues JWT tokens            |
| `app_db`      | /db       | PostgreSQL 18.4 | 5432 | App persistence                            |
| `keycloak_db` | —         | PostgreSQL 18.4 | 5433 | Keycloak persistence (separate instance)   |

Auth flow: Angular redirects to Keycloak (PKCE login) → Keycloak returns JWT → Angular HTTP interceptor attaches `Authorization: Bearer <token>` to all API requests → FastAPI validates JWT signature locally via JWKS endpoint (no roundtrip per request).

# Claude code conventions and project structure

- Use `bash` for shell commands, not `sh` or `zsh` or `PowerShell`.
- Don't use `PowerShell` commands on the shell or in documentation.
- Use `docker compose` instead of `docker-compose`.

## Git Conventions
- This project uses only the `mia-iisaia` branch. Do not create new branches or pull requests.
- The folder of the project is `tp-final/` — all commits should be made to files within this folder. But this folder is not the root of the repository, so be careful with paths in commit messages and commands.
- Do not push to origin directly.
- Commits should be atomic and descriptive of the change.
- Use conventional commit messages (e.g., `feat: add expense form`, `fix: correct JWT validation logic`).
- Git's single `pre-commit` hook lives in `frontend/.husky/pre-commit` and runs two things in sequence: backend `ruff` lint+format (via `uv run pre-commit`) and frontend `lint-staged` (via `npx`). It fires on every commit regardless of which files were changed.

## Development Commands

### Full stack
```bash
docker compose up --build
```

### Infra only (app_db + keycloak_db + keycloak), developing backend/frontend locally
```bash
docker compose up app_db keycloak_db keycloak
```

### Dev extras (pgadmin at port 5050)
```bash
docker compose -f compose.yaml -f compose.dev.yaml up
```

### Backend
```bash
cd backend
cp .env.example .env                   # first time only — adjust credentials if needed
uv sync                                # install all deps (includes dev)
uv run fastapi dev                     # local dev with hot reload
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
docker compose exec backend alembic upgrade head

# Generate a new migration from model changes
docker compose exec backend alembic revision --autogenerate -m "description"
```

### Apply seed data
```bash
docker compose exec -T db \
  psql -U expense_user -d expense_db < db/seeds/01-seed.sql
```

## Key Design Decisions

- `User.keycloak_sub` stores the JWT `sub` claim. Users are auto-created in the DB on first authenticated request to `GET /users/me` — no separate registration flow.
- Keycloak realm `expense-app` is imported automatically on container start from `keycloak/realm-export.json`. Test users: `alice / password` and `bob / password`.
- DB schema is initialized from `db/init/01-init.sql` on first PostgreSQL container start (`app_db` service). Seeds in `db/seeds/` must be applied manually.
- Keycloak uses its own dedicated PostgreSQL instance (`keycloak_db`, port 5433) separate from the app database (`app_db`, port 5432).
- Image versions are parameterized via environment variables. Copy `.env.example` to `.env` to configure; key vars: `POSTGRES_VERSION`, `KEYCLOAK_VERSION`, `PYTHON_VERSION`, `UV_VERSION`, `NODE_VERSION`. No `env_file` directives in compose — variables are injected via shell environment or `.env` file at the project root.
- The backend has its own `backend/.env` (gitignored) for local development outside Docker. Copy `backend/.env.example` to `backend/.env` and adjust credentials to match your root `.env`. When running inside Docker, `compose.yaml` injects `DATABASE_URL` directly and `backend/.env` is not used.
- `compose.dev.yaml` extends the base compose with dev-only tooling. Currently adds pgadmin4 at port 5050 (admin@example.com / password), with access to both `app_db` and `keycloak_db`.
- `BACKEND_CORS_ORIGINS` must be a JSON array string in docker-compose env: `'["http://localhost:4200"]'`; pydantic-settings parses it automatically.
- Angular 22 uses Vitest for testing (not Karma). Run `ng test` without `--browsers ChromeHeadless`.
- Frontend Dockerfile uses `node:24-alpine` — Angular 22 requires Node `>=22.22.3`.
- Keycloak is configured with `KC_HOSTNAME: localhost` for dev. The `iss` claim in JWTs will be `http://localhost:8080/realms/expense-app`. When implementing JWT validation in the backend, validate against `http://localhost:8080` (not `http://keycloak:8080`) to match the issued tokens.
- Database tables should use plural names (e.g., `users`, `expenses`) for consistency. SQL files in `db/init/` should create tables with plural names.
