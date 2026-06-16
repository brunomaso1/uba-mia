# Header Layout — Design Spec

**Date:** 2026-06-16
**Status:** Approved

## Goal

Add a persistent application header (Angular Material toolbar) visible on all authenticated pages. The header provides navigation, the current page title, and user account actions.

## Architecture

```
App (pure router shell — unchanged)
└── AppShell  →  shared/components/app-shell/
    ├── AppHeaderComponent  →  shared/components/app-header/
    └── <router-outlet>
          └── PortalPage  →  features/portal/pages/portal-page/
```

`App` stays a pure router shell. `AppShell` is registered as the parent route at `''` and nests existing feature routes as children. This makes it trivial to add routes without the header in the future (e.g., error pages) — simply don't nest them under `AppShell`.

## New Components

### `AppShell` — `shared/components/app-shell/`

Layout-only component with no logic:

```html
<app-header />
<router-outlet />
```

### `AppHeaderComponent` — `shared/components/app-header/`

Standalone component that owns all toolbar logic.

**Template structure:**
```
mat-toolbar
├── [left]  icon-button (hamburger) → mat-menu with nav links
├── [center-left] span: current page title
└── [right] icon-button (avatar initials) → mat-menu with user info + logout
```

**Data sources:**

| Element | Source |
|---|---|
| Page title | `Router` NavigationEnd events → traverse to leaf route snapshot → `snapshot.title` |
| Avatar initials | `OidcSecurityService.userData` signal → `preferred_username` claim (first character, uppercased) |
| Email in dropdown | `OidcSecurityService.userData` signal → `email` claim |
| Logout action | `OidcSecurityService.logoff()` |
| Nav menu items | Static array `[{ label: 'Portal', path: '/' }]` — extended as features are added |

**Angular Material imports:** `MatToolbarModule`, `MatButtonModule`, `MatIconModule`, `MatMenuModule`

**Angular imports:** `RouterLink` (for nav menu items)

## Route Changes

### `app.routes.ts`

Wrap feature routes under `AppShell`:

```typescript
export const routes: Routes = [
  {
    path: '',
    loadComponent: () => import('./shared/components/app-shell/app-shell').then(m => m.AppShell),
    children: [
      {
        path: '',
        pathMatch: 'full',
        loadChildren: () => import('./features/portal/portal.routes').then(m => m.portalRoutes),
      },
    ],
  },
];
```

### `portal.routes.ts`

Add `title` to the route:

```typescript
export const portalRoutes: Routes = [
  {
    path: '',
    title: 'Portal',
    loadComponent: () => import('./pages/portal-page/portal-page').then(m => m.PortalPage),
  },
];
```

## Changes to Existing Files

- **`portal-page.ts`** — remove `logout()` method and `MatButtonModule` import. Keep `OidcSecurityService` injection (still needed for the `authenticated` signal), `authenticated`, and `me` httpResource.
- **`portal-page.html`** — remove `<button mat-button (click)="logout()">Logout</button>`. Keep the `@if` block and `<app-user-card>`.

## Testing

### `AppShell` spec
- Creates the component
- Renders `<app-header>`
- Renders `<router-outlet>`

### `AppHeader` spec

Mocked dependencies:
- `OidcSecurityService` — `userData` signal with `{ preferred_username: 'alice', email: 'alice@example.com' }`
- `Router` — mocked to emit `NavigationEnd`; route snapshot provides `title`

Test cases:
- Shows the active route title in the toolbar
- Shows the user's initial (uppercased first char of `preferred_username`) in the avatar button
- User dropdown contains the email address
- User dropdown contains a "Cerrar sesión" item
- Clicking "Cerrar sesión" calls `oidc.logoff()`

## Files

**Create:**
- `frontend/src/app/shared/components/app-shell/app-shell.ts`
- `frontend/src/app/shared/components/app-shell/app-shell.html`
- `frontend/src/app/shared/components/app-shell/app-shell.scss`
- `frontend/src/app/shared/components/app-shell/app-shell.spec.ts`
- `frontend/src/app/shared/components/app-header/app-header.ts`
- `frontend/src/app/shared/components/app-header/app-header.html`
- `frontend/src/app/shared/components/app-header/app-header.scss`
- `frontend/src/app/shared/components/app-header/app-header.spec.ts`

**Modify:**
- `frontend/src/app/app.routes.ts`
- `frontend/src/app/features/portal/portal.routes.ts`
- `frontend/src/app/features/portal/pages/portal-page/portal-page.ts`
- `frontend/src/app/features/portal/pages/portal-page/portal-page.html`
- `frontend/src/app/shared/.gitkeep` — remove (directory now has real content)

## Success Criteria

- `ng serve` starts without errors.
- The toolbar is visible on all pages (starting with PortalPage at `/`).
- The toolbar shows "Portal" as the title when at `/`.
- Clicking the avatar opens a dropdown with the username and email.
- Clicking "Cerrar sesión" logs out via Keycloak.
- Clicking the hamburger shows a dropdown with "Portal" linking to `/`.
- The portal-page no longer has its own logout button.
- `ng test` passes.
