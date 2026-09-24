# PLAN — M26: Detailed Scoping: `tre`-Side Primitive Additions & Macro-Layer Loop Construct

*(Replaces the prior M25 plan in this file — M25 is complete, committed.)*

## Goal

Scope both of M25's remaining fronts as separate, buildable-later milestones — full technical design, not just a one-line summary. No implementation this milestone.

## Status

**Complete.**

Front A (tentatively M27, `tre`-side `NodeKindSpec` additions for `radio_button`/`switch`/`link`/`circular_progress`/`linear_progress`/`loading_indicator`/`time_picker_dial`): sized every real constructor against `WidgetSpec`'s existing fields. Found and corrected an incomplete part of M25's own summary — 5 of the 7 primitives hardcode `PaintProperties.background` to `TRANSPARENT` and carry their entire real visual in internal per-kind tint fields that `Checkbox`/`Slider`'s own existing declarative precedent never had to theme-resolve. Scoped a small reusable role-resolve-with-fallback helper to close this, not a new subsystem. Found `loading_indicator` needs an extra required `paint.shape` seeding step (avoids a real, confirmed first-tick flash bug) and that `time_picker_dial`'s real new fields are `hour: u8`/`minute: u8`, not the `mode` field M25 guessed.

Front B (tentatively M28, macro-layer loop/repeat construct): checked `pyCopper` directly (this macro layer's own stated precedent) — found no repeat/loop construct there at all, confirming genuinely new design territory. Found the 6 dynamic-list widgets aren't uniform: `add_list` takes pre-built `Node`s (pure composition, the loop construct's cleanest fit — repeating the already-shipped `ListItem` fragment); `add_tabs`/`add_button_group`/`add_navigation_rail`/`add_navigation_drawer`/`add_menu` take raw `Vec<String>` and construct real state-dependent active/inactive coloring internally in Rust, which a static `{{ }}`-substitution template can't branch on. A loop construct alone gives full fidelity for `list_` but only a static snapshot for the other 5 without a second, separate new capability (conditional per-item styling).

`BUILD_TRACKER.md` updated (26 milestones/53 phases/138 items/11 known gaps/3 fixed gaps), tracker artifact regenerated and republished. Committed locally (`80deaa2`); push deferred pending explicit user confirmation. No fragments shipped this milestone — 60 total, unchanged. Neither front built — user has not yet chosen which to pursue.
