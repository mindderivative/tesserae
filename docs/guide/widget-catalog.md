# Widgets in Python

`tesserae.widgets` builds MD3 (Material Design 3) widgets from Python: one
function per widget, called against a live `Window`. Use it when a widget
is created at run time. For a widget in a view, write `widget: Button` (or
any other [component view](component-fragments.md)) in the YAML instead.

Every widget, with its look and its YAML, has a page under
[Components](../components/index.md). Every function's signature is in the
[Python API](../api/python.md).

The YAML and Python forms are separate. `widget: Button` in a view is the
view Tesserae ships (`Button_View.yaml`), with its properties (`label`,
`variant`, `size`, ...); `button(window, ...)` builds the same Material 3
button from Tesserae's own definition for Python, with the arguments of the
function. A `Button_View.yaml` of your own changes the first, not the
second.

```python
from tesserae.widgets import button

save = button(app.window, "Save", width=120, height=40, variant="filled")
```

## Theme following

On an `App`'s window (`app.window`), a widget made without `theme=` takes
the app's theme and follows it, light and dark included. `theme=` pins it
to a theme. On a window no `App` owns, a widget uses MD3's baseline
colours. See [Themes](../themes/index.md).

## The Widget object

Most widgets are composed: each is built from Tesserae's definition of
that component, a tree of ordinary nodes with named parts. They return a
`Widget`:

```python
from tesserae.widgets import button

save = button(app.window, "Save", 120, 40, variant="filled", on_click=viewmodel.save)
save.node              # the root, attached to the window's root
save.part("label")     # a named piece of it
save.on_click(fn)      # a focusable button: Enter and Space activate it
save.set_theme(theme)  # re-theme it
save.destroy()         # take it down
```

- `.node` is the root `Node`; add your own children to it.
- `.part(name)` is one named piece (`label`, `leading`, `item0`, ...). Each
  widget's page lists its parts.
- `.on_click(fn, part=...)` makes a part clickable and focusable.
- Give an icon-only widget `label=` for screen readers.

Where a widget has state, it is a `Signal` on the widget: a filter chip's
`.selected`, an accordion header's `.expanded`, a tab bar's `.selected`
and `.on_change(fn)`, a search bar's `.query`. Each widget's page says
which.

## Controls

`checkbox`, `radio_button`, `switch`, `slider`, `spin_box`,
`circular_progress`, `linear_progress`, `loading_indicator` and
`time_picker_dial` return a Tesserae control (`tesserae.controls`) rather
than a `Widget`. Its state is a `Signal`:

```python
from tesserae.widgets import checkbox

agree = checkbox(app.window, (0x67, 0x50, 0xA4, 0xFF), 48, 48, label="I agree")
agree.checked.get()        # its state is a Signal
agree.on_change(print)     # the user's changes
agree.node                 # the node, attached to the window's root
```

A checkbox, switch or radio button toggles itself when clicked. A control
uses the app's theme and follows it, or the `theme=` you pass. See
[Controls](controls.md).

## Plain text

`text(window, content, typography_role="body_medium", color="on_surface",
width=None)` is a line of text in one of the theme's type roles and
colours. `.content` is a `Signal`; setting it re-measures the text.

```python
from tesserae.widgets import text

title = text(app.window, "Notes", typography_role="title_large")
count = text(app.window, "0 notes", color="on_surface_variant")
count.content.set("3 notes")
```

## Overlays

`dialog`, `snackbar`, `side_sheet`, `menu`, `tooltip` and `popover` return
overlays with `open()` and `close()`. See [Overlays](overlays.md).

## Code or YAML

| | `tesserae.widgets` | [`widget: Name`](component-fragments.md) |
| --- | --- | --- |
| Called from | Python (a ViewModel, setup code) | a `*_View.yaml` |
| Style | imperative: `button(window, ...)` | declarative: `widget: Button` |
| Runtime data | plain function arguments | any expression, and it follows the data |

Reach for a view first when a widget is part of a layout: it keeps the
screen declarative, and `for:` and `if:` already make widgets from data and
add or remove them as it changes. Reach for `tesserae.widgets` when the
widget has to be made by code, such as one that only some code path
builds, or one added to a window that is not built from a view.

## `list_` and `for:`

`list_` takes pre-built `Node`s and lays them out. In a view, a list is a
container of `ListItem` calls, and
[`for:`](component-fragments.md#repeating-a-view-for) writes the one call
once and builds a row for each element of the data, adding and removing
rows as the data changes.

## Layout

For rows, columns, wrapping, exact placement and a scrolling `ScrollView`,
see [Layout](layout.md).
