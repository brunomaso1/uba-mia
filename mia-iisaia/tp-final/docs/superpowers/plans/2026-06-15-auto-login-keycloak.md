# Auto-Login on App Load Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redirect unauthenticated users to Keycloak automatically on app load — no "Login" button click required.

**Architecture:** Replace `withAppInitializerAuthCheck()` with a custom `provideAppInitializer` that calls `oidc.checkAuth()` and, if the user is not authenticated, calls `oidc.authorize()` and returns a promise that never resolves (the browser is already navigating away). The `App` component and template are trimmed to remove the now-unreachable unauthenticated branch.

**Tech Stack:** Angular 22, `angular-auth-oidc-client` v21, RxJS `firstValueFrom`, Vitest (via `ng test`)

**Spec:** `docs/superpowers/specs/2026-06-15-auto-login-keycloak-design.md`

---

## File Map

| File | Change |
|---|---|
| `frontend/src/app/app.spec.ts` | Remove login-button test; add no-login-button assertion and authenticated-state test |
| `frontend/src/app/app.html` | Remove `@else` branch (Login button) |
| `frontend/src/app/app.ts` | Remove `login()` method |
| `frontend/src/app/app.config.ts` | Replace `withAppInitializerAuthCheck()` with custom `provideAppInitializer` |
| `README.md` | Add auto-redirect note to Authentication Flow section |

---

### Task 1: Update App component tests (write failing tests first)

The existing test `'shows a login button when unauthenticated'` tests the opposite of the desired behavior — delete it. Add a test that verifies no login button is ever rendered, and a separate test (with its own `beforeEach`) that verifies the logout button appears when authenticated.

**Files:**
- Modify: `frontend/src/app/app.spec.ts`

- [ ] **Step 1: Replace the full content of `app.spec.ts`**

```typescript
import { of } from 'rxjs';
import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideHttpClient, withFetch } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { OidcSecurityService } from 'angular-auth-oidc-client';
import { App } from './app';

const unauthenticatedOidc = {
  authenticated: signal({ isAuthenticated: false }),
};

const authenticatedOidc = {
  authenticated: signal({ isAuthenticated: true }),
  logoff: () => of(null),
};

describe('App — unauthenticated state', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [
        provideHttpClient(withFetch()),
        provideHttpClientTesting(),
        { provide: OidcSecurityService, useValue: unauthenticatedOidc },
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
    expect(compiled.querySelector('h1')?.textContent).toContain('Runtime config check');
  });

  it('does not render a login button', () => {
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    const buttons = Array.from(compiled.querySelectorAll('button'));
    expect(buttons.every((b) => !b.textContent?.includes('Login'))).toBe(true);
  });
});

describe('App — authenticated state', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [
        provideHttpClient(withFetch()),
        provideHttpClientTesting(),
        { provide: OidcSecurityService, useValue: authenticatedOidc },
      ],
    }).compileComponents();
  });

  it('shows a logout button when authenticated', () => {
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    const buttons = Array.from(compiled.querySelectorAll('button'));
    expect(buttons.some((b) => b.textContent?.includes('Logout'))).toBe(true);
  });
});
```

- [ ] **Step 2: Run the tests — verify failures**

```bash
cd frontend && ng test --run-once
```

Expected: `'does not render a login button'` FAILS (login button is still in the template). `'shows a logout button when authenticated'` PASSES (logout branch already exists). The old `'shows a login button when unauthenticated'` test no longer exists — no false positive.

---

### Task 2: Remove the Login button and `login()` method

**Files:**
- Modify: `frontend/src/app/app.html`
- Modify: `frontend/src/app/app.ts`

- [ ] **Step 1: Replace `app.html` — remove `@else` branch**

Replace the full file content with:

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
  }
</main>

<router-outlet />
```

- [ ] **Step 2: Replace `app.ts` — remove `login()` method**

Replace the full file content with:

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
    this.authenticated().isAuthenticated ? `${this.apiUrl()}/users/me` : undefined,
  );

  logout(): void {
    this.oidc.logoff().subscribe();
  }
}
```

- [ ] **Step 3: Run tests — verify all pass**

```bash
cd frontend && ng test --run-once
```

