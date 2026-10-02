# Button groups

*Actions*

## In Material Design 3

A button group lays related buttons side by side, with an even gap, so they read as one set of choices.

## In Tesserae

A row of buttons, each made from the fragment named by `button` (filled by default), one for each entry of
`items`.

| Fragment | What it is | Stylesheet |
| --- | --- | --- |
| `component: ButtonGroup` | A row of buttons, each made from the same button fragment. | [`ButtonGroup_Stylesheet.yaml`](../stylesheets/button-groups/button-group.md) |

## How it is built

Each fragment is a `*_Component.yaml`: its structure, and the parameters it takes. Its look is in its stylesheet, linked under each one.

### `ButtonGroup`

A row of buttons, each made from the same button fragment. Its look: [`ButtonGroup_Stylesheet.yaml`](../stylesheets/button-groups/button-group.md).

| Parameter | | Default |
| --- | --- | --- |
| `items` | required |  |
| `width` | required |  |
| `height` | required |  |
| `corner_radius` | required |  |
| `button` | optional | `ButtonFilled` |

```yaml
params:
  - items
  - width
  - height
  - corner_radius
  - {button: ButtonFilled}
id: root
kind: Container
children:
  - id: b
    component: "{{ button }}"
    with:
      width: "{{ width }}"
      height: "{{ height }}"
      corner_radius: "{{ corner_radius }}"
    repeat: "{{ items }}"
```

## Using it

In a view:

```yaml
# Home_View.yaml
id: root
kind: Container
children:
  - id: choices
    component: ButtonGroup
    with:
      items: [{label: Day}, {label: Week}, {label: Month}]
      width: 90
      height: 40
      corner_radius: 20
```

In Python:

```python
from tesserae.widgets import button_group

group = button_group(app.window, ["Day", "Week", "Month"], 90, 40, on_click=viewmodel.pick)
```

## Changing its look

To restyle a component in your whole app, put a stylesheet of the same name next to your views. Its rules go over the built-in ones, field by field, and the rest is kept:

```yaml
# ButtonGroup_Stylesheet.yaml, next to your views
styles:
  - id: root
    style: {flex_direction: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
