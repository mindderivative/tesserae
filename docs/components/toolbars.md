# Toolbars

*Navigation*

## In Material Design 3

A toolbar groups the actions for the content around it. A **docked** one is fixed to an edge; a **floating**
one is a rounded bar over the content.

## In Tesserae

Containers whose children are yours: put buttons or icon buttons inside.

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

In a view:

```yaml
# Home_View.yaml
id: root
kind: Container
children:
  - id: tools
    component: ToolbarFloating
    with: {background: surface_container, width: 240, corner_radius: 28}
```

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
