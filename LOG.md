# LOG — M24: Part 3, Phase 10 — Search, Progress & Status, Media & Graphics, Date & Time Component Fragments

- `SearchBar`, `SearchView`, `Image`, `DatePickerDaySelected`/`Today`/
  `OutsideMonth`/(default), `PeriodSelectorAM`/`PM` — the last 4
  widget categories, 9 new fragments.

## What shipped

1. `SearchBar` — `params: [placeholder, width, corner_radius]` (pill
   shape, no matching MD3 token); `elevation: level_3`; `flex_grow: 1`
   for the `TextField`.
2. `SearchView` — content-free full-screen overlay; `corner_radius:
   extra_large`/`elevation: level_3`.
3. `Image` — uses `kind: Image` directly. Real findings documented in
   its own header: `ContentFitSpec`'s declarative values are
   PascalCase (`Cover`/`Contain`/`Fill`), not the lowercase strings
   `image()`'s imperative `fit=` accepts; `src:` resolves relative to
   the calling view's own directory.
4. `DatePickerDaySelected`/`Today`/`OutsideMonth`/(default) — the 4
   real distinct visual states; `corner_radius: 24` literal (fixed
   `DATE_CELL_SIZE=48`). Real finding: `TextSpec.content` is Rust
   `String`-typed, so `day` must be passed as a quoted string
   (`day: "15"`) — a bare integer fails deserialization since
   whole-value `{{ }}` substitution preserves the caller's real Python
   type verbatim. Documented in all 4 headers.
5. `PeriodSelectorAM`/`PeriodSelectorPM` — 2 stacked options
   (`flex_direction: Vertical`), `corner_radius: small`.
6. Progress & Status confirmed zero-fragment: `CircularProgress`/
   `LinearProgress`/`LoadingIndicator` all confirmed blocked via
   direct failing `unknown variant` tests, matching `tre`'s own M74
   scope note. `video`/`node_graph`/`graph_node`/`TimePickerDial`
   confirmed blocked the same way.
7. `tests/test_fragments_remaining_categories.py` (new file) — 6 real
   pytest tests. Real bug caught and fixed during authoring: the
   quoted-string-day test originally wrapped `pytest.raises` around
   `expand_components(...)` (never raises — pure string substitution)
   instead of the real `View(source=...)` call where the deserialize
   error actually surfaces.
- Verification: `pytest tests/` 134 passed (128 prior + 6 new), 0
  regressions.

## Status

**M24 is complete. 59 fragments total.** Committed locally
(`4994194`); push deferred pending explicit user confirmation.

Every category in the original widget-catalog scope has now been
explored to its real, natural completion point. The remaining unbuilt
widgets are a real structural boundary — dynamic-list widgets
(`tabs`/`navigation_rail`/`navigation_drawer`/`button_group`/`list_`/
`menu`, no macro-layer loop construct) and primitives with no
declarative `NodeKindSpec` (`radio_button`/`switch`/`link`/progress
indicators/`video`/`node_graph`/`graph_node`/`time_picker_dial`) —
not mechanical follow-up. Neither gap has further scope without new
`tre`-side work or a macro-layer loop construct, neither of which has
been requested.

**Item 1 of the standing 3-item follow-up list ("Start 3, then move to
2 and then 1") is complete.**
