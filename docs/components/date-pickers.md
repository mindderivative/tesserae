# Date picker

*Selection and input*

## In Material Design 3

A date picker lets the user pick a date from a month grid. Today is outlined, the chosen day is a filled
circle, and days of the neighbouring months are dimmed.

## In Tesserae

Two views Tesserae ships: `DatePickerDay` (one day, in all its states) and `DatePicker` (the modal dialog).

`DatePicker`'s `open` is two-way (Escape and a press on the scrim close it). `date` is text, `year-month-day` ("2026-10-09", or empty for none), also two-way, and it changes only
when OK is pressed. The days before `earliest` and after `latest` are disabled, `week_starts` is `sunday` (the default) or `monday`, and `on_ok` is called after OK.

The dialog shows the chosen date in `headline_large` and a keyboard button that swaps the grid for a typed field (`####-##-##`; text that is not a real day is left out), the month with arrows between months, the
weekday initials, six weeks of days, and Cancel and OK. Today is outlined, the chosen day is a `primary` circle, and the days of the months either side are faint and move
the view to their month when pressed. The arrow keys move around the grid. A `DatePickerDay` has `day`, `selected`, `today`, `outside` and `disabled`. The dates are worked out with
the expression language's `date_add_days`, `date_weekday`, `days_in_month`, `format_date` and `current_date`, which are there for any view. Not built: a range picker,
a docked picker under a field, month and year selectors, Page Up and Page Down by month, and the names of the months and days in another language.

## How it is built

A view Tesserae ships is a `<Name>_View.yaml` (what it takes and what it is made of) with a `<Name>_Stylesheet.yaml` (how it looks). Use it by name: `widget: DatePicker`. A file of the same name in your project replaces it.

### `DatePicker`

The Material 3 modal date picker: a dialog with the chosen date at the top (and a button that swaps the grid for a typed field), the month with arrows to move between months, the weekday initials and a grid of six weeks of `DatePickerDay`s, and Cancel and OK. `date` is a text `year-month-day` ("2026-10-09", or empty for none) and is two-way, changing only when OK is pressed; `open` is two-way (Escape and a press on the scrim close it). `earliest` and `latest` bound the days that can be chosen; `week_starts` is `sunday` (the default) or `monday`. Today is outlined. Days of the months either side show faintly and choosing one moves to its month. The arrows move the focus around the grid. `on_ok` is called after OK.

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `open` | `bool` | `false` | Whether the picker is showing. Two-way: give it a bare reference and the view writes it back. |
| `date` | `str` |  | The date, year-month-day; set by OK. Two-way: give it a bare reference and the view writes it back. |
| `earliest` | `str` |  | The first date that can be chosen, year-month-day; empty for no limit. |
| `latest` | `str` |  | The last date that can be chosen, year-month-day; empty for no limit. |
| `week_starts` | `sunday` or `monday` | `sunday` | Which day the weeks start on. |
| `title` | `str` | `Select date` | The small heading. |
| `on_ok` | `handler` |  | Called after OK has set the date. |

Its parts, by name (a stylesheet rule's `part:` or `name:` addresses one): `panel` (Container), `heading` (Text), `header` (Container), `chosen` (Text), `header_filler` (Container), `mode_button` (IconButton), `line` (Divider), `month_bar` (Container), `month` (Text), `month_filler` (Container), `previous` (IconButton), `next` (IconButton), `weekdays` (Container), `weekday` (Container), `initial` (Text), `grid` (Container), `day` (DatePickerDay), `entry` (TextField), `footer` (Container), `cancel` (Button), `ok` (Button).

Its look is in [`DatePicker_Stylesheet.yaml`](../stylesheets/date-pickers/date-picker.md).

### `DatePickerDay`

One day of a date picker (Material 3): a 48 pixel target holding a 40 pixel circle with the number in `body_large`. Today is outlined in `primary`; the selected day is a `primary` circle with `on_primary` text; a day outside the month shown is `on_surface_variant`; a disabled day is dimmed. It is pressable; `handlers: {on_click: ...}` on the call is what a press does. One view for the four states the old fragments were.

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `day` | `str` |  | The number shown. |
| `selected` | `bool` | `false` | The chosen day. |
| `today` | `bool` | `false` | Today. |
| `outside` | `bool` | `false` | A day of the month before or after the one shown. |
| `disabled` | `bool` | `false` | Dimmed, and not pressable. |

Its parts, by name (a stylesheet rule's `part:` or `name:` addresses one): `circle` (Container), `number` (Text).

Its look is in [`DatePickerDay_Stylesheet.yaml`](../stylesheets/date-pickers/date-picker-day.md).

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

## Using it in Python

```python
from tesserae.widgets import date_picker_day

day = date_picker_day(app.window, 7, selected=True)
```

## Changing its look

To restyle it in your whole app, write rules for it in your app's stylesheet, or put a stylesheet of the same name next to your views. A rule names the widget and may narrow it by the properties it declares, a part and a state; the most specific rule wins, and a node's own `style:` beats every rule:

```yaml
# DatePicker_Stylesheet.yaml, or any stylesheet your app loads
styles:
  - widget: DatePicker
    part: panel
    style: {background: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
