# LOG — M16: Part 3, Phase 2 — Wire `App.load()`/`instantiate()` to Macro-Expansion

- User-directed ordering: "Start 3, then move to 2 and then 1". Item 3
  (`tre`'s own `instantiate(..., source=...)` widening, its M73)
  landed first, on `tre`'s `0.3.1` branch. This milestone is item 2.

## What shipped

1. Reinstalled `tre` (`0.3.1` branch, with M73) into `tesserae/.venv`
   via `maturin develop --release`, confirmed live with a direct
   interactive check before writing any Tesserae-side code.
2. `src/tesserae/app.py` — `App.load()` now constructs via `tesserae.
   spec.load_view(view_path)` instead of `tre.View(str(view_path))`
   directly. Real, deliberate scope limit stated in its own docstring:
   no `theme_seed`/`custom_theme`/`stylesheet`/`dark` forwarding yet.
3. `src/tesserae/component.py` — `instantiate()` now reads `path`'s
   real content, calls `expand_components()`, and hands off via
   `parent.instantiate(str(path), into, source=expanded)` — reachable
   for nested components too, since `Component.instantiate` (not just
   `View.instantiate`) got the identical `tre`-side widening.
4. Real, honest limitation surfaced while testing, not fixed here:
   `App` has no theme API of its own at all — an MD3-token-using
   `component:` fragment can't actually render through `App.load()`
   without one yet. Proven via a real distinguishing test: before this
   wiring, a `component:`-using view fails with `tre`'s own schema
   error (`component` isn't a real `WidgetSpec` field,
   `deny_unknown_fields`); after, it fails later, at MD3 color
   resolution — proving `component:`/`with:` were genuinely replaced
   before `tre` ever parsed the file, even though the fragment still
   can't fully render without a theme.
5. `tests/test_app.py` (+2) / `test_component.py` (+2) — each pair
   proving the no-op regression case and the genuine-expansion case.
- Verification: `pytest tests/` 101 passed (97 prior + 4 new), 0
  regressions. All 3 real examples (`counter`/`multi_screen`/
  `todo_list`) re-run end to end — genuinely warranted this time (this
  change touches the core construction path every example goes
  through, unlike the additive widget-catalog milestones) — all exited
  cleanly with correct real output (`Count: 3` after 3 clicks, final
  screen `Settings`, final todo items list unchanged from before).

## Status

**M16 is complete, all 3 phases.** `component:` macro-expansion is now
the default for both real construction paths. Committed locally
(`13b58c5`); push deferred pending explicit user confirmation.

Next: item 1 of the user's own ordering — the other 37 component
fragments.
