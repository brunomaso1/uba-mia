---
description: FastAPI backend conventions and best practices
globs: backend/**
---

# Backend Rules — FastAPI 0.136.3

## Stack
- Python
- FastAPI 0.136.3
- SQLAlchemy (async)
- Alembic
- PostgreSQL 19
- Testing: pytest

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

## Testing
- Run `pytest` from the `backend/` directory.
- Use `pytest -v tests/<file>.py` for a single file.
- Integration tests should use a real test database, not mocked sessions.
