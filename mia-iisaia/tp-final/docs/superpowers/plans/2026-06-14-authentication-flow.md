# Authentication Flow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement end-to-end Keycloak authentication: Angular logs in via OIDC/PKCE and attaches a bearer token; FastAPI validates the JWT with `fastapi-keycloak-middleware` and exposes a protected `GET /api/v1/users/me` that auto-creates the DB user.

**Architecture:** Frontend loads OIDC config at runtime from `/config.json` via `StsConfigHttpLoader`, uses `authInterceptor()` to attach the token to backend calls, and checks auth on bootstrap with `withAppInitializerAuthCheck()`. Backend adds the Keycloak middleware *before* CORS (so CORS stays outermost), keeps `user_mapper` minimal (returns claims), and does get-or-create inside a `get_current_user` dependency. In-process tests mock the middleware via conftest and override the `get_user` dependency; a separate E2E test exercises the real middleware against the running Docker stack with a real token.

**Tech Stack:** Angular 22 + `angular-auth-oidc-client@21.0.2`, FastAPI 0.136.3 + `fastapi-keycloak-middleware@1.6.0`, Keycloak 26.6.3, PostgreSQL 18.4, pytest, Vitest.

**Reference spec:** `docs/superpowers/specs/2026-06-14-authentication-flow-design.md`

---

## File Structure

**Backend**
- Modify: `backend/pyproject.toml` — add `fastapi-keycloak-middleware==1.6.0`.
- Create: `backend/app/schemas/user.py` — `UserRead` response schema.
- Create: `backend/app/services/user.py` — `get_or_create` business logic.
- Modify: `backend/app/deps.py` — add `map_user` + `get_current_user`.
- Create: `backend/app/routers/users.py` — protected `GET /users/me`.
- Modify: `backend/app/main.py` — Keycloak middleware (before CORS) + users router.
- Modify: `backend/tests/conftest.py` — mock middleware before app import.
- Create: `backend/tests/test_users.py` — in-process user tests (mocked auth).
- Create: `backend/tests/test_auth_e2e.py` — real-stack E2E (skips if stack down).

**Keycloak**
- Modify: `keycloak/realm-export.json` — add `expense-test` client (direct grants).

**Frontend**
- Modify: `frontend/public/config.json` — add `auth` block.
- Modify: `frontend/src/app/core/config.service.ts` — `AppConfig.auth` + `authConfig`.
- Modify: `frontend/src/app/core/config.service.spec.ts` — cover the new field.
- Modify: `frontend/src/app/app.config.ts` — `provideAuth` + interceptor + loader.
- Modify: `frontend/src/app/app.ts` — login/logout + show `/users/me`.
- Modify: `frontend/src/app/app.html` — auth UI.
- Modify: `frontend/src/app/app.spec.ts` — provide a fake `OidcSecurityService`.
- Modify: `frontend/package.json` (via npm) — add `angular-auth-oidc-client`.

---

## Backend

### Task 1: Add the Keycloak middleware dependency

**Files:**
- Modify: `backend/pyproject.toml:7-16`

- [ ] **Step 1: Add the dependency**

In `backend/pyproject.toml`, add the line to the `dependencies` array (keep alphabetical-ish ordering near the other fastapi entry):

```toml
dependencies = [
    "alembic==1.14.0",
    "asyncpg>=0.31.0",
    "fastapi[standard]==0.136.3",
    "fastapi-keycloak-middleware==1.6.0",
    "httpx==0.28.0",
    "psycopg2-binary==2.9.10",
    "pydantic-settings==2.6.1",
    "python-jose[cryptography]==3.3.0",
    "sqlalchemy==2.0.36",
]
```

- [ ] **Step 2: Install**

Run (from `backend/`): `uv sync`
Expected: resolves and installs `fastapi-keycloak-middleware` and its transitive `python-keycloak`.

- [ ] **Step 3: Verify the import works**

Run (from `backend/`): `uv run python -c "from fastapi_keycloak_middleware import KeycloakConfiguration, setup_keycloak_middleware, get_user; print('ok')"`
Expected: prints `ok`.

- [ ] **Step 4: Commit**

