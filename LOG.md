# LOG — M31: Hot Reload for Theme and Stylesheet Files

*(Replaces M32's log — M32 is complete, committed and pushed.)*

- User: "Push, cleanup, and then start M31". Pushed `3fd0cf3` and
  `dc6d34a`; removed the two scratch `tre` worktrees (`tre-v0.3.2`,
  `tre-v0.3.3`).

## Phase 1 — theme files

1. Probed `tre` 0.3.3 first. `set_theme` keeps the stylesheet,
   `set_stylesheet` keeps the theme, and `reconcile` keeps both.
2. Phase 1 Step 2's question ("does re-theming the first screen
   re-theme the window?") answered by reading `view.rs`/`window.rs` at
   the tag and testing: no. The window's `ThemeState` is shared with
   the view but only `Window.set_theme` fills it. So every M30 `App`
   window was unthemed (`Window.theme.is_set()` was `False`), and
   imperative widgets and interaction tints ignored the app theme.
3. Seed precedence differs: a `View` uses `theme_seed` > custom
   `seed:` > default `seed:` plus both themes' `colors:`, while
   `Window.set_theme` uses custom `seed:` > its `seed` argument and
   ignores the default theme's seed and colors. `_window_theme`
   rewrites the custom-theme dict so the window matches the view.
4. `FileWatcher` (in `spec/watch.py`), `App.set_theme_specs()`,
   `App._start_watchers()` (shared by `run()` and the tests).
   `App.show()` themes the window on first open.
5. 11 tests in `tests/test_theme_reload.py`; each window-theme piece
   removed in turn to check a test fails. 245 passed.
6. Docs: `guide/hot-reload.md`, `guide/themes-and-fonts.md`,
   `api/app.md`, `ARCHITECTURE.md`. `mkdocs build --strict` clean.

Slip: while probing, a `git checkout v0.3.3` ran in `tre`'s main
checkout by mistake; restored to `main` at once (`68c3883`), with the
`tre` session's uncommitted `CLAUDE.md` edit intact. Source reads use
`git show v0.3.3:...` from then on.
