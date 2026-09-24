# LOG — M22: Part 3, Phase 8 — Navigation & Shell Component Fragments (Fixed-Shape Members)

- The real, fixed-shape widgets in Navigation & Shell: `toolbar` (both
  variants), `top_app_bar`, `status_bar`.

## What shipped

1. `ToolbarDocked`/`ToolbarFloating` — content-free, horizontal-only.
   `tone` becomes a plain `background` role-name param instead of a
   separate fragment axis. `elevation: level_3` reused from the FAB
   fragments' own real token match.
2. `TopAppBar` — the common no-leading/no-trailing-icons case,
   `flex_grow: 1` on the title (avoids `add_top_app_bar`'s own
   width-subtraction arithmetic).
3. `StatusBar` — real correction caught before it shipped wrong: an
   initial draft guessed its color role/typography without checking
   the source first (assumed `on_surface`/`body_medium`) — caught by
   reading `add_status_bar`'s own body directly, fixed to the real
   values (`on_surface_variant`/`label_small`) before any test ran.
4. `tests/test_fragments_navigation.py` (new file) — 4 real pytest
   tests, all cross-checked against `tesserae.widgets`.
- Verification: `pytest tests/` 123 passed (119 prior + 4 new), 0
  regressions.

## Status

**M22 is complete. 44 fragments total so far.** Committed locally
(`a0385aa`); push deferred pending explicit user confirmation.

Next: Overlays (`dialog`/`snackbar`/`side_sheet`/`menu_item`/`tooltip`
— all fixed-shape, buildable).
