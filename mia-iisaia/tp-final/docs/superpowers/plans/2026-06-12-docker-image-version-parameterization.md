# Docker Image Version Parameterization — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Parametrize all Docker image version tags via `.env` passed with `--env-file`, and add a `db/Dockerfile` for the PostgreSQL service.

**Architecture:** Each Dockerfile declares `ARG` with a hardcoded default for its base image version. `compose.yaml` wires `.env` values into those args via `build.args`, using `${VAR:-default}` fallback syntax. The `env_file:` directive is removed from all services — runtime vars come exclusively from explicit `environment:` entries.

**Tech Stack:** Docker Compose, Docker `ARG`/`FROM` syntax, `.env` variable substitution.

---

## File Changeset

| File | Action |
|---|---|
| `.env` | Modify — add 5 version variables |
| `.env.example` | Modify — add 5 version variables |
| `db/Dockerfile` | Create |
| `keycloak/Dockerfile` | Modify — add `ARG KEYCLOAK_VERSION` |
| `backend/Dockerfile` | Modify — add `ARG PYTHON_VERSION` and `ARG UV_VERSION` |
| `frontend/Dockerfile` | Modify — add `ARG NODE_VERSION` |
| `compose.yaml` | Modify — remove `env_file:`, add `build.args`, migrate `db` from `image:` to `build:` |

---

## Task 1: Add version variables to env files

**Files:**
- Modify: `.env`
- Modify: `.env.example`

- [ ] **Step 1: Add version variables to `.env`**

Append this block after the existing content of `.env`:

```dotenv
# Image versions
POSTGRES_VERSION=19
KEYCLOAK_VERSION=26.6.0
PYTHON_VERSION=3.12-slim
UV_VERSION=latest
NODE_VERSION=24-alpine
```

The full `.env` after the edit:

```dotenv
# PostgreSQL
POSTGRES_DB=expense_db
POSTGRES_USER=expense_user
POSTGRES_PASSWORD=changeme

# Keycloak admin credentials (for Keycloak management UI)
KC_BOOTSTRAP_ADMIN_USERNAME=admin
KC_BOOTSTRAP_ADMIN_PASSWORD=admin

# Backend
DATABASE_URL=postgresql://expense_user:changeme@db:5432/expense_db
KEYCLOAK_URL=http://keycloak:8080
KEYCLOAK_REALM=expense-app
KEYCLOAK_CLIENT_ID=expense-frontend
BACKEND_CORS_ORIGINS=["http://localhost:4200"]

# Image versions
POSTGRES_VERSION=19
KEYCLOAK_VERSION=26.6.0
PYTHON_VERSION=3.12-slim
UV_VERSION=latest
NODE_VERSION=24-alpine
```

- [ ] **Step 2: Add version variables to `.env.example`**

Append the same block to `.env.example`:

```dotenv
# PostgreSQL
POSTGRES_DB=expense_db
POSTGRES_USER=expense_user
POSTGRES_PASSWORD=changeme

# Keycloak admin credentials (for Keycloak management UI)
KC_BOOTSTRAP_ADMIN_USERNAME=admin
KC_BOOTSTRAP_ADMIN_PASSWORD=admin

# Backend
KEYCLOAK_URL=http://keycloak:8080
KEYCLOAK_REALM=expense-app
KEYCLOAK_CLIENT_ID=expense-frontend
BACKEND_CORS_ORIGINS=["http://localhost:4200"]

# Image versions
POSTGRES_VERSION=19
KEYCLOAK_VERSION=26.6.0
PYTHON_VERSION=3.12-slim
UV_VERSION=latest
NODE_VERSION=24-alpine
```

- [ ] **Step 3: Commit**

```bash
git add tp-final/.env tp-final/.env.example
git commit -m "chore: add image version variables to env files"
```

---

## Task 2: Create `db/Dockerfile`

**Files:**
- Create: `db/Dockerfile`

- [ ] **Step 1: Create `db/Dockerfile`**

```dockerfile
ARG POSTGRES_VERSION=19
FROM postgres:${POSTGRES_VERSION}
```

- [ ] **Step 2: Verify the file builds standalone**

```bash
cd tp-final
docker build --build-arg POSTGRES_VERSION=19 -t test-db ./db
```

Expected: build completes, final line similar to `Successfully built <id>` or `=> exporting to image`.

- [ ] **Step 3: Clean up test image**

```bash
docker rmi test-db
```

- [ ] **Step 4: Commit**

```bash
git add tp-final/db/Dockerfile
git commit -m "chore(db): add dockerfile with parameterized postgres version"
```

---

## Task 3: Update `keycloak/Dockerfile`

**Files:**
- Modify: `keycloak/Dockerfile`

- [ ] **Step 1: Replace contents of `keycloak/Dockerfile`**

```dockerfile
ARG KEYCLOAK_VERSION=26.6.0
FROM quay.io/keycloak/keycloak:${KEYCLOAK_VERSION}

COPY realm-export.json /opt/keycloak/data/import/realm-export.json

CMD ["start-dev", "--import-realm"]
```

- [ ] **Step 2: Verify standalone build**

```bash
cd tp-final
docker build --build-arg KEYCLOAK_VERSION=26.6.0 -t test-keycloak ./keycloak
```

Expected: build completes successfully.

- [ ] **Step 3: Clean up**

