# Spin box

*Selection and input*

## In Material Design 3

Material Design 3 has no spin box. Tesserae's is built from MD3's parts: a number field between two 40dp
icon buttons.

## In Tesserae

The `SpinBox` kind, a Tesserae control. Typing, the arrow keys and the buttons change `value`; `min`, `max`
and `step` bound it.

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

In a view:

```yaml
# Home_View.yaml
id: root
kind: Container
children:
  - id: quantity
    component: SpinBox
    with: {value: 1, min: 0, max: 10, step: 1}
```

In Python:

```python
from tesserae.widgets import spin_box

quantity = spin_box(app.window, 1, min=0, max=10)
```

## See also

- [Controls](../guide/controls.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
