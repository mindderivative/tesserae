# PLAN — `tre`'s Building-Block Program (M34–M43)

*(Replaces the M33 plan in this file — M33 is complete, committed and pushed.)*

## Goal

User-directed: "scope tre's building-block program". `tre`'s approved plan (its M93–M103, D1–D11) moves the declarative layer, reactivity, the MD3 catalog and MD3 theming out of `tre` and into Tesserae. `tre` 0.3.4 has the building blocks with the old API still present. `tre` removes the old API (M98–M99, released as 0.3.5) only after its M97 gate confirms Tesserae no longer uses it. This program is Tesserae's side of that gate. Full write-up: `BUILD_TRACKER.md`, "Program — `tre`'s Building-Block Migration".

## Status

**Approved (2026-09-25)** with all eight recommendations. M34 Phase 1 Steps 1–2 done: `docs/design/building-blocks.md` written. Finding: `tre`'s reactivity is already pure Python apart from a native recording stack, so M35 is small. P3 corrected: `Computed` is eager, not lazy.

## Evidence

- **Inventory of `src/`:** nearly all of Tesserae's ~2,950 lines sit on `tre` APIs that M98–M99 delete: reactivity, `View`/`Component`/`reconcile`/bindings, the cascade and themes, ~50 MD3 factories, 12 MD3 kinds, the ripple and state layer, and the `Rect`/`Container`/`Icon` kinds in 67 fragments.
- **Spike:** 2,000 boxes plus texts built from Python via `create`/`set` took 9.5 ms, against 10.9 ms through `tre`'s `View`. Re-coloring 4,000 nodes took 0.8 ms, against 2.3 ms for `set_theme`. Engine calls aren't the bottleneck; Tesserae's own cascade and binding cost is still to measure (M34).

## Milestones

| | Milestone | Replaces |
|---|---|---|
| M34 | Design and spikes (approval gate) | — |
| M35 | Reactivity | `Signal`, `Computed`, `Effect`, `ViewModel`, `batch`, `untrack` |
| M36 | Bindings and handlers | `binding.rs`, `View._attach` |
| M37 | Declarative engine on primitives | `View`, `reconcile`, `Component`, cascade, `from_view`/`show_view` |
| M38 | MD3 theme | `set_theme`, `Theme`, `engine-md3` color science and tokens |
| M39 | Interaction and accessibility | state layer, ripple, focus rings, per-kind roles |
| M40 | Widgets I: stateful controls | the 12 MD3 kinds |
| M41 | Widgets II: composed catalog and overlays | ~40 composition factories, `open_*` overlays, icon set |
| M42 | Widgets III: inputs, date/time, media, graphs, docking | text fields, pickers, video, node graph, `build_shell` |
| M43 | Migration gate | `tre` M97 Phase 2 Step 2: suite green with removed names stubbed |

## Decisions (M34) — recommendations

1. **P1 YAML format:** keep Tesserae's schema unchanged for app authors, translated to primitives inside Tesserae.
2. **P2 Color science:** a maintained Python port of `material-color-utilities`, accepted only if it matches `tre`'s schemes on reference seeds.
3. **P3 Reactivity:** reproduce `tre`'s semantics exactly (`Computed` is eager), with one test suite run against both.
4. **P4 Bindings:** port `binding.rs`'s safe grammar exactly, and check both evaluators agree on every expression in the repo.
5. **P5 Order:** incremental, bottom-up, suite green after each step.
6. **P6 Public API:** keep every public name. One break, written down: stateful `tesserae.widgets` factories return a small widget object (`.node` plus state) instead of a bare `tre.Node`.
7. **P7 Scope:** rebuild the whole catalog, staged by category; the node graph, docking and app shell last.
8. **P8 Names:** build on `tre` 0.3.4's new API only (`create`, `set`, `on`, `show_layer`, `fill`).

Colour spike done: `materialyoucolor` with `spec_version="2021"` and tone 10 for the four light `on_*_container` roles matches `tre` exactly (784/784), so P2 is accepted. Message sent to `tre`; it agreed and is building the migration guide and the `TRE_FORBID_REMOVED=1` gate shim (its M97 Phase 2).

Spikes (`tools/spikes/`): Python cascade and bindings build 4,000 nodes in 20.7 ms against `tre`'s 11.0 ms, with theme switches and bound updates on par; a full MD3 checkbox on primitives passes 12/12 checks. **M34 complete.**

**M35 complete (2026-09-25):** `tesserae.reactive`, the parity suite (both implementations), and the recording bridge to `tre`'s bindings until M36; 455 passed.

**M36 complete (2026-09-25):** `tesserae.binding`, identical to `tre`'s on 166 expressions. The wiring moved to M37 (user's choice), because `tre`'s new API can't drive the legacy Checkbox/Switch state; bindings on `checked`/`selected`/`value` move to M40.

