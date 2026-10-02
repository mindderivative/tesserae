# Slider

*Selection and input*

## In Material Design 3

A slider lets the user pick a value from a range by dragging a handle, or with the keyboard.

## In Tesserae

The `Slider` kind, a Tesserae control with `value`, `min`, `max` and `step`.

| Fragment | What it is | Stylesheet |
| --- | --- | --- |
| `component: Slider` | A slider: picks a value from a range by dragging. | [`Slider_Stylesheet.yaml`](../stylesheets/sliders/slider.md) |

## How it is built

Each fragment is a `*_Component.yaml`: its structure, and the parameters it takes. Its look is in its stylesheet, linked under each one.

### `Slider`

A slider: picks a value from a range by dragging. Its look: [`Slider_Stylesheet.yaml`](../stylesheets/sliders/slider.md).

| Parameter | | Default |
| --- | --- | --- |
| `background` | required |  |
| `width` | required |  |
| `height` | required |  |
| `value` | required |  |

```yaml
params: [background, width, height, value]
id: root
kind: Slider
value: "{{ value }}"
```

## Using it

In a view:

```yaml
# Home_View.yaml
id: root
kind: Container
children:
  - id: volume
    component: Slider
    with: {background: surface, width: 240, height: 44, value: 0.5}
```

In Python:

```python
from tesserae.widgets import slider

volume = slider(app.window, (0xFF, 0xFF, 0xFF, 0xFF), 240, 44, value=0.5)
volume.on_change(print)
```

## Changing its look

To restyle a component in your whole app, put a stylesheet of the same name next to your views. Its rules go over the built-in ones, field by field, and the rest is kept:

```yaml
# Slider_Stylesheet.yaml, next to your views
styles:
  - id: root
    style: {background: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Controls](../guide/controls.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
