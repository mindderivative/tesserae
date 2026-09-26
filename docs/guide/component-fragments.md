# Declarative Component Fragments

This is a different feature from [Components & Embedding](components.md).
That page covers `tesserae.instantiate` -- embedding a whole other
`*_View.yaml` + `*_ViewModel.py` pair as an independent, stateful
instance. This page covers **`component:` / `with:` / `repeat:`** -- a
pure, static, text-level macro expansion that runs *before* `tre` ever
sees a file. It has no `ViewModel` of its own; it exists so a
`*_View.yaml` (or a `*_Component.yaml` fragment) can reuse one of
Tesserae's 67 built-in MD3 widget shapes -- a filled button, a card, a
checkbox -- by name and parameters, instead of hand-writing the same
`kind: Rect` / `style:` / `children:` block every time.

## Why this exists

`tre` renders a real MD3 (Material Design 3) widget catalog
imperatively, through `Window.add_*` factory calls (`add_button`,
`add_card`, ...). Those factories resolve theme colors, shape tokens,
and internal per-state fields correctly, but they're Python function
calls -- not something a `*_View.yaml` file can reference directly.
Every fragment in `src/tesserae/spec/components/*.yaml` is a
declarative, `WidgetSpec`-shaped YAML template that reproduces one of
those factories' real output, checked directly against its imperative
counterpart. `component: ButtonFilled` in a view expands, at load time,
to the exact subtree that template describes.

## Basic usage

```yaml
# Some_View.yaml
id: root
kind: Container
style: {flex_direction: horizontal, gap: 8}
children:
  - id: save_button
    component: ButtonFilled
    with: {label: "Save", width: 120, height: 40}
```

- `component:` names a fragment -- `ButtonFilled` resolves to
  `spec/components/ButtonFilled_Component.yaml`.
- `id:` is required on every `component:` node. It's used to namespace
  every `id:` *inside* the fragment (`save_button.root`,
  `save_button.label`, ...), so two calls to the same fragment never
  collide -- the fragment's own root `id:` becomes the call site's
  `id:` directly, not a doubled-up `save_button.save_button`.
- `with:` supplies the fragment's declared `params:`. Every declared
  param must be supplied, and supplying an undeclared key is also a
  load-time error (`ComponentError`) -- both fail loudly rather than
  silently doing the wrong thing.

This expands to something equivalent to:

```yaml
id: root
kind: Container
style: {flex_direction: horizontal, gap: 8}
children:
  - id: save_button
    kind: Rect
    style: {width: 120, height: 40, background: primary, corner_radius: full}
    children:
      - id: save_button.label
        kind: Text
        text: {content: "Save", typography_role: label_large}
```

(The real fragment content is theme-role-driven, not a literal hex
color -- see any file under `src/tesserae/spec/components/` for the
genuine shape.)

## Authoring a fragment

A `*_Component.yaml` fragment is a plain `WidgetSpec` tree with one
extra top-level key:

```yaml
# spec/components/ButtonFilled_Component.yaml
params: [label, width, height]
id: root
kind: Rect
style:
  width: "{{ width }}"
  height: "{{ height }}"
  background: primary
  corner_radius: full
children:
  - id: label
    kind: Text
    text: {content: "{{ label }}", typography_role: label_large}
```

- `params:` declares every name the fragment accepts. It's popped off
  before the fragment is treated as a real node tree, so it never
  leaks into the expanded output.
- `{{ name }}` is substituted with the caller's supplied value.

### The whole-value substitution rule

A string that is *exactly* one placeholder (`"{{ width }}"`, optionally
with surrounding whitespace) is replaced with the supplied value's own
real Python type -- not stringified. This is load-bearing, not
cosmetic: PyYAML's dumper quotes a numeric-looking Python `str`, so a
naive string substitution would turn `width: "{{ width }}"` into
`width: '120'` -- a quoted string `tre`'s `serde_yaml_ng` parser
rejects for an `f32` field. Passing `width=120` (a real `int`) instead
round-trips as an unquoted YAML number.

The same rule is what lets a live `tre` binding expression pass through
a fragment untouched:

```yaml
with: {label: "{{ some_signal.get() }}"}
```

