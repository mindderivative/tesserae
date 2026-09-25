# PLAN — M30: Theme Arguments on `App` and `App.load()`

*(Replaces the M29 plan in this file — M29 is complete, committed and pushed. `LOG.md` still holds M29's record until M30 work starts.)*

## Goal

User-directed: "scope adding theme args to App.load()". Give `App` a theme API, closing the known gap that it has none. `load_view` already takes every theme argument (M29), so the real question is where a theme lives in a multi-screen app.

## Status

**In progress — Phase 1 of 3 done (2026-09-25).** The user chose: an app-wide theme on `App(...)`; a stylesheet per screen on `load()`, with an app-wide default on `App(...)`; and to wait for `tre` issue #8 before any theme-file hot reload, which moves to a new M31. Phase 2 (implementation) waits on the user's go-ahead.

Key finding, checked in `tre` v0.3.2: a theme is window-level. `Window.from_view` shares the first screen's theme with the window, and `Window.show_view` never switches it — so per-screen themes would leave imperative `tesserae.widgets` and interaction tints on the first screen's theme after `app.show(...)`. A stylesheet, by contrast, is per-`View`. `View.set_theme` can re-theme a live screen (a complete selection each call; bindings not re-applied); `tre` has no `set_stylesheet`.

Plan (full detail in `BUILD_TRACKER.md` Milestone 30):

1. **Decide** — recommended: an app-wide theme on `App(...)`, a per-screen stylesheet on `load()`; and whether theme-file hot reload is in scope.
2. **Implement** — theme files read once via `load_theme`, passed to every `load()` as dicts; `register()` unchanged.
3. **Hot reload for theme files** (if in scope) — watch them, re-theme every screen via `View.set_theme` on the loop thread. Stylesheets can't be hot-reloaded until `tre` gains `set_stylesheet`.

   Filed [`tre` issue #8](https://github.com/mindderivative/tre/issues/8) (user-directed): `set_theme` and `reconcile` drop `{{ }}` bound values on the nodes they touch (reproduced — a bound label reverts to its static text), and there's no `View.set_stylesheet`. Fixes to either could change Phase 3: re-theming becomes safe to ship, and stylesheets become hot-reloadable. Part 1 also affects M29's shipped hot reload, now a known gap.
4. **Tests, MkDocs, tracker.**
