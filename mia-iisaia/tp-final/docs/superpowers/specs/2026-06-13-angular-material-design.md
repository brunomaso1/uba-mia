# Angular Material Setup — Design Spec

**Date:** 2026-06-13
**Status:** Approved

## Goal

Add Angular Material 22 to the frontend with a Magenta M3 theme and Roboto typography, so all future UI components have a consistent design system from the start.

## Approach

Use the official `ng add @angular/material` schematic, which installs the packages and wires up animations. Then configure the theme manually in `styles.scss` using the `mat.theme()` mixin API (the correct M3 approach for Angular Material 22).

## What gets configured

### Package installation
- `@angular/material@22` and `@angular/cdk@22` added to `package.json` dependencies.

### `index.html`
- Google Fonts link for **Roboto** (300, 400, 500, 700 weights).
- Google Fonts link for **Material Icons**.

### `styles.scss`
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
- `color-scheme: light dark` enables automatic light/dark mode support via CSS.
- `mat.$magenta-palette` is the M3 built-in tonal palette for magenta/violet tones.
- `density: 0` is the default density (no compacting).

### `app.config.ts`
- `provideAnimationsAsync()` added to the `providers` array (async animations for better initial load performance).

## Theme details

- **Design system:** Material Design 3 (M3).
- **Color palette:** `mat.$magenta-palette` — Material's built-in magenta tonal palette.
- **Typography:** Roboto, specified inline in the `mat.theme()` mixin.
- **Density:** 0 (default).
- **Color scheme:** `light dark` — supports both light and dark modes automatically via `prefers-color-scheme`.

## Out of scope

- No UI components are built in this task — Material is installed and configured only.
- No explicit dark mode toggle (OS preference drives it automatically via `color-scheme`).

## Success criteria

- `ng serve` starts without errors after setup.
- `ng test` passes.
- The app loads in the browser with Roboto font visible.
- `@angular/material` and `@angular/cdk` appear in `package.json`.
- `provideAnimationsAsync()` is present in `app.config.ts`.
- `styles.scss` uses `mat.theme()` with `mat.$magenta-palette`.