```bash
git add backend/pyproject.toml backend/uv.lock
git commit -m "build: add fastapi-keycloak-middleware dependency"
```

---

### Task 2: `UserRead` response schema

**Files:**
- Create: `backend/app/schemas/user.py`

- [ ] **Step 1: Write the schema**

```python
import uuid
from datetime import datetime

from pydantic import BaseModel


class UserRead(BaseModel):
    id: uuid.UUID
    keycloak_sub: str
    display_name: str
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}
```

- [ ] **Step 2: Verify it imports**

Run (from `backend/`): `uv run python -c "from app.schemas.user import UserRead; print('ok')"`
Expected: prints `ok`.

- [ ] **Step 3: Commit**

```bash
git add backend/app/schemas/user.py
git commit -m "feat: add UserRead schema"
```

---

### Task 3: User service `get_or_create` (TDD)

**Files:**
- Create: `backend/app/services/user.py`
- Test: `backend/tests/test_users.py`

> Integration tests need the `app_db` container: `docker compose up app_db -d`.

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_users.py`:

```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import user as user_service

# --- Service tests ---


@pytest.mark.asyncio
async def test_get_or_create_creates_user(db: AsyncSession):
    user = await user_service.get_or_create(
        db, keycloak_sub="kc-sub-1", email="alice@example.com", display_name="Alice"
    )
    assert user.id is not None
    assert user.keycloak_sub == "kc-sub-1"
    assert user.email == "alice@example.com"
    assert user.display_name == "Alice"


@pytest.mark.asyncio
async def test_get_or_create_is_idempotent(db: AsyncSession):
    first = await user_service.get_or_create(
        db, keycloak_sub="kc-sub-2", email="bob@example.com", display_name="Bob"
    )
    second = await user_service.get_or_create(
        db, keycloak_sub="kc-sub-2", email="bob@example.com", display_name="Bob"
    )
    assert first.id == second.id
```

- [ ] **Step 2: Run to verify it fails**

Run (from `backend/`): `uv run pytest tests/test_users.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.user'`.

- [ ] **Step 3: Implement the service**

Create `backend/app/services/user.py`:

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def get_or_create(
    db: AsyncSession, keycloak_sub: str, email: str, display_name: str
) -> User:
    result = await db.execute(
        select(User).where(User.keycloak_sub == keycloak_sub)
    )
    user = result.scalar_one_or_none()
    if user is not None:
        return user

    user = User(keycloak_sub=keycloak_sub, email=email, display_name=display_name)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
```

- [ ] **Step 4: Run to verify it passes**

Run (from `backend/`): `uv run pytest tests/test_users.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/user.py backend/tests/test_users.py
git commit -m "feat: add user get_or_create service"
```

---

### Task 4: `map_user` + `get_current_user` dependency

**Files:**
- Modify: `backend/app/deps.py`

> `get_current_user` MUST take `claims=Depends(get_user)` (not read `request.scope` directly) — the in-process tests in Task 7 rely on overriding `get_user`, which only works through `Depends`.

- [ ] **Step 1: Replace `deps.py` content**

```python
from collections.abc import AsyncGenerator
from typing import Any

from fastapi import Depends
from fastapi_keycloak_middleware import get_user
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import AsyncSessionLocal
from app.models.user import User
from app.services import user as user_service


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def map_user(userinfo: dict[str, Any]) -> dict[str, Any]:
    # Runs on every authenticated request inside the middleware.
    # Keep it minimal: no DB access (no Depends/session available here).
    return userinfo


