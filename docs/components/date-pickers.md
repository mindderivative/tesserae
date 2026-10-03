# Date picker

*Selection and input*

## In Material Design 3

A date picker lets the user pick a date from a month grid. Today is outlined, the chosen day is a filled
circle, and days of the neighbouring months are dimmed.

## In Tesserae

The day cell only, in its four states; you lay the grid out (a `display: grid` container is the natural
fit).

| Fragment | What it is | Stylesheet |
| --- | --- | --- |
| `component: DatePickerDay` | One day in a date picker's month grid. | [`DatePickerDay_Stylesheet.yaml`](../stylesheets/date-pickers/date-picker-day.md) |
| `component: DatePickerDayToday` | Today in a date picker's grid: an outlined circle. | [`DatePickerDayToday_Stylesheet.yaml`](../stylesheets/date-pickers/date-picker-day-today.md) |
| `component: DatePickerDaySelected` | The selected day in a date picker's grid: a filled circle. | [`DatePickerDaySelected_Stylesheet.yaml`](../stylesheets/date-pickers/date-picker-day-selected.md) |
| `component: DatePickerDayOutsideMonth` | A day of the neighbouring month, shown dimmed in a date picker's grid. | [`DatePickerDayOutsideMonth_Stylesheet.yaml`](../stylesheets/date-pickers/date-picker-day-outside-month.md) |

## How it is built

Each fragment is a `*_Component.yaml`: its structure, and the parameters it takes. Its look is in its stylesheet, linked under each one.

### `DatePickerDay`, `DatePickerDayToday`, `DatePickerDaySelected`, `DatePickerDayOutsideMonth`

| Parameter | | Default |
| --- | --- | --- |
| `day` | required |  |

These 4 have one structure; only their stylesheets, above, differ.

```yaml
params: [day]
id: root
kind: Container
children:
  - id: label
    kind: Text
    text:
      content: "{{ day }}"
      typography_role: body_large
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
  - id: d7
    component: DatePickerDaySelected
    with: {day: "7"}
```

In Python:

```python
from tesserae.widgets import date_picker_day

day = date_picker_day(app.window, 7, selected=True)
```

## Changing its look

To restyle a component in your whole app, put a stylesheet of the same name next to your views. Its rules go over the built-in ones, field by field, and the rest is kept:

```yaml
# DatePickerDay_Stylesheet.yaml, next to your views
styles:
  - id: root
    style: {background: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
