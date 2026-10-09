# Button groups

*Actions*

## In Material Design 3

A button group lays related buttons side by side, with an even gap, so they read as one set of choices.

## In Tesserae

`widget: ButtonGroup` is a view Tesserae ships (`ButtonGroup_View.yaml`): `Button`s side by side, one for each of `items`.

| Property | Type | Meaning |
| --- | --- | --- |
| `items` | a list | the buttons, each `{value, label}` and optionally `{icon, disabled}` |
| `mode` | `none`, `single`, `multiple` | actions; a choice of one; any number chosen |
| `selected` | a value, or a list with `multiple`; two-way | what is chosen |
| `chosen` | a value; two-way | for `none`: the value of the button last pressed (nothing needs to be bound) |
| `variant`, `size` | as on `Button` | passed to every button |
| `connected` | true or false | a 2 pixel gap and square inner corners, instead of 8 pixels apart |
| `orientation` | `horizontal`, `vertical` | a row or a column |
| `disabled` | true or false | no button responds |

In `single` mode a chosen button is a toggle that is on, and the arrow keys move the choice; `multiple` toggles each button and the arrows only move the
focus. There is one Tab stop. Not built: the pressed button widening and its neighbours giving way, and an overflow button.

`widget: ButtonGroup` is the view-language form (see [The View Language](../guide/view-language.md)); the fragment below is the older `component:` form, which keeps working.

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

```yaml
name: calendar
widget: Container
style: {flex_direction: vertical, gap: 12, padding: 16, width: 360, height: 160}
children:
  - widget: ButtonGroup
    mode: single
    connected: true
    variant: tonal
    selected: "{{ range }}"
    items: [{value: day, label: Day}, {value: week, label: Week}, {value: month, label: Month}]
  - widget: ButtonGroup
    chosen: "{{ last_action }}"
    items: [{value: copy, label: Copy, icon: home}, {value: paste, label: Paste}]
```

## Using it

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
