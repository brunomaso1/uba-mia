# Frontend Feature Structure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish a feature-based folder structure for the Angular frontend and implement the portal feature as an authenticated landing page at route `/`.

**Architecture:** `App` becomes a pure router shell; a new `features/portal/` module lazy-loads `PortalPage` at route `''`. The portal page fetches the authenticated user from `/users/me` and renders it via `UserCardComponent`. A `shared/` directory is created empty for future cross-feature reuse.

**Tech Stack:** Angular 22, TypeScript, Angular Material (MatCard, MatButton, MatProgressSpinner), angular-auth-oidc-client, Vitest (via `ng test`)

---

## File Map

**Create:**
- `frontend/src/app/shared/.gitkeep`
- `frontend/src/app/features/portal/portal.routes.ts`
- `frontend/src/app/features/portal/components/user-card/user-card.ts`
- `frontend/src/app/features/portal/components/user-card/user-card.html`
- `frontend/src/app/features/portal/components/user-card/user-card.scss`
- `frontend/src/app/features/portal/components/user-card/user-card.spec.ts`
- `frontend/src/app/features/portal/pages/portal-page/portal-page.ts`
- `frontend/src/app/features/portal/pages/portal-page/portal-page.html`
- `frontend/src/app/features/portal/pages/portal-page/portal-page.scss`
- `frontend/src/app/features/portal/pages/portal-page/portal-page.spec.ts`
- `README.md` (at `tp-final/` root)

**Modify:**
- `frontend/src/app/app.routes.ts`
- `frontend/src/app/app.ts`
- `frontend/src/app/app.spec.ts`
- `.claude/rules/frontend-rules.md`

**Delete:**
- `frontend/src/app/app.html` (replaced by inline template)

---

### Task 1: Scaffold folder structure and route config

**Files:**
- Create: `frontend/src/app/shared/.gitkeep`
- Create: `frontend/src/app/features/portal/portal.routes.ts`
- Modify: `frontend/src/app/app.routes.ts`

- [ ] **Step 1: Create shared directory placeholder**

Create an empty file at `frontend/src/app/shared/.gitkeep`. No content needed — it exists only to let git track the directory.

- [ ] **Step 2: Create portal route config**

Create `frontend/src/app/features/portal/portal.routes.ts`:

```typescript
import { Routes } from '@angular/router';

export const portalRoutes: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./pages/portal-page/portal-page').then((m) => m.PortalPage),
  },
];
```

- [ ] **Step 3: Wire app routes to lazy-load portal**

Replace `frontend/src/app/app.routes.ts`:

```typescript
import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    loadChildren: () =>
      import('./features/portal/portal.routes').then((m) => m.portalRoutes),
  },
];
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/app/shared/.gitkeep \
        frontend/src/app/features/portal/portal.routes.ts \
        frontend/src/app/app.routes.ts
git commit -m "feat: scaffold feature folder structure and portal route config"
```

---

### Task 2: Create UserCardComponent (TDD)

**Files:**
- Create: `frontend/src/app/features/portal/components/user-card/user-card.spec.ts`
- Create: `frontend/src/app/features/portal/components/user-card/user-card.ts`
- Create: `frontend/src/app/features/portal/components/user-card/user-card.html`
- Create: `frontend/src/app/features/portal/components/user-card/user-card.scss`

- [ ] **Step 1: Write the failing tests**

Create `frontend/src/app/features/portal/components/user-card/user-card.spec.ts`:

```typescript
import { TestBed } from '@angular/core/testing';
import { UserCardComponent } from './user-card';

describe('UserCardComponent', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [UserCardComponent],
    }).compileComponents();
  });

  it('should create', () => {
    const fixture = TestBed.createComponent(UserCardComponent);
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('shows a loading spinner when isLoading is true', () => {
    const fixture = TestBed.createComponent(UserCardComponent);
    fixture.componentRef.setInput('isLoading', true);
    fixture.detectChanges();
    expect(
      (fixture.nativeElement as HTMLElement).querySelector('mat-spinner'),
    ).toBeTruthy();
  });

  it('shows error message when error is set', () => {
    const fixture = TestBed.createComponent(UserCardComponent);
    fixture.componentRef.setInput('error', new Error('fail'));
    fixture.detectChanges();
    const alert = (fixture.nativeElement as HTMLElement).querySelector('[role="alert"]');
    expect(alert?.textContent).toContain('Could not load the authenticated user.');
  });

  it('shows user data when loaded', () => {
    const fixture = TestBed.createComponent(UserCardComponent);
    fixture.componentRef.setInput('user', { id: 1, email: 'alice@example.com' });
    fixture.detectChanges();
    expect(
      (fixture.nativeElement as HTMLElement).querySelector('pre')?.textContent,
    ).toContain('alice@example.com');
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd frontend && ng test
```

Expected: TypeScript compile error — `Cannot find module './user-card'`. This is the valid "red" state.

- [ ] **Step 3: Create the component**

Create `frontend/src/app/features/portal/components/user-card/user-card.ts`:

