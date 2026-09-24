# LOG — M19: Part 3, Phase 5 — `split_button` Component Fragments (Buttons & Actions Complete)

- The last fixed-shape widget in Buttons & Actions: `split_button`,
  all 5 real MD3 variants.

## What shipped

1. `SplitButtonElevated`/`Filled`/`FilledTonal`/`Outlined`/`Text` — an
   auto-sized `Container` wrapping a `ButtonFilled`-shaped leading
   Rect+Text and a square trailing Rect+chevron Icon, both sharing the
   identical real `resolve_button_colors` output per variant.
2. Real, deliberate scope boundary, restated from `tesserae.widgets.
   split_button`'s own docstring: rest-state only, no public Python
   API for the real hover/press shape-tightening animation.
3. Real, useful finding confirmed live before relying on it: a
   declarative `Container` with no explicit `width`/`height` genuinely
   auto-sizes to its children (standard flexbox behavior) — avoids
   needing `{{ }}` arithmetic to compute a total width.
4. `tests/test_fragments_split_button.py` (new file) — 2 real pytest
   tests. Real bug caught in the test itself, not the engine: id-
   namespacing is flat (every id prefixed once by the call-site's own
   id, regardless of nesting depth) — matching pyCopper's own real
   `_namespace_names` precedent — confirmed by direct inspection of
   the expanded YAML before fixing the test's wrong assumption.
- Verification: `pytest tests/` 106 passed (104 prior + 2 new), 0
  regressions.

## Status

**M19 is complete. Buttons & Actions category complete: 22
fragments.** `button_group` (dynamic list) stays real, deliberately
out of scope. Committed locally (`b9542b5`); push deferred pending
explicit user confirmation.

Next: Selection & Input — `checkbox`/`slider` (real declarative
primitives already) and `spin_box` (buildable now). `radio_button`/
`switch` stay blocked — no declarative `NodeKindSpec` variant exists
for either.
