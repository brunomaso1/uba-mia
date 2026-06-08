# Project Scaffolding Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scaffold the full project so `docker compose up` runs all four services (Angular 22 frontend, FastAPI 0.136.3 backend, Keycloak 26.6.0, PostgreSQL 19) with a working health endpoint, imported Keycloak realm, and initialized DB schema.

**Architecture:** Monorepo with `frontend/`, `backend/`, `keycloak/`, `db/`, `infra/`, `docs/` folders. Docker Compose in `infra/` orchestrates all services. Backend is a minimal FastAPI app (health endpoint only); full CRUD is covered in Plan 2.

**Tech Stack:** Angular 22, FastAPI 0.136.3, Keycloak 26.6.0, PostgreSQL 19, Docker Compose, Python 3.12, Node 22, pydantic-settings 2, pytest

---

## File Map

| Path | Purpose |
|------|---------|
| `.gitignore` | Root gitignore for all components |
| `infra/.env.example` | Environment variable template |
| `infra/docker-compose.yml` | Orchestrates all four services |
| `db/init/01-init.sql` | Full DB schema (user, group, group_member, expense) |
| `db/seeds/01-seed.sql` | Optional local test data |
| `keycloak/realm-export.json` | Realm config with expense-frontend client (PKCE) and two test users |
| `keycloak/Dockerfile` | Keycloak image with realm auto-import |
| `backend/Dockerfile` | Python 3.12 backend image |
| `backend/requirements.txt` | Python dependencies |
| `backend/app/__init__.py` | Package marker |
| `backend/app/main.py` | FastAPI entrypoint + health endpoint |
| `backend/app/core/__init__.py` | Package marker |
| `backend/app/core/config.py` | Settings via pydantic-settings |
| `backend/tests/__init__.py` | Package marker |
| `backend/tests/test_health.py` | Health endpoint test |
| `backend/pytest.ini` | Pytest configuration |
| `frontend/` | Angular 22 project (created by ng new) |
| `frontend/Dockerfile` | Node 22 dev image |
| `CLAUDE.md` | Developer guidance for this repo |

---

## Task 1: Root structure and .gitignore

**Files:**
- Create: `.gitignore`

- [ ] **Step 1: Create root .gitignore**

File: `.gitignore`

```gitignore
# Python
__pycache__/
*.py[cod]
.venv/
venv/
*.egg-info/
.pytest_cache/
.coverage
htmlcov/

# Node / Angular
node_modules/
dist/
.angular/
*.log

# Environment — never commit .env, only .env.example
.env
!.env.example

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Superpowers brainstorm artifacts
.superpowers/
```

- [ ] **Step 2: Create component directories**

```bash
mkdir -p frontend backend keycloak db/init db/seeds infra
```

- [ ] **Step 3: Commit**

```bash
git add .gitignore
git commit -m "chore: initial project structure and gitignore"
```

---

## Task 2: Environment configuration

**Files:**
- Create: `infra/.env.example`

- [ ] **Step 1: Create infra/.env.example**

File: `infra/.env.example`

```env
# PostgreSQL
POSTGRES_DB=expense_db
POSTGRES_USER=expense_user
POSTGRES_PASSWORD=changeme

# Keycloak admin (management console only)
KC_BOOTSTRAP_ADMIN_USERNAME=admin
KC_BOOTSTRAP_ADMIN_PASSWORD=admin

# Backend (these are passed to the backend container)
DATABASE_URL=postgresql://expense_user:changeme@db:5432/expense_db
KEYCLOAK_URL=http://keycloak:8080
KEYCLOAK_REALM=expense-app
KEYCLOAK_CLIENT_ID=expense-frontend
BACKEND_CORS_ORIGINS=["http://localhost:4200"]
```

- [ ] **Step 2: Create active .env from template**

```bash
cp infra/.env.example infra/.env
```

The `.env` file is gitignored. `.env.example` is what gets committed.

- [ ] **Step 3: Commit**

```bash
git add infra/.env.example
git commit -m "chore: add environment variable template"
```

---

## Task 3: Database schema

**Files:**
- Create: `db/init/01-init.sql`
- Create: `db/seeds/01-seed.sql`

- [ ] **Step 1: Write init SQL**

