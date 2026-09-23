# LOG — M9: Widget Catalog, Part 2b — Selection & Input

- Continuing the widget catalog with the same thin-delegate pattern M8
  established. Real finding before writing these: `checkbox`/`slider`/
  `radio_button`/`switch` are actual `NodeKind` primitives in `tre`
  (not compositions) -- already fully usable from Python with zero
  blockers. Wrapped anyway, matching M8's own "accessed as if created
  by tesserae" goal: a GUI designer using `tesserae.widgets` shouldn't
  need to know or care which underlying widgets are primitives vs.
  compositions in `tre`. `spin_box` is a real composition.

## What shipped

1. `src/tesserae/widgets/selection.py` -- `checkbox`/`slider`/
   `radio_button`/`switch`/`spin_box`, same parameter names/order/
   defaults as `tre`'s own factories, verified directly against
   `crates/engine-py/src/window_factory.rs`'s real
   `#[pyo3(signature = ...)]` declarations (an earlier regex-based
   extraction attempt silently produced wrong signatures for all 5 --
   caught by spot-checking against the docs before trusting it, fixed
   by reading each function's own signature line directly).
2. `src/tesserae/widgets/__init__.py` extended to re-export all 5.
3. None of these 5 expose an ambiguous color kwarg, so M8's naming-
   translation decision wasn't needed here. Investigating where it
   *should* land turned up a real correction to M8's own tracker note:
   `add_card`/`add_chip`/`add_badge`/`add_list_item` expose no raw
   color kwarg at all -- the `background`-as-glyph-color ambiguity
   lives specifically on the primitive `add_text`/`add_icon`
   factories. Corrected in `BUILD_TRACKER.md` rather than left standing.
4. `tests/test_widgets_selection.py` -- 6 new pytest tests, parity
   asserted on each widget's own real gettable state.
- Verification: `pytest tests/` 37 passed (31 prior + 6 new), 0
  regressions.

## Status

**M9 is complete.** Selection & Input is real, tested, and committed
(`b11ef4c`); push deferred pending explicit user confirmation.

Next: the remaining 6 widget categories (Cards/Lists/Chips/Structural
Rows, Navigation & Shell, Overlays, Search, Date & Time, Media &
Graphs). Then Part 3 (YAML component macro-expansion) -- the real
"ease of use to a GUI designer" deliverable.
