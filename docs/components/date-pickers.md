# Date picker

*Selection and input*

## In Material Design 3

A date picker lets the user pick a date from a month grid. Today is outlined, the chosen day is a filled
circle, and days of the neighbouring months are dimmed.

## In Tesserae

Two views Tesserae ships: `DatePickerDay` (one day, in all its states) and `DatePicker` (the modal dialog).

| Property of `DatePicker` | Type | Meaning |
| --- | --- | --- |
| `open` | true or false; two-way | whether it is showing; Escape and a press on the scrim close it |
| `date` | text `year-month-day`; two-way | the date ("2026-10-09", or empty for none); changed only when OK is pressed |
| `earliest`, `latest` | text `year-month-day` | the days outside them are disabled |
| `week_starts` | `sunday`, `monday` | which day the weeks start on |
| `title`, `on_ok` | text, a handler | the small heading; called after OK |

The dialog shows the chosen date in `headline_large` and a keyboard button that swaps the grid for a typed field (`####-##-##`), the month with arrows between months, the
weekday initials, six weeks of days, and Cancel and OK. Today is outlined, the chosen day is a `primary` circle, and the days of the months either side are faint and move
the view to their month when pressed. The arrow keys move around the grid. A `DatePickerDay` has `day`, `selected`, `today`, `outside` and `disabled`. The dates are worked out with
the expression language's `date_add_days`, `date_weekday`, `days_in_month`, `format_date` and `current_date`, which are there for any view. Not built: a range picker,
a docked picker under a field, month and year selectors, Page Up and Page Down by month, and the names of the months and days in another language.

`widget: DatePicker` is the view-language form (see [The View Language](../guide/view-language.md)); the fragment below is the older `component:` form, which keeps working.

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
      text_align: center
```

## Using it

```yaml
name: booking
widget: Container
style: {width: 480, height: 640}
children:
  - widget: DatePicker
    open: "{{ choosing }}"
    date: "{{ day }}"
    earliest: "2026-01-01"
  - {widget: DatePickerDay, day: "7", selected: true}
```

## Using it

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
