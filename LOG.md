# LOG — M10: Widget Catalog, Part 2c — Cards, Lists, Chips & Structural Rows

- Continuing the widget catalog: `card`/`list_`/`list_item`/`chip`/
  `badge`/`divider`/`link`/`accordion_header`/`tree_node`, same
  thin-delegate pattern M8/M9 established.

## What shipped

1. `src/tesserae/widgets/structural.py` — all 9, verified directly
   against `crates/engine-py/src/window_factory.rs`'s real signatures,
   including the two-element return tuples `add_accordion_header`/
   `add_tree_node` produce (`(header, chevron)`, `(node, chevron |
   None)`).
2. `src/tesserae/widgets/__init__.py` extended to re-export all 9.
3. Confirms M9's own correction: none of these 9 expose a raw color
   kwarg beyond the already-clear `border_color` (`add_list`/`add_link`
   take no color at all).
4. `tests/test_widgets_structural.py` — 12 new pytest tests. Caught one
   broken draft mid-write (a nonsensical placeholder assertion left in
   from an interrupted edit) before it was ever run — the Fact-Forcing
   Gate's re-statement requirement on file creation gave a natural
   pause point to notice and fix it before writing the real content.
- Verification: `pytest tests/` 49 passed (37 prior + 12 new), 0
  regressions.

## Status

**M10 is complete.** Cards/Lists/Chips/Structural Rows is real, tested,
and committed (`e76ee8a`); push deferred pending explicit user
confirmation.

Next: the remaining 3 widget categories in the original Part 2 scope
(Navigation & Shell, Overlays, Search) plus Date & Time and Media &
Graphics. Then Part 3 (YAML component macro-expansion).
