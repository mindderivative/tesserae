# Controls

Tesserae draws MD3's stateful controls itself: the checkbox, radio button, switch, slider, range slider, spin box,
linear and circular progress, loading indicator and time picker dial.
They work with a mouse, a keyboard and a screen reader, and follow the
theme, including light and dark ([Themes](../themes/index.md)). Each control
also has a page under [Components](../components/index.md), and the Python
signatures are in the [Python API](../api/python.md).

## In a view

In a `*_View.yaml`, these widgets are controls: `Checkbox`, `RadioButton`, `Switch`, `Slider`, `RangeSlider`, `SpinBox`,
`LinearProgress`, `CircularProgress`, `LoadingIndicator` and `TimePickerDial`.

```yaml
widget: Container
style: {flex_direction: vertical, gap: 8, width: 320, padding: 16}
children:
  - widget: Checkbox
    name: agree
    label: I agree
    checked: "{{ agreed }}"                 # one bare reference: the user's change is written back to `agreed`
    handlers: {on_change: agreement_changed}
  - {widget: Switch, name: dark, selected: "{{ dark }}"}
  - {widget: Slider, name: volume, value: "{{ volume }}", min: 0, max: 1, step: 0.1, style: {width: 200}}
  - {widget: SpinBox, name: quantity, value: "{{ quantity }}", min: 1, max: 9}
  - {widget: LinearProgress, name: loaded, value: "{{ loaded }}", style: {width: 200}}
```

- **State:** `checked` (Checkbox), `selected` (RadioButton, Switch), `value` (Slider, SpinBox, the progress widgets), `low` and `high`
  (RangeSlider), `hour`, `minute` and `mode` (TimePickerDial), and `disabled` (on every control that has one: not the progress widgets or the dial). Given one bare reference to a
  Signal or a `state:` name, the property is two-way: the user's changes are written back. Any other expression is one-way.
- **`on_change`** runs for changes the user makes, never for ones your
  code or a binding makes.
- **`label`** on a Checkbox, RadioButton or Switch is text beside it that is part of what you press, and what a screen reader calls it. On the
  others it is what a screen reader calls the control (`a11y: {label: ...}` says the same on any node).
- **A `Checkbox`** with `checked: null` is neither on nor off (a parent of some checked children). `error: true` draws a Checkbox or RadioButton in the error
  colours. A `Switch` with `icons: true` shows a check on its handle when on and a cross when off.
- **A `Slider`** takes `min`, `max` (0 and 1 when left out), `step`, `ticks: true` (a mark at each step, which needs `step`), `value_indicator: true` (a
  bubble with the value while dragged), `vertical: true` (the bottom is `min`; `height` is its length and `width` the touch target's), `size` (`xs`, `s`, `m`, `l`, `xl`:
  MD3 Expressive's thicker track and thin handle) and, from size `s` up, an `icon` at the start of the track. A `RangeSlider` is a slider with two handles,
  `low` and `high`, and the same keys.
- **A `SpinBox`** takes `value`, `min`, `max` and `step`, and `decimals` (how many places show), `prefix`, `suffix` and `wrap` (a step past one bound lands on the other,
  which needs both). A bound `value` is shown kept between the bounds. Its `a11y:` label goes to its text field. It is sized by MD3, two 40 px
  buttons around a 64 px field (152 px wide), not by `width`; like any box it is stretched across the layout, so give its parent `align_content: left` (or
  itself `align_self`) to keep that size. Holding a button repeats the step; Page Up and Page Down step by ten.
- **The progress widgets** take `value` from 0 to 1, or nothing (`value: null`) for a wait with no end. `track` is the colour role behind the indicator, `thickness`
  the bar's height or the ring's width in pixels. A `LinearProgress` also has `buffer` (how much has loaded, 0 to 1), `stop_indicator`, `wavy` and
  `two_bar` (an endless wait sweeps as two bars); a `CircularProgress` has `wavy`; a `LoadingIndicator` has `contained`.
- **A `TimePickerDial`** has `hour` (0 to 23), `minute` (0 to 59), `mode` (`hour` or `minute`, which hand the face shows and sets) and `auto_advance`
  (`true`: letting go in hour mode moves on to the minutes).
- **Size:** `style: {width, height}` sets the control's touch target;
  it's MD3's 48 px when not given. A slider's `width` is its track's
  length, a dial's is its face, and a progress bar's is its track.
- **Colour:** `foreground` replaces `primary`, the colour of the selected or active parts.
- **Radio groups:** radio buttons with the same `group:` name exclude
  each other, and the group is a single Tab stop whose arrow keys move
  the selection.
- From Python, `view.control("root.agree")` returns the control, and `view.node("root.agree")`
  its node (a node's id is the path from the root, using its `name`).

## From Python

```python
from tesserae import controls

cb = controls.Checkbox(app.window, checked=True, label="Remember me")  # follows the app's theme
app.window.root.add_child(cb.node)
cb.checked.set(False)            # its state is a Signal
stop = cb.on_change(print)       # the user's changes
cb.disabled.set(True)
```

Every control has `.node` (a `tre` node to put in a tree), its state as
`Signal`s, `set_theme(theme)` and `destroy()`; all but the progress widgets and the loading indicator also have `.disabled` and
`on_change(fn)` (which returns a function that stops it). On an `App`'s window, a
control made without `theme=` takes the app's theme and follows it
through `set_dark`, the OS switching light and dark, and
`set_theme_specs`. Give `theme=` a `tesserae.Theme` to pin it to
that theme instead. On a window no `App` owns, a control without one uses
MD3's baseline colours. `tesserae.widgets`' `checkbox`, `slider` and
so on build these too, attached to the window's root.

| Control | State | Input |
| --- | --- | --- |
| `Checkbox` | `checked` | click, Space, Enter toggle it |
| `RadioButton` | `selected` | a click selects it; with `group=RadioGroup()`, the arrow keys move the selection |
| `Switch` | `selected` | click, Space, Enter toggle it; the handle grows while pressed |
| `Slider(value=, min=, max=, step=, width=)` | `value` | press or drag (the pointer is captured); arrows, Page Up/Down, Home/End; `on_change` once a drag ends |
| `RangeSlider(low=, high=, min=, max=, step=, width=)` | `low`, `high` | the same, for two handles; `high` is never below `low` |
| `SpinBox(value=, min=, max=, step=, decimals=, prefix=, suffix=, wrap=)` | `value` | − and + buttons, the up and down arrows, typing |
| `TimePickerDial(hour=, minute=, mode=, auto_advance=)` | `hour`, `minute`, `mode` | press or drag points the hand; the hour snaps to 12, the minute to 5; releasing on the hour moves on to minutes |
| `LinearProgress(value=, width=)`, `CircularProgress(value=)` | `value`: 0–1, or `None` for indeterminate | none |
| `LoadingIndicator()` | none | none: it morphs forever |

Screen readers hear each control's role, label and state, and can step a
slider, spin box or dial (`a11y_action` increment, decrement and
`set_value`).

A control inside something clickable, such as a checkbox in a clickable
list row or card, takes its own click: the row's handler doesn't run.
A disabled control takes the click too, so nothing happens. See
[nested clickables](interaction.md).

## What they look like

MD3's specification: a checkbox is 18 px, a radio button 20 px, a switch
a 52×32 track, a slider a 4 px track with a 20 px handle, each centred in
its touch target with the state layer, ripple and keyboard focus ring
from [Interaction & Accessibility](interaction.md). Disabled controls use
MD3's disabled colours: content at 38%, containers at 12%. The timing is
MD3's motion tokens.
