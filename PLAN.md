# PLAN — M13: Widget Catalog, Part 2f — Search & Progress/Status

*(Replaces the prior M12 plan in this file — M12 is complete, committed.)*

## Goal

Close out the original Part 2 scope's category list from `tre`'s own
docs: `search_bar`/`search_view` (Search) and `circular_progress`/
`linear_progress`/`loading_indicator` (Progress & Status).

## Status

**Complete.** `src/tesserae/widgets/search.py` — `search_bar`/
`search_view`, verified directly against `window_factory.rs`
(including `add_search_bar`'s real 4-tuple return).
`src/tesserae/widgets/progress.py` — `circular_progress`/
`linear_progress`/`loading_indicator`.

Second real, concrete application of M8's naming translation, found
auditing this category: `add_loading_indicator`'s `color=` is a
genuine RGBA tint for the spinner's own glyph (no background of its
own) — the same "glyph/tint, not a fill" concept M8 named `foreground`.
`loading_indicator(foreground=...)` translates internally.

7 new pytest tests across `test_widgets_search.py`/
`test_widgets_progress.py`. Full suite: 70 passed (63 prior + 7 new),
0 regressions. `BUILD_TRACKER.md` updated, tracker artifact
regenerated (13 milestones/25 phases/54 items/4 known gaps/1 fixed
gap) and republished. Committed locally (`0023c4a`); push deferred
pending explicit user confirmation.

Next: Date & Time and Media & Graphics — the last 2 widget categories
from the original 38-widget scope. Then Part 3 (YAML component
macro-expansion) — the real "ease of use to a GUI designer" deliverable.
