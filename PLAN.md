# PLAN — M23: Part 3, Phase 9 — Overlays Component Fragments

*(Replaces the prior M22 plan in this file — M22 is complete, committed.)*

## Goal

`Dialog`, `Snackbar`, `SideSheetModal`/`SideSheetStandard`, `MenuItem`,
`Tooltip` — every fixed-shape widget in Overlays. `menu` stays out of
scope (dynamic list).

## Status

**Complete, both phases.**

6 new fragments shipped, all cross-checked against `tesserae.widgets`.
Real, useful pattern confirmed twice more: `Dialog`/`SideSheetModal`
both return the full-window scrim imperatively — `scrim_width`/
`scrim_height` are required params on both.

Real, significant finding, not previously encountered: `add_side_sheet`
applies a per-corner `corner_radii_override`, and its own base `paint.
corner_radius` is a literal `0.0` — the real visual rounding lives
entirely in the override, which `Node.get("corner_radius")` never
reads back. A `corner_radius` cross-check isn't meaningful for
`side_sheet` specifically, confirmed by direct testing. Both fragments
use a uniform `corner_radius: large` instead.

Real bug caught in a test, not a fragment: `side_sheet(modal=True)`
returns the outer scrim, not the inner panel — an initial test
compared the wrong two nodes' `elevation`, fixed by comparing what
each side actually returns. A second, unrelated float-precision
artifact needed `pytest.approx`.

5 new pytest tests (`test_fragments_overlays.py`). Full suite: 128
passed (123 prior + 5 new), 0 regressions. `BUILD_TRACKER.md` updated,
tracker artifact regenerated (23 milestones/47 phases/118 items/9
known gaps/3 fixed gaps) and republished. Committed locally
(`3e2b841`); push deferred pending explicit user confirmation.

50 fragments total so far. Next: Search, Progress & Status, Media &
Graphics, Date & Time — the last 4 categories.
