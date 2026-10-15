# Segmented buttons

*Selection and input*

## In Material Design 3

A segmented button is a row of two to five connected options, for one choice or several.

## In Tesserae

`widget: SegmentedButton` is a view Tesserae ships (`SegmentedButton_View.yaml`): one outlined pill (40 pixels tall, a 1 pixel `outline`, fully
rounded) of segments with a line between them.

Each segment is `{value, label}` and optionally `{icon, disabled}`; `options` can be an expression, and follows its Signals. `selected` is the chosen value (with `multiple`, the
list of chosen values) and a press writes it back. A chosen segment is `secondary_container` with a check that takes the place of its icon, and a segment of its own `disabled`,
or all of them with the button's `disabled`, is dimmed and cannot be pressed. Single choice is a radio group: one Tab stop (the chosen segment), and the arrow keys
move the choice, skipping a disabled segment; multiple choice is a group of toggles, each its own Tab stop with the arrows moving focus only. The look is in the view, because each segment's state is its own: write a `SegmentedButton_View.yaml` in your project to change it.

## How it is built

A view Tesserae ships is a `<Name>_View.yaml` (what it takes and what it is made of) with a `<Name>_Stylesheet.yaml` (how it looks). Use it by name: `widget: SegmentedButton`. A file of the same name in your project replaces it.

### `SegmentedButton`

The Material 3 segmented button: two to five connected segments in one outlined pill. `options` is a list of {value, label, icon, disabled}; `selected` is the chosen value, or with `multiple: true` the list of chosen values, and a press writes it back. A chosen segment is `secondary_container` with a check that takes the place of its icon. Single-select behaves as a radio group (one Tab stop, the arrows move the choice); multi-select is a group of toggles. What it looks like is mostly here, in the segments' own style, because each segment's state is its own: restyle it by writing a view of the same name.

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `options` | `list` | `[]` | The segments, each {value, label} and optionally {icon, disabled}. |
| `selected` | `any` |  | The chosen value; with multiple, the list of chosen values. Two-way: give it a bare reference and the view writes it back. |
| `multiple` | `bool` | `false` | Several segments can be chosen at once. |
| `disabled` | `bool` | `false` | Dimmed, and no segment can be pressed. |

Its parts, by name (a stylesheet rule's `part:` or `name:` addresses one): `segment` (Container), `divider` (Container), `icon` (Icon), `label` (Text).

## Using it

```yaml
name: calendar
widget: Container
style: {flex_direction: vertical, gap: 16, width: 360, height: 140, padding: 16}
children:
  - widget: SegmentedButton
    selected: "{{ range }}"
    options:
      - {value: day, label: Day}
      - {value: week, label: Week, icon: home}
      - {value: month, label: Month}
  - widget: SegmentedButton
    multiple: true
    selected: "{{ styles }}"
    options: [{value: bold, label: Bold}, {value: italic, label: Italic}]
```

## Using it in Python

```python
from tesserae.widgets import segmented_button

view = segmented_button(app.window, ["Day", "Week", "Month"], selected=0)
many = segmented_button(app.window, ["Bold", "Italic"], multi=True, selected=[0])
```

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
