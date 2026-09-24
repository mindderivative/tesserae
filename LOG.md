# LOG — M21: Part 3, Phase 7 — Cards, Lists, Chips & Structural Rows Component Fragments

- `Card` (3 variants), `Chip` (multiple variants), `ListItem`, `Badge`
  (2 structural shapes), `Divider`, `AccordionHeader`, `TreeNode` (2
  structural shapes). `link` stays out of scope.

## What shipped

1. `CardElevated`/`CardFilled`/`CardOutlined` — content-free Rects,
   `corner_radius: medium` (a real, confirmed token match).
2. `ChipAssist`/`ChipFilter`/`ChipFilterSelected`/`ChipInput`/
   `ChipSuggestion` — real finding: 5 named states, not 4 (`input`/
   `suggestion` share unselected `filter`'s own colors but are real,
   distinct MD3 names kept as their own fragments); `ChipFilterSelected`
   is a real, distinct structural shape (automatic checkmark Icon, not
   a color swap).
3. `ListItem` — the common single-line, no-icon case.
4. `BadgeDot`/`BadgeLabeled` — the two real structural shapes, fixed
   `error`/`on_error` colors.
5. `Divider` — takes `width`/`height` directly, avoiding 2 fragments
   for what isn't a real MD3 variant.
6. `AccordionHeader` — real, useful finding: `flex_grow: 1` on the
   headline avoids `add_accordion_header`'s own width-subtraction
   arithmetic entirely.
7. `TreeNodeLeaf`/`TreeNodeBranch` — the two real structural shapes.
   Real `depth * TREE_NODE_INDENT_WIDTH` arithmetic handled by
   requiring the already-computed `left_padding` as a param.
8. `link` confirmed blocked — `NodeKind::Link` has no declarative
   equivalent, the same real gap already named for `radio_button`/
   `switch`.
9. `tests/test_fragments_structural.py` (new file) — 9 real pytest
   tests, including a direct proof `TreeNodeLeaf` has no `chevron`
   node at all.
- Verification: `pytest tests/` 119 passed (110 prior + 9 new), 0
  regressions.

## Status

**M21 is complete. 40 fragments total so far.** Committed locally
(`353b071`); push deferred pending explicit user confirmation.

Next: Navigation & Shell (mostly blocked as dynamic-list), Overlays
(fixed-shape, buildable), Search, Progress & Status, Media & Graphics,
Date & Time.
