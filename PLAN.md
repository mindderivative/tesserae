# PLAN — M8: Widget Catalog, Part 2a — Buttons & Actions

*(Replaces the prior M7 plan in this file — M7 is complete, committed.
A real, user-directed course correction reshaped this milestone's own
design partway through, recorded below rather than silently revised.)*

## Goal

Give a Tesserae app a widget catalog it can import as its own, matching
the user's own direction: "Unless direct rendering is required all
other components should be developed using Tesserae." Buttons & Actions
is the first of 8 real categories (38 widgets total) from the approved
plan's Part 2.

## Real course correction (before writing the first widget)

The approved plan called for from-scratch Python reimplementations of
each widget's MD3 color/shape/elevation resolution, mirroring `tre`'s
own internal `window_factory.rs` logic. Before writing `buttons.py`, a
real, load-bearing check: `window.add_button()` and its 37 siblings
already work perfectly from Python *today* -- a from-scratch port
would duplicate real, working Rust logic for zero fidelity gain, and
for `add_button_group`/`add_split_button` specifically could *never*
reach parity (their hover/press shape-tightening and reflow animations
live in `PaintProperties` fields with no public Python setter).

Presented to the user via `AskUserQuestion`. Their own reply reframed
the real goal: "It's not about accessing the widgets it's about ease
of use to a GUI designer." That reframe, plus a follow-up message
about naming clarity, settled the actual design:

1. **`tesserae.widgets` = thin, faithful delegates** to `tre`'s own
   native `add_*` factories -- zero duplicated logic, full fidelity
   (including the two animations a from-scratch port could never
   reach), giving Tesserae apps one consistent namespace to import
   from.
2. **The real "ease of use to a GUI designer" deliverable is Part 3**
   (YAML component macro-expansion, not yet started) -- a designer
   writing `kind: Button` should never need to know it's a Rect+Text
   composition underneath.
3. **A real, separate naming-consistency finding**, confirmed directly
   in `engine-spec/src/build.rs:547-564`: `tre`'s own `style.background`
   doubles as a `Text` node's *glyph* color (not an actual background
   fill), and `add_icon`/`add_badge` separately call the same concept
   `color=`. Tesserae's own API will translate to clear, consistent
   names (`background` = fill, `foreground` = glyph/text color) at the
   point a widget actually exposes one of these -- none of this
   milestone's 6 button-family widgets do (their only color kwarg is
   the already-clear `border_color`), so the translation starts with
   the next category (Text/Icon-family).

## Status

**Complete.** `src/tesserae/widgets/buttons.py` -- `button`/
`icon_button`/`fab`/`extended_fab`/`split_button`/`button_group`, each
delegating directly to `tre`'s matching native factory with identical
parameter names/order/defaults (verified against the real
`#[pyo3(signature = ...)]` declarations in `window_factory.rs`, not
assumed). `src/tesserae/widgets/__init__.py` re-exports all 6.

9 new pytest tests (`test_widgets_buttons.py`): parity against the
native call on every gettable property (`corner_radius`/`elevation`/
`border_width` -- `Node.get()` has no `"background"` property at all,
confirmed directly from `node.rs`, so color parity isn't independently
assertable and isn't needed given the delegate calls the identical
underlying function), plus real kwarg-forwarding checks (`variant=`,
`size=`) proving the wrapper doesn't silently drop an argument. Full
suite: 31 passed (22 prior + 9 new), 0 regressions. `BUILD_TRACKER.md`
updated -- also corrected a real tracker-currency miss from M7's own
commit (Phase 2/3 checkboxes and the Top Metrics row were never
flipped to ✅ despite the real deliverables existing on disk; verified
all three existed before fixing). Tracker artifact regenerated (8
milestones/15 phases/32 items/4 known gaps/1 fixed gap) and republished.
Committed locally (`a4a76b5`); push deferred pending explicit user
confirmation, per standing policy.

Next: the remaining 7 widget categories (Selection & Input, Cards/
Lists/Chips/Structural Rows, Navigation & Shell, Overlays, Search, Date
& Time, Media & Graphs), applying the same thin-delegate pattern and
the naming-consistency translation where a widget actually exposes an
ambiguous color kwarg. Then Part 3 (YAML component macro-expansion).
