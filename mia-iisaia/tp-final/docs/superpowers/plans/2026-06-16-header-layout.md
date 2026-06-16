# Header Layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a persistent Angular Material toolbar to the app — visible on all authenticated pages — with nav dropdown, dynamic page title, and a user avatar dropdown with logout.

**Architecture:** A new `AppShell` component in `shared/` becomes the parent route at `''`. It renders `AppHeaderComponent` (also in `shared/`) above a `<router-outlet>`. `App` stays a pure router shell. The page title is derived from the active route's `title` field by traversing `Router.routerState.snapshot`. User info (username, email) comes from `OidcSecurityService.userData` signal. Logout moves from `PortalPage` to the header.

**Tech Stack:** Angular 22, TypeScript, Angular Material (`MatToolbar`, `MatButton`, `MatIcon`, `MatMenu`, `MatDivider`), `angular-auth-oidc-client` v21, RxJS, Vitest (`ng test`)

---

## File Map

**Create:**
- `frontend/src/app/shared/components/app-header/app-header.spec.ts`
- `frontend/src/app/shared/components/app-header/app-header.ts`
- `frontend/src/app/shared/components/app-header/app-header.html`
- `frontend/src/app/shared/components/app-header/app-header.scss`
- `frontend/src/app/shared/components/app-shell/app-shell.spec.ts`
- `frontend/src/app/shared/components/app-shell/app-shell.ts`
- `frontend/src/app/shared/components/app-shell/app-shell.html`
- `frontend/src/app/shared/components/app-shell/app-shell.scss`

**Modify:**
- `frontend/src/app/app.routes.ts`
- `frontend/src/app/features/portal/portal.routes.ts`
- `frontend/src/app/features/portal/pages/portal-page/portal-page.spec.ts`
- `frontend/src/app/features/portal/pages/portal-page/portal-page.ts`
- `frontend/src/app/features/portal/pages/portal-page/portal-page.html`

**Delete:**
- `frontend/src/app/shared/.gitkeep`

---

## Task 1: Create AppHeaderComponent (TDD)

**Files:**
- Create: `frontend/src/app/shared/components/app-header/app-header.spec.ts`
- Create: `frontend/src/app/shared/components/app-header/app-header.ts`
- Create: `frontend/src/app/shared/components/app-header/app-header.html`
- Create: `frontend/src/app/shared/components/app-header/app-header.scss`

- [ ] **Step 1: Write the failing tests**

Create `frontend/src/app/shared/components/app-header/app-header.spec.ts`:

```typescript
import { TestBed } from '@angular/core/testing';
import { NavigationEnd, provideRouter, Router } from '@angular/router';
import { signal } from '@angular/core';
import { BehaviorSubject, of } from 'rxjs';
import { OidcSecurityService } from 'angular-auth-oidc-client';
import { OverlayContainer } from '@angular/cdk/overlay';
import { AppHeaderComponent } from './app-header';

const mockRouter = {
  events: new BehaviorSubject<unknown>(new NavigationEnd(0, '/', '/')),
  routerState: {
    snapshot: {
      root: {
        firstChild: { firstChild: null, title: 'Portal' },
        title: undefined,
      },
    },
  },
  navigate: () => Promise.resolve(true),
  navigateByUrl: () => Promise.resolve(true),
  createUrlTree: (_commands: unknown[]) => ({ toString: () => '/' }),
  serializeUrl: () => '/',
  isActive: () => false,
  url: '/',
};

let logoffCalled = false;

const mockOidc = {
  userData: signal({
    userData: { preferred_username: 'alice', email: 'alice@example.com' },
    allUserData: [],
  }),
  logoff: () => {
    logoffCalled = true;
    return of(null);
  },
};

describe('AppHeaderComponent', () => {
  let overlayContainer: OverlayContainer;

  beforeEach(async () => {
    logoffCalled = false;
    await TestBed.configureTestingModule({
      imports: [AppHeaderComponent],
      providers: [
        provideRouter([]),
        { provide: Router, useValue: mockRouter },
        { provide: OidcSecurityService, useValue: mockOidc },
      ],
    }).compileComponents();
    overlayContainer = TestBed.inject(OverlayContainer);
  });

  afterEach(() => {
    overlayContainer.ngOnDestroy();
  });

  it('should create', () => {
    const fixture = TestBed.createComponent(AppHeaderComponent);
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('shows the active route title in the toolbar', () => {
    const fixture = TestBed.createComponent(AppHeaderComponent);
    fixture.detectChanges();
    expect((fixture.nativeElement as HTMLElement).textContent).toContain('Portal');
  });

  it('shows the user initial in the avatar button', () => {
    const fixture = TestBed.createComponent(AppHeaderComponent);
    fixture.detectChanges();
    const avatar = (fixture.nativeElement as HTMLElement).querySelector('.avatar-initial');
    expect(avatar?.textContent?.trim()).toBe('A');
  });

  it('user dropdown shows email and Cerrar sesión', async () => {
    const fixture = TestBed.createComponent(AppHeaderComponent);
    fixture.detectChanges();
    const userBtn = (fixture.nativeElement as HTMLElement).querySelector(
      '[aria-label^="Cuenta de"]',
    ) as HTMLButtonElement;
    userBtn.click();
    fixture.detectChanges();
    await fixture.whenStable();
    const overlay = overlayContainer.getContainerElement();
    expect(overlay.textContent).toContain('alice@example.com');
    expect(overlay.textContent).toContain('Cerrar sesión');
  });

  it('clicking Cerrar sesión calls logoff', async () => {
    const fixture = TestBed.createComponent(AppHeaderComponent);
    fixture.detectChanges();
    const userBtn = (fixture.nativeElement as HTMLElement).querySelector(
      '[aria-label^="Cuenta de"]',
    ) as HTMLButtonElement;
    userBtn.click();
    fixture.detectChanges();
    await fixture.whenStable();
    const cerrarBtn = overlayContainer
      .getContainerElement()
      .querySelector('button[mat-menu-item]') as HTMLButtonElement;
    cerrarBtn.click();
    expect(logoffCalled).toBe(true);
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd frontend && ng test
```

