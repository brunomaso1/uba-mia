# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture

Multi-user expense management app. Services are orchestrated via Docker Compose from `infra/`.

| Component  | Technology       | Port | Role |
|------------|------------------|------|------|
| `frontend` | Angular 22       | 4200 | SPA — delegates auth to Keycloak via PKCE |
| `backend`  | FastAPI 0.136.3  | 8000 | REST API — validates JWT via Keycloak JWKS |
| `keycloak` | Keycloak 26.6.0  | 8080 | Auth server — issues JWT tokens |
| `db`       | PostgreSQL 19    | 5432 | Persistence |

Auth flow: Angular redirects to Keycloak (PKCE login) → Keycloak returns JWT → Angular HTTP interceptor attaches `Authorization: Bearer <token>` to all API requests → FastAPI validates JWT signature locally via JWKS endpoint (no roundtrip per request).

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
pip install -r requirements.txt
uvicorn app.main:app --reload          # local dev with hot reload
pytest                                  # all tests
pytest tests/test_health.py -v         # single file
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
docker compose -f infra/docker-compose.yml exec db \
  psql -U expense_user -d expense_db -f /seeds/01-seed.sql
```

## Key Design Decisions

- `User.keycloak_sub` stores the JWT `sub` claim. Users are auto-created in the DB on first authenticated request to `GET /users/me` — no separate registration flow.
- Keycloak realm `expense-app` is imported automatically on container start from `keycloak/realm-export.json`. Test users: `alice / alice123` and `bob / bob123`.
- DB schema is initialized from `db/init/01-init.sql` on first PostgreSQL container start. Seeds in `db/seeds/` must be applied manually.
- `BACKEND_CORS_ORIGINS` must be a JSON array string in docker-compose env: `'["http://localhost:4200"]'`; pydantic-settings parses it automatically.
- Angular 22 uses Vitest for testing (not Karma). Run `ng test` without `--browsers ChromeHeadless`.
- Frontend Dockerfile uses `node:24-alpine` — Angular 22 requires Node `>=22.22.3`.
