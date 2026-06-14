# Frontend Runtime Configuration — Design

**Date:** 2026-06-14
**Status:** Approved

## Problem

The frontend currently has no way to read environment-specific values (like the
backend API URL) at runtime. Build-time `environment.ts` files require rebuilding
the image per environment, which does not fit a Kubernetes-style deployment where
configuration is injected into a running container.

We want the frontend to load its configuration from a JSON file served alongside
the app, resolved **before** the application bootstraps, so that a single built
image can be reconfigured per environment by overwriting that file (e.g. mounting
a ConfigMap over it).

## Goals

- Load runtime configuration from a JSON file at app startup, before bootstrap.
- Expose the configuration through a service backed by a signal.
- Prove the mechanism end-to-end: a backend `/test` endpoint whose response is
  fetched using the configured API URL and rendered in the UI.
- Lay groundwork compatible with future Keycloak auth config living in the same
  JSON file.

## Non-Goals

- Authentication / Keycloak integration (future work; the design only stays
  compatible with it).
- Multiple config files or per-feature config splitting (YAGNI).
- Schema validation of the config file beyond basic parsing.

## Key Decisions

1. **Config file lives at `public/config.json`.** Angular 22 serves the `public/`
   folder at the web root (see `angular.json` `assets`), so the file is reachable
   at `/config.json`. This is the native v22 convention and is the natural target
   for a Kubernetes ConfigMap mount. We do **not** use `src/assets/`.

2. **The initializer loads config with native `fetch()`, not `HttpClient`.**
   Rationale, given that Keycloak auth config will later live in the same file:
   - **Startup ordering:** config must resolve before any auth initialization
     that depends on it. `fetch` has no DI dependencies, so it is the clean first
     step.
   - **Interceptor isolation:** the future auth HTTP interceptor (attaching
     `Authorization: Bearer <token>` and handling 401 re-login) lives in the
     `HttpClient` pipeline. Loading config via `HttpClient` would route the
     config request through that interceptor before a token exists — a classic
     chicken-and-egg bug. `fetch` keeps the config request outside the
     interceptor chain entirely.
   - **Less coupling:** does not require `provideHttpClient` to be mounted to load
     config.

   `provideHttpClient(withFetch())` is still added — for the real API calls
   (including the demo `/test` fetch), not for loading config.

3. **`apiUrl` is the backend base URL without prefix** (`http://localhost:8000`).
   Per-call paths are appended by callers. The `/test` endpoint is defined at root
   in `main.py`, mirroring the existing `/health` exception to the `/api/v1` rule.

## Architecture

```
provideAppInitializer  →  fetch('/config.json')  →  ConfigService signal set
        │  (bootstrap awaits the returned promise)
        ▼
App component  →  httpResource(`${apiUrl()}/test`)  →  renders backend info
```

## Components

### 1. `public/config.json`

```json
{ "apiUrl": "http://localhost:8000" }
```

Base URL of the backend. Overwritten per environment (ConfigMap mount in K8s).
Extensible: future keys (e.g. a `keycloak` object) are added here without code
changes to the loading mechanism.

### 2. `ConfigService` — `frontend/src/app/core/config.service.ts`

- Uses the **`@Service`** decorator (project rule for singletons in v22 — not
  `@Injectable({ providedIn: 'root' })`).
- Holds a private `WritableSignal` of the parsed config; exposes a public
  `apiUrl = computed(...)` (and the raw config as needed).
- `load(): Promise<void>` performs `fetch('/config.json')`, parses JSON, and
  `.set()`s the signal. **It returns the promise** so the initializer can await
  it. Throws/rejects if the fetch fails (fail fast — a misconfigured app should
  not start silently).

Sketch:

```ts
import { Service, signal, computed } from '@angular/core';

interface AppConfig {
  apiUrl: string;
}

@Service()
export class ConfigService {
  private readonly _config = signal<AppConfig | null>(null);
  readonly apiUrl = computed(() => this._config()?.apiUrl ?? '');

  async load(): Promise<void> {
    const res = await fetch('/config.json');
    if (!res.ok) {
      throw new Error(`Failed to load config.json: ${res.status}`);
    }
    this._config.set(await res.json());
  }
}
```