async def get_current_user(
    claims: dict[str, Any] = Depends(get_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    sub = claims["sub"]
    email = claims.get("email", "")
    display_name = (
        claims.get("name") or claims.get("preferred_username") or email or sub
    )
    return await user_service.get_or_create(db, sub, email, display_name)
```

- [ ] **Step 2: Verify it imports**

Run (from `backend/`): `uv run python -c "from app.deps import map_user, get_current_user, get_db; print('ok')"`
Expected: prints `ok`.

- [ ] **Step 3: Commit**

```bash
git add backend/app/deps.py
git commit -m "feat: add map_user and get_current_user dependency"
```

---

### Task 5: Wire middleware + users router into the app

**Files:**
- Create: `backend/app/routers/users.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Create the users router**

Create `backend/app/routers/users.py`:

```python
from fastapi import APIRouter, Depends

from app.deps import get_current_user
from app.models.user import User
from app.schemas.user import UserRead

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
async def read_me(user: User = Depends(get_current_user)):
    return user
```

- [ ] **Step 2: Rewrite `main.py` with correct middleware order**

Replace `backend/app/main.py` with:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_keycloak_middleware import KeycloakConfiguration, setup_keycloak_middleware

from app.core.config import settings
from app.deps import map_user
from app.routers.categories import router as categories_router
from app.routers.users import router as users_router

app = FastAPI(title="Expense API", version="0.1.0")

app.include_router(categories_router, prefix=settings.api_prefix)
app.include_router(users_router, prefix=settings.api_prefix)

keycloak_config = KeycloakConfiguration(
    url=f"{settings.keycloak_url}/",
    realm=settings.keycloak_realm,
    client_id=settings.keycloak_client_id,
)

# Add the Keycloak middleware FIRST so that, after CORS is added below, CORS is
# the OUTERMOST middleware: it answers OPTIONS preflight without auth and emits
# CORS headers even on 401 responses. (Starlette runs the last-added middleware
# first.)
setup_keycloak_middleware(
    app,
    keycloak_configuration=keycloak_config,
    user_mapper=map_user,
    exclude_patterns=["/health", "/docs", "/redoc", "/openapi.json"],
)

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


@app.get("/test")
def test_info():
    return {
        "service": app.title,
        "version": app.version,
        "api_prefix": settings.api_prefix,
        "status": "ok",
    }
```

- [ ] **Step 3: Verify the app imports (middleware actually wires up)**

Run (from `backend/`): `uv run python -c "import app.main; print('ok')"`
Expected: prints `ok` (no exception from `setup_keycloak_middleware`).

> Note: this import contacts Keycloak's OIDC discovery only lazily at request time, so it should not require a running Keycloak. If it does fail here, Keycloak must be up (`docker compose up keycloak -d`).

- [ ] **Step 4: Commit**

```bash
git add backend/app/routers/users.py backend/app/main.py
git commit -m "feat: protect API with keycloak middleware and add /users/me"
```

---

### Task 6: Mock the middleware in tests + prove existing tests still pass

**Files:**
- Modify: `backend/tests/conftest.py`

> Why: once the middleware is active, every in-process route except `exclude_patterns` returns 401. The fix (per the library's testing guide) is to patch `setup_keycloak_middleware` to a no-op **before** `app.main` is imported. conftest.py is imported by pytest before any test module, so patching at the top of conftest lands before `from app.main import app` runs in the test modules.

- [ ] **Step 1: Add the patch at the very top of `conftest.py`**

Edit `backend/tests/conftest.py` so the FIRST executable lines (before the other imports) are:

```python
from unittest import mock

# Disable the Keycloak middleware for all in-process tests. Must run before any
# `from app.main import app`. The real middleware is exercised by the separate
# E2E test (test_auth_e2e.py) against the running Docker stack.
mock.patch("fastapi_keycloak_middleware.setup_keycloak_middleware").start()

import pytest_asyncio  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

import app.models  # noqa: F401, E402 — ensures all tables are registered
from app.core.config import settings  # noqa: E402
from app.db import Base  # noqa: E402
```

(Keep the existing `_async_test_url()` and `db` fixture below, unchanged.)

- [ ] **Step 2: Prove the patch lands — existing category router tests still return 200, not 401**

Run (from `backend/`, with `app_db` up): `uv run pytest tests/test_categories.py -v`
Expected: ALL PASS (the HTTP router tests return 200/201/404 as before — NOT 401). If any return 401, the patch is not landing before `app.main` import — stop and fix before continuing.

- [ ] **Step 3: Run the full existing suite**

Run (from `backend/`): `uv run pytest -v`
Expected: all previously-passing tests still pass (`test_health.py`, `test_main.py`, `test_categories.py`, `test_users.py` service tests).

- [ ] **Step 4: Commit**

```bash
git add backend/tests/conftest.py
git commit -m "test: mock keycloak middleware for in-process tests"
```

---

### Task 7: In-process test for `/users/me` (mocked auth)

**Files:**
- Modify: `backend/tests/test_users.py`

- [ ] **Step 1: Append router tests to `test_users.py`**

Add these imports at the top of `backend/tests/test_users.py` (next to the existing ones):

```python
from fastapi_keycloak_middleware import get_user
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.deps import get_db
from app.main import app
from app.models.user import User
```

Append these tests:

```python
# --- Router tests (auth mocked via get_user override) ---


@pytest.mark.asyncio
async def test_users_me_creates_and_returns_user(db: AsyncSession):
    claims = {
        "sub": "kc-sub-me",
        "email": "alice@example.com",
        "name": "Alice Test",
    }

    async def override_user():
        return claims

    async def override_db():
        yield db

    app.dependency_overrides[get_user] = override_user
    app.dependency_overrides[get_db] = override_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/users/me")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["keycloak_sub"] == "kc-sub-me"
    assert data["email"] == "alice@example.com"
    assert data["display_name"] == "Alice Test"

    # The user was persisted.
    result = await db.execute(select(User).where(User.keycloak_sub == "kc-sub-me"))
    assert result.scalar_one_or_none() is not None
```

- [ ] **Step 2: Run to verify it passes**

Run (from `backend/`, `app_db` up): `uv run pytest tests/test_users.py -v`
Expected: PASS (3 passed total).

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_users.py
git commit -m "test: add in-process /users/me test with mocked auth"
```

---

## Keycloak

### Task 8: Add the `expense-test` client to the realm

**Files:**
- Modify: `keycloak/realm-export.json:11-34`

> The production client `expense-frontend` is left UNCHANGED. The new client only enables the password grant so the E2E test can fetch a token.

- [ ] **Step 1: Add the client to the `clients` array**

In `keycloak/realm-export.json`, add this object to the `"clients"` array (after the existing `expense-frontend` object, inside the same array):

```json
    {
      "clientId": "expense-test",
      "name": "Expense Test (direct grants)",
      "enabled": true,
      "publicClient": true,
      "standardFlowEnabled": false,
      "implicitFlowEnabled": false,
      "directAccessGrantsEnabled": true,
      "serviceAccountsEnabled": false,
      "protocol": "openid-connect"
    }
```

(Ensure the preceding `expense-frontend` object ends with a comma so the array stays valid JSON.)

- [ ] **Step 2: Validate the JSON**

Run: `python -c "import json; json.load(open('keycloak/realm-export.json')); print('valid json')"`
Expected: prints `valid json`.

- [ ] **Step 3: Commit**

```bash
git add keycloak/realm-export.json
git commit -m "feat: add expense-test keycloak client for e2e tests"
```

---

## Frontend

### Task 9: Runtime config — `config.json` + `ConfigService`

**Files:**
- Modify: `frontend/public/config.json`
- Modify: `frontend/src/app/core/config.service.ts`
- Modify: `frontend/src/app/core/config.service.spec.ts`

- [ ] **Step 1: Extend `config.json`**

Replace `frontend/public/config.json` with:

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

- [ ] **Step 2: Extend `ConfigService` and export `AppConfig`**

Replace `frontend/src/app/core/config.service.ts` with:

```typescript
import { Service, computed, signal } from '@angular/core';

export interface AppConfig {
  apiUrl: string;
  auth: {
    authority: string;
    clientId: string;
    scope: string;
  };
}

@Service()
export class ConfigService {
  private readonly _config = signal<AppConfig | null>(null);

  readonly apiUrl = computed(() => this._config()?.apiUrl ?? '');
  readonly authConfig = computed(() => this._config()?.auth ?? null);

  async load(): Promise<void> {
    const response = await fetch('/config.json');
    if (!response.ok) {
      throw new Error(`Failed to load config.json: ${response.status}`);
    }
    this._config.set((await response.json()) as AppConfig);
  }
}
```

- [ ] **Step 3: Update the spec to cover the new field**

In `frontend/src/app/core/config.service.spec.ts`, update the first test's fetch mock and add an assertion so the mocked config includes `auth`:

```typescript
  it('loads config.json and exposes apiUrl and authConfig', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          apiUrl: 'http://test-host:9999',
          auth: {
            authority: 'http://kc/realms/r',
            clientId: 'c',
            scope: 'openid',
          },
        }),
      }),
    );

    const service = TestBed.inject(ConfigService);
    await service.load();

    expect(service.apiUrl()).toBe('http://test-host:9999');
    expect(service.authConfig()?.clientId).toBe('c');
  });
```

(Leave the other two tests in that file unchanged.)

- [ ] **Step 4: Run the config service tests**

Run (from `frontend/`): `ng test --include='**/config.service.spec.ts'`
Expected: PASS.

> If `--include` is unsupported in this setup, run `ng test` and confirm the ConfigService suite passes.

- [ ] **Step 5: Commit**

```bash
git add frontend/public/config.json frontend/src/app/core/config.service.ts frontend/src/app/core/config.service.spec.ts
git commit -m "feat: add auth config to runtime config.json"
```

---

### Task 10: Install library + wire `provideAuth`

**Files:**
- Modify: `frontend/package.json` (via npm)
- Modify: `frontend/src/app/app.config.ts`

- [ ] **Step 1: Install the library**

Run (from `frontend/`): `npm install angular-auth-oidc-client@21`
Expected: `angular-auth-oidc-client` (^21.0.2) added to `dependencies` in `package.json`.

- [ ] **Step 2: Rewrite `app.config.ts`**

Replace `frontend/src/app/app.config.ts` with:

```typescript
import {
  ApplicationConfig,
  inject,
  provideAppInitializer,
  provideBrowserGlobalErrorListeners,
} from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import {
  HttpClient,
  provideHttpClient,
  withFetch,
  withInterceptors,
} from '@angular/common/http';
import {
  authInterceptor,
  provideAuth,
  StsConfigHttpLoader,
  StsConfigLoader,
  withAppInitializerAuthCheck,
} from 'angular-auth-oidc-client';
import { map } from 'rxjs';

import { routes } from './app.routes';
import { AppConfig, ConfigService } from './core/config.service';

export const httpLoaderFactory = (http: HttpClient): StsConfigHttpLoader => {
  const config$ = http.get<AppConfig>('/config.json').pipe(
    map((cfg) => ({
      authority: cfg.auth.authority,
      redirectUrl: window.location.origin,
      postLogoutRedirectUri: window.location.origin,
      clientId: cfg.auth.clientId,
      scope: cfg.auth.scope,
      responseType: 'code',
      silentRenew: true,
      useRefreshToken: true,
      secureRoutes: [cfg.apiUrl],
    })),
  );
  return new StsConfigHttpLoader(config$);
};

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes),
    provideAnimationsAsync(),
    provideHttpClient(withFetch(), withInterceptors([authInterceptor()])),
    provideAppInitializer(() => inject(ConfigService).load()),
    provideAuth(
      {
        loader: {
          provide: StsConfigLoader,
          useFactory: httpLoaderFactory,
          deps: [HttpClient],
        },
      },
      withAppInitializerAuthCheck(),
    ),
  ],
};
```

- [ ] **Step 3: Verify the build compiles**

Run (from `frontend/`): `ng build`
Expected: build succeeds (no TS errors about missing exports from `angular-auth-oidc-client`).

- [ ] **Step 4: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/src/app/app.config.ts
git commit -m "feat: configure angular-auth-oidc-client with runtime config loader"
```

---

### Task 11: Login/logout UI + show `/users/me`

**Files:**
- Modify: `frontend/src/app/app.ts`
- Modify: `frontend/src/app/app.html`
- Modify: `frontend/src/app/app.spec.ts`

- [ ] **Step 1: Rewrite `app.ts`**

Replace `frontend/src/app/app.ts` with:

```typescript
import { Component, inject } from '@angular/core';
import { JsonPipe } from '@angular/common';
import { httpResource } from '@angular/common/http';
import { RouterOutlet } from '@angular/router';
import { OidcSecurityService } from 'angular-auth-oidc-client';

import { ConfigService } from './core/config.service';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, JsonPipe],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App {
  private readonly config = inject(ConfigService);
  private readonly oidc = inject(OidcSecurityService);

  protected readonly apiUrl = this.config.apiUrl;
  protected readonly authenticated = this.oidc.authenticated;

  protected readonly me = httpResource(() =>
    this.authenticated().isAuthenticated
      ? `${this.apiUrl()}/api/v1/users/me`
      : undefined,
  );

  login(): void {
    this.oidc.authorize();
  }

  logout(): void {
    this.oidc.logoff().subscribe();
  }
}
```

- [ ] **Step 2: Rewrite `app.html`**

Replace `frontend/src/app/app.html` with:

```html
<main>
  <h1>Runtime config check</h1>
  <p>API URL: {{ apiUrl() }}</p>

  @if (authenticated().isAuthenticated) {
    <button type="button" (click)="logout()">Logout</button>

    @if (me.isLoading()) {
      <p>Loading user…</p>
    } @else if (me.error()) {
      <p role="alert">Could not load the authenticated user.</p>
    } @else if (me.value(); as user) {
      <h2>Authenticated as:</h2>
      <pre>{{ user | json }}</pre>
    }
  } @else {
    <button type="button" (click)="login()">Login</button>
  }
</main>

<router-outlet />
```

- [ ] **Step 3: Fix `app.spec.ts` to provide a fake `OidcSecurityService`**

Replace `frontend/src/app/app.spec.ts` with:

```typescript
import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideHttpClient, withFetch } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { OidcSecurityService } from 'angular-auth-oidc-client';
import { App } from './app';

