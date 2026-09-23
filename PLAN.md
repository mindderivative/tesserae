# PLAN — M12: Widget Catalog, Part 2e — Overlays

*(Replaces the prior M11 plan in this file — M11 is complete, committed.)*

## Goal

Continue the widget catalog: `dialog`/`snackbar`/`side_sheet`/`menu`/
`menu_item`/`tooltip` — `tre`'s own "Overlays" category — same
thin-delegate pattern M8-M11 established.

## Status

**Complete.** `src/tesserae/widgets/overlays.py` — all 6, verified
directly against `window_factory.rs` (including `add_snackbar`'s
`(container, action|None, close|None)` return shape).
`src/tesserae/widgets/__init__.py` extended.

Real scope decision: deliberately does not wrap `Window.open_*`/
`close_*` (e.g. `open_dialog`/`close_dialog`) — those are already
plain, minimal `Window` methods with no naming ambiguity or
construction-time logic to delegate around, so a wrapper would only
add indirection, not clarity. None of these 6 expose an ambiguous
color kwarg, so M8's naming translation wasn't needed here.

7 new pytest tests (`test_widgets_overlays.py`): parity on
`corner_radius`, `add_snackbar`'s real `None`-shape for an omitted
`action_label`/`closable` reproduced through the delegate, and
`build_menu`'s real `ValueError` on an empty item list reproduced
through `menu(...)`. Full suite: 63 passed (56 prior + 7 new), 0
regressions. `BUILD_TRACKER.md` updated, tracker artifact regenerated
(12 milestones/23 phases/48 items/4 known gaps/1 fixed gap) and
republished. Committed locally (`416ab3a`); push deferred pending
explicit user confirmation.

Next: the remaining widget category in the original Part 2 scope
(Search) plus Date & Time and Media & Graphics. Then Part 3 (YAML
component macro-expansion).
