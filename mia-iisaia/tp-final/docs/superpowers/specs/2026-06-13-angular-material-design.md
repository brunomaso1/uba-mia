# Angular Material Setup — Design Spec

**Date:** 2026-06-13
**Status:** Approved

## Goal

Add Angular Material 22 to the frontend with the `magenta-violet` pre-built M3 theme and Roboto typography, so all future UI components have a consistent design system from the start.

## Approach

Use the official `ng add @angular/material` schematic, which automates all integration steps. Select the `magenta-violet` pre-built theme during the schematic prompts.

## What gets configured

### Package installation
- `@angular/material@22` and `@angular/cdk@22` added to `package.json` dependencies.

### `index.html`
- Google Fonts link for **Roboto** (300, 400, 500, 700 weights).
- Google Fonts link for **Material Icons**.

### `styles.scss`
- Pre-built M3 theme `magenta-violet` imported from `@angular/material/prebuilt-themes/magenta-violet.css`.
- Global typography classes applied to `body`.
- `mat-icon` font family set to Material Icons.

### `app.config.ts`
- `provideAnimationsAsync()` added to the `providers` array (async animations for better initial load performance).

## Theme details

- **Design system:** Material Design 3 (M3) — default in Angular Material 22.
- **Theme:** `magenta-violet` pre-built theme (ships with Angular Material, no custom SCSS needed).
- **Typography:** Roboto loaded from Google Fonts; applied globally via Material's typography system.
- **Animations:** async (lazy-loaded, does not block initial render).

## Out of scope

- No UI components are built in this task — Material is installed and configured only.
- No dark mode configuration (can be added later).

## Success criteria

- `ng serve` starts without errors after the schematic runs.
- `ng test` passes.
- The app loads in the browser with Roboto font visible.
- `@angular/material` and `@angular/cdk` appear in `package.json`.
- `provideAnimationsAsync()` is present in `app.config.ts`.
- `magenta-violet.css` is imported in `styles.scss`.
