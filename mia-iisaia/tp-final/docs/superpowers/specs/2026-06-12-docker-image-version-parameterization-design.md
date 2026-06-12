# Docker Image Version Parameterization — Design Spec

**Date:** 2026-06-12  
**Status:** Approved

## Overview

Parametrize all Docker image version tags via `.env` so they can be controlled from a single place and passed to `docker compose` with `--env-file`. Additionally, add a `db/Dockerfile` for the PostgreSQL service to make it consistent with the other services (keycloak, backend, frontend).

## Goals

- All image version tags live in `.env` / `.env.example` as explicit variables.
- `docker compose --env-file .env up --build` is the canonical dev command.
- Remove `env_file:` directives from all services in `compose.yaml` — runtime env vars come only from explicit `environment:` entries.
- Dockerfiles remain buildable standalone (defaults baked into `ARG`).

## Out of Scope

- Parameterizing full image names (only the version tag).
- Any changes to runtime environment variables or service configuration beyond what's described here.

---

## 1. Variables — `.env` and `.env.example`

Add a new `# Image versions` section to both files:

```dotenv
# Image versions
POSTGRES_VERSION=19
KEYCLOAK_VERSION=26.6.0
PYTHON_VERSION=3.12-slim
UV_VERSION=latest
NODE_VERSION=24-alpine
```

`.env` is not committed. `.env.example` documents all expected variables and is committed.

---

## 2. Dockerfiles

### New: `db/Dockerfile`

```dockerfile
ARG POSTGRES_VERSION=19
FROM postgres:${POSTGRES_VERSION}
```

Minimal by design — the db service uses the official image as-is. The Dockerfile exists to make version control consistent with the other services and to enable `build.args` wiring in compose.

### `keycloak/Dockerfile`

Add `ARG` before `FROM`:

```dockerfile
ARG KEYCLOAK_VERSION=26.6.0
FROM quay.io/keycloak/keycloak:${KEYCLOAK_VERSION}

COPY realm-export.json /opt/keycloak/data/import/realm-export.json

CMD ["start-dev", "--import-realm"]
```

### `backend/Dockerfile`

Add two `ARG` declarations — one for the base image, one for the `uv` copy source:

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

### `frontend/Dockerfile`

Add `ARG` before `FROM`:

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

---

## 3. `compose.yaml`

### Key changes per service

| Service | Change |
|---|---|
| `db` | Replace `image: postgres:19` with `build: context: ./db` + `args`; remove `env_file:` |
| `keycloak` | Add `args:` to existing `build:`; remove `env_file:` |
| `backend` | Add `args:` (two vars) to existing `build:`; remove `env_file:` |
| `frontend` | Add `args:` to existing `build:` |

### `build.args` syntax

All `args` use `${VAR:-default}` fallback syntax so compose works even without `--env-file`:

```yaml
# db
build:
  context: ./db
  args:
    POSTGRES_VERSION: ${POSTGRES_VERSION:-19}

# keycloak
build:
  context: ./keycloak
  args:
    KEYCLOAK_VERSION: ${KEYCLOAK_VERSION:-26.6.0}

# backend
build:
  context: ./backend
  args:
    PYTHON_VERSION: ${PYTHON_VERSION:-3.12-slim}
    UV_VERSION: ${UV_VERSION:-latest}

# frontend
build:
  context: ./frontend
  args:
    NODE_VERSION: ${NODE_VERSION:-24-alpine}
```

### `env_file:` removal

`env_file: .env` is removed from `db`, `keycloak`, and `backend`. Runtime variables already reach containers via explicit `environment:` entries — no behavioral change.

---

## 4. Usage

```bash
# Standard dev workflow
docker compose --env-file .env up --build

# Override a specific version at runtime
KEYCLOAK_VERSION=26.7.0 docker compose --env-file .env up --build keycloak

# Use an alternate env file (e.g. staging)
docker compose --env-file .env.staging up --build
```

---

## 5. File Changeset Summary

| File | Action |
|---|---|
| `.env` | Add 5 version variables |
| `.env.example` | Add 5 version variables |
| `db/Dockerfile` | Create (new) |
| `keycloak/Dockerfile` | Add `ARG KEYCLOAK_VERSION` |
| `backend/Dockerfile` | Add `ARG PYTHON_VERSION` and `ARG UV_VERSION` |
| `frontend/Dockerfile` | Add `ARG NODE_VERSION` |
| `compose.yaml` | Remove `env_file:` from 3 services; add `build.args` to all 4; migrate `db` from `image:` to `build:` |
