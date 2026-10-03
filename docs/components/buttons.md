# Buttons

*Actions*

## In Material Design 3

Buttons let people take an action with one tap. Material Design 3 has five, in order of emphasis: **filled**
for a screen's one main action, **filled tonal** and **elevated** for important but secondary ones,
**outlined** for medium emphasis, and **text** for the lowest: dialogs, cards and toolbars. A button is 40dp
high and fully rounded, and its label is in the *label large* type style.

## In Tesserae

Each type is its own fragment: `component:` can't branch on a name, so a `variant` can't pick between them
the way `button(variant=)` does in Python. A fragment's `corner_radius` is a parameter because `{{ }}` can't
do arithmetic: a pill is half the height, and `button()` works that out for you.

| Fragment | What it is | Stylesheet |
| --- | --- | --- |
| `component: ButtonFilled` | A filled button: the highest-emphasis button, for a screen's main action. | [`ButtonFilled_Stylesheet.yaml`](../stylesheets/buttons/button-filled.md) |
| `component: ButtonFilledTonal` | A filled tonal button: a medium-emphasis button in the secondary container colour. | [`ButtonFilledTonal_Stylesheet.yaml`](../stylesheets/buttons/button-filled-tonal.md) |
| `component: ButtonElevated` | An elevated button: a tinted surface with a shadow, for emphasis on a busy background. | [`ButtonElevated_Stylesheet.yaml`](../stylesheets/buttons/button-elevated.md) |
| `component: ButtonOutlined` | An outlined button: a medium-emphasis button with a border and no fill. | [`ButtonOutlined_Stylesheet.yaml`](../stylesheets/buttons/button-outlined.md) |
| `component: ButtonText` | A text button: the lowest-emphasis button, for dialogs and cards. | [`ButtonText_Stylesheet.yaml`](../stylesheets/buttons/button-text.md) |

## How it is built

Each fragment is a `*_Component.yaml`: its structure, and the parameters it takes. Its look is in its stylesheet, linked under each one.

### `ButtonFilled`, `ButtonFilledTonal`, `ButtonElevated`, `ButtonOutlined`, `ButtonText`

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
kind: Rect
children:
  - id: label
    kind: Text
    text:
      content: "{{ label }}"
      typography_role: label_large
      wrap: none
      overflow: ellipsis
      text_align: center
```

## Using it

In a view:

```yaml
# Home_View.yaml
id: root
kind: Container
children:
  - id: save
    component: ButtonFilled
    with: {label: Save, width: 120, height: 40, corner_radius: 20}
    handlers: {on_click: save}
```

In Python:

```python
from tesserae.widgets import button

save = button(app.window, "Save", 120, 40, variant="filled", on_click=viewmodel.save)
```

## Changing its look

To restyle a component in your whole app, put a stylesheet of the same name next to your views. Its rules go over the built-in ones, field by field, and the rest is kept:

```yaml
# ButtonFilled_Stylesheet.yaml, next to your views
styles:
  - id: root
    style: {background: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Widget Catalog](../guide/widget-catalog.md)
- [Interaction](../guide/interaction.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
