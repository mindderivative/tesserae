# Segmented buttons

*Selection and input*

## In Material Design 3

A segmented button is a row of two to five connected options, for one choice or several.

## In Tesserae

`widget: SegmentedButton` is a view Tesserae ships (`SegmentedButton_View.yaml`): one outlined pill (40 pixels tall, a 1 pixel `outline`, fully
rounded) of segments with a line between them.

| Property | Type | Meaning |
| --- | --- | --- |
| `options` | a list | the segments, each `{value, label}` and optionally `{icon, disabled}`; an expression follows its Signals |
| `selected` | a value, or a list with `multiple`; two-way | the chosen one(s); a press writes it back |
| `multiple` | true or false | several can be chosen; each segment toggles |
| `disabled` | true or false | dimmed, and no segment can be pressed |

A chosen segment is `secondary_container` with a check that takes the place of its icon. Single choice is a radio group: one Tab stop (the
chosen segment), and the arrow keys move the choice; multiple choice is a group of toggles, each its own Tab stop with the arrows moving focus
only. The look is in the view, because each segment's state is its own: write a `SegmentedButton_View.yaml` in your project to change it.

This component is a view Tesserae ships: use `widget: SegmentedButton` in a view (see [The View Language](../guide/view-language.md)).

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

## Using it

In Python:

```python
from tesserae.widgets import segmented_button

view = segmented_button(app.window, ["Day", "Week", "Month"], selected=0)
many = segmented_button(app.window, ["Bold", "Italic"], multi=True, selected=[0])
```

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
