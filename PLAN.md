# PLAN — M31: Hot Reload for Theme and Stylesheet Files

*(Replaces the M32 plan in this file — M32 is complete, committed and pushed.)*

## Goal

User-directed: "Push, cleanup, and then start M31". With `run(hot_reload=True)`, editing a theme or stylesheet file re-styles the running app in place, keeping bound values live (`tre` 0.3.3, M91 / issue #8). Split out of M30; unblocked by M32.

## Status

**In progress — Phase 1 of 3 done (2026-09-25).**

1. **Theme files** — ✅ `FileWatcher` watches `App(default_theme=, custom_theme=)`; an edit queues `App.set_theme_specs()`, which re-themes every view `build_view()`/`load()` made plus the window. Found and fixed an M30 bug on the way: the window was never themed (building a `View` doesn't set the window's theme), so `App.show()` now calls `Window.set_theme`, resolving seed and colors the way a `View` does. 234 → 245 tests.
2. **Stylesheet files** — watch the app's default stylesheet and each screen's own `load(stylesheet=)` file; re-apply with `View.set_stylesheet`. Settle the two M91 consequences: an `on_change` handler fires once per live update when bindings are re-applied, and an embedded `tesserae.instantiate` component isn't re-themed (`tre`'s `Component` has no `set_theme`).
3. **Tests, docs, tracker** — a subprocess live test (M29 Phase 6's pattern); final MkDocs pass; tracker and artifact.

**Up next:** Phase 2, waiting on the user's go-ahead.
