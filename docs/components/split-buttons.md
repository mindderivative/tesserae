# Split buttons

*Actions*

## In Material Design 3

A split button joins a main action to a menu of related ones: the leading part does the usual thing, and the
trailing chevron opens the others.

## In Tesserae

One container with a leading and a trailing part; the two parts are separate click targets.

| Fragment | What it is | Stylesheet |
| --- | --- | --- |
| `component: SplitButtonFilled` | A filled split button: an action, and a menu of related ones. | [`SplitButtonFilled_Stylesheet.yaml`](../stylesheets/split-buttons/split-button-filled.md) |
| `component: SplitButtonFilledTonal` | A filled tonal split button: an action, and a menu of related ones. | [`SplitButtonFilledTonal_Stylesheet.yaml`](../stylesheets/split-buttons/split-button-filled-tonal.md) |
| `component: SplitButtonElevated` | An elevated split button: an action, and a menu of related ones. | [`SplitButtonElevated_Stylesheet.yaml`](../stylesheets/split-buttons/split-button-elevated.md) |
| `component: SplitButtonOutlined` | An outlined split button: an action, and a menu of related ones. | [`SplitButtonOutlined_Stylesheet.yaml`](../stylesheets/split-buttons/split-button-outlined.md) |
| `component: SplitButtonText` | A text split button: an action, and a menu of related ones. | [`SplitButtonText_Stylesheet.yaml`](../stylesheets/split-buttons/split-button-text.md) |

## How it is built

Each fragment is a `*_Component.yaml`: its structure, and the parameters it takes. Its look is in its stylesheet, linked under each one.

### `SplitButtonFilled`, `SplitButtonFilledTonal`, `SplitButtonElevated`, `SplitButtonOutlined`, `SplitButtonText`

| Parameter | | Default |
| --- | --- | --- |
| `label` | required |  |
| `width` | required |  |
| `height` | required |  |
| `corner_radius` | required |  |

These 5 have one structure; only their stylesheets, above, differ.

```yaml
params: [label, width, height, corner_radius]
id: root
kind: Container
children:
  - id: leading
    kind: Rect
    children:
      - id: label
        kind: Text
        text:
          content: "{{ label }}"
          typography_role: label_large
  - id: trailing
    kind: Rect
    children:
      - id: chevron
        kind: Icon
        icon: {name: expand_more}
```

## Using it

In a view:

```yaml
# Home_View.yaml
id: root
kind: Container
children:
  - id: send
    component: SplitButtonFilled
    with: {label: Send, width: 160, height: 40, corner_radius: 20}
```

In Python:

```python
from tesserae.widgets import split_button

send = split_button(app.window, "Send", 160, 40, variant="filled")
```

## Changing its look

To restyle a component in your whole app, put a stylesheet of the same name next to your views. Its rules go over the built-in ones, field by field, and the rest is kept:

```yaml
# SplitButtonFilled_Stylesheet.yaml, next to your views
styles:
  - id: leading
    style: {background: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
