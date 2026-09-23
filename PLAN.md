# PLAN — M10: Widget Catalog, Part 2c — Cards, Lists, Chips & Structural Rows

*(Replaces the prior M9 plan in this file — M9 is complete, committed.)*

## Goal

Continue the widget catalog: `card`/`list_`/`list_item`/`chip`/
`badge`/`divider`/`link`/`accordion_header`/`tree_node` — the 9 real
factories in `tre`'s own "Cards, Lists, Chips & Structural Rows"
category — same thin-delegate pattern M8/M9 established.

## Status

**Complete.** `src/tesserae/widgets/structural.py` — all 9, verified
directly against `window_factory.rs` (including the two-element return
tuples `add_accordion_header`/`add_tree_node` produce).
`src/tesserae/widgets/__init__.py` extended (`list_`/named to avoid
shadowing Python builtins).

Confirms M9's own naming-consistency correction: none of these 9
expose a raw color kwarg beyond the already-clear `border_color`
(`add_list`/`add_link` take no color at all) — the
`background`-as-glyph-color issue really is confined to the primitive
`add_text`/`add_icon` factories, not this category either.

12 new pytest tests (`test_widgets_structural.py`): parity on
`elevation`/`corner_radius`/`border_width`, a real kwarg-forwarding
check (`card`'s `elevated` vs. `outlined` variant resolves to
different elevation *and* border width), `add_list`'s real `ValueError`
on an empty item list reproduced through the delegate, and
`add_tree_node`'s `leaf=True` correctly producing `chevron=None`. Full
suite: 49 passed (37 prior + 12 new), 0 regressions. `BUILD_TRACKER.md`
updated, tracker artifact regenerated (10 milestones/19 phases/40
items/4 known gaps/1 fixed gap) and republished. Committed locally
(`e76ee8a`); push deferred pending explicit user confirmation.

Next: the remaining 3 widget categories in the original Part 2 scope
(Navigation & Shell, Overlays, Search) plus Date & Time and Media &
Graphics. Then Part 3 (YAML component macro-expansion) — the real
"ease of use to a GUI designer" deliverable.
