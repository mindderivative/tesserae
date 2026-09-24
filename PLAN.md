# PLAN — M16: Part 3, Phase 2 — Wire `App.load()`/`instantiate()` to Macro-Expansion

*(Replaces the prior M15 plan in this file — M15 is complete, committed.
User-directed ordering: "Start 3, then move to 2 and then 1" — item 3
(the `tre`-side widening) landed first, on `tre`'s own `0.3.1` branch as
its M73. This is item 2.)*

## Goal

`App.load()` (top-level screens) and `tesserae.instantiate()` (embedded
components) should apply `component:` macro-expansion by default —
an app author should never need to call `tesserae.spec.load_view`/
`expand_components` directly.

## Status

**Complete, all 3 phases.**

`tre`'s own M73 (`instantiate(..., source=...)`, commit `b963331` on
its `0.3.1` branch) closed the one real blocker M15 had named —
reinstalled into `tesserae/.venv`, confirmed live with a direct
interactive check before proceeding.

`src/tesserae/app.py` — `App.load()` now constructs via `tesserae.
spec.load_view(view_path)` instead of `tre.View(str(view_path))`
directly. `src/tesserae/component.py` — `instantiate()` now expands
`path`'s content and hands off via `source=`, reaching nested
components too.

Real, honest limitation surfaced while testing, not fixed here: `App`
has no theme API at all (`theme_seed`/`custom_theme`/`dark`/
`stylesheet` never existed on it) — a `component:` fragment
referencing an MD3 color role can't actually render through
`App.load()` without one. Proven directly via a real distinguishing
test: before this wiring, a `component:`-using view fails with `tre`'s
own schema error (`component` isn't a real `WidgetSpec` field); after,
it fails later, at MD3 color resolution — proving expansion genuinely
ran even though the fragment still can't fully render without a theme.

4 new pytest tests (2 in `test_app.py`, 2 in `test_component.py`),
each pair covering the no-op regression case and the genuine-expansion
case via that distinguishing-error technique. Full suite: 101 passed
(97 prior + 4 new), 0 regressions. All 3 real examples (`counter`/
`multi_screen`/`todo_list`) re-run end to end — genuinely warranted
this time, since this change touches the core construction path every
example goes through, not an independent new module; all exited
cleanly with correct real output. `BUILD_TRACKER.md` updated, tracker
artifact regenerated (16 milestones/32 phases/76 items/6 known gaps/3
fixed gaps) and republished. Committed locally (`13b58c5`); push
deferred pending explicit user confirmation.

Next: item 1 of the user's own ordering — the other 37 component
fragments.
