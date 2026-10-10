# Slider

*Selection and input*

## In Material Design 3

A slider lets the user pick a value from a range by dragging a handle, or with the keyboard.

## In Tesserae

`widget: Slider`, a Tesserae control: a 4 pixel track, a 20 pixel handle and a 40 pixel state layer in a 48 pixel target.

| Property | Type | Meaning |
| --- | --- | --- |
| `value` | number, two-way | from `min` to `max`; a bound Signal follows the drag, not only its end |
| `min`, `max` | numbers | the range; 0 to 1 by default |
| `step` | number | snap to multiples of it from `min`; the keys move by it (else by a hundredth of the range) |
| `ticks` | true or false | a mark at each step (needs `step`): a discrete slider |
| `value_indicator` | true or false | a bubble with the value over the handle while it is dragged or has the keyboard |
| `vertical` | true or false | stood up: the bottom is `min`, `style.height` is its length and `style.width` the touch target's; up and down arrows step it |
| `size` | `xs`, `s`, `m`, `l`, `xl` | MD3 Expressive: a track 16, 24, 40, 56 or 96 px thick, in two pieces with a 6 px gap, and a thin 4 px handle across it (empty: the standard 4 px track and 20 px handle) |
| `icon` | an icon name | a glyph inset at the start of the track (needs a `size` of `s` or larger); the colour of what it lies on |
| `label` | text | what a screen reader calls it |
| `disabled` | true or false | dimmed and does not move |

Events: `on_input` while it is dragged (every step), `on_change` once it is let go and after each key. Dragging captures the pointer; the arrow keys
step it, Page Up and Down move by ten steps, Home and End go to the ends, and a screen reader can increment, decrement and set it. The colour is
`style.foreground` and the length is `style.width` (`style.height` when `vertical`).

### Range slider

`widget: RangeSlider` picks two values, a least and a most, with two handles. It takes the slider's `min`, `max`, `step`, `ticks`, `value_indicator`,
`vertical`, `size`, `icon`, `label` and `disabled`, and, in place of `value`:

| Property | Type | Meaning |
| --- | --- | --- |
| `low` | number, two-way | the least of the two; a bound Signal follows the drag |
| `high` | number, two-way | the most of the two; never below `low` (a `high` below it is read as `low`) |

The handles never cross: a drag stops at the other handle. Each handle is its own stop for Tab, has its own state layer and focus ring and, for a
screen reader, is a slider of its own (named from `label`: "Price, minimum" and "Price, maximum"; its reach is up to or down from the other handle).
The arrow, Page Up and Down keys move the handle that has the focus; Home and End take it to the end of what it may reach. A press on the track moves the
nearer handle there, and a drag keeps hold of the handle it began on. The track between the handles is `primary`; with a `size` it is three pieces, a gap
from each handle. `on_input` and `on_change` fire as for a slider; read the values from the bound `low` and `high`.

`widget: Slider` is the view-language form (see [The View Language](../guide/view-language.md)); the fragment below is the older `component:` form, which keeps working.

| Fragment | What it is | Stylesheet |
| --- | --- | --- |
| `component: Slider` | A slider: picks a value from a range by dragging. | [`Slider_Stylesheet.yaml`](../stylesheets/sliders/slider.md) |

## How it is built

Each fragment is a `*_Component.yaml`: its structure, and the parameters it takes. Its look is in its stylesheet, linked under each one.

### `Slider`

A slider: picks a value from a range by dragging. Its look: [`Slider_Stylesheet.yaml`](../stylesheets/sliders/slider.md).

| Parameter | | Default |
| --- | --- | --- |
| `background` | required |  |
| `width` | required |  |
| `height` | required |  |
| `value` | required |  |

```yaml
params: [background, width, height, value]
id: root
kind: Slider
value: "{{ value }}"
```

## Using it

```yaml
name: player
widget: Container
style: {flex_direction: vertical, gap: 16, width: 280, height: 160, padding: 16}
children:
  - {widget: Slider, value: "{{ volume }}", min: 0, max: 100, label: Volume, value_indicator: true, style: {width: 240}}
  - {widget: Slider, value: "{{ stars }}", min: 1, max: 5, step: 1, ticks: true, style: {width: 240}}
  - {widget: RangeSlider, low: "{{ cheapest }}", high: "{{ dearest }}", min: 0, max: 500, step: 10, label: Price, style: {width: 240}}
```

## Using the fragment

In a view:

```yaml
# Home_View.yaml
id: root
kind: Container
children:
  - id: volume
    component: Slider
    with: {background: surface, width: 240, height: 44, value: 0.5}
```

In Python:

```python
from tesserae.widgets import slider

volume = slider(app.window, (0xFF, 0xFF, 0xFF, 0xFF), 240, 44, value=0.5)
volume.on_change(print)
```

## Changing its look

To restyle a component in your whole app, put a stylesheet of the same name next to your views. Its rules go over the built-in ones, field by field, and the rest is kept:

```yaml
# Slider_Stylesheet.yaml, next to your views
styles:
  - id: root
    style: {background: tertiary}
```

See [Component stylesheets](../stylesheets/index.md).

## See also

- [Controls](../guide/controls.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
