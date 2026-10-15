# Button groups

*Actions*

## In Material Design 3

A button group lays related buttons side by side, with an even gap, so they read as one set of choices.

## In Tesserae

`widget: ButtonGroup` is a view Tesserae ships (`ButtonGroup_View.yaml`): `Button`s side by side, one for each of `items`.

The `mode` says what the buttons are: `none` (the default) is a row of actions, and the value of the one last pressed goes to `chosen` (nothing needs to be bound);
`single` is a choice of one, with `selected` its value; `multiple` is a set, with `selected` the list of chosen values. Each item is `{value, label}` and optionally
`{icon, disabled}`. `variant` and `size` are `Button`'s and go to every button. By default the buttons stand 8 pixels apart; `connected: true` makes the gap 2
pixels with 4 pixel inner corners, and `orientation: vertical` makes a column.

In `single` mode a chosen button is a toggle that is on, and the arrow keys move the choice; `multiple` toggles each button and the arrows only move the
focus. There is one Tab stop. Not built: the pressed button widening and its neighbours giving way, and an overflow button.

## How it is built

A view Tesserae ships is a `<Name>_View.yaml` (what it takes and what it is made of) with a `<Name>_Stylesheet.yaml` (how it looks). Use it by name: `widget: ButtonGroup`. A file of the same name in your project replaces it.

### `ButtonGroup`

The Material 3 button group: buttons that behave as a set. `mode: none` is a row of actions (the last one pressed goes to `chosen`), `single` is a choice of one (`selected` is the chosen value) and `multiple` a set (`selected` is the list of chosen values). `connected: true` joins the buttons with a 2 pixel gap and square inner corners; otherwise they stand 8 pixels apart. One Tab stop; the arrow keys move the focus (and, for `single`, the choice). The look of each button is Button's: `variant` and `size` pass to every one.

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `items` | `list` | `[]` | The buttons, each {value, label} and optionally {icon, disabled}. |
| `mode` | `none` or `single` or `multiple` | `none` | none: actions; single: one chosen; multiple: any number chosen. |
| `selected` | `any` |  | single: the chosen value; multiple: the list of chosen values. Two-way: give it a bare reference and the view writes it back. |
| `chosen` | `any` |  | none: the value of the button last pressed. Two-way: give it a bare reference and the view writes it back. |
| `variant` | `filled` or `tonal` or `elevated` or `outlined` or `text` | `filled` | Passed to every button. |
| `size` | `xs` or `s` or `m` or `l` or `xl` | `s` | Passed to every button. |
| `connected` | `bool` | `false` | Joined, with square inner corners. |
| `orientation` | `horizontal` or `vertical` | `horizontal` | A row, or a column. |
| `disabled` | `bool` | `false` | No button can be pressed. |

Its parts, by name (a stylesheet rule's `part:` or `name:` addresses one): `item` (Button).

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

## Using it in Python

```python
from tesserae.widgets import button_group

group = button_group(app.window, ["Day", "Week", "Month"], 90, 40, on_click=viewmodel.pick)
```

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
