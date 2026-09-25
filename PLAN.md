# PLAN — M30: Theme Arguments on `App` and `App.load()`

*(Replaces the M29 plan in this file — M29 is complete, committed and pushed. `LOG.md` still holds M29's record until M30 work starts.)*

## Goal

User-directed: "scope adding theme args to App.load()". Give `App` a theme API, closing the known gap that it has none. `load_view` already takes every theme argument (M29), so the real question is where a theme lives in a multi-screen app.

## Status

**Scoped, not started — waiting on user decisions (Phase 1).**

Key finding, checked in `tre` v0.3.2: a theme is window-level. `Window.from_view` shares the first screen's theme with the window, and `Window.show_view` never switches it — so per-screen themes would leave imperative `tesserae.widgets` and interaction tints on the first screen's theme after `app.show(...)`. A stylesheet, by contrast, is per-`View`. `View.set_theme` can re-theme a live screen (a complete selection each call; bindings not re-applied); `tre` has no `set_stylesheet`.

Plan (full detail in `BUILD_TRACKER.md` Milestone 30):

1. **Decide** — recommended: an app-wide theme on `App(...)`, a per-screen stylesheet on `load()`; and whether theme-file hot reload is in scope.
2. **Implement** — theme files read once via `load_theme`, passed to every `load()` as dicts; `register()` unchanged.
3. **Hot reload for theme files** (if in scope) — watch them, re-theme every screen via `View.set_theme` on the loop thread. Stylesheets can't be hot-reloaded until `tre` gains `set_stylesheet`.
4. **Tests, MkDocs, tracker.**
