# Angular Material Setup — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Install Angular Material 22 with a magenta M3 theme and Roboto typography in the Angular 22 frontend.

**Architecture:** Run the official `ng add @angular/material@22` schematic to install packages and wire up animations automatically, then overwrite `styles.scss` with the exact `mat.theme()` mixin the spec requires. No custom SCSS beyond what the spec defines.

**Tech Stack:** Angular 22, Angular Material 22, SCSS, Google Fonts (Roboto + Material Icons)

---

### Task 1: Establish a clean baseline

Before touching anything, confirm the existing tests pass.

**Files:**
- Read: `frontend/src/app/app.spec.ts`

- [ ] **Step 1: Run the existing test suite**

```bash
cd frontend && ng test --watch=false
```

Expected output: 2 tests pass — `should create the app` and `should render title`.
If they already fail, stop and investigate before continuing.

---

### Task 2: Install Angular Material via schematic

The `ng add` schematic handles package installation, font links in `index.html`, and wiring `provideAnimationsAsync()` into `app.config.ts`.

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/package-lock.json`
- Modify: `frontend/src/index.html`
- Modify: `frontend/src/app/app.config.ts`
- Modify: `frontend/src/styles.scss` (schematic writes a default theme — Task 3 replaces it)

- [ ] **Step 1: Run ng add from the frontend directory**

```bash
cd frontend && npx ng add @angular/material@22 --theme=custom --typography=true --animations=enabled
```

If the schematic shows interactive prompts instead of consuming the flags, answer:
- "Choose a prebuilt theme name, or 'custom' for a custom theme" → **custom**
- "Set up global Angular Material typography styles?" → **Yes**
- "Include the Angular animations module?" → **enabled**

- [ ] **Step 2: Verify @angular/material and @angular/cdk appear in package.json**

Open `frontend/package.json`. Under `dependencies`, confirm both entries exist:

```json
"@angular/cdk": "^22.x.x",
"@angular/material": "^22.x.x"
```

- [ ] **Step 3: Verify Roboto and Material Icons links were added to index.html**

Open `frontend/src/index.html`. Confirm both `<link>` tags appear inside `<head>`:

```html
<link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
```

The exact URLs may differ slightly between schematic versions — what matters is that Roboto and Material Icons links are present.

- [ ] **Step 4: Verify provideAnimationsAsync() was added to app.config.ts**

Open `frontend/src/app/app.config.ts`. It should look like this:

```typescript
import { ApplicationConfig, provideBrowserGlobalErrorListeners } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';

import { routes } from './app.routes';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes),
    provideAnimationsAsync(),
  ],
};
```

If `provideAnimationsAsync()` is missing (the schematic might skip it depending on version), add it manually: import from `@angular/platform-browser/animations/async` and include it in `providers`.

---

### Task 3: Replace styles.scss with the magenta M3 theme

The schematic writes its own default theme into `styles.scss`. We discard it entirely and write the spec's exact content.

**Files:**
- Modify: `frontend/src/styles.scss`

- [ ] **Step 1: Replace the full content of styles.scss**

Overwrite `frontend/src/styles.scss` with exactly:

```scss
@use '@angular/material' as mat;

html {
  color-scheme: light dark;
  @include mat.theme((
    color: mat.$magenta-palette,
    typography: Roboto,
    density: 0
  ));
}
```

- [ ] **Step 2: Verify the SCSS compiles**

```bash
cd frontend && npx ng build
```

Expected: build completes with no errors. Budget warnings are fine — compilation errors are not.

---

### Task 4: Run tests and commit

**Files:** none new

- [ ] **Step 1: Run the test suite**

```bash
cd frontend && ng test --watch=false
```

Expected: the same 2 tests pass as in Task 1.

If tests fail with an animation-related error, add `provideAnimationsAsync()` to the TestBed config in `frontend/src/app/app.spec.ts`:

```typescript
import { TestBed } from '@angular/core/testing';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { App } from './app';

describe('App', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [provideAnimationsAsync()],
    }).compileComponents();
  });

  it('should create the app', () => {
    const fixture = TestBed.createComponent(App);
    const app = fixture.componentInstance;
    expect(app).toBeTruthy();
  });

  it('should render title', async () => {
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('h1')?.textContent).toContain('Hello, expense-app');
  });
});
```

Re-run `ng test --watch=false` after this change and confirm both tests pass.

- [ ] **Step 2: Commit all changes**

Run from the repository root (`mia-iisaia/`, one level above `tp-final/`):

```bash
git add tp-final/frontend/package.json tp-final/frontend/package-lock.json tp-final/frontend/src/index.html tp-final/frontend/src/app/app.config.ts tp-final/frontend/src/styles.scss
git commit -m "feat: add Angular Material 22 with magenta M3 theme and Roboto typography"
```

If `app.spec.ts` was modified in Step 1, include it:

```bash
git add tp-final/frontend/package.json tp-final/frontend/package-lock.json tp-final/frontend/src/index.html tp-final/frontend/src/app/app.config.ts tp-final/frontend/src/styles.scss tp-final/frontend/src/app/app.spec.ts
git commit -m "feat: add Angular Material 22 with magenta M3 theme and Roboto typography"
```
