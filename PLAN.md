# PLAN — M15: Part 3, Phase 1 — Component Macro-Expansion Engine

*(Replaces the prior M14 plan in this file — M14 is complete, committed.
Part 2 of the approved plan, the full widget catalog, is done. This
starts Part 3: the real "ease of use to a GUI designer" deliverable.)*

## Goal

Let a `*_View.yaml` author write `component: Button` / `with: {label:
..., variant: ...}` directly, with no knowledge that `Button` is a
Rect+Text composition underneath. Modeled on pyCopper's real
`source:`/`with:`/`params:` precedent (confirmed by direct reading of
`pyCopper/src/pycopper/spec/include.py`), adapted to `tre`'s own real
`WidgetSpec` schema.

## Real findings that reshape the design (checked directly, not assumed)

1. **`tre` already has a real, working `include:` splice mechanism**
   (`crates/engine-spec/src/include.rs`, confirmed by direct read) —
   `{include: path.yaml}` as a sole key, spliced onto the raw
   `serde_yaml_ng::Value` tree *before* `WidgetSpec` validation, with
   real path confinement (`canonicalize` + `starts_with`), cycle
   detection, and an 8-deep limit. **It has no parameterization at
   all** — a pure, dumb splice. Tesserae's macro layer does not need
   to reimplement path confinement/cycle detection/splicing for plain
   reuse — `include:` already does that, and stays untouched, passed
   through as-is by the macro-expansion pass (Tesserae never touches a
   literal `include:` key). The real, missing capability is
   *parameterized* expansion (`component:`/`with:`/`params:`), which
   `include:` was never meant to provide.
2. **`tre`'s declarative layer resolves MD3 color roles and shape/
   elevation tokens for real**, confirmed with a live `tre.View(path=,
   source=, theme_seed=(0x67,0x50,0xA4,0xFF))` call: `style:
   {background: primary, corner_radius: small}` resolves correctly
   with no Python-side color computation needed. Component fragments
   can use MD3 token names directly, the same vocabulary
   `docs/guide/declarative-views.md` already documents.
3. **Real, honest gap, confirmed by grepping `build.rs`/`cascade.rs`
   for `components`**: the declarative cascade never consults
   `ThemeSpec.components` (the per-component `{corner_radius: ...}`-
   style override a *theme file* can carry) — only the imperative
   catalog's `window.theme.shape("button", variant)` does. A
   declarative `component: Button` gets real MD3 color-role/shape-
   token styling, but not an app's own custom per-component override.
   Named directly here rather than silently dropped; an app wanting
   that level of customization uses the imperative `tesserae.widgets`
   catalog instead.
4. **`WidgetSpec`'s real schema** (confirmed by direct read of
   `crates/engine-spec/src/spec.rs`): `id`, `kind`, `classes`, `style`,
   `text`, `checked`, `value`, `image`, `bindings`, `handlers`,
   `two_way`, `children` — `#[serde(deny_unknown_fields)]`, so
   `component:`/`with:`/`params:` must be fully gone from a node
   before `tre` ever deserializes it. No `anchor:`-style cross-
   reference field exists (unlike pyCopper's own schema) — only `id:`
   needs namespacing when a fragment is used more than once, nothing
   else.
5. **`View`'s real constructor**, confirmed via `#[pyo3(signature =
   ...)]`: `View(path, stylesheet=None, theme_seed=None, dark=False,
   default_theme=None, custom_theme=None, source=None)` — `source=`
   (`tre`'s own M71) is the real hand-off point: Tesserae expands
   `path`'s raw text into pure `WidgetSpec`-shaped YAML and passes it
   as `source=`, with `path` still supplying the real file `poll_
   reload()` watches.

## Design

### Component fragment format (`*_Component.yaml`)

A plain `WidgetSpec`-shaped YAML document with one extra, Tesserae-only
key popped before hand-off:

```yaml
# src/tesserae/spec/components/Button_Component.yaml
params: [label, width, height, variant]
id: root
kind: Rect
style: {background: primary, corner_radius: small}
children:
  - id: label
    kind: Text
    text: {content: "{{ label }}"}
    style: {background: on_primary}
```

### Call site (`*_View.yaml`)

```yaml
children:
  - id: save_button
    component: Button
    with: {label: "Save", width: 120, height: 40, variant: filled}
```

### `src/tesserae/spec/expand.py` (new)

Mirrors `pyCopper/spec/include.py`'s own real, proven shape --
`yaml.safe_load` first (never raw-text substitution, which would be
fragile against YAML syntax), walk the untyped dict, substitute, walk
again for nested `component:` usage, then `yaml.safe_dump` back to text
for `tre.View(source=...)`:

1. `_PARAM_RE = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")`
   -- identical to pyCopper's own, textual substitution so a real
   `with: {label: "{{ some_signal.get() }}"}` leaves a live `tre`
   binding expression behind untouched (the same "compose with
   bindings, no separate reactive path" property pyCopper's own
   docstring names).
2. `_expand_node(node, ...)`: pops `params:`, validates `with:`
   against it (missing/unknown both real errors, mirroring pyCopper's
   own `_expand` exactly), substitutes, recurses into the fragment's
   own `children:` for nested component use, then renames every
   `id:` found inside: the fragment's own root `id:` becomes the call
   site's `id:` directly; every other `id:` gets prefixed
   `"{call_site_id}.{original_id}"` (matching pyCopper's own
   `_namespace_names`, adapted from `name:` to `id:`).
