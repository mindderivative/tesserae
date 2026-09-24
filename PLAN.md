# PLAN — M18: Part 3, Phase 4 — `icon_button`/`fab`/`extended_fab` Component Fragments

*(Replaces the prior M17 plan in this file — M17 is complete, committed.
Continues item 1, now unblocked by `tre`'s new declarative `kind:
Icon`.)*

## Goal

The first 3 widget families that actually need an icon glyph:
`icon_button` (4 variants), `fab` (4 variants), `extended_fab` (4
variants).

## Status

**Complete, both phases.**

`icon_button` reuses `resolve_button_colors` directly (confirmed:
`"standard"` maps to `"text"`'s own colors). `fab`/`extended_fab` use
`resolve_fab_colors`; a real, useful finding — both get fixed MD3
elevation/shape tokens baked directly into the fragment (`elevation:
level_3`, and `corner_radius: large` for Extended FAB specifically),
confirmed equal to the real unthemed constants (`ELEVATION_LEVEL_3 ==
3.0`, `SHAPE_LARGE == 16.0 == EXTENDED_FAB_CORNER_RADIUS`) — no param
needed for those two, unlike plain FAB's own size-dependent
`corner_radius`.

Real, deliberate scope boundary: only `extended_fab`'s leading-icon
shape shipped — the icon-less shape is a genuine structural difference
(different padding, no `Icon` child) `{{ }}` can't conditionally
express, deferred as a named gap.

`tests/test_fragments_buttons.py` (new file) — 3 real pytest tests,
each looping over its family's 4 variants and cross-checking against
`tesserae.widgets`'s own imperative output (12 real variant checks) —
all MATCH. Full suite: 104 passed (101 prior + 3 new), 0 regressions.
`BUILD_TRACKER.md` updated, tracker artifact regenerated (18
milestones/37 phases/89 items/9 known gaps/3 fixed gaps) and
republished. Committed locally (`8c6500e`); push deferred pending
explicit user confirmation.

17 fragments total so far. Next: `split_button` (a fixed 2-button+
chevron shape, not a dynamic list), then onward through the remaining
categories.
