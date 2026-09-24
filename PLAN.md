# PLAN — M19: Part 3, Phase 5 — `split_button` Component Fragments (Buttons & Actions Complete)

*(Replaces the prior M18 plan in this file — M18 is complete, committed.)*

## Goal

The last fixed-shape widget in Buttons & Actions: `split_button`, all
5 real MD3 variants.

## Status

**Complete, both phases.**

`SplitButtonElevated`/`Filled`/`FilledTonal`/`Outlined`/`Text` — an
auto-sized `Container` (`flex_direction: Horizontal`, `gap: 2`)
wrapping a `ButtonFilled`-shaped leading Rect+Text and a square
trailing Rect+chevron Icon, both sharing the identical real `resolve_
button_colors` output per variant. Rest-state only, matching `tesserae.
widgets.split_button`'s own already-stated scope cut (the hover/press
shape-tightening animation has no public Python API).

Real, useful finding confirmed live: a declarative `Container` with no
explicit `width`/`height` genuinely auto-sizes to its children —
avoids needing `{{ }}` arithmetic for a total width.

2 new pytest tests (`test_fragments_split_button.py`). Real bug caught
in the test itself, not the engine, while writing it: id-namespacing
is flat (one prefix level from the call site, regardless of nesting
depth) — confirmed by direct inspection of the expanded YAML before
fixing the test's wrong assumption. Full suite: 106 passed (104 prior
+ 2 new), 0 regressions. `BUILD_TRACKER.md` updated, tracker artifact
regenerated (19 milestones/39 phases/92 items/9 known gaps/3 fixed
gaps) and republished. Committed locally (`b9542b5`); push deferred
pending explicit user confirmation.

**Buttons & Actions category complete: 22 fragments.** `button_group`
(dynamic list) stays real, deliberately out of scope.

Next: Selection & Input — `checkbox`/`slider` (real declarative
primitives already) and `spin_box` (buildable now). `radio_button`/
`switch` stay blocked — no declarative `NodeKindSpec` variant exists.
