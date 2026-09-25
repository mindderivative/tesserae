# PLAN — M31: Hot Reload for Theme and Stylesheet Files

*(Replaces the M32 plan in this file — M32 is complete, committed and pushed.)*

## Goal

User-directed: "Push, cleanup, and then start M31". With `run(hot_reload=True)`, editing a theme or stylesheet file re-styles the running app in place, keeping bound values live (`tre` 0.3.3, M91 / issue #8). Split out of M30; unblocked by M32.

## Status

**Complete (2026-09-25).** 234 → 255 tests.

1. **Theme files** — ✅ `FileWatcher` watches `App(default_theme=, custom_theme=)`; an edit queues `App.set_theme_specs()`, which re-themes every view `build_view()`/`load()` made plus the window. Found and fixed an M30 bug on the way: the window was never themed (building a `View` doesn't set the window's theme), so `App.show()` now calls `Window.set_theme`, resolving seed and colors the way a `View` does. 234 → 245 tests.
2. **Stylesheet files** — ✅ the default (`App.set_stylesheet_spec()`) and each screen's own file are watched; a failed re-style is undone on the screens already changed. The M91 consequences are documented, not worked around: `on_change` fires once per reload on bound nodes (pinned by a test), and embedded components never get the host's theme or stylesheet (a `tre` limitation, found reading `View.instantiate`). 245 → 254 tests.
3. **Tests, docs, tracker** — ✅ a subprocess live test edits a theme file and a stylesheet file inside a real `App.run(hot_reload=True)` (fails if the stylesheet watcher is switched off); `README.md`, `docs/index.md` and the hot-reload guide updated. `tre` issue #12 filed for `on_change` firing on every reload.

**Up next:** nothing started. Candidates: `tre`'s building-block program (0.3.4 released; a large Tesserae-side program, not yet scoped), hot reload for `App.register()`ed screens, conditional per-item styling.