describe('App', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [
        provideHttpClient(withFetch()),
        provideHttpClientTesting(),
        {
          provide: OidcSecurityService,
          useValue: { authenticated: signal({ isAuthenticated: false }) },
        },
      ],
    }).compileComponents();
  });

  it('should create the app', () => {
    const fixture = TestBed.createComponent(App);
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('should render the config check heading', () => {
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('h1')?.textContent).toContain(
      'Runtime config check',
    );
  });

  it('shows a login button when unauthenticated', () => {
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('button')?.textContent).toContain('Login');
  });
});
```

- [ ] **Step 4: Run the frontend tests**

Run (from `frontend/`): `ng test`
Expected: all suites PASS (App + ConfigService).

- [ ] **Step 5: Commit**

```bash
git add frontend/src/app/app.ts frontend/src/app/app.html frontend/src/app/app.spec.ts
git commit -m "feat: add login/logout UI and show authenticated user"
```

---

## End-to-end validation

### Task 12: Re-import realm, verify token, add E2E test

**Files:**
- Create: `backend/tests/test_auth_e2e.py`

> The realm imports only on Keycloak's first start against an empty `keycloak_db`, and that DB is persisted in the `keycloak_postgres_data` volume. Adding `expense-test` to `realm-export.json` does nothing until the realm is re-imported.

- [ ] **Step 1: Recreate the stack so the realm re-imports**

Run (from project root):

```bash
docker compose down -v
docker compose up --build -d
```

Expected: containers start. `docker compose down -v` removes the volumes (including `keycloak_postgres_data`), forcing a fresh realm import; `app_db` re-initializes from `db/init/01-init.sql`.

- [ ] **Step 2: Wait for Keycloak and the backend to be ready**

Run: `curl -sf http://localhost:8080/realms/expense-app/.well-known/openid-configuration > /dev/null && echo kc-ok`
Expected: prints `kc-ok` (retry for ~30-60s while Keycloak boots).
Run: `curl -sf http://localhost:8000/health && echo`
Expected: `{"status":"ok"}`.

