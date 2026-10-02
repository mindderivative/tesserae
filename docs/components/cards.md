# Cards

*Containment*

## In Material Design 3

A card holds content and actions about one subject. It comes **elevated** (a shadow), **filled** (a
higher surface) or **outlined** (a border). All have a medium (12dp) corner radius.

## In Tesserae

A content-free `Rect`: add children inside it in your view, or with `.node.add_child` in Python.

| Fragment | What it is | Stylesheet |
| --- | --- | --- |
| `component: CardElevated` | An elevated card: a container on a tinted surface with a shadow. | [`CardElevated_Stylesheet.yaml`](../stylesheets/cards/card-elevated.md) |
| `component: CardFilled` | A filled card: a container on a higher surface, with no shadow or border. | [`CardFilled_Stylesheet.yaml`](../stylesheets/cards/card-filled.md) |
| `component: CardOutlined` | An outlined card: a container with a border and no fill. | [`CardOutlined_Stylesheet.yaml`](../stylesheets/cards/card-outlined.md) |

## How it is built

Each fragment is a `*_Component.yaml`: its structure, and the parameters it takes. Its look is in its stylesheet, linked under each one.

### `CardElevated`, `CardFilled`, `CardOutlined`

| Parameter | | Default |
| --- | --- | --- |
| `width` | required |  |
| `height` | required |  |

These 3 have one structure; only their stylesheets, above, differ.

```yaml
params: [width, height]
id: root
kind: Rect
```

## Using it

In a view:

```yaml
# Home_View.yaml
id: root
kind: Container
children:
  - id: summary
    component: CardElevated
    with: {width: 240, height: 120}
```

In Python:

```python
from tesserae.widgets import card

summary = card(app.window, 240, 120, variant="elevated")
```

## Changing its look

To restyle a component in your whole app, put a stylesheet of the same name next to your views. Its rules go over the built-in ones, field by field, and the rest is kept:

```yaml
# CardElevated_Stylesheet.yaml, next to your views
styles:
  - id: root
    style: {background: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
