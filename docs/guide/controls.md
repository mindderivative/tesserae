# Controls

Tesserae draws MD3's stateful controls itself (M40), since `tre` 0.3.5
removes its own: the checkbox, radio button, switch, slider, spin box,
linear and circular progress, loading indicator and time picker dial.
They work with a mouse, a keyboard and a screen reader, and follow the
theme, including light and dark.

## In a view

In a `*_View.yaml`, the nine control kinds are controls (`SpinBox` since M58):

```yaml
- id: agree
  kind: Checkbox
  checked: false
  style: {}
  bindings: {checked: "{{ agreed.get() }}"}
  two_way: checked
  handlers: {on_change: "agreement_changed"}
```

- **State:** bind `checked` (Checkbox), `selected` (RadioButton, Switch),
  `value` (Slider, SpinBox, the progress kinds), `hour` and `minute`
  (TimePickerDial), and `disabled` (any). `two_way:` writes the user's
  changes back to the `Signal`.
- **`on_change`** runs for changes the user makes, never for ones your
  code or a binding makes.
- **A `SpinBox`** takes `value:`, `min:`, `max:` and `step:` (a bound
  `value` is kept between the bounds), and its `a11y:` label goes to its
  text field. It's sized by MD3, two 40 px buttons around a 64 px field,
  not by `width`/`height`.
- **Size:** `style: {width, height}` sets the control's touch target;
  it's MD3's 48 px when not given. A slider's `width` is its track's
  length, a dial's is its face, and a progress bar's is its track.
- **Colour:** `background` replaces `primary` for the selected parts;
  for the indicators, `foreground` does.
- **Radio groups:** radio buttons with the same `group:` name exclude
  each other, and the group is a single Tab stop whose arrow keys move
  the selection.
- `view.control("agree")` returns the control, and `view.node("agree")`
  its node.

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
`Signal`s, `.disabled`, `on_change(fn)` (which returns a function that
stops it), `set_theme(theme)` and `destroy()`. On an `App`'s window, a
control made without `theme=` takes the app's theme and follows it
through `set_dark`, the OS switching light and dark, and
`set_theme_specs` (M50). Give `theme=` a `tesserae.Theme` to pin it to
that theme instead. On a window no `App` owns, a control without one uses
MD3's baseline colours. `tesserae.widgets`' `checkbox`, `slider` and
so on build these too, attached to the window's root.

| Control | State | Input |
| --- | --- | --- |
| `Checkbox` | `checked` | click, Space, Enter toggle it |
| `RadioButton` | `selected` | a click selects it; with `group=RadioGroup()`, the arrow keys move the selection |
| `Switch` | `selected` | click, Space, Enter toggle it; the handle grows while pressed |
| `Slider(value=, min=, max=, step=, width=)` | `value` | press or drag (the pointer is captured); arrows, Page Up/Down, Home/End; `on_change` once a drag ends |
| `SpinBox(value=, min=, max=, step=)` | `value` | − and + buttons, the up and down arrows, typing |
| `TimePickerDial(hour=, minute=, mode=)` | `hour`, `minute`, `mode` | press or drag points the hand; the hour snaps to 12, the minute to 5; releasing on the hour moves on to minutes |
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

## Not yet covered

- Checkbox's indeterminate state, error colours, and the switch's icons
  aren't built. The linear indicator's indeterminate sweep is one bar,
  not MD3's two.
