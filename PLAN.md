# PLAN — M25: Scoping the Next Boundary + `NodeGraph` Component Fragment

*(Replaces the prior M24 plan in this file — M24 is complete, committed.)*

## Goal

Scope the two real boundaries M24 named (dynamic-list widgets needing a macro-layer loop construct; primitives with no declarative `NodeKindSpec`) into something concrete enough to plan real work from — not implement either yet.

## Status

**Complete.**

Scoping surfaced a real correction to M24's own work: direct source investigation found `add_video`/`add_node_graph`/`add_graph_node` were wrongly lumped into "confirmed blocked, no declarative kind" — true for none of them in that form. `add_node_graph` is a plain themed `Rect` (zero new primitives needed — shipped today as `NodeGraph_Component.yaml`). `add_video` is a `NodeKind::Image` with a synthetic placeholder — `kind: Image` is already declarative but `ImageSpec.src` is required, so a faithful port needs one small `tre`-side change; filed [`tre` issue #2](https://github.com/mindderivative/tre/issues/2) rather than ship a non-faithful approximation (offered to the user directly, declined). `graph_node` needs a live node reference as its own attachment parent — reclassified from "no primitive" into the same dynamic/runtime-constructed bucket as `tabs`/`menu`/etc., for a different real reason.

`NodeGraph_Component.yaml` shipped: themed `Rect`, `background: surface_container_low`, common no-border case. 1 new pytest test. Full suite: 135 passed (134 prior + 1 new), 0 regressions. `BUILD_TRACKER.md` updated (25 milestones/51 phases/132 items/11 known gaps/3 fixed gaps), tracker artifact regenerated and republished. Committed locally (`8d87a3c`); push deferred pending explicit user confirmation.

Two real fronts sized for a future milestone, neither started: (1) `tre`-side `NodeKindSpec` additions for `radio_button`/`switch`/`link`/`circular_progress`/`linear_progress`/`loading_indicator`/`time_picker_dial` (7 widgets, mirrors the proven M74 `Icon` precedent, mostly reuses existing `WidgetSpec` fields); (2) a macro-layer loop/repeat construct for the 6 dynamic-list widgets (real, novel design surface — `expand.py`'s `_substitute` only handles scalar params today — with a permanent load-time-only limitation regardless of syntax chosen). 60 fragments total.