File: `db/init/01-init.sql`

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS "user" (
    id            UUID          PRIMARY KEY DEFAULT uuid_generate_v4(),
    keycloak_sub  TEXT          UNIQUE NOT NULL,
    display_name  TEXT          NOT NULL,
    email         TEXT          UNIQUE NOT NULL,
    created_at    TIMESTAMPTZ   DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS "group" (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        TEXT        NOT NULL,
    created_by  UUID        NOT NULL REFERENCES "user"(id) ON DELETE RESTRICT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS group_member (
    user_id   UUID        NOT NULL REFERENCES "user"(id)  ON DELETE CASCADE,
    group_id  UUID        NOT NULL REFERENCES "group"(id) ON DELETE CASCADE,
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, group_id)
);

CREATE TABLE IF NOT EXISTS expense (
    id          UUID          PRIMARY KEY DEFAULT uuid_generate_v4(),
    group_id    UUID          NOT NULL REFERENCES "group"(id) ON DELETE CASCADE,
    paid_by     UUID          NOT NULL REFERENCES "user"(id) ON DELETE RESTRICT,
    amount      NUMERIC(12,2) NOT NULL CHECK (amount > 0),
    description TEXT,
    date        DATE          NOT NULL,
    created_at  TIMESTAMPTZ   DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_expense_group_id       ON expense(group_id);
CREATE INDEX IF NOT EXISTS idx_expense_paid_by        ON expense(paid_by);
CREATE INDEX IF NOT EXISTS idx_group_member_user_id   ON group_member(user_id);
CREATE INDEX IF NOT EXISTS idx_group_member_group_id  ON group_member(group_id);
```

- [ ] **Step 2: Write seed data**

File: `db/seeds/01-seed.sql`

```sql
-- Seeds use fake keycloak_sub values for local testing.
-- Real users are auto-created by the backend on first login (sub from JWT).
-- Apply manually: docker compose exec db psql -U expense_user -d expense_db -f /seeds/01-seed.sql

INSERT INTO "user" (keycloak_sub, display_name, email) VALUES
    ('test-sub-alice', 'Alice Test', 'alice@example.com'),
    ('test-sub-bob',   'Bob Test',   'bob@example.com')
ON CONFLICT DO NOTHING;

INSERT INTO "group" (name, created_by) VALUES
    ('Familia', (SELECT id FROM "user" WHERE keycloak_sub = 'test-sub-alice'))
ON CONFLICT DO NOTHING;

INSERT INTO group_member (user_id, group_id)
SELECT u.id, g.id
FROM "user" u, "group" g
WHERE u.keycloak_sub IN ('test-sub-alice', 'test-sub-bob')
  AND g.name = 'Familia'
ON CONFLICT DO NOTHING;
```

- [ ] **Step 3: Commit**

```bash
git add db/
git commit -m "feat: add database schema and seed scripts"
```

---

## Task 4: Keycloak configuration

**Files:**
- Create: `keycloak/realm-export.json`
- Create: `keycloak/Dockerfile`

- [ ] **Step 1: Write realm-export.json**

File: `keycloak/realm-export.json`

```json
{
  "realm": "expense-app",
  "displayName": "Expense App",
  "enabled": true,
  "sslRequired": "none",
  "registrationAllowed": true,
  "loginWithEmailAllowed": true,
  "duplicateEmailsAllowed": false,
  "verifyEmail": false,
  "accessTokenLifespan": 300,
  "clients": [
    {
      "clientId": "expense-frontend",
      "name": "Expense Frontend",
      "enabled": true,
      "publicClient": true,
      "standardFlowEnabled": true,
      "implicitFlowEnabled": false,
      "directAccessGrantsEnabled": false,
      "serviceAccountsEnabled": false,
      "frontchannelLogout": true,
      "protocol": "openid-connect",
      "redirectUris": [
        "http://localhost:4200/*"
      ],
      "webOrigins": [
        "http://localhost:4200"
      ],
      "attributes": {
        "pkce.code.challenge.method": "S256",
        "post.logout.redirect.uris": "http://localhost:4200/*"
      }
    }
  ],
  "users": [
    {
      "username": "alice",
      "enabled": true,
      "email": "alice@example.com",
      "firstName": "Alice",
      "lastName": "Test",
      "emailVerified": true,
      "credentials": [
        {
          "type": "password",
          "value": "alice123",
          "temporary": false
        }
      ]
    },
    {
      "username": "bob",
      "enabled": true,
      "email": "bob@example.com",
      "firstName": "Bob",
      "lastName": "Test",
      "emailVerified": true,
      "credentials": [
        {
          "type": "password",
          "value": "bob123",
          "temporary": false
        }
      ]
    }
  ]
}
```

- [ ] **Step 2: Write Keycloak Dockerfile**

File: `keycloak/Dockerfile`

```dockerfile
FROM quay.io/keycloak/keycloak:26.6.0

COPY realm-export.json /opt/keycloak/data/import/realm-export.json

ENTRYPOINT ["/opt/keycloak/bin/kc.sh"]
CMD ["start-dev", "--import-realm"]
```

- [ ] **Step 3: Commit**

```bash
git add keycloak/
git commit -m "feat: add Keycloak realm config and Dockerfile"
```

---

## Task 5: Backend skeleton

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/pytest.ini`
- Create: `backend/app/__init__.py`
- Create: `backend/app/core/__init__.py`
- Create: `backend/app/core/config.py`
- Create: `backend/app/main.py`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/test_health.py`
- Create: `backend/Dockerfile`

- [ ] **Step 1: Write failing test**

File: `backend/tests/__init__.py` — empty file.

File: `backend/tests/test_health.py`

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 2: Run test — verify it fails**

```bash
cd backend
pip install fastapi pytest httpx
pytest tests/test_health.py -v
```

Expected output:
```
FAILED tests/test_health.py::test_health_returns_ok — ModuleNotFoundError: No module named 'app'
```

- [ ] **Step 3: Write requirements.txt**

File: `backend/requirements.txt`

```
fastapi==0.136.3
uvicorn[standard]==0.32.0
sqlalchemy==2.0.36
alembic==1.14.0
psycopg2-binary==2.9.10
python-jose[cryptography]==3.3.0
pydantic-settings==2.6.1
httpx==0.28.0
pytest==8.3.3
pytest-asyncio==0.24.0
```

```bash
pip install -r requirements.txt
```

- [ ] **Step 4: Write config and app**

File: `backend/app/__init__.py` — empty file.

File: `backend/app/core/__init__.py` — empty file.

File: `backend/app/core/config.py`

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://expense_user:changeme@localhost:5432/expense_db"
    keycloak_url: str = "http://localhost:8080"
    keycloak_realm: str = "expense-app"
    keycloak_client_id: str = "expense-frontend"
    backend_cors_origins: list[str] = ["http://localhost:4200"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
```

File: `backend/app/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

app = FastAPI(title="Expense API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok"}
```

File: `backend/pytest.ini`

```ini
[pytest]
testpaths = tests
asyncio_mode = auto
```

- [ ] **Step 5: Run test — verify it passes**

```bash
pytest tests/test_health.py -v
```

Expected output:
```
tests/test_health.py::test_health_returns_ok PASSED
1 passed in 0.XXs
```

- [ ] **Step 6: Write Dockerfile**

File: `backend/Dockerfile`

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

- [ ] **Step 7: Commit**

```bash
git add backend/
git commit -m "feat: add backend skeleton with health endpoint and tests"
```

---

## Task 6: Frontend skeleton

**Files:**
- Create: `frontend/` (via ng new)
- Create: `frontend/Dockerfile`

- [ ] **Step 1: Scaffold Angular 22 app**

```bash
cd frontend
npx -y @angular/cli@22 new expense-app --directory . --routing --style scss --ssr false
```

Expected: Angular 22 project created in `frontend/` with standalone components, SCSS, and routing enabled.

- [ ] **Step 2: Verify dev server starts**

```bash
ng serve
```

Open `http://localhost:4200` — expect the default Angular welcome page.
Stop with Ctrl+C.

- [ ] **Step 3: Run default tests**

```bash
ng test --watch=false --browsers ChromeHeadless
```

Expected: all generated default tests pass.

- [ ] **Step 4: Write frontend Dockerfile**

File: `frontend/Dockerfile`

```dockerfile
FROM node:22-alpine
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
EXPOSE 4200
CMD ["npx", "ng", "serve", "--host", "0.0.0.0", "--port", "4200", "--poll", "2000"]
```

- [ ] **Step 5: Commit**

```bash
git add frontend/
git commit -m "feat: scaffold Angular 22 frontend"
```

---

## Task 7: Docker Compose

**Files:**
- Create: `infra/docker-compose.yml`

- [ ] **Step 1: Write docker-compose.yml**

File: `infra/docker-compose.yml`

```yaml
services:
  db:
    image: postgres:19
    restart: unless-stopped
    env_file: .env
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ../db/init:/docker-entrypoint-initdb.d
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 5s
      timeout: 5s
      retries: 10

  keycloak:
    build: ../keycloak
    restart: unless-stopped
    env_file: .env
    environment:
      KC_BOOTSTRAP_ADMIN_USERNAME: ${KC_BOOTSTRAP_ADMIN_USERNAME}
      KC_BOOTSTRAP_ADMIN_PASSWORD: ${KC_BOOTSTRAP_ADMIN_PASSWORD}
      KC_DB: postgres
      KC_DB_URL: jdbc:postgresql://db:5432/${POSTGRES_DB}
      KC_DB_USERNAME: ${POSTGRES_USER}
      KC_DB_PASSWORD: ${POSTGRES_PASSWORD}
      KC_HOSTNAME: localhost
      KC_HTTP_ENABLED: "true"
      KC_HOSTNAME_STRICT: "false"
    ports:
      - "8080:8080"
    depends_on:
      db:
        condition: service_healthy

  backend:
    build: ../backend
    restart: unless-stopped
    env_file: .env
    environment:
      DATABASE_URL: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
      KEYCLOAK_URL: http://keycloak:8080
      KEYCLOAK_REALM: expense-app
      KEYCLOAK_CLIENT_ID: expense-frontend
      BACKEND_CORS_ORIGINS: '["http://localhost:4200"]'
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - ../backend:/app

  frontend:
    build: ../frontend
    restart: unless-stopped
    ports:
      - "4200:4200"
    depends_on:
      - backend
    volumes:
      - ../frontend:/app
      - /app/node_modules

volumes:
  postgres_data:
```

- [ ] **Step 2: Validate compose syntax**

```bash
cd infra
docker compose config
```

Expected: full expanded YAML with no errors.

- [ ] **Step 3: Build and start the stack**

```bash
docker compose up --build -d
```

Wait ~90 seconds for Keycloak to initialize on first run.

- [ ] **Step 4: Verify all services are healthy**

```bash
# Backend health check
curl http://localhost:8000/health
# Expected: {"status":"ok"}

# Keycloak realm discovery document
curl http://localhost:8080/realms/expense-app/.well-known/openid-configuration
# Expected: JSON with "issuer", "authorization_endpoint", "jwks_uri", etc.

# PostgreSQL tables
docker compose exec db psql -U expense_user -d expense_db -c "\dt"
# Expected: lists user, group, group_member, expense tables
```

- [ ] **Step 5: Stop the stack**

```bash
docker compose down
```

- [ ] **Step 6: Commit**

```bash
git add infra/docker-compose.yml
git commit -m "feat: add Docker Compose for full stack orchestration"
```

---

## Task 8: CLAUDE.md

**Files:**
- Create: `CLAUDE.md`

- [ ] **Step 1: Write CLAUDE.md**

File: `CLAUDE.md`

```markdown
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
ng test --watch=false --browsers ChromeHeadless   # headless tests
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
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add CLAUDE.md with architecture and development commands"
```

---

## Verification

After all tasks are complete:

```bash
cd infra
docker compose up --build -d

# Wait ~90s, then:
curl http://localhost:8000/health
# → {"status":"ok"}

curl http://localhost:8080/realms/expense-app/.well-known/openid-configuration | python -m json.tool | grep issuer
# → "issuer": "http://localhost:8080/realms/expense-app"

docker compose exec db psql -U expense_user -d expense_db -c "\dt"
# → user, group, group_member, expense

# Open http://localhost:4200 — Angular welcome page
# Open http://localhost:8080 — Keycloak admin console (admin/admin)
```
