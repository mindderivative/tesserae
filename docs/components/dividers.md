# Dividers

*Containment*

## In Material Design 3

A divider is a thin line that groups and separates content in lists and containers. It spans the whole length (**full-width**), starts
16 dp in from the start (**inset**), or is 16 dp in from both ends (**middle inset**), and is horizontal or vertical.

## In Tesserae

`widget: Divider` is a view Tesserae ships (`Divider_View.yaml`) with its look as rules (`Divider_Stylesheet.yaml`): a line in the
`outline_variant` colour that fills the length it is in, and is hidden from a screen reader (tre has no `separator` role to give it).

| Property | Type | Meaning |
| --- | --- | --- |
| `variant` | `full`, `inset` or `middle` | how much of the ends it keeps clear; `full` by default |
| `orientation` | `horizontal` or `vertical` | horizontal fills the width it is in, vertical the height; `horizontal` by default |
| `thickness` | number | how thick the line is; `1` by default |

`widget: Divider` is the view-language form (see [The View Language](../guide/view-language.md)); the fragment below is the older `component:` form, which keeps working.

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

```yaml
name: settings
widget: Container
style: {flex_direction: vertical, width: 320, height: 160}
children:
  - {widget: Text, text: Wi-Fi, typography_role: body_large, style: {foreground: on_surface}}
  - {widget: Divider, variant: inset}
  - {widget: Text, text: Bluetooth, typography_role: body_large, style: {foreground: on_surface}}
  - {widget: Divider}
```

## Changing its look

Write rules for `Divider` in your app's stylesheet; they sit above the shipped ones, and a `style:` on the node beats every rule for the
fields it sets.

```yaml
styles:
  - widget: Divider
    style: {background: outline}
```

A view named `Divider_View.yaml` in your project replaces the shipped divider, and its shipped look with it.

## Using the fragment

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
