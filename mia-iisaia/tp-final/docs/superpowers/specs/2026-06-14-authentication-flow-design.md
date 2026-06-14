# Authentication flow design — Keycloak OIDC / PKCE

**Date:** 2026-06-14
**Status:** Approved (design)

## Goal

Implement the end-to-end authentication flow for the expense management app:

- **Frontend** (Angular 22): delegate login to Keycloak via OIDC Authorization Code Flow + PKCE, using `angular-auth-oidc-client`. Attach the access token as `Authorization: Bearer <token>` to backend API calls.
- **Backend** (FastAPI): validate the JWT locally against Keycloak using `fastapi-keycloak-middleware`. Expose a protected `GET /api/v1/users/me` that auto-creates the DB user on first authenticated request.
- **E2E test**: a pytest integration test that obtains a real token from a running Keycloak and exercises the protected endpoint.

## Library versions (latest as of 2026-06-14)

- `angular-auth-oidc-client@21.0.2`
- `fastapi-keycloak-middleware@1.6.0`

## Decisions

- **E2E test type:** Backend pytest integration test (not browser/Playwright). Obtains a real token via Resource Owner Password Credentials (password grant) against a running Keycloak container.
- **Frontend scope:** Minimal — login/logout buttons, auth-state check on startup, bearer-token interceptor, and display of the authenticated user from `/users/me`. No new routes or guards.
- **Test client:** Add a dedicated public client `expense-test` with `directAccessGrantsEnabled: true` to the realm so the password grant works. The production client `expense-frontend` is left unchanged (PKCE only, no direct grants).
- **Audience validation:** Start **without** setting `audience` in `KeycloakConfiguration`. If a real token is rejected during implementation, the fix is to add an Audience protocol mapper in the realm (documented as a known caveat, not done preemptively).

---

## Frontend (Angular 22 + angular-auth-oidc-client)

### Runtime config via fetch

Extend `frontend/public/config.json`. The same `/config.json` URL feeds both the existing `ConfigService` (for `apiUrl`) and the OIDC config loader.

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

### `ConfigService`

Extend the `AppConfig` interface and the service to also expose the `auth` block (e.g. a computed `authConfig`). The existing `load()` / `apiUrl` behavior is preserved.

### `app.config.ts`

Add `provideAuth` with an HTTP-backed config loader:

```typescript
provideAuth({
  loader: {
    provide: StsConfigLoader,
    useFactory: (http: HttpClient) =>
      new StsConfigHttpLoader(
        http.get<AppConfig>('/config.json').pipe(
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
        ),
      ),
    deps: [HttpClient],
  },
})
```

- Register the auth HTTP interceptor with `withInterceptors([authInterceptor])` so the bearer token is attached **only** to URLs listed in `secureRoutes` (the backend `apiUrl`).
- Use the library's `withAppInitializerAuthCheck()` feature so the OAuth callback is processed during bootstrap (no manual `checkAuth()` needed).

### Initialization ordering (delicate point)

- `StsConfigHttpLoader` performs its own `GET /config.json`, so the OIDC config does not depend on `ConfigService`.
- The existing `provideAppInitializer(() => inject(ConfigService).load())` is kept for `apiUrl`.
- The auth check (`withAppInitializerAuthCheck()`) must run after config is available; since the loader fetches config itself, this ordering is satisfied by the library.

### UI (`app.ts` / `app.html`)

- Inject `OidcSecurityService`.
- Reactive auth state from `checkAuth()` (`isAuthenticated`).
- **Login** button → `oidcSecurityService.authorize()`.
- **Logout** button → `oidcSecurityService.logoff()`.
- When authenticated, call `GET {apiUrl}/api/v1/users/me` and display the returned user.
- Replace the current `/test` demo (which becomes protected) with `/users/me`.

---

## Backend (FastAPI + fastapi-keycloak-middleware)

### Dependencies

Add `fastapi-keycloak-middleware==1.6.0` to `backend/pyproject.toml`. `python-jose` may become redundant but is left in place unless cleanly removable.

### Config (`app/core/config.py`)