```typescript
import { Component, input } from '@angular/core';
import { JsonPipe } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

@Component({
  selector: 'app-user-card',
  imports: [JsonPipe, MatCardModule, MatProgressSpinnerModule],
  templateUrl: './user-card.html',
  styleUrl: './user-card.scss',
})
export class UserCardComponent {
  readonly user = input<unknown>(undefined);
  readonly isLoading = input<boolean>(false);
  readonly error = input<unknown>(undefined);
}
```

Create `frontend/src/app/features/portal/components/user-card/user-card.html`:

```html
@if (isLoading()) {
  <mat-spinner diameter="32" aria-label="Loading user…" />
} @else if (error()) {
  <p role="alert">Could not load the authenticated user.</p>
} @else if (user(); as userData) {
  <mat-card>
    <mat-card-header>
      <mat-card-title>Authenticated User</mat-card-title>
    </mat-card-header>
    <mat-card-content>
      <pre>{{ userData | json }}</pre>
    </mat-card-content>
  </mat-card>
}
```

Create `frontend/src/app/features/portal/components/user-card/user-card.scss` (empty file — no styles yet).

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd frontend && ng test
```

Expected: all 4 `UserCardComponent` tests PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/app/features/portal/components/
git commit -m "feat: add UserCardComponent to portal feature"
```

---

### Task 3: Create PortalPage (TDD)

**Files:**
- Create: `frontend/src/app/features/portal/pages/portal-page/portal-page.spec.ts`
- Create: `frontend/src/app/features/portal/pages/portal-page/portal-page.ts`
- Create: `frontend/src/app/features/portal/pages/portal-page/portal-page.html`
- Create: `frontend/src/app/features/portal/pages/portal-page/portal-page.scss`

- [ ] **Step 1: Write the failing tests**

Create `frontend/src/app/features/portal/pages/portal-page/portal-page.spec.ts`:

```typescript
import { of } from 'rxjs';
import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideHttpClient, withFetch } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { OidcSecurityService } from 'angular-auth-oidc-client';
import { PortalPage } from './portal-page';

const unauthenticatedOidc = {
  authenticated: signal({ isAuthenticated: false }),
};

const authenticatedOidc = {
  authenticated: signal({ isAuthenticated: true }),
  logoff: () => of(null),
};

describe('PortalPage — unauthenticated', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PortalPage],
      providers: [
        provideHttpClient(withFetch()),
        provideHttpClientTesting(),
        { provide: OidcSecurityService, useValue: unauthenticatedOidc },
      ],
    }).compileComponents();
  });

  it('should create', () => {
    const fixture = TestBed.createComponent(PortalPage);
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('renders no logout button when unauthenticated', () => {
    const fixture = TestBed.createComponent(PortalPage);
    fixture.detectChanges();
    const buttons = Array.from(
      (fixture.nativeElement as HTMLElement).querySelectorAll('button'),
    );
    expect(buttons.some((b) => b.textContent?.trim() === 'Logout')).toBe(false);
  });
});

describe('PortalPage — authenticated', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PortalPage],
      providers: [
        provideHttpClient(withFetch()),
        provideHttpClientTesting(),
        { provide: OidcSecurityService, useValue: authenticatedOidc },
      ],
    }).compileComponents();
  });

  it('shows a logout button when authenticated', () => {
    const fixture = TestBed.createComponent(PortalPage);
    fixture.detectChanges();
    const buttons = Array.from(
      (fixture.nativeElement as HTMLElement).querySelectorAll('button'),
    );
    expect(buttons.some((b) => b.textContent?.trim() === 'Logout')).toBe(true);
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd frontend && ng test
```

Expected: TypeScript compile error — `Cannot find module './portal-page'`. Valid "red" state.

- [ ] **Step 3: Create the page component**

Create `frontend/src/app/features/portal/pages/portal-page/portal-page.ts`:

```typescript
import { Component, inject } from '@angular/core';
import { httpResource } from '@angular/common/http';
import { OidcSecurityService } from 'angular-auth-oidc-client';
import { MatButtonModule } from '@angular/material/button';
import { ConfigService } from '../../../../core/config.service';
import { UserCardComponent } from '../../components/user-card/user-card';

@Component({
  selector: 'app-portal-page',
  imports: [MatButtonModule, UserCardComponent],
  templateUrl: './portal-page.html',
  styleUrl: './portal-page.scss',
})
export class PortalPage {
  private readonly config = inject(ConfigService);
  private readonly oidc = inject(OidcSecurityService);

  protected readonly authenticated = this.oidc.authenticated;

  protected readonly me = httpResource<unknown>(() =>
    this.authenticated().isAuthenticated
      ? `${this.config.apiUrl()}/users/me`
      : undefined,
  );

  protected logout(): void {
    this.oidc.logoff().subscribe();
  }
}
```

Create `frontend/src/app/features/portal/pages/portal-page/portal-page.html`:

```html
<main>
  @if (authenticated().isAuthenticated) {
    <app-user-card
      [user]="me.value()"
      [isLoading]="me.isLoading()"
      [error]="me.error()"
    />
    <button mat-button type="button" (click)="logout()">Logout</button>
  }
</main>
```

