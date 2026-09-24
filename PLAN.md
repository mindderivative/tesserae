# PLAN — M22: Part 3, Phase 8 — Navigation & Shell Component Fragments (Fixed-Shape Members)

*(Replaces the prior M21 plan in this file — M21 is complete, committed.)*

## Goal

The real, fixed-shape widgets in Navigation & Shell: `toolbar` (both
variants), `top_app_bar`, `status_bar`. `tabs`/`navigation_rail`/
`navigation_drawer` stay out of scope — variable-length lists.

## Status

**Complete, both phases.**

`ToolbarDocked`/`ToolbarFloating`, `TopAppBar`, `StatusBar` — all 4
shipped, content-free where real MD3 anatomy is (an app populates via
nested `component:`/`Node.add_child`).

Real correction caught before it shipped wrong: an initial `StatusBar`
draft guessed its real color role/typography without checking the
source first — caught by reading `add_status_bar`'s own body directly,
fixed to the real values (`on_surface_variant`/`label_small`) before
any test ran against it.

`Toolbar`'s real 3-axis design (variant/orientation/tone) handled by
making `tone` a plain `background` role-name param (not a separate
fragment axis) and shipping horizontal-only (a docked toolbar has no
vertical variant in real MD3 anatomy at all, so that's not even a real
gap for `ToolbarDocked`). `TopAppBar` reuses the `flex_grow: 1`
title-fills-remaining-space pattern already established.

4 new pytest tests (`test_fragments_navigation.py`), all cross-checked
against `tesserae.widgets`. Full suite: 123 passed (119 prior + 4 new),
0 regressions. `BUILD_TRACKER.md` updated, tracker artifact
regenerated (22 milestones/45 phases/111 items/9 known gaps/3 fixed
gaps) and republished. Committed locally (`a0385aa`); push deferred
pending explicit user confirmation.

44 fragments total so far. Next: Overlays (`dialog`/`snackbar`/
`side_sheet`/`menu_item`/`tooltip` — all fixed-shape, buildable).
