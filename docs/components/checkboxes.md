# Checkbox

*Selection and input*

## In Material Design 3

A checkbox lets the user select one or more items from a set, or turn an option on or off. It has a 40dp
state layer around an 18dp box.

## In Tesserae

The `Checkbox` kind is one of Tesserae's controls (`tesserae.controls.Checkbox`), whose `checked` is a
signal, so a binding can read and write it.

| Fragment | What it is | Stylesheet |
| --- | --- | --- |
| `component: Checkbox` | A checkbox: one choice, on or off. | [`Checkbox_Stylesheet.yaml`](../stylesheets/checkboxes/checkbox.md) |

## How it is built

Each fragment is a `*_Component.yaml`: its structure, and the parameters it takes. Its look is in its stylesheet, linked under each one.

### `Checkbox`

A checkbox: one choice, on or off. Its look: [`Checkbox_Stylesheet.yaml`](../stylesheets/checkboxes/checkbox.md).

| Parameter | | Default |
| --- | --- | --- |
| `background` | required |  |
| `width` | required |  |
| `height` | required |  |
| `checked` | required |  |

```yaml
params: [background, width, height, checked]
id: root
kind: Checkbox
checked: "{{ checked }}"
```

## Using it

In a view:

```yaml
# Home_View.yaml
id: root
kind: Container
children:
  - id: agree
    component: Checkbox
    with: {background: surface, width: 48, height: 48, checked: false}
    handlers: {on_change: toggled}
```

In Python:

```python
from tesserae.widgets import checkbox

agree = checkbox(app.window, (0xFF, 0xFF, 0xFF, 0xFF), 48, 48, checked=False)
agree.checked.get()
```

## Changing its look

To restyle a component in your whole app, put a stylesheet of the same name next to your views. Its rules go over the built-in ones, field by field, and the rest is kept:

```yaml
# Checkbox_Stylesheet.yaml, next to your views
styles:
  - id: root
    style: {background: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Controls](../guide/controls.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
