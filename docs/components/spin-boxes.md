# Spin box

*Selection and input*

## In Material Design 3

Material Design 3 has no spin box. Tesserae's is built from MD3's parts: a number field between two 40dp
icon buttons.

## In Tesserae

The `SpinBox` kind (`widget: SpinBox` in a view), a Tesserae control. Typing, the arrow keys and the buttons change `value`; `min`, `max` and `step` bound it.

| Property | Type | Meaning |
| --- | --- | --- |
| `value`, `min`, `max`, `step` | numbers; `value` is two-way | the number and what bounds and moves it |
| `decimals` | a whole number | how many decimal places show |
| `prefix`, `suffix` | text | shown with the number (a currency sign, a unit); typing may include them or not |
| `wrap` | true or false | a step past one bound lands on the other, so the buttons never disable (needs `min` and `max`) |
| `label`, `disabled` | text, true or false | the name for a screen reader; dimmed |

Holding a button steps again after 400 milliseconds and then every 80, until it is let go or reaches a bound; Page Up and Page Down step ten at a time.
`widget: SpinBoxField` is a view Tesserae ships that adds a visible `label` above and a line of `supporting` or `error` text under it (`least` and `most` are its
bounds, `min` and `max` being reserved names). Not built: a hold that speeds up the longer it is held, and a spin box in a vertical arrangement.

| Fragment | What it is | Stylesheet |
| --- | --- | --- |
| `component: SpinBox` | A number field between minus and plus buttons. | none: the control draws itself |

## How it is built

Each fragment is a `*_Component.yaml`: its structure, and the parameters it takes. Its look is in its stylesheet, linked under each one.

### `SpinBox`

A number field between minus and plus buttons.

| Parameter | | Default |
| --- | --- | --- |
| `value` | required |  |
| `min` | optional | `None` |
| `max` | optional | `None` |
| `step` | optional | `1` |

```yaml
params:
  - value
  - {min: null}
  - {max: null}
  - {step: 1}
id: root
kind: SpinBox
value: "{{ value }}"
min: "{{ min }}"
max: "{{ max }}"
step: "{{ step }}"
```

## Using it

```yaml
name: order
widget: Container
style: {flex_direction: vertical, gap: 16, width: 320, height: 240}
children:
  - {widget: SpinBox, value: "{{ count }}", min: 0, max: 10, label: Count}
  - {widget: SpinBoxField, label: Weight, value: "{{ weight }}", least: 0, most: 50, step: 0.5, decimals: 1, suffix: " kg", supporting: Up to 50}
```

## Using it

In Python:

```python
from tesserae.widgets import spin_box

quantity = spin_box(app.window, 1, min=0, max=10)
```

## See also

- [Controls](../guide/controls.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
