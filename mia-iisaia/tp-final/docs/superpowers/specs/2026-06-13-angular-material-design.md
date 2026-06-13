# Angular Material Setup — Design Spec

**Date:** 2026-06-13
**Status:** Approved

## Goal

Add Angular Material 22 to the frontend with a Deep Purple M3 theme and Roboto typography, so all future UI components have a consistent design system from the start.

## Approach

Use the official `ng add @angular/material` schematic (option A), which automates all integration steps. Post-install, manually adjust the generated theme palette to Deep Purple.

## What gets configured

### Package installation
- `@angular/material@22` and `@angular/cdk@22` added to `package.json` dependencies.

### `index.html`
- Google Fonts link for **Roboto** (300, 400, 500, 700 weights).
- Google Fonts link for **Material Icons**.

### `styles.scss`
- Global Material theme import using M3 `mat.theme()` with Deep Purple as the primary palette.
- Global typography classes applied to `body` via `mat.theme()` typography config.
- `mat-icon` font family set to Material Icons.

### `app.config.ts`
- `provideAnimationsAsync()` added to the `providers` array (async animations for better initial load performance).

## Theme details

- **Design system:** Material Design 3 (M3) — default in Angular Material 22.
- **Primary source color:** `#673AB7` (Deep Purple). M3 derives the full tonal palette (primary, secondary, tertiary, error, neutral) automatically from this single seed color via the Material color algorithm.
- **Typography:** Roboto loaded from Google Fonts; applied globally via Material's typography system.
- **Animations:** async (lazy-loaded, does not block initial render).
- **Theme generation:** The `ng add` schematic generates a custom M3 theme file (`_theme.scss` or inline in `styles.scss`) using `mat.theme()` with `$primary: mat.define-theme-color(#673AB7)`.

## Out of scope

- No UI components are built in this task — Material is installed and configured only.
- No custom color overrides beyond selecting Deep Purple as the primary palette.
- No dark mode configuration (can be added later).

## Success criteria

- `ng serve` starts without errors after the schematic runs.
- `ng test` passes.
- The app loads in the browser with Roboto font visible.
- `@angular/material` and `@angular/cdk` appear in `package.json`.
- `provideAnimationsAsync()` is present in `app.config.ts`.
