# Component Fragments

A **fragment** is a reusable piece of a view: structure with `{{ parameters }}`, used by name. It is
a different thing from [Components & Embedding](components.md), which embeds a whole other view and
ViewModel pair with state of its own. A fragment has no ViewModel and no state: it expands, when the
file loads, into ordinary nodes. Tesserae ships [77 of them](../components/index.md), one for
each MD3 widget shape, and you can write your own.

## Using one

```yaml
# Some_View.yaml
id: root
kind: Container
style: {flex_direction: horizontal, gap: 8}
children:
  - id: save_button
    component: ButtonFilled
    with: {label: Save, width: 120, height: 40, corner_radius: 20}
```

- `component:` names the fragment: `ButtonFilled` is `ButtonFilled_Component.yaml`.
- `id:` is required. It namespaces every `id:` inside the fragment (`save_button.label`), so two calls
  never collide; the fragment's root takes the call's `id:`.
- `with:` supplies the fragment's parameters. A missing or unknown one is an error at load time.

### Wiring a call

A call also takes the keys that wire and name the fragment's root: `handlers:`, `bindings:`,
`two_way:`, `a11y:`, `interaction:`, `classes:` and `window_region:`.

```yaml
  - id: save
    component: ButtonFilled
    with: {label: Save, width: 120, height: 40, corner_radius: 20}
    handlers: {on_click: save}
    a11y: {label: Save the note}
```

- They go on the fragment's **root**, after it expands. A root that has its own keeps them: the call's
  are merged in key by key and win; `two_way:` replaces the root's and `classes:` adds to them.
- They belong to the view, not the fragment: a `{{ }}` in them is the ViewModel's binding, never one of
  the fragment's parameters.
- With `repeat:`, every item gets them.
- A clickable root is a button for the keyboard and assistive technology too, with the state layer and
  ripple (see [Interaction](interaction.md)).

## Where the look is

A fragment holds structure. Its look lives in a **stylesheet** of the same name, a list of rules
that name the fragment's parts by `id`:

```yaml
# ButtonFilled_Component.yaml: the structure
params: [label, width, height, corner_radius]
id: root
kind: Rect
children:
  - id: label
    kind: Text
    text: {content: "{{ label }}", typography_role: label_large}
```

```yaml
# ButtonFilled_Stylesheet.yaml: the look
styles:
  - id: root
    style: {width: "{{ width }}", height: "{{ height }}", background: primary, corner_radius: "{{ corner_radius }}"}
  - id: label
    style: {foreground: on_primary}
```

The parameters fill the stylesheet as they fill the fragment, and each rule goes under the style the
part already has, so a part's own `style:` in the fragment wins. Every built-in
[stylesheet](../stylesheets/index.md) has a page.

## Writing your own

Put a `<Name>_Component.yaml` in the same folder as the view that uses it, and use it as
`component: Name`. Add a `<Name>_Stylesheet.yaml` beside it for its look, or give its parts `style:`
directly; both work, and you can mix them.

```yaml
# Stat_Component.yaml
params: [label, {unit: ""}]
id: root
kind: Container
children:
  - id: value
    kind: Text
    text: {content: "0", typography_role: title_large}
    bindings: {text: "{{ value }}"}
  - id: label
    kind: Text
    text: {content: "{{ label }}", typography_role: label_medium}
```

- `params:` lists every name the fragment takes. A name is required; `{name: default}` is optional.
- A fragment of your own with a built-in name replaces the built-in one, and its stylesheet.
- A stylesheet of your own with a built-in component's name goes over the built-in one, field by field.
- A fragment can't use `include:` or a `style:` file; use a nested `component:`.
- Hot reload watches the fragment and its stylesheet.

### How a parameter is filled in

A string that is exactly one placeholder (`"{{ width }}"`) is replaced by the supplied value with its own
type, so `width: 120` stays a number. A placeholder inside a larger string (`"Item {{ n }}"`) is
interpolated as text. The same rule lets a live binding pass through a fragment untouched:

```yaml
with: {value: "{{ open_text.get() }}"}   # reaches the Text's `bindings:` as written
```

!!! warning "Don't name a parameter `on`, `off`, `yes` or `no`"
    YAML reads those bare words as booleans before Tesserae sees them. Name a boolean parameter
    `selected` or `enabled`.

### Optional parameters and conditionals

Two conditionals shape a fragment around the values it was given, once the parameters are filled in:

- **`when:` on a child** keeps the child only when the value is true.
- **`{if: c, then: a, else: b}` as a value** becomes `a` when `c` is true, else `b`; with no `else:` the
  key is left out.

```yaml
params: [label, {icon: null}]
id: root
kind: Container
children:
  - id: icon
    when: "{{ icon }}"
    kind: Icon
    icon: {name: "{{ icon }}"}
  - id: label
    kind: Text
    text: {content: "{{ label }}", typography_role: label_large}
```

```yaml
styles:
  - id: root
    style: {padding: {if: "{{ icon }}", then: {left: 16, right: 20}, else: {left: 20, right: 20}}}
```

False values are `null`, `false`, `0`, an empty string, list or mapping, and the strings `"false"`,
`"no"`, `"null"`, `"none"` and `"0"`, in any case. Everything else is true.

## Nesting

A fragment can use `component:` itself. The nested fragment's ids are namespaced by the outer call too.
A fragment that uses itself, directly or through others, is rejected, as is nesting more than 16 deep.

## Repeating: `repeat:`

`repeat:` expands one `component:` entry into several siblings from a list of per-item values:

```yaml
id: settings_list
component: ListItem
with: {width: 360}
repeat:
  - {headline: Notifications}
  - {headline: Privacy}
  - {headline: Storage}
```

Each entry is merged over the shared `with:`. The nodes are `settings_list.0`, `settings_list.1`, and so
on. A key in both `with:` and an entry is an error: a value that varies belongs in `repeat:`, a shared one
in `with:`. `repeat:` works only on a `component:` that is an entry of `children:`.

`repeat:` is fixed when the file loads. For a list that changes while the app runs, use a
[Repeater](repeater.md).

A fragment can forward a list parameter to `repeat:` (`repeat: "{{ items }}"`), so a container takes its
items as one list, and an item can carry a `selected: true` that its fragment turns into a look with
`{if:}`. That is how `Tabs`, `NavigationRail`, `NavigationDrawer`, `Menu` and `ButtonGroup` take theirs:

```yaml
- id: tabs
  component: Tabs
  with:
    item_width: 90
    items:
      - {label: Inbox}
      - {label: Sent, selected: true}
```

These are static: the selected item is whatever the file says. For selection that changes as the user
clicks, use the [widgets in Python](widget-catalog.md).