The supplied value here is itself the literal string
`"{{ some_signal.get() }}"` -- a whole-value substitution reproduces it
exactly, and `tre`'s own `binding.rs` resolves it later, at
`View._attach()` time, exactly as if it had been written directly into
a non-fragment node.

Only a placeholder embedded in a larger string (`"Item {{ n }}"`) falls
back to plain string interpolation, where stringifying is correct.

### A real gotcha: don't name a param `on`/`off`

PyYAML's default loader treats a bare, unquoted `on`/`off` as a YAML
1.1 boolean literal. A fragment (or `params:` list) with a key
literally named `on` gets silently coerced to `True` before
`_substitute` ever runs, and `{{ on }}` is left as unresolved literal
text in the output for `tre` to reject. That's why `Switch_Component.yaml`
names its parameter `selected` rather than `on` -- prefer a name that
isn't a YAML 1.1 boolean keyword (`on`/`off`/`yes`/`no`/`true`/`false`)
for any boolean-ish param.

## Nesting

A fragment can itself use `component:` -- the nested fragment's own
`id:`s get namespaced by the *outer* call site's `id:` too, exactly
once, not twice. Cycles (a fragment that references itself, directly
or transitively) are rejected, and nesting past `MAX_DEPTH` (16 --
generous headroom for real composition, not a limit any legitimate
tree should approach) is also rejected.

## Repeating a fragment: `repeat:`

`repeat:` expands one `component:` entry to N sibling nodes from a
static, literal list of per-item overrides -- for a list of rows built
from data you already have at load time, without hand-duplicating N
near-identical `component:` blocks:

```yaml
id: settings_list
component: ListItem
with: {width: 360}
repeat:
  - {headline: "Notifications"}
  - {headline: "Privacy"}
  - {headline: "Storage"}
```

Each `repeat:` entry is merged on top of the shared `with:` values.
Each iteration gets its own `id:`, auto-suffixed `.0`/`.1`/`.2`/...
(`settings_list.0`, `settings_list.1`, `settings_list.2`), so every
generated node still has a unique, predictable id.

A key given in **both** `with:` and a `repeat:` entry is a load-time
error, not a "last one wins" resolution -- a value that varies per item
belongs in `repeat:`; a value shared by every item belongs in `with:`.
Missing/unknown parameters are still checked per iteration, exactly as
for a non-repeated call.

`repeat:` is only valid on a `component:` node that's an entry inside a
`children:` list -- there's nowhere for a 2nd or 3rd instance to go if
the `component:` node is a document's single root.

### `repeat:` is not reactive

Everything `repeat:`'s own list expands to is fixed at macro-expansion
time, before `tre` ever sees the file -- the same "before `tre` ever
sees the file" framing this whole module is built on. An app that
needs runtime-changing content (items added/removed, live reordering
driven by a `Signal`) still uses the existing imperative
[`Repeater`](repeater.md), not `repeat:`. `repeat:`'s own value *can*
itself use `{{ param }}` substitution, though -- an outer component's
own list-typed parameter can be forwarded straight into an inner
`repeat:`, since the existing substitution pass runs before expansion
ever descends into a nested `component:` node.

### Known, deliberate scope limit