Expected: TypeScript compile error — `Cannot find module './app-header'`. Valid red state.

- [ ] **Step 3: Create app-header.ts**

Create `frontend/src/app/shared/components/app-header/app-header.ts`:

```typescript
import { Component, computed, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { NavigationEnd, Router, RouterLink } from '@angular/router';
import { filter, map, startWith } from 'rxjs';
import { OidcSecurityService } from 'angular-auth-oidc-client';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatMenuModule } from '@angular/material/menu';
import { MatDividerModule } from '@angular/material/divider';

@Component({
  selector: 'app-header',
  imports: [
    RouterLink,
    MatToolbarModule,
    MatButtonModule,
    MatIconModule,
    MatMenuModule,
    MatDividerModule,
  ],
  templateUrl: './app-header.html',
  styleUrl: './app-header.scss',
})
export class AppHeaderComponent {
  private readonly router = inject(Router);
  private readonly oidc = inject(OidcSecurityService);

  private getLeafTitle(): string {
    let route = this.router.routerState.snapshot.root;
    while (route.firstChild) route = route.firstChild;
    return route.title ?? '';
  }

  protected readonly pageTitle = toSignal(
    this.router.events.pipe(
      filter((e) => e instanceof NavigationEnd),
      startWith(null),
      map(() => this.getLeafTitle()),
    ),
    { initialValue: '' },
  );

  protected readonly username = computed(
    () => (this.oidc.userData().userData?.preferred_username as string) ?? '',
  );

  protected readonly email = computed(
    () => (this.oidc.userData().userData?.email as string) ?? '',
  );

  protected readonly initial = computed(() => {
    const name = this.username();
    return name ? name[0].toUpperCase() : '?';
  });

  protected readonly navItems = [{ label: 'Portal', path: '/' }];

  protected logout(): void {
    this.oidc.logoff().subscribe();
  }
}
```

- [ ] **Step 4: Create app-header.html**

Create `frontend/src/app/shared/components/app-header/app-header.html`:

```html
<mat-toolbar color="primary">
  <button
    mat-icon-button
    [matMenuTriggerFor]="navMenu"
    aria-label="Abrir menú de navegación"
  >
    <mat-icon>menu</mat-icon>
  </button>

  <span class="page-title">{{ pageTitle() }}</span>

  <span class="spacer"></span>

  <button
    mat-icon-button
    [matMenuTriggerFor]="userMenu"
    [attr.aria-label]="'Cuenta de ' + username()"
    class="avatar-btn"
  >
    <span class="avatar-initial">{{ initial() }}</span>
  </button>
</mat-toolbar>

<mat-menu #navMenu="matMenu">
  @for (item of navItems; track item.path) {
    <a mat-menu-item [routerLink]="item.path">{{ item.label }}</a>
  }
</mat-menu>

<mat-menu #userMenu="matMenu">
  <div class="user-menu-header" (click)="$event.stopPropagation()">
    <span class="user-menu-name">{{ username() }}</span>
    <span class="user-menu-email">{{ email() }}</span>
  </div>
  <mat-divider />
  <button mat-menu-item (click)="logout()">
    <mat-icon>logout</mat-icon>
    Cerrar sesión
  </button>
</mat-menu>
```

