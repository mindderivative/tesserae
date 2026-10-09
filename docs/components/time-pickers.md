# Time picker

*Selection and input*

## In Material Design 3

A time picker lets the user choose an hour and a minute on a dial, with an AM/PM selector in a 12-hour
format.

## In Tesserae

Four pieces. `TimePickerDial` is a Tesserae control (`widget: TimePickerDial`): `hour`, `minute` and `mode` (`hour` or `minute`; letting go on an hour moves on to the
minutes unless `auto_advance` is off). `PeriodSelector` is a view: two halves, `period` `AM` or `PM` (two-way), with an `on_change` handler for after a choice.
`TimeInput` is a view: an hour field, a colon, a minute field and, in 12-hour time, a period selector, where `hour` and `minute` are two-way and a number that does
not fit is left out (the fields are filled from the time when they appear). `TimePicker` is the dialog of Material 3.

| Property of `TimePicker` | Type | Meaning |
| --- | --- | --- |
| `open` | true or false; two-way | whether it is showing; Escape and a press on the scrim close it |
| `hour`, `minute` | whole numbers; two-way | the time, 0 to 23; changed only when OK is pressed |
| `twelve` | true or false | 12-hour time with a dial and a period selector; off, only the typed fields |
| `title`, `on_ok` | text, a handler | the small heading; called after OK |

The picker shows the time as an hour and a minute you press to choose which the dial sets, the period selector, the 256 pixel dial, a keyboard button that
swaps the dial for the typed fields (and back), and Cancel and OK. Reopening it starts from the time as it then is. Not built: a 24-hour dial with an inner ring,
limits on the times that can be chosen, and the times as a locale writes them.

`widget: TimePicker` is the view-language form (see [The View Language](../guide/view-language.md)); the fragment below is the older `component:` form, which keeps working.

| Fragment | What it is | Stylesheet |
| --- | --- | --- |
| `component: TimePickerDial` | A time picker dial: a clock face for picking the hour, then the minute. | [`TimePickerDial_Stylesheet.yaml`](../stylesheets/time-pickers/time-picker-dial.md) |
| `component: PeriodSelectorAM` | A time picker's AM / PM selector, with AM selected. | [`PeriodSelectorAM_Stylesheet.yaml`](../stylesheets/time-pickers/period-selector-am.md) |
| `component: PeriodSelectorPM` | A time picker's AM / PM selector, with PM selected. | [`PeriodSelectorPM_Stylesheet.yaml`](../stylesheets/time-pickers/period-selector-pm.md) |

## How it is built

Each fragment is a `*_Component.yaml`: its structure, and the parameters it takes. Its look is in its stylesheet, linked under each one.

### `TimePickerDial`

A time picker dial: a clock face for picking the hour, then the minute. Its look: [`TimePickerDial_Stylesheet.yaml`](../stylesheets/time-pickers/time-picker-dial.md).

| Parameter | | Default |
| --- | --- | --- |
| `size` | required |  |
| `hour` | required |  |
| `minute` | required |  |

```yaml
params: [size, hour, minute]
id: root
kind: TimePickerDial
hour: "{{ hour }}"
minute: "{{ minute }}"
```

### `PeriodSelectorAM`, `PeriodSelectorPM`

It takes no parameters.

These 2 have one structure; only their stylesheets, above, differ.

```yaml
id: root
kind: Container
children:
  - id: am
    kind: Container
    children:
      - id: am_label
        kind: Text
        text: {content: AM, typography_role: label_large, text_align: center}
  - id: pm
    kind: Container
    children:
      - id: pm_label
        kind: Text
        text: {content: PM, typography_role: label_large, text_align: center}
```

## Using it

```yaml
name: alarm
widget: Container
style: {width: 480, height: 520}
children:
  - widget: TimePicker
    open: "{{ choosing }}"
    hour: "{{ alarm_hour }}"
    minute: "{{ alarm_minute }}"
    on_ok: alarm_set
  - widget: TimeInput
    hour: "{{ alarm_hour }}"
    minute: "{{ alarm_minute }}"
  - {widget: PeriodSelector, period: "{{ half }}"}
```

## Using it

In Python:

```python
from tesserae.widgets import time_picker_dial

dial = time_picker_dial(app.window, hour=9, minute=30)
```

## Changing its look

To restyle a component in your whole app, put a stylesheet of the same name next to your views. Its rules go over the built-in ones, field by field, and the rest is kept:

```yaml
# TimePickerDial_Stylesheet.yaml, next to your views
styles:
  - id: root
    style: {width: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Controls](../guide/controls.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