Existing fields are sufficient: `keycloak_url`, `keycloak_realm`, `keycloak_client_id`. No new fields strictly required (audience intentionally omitted).

### Middleware setup (`app/main.py`)

```python
keycloak_config = KeycloakConfiguration(
    url=f"{settings.keycloak_url}/",
    realm=settings.keycloak_realm,
    client_id=settings.keycloak_client_id,
)

setup_keycloak_middleware(
    app,
    keycloak_configuration=keycloak_config,
    user_mapper=map_user,
    exclude_patterns=["/health", "/docs", "/openapi.json", "/redoc"],
)

# CORS added AFTER setup_keycloak_middleware so it is the OUTERMOST middleware:
# it handles OPTIONS preflight and emits CORS headers even on 401 responses.
app.add_middleware(CORSMiddleware, ...)  # unchanged options
```

**Ordering rationale:** In Starlette, the middleware added last runs first (outermost). CORS must wrap the Keycloak middleware so preflight `OPTIONS` requests are answered without auth and error responses still carry CORS headers.

### `user_mapper` (minimal)

```python
async def map_user(userinfo: dict) -> dict:
    # Runs on every request; no Depends / DB session available here.
    return userinfo  # claims: sub, email, preferred_username, name, ...
```

### Get-or-create in a dependency, not the mapper (`app/deps.py`)

`get_current_user(request, db=Depends(get_db))`:

- Reads the mapped claims from the request (via `get_user` / `request.state`).
- Looks up `User` by `keycloak_sub` (the `sub` claim).
- If absent, creates the user (`keycloak_sub`, `email`, `display_name` from claims) — matches the CLAUDE.md convention of auto-creating on first `GET /users/me`.
- Returns the `User` ORM object.

### Router (`app/routers/users.py`)

- `GET /api/v1/users/me` → protected → returns `UserRead` Pydantic schema.
- Register the router in `main.py` with the `settings.api_prefix` prefix.

### Schema (`app/schemas/user.py`)

`UserRead` with `id`, `keycloak_sub`, `display_name`, `email`, `created_at` (`from_attributes = True`).

### Effect on existing endpoints

- `/health` → excluded (public).
- `/test` → becomes protected (no longer the unauthenticated demo).
- `/docs`, `/openapi.json`, `/redoc` → excluded so Swagger UI keeps working.

---

## Keycloak realm (`keycloak/realm-export.json`)

Add a second client **without modifying `expense-frontend`**:

```json
{
  "clientId": "expense-test",
  "name": "Expense Test (direct grants)",
  "enabled": true,
  "publicClient": true,
  "standardFlowEnabled": false,
  "directAccessGrantsEnabled": true,
  "protocol": "openid-connect"
}
```

Used only by the pytest E2E to obtain a token via password grant. Test users `alice / alice123` and `bob / bob123` already exist.

---

## E2E test (pytest)

New integration test (e.g. `backend/tests/test_auth.py`). Requires running `keycloak` and `app_db` containers.

**Helper:** obtain an access token via password grant:

```
POST {keycloak_url}/realms/expense-app/protocol/openid-connect/token
  grant_type=password
  client_id=expense-test
  username=alice
  password=alice123
```

**Cases:**

1. **Authenticated:** call `GET /api/v1/users/me` with `Authorization: Bearer <token>` → expect `200`, response email/display_name match `alice`, and a `User` row now exists in the DB with the token's `sub` as `keycloak_sub`.
2. **Unauthenticated:** call `GET /api/v1/users/me` without a token → expect `401`.

The test reads Keycloak/DB connection details from settings/env consistent with existing integration tests (`conftest.py`).

---

## Known caveat

Token acceptance depends on the `aud` claim of a real `expense-frontend` token. We start without `audience` configured. If validation rejects valid tokens during implementation, add an Audience protocol mapper to the realm (so `aud` includes the backend) and set `audience` accordingly in `KeycloakConfiguration`. This is a contingency, not part of the initial implementation.

## Out of scope

- Role-based authorization / permissions.
- Frontend route guards and protected routes.
- Browser-based (Playwright) E2E.
- User profile editing or a registration flow (users auto-created on first `/users/me`).
