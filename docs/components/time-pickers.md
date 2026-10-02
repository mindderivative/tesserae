# Time picker

*Selection and input*

## In Material Design 3

A time picker lets the user choose an hour and a minute on a dial, with an AM/PM selector in a 12-hour
format.

## In Tesserae

The dial is a Tesserae control (`TimePickerDial`): drag or use the keys to point the hand at the hour, then
the minute. The AM and PM selectors are two fragments, one for each selected state.

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
        text: {content: AM, typography_role: label_large}
  - id: pm
    kind: Container
    children:
      - id: pm_label
        kind: Text
        text: {content: PM, typography_role: label_large}
```

## Using it

In a view:

```yaml
# Home_View.yaml
id: root
kind: Container
children:
  - id: dial
    component: TimePickerDial
    with: {size: 256, hour: 9, minute: 30}
```

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
