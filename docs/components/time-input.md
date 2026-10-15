# Time input

*Selection and input*

## In Material Design 3

A time input field is a numeric field for the hour or the minute, used in the time picker's keyboard mode.

## In Tesserae

`widget: TimeInput` is a view Tesserae ships (`TimeInput_View.yaml`): two outlined `TextField`s, 96 pixels wide, for the hour and the minute, a colon between them and, in
12-hour time, a `PeriodSelector`. `hour` (0 to 23) and `minute` are two-way. The fields take two digits (`mask: "##"`); a number that does not fit (1 to 12 in 12-hour
time, 0 to 23 otherwise, and 0 to 59 for the minute) is left out until it does. The fields are filled from the time when the input appears and follow what is typed after
that. The time picker shows it in its keyboard mode.

In Python, `time_input_field` is one numeric field of Material 3's: 96 by 72 pixels, a centred two-digit numeral, `unit` `hour` or `minute`. Its `value` is a `Signal`;
typing a number in range sets it, and the up and down arrows (and a screen reader's increment and decrement) step it, wrapping.

## How it is built

A view Tesserae ships is a `<Name>_View.yaml` (what it takes and what it is made of) with a `<Name>_Stylesheet.yaml` (how it looks). Use it by name: `widget: TimeInput`. A file of the same name in your project replaces it.

### `TimeInput`

The keyboard form of a time picker (Material 3's "input mode"): an hour field, a colon, a minute field and, in 12-hour time, an AM / PM selector. `hour` (0 to 23) and `minute` (0 to 59) are two-way; the fields take the digits, and a number that does not fit is left out until it does. The fields are filled from `hour` and `minute` when the input appears, and follow what is typed after that. `twelve` shows 1 to 12 and the period selector, otherwise the hour is 0 to 23.

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `hour` | `int` | `0` | 0 to 23. Two-way: give it a bare reference and the view writes it back. |
| `minute` | `int` | `0` | 0 to 59. Two-way: give it a bare reference and the view writes it back. |
| `twelve` | `bool` | `true` | 12-hour time with an AM / PM selector. |
| `disabled` | `bool` | `false` | Dimmed and not editable. |

Its parts, by name (a stylesheet rule's `part:` or `name:` addresses one): `hour_field` (TextField), `colon` (Text), `minute_field` (TextField), `period_selector` (PeriodSelector).

Its look is in [`TimeInput_Stylesheet.yaml`](../stylesheets/time-input/time-input.md).

## Using it

```yaml
name: alarm_time
widget: Container
style: {width: 360, height: 120, padding: 16}
children:
  - {widget: TimeInput, hour: "{{ alarm_hour }}", minute: "{{ alarm_minute }}", twelve: false}
```

## Using it in Python

```python
from tesserae.widgets import time_input_field

hour = time_input_field(app.window, 9, unit="hour")
```

## Changing its look

To restyle it in your whole app, write rules for it in your app's stylesheet, or put a stylesheet of the same name next to your views. A rule names the widget and may narrow it by the properties it declares, a part and a state; the most specific rule wins, and a node's own `style:` beats every rule:

```yaml
# TimeInput_Stylesheet.yaml, or any stylesheet your app loads
styles:
  - widget: TimeInput
    part: colon
    style: {foreground: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