Create `frontend/src/app/features/portal/pages/portal-page/portal-page.scss` (empty file — no styles yet).

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd frontend && ng test
```

Expected: all 3 `PortalPage` tests PASS alongside the 4 `UserCardComponent` tests.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/app/features/portal/pages/
git commit -m "feat: add PortalPage to portal feature"
```

---

### Task 4: Simplify App to a pure router shell (TDD refactor)

**Files:**
- Modify: `frontend/src/app/app.spec.ts`
- Modify: `frontend/src/app/app.ts`
- Delete: `frontend/src/app/app.html`

- [ ] **Step 1: Replace app.spec.ts with tests for the simplified shell**

Replace the entire content of `frontend/src/app/app.spec.ts`:

```typescript
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { App } from './app';

describe('App', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [provideRouter([])],
    }).compileComponents();
  });

  it('should create the app', () => {
    const fixture = TestBed.createComponent(App);
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('renders a router-outlet', () => {
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();
    expect(
      (fixture.nativeElement as HTMLElement).querySelector('router-outlet'),
    ).toBeTruthy();
  });
});
```

- [ ] **Step 2: Run tests to confirm new tests pass with current App**

```bash
cd frontend && ng test
```

Expected: all tests PASS (current `App` already has a `<router-outlet>` in its template). This confirms the new tests are valid before we simplify the implementation.

- [ ] **Step 3: Simplify app.ts to an inline router shell**

Replace `frontend/src/app/app.ts`:

```typescript
import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet],
  template: '<router-outlet />',
})
export class App {}
```

- [ ] **Step 4: Delete app.html**

Delete `frontend/src/app/app.html` — it is no longer referenced (the component now uses an inline `template`).

- [ ] **Step 5: Run all tests**

```bash
cd frontend && ng test
```

Expected: all tests PASS (9 total: 2 App + 4 UserCard + 3 PortalPage).

- [ ] **Step 6: Commit**

```bash
git add frontend/src/app/app.ts frontend/src/app/app.spec.ts
git rm frontend/src/app/app.html
git commit -m "refactor: simplify App to pure router shell"
```

---

### Task 5: Update documentation

**Files:**
- Modify: `.claude/rules/frontend-rules.md`
- Create: `README.md` (at `tp-final/` root)

- [ ] **Step 1: Add folder structure section to frontend-rules.md**

Append the following section to `.claude/rules/frontend-rules.md` (before the trailing blank lines at the end of the file):

````markdown
## Folder Structure

The app is organized by feature under `src/app/`:

```
src/app/
├── core/       # App-wide infrastructure (ConfigService, auth plumbing)
├── shared/     # Reusable components, pipes, directives across features
└── features/
    └── <feature>/
        ├── components/          # Each component in its own subfolder (ts + html + scss + spec)
        ├── pages/               # Page components that compose feature components
        └── <feature>.routes.ts  # Lazy-loaded route config for this feature
```

**Structural rules:**
- Components always get a subfolder — a component's `.ts`, `.html`, `.scss`, and `.spec.ts` live together under `components/<name>/`.
- Single-file artifacts (one service, one model, one pipe) live directly at the feature root — no subfolder until a second file of that type is added.
- `shared/` fills as cross-feature needs emerge; nothing is pre-emptively placed there.
````

- [ ] **Step 2: Create README.md at the tp-final root**

Create `README.md` at `tp-final/`:

```markdown
# Expense App — TP Final

Multi-user expense management app built with Angular 22, FastAPI, Keycloak, and PostgreSQL.

## Services

| Service     | Port | Description                 |
|-------------|------|-----------------------------|
| Frontend    | 4200 | Angular SPA (Keycloak PKCE) |
| Backend     | 8000 | FastAPI REST API            |
| Keycloak    | 8080 | Auth server (OIDC/PKCE)     |
| App DB      | 5432 | PostgreSQL (app data)       |
| Keycloak DB | 5433 | PostgreSQL (Keycloak data)  |

## Quick start

```bash
docker compose up --build
```

Open [http://localhost:4200](http://localhost:4200). You will be redirected to Keycloak automatically. Log in with `alice / password` or `bob / password`.

## Frontend structure

```
frontend/src/app/
├── core/           # App-wide infrastructure (ConfigService, auth plumbing)
├── shared/         # Reusable components, pipes, directives
└── features/
    └── <feature>/
        ├── components/          # Standalone UI components (each in own subfolder)
        ├── pages/               # Page components (compose feature components)
        └── <feature>.routes.ts  # Lazy-loaded route config
```

Single-file artifacts (one service, one model, one pipe) live at the feature root — no subfolder until a second file of the same type is added.

## Features

### Portal (`/`)

Authenticated landing page. After Keycloak login, displays the current user's profile data fetched from `GET /users/me`. Provides a Logout button.

**Components:**
- `PortalPage` — main page; fetches the authenticated user via `httpResource`
- `UserCardComponent` — displays user data in a Material card; shows a loading spinner and error state
```

- [ ] **Step 3: Commit**

```bash
git add .claude/rules/frontend-rules.md README.md
git commit -m "docs: add feature folder structure rules and portal feature to README"
```