```bash
docker rmi test-keycloak
```

- [ ] **Step 4: Commit**

```bash
git add tp-final/keycloak/Dockerfile
git commit -m "chore(keycloak): parameterize base image version via ARG"
```

---

## Task 4: Update `backend/Dockerfile`

**Files:**
- Modify: `backend/Dockerfile`

- [ ] **Step 1: Replace contents of `backend/Dockerfile`**

```dockerfile
ARG PYTHON_VERSION=3.12-slim
FROM python:${PYTHON_VERSION}

ARG UV_VERSION=latest
COPY --from=ghcr.io/astral-sh/uv:${UV_VERSION} /uv /uvx /bin/

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY . /app

WORKDIR /app
RUN uv sync --frozen --no-cache --no-dev

EXPOSE 8000
CMD ["/app/.venv/bin/fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: Verify standalone build**

```bash
cd tp-final
docker build --build-arg PYTHON_VERSION=3.12-slim --build-arg UV_VERSION=latest -t test-backend ./backend
```

Expected: build completes successfully.

- [ ] **Step 3: Clean up**

```bash
docker rmi test-backend
```

- [ ] **Step 4: Commit**

```bash
git add tp-final/backend/Dockerfile
git commit -m "chore(backend): parameterize python and uv image versions via ARG"
```

---

## Task 5: Update `frontend/Dockerfile`

**Files:**
- Modify: `frontend/Dockerfile`

- [ ] **Step 1: Replace contents of `frontend/Dockerfile`**

```dockerfile
ARG NODE_VERSION=24-alpine
FROM node:${NODE_VERSION}
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
EXPOSE 4200
CMD ["npx", "ng", "serve", "--host", "0.0.0.0", "--port", "4200", "--poll", "2000"]
```

- [ ] **Step 2: Verify standalone build**

```bash
cd tp-final
docker build --build-arg NODE_VERSION=24-alpine -t test-frontend ./frontend
```

Expected: build completes successfully (this one takes a few minutes due to `npm ci`).

- [ ] **Step 3: Clean up**

```bash
docker rmi test-frontend
```

- [ ] **Step 4: Commit**

```bash
git add tp-final/frontend/Dockerfile
git commit -m "chore(frontend): parameterize node image version via ARG"
```

---

## Task 6: Update `compose.yaml`

**Files:**
- Modify: `compose.yaml`

This task migrates `db` from `image:` to `build:`, adds `build.args` to all services, and removes `env_file:` from the three services that had it.

- [ ] **Step 1: Replace `compose.yaml` with the updated version**

```yaml
name: expense-app

services:
  db:
    build:
      context: ./db
      args:
        POSTGRES_VERSION: ${POSTGRES_VERSION:-19}
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./db/init:/docker-entrypoint-initdb.d
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 5s
      timeout: 5s
      retries: 10

  keycloak:
    build:
      context: ./keycloak
      args:
        KEYCLOAK_VERSION: ${KEYCLOAK_VERSION:-26.6.0}
    restart: unless-stopped
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
    build:
      context: ./backend
      args:
        PYTHON_VERSION: ${PYTHON_VERSION:-3.12-slim}
        UV_VERSION: ${UV_VERSION:-latest}
    restart: unless-stopped
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
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
      interval: 5s
      timeout: 3s
      retries: 10
      start_period: 10s
    volumes:
      - ./backend:/app

  frontend:
    build:
      context: ./frontend
      args:
        NODE_VERSION: ${NODE_VERSION:-24-alpine}
    restart: unless-stopped
    ports:
      - "4200:4200"
    depends_on:
      backend:
        condition: service_healthy
    volumes:
      - ./frontend:/app
      - /app/node_modules

volumes:
  postgres_data:
```

- [ ] **Step 2: Verify compose config parses correctly**

```bash
cd tp-final
docker compose --env-file .env config
```

Expected: Docker Compose prints the resolved (interpolated) config with no errors. Check that `POSTGRES_VERSION`, `KEYCLOAK_VERSION`, `PYTHON_VERSION`, `UV_VERSION`, and `NODE_VERSION` appear with their values from `.env`.

- [ ] **Step 3: Commit**

```bash
git add tp-final/compose.yaml
git commit -m "chore: remove env_file directives and add build.args for image versions"
```

---

## Task 7: Full stack verification

No files modified. This task validates the entire changeset works end-to-end.

- [ ] **Step 1: Build all images via compose**

```bash
cd tp-final
docker compose --env-file .env build
```

Expected: all 4 images build successfully with no errors.

- [ ] **Step 2: Bring up the full stack**

```bash
docker compose --env-file .env up -d
```

Expected: all containers start. Check with:

```bash
docker compose --env-file .env ps
```

Expected output: all 4 services in `running` state, `db` and `backend` show `healthy`.

- [ ] **Step 3: Verify backend health endpoint**

```bash
curl http://localhost:8000/health
```

Expected: `{"status":"ok"}` or similar 200 response.

- [ ] **Step 4: Tear down**

```bash
docker compose --env-file .env down
```

- [ ] **Step 5: Verify fallback defaults work (no --env-file)**

```bash
docker compose config
```

Expected: compose resolves config using `:-` fallback defaults (e.g. `POSTGRES_VERSION` resolves to `19`) with no "variable is not set" warnings.
