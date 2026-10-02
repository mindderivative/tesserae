# Extended FABs

*Actions*

## In Material Design 3

An extended FAB is a FAB with a text label, for a main action that an icon alone wouldn't explain.

## In Tesserae

A container with an optional icon and a label; give no `icon` for a text-only one.

| Fragment | What it is | Stylesheet |
| --- | --- | --- |
| `component: ExtendedFabPrimary` | An extended floating action button in the primary colour: an icon and a label. | [`ExtendedFabPrimary_Stylesheet.yaml`](../stylesheets/extended-fabs/extended-fab-primary.md) |
| `component: ExtendedFabSecondary` | An extended floating action button in the secondary colour. | [`ExtendedFabSecondary_Stylesheet.yaml`](../stylesheets/extended-fabs/extended-fab-secondary.md) |
| `component: ExtendedFabTertiary` | An extended floating action button in the tertiary colour. | [`ExtendedFabTertiary_Stylesheet.yaml`](../stylesheets/extended-fabs/extended-fab-tertiary.md) |
| `component: ExtendedFabSurface` | An extended floating action button on the surface colour. | [`ExtendedFabSurface_Stylesheet.yaml`](../stylesheets/extended-fabs/extended-fab-surface.md) |

## How it is built

Each fragment is a `*_Component.yaml`: its structure, and the parameters it takes. Its look is in its stylesheet, linked under each one.

### `ExtendedFabPrimary`, `ExtendedFabSecondary`, `ExtendedFabTertiary`, `ExtendedFabSurface`

| Parameter | | Default |
| --- | --- | --- |
| `label` | required |  |
| `width` | required |  |
| `icon` | optional | `None` |

These 4 have one structure; only their stylesheets, above, differ.

```yaml
params:
  - label
  - width
  - {icon: null}
id: root
kind: Container
children:
  - id: icon
    when: "{{ icon }}"
    kind: Icon
    icon:
      name: "{{ icon }}"
  - id: label
    kind: Text
    text:
      content: "{{ label }}"
      typography_role: label_large
```

## Using it

In a view:

```yaml
# Home_View.yaml
id: root
kind: Container
children:
  - id: new
    component: ExtendedFabPrimary
    with: {label: New, icon: add, width: 120}
```

In Python:

```python
from tesserae.widgets import extended_fab

new = extended_fab(app.window, "New", 120, icon="add", variant="primary")
```

## Changing its look

To restyle a component in your whole app, put a stylesheet of the same name next to your views. Its rules go over the built-in ones, field by field, and the rest is kept:

```yaml
# ExtendedFabPrimary_Stylesheet.yaml, next to your views
styles:
  - id: root
    style: {background: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
