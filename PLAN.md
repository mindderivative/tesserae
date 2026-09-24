# PLAN — M21: Part 3, Phase 7 — Cards, Lists, Chips & Structural Rows Component Fragments

*(Replaces the prior M20 plan in this file — M20 is complete, committed.)*

## Goal

`Card` (3 variants), `Chip` (multiple variants), `ListItem`, `Badge`
(2 structural shapes), `Divider`, `AccordionHeader`, `TreeNode` (2
structural shapes). `link` stays out of scope.

## Status

**Complete, both phases.**

15 new fragments, all cross-checked against `tesserae.widgets`'s own
imperative output. Real findings: `Chip`'s real variant space is 5
named states, not 4 (`input`/`suggestion` are real, distinct MD3 names
even though they resolve to identical colors as unselected `filter`);
`ChipFilterSelected` is a real, distinct structural shape (automatic
checkmark Icon); two more real token matches (`corner_radius: medium`
for `Card`, `small` for `Chip`/`BadgeLabeled`); `TreeNode`'s real
`depth * TREE_NODE_INDENT_WIDTH` arithmetic handled by requiring the
already-computed `left_padding` as a param.

`link` confirmed blocked — `NodeKind::Link` has no declarative
equivalent, the same real gap already named for `radio_button`/
`switch`.

9 new pytest tests (`test_fragments_structural.py`), including a real
direct proof `TreeNodeLeaf` has no `chevron` node at all, not just an
empty one. Full suite: 119 passed (110 prior + 9 new), 0 regressions.
`BUILD_TRACKER.md` updated, tracker artifact regenerated (21
milestones/43 phases/106 items/9 known gaps/3 fixed gaps) and
republished. Committed locally (`353b071`); push deferred pending
explicit user confirmation.

40 fragments total so far. Next: Navigation & Shell (mostly blocked as
dynamic-list), Overlays (`dialog`/`snackbar`/`side_sheet`/`menu_item`/
`tooltip` — all fixed-shape, buildable), Search, Progress & Status,
Media & Graphics, Date & Time.