- [ ] **Step 3: Verify the password grant against `expense-test` returns a token (before writing the test)**

Run:

```bash
curl -s -X POST \
  http://localhost:8080/realms/expense-app/protocol/openid-connect/token \
  -d grant_type=password -d client_id=expense-test \
  -d username=alice -d password=alice123 | python -c "import sys,json; print('access_token' in json.load(sys.stdin))"
```

Expected: prints `True`. If it prints `False` / shows `invalid_client`, the realm did not re-import — re-run Step 1 and confirm `expense-test` exists in `realm-export.json`.

- [ ] **Step 4: Manually confirm the protected endpoint accepts the token**

Run:

```bash
TOKEN=$(curl -s -X POST http://localhost:8080/realms/expense-app/protocol/openid-connect/token -d grant_type=password -d client_id=expense-test -d username=alice -d password=alice123 | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/api/v1/users/me -H "Authorization: Bearer $TOKEN"
```

Expected: prints `200`. If it prints `401`, the token's `aud` is being rejected — apply the known caveat: add an Audience protocol mapper to the realm so `aud` includes the backend, set `audience=...` in `KeycloakConfiguration` (Task 5 Step 2), recreate the stack (Step 1), and retry. Do not proceed until this returns `200`.

- [ ] **Step 5: Write the E2E test**

