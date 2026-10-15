# Toolbars

*Navigation*

## In Material Design 3

A toolbar groups the actions for the content around it. A **docked** one is fixed to an edge; a **floating**
one is a rounded bar over the content.

## In Tesserae

`widget: Toolbar` is a view Tesserae ships (`Toolbar_View.yaml`): one widget for the docked and the floating toolbar, built from `IconButton`s, an optional `Fab` and a `Menu`.

A `docked` toolbar spans its width (or `width`), 64 tall, on `surface_container`; a `floating` one is a pill with a shadow as long as its buttons, and with `orientation: vertical` a
column 64 wide. `vibrant: true` puts it on `primary_container`, with `on_primary_container` icons. The `items` are icon buttons, each `{value, icon, label}` and optionally `disabled`;
the `value` of the item or overflow row pressed goes to `chosen`. `overflow` is `Menu` rows under a more button at the end. `fab_icon` (with `fab_label` and `on_fab`) adds a small
action button at the end. With `fit`, items that do not fit move, in order, into the overflow menu; a docked toolbar measures itself, a floating one uses `max_length` pixels.
`hidden` fades it out and takes its buttons out of the tab order (bind it to the way a list scrolls). `label` is its accessible name, and `disabled` stops every button.

Your own content goes in the default slot after the items. The arrow keys move between the buttons (one Tab stop). The role is `group`: the engine has no toolbar role.
With `fit`, the items that spill and the rows of `overflow` share one menu, a divider between. Not built: sliding out of the way (it fades).

## How it is built

A view Tesserae ships is a `<Name>_View.yaml` (what it takes and what it is made of) with a `<Name>_Stylesheet.yaml` (how it looks). Use it by name: `widget: Toolbar`. A file of the same name in your project replaces it.

### `Toolbar`

The Material 3 toolbar: a row (or, floating, a column) of icon buttons with an optional action button at the end and an overflow menu. `variant: docked` spans its width, 64 tall, on `surface_container`; `floating` is a pill with a shadow that is as long as its buttons, and `vibrant: true` puts it on `primary_container` (the icons on_primary_container). `items` is a list of {value, icon, label} and optionally {disabled}: pressing one sets `chosen` to its `value`; every icon has a label (its name and its tooltip). `overflow` is a list of Menu rows shown under a more button at the end (what does not fit is for the caller to put there). Your own content goes in the default slot after the items. `fab_icon` (with `fab_label` and `on_fab`) adds an action button at the end. `hidden: true` fades the toolbar out of the way and out of the tab order (bind it to the way a list scrolls). The arrow keys move between the buttons (one Tab stop). Role: a group, because the engine has no toolbar role.

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `variant` | `docked` or `floating` | `docked` | docked spans its width; floating is a pill with a shadow. |
| `orientation` | `horizontal` or `vertical` | `horizontal` | A row, or (for the floating one) a column. |
| `vibrant` | `bool` | `false` | primary_container, with on_primary_container icons. |
| `width` | `any` |  | A docked toolbar's width; the width of its place when not given. |
| `label` | `str` | `Toolbar` | The toolbar's accessible name. |
| `items` | `list` | `[]` | The icon buttons, each {value, icon, label} and optionally {disabled}. |
| `overflow` | `list` | `[]` | Menu rows under a more button at the end (empty shows no button). |
| `chosen` | `any` |  | The value of the item or overflow row last pressed. Two-way: give it a bare reference and the view writes it back. |
| `fab_icon` | `str` |  | An action button at the end (empty shows none). |
| `fab_label` | `str` |  | Its name and tooltip. |
| `on_fab` | `handler` |  | What the action button does. |
| `fit` | `bool` | `false` | Items that do not fit move into the overflow menu, after the ones that do (a docked toolbar measures itself; a floating one uses `max_length`). |
| `max_length` | `any` |  | A floating toolbar's longest length in pixels, for `fit`. |
| `hidden` | `bool` | `false` | Faded out of the way and out of the tab order. |
| `disabled` | `bool` | `false` | No button responds. |

Children go in the default slot.

Its parts, by name (a stylesheet rule's `part:` or `name:` addresses one): `group` (Container), `item` (IconButton), `more` (IconButton), `menu` (Menu), `fab` (Fab).

Its look is in [`Toolbar_Stylesheet.yaml`](../stylesheets/toolbars/toolbar.md).

## Using it

```yaml
name: editor
widget: Container
style: {width: 420, height: 200, padding: 16, flex_direction: vertical, gap: 16}
children:
  - widget: Toolbar
    name: tools
    items:
      - {value: bold, icon: format_bold, label: Bold}
      - {value: italic, icon: format_italic, label: Italic}
      - {value: link, icon: link, label: Link}
    overflow:
      - {value: copy, label: Copy}
      - {value: share, label: Share}
    fab_icon: plus
    fab_label: Add
    chosen: "{{ last }}"
  - widget: Toolbar
    variant: floating
    vibrant: true
    items:
      - {value: search, icon: search, label: Search}
      - {value: star, icon: star, label: Star}
  - {widget: Text, text: "{{ last }}", typography_role: body_medium, style: {foreground: on_surface}}
```

## Using it in Python

```python
from tesserae.widgets import toolbar

tools = toolbar(app.window, variant="floating", width=240)
```

## Changing its look

To restyle it in your whole app, write rules for it in your app's stylesheet, or put a stylesheet of the same name next to your views. A rule names the widget and may narrow it by the properties it declares, a part and a state; the most specific rule wins, and a node's own `style:` beats every rule:

```yaml
# Toolbar_Stylesheet.yaml, or any stylesheet your app loads
styles:
  - widget: Toolbar
    style: {background: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