**M37 scoped in detail (2026-09-25):** six phases (tokens, compiler and cascade, tree parity, View/reconciler/bindings, components and screens, tests and docs) and four decisions, Q1–Q4, in `BUILD_TRACKER.md`.

**M37:** decisions Q1–Q4 as recommended. Phase 1 done: `tesserae.tokens` matches `tre` on 74 checks (roles, shapes, elevation shadows, type scale, colour strings); 698 passed.

Phase 2 done: the spec compiler (`spec/build.py`) and cascade (`spec/cascade.py`), checked against `tre`'s builder, with errors matching `tre`'s; 741 passed.

Phase 3 done: 127 views identical to `tre`'s node by node (`tests/test_tree_parity.py`); 870 passed.

Phase 4 done: `tesserae.View` with the reconciler and Tesserae's own binding, handler and `two_way:` wiring; `on_change` only for user edits; 900 passed.

Phase 5 done: components on Tesserae's builder, with the host's theme and stylesheet (M31's gap closed); `App` builds screens in its own window; `tesserae.View`/`Component` are Tesserae's; 913 passed.

Phase 6 done: `load_view`, `instantiate`, `ViewWatcher` and the suite off `tre`'s `View` (reference tests excepted); the recording bridge removed; atomic reconcile; theme key validation; 909 passed. **M37 complete.**

**M38 scoped (2026-09-25):** a `tesserae.Theme` (roles, `components:`, `typography:`, motion), theme typography in views, light/dark with the OS, docs; decisions Q1–Q4 in `BUILD_TRACKER.md`.

**M38 decisions (user):**
- Q1: theme typography for display text, not text inputs.
- Q2: `App(dark="system")` by default, plus `set_dark`.
- Q3: `"system"` starts dark.
- Q4: Emphasized as (0.2, 0, 0, 1).

Phase 1 done: `tesserae.Theme`, matching `tre`'s `Window.theme`; 1019 passed.

Phase 2 done: theme typography for Text and Link, not text inputs; 1029 passed.

Phase 3 done: `App(dark="system")` by default, following the OS; `set_dark`; 1042 passed.

Phase 4 done: final docs; a known gap for `"system"` starting dark. **M38 complete.**

**M39 scoped (2026-09-25):** from `tre`'s legacy behaviour write-up. It found a keyboard regression from M37 (`on_click` nodes aren't Tab stops), which Phase 1 fixes. Decisions Q1–Q3 pending.

**M39:** decisions Q1–Q3 as recommended. Phase 1 done: clickable nodes are keyboard-reachable buttons; 1048 passed. The dry-run gate report went to `tre`.

Phase 2 done: MD3's state layer and ripple on clickable Rect/Container nodes (`tesserae.interaction`, `interaction:`); 1068 passed.

Phase 3 done: the focus ring, YAML `a11y:`, `tesserae.a11y`; 1094 passed.

Phase 4 done: examples labelled, a keyboard-only test of the counter, the parity differ strips Tesserae-only fields for `tre`. **M39 complete**; 1095 passed.

**M40 scoped (2026-09-25):** 6 phases: a control foundation, then selection controls, slider and spin box, progress/loading/time dial, wiring (YAML kinds, bindings, fragments, factories), and tests and docs with the gate check. Found: YAML checkboxes, switches and radios never toggle and aren't Tab stops, as in `tre`. Decisions Q1–Q4 pending.

**M40:** Q1–Q4 as recommended. Phase 1 done: `tesserae.controls.Control` (with `Listeners` and `tokens.BASELINE`), proved on MD3's checkbox; 1114 passed.

Phase 2 done: RadioButton with RadioGroup, and Switch; 1127 passed.

Phase 3 done: Slider and SpinBox; 1142 passed.

Phase 4 done: progress (linear and circular, indeterminate too), the loading indicator, the time picker dial; 1157 passed.

Phase 5 done: the YAML control kinds and the stateful factories are Tesserae's controls; the todo_list checkbox ticks; 1179 passed.

Phase 6 done: the static gate, the examples clean under tre's removal shim, the controls guide. **M40 complete**; 1183 passed.

**M41 scoped (2026-09-25):** 6 phases. The composed factories are to be built from the fragments through the compiler, returning `Widget` objects, with MD3 feedback and selection, `tesserae.overlays` on `show_layer`, and a gate. The window-theme removal moves to M42's end. Decisions Q1–Q4 pending.

**M41:** Q1–Q4 as recommended. Phase 1 done: the `Widget` base (built from fragments) and `button`; content-sized text; an M37 patch bug fixed; 1198 passed.

Phase 2 done: icon buttons, FABs, extended FABs, the split button and the button group; 1205 passed.

**Up next:** M41 Phase 3 (containment and lists).
