# LOG — M14: Widget Catalog, Part 2g — Media/Graphics & Date/Time (Part 2 complete)

- Closing out the widget catalog: Media & Graphics and Date & Time
  Pickers, the last 2 categories.

## What shipped

1. `src/tesserae/widgets/media.py` — `image`/`video`/`icon`/
   `graph_node`/`node_graph`. `icon` gets the real naming translation
   M8/M9's finding always pointed to: `add_icon`'s `color=` is the
   glyph's own paint, no background at all — translated to
   `foreground=`.
2. `src/tesserae/widgets/date_time.py` — `date_picker_day`/
   `time_picker_dial`/`period_selector` (named to avoid shadowing the
   stdlib `datetime` module).
3. `src/tesserae/widgets/__init__.py` extended to re-export all 8.
4. `tests/fixtures/pixel.png` — a real, minimal valid 1×1 PNG,
   hand-built via `zlib`/`struct` (no PIL dependency in this venv),
   checked in for `image(...)`'s own real file-loading test coverage.
5. `tests/test_widgets_media.py` (6 tests) / `test_widgets_date_time.py`
   (5 tests) — including 3 real error-path checks (`add_image`'s
   `OSError` on a missing file, `add_icon`'s `ValueError` on an unknown
   name, `add_period_selector`'s `ValueError` on an invalid value) all
   reproduced through the delegates, not just happy-path parity.
- Verification: `pytest tests/` 81 passed (70 prior + 11 new), 0
  regressions.

## Status

**M14 is complete. Part 2 of the approved plan is now fully done** --
every widget-catalog category from `tre`'s own docs has a real, tested
`tesserae.widgets` counterpart. Committed locally (`97cfb59`); push
deferred pending explicit user confirmation.

Summary across the whole catalog: 3 real naming translations applied
where `tre`'s own vocabulary was genuinely ambiguous (`add_toolbar`
color->tone, `add_loading_indicator` color->foreground, `add_icon`
color->foreground) -- everywhere else `tre`'s own names were already
clear.

Next: Part 3 -- the YAML component macro-expansion layer. This is the
real "ease of use to a GUI designer" deliverable per the user's own
direct correction earlier in this milestone sequence.
