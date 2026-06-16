---
paths: 
  - frontend/**/*
---

# Frontend Rules — Angular 22

## Stack
- Angular v22.
- TypeScript v6.0.3
- Testing: Vitest via `ng test` (not Karma; Jest and Web Test Runner support have been removed in v22)
- Node >= 22.22.3 required

## TypeScript Best Practices
- Use strict type checking
- Prefer type inference when the type is obvious
- Avoid the `any` type; use `unknown` when type is uncertain

## Angular Best Practices
- Always use standalone components over NgModules
- Must NOT set `standalone: true` inside Angular decorators. It's the default in Angular v20+.
- Use signals for state management
- Implement lazy loading for feature routes
- Do NOT use the `@HostBinding` and `@HostListener` decorators. Put host bindings inside the `host` object of the `@Component` or `@Directive` decorator instead
- Use `NgOptimizedImage` for all static images.
- `NgOptimizedImage` does not work for inline base64 images.
- Zoneless change detection is the default for new apps - do NOT add `provideZonelessChangeDetection()` to new projects.
- `OnPush` is the default change detection strategy for components. Do not set it explicitly.
- The former `Default` strategy has been renamed to `ChangeDetectionStrategy.Eager`. Use it only when explicitly opting out of OnPush.

## Accessibility Requirements
- It MUST pass all AXE checks.
- It MUST follow all WCAG AA minimums, including focus management, color contrast, and ARIA attributes.
- Use Angular Aria utilities (stable in v22) for ARIA patterns instead of managing ARIA attributes manually.

## Components
- Keep components small and focused on a single responsibility
- Use `input()` and `output()` functions instead of decorators
- Use `computed()` for derived state
- Prefer inline templates for small components
- Prefer Signal forms (stable in v22) for new form implementations; fall back to Reactive forms only when Signal forms don't cover the use case.
- Prefer Reactive forms over Template-driven forms.
- Do NOT use `ngClass`, use `class` bindings instead
- Do NOT use `ngStyle`, use `style` bindings instead

## Styling
- Keep styles scoped to the component (`styleUrl`).
- No global CSS hacks; use CSS variables for theming.
- When using external templates/styles, use paths relative to the component TS file.

## State Management
- Use signals for local component state
- Use `computed()` for derived state
- Use `resource()` (stable in v22) for async data fetching; it integrates with signals and manages loading/error states automatically.
- Keep state transformations pure and predictable
- Do NOT use `mutate` on signals, use `update` or `set` instead

## Templates
- Keep templates simple and avoid complex logic
- Use native control flow (`@if`, `@for`, `@switch`) instead of `*ngIf`, `*ngFor`, `*ngSwitch`
- Use the async pipe to handle observables
- Do not assume globals like (`new Date()`) are available.

## Services
- RxJS is still appropriate in services for async operations
- Design services around a single responsibility
- Use the `@Service` decorator (stable in v22) instead of `@Injectable({ providedIn: 'root' })` for singleton services.
- Use the `inject()` function instead of constructor injection
- All HTTP calls go to the backend at `http://localhost:8000`
- Handle 401 responses by triggering a Keycloak re-login flow

## Auth
- Auth is handled entirely by Keycloak via PKCE — never implement custom login forms.
- Use the HTTP interceptor to attach `Authorization: Bearer <token>` to all API requests.
- The Keycloak issuer for dev is `http://localhost:8080/realms/expense-app`.

## Runtime Configuration

The app reads environment-specific values at **runtime** via `fetch('/config.json')` in `ConfigService` (`frontend/src/app/core/config.service.ts`), before Angular bootstraps. This allows a single Docker image to be reconfigured per environment without rebuilding.

**Two files in `frontend/public/`:**
- `config.json` — committed with local-dev defaults (used directly by `ng serve`; overwritten in Docker at container start).
- `config.template.json` — template with `${VAR_NAME}` placeholders. `frontend/entrypoint.sh` runs `envsubst` over it at Docker startup and writes the result to `config.json`.

`envsubst` variables are detected dynamically from the placeholders in `config.template.json`, so no manual whitelist is maintained.

**To add a new runtime variable**, make all four of these changes:
1. Add `"newKey": "${NEW_VAR}"` to `frontend/public/config.template.json`.
2. Add `"newKey": "<local-default>"` to `frontend/public/config.json` (used by `ng serve`).
3. Expose the value in `ConfigService` as a signal.
4. Declare `NEW_VAR` in `compose.yaml` (under the `frontend` service environment) and add it to `.env.example`.

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
- Components and pages always get a subfolder — a component's `.ts`, `.html`, `.scss`, and `.spec.ts` live together under `components/<name>/`; page components follow the same pattern under `pages/<name>/`.
- Single-file artifacts (one service, one model, one pipe) live directly at the feature root — no subfolder until a second file of that type is added.
- `shared/` fills as cross-feature needs emerge; nothing is pre-emptively placed there.





