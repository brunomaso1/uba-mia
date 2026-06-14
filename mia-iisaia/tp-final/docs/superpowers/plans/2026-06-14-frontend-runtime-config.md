# Frontend Runtime Configuration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Load the frontend's environment configuration (the backend API URL) from a runtime JSON file before bootstrap, exposed via a signal-backed service, and prove it end-to-end against a new backend `/test` endpoint.

**Architecture:** `provideAppInitializer` runs `ConfigService.load()`, which `fetch`es `/config.json` (served from Angular's `public/` folder) and stores the parsed config in a signal. `provideHttpClient(withFetch())` powers the real API calls. The root `App` component reads `ConfigService.apiUrl()` and uses `httpResource` to call the backend `/test` endpoint, rendering the response to confirm the whole chain works.

**Tech Stack:** Angular 22 (standalone, signals, `@Service`, `provideAppInitializer`, `httpResource`), Vitest, FastAPI 0.136.3, pytest.

---

## File Structure

| File | Responsibility |
| --- | --- |
| `backend/app/main.py` | Add root `/test` diagnostic endpoint (next to `/health`) |
| `backend/tests/test_main.py` | Pytest for `/test` |
| `frontend/public/config.json` | Runtime config (`apiUrl`) — overwritten per environment |
| `frontend/src/app/core/config.service.ts` | Loads config via `fetch`, exposes `apiUrl` signal |
| `frontend/src/app/core/config.service.spec.ts` | Vitest for `ConfigService` |
| `frontend/src/app/app.config.ts` | Register `provideHttpClient` + `provideAppInitializer` |
| `frontend/src/app/app.ts` | Inject `ConfigService`, fetch `/test` via `httpResource` |
| `frontend/src/app/app.html` | Render API URL + `/test` response |
| `frontend/src/app/app.spec.ts` | Update existing test for the new template |

**Conventions:** backend tests run from `backend/`; frontend uses Vitest via `ng test`. Use `bash`. Commits target the `mia-iisaia` branch; never push. The pre-commit hook runs ruff (backend) + lint-staged (frontend) automatically.

---

## Task 1: Backend `/test` endpoint

**Files:**
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_main.py` (create)

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_main.py`:

```python
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_test_endpoint_returns_backend_info():
    response = client.get("/test")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "Expense API"
    assert body["api_prefix"] == "/api/v1"
    assert "version" in body
```

- [ ] **Step 2: Run test to verify it fails**

Run (from `backend/`): `uv run pytest tests/test_main.py -v`
Expected: FAIL with 404 (no `/test` route) → assertion error on `status_code == 200`.

- [ ] **Step 3: Add the endpoint**

In `backend/app/main.py`, add below the existing `health_check` function:

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

(`settings` is already imported at the top of `main.py`.)

- [ ] **Step 4: Run test to verify it passes**

Run (from `backend/`): `uv run pytest tests/test_main.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/main.py backend/tests/test_main.py
git commit -m "feat: add /test diagnostic endpoint"
```

---

## Task 2: Runtime config file

**Files:**
- Create: `frontend/public/config.json`

- [ ] **Step 1: Create the config file**

Create `frontend/public/config.json`:

```json
{
  "apiUrl": "http://localhost:8000"
}
```

Angular 22 serves `public/` at the web root, so this is reachable at `/config.json`. No `angular.json` change is needed (the `public` glob already covers it).

- [ ] **Step 2: Verify it is served (optional sanity check)**

If a dev server is running: `curl http://localhost:4200/config.json` → returns the JSON above. Skip if no server is running; the Vitest test in Task 3 covers loading behavior.

- [ ] **Step 3: Commit**

```bash
git add frontend/public/config.json
git commit -m "feat: add frontend runtime config.json"
```

---

## Task 3: `ConfigService`

**Files:**
- Create: `frontend/src/app/core/config.service.ts`
- Test: `frontend/src/app/core/config.service.spec.ts`

- [ ] **Step 1: Write the failing test**

Create `frontend/src/app/core/config.service.spec.ts`:

```ts
import { TestBed } from '@angular/core/testing';
import { ConfigService } from './config.service';

describe('ConfigService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('loads config.json and exposes apiUrl', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ apiUrl: 'http://test-host:9999' }),
      }),
    );

    const service = TestBed.inject(ConfigService);
    await service.load();

    expect(service.apiUrl()).toBe('http://test-host:9999');
  });

  it('rejects when config.json fetch is not ok', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 404 }));

    const service = TestBed.inject(ConfigService);

    await expect(service.load()).rejects.toThrow();
  });

  it('returns empty apiUrl before load', () => {
    const service = TestBed.inject(ConfigService);
    expect(service.apiUrl()).toBe('');
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run (from `frontend/`): `ng test --include src/app/core/config.service.spec.ts`
Expected: FAIL — cannot resolve `./config.service` (file does not exist).

- [ ] **Step 3: Implement the service**

Create `frontend/src/app/core/config.service.ts`:

```ts
import { Service, computed, signal } from '@angular/core';

interface AppConfig {
  apiUrl: string;
}

@Service()
export class ConfigService {
  private readonly _config = signal<AppConfig | null>(null);

  readonly apiUrl = computed(() => this._config()?.apiUrl ?? '');

  async load(): Promise<void> {
    const response = await fetch('/config.json');
    if (!response.ok) {
      throw new Error(`Failed to load config.json: ${response.status}`);
    }
    this._config.set((await response.json()) as AppConfig);
  }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run (from `frontend/`): `ng test --include src/app/core/config.service.spec.ts`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add frontend/src/app/core/config.service.ts frontend/src/app/core/config.service.spec.ts
git commit -m "feat: add signal-backed ConfigService that loads config.json"
```

---

## Task 4: Wire providers in `app.config.ts`

**Files:**
- Modify: `frontend/src/app/app.config.ts`

- [ ] **Step 1: Update the application config**

Replace the contents of `frontend/src/app/app.config.ts` with:

```ts
import {
  ApplicationConfig,
  inject,
  provideAppInitializer,
  provideBrowserGlobalErrorListeners,
} from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { provideHttpClient, withFetch } from '@angular/common/http';

import { routes } from './app.routes';
import { ConfigService } from './core/config.service';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes),
    provideAnimationsAsync(),
    provideHttpClient(withFetch()),
    provideAppInitializer(() => inject(ConfigService).load()),
  ],
};
```

The initializer **returns** `load()`'s promise so bootstrap waits for the config before rendering.

- [ ] **Step 2: Verify the app still builds**

Run (from `frontend/`): `ng build`
Expected: build succeeds with no errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/app/app.config.ts
git commit -m "feat: load config via provideAppInitializer and add HttpClient"
```

