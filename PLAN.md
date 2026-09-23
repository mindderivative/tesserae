# PLAN — M14: Widget Catalog, Part 2g — Media/Graphics & Date/Time (Part 2 complete)

*(Replaces the prior M13 plan in this file — M13 is complete, committed.)*

## Goal

Close out the widget catalog entirely: `image`/`video`/`icon`/
`graph_node`/`node_graph` (Media & Graphics) and `date_picker_day`/
`time_picker_dial`/`period_selector` (Date & Time Pickers) — the last
2 categories in `tre`'s own `docs/guide/components.md`.

## Status

**Complete. Part 2 of the approved plan is now fully done.**
`src/tesserae/widgets/media.py` — all 5, with `icon`'s real naming
translation applied (`add_icon`'s `color=` is the glyph's own paint,
no background at all — same reasoning `image`/`video` already have for
taking no color param). `src/tesserae/widgets/date_time.py` — all 3
(named to avoid shadowing the stdlib `datetime` module).

Real, deliberate scope note: no dedicated `tesserae.widgets.text`
wrapper for the bare `add_text` primitive was built — every widget
that displays text does so through its own already-clear param
(`label`/`headline`/`content`), never a raw passthrough to `add_text`'s
own ambiguous `background=`.

11 new pytest tests (`test_widgets_media.py`/`test_widgets_date_time.py`),
including real file-loading parity via a new checked-in 1×1 PNG
fixture (`tests/fixtures/pixel.png`, hand-built with `zlib`, no
external dependency), and 3 real error-path checks (`add_image`'s
`OSError`, `add_icon`'s `ValueError`, `add_period_selector`'s
`ValueError`) reproduced through the delegates. Full suite: 81 passed
(70 prior + 11 new), 0 regressions. `BUILD_TRACKER.md` updated,
tracker artifact regenerated (14 milestones/27 phases/61 items/5 known
gaps/1 fixed gap) and republished. Committed locally (`97cfb59`); push
deferred pending explicit user confirmation.

**Summary of the naming-consistency work across the whole catalog:** 3
real, concrete translations applied where `tre`'s own vocabulary was
genuinely ambiguous — `add_toolbar`'s `color`→`tone` (M11, a named
variant selector, not a color), `add_loading_indicator`'s
`color`→`foreground` (M13, a glyph tint), `add_icon`'s
`color`→`foreground` (M14, a glyph paint). Everywhere else, `tre`'s own
names were already clear and kept as-is.

Next: Part 3 — the YAML component macro-expansion layer, the real
"ease of use to a GUI designer" deliverable.
