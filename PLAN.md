# PLAN — M31: Hot Reload for Theme and Stylesheet Files

*(Replaces the M32 plan in this file — M32 is complete, committed and pushed.)*

## Goal

User-directed: "Push, cleanup, and then start M31". With `run(hot_reload=True)`, editing a theme or stylesheet file re-styles the running app in place, keeping bound values live (`tre` 0.3.3, M91 / issue #8). Split out of M30; unblocked by M32.

## Status

**In progress — Phase 2 of 3 done (2026-09-25).**

1. **Theme files** — ✅ `FileWatcher` watches `App(default_theme=, custom_theme=)`; an edit queues `App.set_theme_specs()`, which re-themes every view `build_view()`/`load()` made plus the window. Found and fixed an M30 bug on the way: the window was never themed (building a `View` doesn't set the window's theme), so `App.show()` now calls `Window.set_theme`, resolving seed and colors the way a `View` does. 234 → 245 tests.
2. **Stylesheet files** — ✅ the default (`App.set_stylesheet_spec()`) and each screen's own file are watched; a failed re-style is undone on the screens already changed. The M91 consequences are documented, not worked around: `on_change` fires once per reload on bound nodes (pinned by a test), and embedded components never get the host's theme or stylesheet (a `tre` limitation, found reading `View.instantiate`). 245 → 254 tests.
3. **Tests, docs, tracker** — a subprocess live test (M29 Phase 6's pattern); final MkDocs pass; tracker and artifact.

**Up next:** Phase 3, waiting on the user's go-ahead.
