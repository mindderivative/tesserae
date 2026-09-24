# LOG — M23: Part 3, Phase 9 — Overlays Component Fragments

- `Dialog`, `Snackbar`, `SideSheetModal`/`SideSheetStandard`,
  `MenuItem`, `Tooltip` — every fixed-shape widget in Overlays.

## What shipped

1. `Dialog` — returns the scrim, not the panel (real finding);
   `scrim_width`/`scrim_height` required params; `corner_radius:
   extra_large`/`elevation: level_3`/`opacity: 0.32` all real, fixed,
   confirmed values.
2. `Snackbar` — the common no-action/non-closable case; `corner_
   radius: extra_small`/`elevation: level_3`.
3. `SideSheetModal`/`SideSheetStandard` — the two real structural
   shapes. Real, significant finding: `add_side_sheet`'s own base
   `paint.corner_radius` is a literal `0.0` — the real visual rounding
   comes entirely from a per-corner `corner_radii_override` `Node.get`
   never reads back, so a `corner_radius` cross-check isn't meaningful
   here, unlike everywhere else in this catalog. Both fragments use a
   uniform `corner_radius: large` instead of matching the imperative's
   misleading `0.0` readback.
4. `MenuItem` — the common no-icon/no-submenu-chevron case.
5. `Tooltip` — `corner_radius: extra_small`.
6. `tests/test_fragments_overlays.py` (new file) — 5 real pytest
   tests. Real bug caught in the test itself, not a fragment:
   `side_sheet(modal=True)` returns the outer scrim, not the inner
   panel — an initial test compared the wrong two nodes' `elevation`,
   fixed by comparing what each side actually returns. A second,
   unrelated f32-vs-f64 float precision artifact needed
   `pytest.approx`.
- Verification: `pytest tests/` 128 passed (123 prior + 5 new), 0
  regressions.

## Status

**M23 is complete. 50 fragments total so far.** Committed locally
(`3e2b841`); push deferred pending explicit user confirmation.

Next: Search, Progress & Status, Media & Graphics, Date & Time — the
last 4 categories.
