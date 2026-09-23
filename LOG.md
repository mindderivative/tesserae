# LOG — M12: Widget Catalog, Part 2e — Overlays

- Continuing the widget catalog: `dialog`/`snackbar`/`side_sheet`/
  `menu`/`menu_item`/`tooltip`, same thin-delegate pattern M8-M11
  established.

## What shipped

1. `src/tesserae/widgets/overlays.py` — all 6, verified directly
   against `crates/engine-py/src/window_factory.rs`'s real signatures.
2. `src/tesserae/widgets/__init__.py` extended to re-export all 6.
3. Real scope decision, documented rather than silently assumed:
   `Window.open_*`/`close_*` pairs (`open_dialog`/`close_dialog`, etc.)
   are not wrapped -- they're already minimal, unambiguous methods, so
   a `tesserae.widgets` wrapper would add indirection without adding
   clarity, unlike the construction-time factories which genuinely
   benefit from a uniform namespace.
4. `tests/test_widgets_overlays.py` — 7 new pytest tests.
- Verification: `pytest tests/` 63 passed (56 prior + 7 new), 0
  regressions.

## Status

**M12 is complete.** Overlays is real, tested, and committed
(`416ab3a`); push deferred pending explicit user confirmation.

Next: the remaining widget category in the original Part 2 scope
(Search) plus Date & Time and Media & Graphics. Then Part 3 (YAML
component macro-expansion).
