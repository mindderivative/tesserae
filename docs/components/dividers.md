# Dividers

*Containment*

## In Material Design 3

A divider is a thin line that groups and separates content in lists and containers.

## In Tesserae

A one-pixel `Rect` in the `outline_variant` colour.

| Fragment | What it is | Stylesheet |
| --- | --- | --- |
| `component: Divider` | A thin line that separates content. | [`Divider_Stylesheet.yaml`](../stylesheets/dividers/divider.md) |

## How it is built

Each fragment is a `*_Component.yaml`: its structure, and the parameters it takes. Its look is in its stylesheet, linked under each one.

### `Divider`

A thin line that separates content. Its look: [`Divider_Stylesheet.yaml`](../stylesheets/dividers/divider.md).

| Parameter | | Default |
| --- | --- | --- |
| `width` | required |  |
| `height` | required |  |

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
  - id: rule
    component: Divider
    with: {width: 240, height: 1}
```

In Python:

```python
from tesserae.widgets import divider

rule = divider(app.window, 240)
```

## Changing its look

To restyle a component in your whole app, put a stylesheet of the same name next to your views. Its rules go over the built-in ones, field by field, and the rest is kept:

```yaml
# Divider_Stylesheet.yaml, next to your views
styles:
  - id: root
    style: {background: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
