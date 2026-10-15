# Slider

*Selection and input*

## In Material Design 3

A slider lets the user pick a value from a range by dragging a handle, or with the keyboard.

## In Tesserae

`widget: Slider`, a Tesserae control: a 4 pixel track, a 20 pixel handle and a 40 pixel state layer in a 48 pixel target. A bound `value` follows the drag, not only its end.
With a `step` the value snaps to multiples of it from `min`, the keys move by it (else by a hundredth of the range), and `ticks: true` puts a mark at each step: a discrete
slider (without a `step` there is nothing to mark). `value_indicator: true` shows a bubble with the value over the handle while it is dragged or has the keyboard focus.
A `max` that is not above `min`, or a `step` that is not positive, is an error.

Three looks go beyond the standard one. `vertical: true` stands it up: the bottom is `min`, `style.height` is its length and `style.width` the touch target's. `size`
(`xs`, `s`, `m`, `l` or `xl`) is the Expressive form: a track 16, 24, 40, 56 or 96 pixels thick, in two pieces with a 6 pixel gap either side of a thin 4 pixel handle that
stands across it. `icon` insets a glyph at the start of the track (it needs a `size` of `s` or larger) in the colour of what it lies on.

Events: `on_input` while it is dragged (every step), `on_change` once it is let go, and after each key. Dragging captures the pointer, and a press anywhere on the track
sets the value there. The arrow keys step it (all four, whichever way it lies), Page Up and Down move by ten steps, Home and End go to the ends, and a screen reader can
increment, decrement and set it. The colour is `style.foreground` and the length is `style.width` (`style.height` when `vertical`); a slider laid out longer or shorter than
it was built, in a flexible row, takes the room it was given.

### Range slider

`widget: RangeSlider` picks two values, a least and a most, with two handles. It takes the slider's `min`, `max`, `step`, `ticks`, `value_indicator`,
`vertical`, `size`, `icon`, `label` and `disabled`, and, in place of `value`, two two-way numbers: `low`, the least of the two, and `high`, the most. A `high` below
`low` is read as `low`.

The handles never cross: a drag stops at the other handle. Each handle is its own stop for Tab, has its own state layer and focus ring and, for a
screen reader, is a slider of its own (named from `label`: "Price, minimum" and "Price, maximum"; its reach is up to or down from the other handle).
The arrow, Page Up and Down keys move the handle that has the focus; Home and End take it to the end of what it may reach. A press on the track moves the
nearer handle there, and a drag keeps hold of the handle it began on. The track between the handles is `primary`; with a `size` it is three pieces, a gap
from each handle. `on_input` and `on_change` fire as for a slider; read the values from the bound `low` and `high`.

## How it is built

### `Slider`

Picks a value between `min` and `max` by dragging.

| Property | Type | Default | Meaning |
| --- | --- | --- | --- |
| `value` | `float` |  | From `min` to `max`; a bound Signal follows the drag. Two-way. |
| `min` | `float` |  |  |
| `max` | `float` | `1.0` |  |
| `step` | `float` |  | Snap to multiples of this from `min`; the keys move by it. |
| `ticks` | `bool` |  | A mark at each step (needs `step`): a discrete slider. |
| `value_indicator` | `bool` |  | A bubble with the value over the handle while it is dragged or has the keyboard. |
| `vertical` | `bool` |  | Stood up: the bottom is `min`; `style.height` is its length and `style.width` the touch target's. |
| `size` | `xs` or `s` or `m` or `l` or `xl` |  | MD3 Expressive's size: a thicker track in two pieces and a thin 4 px handle (empty: the standard 4 px track and 20 px handle). |
| `icon` | `str` |  | An icon inset at the start of the track (needs a `size` of `s` or larger). |
| `label` | `str` |  | What a screen reader calls it. |
| `disabled` | `bool` |  |  |

Its `style:` also takes `foreground`.

### `RangeSlider`

Picks two values, a least and a most, between `min` and `max` by dragging two handles.

| Property | Type | Default | Meaning |
| --- | --- | --- | --- |
| `low` | `float` |  | The least of the two values; a bound Signal follows the drag. Two-way. |
| `high` | `float` | `1.0` | The most of the two values; it is never below `low`. Two-way. |
| `min` | `float` |  |  |
| `max` | `float` | `1.0` |  |
| `step` | `float` |  | Snap to multiples of this from `min`; the keys move by it. |
| `ticks` | `bool` |  | A mark at each step (needs `step`): a discrete slider. |
| `value_indicator` | `bool` |  | A bubble with the value over a handle while it is dragged or has the keyboard. |
| `vertical` | `bool` |  | Stood up: the bottom is `min`; `style.height` is its length and `style.width` the touch target's. |
| `size` | `xs` or `s` or `m` or `l` or `xl` |  | MD3 Expressive's size: a thicker track in three pieces and thin 4 px handles (empty: the standard 4 px track and 20 px handles). |
| `icon` | `str` |  | An icon inset at the start of the track (needs a `size` of `s` or larger). |
| `label` | `str` |  | What a screen reader calls it; the handles are 'minimum' and 'maximum' of it. |
| `disabled` | `bool` |  |  |

Its `style:` also takes `foreground`.

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

## Using it in Python

```python
from tesserae.widgets import slider

volume = slider(app.window, (0xFF, 0xFF, 0xFF, 0xFF), 240, 44, value=0.5)
volume.on_change(print)
```

## See also

- [Controls](../guide/controls.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
