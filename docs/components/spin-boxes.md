# Spin box

*Selection and input*

## In Material Design 3

Material Design 3 has no spin box. Tesserae's is built from MD3's parts: a number field between two 40dp
icon buttons.

## In Tesserae

The `SpinBox` kind (`widget: SpinBox` in a view), a Tesserae control: a 64 by 40 pixel number field between two 40 pixel buttons. The buttons, the up and down arrow keys in the
field and a screen reader's increment and decrement change `value` by `step`; typing a number sets it once it parses and fits `min` to `max`, and leaving the field puts the
value's text back if what was typed did not. A button whose step would pass a bound is disabled, unless `wrap` is on (it needs `min` and `max`): then a step past one bound
lands on the other and the buttons never disable. `decimals` fixes how many places show (without it, only as many as the number needs). `prefix` and `suffix` (a currency sign,
a unit) are shown with the number, and typing may include them or not. `label` is the name for a screen reader.

Holding a button steps again after 400 milliseconds and then every 80, until it is let go or reaches a bound; Page Up and Page Down step ten at a time.
`widget: SpinBoxField` is a view Tesserae ships that adds a visible `label` above and a line of `supporting` or `error` text under it (`least` and `most` are its
bounds, `min` and `max` being reserved names). Not built: a hold that speeds up the longer it is held, and a spin box in a vertical arrangement.

## How it is built

A view Tesserae ships is a `<Name>_View.yaml` (what it takes and what it is made of) with a `<Name>_Stylesheet.yaml` (how it looks). Use it by name: `widget: SpinBoxField`. A file of the same name in your project replaces it.

### `SpinBoxField`

A spin box with a visible label above it and a line of supporting or error text under it, as a text field has them. `value` is two-way. The label also names the spin box for a screen reader; when `error` is not empty it replaces the supporting text, in the error colour.

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `label` | `str` |  | The name above the spin box. |
| `supporting` | `str` |  | Help under it. |
| `error` | `str` |  | An error message; it replaces the supporting text. |
| `value` | `float` | `0` | The number; stepping and typing write it back. Two-way: give it a bare reference and the view writes it back. |
| `least` | `float` |  | The least it takes (`min` is a reserved name). |
| `most` | `float` |  | The most it takes. |
| `step` | `float` | `1` | How far a button moves it. |
| `decimals` | `int` |  | How many decimal places show. |
| `prefix` | `str` |  | Shown before the number. |
| `suffix` | `str` |  | Shown after the number (a unit). |
| `wrap` | `bool` | `false` | A step past one bound lands on the other. |
| `disabled` | `bool` | `false` | Dimmed and not steppable. |

Its parts, by name (a stylesheet rule's `part:` or `name:` addresses one): `label` (Text), `box` (SpinBox), `help` (Text).

Its look is in [`SpinBoxField_Stylesheet.yaml`](../stylesheets/spin-boxes/spin-box-field.md).

### `SpinBox`

A number with step buttons. Holding a button repeats the step; Page Up and Page Down step by ten.

| Property | Type | Default | Meaning |
| --- | --- | --- | --- |
| `value` | `float` |  |  Two-way. |
| `min` | `float` |  |  |
| `max` | `float` |  |  |
| `step` | `float` | `1.0` |  |
| `disabled` | `bool` |  |  |
| `label` | `str` |  | What a screen reader calls it. |
| `decimals` | `int` |  | How many decimal places show (empty: only as many as the number needs). |
| `prefix` | `str` |  | Shown before the number, such as a currency sign. |
| `suffix` | `str` |  | Shown after the number, such as a unit. |
| `wrap` | `bool` |  | A step past one bound lands on the other (needs min and max). |

## Using it

```yaml
name: order
widget: Container
style: {flex_direction: vertical, gap: 16, width: 320, height: 240}
children:
  - {widget: SpinBox, value: "{{ count }}", min: 0, max: 10, label: Count}
  - {widget: SpinBoxField, label: Weight, value: "{{ weight }}", least: 0, most: 50, step: 0.5, decimals: 1, suffix: " kg", supporting: Up to 50}
```

## Using it in Python

```python
from tesserae.widgets import spin_box

quantity = spin_box(app.window, 1, min=0, max=10)
```

## Changing its look

To restyle it in your whole app, write rules for it in your app's stylesheet, or put `<Name>_Stylesheet.yaml` next to your views (or in `Styles/`); it is read only while the app uses the view. A rule names the widget and may narrow it by the properties it declares, a part and a state; the most specific rule wins, and a node's own `style:` beats every rule:

```yaml
# SpinBoxField_Stylesheet.yaml, or any stylesheet your app loads
styles:
  - widget: SpinBoxField
    part: label
    style: {foreground: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Controls](../guide/controls.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
