# LOG — M8: Widget Catalog, Part 2a — Buttons & Actions

- Real course correction, found before writing the first widget: the
  approved plan called for from-scratch Python reimplementations of
  each widget's MD3 color/shape/elevation math. `window.add_button()`
  and its 37 siblings already work perfectly from Python today, so a
  from-scratch port duplicates real, working Rust logic for zero
  fidelity gain -- and for `add_button_group`/`add_split_button`
  specifically, could never reach parity at all (their hover/press
  shape-tightening and reflow animations live in `PaintProperties`
  fields with no public Python setter -- confirmed directly by reading
  `window_factory.rs`, not assumed).
- Presented via `AskUserQuestion`; user's own reply reframed the real
  goal directly: "It's not about accessing the widgets it's about ease
  of use to a GUI designer." A follow-up message added a second, real
  requirement: naming has to be genuinely clear, not just delegated --
  "background for background colors and foreground for foreground
  colors, or fill."

## What shipped

1. `src/tesserae/widgets/buttons.py` -- `button`/`icon_button`/`fab`/
   `extended_fab`/`split_button`/`button_group`, each a thin delegate to
   `tre`'s matching native `add_*` factory, `window` as the first
   positional arg (matching `tesserae.component.instantiate`'s own
   convention), identical parameter names/order/defaults -- verified
   against the real `#[pyo3(signature = ...)]` declarations in
   `crates/engine-py/src/window_factory.rs`, not assumed.
2. `src/tesserae/widgets/__init__.py` re-exports all 6.
3. A real, separate naming-consistency finding, confirmed directly in
   `engine-spec/src/build.rs:547-564`: `tre`'s own `style.background`
   doubles as a `Text` node's own *glyph* color (not an actual
   background fill), and `add_icon`/`add_badge` separately name the
   same underlying concept `color=`. Decision, recorded for the next
   category: Tesserae's own API translates to `background` (always a
   real fill) / `foreground` (glyph/text color) at the point a widget
   exposes one of these -- none of this milestone's 6 widgets do (their
   only color kwarg is the already-clear `border_color`).
4. `tests/test_widgets_buttons.py` -- 9 new pytest tests. Two real bugs
   caught and fixed while writing them: `"edit"` isn't a valid icon
   name (`Window`'s icon vocabulary is a fixed 12-name set); and
   `Node.get("background")` doesn't exist at all -- confirmed directly
   from `node.rs`'s real `match` arms, `get()` only returns `f64`
   values, colors are deliberately excluded (the same real reason
   `border_color` is excluded while `border_width` isn't). Rewrote the
   parity assertions onto `corner_radius`/`elevation`/`border_width`
   instead, and added real kwarg-forwarding checks (`variant=`,
   `size=`) so the tests prove the delegate isn't silently dropping an
   argument, not just that *a* Node got constructed.
5. `BUILD_TRACKER.md` -- also corrected a real tracker-currency miss
   left over from M7's own commit: Phase 2/3 checkboxes and the Top
   Metrics status row were never flipped to ✅ before `686214a` landed,
   despite the real MkDocs site/`docs.yml`/`PLAN.md`/`LOG.md` all
   existing on disk -- verified all three were genuinely present
   (`ls docs/`, `.github/workflows/docs.yml`, `mkdocs.yml`/`PLAN.md`/
   `LOG.md`) before flipping the status, not just trusting the old
   commit message.
- Verification: `pytest tests/` 31 passed (22 prior + 9 new), 0
  regressions. `tools/generate_tracker_artifact.py` re-run (8
  milestones, 15 phases, 32 items, 4 known gaps, 1 fixed gap), artifact
  republished. The 3 live-window examples (`counter`/`multi_screen`/
  `todo_list`) were not manually re-launched this milestone -- this
  change added a fully independent module untouched by `App`/`View`/
  `instantiate`, and they're already covered by CI.

## Status

**M8 is complete.** The Buttons & Actions category is real, tested,
and committed (`a4a76b5`); push deferred pending explicit user
confirmation, per standing policy.

Next: the remaining 7 widget categories (Selection & Input, Cards/
Lists/Chips/Structural Rows, Navigation & Shell, Overlays, Search, Date
& Time, Media & Graphs), same thin-delegate pattern, naming translation
applied wherever a widget exposes an ambiguous color kwarg. Then Part 3
(YAML component macro-expansion) -- the real "ease of use to a GUI
designer" deliverable.
