# LOG — M20: Part 3, Phase 6 — Selection & Input Component Fragments

- Selection & Input category: `Checkbox`/`Slider`/`SpinBox`. `radio_
  button`/`switch` stay out of scope — no declarative `NodeKindSpec`
  variant exists for either.

## What shipped

1. `Checkbox_Component.yaml`/`Slider_Component.yaml` — `checked`/
   `value` map directly onto `WidgetSpec`'s own top-level fields (not
   a sibling block, confirmed against `build.rs`), no `corner_radius`
   param (both `add_checkbox`/`add_slider` hardcode `0.0`
   imperatively). Real, honest gap named directly, not fixed here:
   `mark_tint`/`text_tint` theming has no declarative equivalent at
   all.
2. `SpinBox_Component.yaml` — a real, deliberate structural
   translation: `add_spin_box` builds 3 independent sibling nodes via
   absolute x/y arithmetic; the fragment composes the identical result
   via a `Container` + `flex_direction: Horizontal`. Second real token
   match found: `corner_radius: small == CHIP_CORNER_RADIUS ==
   SHAPE_SMALL` exactly.
3. `tests/test_fragments_selection.py` (new file) — 4 real pytest
   tests.
- Verification: `pytest tests/` 110 passed (106 prior + 4 new), 0
  regressions.

## Status

**M20 is complete. 25 fragments total so far.** Committed locally
(`1aa1549`); push deferred pending explicit user confirmation.

Next: Cards/Lists/Chips/Structural Rows — `card` (3 variants), `chip`
(4 variants), `list_item`, `badge` (2 structural shapes), `divider`,
`link`, `accordion_header`, `tree_node`.
