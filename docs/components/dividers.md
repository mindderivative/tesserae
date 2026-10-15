# Dividers

*Containment*

## In Material Design 3

A divider is a thin line that groups and separates content in lists and containers. It spans the whole length (**full-width**), starts
16 dp in from the start (**inset**), or is 16 dp in from both ends (**middle inset**), and is horizontal or vertical.

## In Tesserae

`widget: Divider` is a view Tesserae ships (`Divider_View.yaml`) with its look as rules (`Divider_Stylesheet.yaml`): a line in the
`outline_variant` colour that fills the length it is in, and is a `separator` to a screen reader.

The `variant` says how much of the ends it keeps clear (`full` by default; `inset` leaves 16 pixels at the start, `middle` 16 at both ends). A `horizontal` divider fills the
width it is in and a `vertical` one the height; it is 1 pixel thick unless `thickness` says.

## How it is built

A view Tesserae ships is a `<Name>_View.yaml` (what it takes and what it is made of) with a `<Name>_Stylesheet.yaml` (how it looks). Use it by name: `widget: Divider`. A file of the same name in your project replaces it.

### `Divider`

The Material 3 divider: a thin line that separates content. `variant: full | inset | middle`, `orientation: horizontal | vertical`. What it looks like (the colour, the thickness, the insets) is in Divider_Stylesheet.yaml; this file is its structure. A screen reader hears it as a `separator`.

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `variant` | `full` or `inset` or `middle` | `full` | full spans the whole length; inset starts 16 in from the start; middle is 16 in from both ends. |
| `orientation` | `horizontal` or `vertical` | `horizontal` | Horizontal separates rows and fills the width it is in; vertical separates columns and fills the height. |
| `thickness` | `float` | `1` | How thick the line is. |

Its look is in [`Divider_Stylesheet.yaml`](../stylesheets/dividers/divider.md).

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

## Using it in Python

```python
from tesserae.widgets import divider

rule = divider(app.window, 240)
```

## Changing its look

To restyle it in your whole app, write rules for it in your app's stylesheet, or put a stylesheet of the same name next to your views. A rule names the widget and may narrow it by the properties it declares, a part and a state; the most specific rule wins, and a node's own `style:` beats every rule:

```yaml
# Divider_Stylesheet.yaml, or any stylesheet your app loads
styles:
  - widget: Divider
    style: {background: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