3. `_walk(node, ...)`: recurses only into `children:` (the one real
   tree-shaped key in `WidgetSpec` -- simpler than pyCopper's own
   `_TREE_KEYS` tuple, which needs 4 keys for its richer schema).
   A mapping with a `component:` key is expanded; anything else is
   walked structurally, untouched otherwise. A literal `include:` key
   is left completely alone -- resolved later by `tre`'s own real
   mechanism, not touched by this pass at all.
4. Real guards, mirroring pyCopper's own: a `component:` name not
   found in the component directory is a clear `ComponentError`
   naming it; a cycle (`Button` fragment using `component: Button`)
   is a clear `ComponentError` with the call chain; depth capped at 16
   (`tre`'s own `include:` uses 8 for a simpler, unparameterized case;
   16 gives real component nesting -- e.g. `card` composing `button` --
   headroom without being unbounded).
5. `expand_components(yaml_text: str, *, component_dirs: list[Path]) ->
   str` -- the one public entry point. Component fragments are looked
   up by name across `component_dirs` (Tesserae's own built-in
   `spec/components/` directory first, with room for an app's own
   directory to add/override later -- not built this milestone, a
   real, named future extension point, not silently precluded).

### Real, additional finding while scoping the integration point:
`Component.instantiate` (the embedded-component path `tesserae.
instantiate()` uses) has no `source=` override at all -- confirmed
directly: `View.instantiate(path, into)` delegates to `crate::
component::instantiate_component(..., path)`, which does `std::fs::
read_to_string(path)` directly (`crates/engine-py/src/component.rs:
119`). So `component:` expansion can reach a top-level screen (`App.
load()` constructs a `View` directly, Tesserae controls that call) but
**not** an embedded component today -- that needs a small `tre`-side
widening of `View.instantiate` with a `source=` param, mirroring M71's
own `View.__new__`/`poll_reload` precedent exactly. Named here as a
real, deferred gap, not silently promised as already working.

### Integration point (`src/tesserae/spec/load.py`, new)

Rather than subclassing `tre.View` (a real pyo3 native class -- adds
real complexity for uncertain benefit) or replacing the top-level
`tesserae.View` re-export in this same milestone, M15 ships one plain
function: `load_view(path, *, component_dirs=None, **view_kwargs) ->
tre.View` -- reads `path`, expands `component:` usage, constructs and
returns a genuine `tre.View(path=path, source=expanded, **view_
kwargs)`. Wiring `App.load()` to use this by default, and a matching
`poll_reload` helper that re-expands on every real reload, are real,
named follow-ups once this core path is proven -- not done silently in
this same pass alongside the engine itself.

## Scope for this milestone (M15)

The engine (`expand.py`) + the integration function (`load.py`) + one
real fragment (`Button_Component.yaml`), proven end-to-end: a real
pytest constructing a view that uses `component: Button` via `load_
view(...)` and asserting the resulting live tree matches what
`tesserae.widgets.button(...)` would produce directly (the same
cross-check strategy the M8-M14 widget tests already use), plus real
coverage of every guard (missing/unknown param, cycle, unknown
component name, id-namespacing across two uses of the same component
in one view, a `{{ }}` binding forwarded as a param value surviving
untouched).

**Deliberately not in this milestone (named, not silently dropped):**
- The other 37 fragments -- a separate, mostly-mechanical follow-up
  once the engine itself is proven real.
- Wiring `App.load()`/`tesserae.instantiate()` to use `load_view`
  automatically.
- Embedded-component `component:` support -- blocked on the `tre`-side
  `View.instantiate(source=...)` widening named above.
- A `poll_reload`-integrated re-expansion helper.
- The declarative-vs-imperative `components:` theme-override gap named
  above (not a bug to fix here -- a real, stated scope boundary).

## Status

**Complete.** `src/tesserae/spec/expand.py` -- `expand_components`/
`ComponentError`, mirroring pyCopper's real `include.py` shape,
verified with a real, load-bearing fix found while testing (not
assumed): PyYAML's `safe_dump` quotes a numeric-looking Python `str`,
which would have turned every numeric param into a quoted string
`tre`'s own `f32`/`f64` fields reject -- fixed by preserving the
supplied value's real type on a whole-value (not embedded) placeholder
match. `src/tesserae/spec/load.py` -- `load_view`, the real integration
point, proven against an actual file on disk. `src/tesserae/spec/
components/Button_Component.yaml` -- one real, faithful "filled"-
variant fragment (container=primary, label=on_primary, matching
`resolve_button_colors` exactly), with its own real, stated limitation
(`corner_radius` is a required param, not derived from `height`, since
`{{ }}` substitution has no arithmetic and no MD3 "full/pill" shape
token exists to reach for instead).

16 new pytest tests (`test_spec_expand.py` 13, `test_spec_load.py` 3):
every guard named in the design (missing/unknown param, missing
call-site `id:`, unknown component, a real cycle using a temp fixture
directory, id-namespacing across two uses of one component, a `{{ }}`
binding forwarded as a param value surviving untouched, numeric-type
round-tripping), plus the real cross-check that matters most --
constructing the same button both ways (`component: Button` through
`load_view`/`View(source=...)`, and `tesserae.widgets.button(...)`
directly) and asserting identical `corner_radius`. Full suite: 97
passed (81 prior + 16 new), 0 regressions. `pyproject.toml` gained a
real `pyyaml>=6.0` dependency (previously only present transitively via
mkdocs, not declared).

Next: `BUILD_TRACKER.md`/tracker artifact/commit, then the real,
named follow-ups this milestone deliberately deferred (see above) --
starting with the remaining 37 component fragments, a separate,
mostly-mechanical milestone.
