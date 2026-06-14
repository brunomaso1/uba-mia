---
paths: 
  - backend/**/*
---

# Backend Rules — FastAPI 0.136.3

## Stack
- Python 3.12+
- FastAPI 0.136.3
- SQLAlchemy (async)
- Alembic
- PostgreSQL 18.4 (image: `postgres:18.4`)
- uv (package manager)
- Testing: pytest

# Code conventions
- Use snake_case for variables, functions, and file names.
- Use uv for dependency management and scripts. Do not use pip or poetry.

## Project structure
- `app/main.py` — FastAPI app entrypoint, router registration, CORS config.
- `app/models/` — SQLAlchemy ORM models.
- `app/schemas/` — Pydantic request/response schemas.
- `app/routers/` — Route handlers, one file per resource.
- `app/services/` — Business logic and database interactions.
- `app/deps.py` — Shared FastAPI dependencies (DB session, current user).

## Auth
- Validate JWT locally using Keycloak's JWKS endpoint — no per-request roundtrip to Keycloak.
- Validate `iss` against `http://localhost:8080` (not `http://keycloak:8080`).
- `User.keycloak_sub` = JWT `sub` claim. Auto-create the DB user on first `GET /users/me`.

## Database
- Use async SQLAlchemy sessions via the dependency in `app/deps.py`.
- The app database Docker service is named `app_db` (port 5432). Keycloak has its own separate `keycloak_db` (port 5433).
- All schema changes go through Alembic migrations — never modify `db/init/01-init.sql` for schema changes.
- Generate migrations: `alembic revision --autogenerate -m "description"`.
- Apply migrations: `alembic upgrade head`.

## API design
- Return Pydantic schemas, not raw ORM objects.
- Use `HTTPException` with appropriate status codes; never return errors as 200.
- Prefix all routes with `/api/v1/`.

## CORS
- `BACKEND_CORS_ORIGINS` is a JSON array string in the environment. pydantic-settings parses it automatically.
- Dev value: `'["http://localhost:4200"]'`.

## Environment
- `backend/.env` (gitignored) provides local dev overrides — copy from `backend/.env.example`.
- Key vars: `DATABASE_URL`, `TEST_DATABASE_URL` (optional, falls back to `DATABASE_URL`), `API_VERSION`.
- `compose.yaml` injects `DATABASE_URL` directly into the container; `backend/.env` is not used in Docker.
- `DATABASE_URL` defaults in `Settings` match the `compose.yaml` defaults (`admin:password`).

## Testing
- Run `pytest` from the `backend/` directory.
- Use `pytest -v tests/<file>.py` for a single file.
- Integration tests use a real database — requires `app_db` container running (`docker compose up app_db -d`).
- Test DB connection is read from `TEST_DATABASE_URL` env var, falling back to `DATABASE_URL`.
