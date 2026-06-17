---
name: scaffold-feature
description: >-
  Scaffold a new Angular 22 feature in this project following its exact folder
  and code conventions — a lazy-loaded routes file, an optional HttpClient
  service, page components, and child components, each with co-located
  ts+html+scss+spec, then wire the feature into app.routes.ts. Invoke when the
  user wants to create / add / start a new frontend feature, page, or section
  (e.g. "add a settings feature", "scaffold a balances page", "new feature for
  notifications").
---

# Scaffold a frontend feature

Generate a new feature under `frontend/src/app/features/<feature>/` that matches
the patterns already used in `groups/`, `expenses/`, and `portal/`. The goal is
code indistinguishable from what's already there — same imports, same idioms, same
test setup. Do not introduce new patterns.

## 1. Gather inputs

Confirm these before writing (ask only for what's missing — infer sensible defaults):

- **Feature name** in `kebab-case` (e.g. `balances`). Derive:
  - PascalCase base for class names (e.g. `Balances`).
  - `app-<name>` for selectors.
- **Route path** the feature mounts at under the app shell (e.g. `balances`).
- **Pages** to create (at least one; default a single landing page named
  `<feature>-page`).
- **Child components** to create now (optional — can be none).
- **Backend-backed?** If it fetches data, create a `<feature>.service.ts` and use
  `httpResource` in the page. If purely presentational, skip the service.

## 2. Create the folder structure

```
features/<feature>/
├── <feature>.routes.ts          # always
├── <feature>.service.ts         # only if backend-backed (single file, feature root)
├── pages/
│   └── <feature>-page/
│       ├── <feature>-page.ts
│       ├── <feature>-page.html
│       ├── <feature>-page.scss
│       └── <feature>-page.spec.ts
└── components/                  # only if there are child components
    └── <component>/
        ├── <component>.ts
        ├── <component>.html
        ├── <component>.scss
        └── <component>.spec.ts
```

Rules (from `.claude/rules/frontend-rules.md`):
- Every component/page gets its own subfolder with all four files together.
- Single-file artifacts (the one service) live at the feature root — no subfolder.

## 3. File templates

Replace `<feature>` (kebab), `<Feature>` (Pascal), `<page>` / `<Page>`,
`<component>` / `<Component>` accordingly. Page classes end in `Page`, components
end in `Component`. Use Spanish for user-facing `title`, labels, and `aria-label`
(matches the existing UI).

### `<feature>.routes.ts`

```ts
import { Routes } from '@angular/router';

export const <feature>Routes: Routes = [
  {
    path: '',
    title: '<Título en español>',
    loadComponent: () =>
      import('./pages/<page>/<page>').then((m) => m.<Page>),
  },
];
```

### `<feature>.service.ts` (only if backend-backed)

```ts
import { HttpClient } from '@angular/common/http';
import { Service, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { ConfigService } from '../../core/config.service';

export interface <Feature> {
  id: string;
  // ...fields returned by the backend
}

@Service()
export class <Feature>Service {
  private readonly http = inject(HttpClient);
  private readonly config = inject(ConfigService);

  private get base(): string {
    return `${this.config.apiUrl()}/<resource>`;
  }

  list(): Observable<<Feature>[]> {
    return this.http.get<<Feature>[]>(this.base);
  }
}
```

Notes:
- Use `@Service()` for singletons — NOT `@Injectable({ providedIn: 'root' })`.
- `config.apiUrl()` already includes the `/api/v1` prefix.

### `pages/<page>/<page>.ts`

```ts
import { Component, inject, signal } from '@angular/core';
import { httpResource } from '@angular/common/http';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { OidcSecurityService } from 'angular-auth-oidc-client';

import { ConfigService } from '../../../../core/config.service';
import { <Feature> } from '../../<feature>.service';

@Component({
  selector: 'app-<page>',
  imports: [MatProgressSpinnerModule],
  templateUrl: './<page>.html',
  styleUrl: './<page>.scss',
})
export class <Page> {
  private readonly config = inject(ConfigService);
  private readonly oidc = inject(OidcSecurityService);

  protected readonly authenticated = this.oidc.authenticated;

  // Only fetch once authenticated; httpResource manages loading/error state.
  protected readonly items = httpResource<<Feature>[]>(() =>
    this.authenticated().isAuthenticated ? `${this.config.apiUrl()}/<resource>` : undefined,
  );

  protected readonly busy = signal(false);
}
```

Notes:
- Do NOT set `standalone: true`, `changeDetection`, or
  `provideZonelessChangeDetection()` — all are defaults in v22.
- Use signals for local state; `httpResource` for data — never hand-rolled
  loading flags for fetches.
- For a presentational page, drop `httpResource`/`OidcSecurityService` and the
  service import.

### `pages/<page>/<page>.html`

```html
<div class="<page>-container">
  @if (items.isLoading()) {
    <div class="loading">
      <mat-spinner diameter="48" aria-label="Cargando…" />
    </div>
  } @else if (items.error()) {
    <p role="alert">No se pudieron cargar los datos.</p>
  } @else {
    @for (item of items.value() ?? []; track item.id) {
      <!-- render item -->
    } @empty {
      <p>No hay nada todavía.</p>
    }
  }
</div>
```

Notes:
- Native control flow (`@if` / `@for` / `@switch`); `track` always set; `style` /
  `class` bindings (never `ngClass` / `ngStyle`).
- **Always iterate `items.value() ?? []`, never `items.value()` directly** — an
  `httpResource` is `undefined` before its first load, and `@for` over `undefined`
  throws. The existing pages (`groups-page`, `group-expenses-page`) all use the
  `?? []` guard.
- Give the `<mat-spinner>` an `aria-label` (WCAG AA), and wrap it in a `.loading`
  div, matching the existing pages.

### `pages/<page>/<page>.scss`

```scss
:host {
  display: block;
}
```

Keep styles scoped; use CSS variables for theming; no global CSS.

### `pages/<page>/<page>.spec.ts`

```ts
import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideRouter } from '@angular/router';
import { OidcSecurityService } from 'angular-auth-oidc-client';

import { <Page> } from './<page>';
import { ConfigService } from '../../../../core/config.service';

describe('<Page>', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [<Page>],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        {
          provide: ConfigService,
          useValue: { apiUrl: () => 'http://localhost:8000/api/v1' },
        },
        {
          provide: OidcSecurityService,
          useValue: { authenticated: signal({ isAuthenticated: true }) },
        },
      ],
    }).compileComponents();
  });

  it('should create', () => {
    const fixture = TestBed.createComponent(<Page>);
    expect(fixture.componentInstance).toBeTruthy();
  });
});
```

### `components/<component>/<component>.ts` (only if requested)

```ts
import { Component, input, output, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';

import { <Feature> } from '../../<feature>.service';

@Component({
  selector: 'app-<component>',
  imports: [MatButtonModule, MatCardModule],
  templateUrl: './<component>.html',
  styleUrl: './<component>.scss',
})
export class <Component> {
  readonly item = input.required<<Feature>>();
  readonly selected = output<<Feature>>();

  protected readonly busy = signal(false);
}
```

Notes: `input()` / `input.required()` / `output()` functions (never decorators);
`inject()` over constructor injection; no `@HostBinding` / `@HostListener` (use the
`host` object instead).

The component's `.html`, `.scss`, and `.spec.ts` follow the same shape as the page's
(see `group-card` for a full real example with `setInput` + `vi.spyOn`).

## 4. Wire the feature into routing

Add a child route under the app shell in `frontend/src/app/app.routes.ts`,
matching the existing entries:

```ts
{
  path: '<route-path>',
  loadChildren: () =>
    import('./features/<feature>/<feature>.routes').then((m) => m.<feature>Routes),
},
```

Keep it inside the `app-shell` `children` array alongside `portal` and `groups`.

## 5. Verify

Run the new specs. Per project memory, `npx ng` segfaults here — use the local
binary directly:

```bash
cd frontend && node ./node_modules/@angular/cli/bin/ng.js test --include src/app/features/<feature>/**/*.spec.ts
```

Then report to the user: the files created, the route registered, and the test
result. Remind them the backend resource (`/api/v1/<resource>`) must exist for the
data fetch to work, if the feature is backend-backed.
