# Design: Auto-login on App Load (Keycloak redirect)

**Date:** 2026-06-15
**Status:** Approved

## Problem

Currently, users land on the app and see a "Login" button they must click before being redirected to Keycloak. The desired behavior is that the app immediately redirects unauthenticated users to Keycloak — no button click required.

## Constraint

All routes in the application require authentication. There are no public routes.

## Approach

Replace `withAppInitializerAuthCheck()` with a custom `provideAppInitializer` that combines the OIDC auth check and the auto-redirect in a single initialization step.

The library's `withAppInitializerAuthCheck()` is a convenience wrapper around `checkAuth()`. By replacing it with our own initializer we gain full control over what happens after the check.

## Implementation

### `app.config.ts`

Remove `withAppInitializerAuthCheck()` from `provideAuth(...)`. Add a `provideAppInitializer` after the `provideAuth(...)` block that:

1. Injects `OidcSecurityService`.
2. Calls `firstValueFrom(oidc.checkAuth())` — this processes any OAuth callback present in the URL (`?code=...&state=...`), restores an existing session from storage, or determines that the user is unauthenticated.
3. If `result.isAuthenticated` is `false`: calls `oidc.authorize()` and returns a promise that never resolves. The browser is already navigating to Keycloak; Angular never finishes bootstrapping.
4. If `result.isAuthenticated` is `true`: returns normally; Angular continues bootstrapping.

> **Ordering note:** `provideAuth(...)` must be declared before the custom initializer so that `OidcSecurityService` is available for injection when the initializer runs. The `StsConfigHttpLoader` fetches `/config.json` independently (it does not depend on `ConfigService`), so there is no ordering issue between config loading and OIDC config loading. Angular runs `APP_INITIALIZER` functions concurrently; the OIDC library handles internally waiting for its own config before `checkAuth()` can execute.

### `app.html`

Remove the `@else` branch that contains the "Login" button. By the time any component renders, the user is always authenticated. Keep only the authenticated branch (logout button + user info).

### `app.ts`

Remove the `login()` method — it becomes dead code once auto-login is in place.

## Authentication Flows

| Scenario | Behavior |
|---|---|
| First visit (no tokens) | `checkAuth()` → `isAuthenticated: false` → `authorize()` → redirect to Keycloak |
| Return from Keycloak callback (`?code=xxx`) | `checkAuth()` processes the code, exchanges for tokens → `isAuthenticated: true` → app bootstraps |
| Existing valid session | `checkAuth()` restores session from storage → `isAuthenticated: true` → app bootstraps |
| Expired token, silent renew fails | `checkAuth()` → `isAuthenticated: false` → `authorize()` → redirect to Keycloak |

## Documentation

Update `README.md` to reflect that the app auto-redirects to Keycloak on load. Users cannot access any part of the UI without an authenticated session.

## Out of Scope

- Adding routes or restructuring the router (no routes exist yet; this design leaves the routing layer untouched).
- Changing the logout flow.
- Error handling for `checkAuth()` failures beyond the unauthenticated redirect (e.g., network errors during token exchange are not handled specially — the app will not bootstrap and the user will see a blank page with a console error; this is acceptable for now).