Create `backend/tests/test_auth_e2e.py`:

```python
import os

import httpx
import pytest

BACKEND_URL = os.environ.get("E2E_BACKEND_URL", "http://localhost:8000")
KEYCLOAK_URL = os.environ.get("E2E_KEYCLOAK_URL", "http://localhost:8080")
REALM = "expense-app"
TEST_CLIENT_ID = "expense-test"


def _stack_is_up() -> bool:
    try:
        return httpx.get(f"{BACKEND_URL}/health", timeout=2.0).status_code == 200
    except httpx.HTTPError:
        return False


pytestmark = pytest.mark.skipif(
    not _stack_is_up(),
    reason="E2E requires the full Docker stack running (docker compose up)",
)


def _get_token(username: str, password: str) -> str:
    response = httpx.post(
        f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token",
        data={
            "grant_type": "password",
            "client_id": TEST_CLIENT_ID,
            "username": username,
            "password": password,
        },
        timeout=10.0,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def test_me_with_valid_token_returns_user():
    token = _get_token("alice", "alice123")
    response = httpx.get(
        f"{BACKEND_URL}/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10.0,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "alice@example.com"
    assert data["keycloak_sub"]


def test_me_without_token_is_unauthorized():
    response = httpx.get(f"{BACKEND_URL}/api/v1/users/me", timeout=10.0)
    assert response.status_code == 401


def test_cors_preflight_succeeds_without_token():
    # Proves CORS is the outermost middleware: preflight is answered without auth.
    response = httpx.options(
        f"{BACKEND_URL}/api/v1/users/me",
        headers={
            "Origin": "http://localhost:4200",
            "Access-Control-Request-Method": "GET",
        },
        timeout=10.0,
    )
    assert response.status_code in (200, 204)
    header_names = {k.lower() for k in response.headers}
    assert "access-control-allow-origin" in header_names
```

