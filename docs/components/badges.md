# Badges

*Communication*

## In Material Design 3

A badge shows that something has news. The small one is a dot, and the large one carries a short count or
text. It sits on the corner of what it describes.

## In Tesserae

The dot is a small `Rect`; the labelled badge is a pill with `label_small` text.

| Fragment | What it is | Stylesheet |
| --- | --- | --- |
| `component: BadgeDot` | A small dot that marks something as having news, with no number. | [`BadgeDot_Stylesheet.yaml`](../stylesheets/badges/badge-dot.md) |
| `component: BadgeLabeled` | A small pill carrying a short count or label. | [`BadgeLabeled_Stylesheet.yaml`](../stylesheets/badges/badge-labeled.md) |

## How it is built

Each fragment is a `*_Component.yaml`: its structure, and the parameters it takes. Its look is in its stylesheet, linked under each one.

### `BadgeDot`

A small dot that marks something as having news, with no number. Its look: [`BadgeDot_Stylesheet.yaml`](../stylesheets/badges/badge-dot.md).

It takes no parameters.

```yaml
{id: root, kind: Rect}
```

### `BadgeLabeled`

A small pill carrying a short count or label. Its look: [`BadgeLabeled_Stylesheet.yaml`](../stylesheets/badges/badge-labeled.md).

| Parameter | | Default |
| --- | --- | --- |
| `label` | required |  |
| `width` | required |  |

```yaml
params: [label, width]
id: root
kind: Container
children:
  - id: label
    kind: Text
    text:
      content: "{{ label }}"
      typography_role: label_small
      text_align: center
```

## Using it

In a view:

```yaml
# Home_View.yaml
id: root
kind: Container
children:
  - id: unread
    component: BadgeLabeled
    with: {label: "3", width: 20}
```

In Python:

```python
from tesserae.widgets import badge

unread = badge(app.window, "3")
```

## Changing its look

To restyle a component in your whole app, put a stylesheet of the same name next to your views. Its rules go over the built-in ones, field by field, and the rest is kept:

```yaml
# BadgeDot_Stylesheet.yaml, next to your views
styles:
  - id: root
    style: {background: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
