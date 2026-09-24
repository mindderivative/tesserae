# LOG — M25: Scoping the Next Boundary + `NodeGraph` Component Fragment

- User asked to scope the two real boundaries M24 named. Investigation
  surfaced a real correction to M24's own categorization, not just a
  plan.

## What shipped

1. Real correction: `add_node_graph` is a plain themed `NodeKind::Rect`
   (`background: surface_container_low`, `corner_radius`/`elevation`
   both literal `0.0`) — zero new `tre` primitives needed. Shipped as
   `NodeGraph_Component.yaml` today.
2. Real correction: `add_video` builds `NodeKind::Image` with a
   synthetic transparent placeholder — `kind: Image` is already
   declarative, but `ImageSpec.src` is a required file path with no
   blank-placeholder concept, so a faithful port isn't possible today.
   User declined a non-faithful poster-image approximation; filed
   [`tre` issue #2](https://github.com/mindderivative/tre/issues/2)
   requesting `ImageSpec.src` become optional, scoped precisely to the
   placeholder shape (not a declarative video-source concept).
3. Real reclassification: `graph_node` needs a live `graph` node
   reference as its own attachment parent — not a missing
   `NodeKindSpec` at all. Moved into the same "runtime-constructed"
   bucket as `tabs`/`navigation_rail`/`navigation_drawer`/
   `button_group`/`list_`/`menu`.
4. `tests/test_fragments_media_graph.py` (new file) — 1 real pytest
   test for `NodeGraph`.
5. Sized (not built) the two real remaining fronts: `tre`-side
   `NodeKindSpec` additions for 7 primitives (mirrors the proven M74
   `Icon` precedent); a macro-layer loop/repeat construct for the 6
   dynamic-list widgets (real novel design surface, permanent
   load-time-only limitation regardless of syntax).
- Verification: `pytest tests/` 135 passed (134 prior + 1 new), 0
  regressions.

## Status

**M25 is complete. 60 fragments total.** Committed locally (`8d87a3c`);
push deferred pending explicit user confirmation.

Both remaining fronts are scoped, not started. Next step is the
user's: pick a front (`tre`-side primitives, or the macro-layer loop
construct), or continue scoping something else.
