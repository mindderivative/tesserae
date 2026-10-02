# Floating action buttons

*Actions*

## In Material Design 3

A floating action button (FAB) is the screen's most important action, as an icon in a prominent container.
There are four colours (primary, secondary, tertiary and surface) and three sizes: small (40dp), the
default (56dp) and large (96dp).

## In Tesserae

The size is a parameter, and `fab_size` names it (`small`, `default` or `large`) so a theme's
`components:` entry can shape each.

| Fragment | What it is | Stylesheet |
| --- | --- | --- |
| `component: FabPrimary` | A floating action button in the primary colour: the screen's main action. | [`FabPrimary_Stylesheet.yaml`](../stylesheets/fabs/fab-primary.md) |
| `component: FabSecondary` | A floating action button in the secondary colour. | [`FabSecondary_Stylesheet.yaml`](../stylesheets/fabs/fab-secondary.md) |
| `component: FabTertiary` | A floating action button in the tertiary colour. | [`FabTertiary_Stylesheet.yaml`](../stylesheets/fabs/fab-tertiary.md) |
| `component: FabSurface` | A floating action button on the surface colour. | [`FabSurface_Stylesheet.yaml`](../stylesheets/fabs/fab-surface.md) |

## How it is built

Each fragment is a `*_Component.yaml`: its structure, and the parameters it takes. Its look is in its stylesheet, linked under each one.

### `FabPrimary`, `FabSecondary`, `FabTertiary`, `FabSurface`

| Parameter | | Default |
| --- | --- | --- |
| `icon` | required |  |
| `size` | required |  |
| `corner_radius` | required |  |
| `fab_size` | optional | `default` |

These 4 have one structure; only their stylesheets, above, differ.

```yaml
params:
  - icon
  - size
  - corner_radius
  - {fab_size: default}
id: root
component_of: "fab.{{ fab_size }}"
kind: Rect
children:
  - id: icon
    kind: Icon
    icon:
      name: "{{ icon }}"
```

## Using it

In a view:

```yaml
# Home_View.yaml
id: root
kind: Container
children:
  - id: add
    component: FabPrimary
    with: {icon: add, size: 56, corner_radius: 16}
    handlers: {on_click: add_item}
```

In Python:

```python
from tesserae.widgets import fab

add = fab(app.window, "add", size="default", variant="primary")
```

## Changing its look

To restyle a component in your whole app, put a stylesheet of the same name next to your views. Its rules go over the built-in ones, field by field, and the rest is kept:

```yaml
# FabPrimary_Stylesheet.yaml, next to your views
styles:
  - id: root
    style: {background: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
