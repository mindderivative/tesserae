# PLAN — M30: Theme Arguments on `App` and `App.load()`

*(Replaces the M29 plan in this file — M29 is complete, committed and pushed.)*

## Goal

User-directed: "scope adding theme args to App.load()". Give `App` a theme API, closing the known gap that it had none.

## Status

**Complete (2026-09-25).**

- **Phase 1 — decisions (user):** an app-wide theme on `App(...)`; a stylesheet per screen on `load()`, with an app-wide default on `App(...)`; theme-file hot reload deferred until `tre` issue #8 is fixed — split out into M31.
- **Phase 2 — implementation:** `App(..., theme_seed=, dark=, default_theme=, custom_theme=, stylesheet=)` plus `*_spec=` forms, files read once by Tesserae; `App.load(..., stylesheet=)`; new `App.build_view()` for `register()`ed screens (the `multi_screen` example uses it). MkDocs updated.
- **Phase 3 — tests, docs, tracker:** 12 new tests, mutation-checked; verified against `tre` v0.3.2 built from source in a scratch venv, since this repo's `.venv` loads `tre`'s unreleased 0.3.3; a docs inaccuracy about when stylesheet files are read fixed.

Why app-wide: in `tre`, `Window.from_view` shares the first screen's theme with the window and `Window.show_view` never switches it, so per-screen themes would leave `tesserae.widgets` and interaction tints on the first screen's theme.

`pytest tests/` 233 passed against v0.3.2.

**Up next:** nothing scoped. M31 waits on Tesserae's move to `tre` 0.3.3 (where issue #8 is fixed); that migration is the natural next milestone once 0.3.3 is released.
