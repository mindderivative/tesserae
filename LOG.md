# LOG — M30: Theme Arguments on `App` and `App.load()`

- User: "scope adding theme args to App.load()" — scoped in
  `BUILD_TRACKER.md`, then filed `tre` issue #8 (user-directed) after
  reproducing that `set_theme`/`reconcile` drop bound values and that
  `View` has no `set_stylesheet`.
- User decisions: app-wide theme on `App(...)`; per-screen stylesheet on
  `load()` with an app-wide default; wait for #8 before theme-file hot
  reload (→ M31). Then "push it and start Phase 2", "push it and start
  Phase 3".

## What shipped

1. `App(..., theme_seed=, dark=, default_theme=/default_theme_spec=,
   custom_theme=/custom_theme_spec=, stylesheet=/stylesheet_spec=)`.
   Theme and default stylesheet files are read once, at construction;
   `tre` gets dicts.
2. `App.load(..., stylesheet=, stylesheet_spec=)` replaces the default
   stylesheet for one screen.
3. `App.build_view(path, *, stylesheet=)` — the app's theme and
   stylesheet for a screen given to `register()`; `load()` uses it too.
   `examples/multi_screen/` builds its screens with it.
4. Docs: `api/app.md`, `guide/themes-and-fonts.md`,
   `guide/apps-and-screens.md`, `ARCHITECTURE.md`.
5. 12 new tests (`test_app_theme.py`).

## Real findings

- A theme is window-level in `tre`: `Window.from_view` shares the first
  screen's theme with the window and `show_view` never switches it —
  the reason the theme is app-wide.
- `set_theme` and `reconcile` dropped `{{ }}` bound values on the nodes
  they touched (reproduced), also affecting M29's hot reload → `tre`
  issue #8 → fixed in `tre` M91 (0.3.3, unreleased; verified locally).
- `tre` 0.3.3 (M90) renames much of the declarative schema — recorded
  as a known gap for a future migration milestone.
- This repo's `.venv` loads `tre` from its source tree, so the `tre`
  session's 0.3.3 rebuild broke 81 local tests mid-milestone. Verified
  instead against `tre` v0.3.2 built offline from source in a scratch
  venv.
- A docs inaccuracy caught by the tests: a screen's own stylesheet file
  is read when it loads, not when the `App` is created.

## Status

**M30 complete.** `pytest tests/` 233 passed against `tre` v0.3.2
(221 → 233); mutation-checked; `mkdocs build --strict` clean.