---

## Task 5: Prove it in the `App` component

**Files:**
- Modify: `frontend/src/app/app.ts`
- Modify: `frontend/src/app/app.html`
- Modify: `frontend/src/app/app.spec.ts`

- [ ] **Step 1: Update the component test (failing)**

Replace the contents of `frontend/src/app/app.spec.ts` with:

```ts
import { TestBed } from '@angular/core/testing';
import { provideHttpClient, withFetch } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { App } from './app';

describe('App', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [provideHttpClient(withFetch()), provideHttpClientTesting()],
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
    expect(compiled.querySelector('h1')?.textContent).toContain('Runtime config check');
  });
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run (from `frontend/`): `ng test --include src/app/app.spec.ts`
Expected: FAIL — current `app.html` renders `Hello, expense-app`, not `Runtime config check`.

- [ ] **Step 3: Update the component**

Replace the contents of `frontend/src/app/app.ts` with:

```ts
import { Component, inject } from '@angular/core';
import { JsonPipe } from '@angular/common';
import { httpResource } from '@angular/common/http';
import { RouterOutlet } from '@angular/router';
import { ConfigService } from './core/config.service';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, JsonPipe],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App {
  private readonly config = inject(ConfigService);

  protected readonly apiUrl = this.config.apiUrl;
  protected readonly testInfo = httpResource(() => `${this.config.apiUrl()}/test`);
}
```

- [ ] **Step 4: Replace the template**

Replace the entire contents of `frontend/src/app/app.html` with:

```html
<main>
  <h1>Runtime config check</h1>
  <p>API URL: {{ apiUrl() }}</p>

  @if (testInfo.isLoading()) {
    <p>Loading backend info…</p>
  } @else if (testInfo.error()) {
    <p role="alert">Could not reach the backend at {{ apiUrl() }}.</p>
  } @else if (testInfo.value(); as info) {
    <h2>Backend says:</h2>
    <pre>{{ info | json }}</pre>
  }
</main>

<router-outlet />
```

- [ ] **Step 5: Run the component test to verify it passes**

Run (from `frontend/`): `ng test --include src/app/app.spec.ts`
Expected: PASS (2 tests).

- [ ] **Step 6: Manual end-to-end verification**

Start infra + backend + frontend, then open the app:

```bash
# terminal 1 — infra
docker compose up app_db keycloak_db keycloak
# terminal 2 — backend (from backend/)
uv run fastapi dev
# terminal 3 — frontend (from frontend/)
ng serve
```

Open `http://localhost:4200`. Expected: the page shows `API URL: http://localhost:8000` and a "Backend says:" block with the JSON `{ "service": "Expense API", "version": "0.1.0", "api_prefix": "/api/v1", "status": "ok" }`. This confirms config loaded from `config.json` and the API call used it.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/app/app.ts frontend/src/app/app.html frontend/src/app/app.spec.ts
git commit -m "feat: render backend /test response using runtime config"
```

---

## Final verification

- [ ] **Run the full backend suite**

Run (from `backend/`): `uv run pytest`
Expected: all tests pass (including the existing `test_health.py` and `test_categories.py`).

- [ ] **Run the full frontend suite**

Run (from `frontend/`): `ng test`
Expected: all tests pass.

- [ ] **Confirm production build**

Run (from `frontend/`): `ng build`
Expected: build succeeds.
