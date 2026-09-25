# LOG — M27 + M28: Primitive Fragments (7) + Macro-Layer `repeat:` Construct

- User directed both fronts M26 scoped be built in one pass: "Start
  with M27 and then move onto M28."

## What shipped

### M27 — 7 new primitive fragments

1. `tre`'s own side landed first, as `tre`'s own M84
   (`engine-spec::NodeKindSpec` + `build.rs`) — verified against M26's
   own scoping before writing anything, confirmed accurate on every
   field/role/constructor name it named. One real gap M26 missed,
   found and closed there: `Md3Baseline`'s fallback colors live in
   `engine-py`, a crate `engine-spec` can't depend on — resolved with
   a small local copy of just the 4 values needed, not a bigger
   shared-constants refactor. `LoadingIndicator`'s real required
   `paint.shape`-seeding step (avoiding a confirmed first-tick flash
   bug) carried over correctly.
2. All 7 `*_Component.yaml` fragments authored here
   (`RadioButton`/`Switch`/`CircularProgress`/`LinearProgress`/
   `LoadingIndicator`/`TimePickerDial`/`Link`), each checked directly
   against its own real imperative-catalog counterpart.
3. Real bug caught here, not on the `tre` side: `Switch`'s first
   fragment draft named its toggle param `on` — PyYAML's default
   loader treats a bare, unquoted `on`/`off` as a YAML 1.1 boolean
   literal (confirmed directly: `yaml.safe_load('on: false')` →
   `{True: False}`), silently breaking `{{ on }}` substitution;
   renamed to `is_on`.
4. Real, small `tre`-side fix found and shipped alongside `tre`'s own
   M84, while writing this milestone's own `Link` test:
   `Node.get_text()` had no match arm for `Link` at all — added the
   same one-line arm `Text` already has.
5. 12 new pytest tests across 4 files, each comparing a fragment's
   real observable state directly against its own imperative-catalog
   counterpart.

### M28 — macro-layer `repeat:` construct

1. Real finding before designing anything: checked `add_list`'s own
   real imperative body first (M26 named it the loop construct's
   "cleanest fit" target). Found it takes pre-built `Node`s and does
   pure layout composition — no `NodeKind::List` primitive exists at
   all — so "a list" was already fully expressible today as a plain
   `Container` with N literal `component: ListItem` children. The
   real, missing capability is narrower: repeating one fragment call
   N times from static, known-at-authoring-time data, without
   hand-duplicating N near-identical `component:` blocks.
2. New, optional `repeat:` key on any `component:` node — a literal
   list of per-item mappings, each merged onto the node's shared
   `with:` values. A key given in *both* is a real, rejected
   `ComponentError` (ambiguous which should win, so neither does).
   Each iteration's own id auto-suffixed `.0`/`.1`/`.2`/..., collision
   -free by construction.
3. Deliberately, explicitly out of scope, matching M26's own staging
   recommendation: the 5 Rust-internal-state-dependent-coloring
   widgets (`tabs`/`button_group`/`navigation_rail`/
   `navigation_drawer`/`menu`) are not addressed — their real
   active/inactive coloring is computed inside Rust from a selected
   index, which a static `{{ }}`-substitution template can't branch
   on. `repeat:` alone gives only a static, always-identically-styled
   snapshot for these 5.
4. Real, load-bearing architectural point, confirmed with its own
   test, not assumed: `repeat:`'s own value already supports
   `{{ param }}` substitution with zero extra code, since the existing
   general-purpose `_substitute` pass runs over the entire fragment
   template — including a nested `repeat:` key's own placeholder value
   — before `_walk` ever recurses into that nested `component:` node.
5. 10 new pytest tests (`test_spec_expand.py`) — expansion to N nodes
   with correct namespaced ids, zero-item repeats, every real guard
   (must be a list, each entry a mapping, a `with:`/`repeat:` key
   collision, per-iteration missing-parameter validation, `repeat:`
   rejected outside a `children:` list), and the nested-substitution
   composition case.

### Docs catch-up (separate follow-up, same day)

A real gap found afterward: the whole macro-expansion layer and
imperative widget catalog had zero MkDocs coverage. Added
`guide/component-fragments.md`, `guide/widget-catalog.md`,
`api/spec.md`; updated `api/index.md`/`index.md`/`architecture.md` to
reference the new layers; `mkdocs.yml` nav wired; verified with
`mkdocs build --strict` (clean, no warnings, anchors resolve).

## Status

**M27 and M28 are complete. 67 fragments total, up from 60.**
Committed locally (`052c2af`, `9512d3f`); docs catch-up committed
separately. Push deferred pending explicit user confirmation.

`pytest tests/` — 157 passed (up from 135 at the top of M27: +12 for
M27, +10 for M28). All 3 real examples (`counter`/`multi_screen`/
`todo_list`) ran clean end to end.

Nothing currently scoped next. The 5 Rust-internal-state-dependent
-coloring widgets remain a real, named, un-scoped future candidate for
whenever conditional per-item styling gets designed.
