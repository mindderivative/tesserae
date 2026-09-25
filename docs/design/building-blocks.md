# Design: Tesserae on `tre`'s Building Blocks

*Status: design for M34 (2026-09-25), decisions P1–P8 settled. It will
change as each milestone is scoped against the source.*

## Why

`tre` is becoming an engine of building blocks: a node tree, flex layout,
paint, text, animation, input, accessibility, layers and the event loop
(`tre`'s M93–M96, released in 0.3.4). Everything a framework can build
from those moves out of `tre` and into Tesserae:

- the declarative layer: views, the style cascade, reconciling,
  components and `{{ }}` bindings;
- reactivity: `Signal`, `Computed`, `Effect`, `ViewModel`, `batch`,
  `untrack`;
- the MD3 widget catalog and MD3 theming.

`tre` 0.3.5 deletes the old API (its M98–M99), but only once Tesserae
no longer calls any of it (`tre`'s M97 gate). This page is the plan for
getting there without app authors noticing.

## What app authors see

Nothing changes for them (P1, P6):

- `*_View.yaml` files keep today's schema: `kind: Rect`/`Container`/
  `Text`/`Icon`/`Image`/`TextField`, `style: {background, foreground,
  ...}`, `bindings:`, `handlers:`, `two_way:`, `component:`/`with:`/
  `repeat:`, `include:`.
- `*_ViewModel.py` files keep `Signal`, `Computed`, `Effect`, `batch`,
  `untrack` and `ViewModel`, now imported from Tesserae's own code.
- `App`, `instantiate`, `Repeater`, `load_view`, the theme and stylesheet
  arguments, and hot reload keep their signatures.
- **One break, written down:** a stateful `tesserae.widgets` factory
  (checkbox, radio, switch, slider, …) returns a small Tesserae widget
  object, which holds `.node` (the `tre` node) and its state. Today it
  returns a bare `tre.Node`. Once `tre` stops holding a checkbox's
  `checked`, something in Tesserae has to.

## Layers

```
 app code:  *_View.yaml   *_ViewModel.py   App / widgets
               │                │              │
 Tesserae:  expand (component:/include:, today) ─┐
            spec compiler ── cascade ── theme ───┤
            reconciler                           │
            bindings ── reactivity               │
            widgets (controls, composed, overlays)
               │
 tre 0.3.4: window.create / set / get / animate / on / show_layer
            add_child / insert_child / remove / destroy
```

### Reactivity (M35)

`tre`'s reactivity is already pure Python (`python/tre/__init__.py`,
~400 lines). The only native parts are three small functions: a
dependency-recording stack (`_record_read`, `_begin_recording`,
`_end_recording`). Tesserae takes the module over and keeps a recording
stack of its own. Semantics stay exactly `tre`'s (P3):

- a same-value `set` doesn't notify;
- `Computed` recomputes when a dependency changes, and notifies only if
  its value changed;
- `batch` defers notification and runs each subscriber once;
- `untrack` hides reads from the enclosing scope;
- writing to a `Signal` while it's still notifying raises a clear error.

One test suite runs against both implementations while `tre` 0.3.4 still
has its own.

### Bindings and handlers (M36)

A port of `tre`'s safe `{{ }}` grammar (`engine-spec/src/binding.rs`, P4).
It supports attribute access, indexing, comparison, arithmetic, boolean
logic and zero-argument method calls, and never uses `eval`. Evaluating
a binding inside a recording scope finds its dependencies. A change
re-evaluates it and `set`s the node property. **A value that didn't
change isn't set again**, so `on_change` doesn't fire on a reload
(`tre` issue #12 disappears on Tesserae's side). Handlers are
`node.on(event, ...)` calls, and `two_way:` is a handler that writes the
`Signal`.

The evaluator shipped in M36; the wiring lands with M37's builder. It
can't come sooner: on nodes a `tre` `View` builds, 0.3.4's new API sets
text, paint and layout, but `set(checked=...)` on a legacy Checkbox
only sets its accessibility flag, and nothing but the legacy
`set_checked` reaches its state. Bindings on `checked`/`selected`/`value`
therefore arrive with Tesserae's own controls (M40).

### Spec compiler and cascade (M37)

The compiler takes an expanded spec dict (from Tesserae's existing
`expand` stage) and builds nodes:

| Tesserae YAML | `tre` 0.3.4 |
|---|---|
| `kind: Rect`, `kind: Container` | `create("box")` (`tre` D3) |
| `kind: Text` | `create("text")` |
| `kind: Icon` | `create("path")`, data from Tesserae's icon set (D4) |
| `kind: TextField` | `create("text_input")` |
| `kind: Image` | `create("image")` with decoded `rgba` |
| `background` on a box, `foreground` on text or an icon | `fill` |
| `border_color`/`border_width` | `stroke_color`/`stroke_width` |
| a theme role (`primary`), shape token (`extra_large`), elevation (`level_3`), `typography_role` | resolved by the theme (M38) to tuples, numbers and `shadows` |
| a hex or CSS color string | parsed by Tesserae to an `(r, g, b, a)` tuple |

The cascade is `tre`'s rule, reproduced: default theme, then custom
theme, then stylesheet, then inline `style:`. Within a sheet, a baseline
rule loses to a `kind:` rule, which loses to `classes:` (more classes
win), which loses to `id:`. It's resolved when a view is built or
reconciled, never per frame.

### Reconciler, components, screens (M37)

- **Reconciler:** a keyed diff by widget `id`. Unchanged nodes keep
  their identity, focus and running animations. Changed properties are
  `set`, moved children use `insert_child`, and removed ones are
  `destroy`ed. Hot reload (`ViewWatcher`) calls it instead of
  `View.reconcile`.
- **Components:** `instantiate` builds a component with the host's theme
  and stylesheet. That closes M31's gap, where an embedded component got
  neither.
- **Screens:** `App.show` attaches a screen's root to `window.root` and
  detaches the previous one with `remove()`, which keeps it alive with
  its state (`tre` R5). This replaces `Window.from_view`/`show_view`.

### Tokens (M37 Phase 1)

`tesserae.tokens` holds the MD3 values the builder resolves, checked
against `tre` 0.3.4 by `tests/test_tokens.py`:

- **colour roles**, all 49 from a seed, light and dark, with `colors:`
  overrides and `tre`'s seed precedence;
- the **shape** scale and **elevation** levels;
- **elevation as `shadows`**, `tre`'s key and ambient pair. 0.3.4 nodes
  have no `elevation`, and level 1 is exactly the pair `tre`'s docs give;
- the 15 **type** roles;
- **colour strings**: hex, CSS names, `transparent`, and CSS Color 4
  `rgb()`/`hsl()` with alpha.

`tre` also accepts CSS's wide-gamut functions (`color()`, `oklch()`, …),
and Tesserae doesn't yet: it raises a clear error instead.

### Theme (M38)

`tre` keeps no theme (D7), so Tesserae owns all of it:

- colour schemes from a seed, light and dark, with `colors:` overrides.
  The colour science comes from `materialyoucolor` (P2), a pure-Python,
  MIT-licensed port of Google's `material-color-utilities`. M34's spike
  showed it reproduces `tre`'s schemes exactly (784 of 784 role values,
  8 seeds, light and dark) with two settings: `spec_version="2021"`, and
  tone 10 for the four light-mode `on_*_container` roles, where current
  `material-color-utilities` uses tone 30;
- the shape, elevation (MD3's key and ambient shadows), typography and
  motion tokens;
- theme files as today.

A theme change re-resolves the cascade and `set`s the changed values.
M34's measurement puts that well within budget: re-`set`ting `fill` on
4,000 nodes took 0.8 ms. The OS light/dark switch arrives as the
window's `color_scheme` event.

### Interaction and widgets (M39–M42)

`tre` draws no ripple, state layer, scrim or focus ring (D8, R12).
Tesserae builds them:

- **Ripple:** a clipped box holding a circle `path`, animated by `scale`
  and `opacity`.
- **State layers:** from the `pointer_enter`/`pointer_leave` subtree
  events.
- **Focus rings:** from bubbling `focus`/`unfocus`.
- **Accessibility:** each widget sets its own `role`, state and
  `a11y_action`s.

Every MD3 widget is then built from these and the primitives, following
`tre`'s own table ("Rebuilding the MD3 widgets from building blocks" in
`tre`'s `docs/design/target-api.md`). The whole catalog is rebuilt,
staged by category: stateful controls, then composed widgets and
overlays on `show_layer`, then inputs, date and time, media, the node
graph and docking (P7).

## Rules

- **Build only on `tre` 0.3.4's new API** (P8): `create`, `set`/`get`/
  `animate`, `on`, `show_layer`, `insert_child`/`remove`/`destroy`,
  `fill`/`stroke_color`. Never a name `tre` M98–M99 deletes, so the
  move to 0.3.5 is deletions, not a second migration.
- **Incremental** (P5): one subsystem at a time, suite green after each
  step. Old and new coexist on 0.3.4 until M43.
- **Proved against `tre`, not assumed:** while `tre` 0.3.4 still has
  its own reactivity, binding evaluator, cascade and themes, each
  Tesserae replacement is tested for identical results against it.
- **The gate check** (M43, `tre` M97 Phase 2 Step 2): Tesserae's full
  suite and examples pass with every removed `tre` name stubbed to raise.

## Measured so far

On `tre` 0.3.4, this machine, 2,000 boxes each holding a text node:

| | Tesserae via `create`/`set` | `tre`'s `View` |
|---|---|---|
| build | 9.5 ms | 10.9 ms |
| re-colour every node | 0.8 ms | 2.3 ms (`set_theme`) |

With Tesserae's own cascade, role colours and bindings prototyped in
Python (`tools/spikes/cascade_cost.py`), on 2,000 boxes and 2,000 texts
with a 4-rule stylesheet and 500 texts bound to one `Signal`:

| | Tesserae prototype | `tre`'s `View` |
|---|---|---|
| build, including cascade and bindings | 20.7 ms | 11.0 ms |
| theme switch | 2.8 ms | 3.1 ms |
| one `Signal.set` reaching 500 nodes | 0.7 ms | 0.5 ms |

Half the prototype's build is its naive cascade, which scans every rule
for every node; the real one (M37) indexes rules by kind, class and id.

A full MD3 checkbox built from the building blocks alone
(`tools/spikes/checkbox_on_primitives.py`, ~70 lines) passes 12
headless checks: state layers, ripple, keyboard-only focus ring, the
check mark drawn in with `trim_end`, accessibility role, label and state,
and Space/Enter activation.
