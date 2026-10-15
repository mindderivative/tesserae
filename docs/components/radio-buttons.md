# Radio button

*Selection and input*

## In Material Design 3

A radio button lets the user choose one option from a set. Radio buttons in one group exclude each other,
and the arrow keys move between them.

## In Tesserae

`widget: RadioButton`, a Tesserae control: a 20 pixel ring with a dot that grows in when it is chosen. Radio buttons with one `group:` name share a group: choosing
one unchooses the others, the group is one Tab stop (the chosen one, else the first that is not disabled), and the arrow keys move the choice (and the focus) to the next or
previous button that is not disabled, wrapping round. A press on a chosen one does not unchoose it. The `label` sits beside the ring and is part of what you press.

To keep the choice in one value, test it in `selected` and set it in `on_change`: `selected: "{{ size == 'm' }}"`, `on_change: "size = 'm'"`.

## How it is built

### `RadioButton`

One choice of a group.

| Property | Type | Default | Meaning |
| --- | --- | --- | --- |
| `selected` | `bool` |  |  Two-way. |
| `group` | `str` |  | Buttons with one group are exclusive. |
| `disabled` | `bool` |  |  |
| `error` | `bool` |  | Drawn in the error colours. |
| `label` | `str` |  | Text beside it that is part of what you press, and what a screen reader calls it. |

Its `style:` also takes `foreground`.

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

## Using it in Python

```python
from tesserae.controls import RadioGroup
from tesserae.widgets import radio_button

group = RadioGroup()
small = radio_button(app.window, 48, selected=True, group=group)
```

## See also

- [Controls](../guide/controls.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