`repeat:` gives full fidelity for `ListItem` (and any other fragment
that's pure layout composition). It does **not** yet give full
fidelity for the widgets whose real imperative construction computes
state-dependent active/inactive coloring internally in Rust --
`tabs`/`button_group`/`navigation_rail`/`navigation_drawer`/`menu`.
Repeating a fragment call for these produces a static snapshot, not the
real per-item selected/unselected styling; that needs a second,
separate, not-yet-designed capability (conditional per-item styling),
tracked in [`BUILD_TRACKER.md`](https://github.com/mindderivative/tesserae/blob/main/BUILD_TRACKER.md)'s
known-gaps list.

## The built-in fragment catalog

67 of ~68 real MD3 widgets have a `*_Component.yaml` fragment today,
covering every MD3 category:

| Category | Fragments |
| --- | --- |
| Buttons & Actions | `ButtonElevated`/`ButtonFilled`/`ButtonFilledTonal`/`ButtonOutlined`/`ButtonText`, `IconButtonStandard`/`IconButtonFilled`/`IconButtonFilledTonal`/`IconButtonOutlined`, `Fab{Primary,Secondary,Tertiary,Surface}`, `ExtendedFab{Primary,Secondary,Tertiary,Surface}`, `SplitButton{Elevated,Filled,FilledTonal,Outlined,Text}` |
| Selection & Input | `Checkbox`, `RadioButton`, `Switch`, `Slider`, `SpinBox` |
| Cards/Lists/Chips/Structural | `CardElevated`/`CardFilled`/`CardOutlined`, `ListItem`, `Chip{Assist,Filter,FilterSelected,Input,Suggestion}`, `Badge{Dot,Labeled}`, `Divider`, `Link`, `AccordionHeader`, `TreeNode{Branch,Leaf}` |
| Navigation & Shell | `Toolbar{Docked,Floating}`, `TopAppBar`, `StatusBar` (fixed-shape members; see `BUILD_TRACKER.md` M22) |
| Overlays | `Dialog`, `Snackbar`, `Tooltip`, `MenuItem`, `SideSheet{Modal,Standard}` |
| Search | `SearchBar`, `SearchView` |
| Progress & Status | `CircularProgress`, `LinearProgress`, `LoadingIndicator` |
| Media & Graphics | `Image`, `NodeGraph` |
| Date & Time | `DatePickerDay`/`DatePickerDaySelected`/`DatePickerDayToday`/`DatePickerDayOutsideMonth`, `PeriodSelector{AM,PM}`, `TimePickerDial` |

The Selection & Input, Progress & Status and `TimePickerDial` fragments
expand to the eight **control kinds** (`Checkbox`, `RadioButton`,
`Switch`, `Slider`, `CircularProgress`, `LinearProgress`,
`LoadingIndicator`, `TimePickerDial`). Since M40 these are Tesserae's MD3
controls, which respond to the pointer and keyboard themselves: a
checkbox ticks, a slider drags. Their state takes bindings and
`two_way:` (`checked`, `selected`, `value`, `hour`, `minute`), as does
`disabled`, and `on_change` runs for the user's changes. Radio buttons
with the same `group:` name exclude each other and are one Tab stop:

```yaml
- {id: small, kind: RadioButton, selected: true, group: size, style: {}}
- {id: large, kind: RadioButton, selected: false, group: size, style: {}}
```

`view.control("small")` returns a control, whose `Signal`s are its state
(see [Controls](controls.md)).
The `SpinBox` fragment is still a composition, with no behaviour of its
own; `tesserae.widgets.spin_box` gives a working one.

Since M41 a `Text` or `Link` with no `width` or `height` is sized to its
content (`tre` 0.3.4's text has no size of its own, so before M41 such a
label was 0 px wide and didn't show). The button fragments centre their
label, the chips pad theirs, and a list item's headline is MD3's
`body_large`. A `Link` is a box holding its text since M41: `tre`'s
`text` never gets pointer events, so before, only the keyboard could
follow a link. `view.node(id)` for a Link is the box.

For each fragment's exact `params:` and structure, read the file
directly under `src/tesserae/spec/components/` -- every one is short
(typically under 25 lines) and carries its own comment explaining which
real `tre` factory it matches and any real MD3 token it hardcodes.

### What has no fragment yet, and why

- **`video`** -- a fragment can declare the same synthetic blank
  placeholder `add_video` builds (an `Image` with no `src:`), but real
  video content still needs the app to fetch the resulting `Node` and
  call `push_frame` imperatively afterward -- no way for a one-shot
  static expansion to wire that up on its own.
- **`graph_node`** -- structurally unfragmentable: it needs a live node
  reference as its own attachment parent, which textual expansion can't
  express.
- **`extended_fab`'s icon-less structural shape** -- deliberately
  deferred (see `BUILD_TRACKER.md` M18).

## Loading a view that uses `component:`

Nothing extra is required at the call site -- `App.load()` (and
`tesserae.instantiate`) already expand `component:` usage
automatically, via `tesserae.spec.load_view` /
`expand_components_to_spec` under the hood, and hand `tre` the finished
dict -- `tre` never reads the view file itself. See
[`load_view`](../api/spec.md) if you need to expand a fragment-using
file manually (e.g. for a tool, or outside `App`), and for the
[`include:`](../api/spec.md#include) rules, which Tesserae also
resolves.

A view with zero `component:` usage expands to itself unchanged, so
this is a safe, no-op-preserving layer under every existing view --
not an opt-in switch.
