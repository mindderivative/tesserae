# PLAN — M9: Widget Catalog, Part 2b — Selection & Input

*(Replaces the prior M8 plan in this file — M8 is complete, committed.)*

## Goal

Continue the widget catalog: `checkbox`/`slider`/`radio_button`/
`switch`/`spin_box`, same thin-delegate pattern M8 established.

## Real finding before writing these

`checkbox`/`slider`/`radio_button`/`switch` are actual `NodeKind`
primitives in `tre` (not compositions) — confirmed against the
approved plan's own list of the 21 real primitive kinds — already
fully usable from Python with zero blockers. Wrapped anyway, matching
M8's own "accessed as if created by tesserae" goal: a GUI designer
using `tesserae.widgets` shouldn't need to know or care which
underlying widgets are primitives vs. compositions in `tre`. `spin_box`
is a real composition (a text field flanked by minus/plus icon
buttons).

None of these 5 expose an ambiguous color kwarg — `background` already
means "this widget's own fill" everywhere it appears (`checkbox`/
`slider` take it directly; `radio_button`/`switch` are auto-themed with
no color override at all) — so M8's naming-translation decision didn't
need to be applied here.

**Correction to M8's own tracker note**, found while investigating
where that translation actually *should* land: `add_card`/`add_chip`/
`add_badge`/`add_list_item` (the composition-only factories) expose no
raw color kwarg at all, only the already-clear `border_color`/
`variant` — the `background`-as-glyph-color ambiguity lives
specifically on the *primitive* `add_text(background=...)`/
`add_icon(color=...)` factories, confirmed directly against
`window_factory.rs`, not on any composition-only widget category.
Recorded in `BUILD_TRACKER.md`'s "Up next" rather than left standing
as a wrong claim.

## Status

**Complete.** `src/tesserae/widgets/selection.py` — `checkbox`/
`slider`/`radio_button`/`switch`/`spin_box`, same parameter names/
order/defaults as `tre`'s own factories (verified directly against
`window_factory.rs`). `src/tesserae/widgets/__init__.py` extended.

6 new pytest tests (`test_widgets_selection.py`), parity asserted on
each widget's own real gettable state (`get_checked()`/
`.get("thumb_position")`/`.get("select_progress")`/
`.get("toggle_progress")`/`.get("corner_radius")`). Full suite: 37
passed (31 prior + 6 new), 0 regressions. `BUILD_TRACKER.md` updated,
tracker artifact regenerated (9 milestones/17 phases/36 items/4 known
gaps/1 fixed gap) and republished. Committed locally (`b11ef4c`); push
deferred pending explicit user confirmation, per standing policy.

Next: the remaining 6 widget categories (Cards/Lists/Chips/Structural
Rows, Navigation & Shell, Overlays, Search, Date & Time, Media &
Graphs). The Text/Icon primitives (`add_text`/`add_icon`) are where
M8's naming translation actually applies, if/when they get their own
`tesserae.widgets` wrapper — not yet decided which milestone that is.
Then Part 3 (YAML component macro-expansion) — the real "ease of use
to a GUI designer" deliverable.