Expected: all tests pass, including `'does not render a login button'`.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/app/app.spec.ts frontend/src/app/app.html frontend/src/app/app.ts
git commit -m "feat: remove manual login button — auto-login handled by app initializer"
```

---

### Task 3: Replace `withAppInitializerAuthCheck()` with custom auto-login initializer

This is the core change. `checkAuth()` processes the OAuth callback URL (if the user is returning from Keycloak with `?code=...&state=...`) or restores an existing session. If neither applies, it returns `isAuthenticated: false` and we redirect immediately.

The initializer returns an Observable (Angular's `APP_INITIALIZER` accepts both Observables and Promises). In the unauthenticated branch: `authorize()` triggers the browser redirect to Keycloak and `stsCallback$` is returned as the blocking observable — it never emits in this context because the page is already navigating away, which is the intended behavior. On the next boot (callback URL), `checkAuth()` returns `isAuthenticated: true` and the initializer completes via `of(void 0)`.

**Files:**
- Modify: `frontend/src/app/app.config.ts`

- [ ] **Step 1: Replace `app.config.ts` with the new initializer**

```typescript
import {
  ApplicationConfig,
  inject,
  provideAppInitializer,
  provideBrowserGlobalErrorListeners,
} from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { HttpClient, provideHttpClient, withFetch, withInterceptors } from '@angular/common/http';
import {
  authInterceptor,
  OidcSecurityService,
  provideAuth,
  StsConfigHttpLoader,
  StsConfigLoader,
} from 'angular-auth-oidc-client';
import { of, switchMap } from 'rxjs';
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
    provideAuth({
      loader: {
        provide: StsConfigLoader,
        useFactory: httpLoaderFactory,
        deps: [HttpClient],
      },
    }),
    provideAppInitializer(() => {
      const oidc = inject(OidcSecurityService);
      return oidc.checkAuth().pipe(
        switchMap(({ isAuthenticated }) => {
          if (isAuthenticated) {
            return of(void 0 as void);
          }
          oidc.authorize();
          return oidc.stsCallback$.pipe(map(() => void 0 as void));
        }),
      );
    }),
  ],
};
```

Key changes from the original:
- `withAppInitializerAuthCheck` removed from the `angular-auth-oidc-client` import and from `provideAuth(...)`.
- `OidcSecurityService` added to the `angular-auth-oidc-client` import.
- `of`, `switchMap` added from `rxjs`.
- New Observable-based `provideAppInitializer` block added after `provideAuth(...)`.
- Uses `stsCallback$` (library-native observable) instead of a never-resolving Promise to block initialization while the browser navigates to Keycloak.

- [ ] **Step 2: Run tests — verify all still pass**

```bash
cd frontend && ng test --run-once
```

Expected: all tests pass. The `app.config.ts` providers are not loaded in unit tests (components mock `OidcSecurityService` directly), so this verifies no unintended regressions.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/app/app.config.ts
git commit -m "feat: auto-redirect to Keycloak on app load via APP_INITIALIZER"
```

---

### Task 4: Update README — Authentication Flow section

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add auto-redirect note to the Authentication Flow section**

In `README.md`, locate the `### Authentication Flow` section under `## Features`. After the code block that shows the auth flow, add this paragraph (before the "On the first successful authenticated request…" sentence):

```markdown
**The app automatically redirects unauthenticated users to Keycloak on load.** There is no manual login button — if a user is not authenticated when the Angular app initializes, it calls `oidc.authorize()` and the browser navigates to Keycloak immediately. After a successful login, Keycloak redirects back to the app and the OIDC library completes the token exchange transparently.
```

The section should look like this after the edit:

```markdown
### Authentication Flow

Authentication is handled entirely by Keycloak using the **PKCE (Proof Key for Code Exchange)** flow — no custom login forms exist in the application.

\`\`\`
User → Angular SPA → Keycloak (PKCE login) → JWT issued
JWT → Angular HTTP interceptor → Authorization: Bearer <token> on all API requests
FastAPI → validates JWT signature locally via Keycloak JWKS endpoint (no roundtrip per request)
\`\`\`

**The app automatically redirects unauthenticated users to Keycloak on load.** There is no manual login button — if a user is not authenticated when the Angular app initializes, it calls `oidc.authorize()` and the browser navigates to Keycloak immediately. After a successful login, Keycloak redirects back to the app and the OIDC library completes the token exchange transparently.

On the first successful authenticated request to `GET /users/me`, the user is automatically created in the application database using the `sub` claim from the JWT. No separate registration step is required.
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: document auto-login redirect behavior in auth flow section"
```

---

## Self-Review

**Spec coverage:**
- ✅ `withAppInitializerAuthCheck()` replaced with custom initializer → Task 3
- ✅ Calls `checkAuth()` first (handles callback and session restore) → Task 3
- ✅ If not authenticated → `authorize()` + never-resolving promise → Task 3
- ✅ Login button removed from template → Task 2
- ✅ `login()` method removed from component → Task 2
- ✅ README updated → Task 4
- ✅ All four auth flows (first visit, callback return, existing session, expired token) handled by `checkAuth()` + the conditional `authorize()` call → Task 3

**Placeholder scan:** No TBDs, no "add error handling" vague steps, all code blocks complete.

**Type consistency:**
- `OidcSecurityService` referenced in Task 3 (`app.config.ts`) and Task 1/2 mocks — same type throughout.
- `firstValueFrom(oidc.checkAuth())` returns `LoginResponse` (from the library); `.isAuthenticated` is a boolean field on `LoginResponse` — consistent with how `authenticated()` signal is checked in the component.
- `logoff()` returns `Observable<unknown>`; `.subscribe()` call in `app.ts` is correct.
