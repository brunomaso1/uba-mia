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






