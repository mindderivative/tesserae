# LOG — M13: Widget Catalog, Part 2f — Search & Progress/Status

- Closing out the original Part 2 scope's category list: Search and
  Progress & Status.

## What shipped

1. `src/tesserae/widgets/search.py` — `search_bar`/`search_view`,
   verified directly against `window_factory.rs`.
2. `src/tesserae/widgets/progress.py` — `circular_progress`/
   `linear_progress`/`loading_indicator`. Second real application of
   M8's naming translation: `add_loading_indicator`'s `color=` is a
   genuine RGBA tint for the spinner's own glyph, no background of its
   own — translated to `foreground=` in Tesserae's own API.
3. `src/tesserae/widgets/__init__.py` extended to re-export all 5.
4. `tests/test_widgets_search.py` (3 tests) / `test_widgets_progress.py`
   (4 tests) — proving `search_bar`'s returned `TextField` is genuinely
   wireable via `set_on_change`, progress `value` parity, and the
   `foreground=`→`color=` translation reaching `tre` without raising.
- Verification: `pytest tests/` 70 passed (63 prior + 7 new), 0
  regressions.

## Status

**M13 is complete.** Search and Progress & Status are real, tested,
and committed (`0023c4a`); push deferred pending explicit user
confirmation.

Next: Date & Time and Media & Graphics — the last 2 widget categories.
Then Part 3 (YAML component macro-expansion).