- [ ] **Step 5: Create app-header.scss**

Create `frontend/src/app/shared/components/app-header/app-header.scss`:

```scss
.spacer {
  flex: 1 1 auto;
}

.page-title {
  font-size: 18px;
  font-weight: 500;
  margin-left: 8px;
}

.avatar-btn .avatar-initial {
  font-weight: 600;
  font-size: 15px;
}

.user-menu-header {
  padding: 12px 16px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.12);
  display: flex;
  flex-direction: column;
  gap: 2px;
  cursor: default;

  .user-menu-name {
    font-weight: 600;
    font-size: 14px;
  }

  .user-menu-email {
    font-size: 12px;
    color: rgba(0, 0, 0, 0.6);
  }
}
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
cd frontend && ng test
```

Expected: all 5 `AppHeaderComponent` tests PASS alongside existing tests.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/app/shared/components/app-header/
git commit -m "feat: add AppHeaderComponent to shared"
```

---

## Task 2: Create AppShell (TDD)

**Files:**
- Create: `frontend/src/app/shared/components/app-shell/app-shell.spec.ts`
- Create: `frontend/src/app/shared/components/app-shell/app-shell.ts`
- Create: `frontend/src/app/shared/components/app-shell/app-shell.html`
- Create: `frontend/src/app/shared/components/app-shell/app-shell.scss`

- [ ] **Step 1: Write the failing tests**

Create `frontend/src/app/shared/components/app-shell/app-shell.spec.ts`:

```typescript
import { TestBed } from '@angular/core/testing';
import { NavigationEnd, provideRouter, Router } from '@angular/router';
import { signal } from '@angular/core';
import { BehaviorSubject, of } from 'rxjs';
import { OidcSecurityService } from 'angular-auth-oidc-client';
import { AppShell } from './app-shell';

const mockRouter = {
  events: new BehaviorSubject<unknown>(new NavigationEnd(0, '/', '/')),
  routerState: {
    snapshot: {
      root: { firstChild: null, title: '' },
    },
  },
  navigate: () => Promise.resolve(true),
  navigateByUrl: () => Promise.resolve(true),
  createUrlTree: (_commands: unknown[]) => ({ toString: () => '/' }),
  serializeUrl: () => '/',
  isActive: () => false,
  url: '/',
};

const mockOidc = {
  userData: signal({ userData: { preferred_username: 'alice', email: '' }, allUserData: [] }),
  logoff: () => of(null),
};

