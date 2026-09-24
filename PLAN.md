# PLAN — M20: Part 3, Phase 6 — Selection & Input Component Fragments

*(Replaces the prior M19 plan in this file — M19 is complete, committed.)*

## Goal

Selection & Input category: `Checkbox`/`Slider`/`SpinBox`. `radio_
button`/`switch` stay out of scope — no declarative `NodeKindSpec`
variant exists for either.

## Status

**Complete, both phases.**

`Checkbox_Component.yaml`/`Slider_Component.yaml` map `checked`/
`value` directly onto `WidgetSpec`'s own top-level fields, no
`corner_radius` param (both `add_checkbox`/`add_slider` hardcode
`0.0`). Real, honest gap named in `Checkbox_Component.yaml`'s own
header: `mark_tint`/`text_tint` theming has no declarative equivalent
at all — a declarative checkbox/text field always paints its default
tint, regardless of theme.

`SpinBox_Component.yaml` — a real, deliberate structural translation:
`add_spin_box` builds 3 independent sibling nodes via absolute x/y
arithmetic; the fragment composes the identical result via a
`Container` + `flex_direction: Horizontal` instead. `add_spin_box`
takes only `value`, so every other value is a literal/token —
including a second real token match, `corner_radius: small ==
CHIP_CORNER_RADIUS == SHAPE_SMALL`.

4 new pytest tests (`test_fragments_selection.py`). Full suite: 110
passed (106 prior + 4 new), 0 regressions. `BUILD_TRACKER.md` updated,
tracker artifact regenerated (20 milestones/41 phases/97 items/9 known
gaps/3 fixed gaps) and republished. Committed locally (`1aa1549`);
push deferred pending explicit user confirmation.

25 fragments total so far. Next: Cards/Lists/Chips/Structural Rows —
`card` (3 variants), `chip` (4 variants), `list_item`, `badge` (2
structural shapes), `divider`, `link`, `accordion_header`, `tree_node`.