- [ ] **Step 6: Run the E2E test against the running stack**

Run (from `backend/`): `uv run pytest tests/test_auth_e2e.py -v`
Expected: 3 passed. (If the stack is down, the suite is skipped instead of failing.)

- [ ] **Step 7: Run the full backend suite**

Run (from `backend/`): `uv run pytest -v`
Expected: all in-process tests pass; E2E tests pass (stack up) or skip (stack down).

- [ ] **Step 8: Commit**

```bash
git add backend/tests/test_auth_e2e.py
git commit -m "test: add end-to-end authentication test against running stack"
```

---

## Final verification checklist

- [ ] Backend: `cd backend && uv run pytest -v` — all pass (or E2E skipped if stack down).
- [ ] Frontend: `cd frontend && ng test` — all pass.
- [ ] Frontend: `cd frontend && ng build` — succeeds.
- [ ] Manual browser check (stack up, `ng serve`): Login redirects to Keycloak; logging in as `alice / alice123` returns to the app and shows the `/users/me` JSON; Logout returns to the unauthenticated state.

---

## Notes / contingencies

- **Audience rejection (caveat):** if Task 12 Step 4 returns 401, add an Audience protocol mapper to the realm so the access token's `aud` includes the backend, and set `audience=` in `KeycloakConfiguration`. This is the only anticipated realm change beyond `expense-test`.
- **`down -v` wipes app_db:** acceptable in dev — schema re-inits from `db/init/01-init.sql`; re-apply seeds manually if needed (`db/seeds/`).
- **Migrations:** the `users` table already exists in the schema; no Alembic change is required for this feature.
