# PLAN — M24: Part 3, Phase 10 — Search, Progress & Status, Media & Graphics, Date & Time Component Fragments

*(Replaces the prior M23 plan in this file — M23 is complete, committed.)*

## Goal

`SearchBar`/`SearchView` (Search), `Image` (Media & Graphics), `DatePickerDay` (4 real states)/`PeriodSelectorAM`/`PeriodSelectorPM` (Date & Time) — the last 4 widget categories in the original scope. Progress & Status (`circular_progress`/`linear_progress`/`loading_indicator`) confirmed and documented as zero-fragment, not silently dropped.

## Status

**Complete, both phases.**

9 new fragments shipped, all cross-checked against `tesserae.widgets` where a numeric readback exists. Progress & Status confirmed blocked for all 3 widgets via direct failing-test verification — no declarative `NodeKindSpec` equivalent, matching `tre`'s own M74 scope note. `video`/`node_graph`/`graph_node`/`TimePickerDial` confirmed blocked the same way.

Real finding: `TextSpec.content` is Rust `String`-typed — `DatePickerDay*`'s `day` param must be a quoted string (`day: "15"`); a bare integer fails deserialization since whole-value `{{ }}` substitution preserves the caller's real Python type verbatim. Documented in all 4 fragments' own headers.

Real finding: `ContentFitSpec`'s declarative values are PascalCase (`Cover`/`Contain`/`Fill`), not the lowercase strings `image()`'s own imperative `fit=` kwarg accepts. `src:` resolves relative to the calling view's own directory, not the working directory. Both documented in `Image_Component.yaml`'s own header.

Real test bug caught while authoring `test_fragments_remaining_categories.py`: the quoted-string-day test originally wrapped `pytest.raises` around `expand_components(...)` (pure string substitution, never raises) instead of the actual `View(source=...)` call where the real deserialize error surfaces. Fixed before the file was committed.

6 new pytest tests (`test_fragments_remaining_categories.py`). Full suite: 134 passed (128 prior + 6 new), 0 regressions. `BUILD_TRACKER.md` updated, tracker artifact regenerated (24 milestones/49 phases/126 items/10 known gaps/3 fixed gaps) and republished. Committed locally (`4994194`); push deferred pending explicit user confirmation.

59 fragments total. Every category in the original widget-catalog scope has now been explored to its real, natural completion point — the remaining unbuilt widgets are a structural boundary (dynamic-list widgets, primitives with no declarative `NodeKindSpec`), not mechanical follow-up. Item 1 of the standing 3-item follow-up list ("Start 3, then move to 2 and then 1") is complete.
