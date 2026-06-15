# Frontend Feature Structure — Design Spec

**Date:** 2026-06-15
**Status:** Approved

## Goal

Establish a feature-based folder structure for the Angular frontend and implement the first feature: **portal**, an authenticated landing page that serves as the application entry point.

## Folder Structure

```
frontend/src/app/
├── core/                     # App-wide infrastructure (config, auth plumbing)
├── shared/                   # Reusable components, pipes, directives (starts empty)
└── features/
    └── portal/               # First feature — authenticated landing
        ├── components/
        │   └── user-card/    # Displays authenticated user info
        ├── pages/
        │   └── portal-page/  # Main page — composes components
        └── portal.routes.ts  # Lazy-loaded route config for this feature
```

## Structural Rules

- **Components always get a subfolder** — a component's `.ts`, `.html`, and `.scss` files live together under `components/<name>/`.
- **Single-file artifacts live directly in the feature root** — if a feature has only one service, it lives as `my-feature.service.ts` at the feature root, not inside a `services/` folder. Same for models, pipes, directives, etc. Only create a subfolder when there are two or more files of that type.
- **`shared/` starts empty** — it fills as cross-feature needs emerge; nothing is pre-emptively placed there.

## Portal Feature

### Route
- Registered in `app.routes.ts` as `''` (root), lazy-loading `portal.routes.ts`.
- `portal.routes.ts` maps `''` → `PortalPage`.

### Pages
**`portal-page/`** — the feature's main page.
- Injects `OidcSecurityService` and `ConfigService`.
- Calls `httpResource` to fetch `/users/me` when authenticated.
- Renders the `UserCardComponent`.
- Provides a **Logout** button (Material `mat-button`).

### Components
**`user-card/`** — displays authenticated user info.
- Accepts a `user` input (the raw JSON from `/users/me`).
- Uses a Material `mat-card` to present the user data.
- Shows a loading skeleton and error state.

### No services subfolder
No dedicated service is needed — auth comes from `OidcSecurityService` (core), HTTP from Angular's `httpResource`. The `httpResource` call lives directly in `PortalPage`.

### No models subfolder
The user shape is an untyped JSON response from the API at this stage. No model file warranted.

## App Shell

`App` (`app.ts`) becomes a **pure router shell**: it removes all auth/user logic and renders only `<router-outlet>`. The portal page takes over that responsibility.

## Documentation Updates

- **`frontend-rules.md`** — add a brief section describing the feature structure and the "single-file lives at feature root" rule.
- **`README.md`** — add sections for frontend folder structure and the Portal feature.

## Success Criteria

- `ng serve` starts without errors.
- Navigating to `/` renders the portal page (user card visible after Keycloak login).
- `ng test` passes.
- `App` component has no auth/user logic — only `<router-outlet>`.
- `frontend-rules.md` documents the structure.
- `README.md` describes the portal feature and folder layout.
