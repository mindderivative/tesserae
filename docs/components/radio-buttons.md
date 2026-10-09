# Radio button

*Selection and input*

## In Material Design 3

A radio button lets the user choose one option from a set. Radio buttons in one group exclude each other,
and the arrow keys move between them.

## In Tesserae

`widget: RadioButton`, a Tesserae control. Radio buttons with one `group:` name share a group: choosing one unchooses the others, the group is one
Tab stop (the chosen one, else the first), and the arrow keys move the choice.

| Property | Type | Meaning |
| --- | --- | --- |
| `selected` | true or false, two-way | whether it is the chosen one |
| `group` | a name | buttons with the same name exclude each other |
| `label` | text | beside the ring, part of what you press, and what a screen reader calls it |
| `error` | true or false | drawn in the error colours |
| `disabled` | true or false | dimmed and does nothing |

To keep the choice in one value, test it in `selected` and set it in `on_change`: `selected: "{{ size == 'm' }}"`, `on_change: "size = 'm'"`.

`widget: RadioButton` is the view-language form (see [The View Language](../guide/view-language.md)); the fragment below is the older `component:` form, which keeps working.

| Fragment | What it is | Stylesheet |
| --- | --- | --- |
| `component: RadioButton` | A radio button: one choice among several. | [`RadioButton_Stylesheet.yaml`](../stylesheets/radio-buttons/radio-button.md) |

## How it is built

Each fragment is a `*_Component.yaml`: its structure, and the parameters it takes. Its look is in its stylesheet, linked under each one.

### `RadioButton`

A radio button: one choice among several. Its look: [`RadioButton_Stylesheet.yaml`](../stylesheets/radio-buttons/radio-button.md).

| Parameter | | Default |
| --- | --- | --- |
| `size` | required |  |
| `selected` | required |  |

```yaml
params: [size, selected]
id: root
kind: RadioButton
selected: "{{ selected }}"
```

## Using it

```yaml
name: sizes
widget: Container
style: {flex_direction: vertical, gap: 4, width: 240, height: 180, padding: 16}
children:
  - {widget: RadioButton, group: size, label: Small, selected: "{{ size == 's' }}", handlers: {on_change: "size = 's'"}}
  - {widget: RadioButton, group: size, label: Medium, selected: "{{ size == 'm' }}", handlers: {on_change: "size = 'm'"}}
  - {widget: RadioButton, group: size, label: Large, selected: "{{ size == 'l' }}", handlers: {on_change: "size = 'l'"}}
```

## Using the fragment

In a view:

```yaml
# Home_View.yaml
id: root
kind: Container
children:
  - id: small
    component: RadioButton
    with: {size: 48, selected: true}
```

In Python:

```python
from tesserae.controls import RadioGroup
from tesserae.widgets import radio_button

group = RadioGroup()
small = radio_button(app.window, 48, selected=True, group=group)
```

## Changing its look

To restyle a component in your whole app, put a stylesheet of the same name next to your views. Its rules go over the built-in ones, field by field, and the rest is kept:

```yaml
# RadioButton_Stylesheet.yaml, next to your views
styles:
  - id: root
    style: {width: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Controls](../guide/controls.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
