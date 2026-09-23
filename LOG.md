# LOG — M11: Widget Catalog, Part 2d — Navigation & Shell Composition

- Continuing the widget catalog: `tabs`/`navigation_rail`/
  `navigation_drawer`/`toolbar`/`top_app_bar`/`status_bar`, same
  thin-delegate pattern M8-M10 established.

## What shipped

1. `src/tesserae/widgets/navigation.py` — all 6, verified directly
   against `crates/engine-py/src/window_factory.rs`'s real signatures.
2. `src/tesserae/widgets/__init__.py` extended to re-export all 6.
3. Real, concrete first application of M8's naming-translation
   decision: `add_toolbar`'s own `color: Option<&str>` param isn't an
   RGBA color at all — confirmed directly at
   `window_factory.rs:6727-6734`, it accepts exactly two named strings
   (`"standard"`/`"vibrant"`), a container-tone selector. Calling it
   `color` is its own real source of confusion — every other `color`/
   `background` kwarg across the whole catalog takes an RGBA tuple, so
   a caller would reasonably expect one here too. Tesserae's own
   `toolbar(tone=...)` renames it, translating internally when it
   delegates.
4. `tests/test_widgets_navigation.py` — 7 new pytest tests, including
   a dedicated check that `toolbar(tone="vibrant")` reaches the
   identical resolution as the native `add_toolbar(color="vibrant")`
   call — proving the translation is real, not just cosmetic.
- Verification: `pytest tests/` 56 passed (49 prior + 7 new), 0
  regressions.

## Status

**M11 is complete.** Navigation & Shell Composition is real, tested,
and committed (`66d2137`); push deferred pending explicit user
confirmation.

Next: the remaining 2 widget categories in the original Part 2 scope
(Overlays, Search) plus Date & Time and Media & Graphics. Then Part 3
(YAML component macro-expansion).
