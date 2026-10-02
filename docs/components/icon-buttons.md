# Icon buttons

*Actions*

## In Material Design 3

An icon button is an action shown as a glyph alone. Like buttons it has four emphases: standard (no
container), filled, filled tonal and outlined. It is 40dp, with a 48dp touch target.

## In Tesserae

A round `Rect` with an `Icon` inside. `corner_radius` is half the `size`.

| Fragment | What it is | Stylesheet |
| --- | --- | --- |
| `component: IconButtonStandard` | A standard icon button: a low-emphasis action shown as an icon alone. | [`IconButtonStandard_Stylesheet.yaml`](../stylesheets/icon-buttons/icon-button-standard.md) |
| `component: IconButtonFilled` | A filled icon button: a high-emphasis action shown as an icon. | [`IconButtonFilled_Stylesheet.yaml`](../stylesheets/icon-buttons/icon-button-filled.md) |
| `component: IconButtonFilledTonal` | A filled tonal icon button: a medium-emphasis action shown as an icon. | [`IconButtonFilledTonal_Stylesheet.yaml`](../stylesheets/icon-buttons/icon-button-filled-tonal.md) |
| `component: IconButtonOutlined` | An outlined icon button: a medium-emphasis action shown as an icon with a border. | [`IconButtonOutlined_Stylesheet.yaml`](../stylesheets/icon-buttons/icon-button-outlined.md) |

## How it is built

Each fragment is a `*_Component.yaml`: its structure, and the parameters it takes. Its look is in its stylesheet, linked under each one.

### `IconButtonStandard`, `IconButtonFilled`, `IconButtonFilledTonal`, `IconButtonOutlined`

| Parameter | | Default |
| --- | --- | --- |
| `icon` | required |  |
| `size` | required |  |
| `corner_radius` | required |  |

These 4 have one structure; only their stylesheets, above, differ.

```yaml
params: [icon, size, corner_radius]
id: root
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
  - id: settings
    component: IconButtonStandard
    with: {icon: settings, size: 40, corner_radius: 20}
    handlers: {on_click: open_settings}
```

In Python:

```python
from tesserae.widgets import icon_button

settings = icon_button(app.window, "settings", 40, variant="standard")
```

## Changing its look

To restyle a component in your whole app, put a stylesheet of the same name next to your views. Its rules go over the built-in ones, field by field, and the rest is kept:

```yaml
# IconButtonStandard_Stylesheet.yaml, next to your views
styles:
  - id: root
    style: {background: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