describe('AppShell', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AppShell],
      providers: [
        provideRouter([]),
        { provide: Router, useValue: mockRouter },
        { provide: OidcSecurityService, useValue: mockOidc },
      ],
    }).compileComponents();
  });

  it('should create', () => {
    const fixture = TestBed.createComponent(AppShell);
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('renders app-header', () => {
    const fixture = TestBed.createComponent(AppShell);
    fixture.detectChanges();
    expect((fixture.nativeElement as HTMLElement).querySelector('app-header')).toBeTruthy();
  });

  it('renders router-outlet', () => {
    const fixture = TestBed.createComponent(AppShell);
    fixture.detectChanges();
    expect((fixture.nativeElement as HTMLElement).querySelector('router-outlet')).toBeTruthy();
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd frontend && ng test
```

Expected: TypeScript compile error — `Cannot find module './app-shell'`. Valid red state.

- [ ] **Step 3: Create app-shell.ts**

Create `frontend/src/app/shared/components/app-shell/app-shell.ts`:

```typescript
import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { AppHeaderComponent } from '../app-header/app-header';

@Component({
  selector: 'app-shell',
  imports: [RouterOutlet, AppHeaderComponent],
  templateUrl: './app-shell.html',
})
export class AppShell {}
```

- [ ] **Step 4: Create app-shell.html**

Create `frontend/src/app/shared/components/app-shell/app-shell.html`:

```html
<app-header />
<router-outlet />
```

- [ ] **Step 5: Create app-shell.scss**

Create `frontend/src/app/shared/components/app-shell/app-shell.scss` — empty file (no styles needed at this level).

- [ ] **Step 6: Run tests to verify they pass**

```bash
cd frontend && ng test
```

Expected: all 3 `AppShell` tests PASS alongside all previous tests.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/app/shared/components/app-shell/
git commit -m "feat: add AppShell layout component to shared"
```

---

## Task 3: Wire routes, update portal-page, cleanup

**Files:**
- Modify: `frontend/src/app/app.routes.ts`
- Modify: `frontend/src/app/features/portal/portal.routes.ts`
- Modify: `frontend/src/app/features/portal/pages/portal-page/portal-page.spec.ts`
- Modify: `frontend/src/app/features/portal/pages/portal-page/portal-page.ts`
- Modify: `frontend/src/app/features/portal/pages/portal-page/portal-page.html`
- Delete: `frontend/src/app/shared/.gitkeep`

- [ ] **Step 1: Update portal-page.spec.ts**

The existing "shows a logout button when authenticated" test becomes invalid because logout moves to the header. Remove that test and the now-unnecessary `logoff` mock. Replace `portal-page.spec.ts` with:

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

  it('renders no user card when unauthenticated', () => {
    const fixture = TestBed.createComponent(PortalPage);
    fixture.detectChanges();
    expect(
      (fixture.nativeElement as HTMLElement).querySelector('app-user-card'),
    ).toBeNull();
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

  it('renders user card when authenticated', () => {
    const fixture = TestBed.createComponent(PortalPage);
    fixture.detectChanges();
    expect(
      (fixture.nativeElement as HTMLElement).querySelector('app-user-card'),
    ).toBeTruthy();
  });
});
```

- [ ] **Step 2: Run tests to confirm updated spec passes with current implementation**

```bash
cd frontend && ng test
```

Expected: all tests pass. The removed logout test is no longer checked; the new "renders user card" test passes because `<app-user-card>` is already in the portal-page template.

- [ ] **Step 3: Update portal-page.ts — remove logout**

Replace `frontend/src/app/features/portal/pages/portal-page/portal-page.ts`:

```typescript
import { Component, inject } from '@angular/core';
import { httpResource } from '@angular/common/http';
import { OidcSecurityService } from 'angular-auth-oidc-client';
import { ConfigService } from '../../../../core/config.service';
import { UserCardComponent } from '../../components/user-card/user-card';

@Component({
  selector: 'app-portal-page',
  imports: [UserCardComponent],
  templateUrl: './portal-page.html',
  styleUrl: './portal-page.scss',
})
export class PortalPage {
  private readonly config = inject(ConfigService);
  private readonly oidc = inject(OidcSecurityService);

  protected readonly authenticated = this.oidc.authenticated;

  protected readonly me = httpResource<unknown>(() =>
    this.authenticated().isAuthenticated ? `${this.config.apiUrl()}/users/me` : undefined,
  );
}
```

- [ ] **Step 4: Update portal-page.html — remove logout button**

Replace `frontend/src/app/features/portal/pages/portal-page/portal-page.html`:

```html
<main>
  @if (authenticated().isAuthenticated) {
    <app-user-card [user]="me.value()" [isLoading]="me.isLoading()" [error]="me.error()" />
  }
</main>
```

- [ ] **Step 5: Run all tests to confirm nothing broke**

```bash
cd frontend && ng test
```

Expected: all tests pass.

- [ ] **Step 6: Update app.routes.ts — wrap routes under AppShell**

Replace `frontend/src/app/app.routes.ts`:

```typescript
import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./shared/components/app-shell/app-shell').then((m) => m.AppShell),
    children: [
      {
        path: '',
        loadChildren: () =>
          import('./features/portal/portal.routes').then((m) => m.portalRoutes),
      },
    ],
  },
];
```

- [ ] **Step 7: Update portal.routes.ts — add title**

Replace `frontend/src/app/features/portal/portal.routes.ts`:

```typescript
import { Routes } from '@angular/router';

export const portalRoutes: Routes = [
  {
    path: '',
    title: 'Portal',
    loadComponent: () =>
      import('./pages/portal-page/portal-page').then((m) => m.PortalPage),
  },
];
```

- [ ] **Step 8: Run all tests**

```bash
cd frontend && ng test
```

Expected: all tests pass. Total: 2 (App) + 5 (AppHeader) + 3 (AppShell) + 4 (UserCard) + 3 (PortalPage) = 17 tests.

- [ ] **Step 9: Remove .gitkeep**

```bash
git rm frontend/src/app/shared/.gitkeep
```

- [ ] **Step 10: Commit**

`git rm` in Step 9 already staged the `.gitkeep` deletion. The `git add` below stages the route and portal-page changes. Both go into the same commit.

```bash
git add frontend/src/app/app.routes.ts \
        frontend/src/app/features/portal/portal.routes.ts \
        frontend/src/app/features/portal/pages/portal-page/portal-page.ts \
        frontend/src/app/features/portal/pages/portal-page/portal-page.html \
        frontend/src/app/features/portal/pages/portal-page/portal-page.spec.ts
git commit -m "feat: wire AppShell as layout route and move logout to header"
```