### 3. `frontend/src/app/app.config.ts`

Add two providers:

```ts
import { provideHttpClient, withFetch } from '@angular/common/http';
import { provideAppInitializer, inject } from '@angular/core';
import { ConfigService } from './core/config.service';

// inside providers: [...]
provideHttpClient(withFetch()),
provideAppInitializer(() => inject(ConfigService).load()),
```

The initializer callback **returns** `load()`'s promise so bootstrap waits for it;
otherwise the signal would be empty when the component first renders.

### 4. App component (end-to-end proof) — `frontend/src/app/app.ts` + `app.html`

- Injects `ConfigService` via `inject()`.
- Uses **`httpResource(() => `${config.apiUrl()}/test`)`** to fetch backend info
  (project rule prefers `resource()`/`httpResource()` for async data).
- Template uses native control flow to render the three states:

```
@if (testInfo.isLoading()) { Loading… }
@else if (testInfo.error()) { Error contacting backend }
@else if (testInfo.value(); as info) { <pre>{{ info | json }}</pre> }
```

This proves the config loaded (the URL came from `config.json`) and the API is
reachable.

### 5. Backend — `/test` endpoint in `backend/app/main.py`

Defined at root, next to `/health`:

```python
@app.get("/test")
def test_info():
    return {
        "service": app.title,
        "version": app.version,
        "api_prefix": settings.api_prefix,
        "status": "ok",
    }
```

`config.json.apiUrl` (`http://localhost:8000`) + `/test` ⇒ the frontend calls
`http://localhost:8000/test`. CORS is already configured for
`http://localhost:4200`.

## Data Flow

1. Browser loads `index.html` and the Angular bundle.
2. `provideAppInitializer` runs `ConfigService.load()`; bootstrap awaits it.
3. `fetch('/config.json')` resolves; the `apiUrl` signal is populated.
4. App component renders; `httpResource` issues `GET http://localhost:8000/test`.
5. The backend response is rendered, confirming the full chain.

## Error Handling

- **Config fetch fails** (missing/invalid `config.json`): `load()` rejects, the
  app initializer fails, and bootstrap aborts. This is intentional — running with
  no API URL is worse than a visible failure. The error surfaces in the console.
- **Backend `/test` unreachable**: handled by `httpResource`'s `error()` state and
  shown in the template; does not crash the app.

## Testing

- **Vitest** — `frontend/src/app/core/config.service.spec.ts`: stub global
  `fetch` to return a known payload; assert `load()` populates the signal and
  `apiUrl()` returns the expected value; assert `load()` rejects on a non-OK
  response.
- **pytest** — `backend/tests/test_test_endpoint.py`: `GET /test` returns 200 and
  the response contains the expected keys (`service`, `version`, `api_prefix`,
  `status`).

## Conventions Honored

- Frontend: `@Service` decorator, signals + `computed`, `httpResource` for async
  data, native control flow, `provideHttpClient(withFetch())`, zoneless (no
  `provideZonelessChangeDetection()` added).
- Backend: endpoint in `main.py` mirroring `/health`; returns a plain dict (no DB,
  no schema needed for a diagnostic endpoint).

## Files Touched

| File | Change |
| --- | --- |
| `frontend/public/config.json` | new — runtime config |
| `frontend/src/app/core/config.service.ts` | new — config service |
| `frontend/src/app/core/config.service.spec.ts` | new — Vitest test |
| `frontend/src/app/app.config.ts` | add HttpClient + app initializer providers |
| `frontend/src/app/app.ts` | inject ConfigService, add `httpResource` |
| `frontend/src/app/app.html` | render `/test` response |
| `backend/app/main.py` | add `/test` endpoint |
| `backend/tests/test_test_endpoint.py` | new — pytest test |
