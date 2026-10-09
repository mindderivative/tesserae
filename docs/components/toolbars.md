# Toolbars

*Navigation*

## In Material Design 3

A toolbar groups the actions for the content around it. A **docked** one is fixed to an edge; a **floating**
one is a rounded bar over the content.

## In Tesserae

`widget: Toolbar` is a view Tesserae ships (`Toolbar_View.yaml`): one widget for the docked and the floating toolbar, built from `IconButton`s, an optional `Fab` and a `Menu`.

| Property | Type | Meaning |
| --- | --- | --- |
| `variant` | `docked` or `floating` | docked spans its width, 64 tall, on `surface_container`; floating is a pill with a shadow as long as its buttons |
| `orientation` | `horizontal` or `vertical` | a floating toolbar can be a column, 64 wide |
| `vibrant` | true or false | `primary_container`, with `on_primary_container` icons |
| `items` | a list | the icon buttons, each `{value, icon, label}` and optionally `disabled` |
| `chosen` | a value; two-way | the `value` of the item or overflow row pressed |
| `overflow` | a list | `Menu` rows under a more button at the end |
| `fab_icon`, `fab_label`, `on_fab` | | an action button at the end, and what it does |
| `hidden` | true or false | fades it out and takes its buttons out of the tab order (bind it to the way a list scrolls) |
| `label`, `width`, `disabled` | | its accessible name; a docked toolbar's width; no button responds |

Your own content goes in the default slot after the items. The arrow keys move between the buttons (one Tab stop). The role is `group`: the engine has no toolbar role.
Not built: moving the buttons that do not fit into the overflow menu by width (list them in `overflow` yourself), and sliding out of the way (it fades).

`widget: Toolbar` is the view-language form (see [The View Language](../guide/view-language.md)); the fragment below is the older `component:` form, which keeps working.

| Fragment | What it is | Stylesheet |
| --- | --- | --- |
| `component: ToolbarDocked` | A docked toolbar: a bar of actions fixed to an edge of the window. | [`ToolbarDocked_Stylesheet.yaml`](../stylesheets/toolbars/toolbar-docked.md) |
| `component: ToolbarFloating` | A floating toolbar: a rounded bar of actions over the content. | [`ToolbarFloating_Stylesheet.yaml`](../stylesheets/toolbars/toolbar-floating.md) |

## How it is built

Each fragment is a `*_Component.yaml`: its structure, and the parameters it takes. Its look is in its stylesheet, linked under each one.

### `ToolbarDocked`

A docked toolbar: a bar of actions fixed to an edge of the window. Its look: [`ToolbarDocked_Stylesheet.yaml`](../stylesheets/toolbars/toolbar-docked.md).

| Parameter | | Default |
| --- | --- | --- |
| `background` | required |  |
| `width` | required |  |

```yaml
params: [background, width]
id: root
kind: Container
children: []
```

### `ToolbarFloating`

A floating toolbar: a rounded bar of actions over the content. Its look: [`ToolbarFloating_Stylesheet.yaml`](../stylesheets/toolbars/toolbar-floating.md).

| Parameter | | Default |
| --- | --- | --- |
| `background` | required |  |
| `width` | required |  |
| `corner_radius` | required |  |

```yaml
params: [background, width, corner_radius]
id: root
kind: Container
children: []
```

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

## Using it

In Python:

```python
from tesserae.widgets import toolbar

tools = toolbar(app.window, variant="floating", width=240)
```

## Changing its look

To restyle a component in your whole app, put a stylesheet of the same name next to your views. Its rules go over the built-in ones, field by field, and the rest is kept:

```yaml
# ToolbarDocked_Stylesheet.yaml, next to your views
styles:
  - id: root
    style: {background: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
