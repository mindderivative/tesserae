# Widgets in Python

`tesserae.widgets` builds MD3 (Material Design 3) widgets from Python: one
function per widget, called against a live `Window`. Use it when a widget
is created at run time. For a widget in a static view, write
[`component:`](component-fragments.md) in the YAML instead.

Every widget, with its look and its YAML, has a page under
[Components](../components/index.md). Every function's signature is in the
[Python API](../api/python.md).

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

Most widgets are composed: each expands the same `*_Component.yaml`
fragment that a `component: ButtonFilled` does, and builds it with
Tesserae's compiler, so the Python and YAML paths share one definition.
They return a `Widget`:

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

| | `tesserae.widgets` | [`component:`](component-fragments.md) |
| --- | --- | --- |
| Called from | Python (a ViewModel, setup code) | a `*_View.yaml` |
| Style | imperative: `button(window, ...)` | declarative: `component: ButtonFilled` |
| Runtime data | plain function arguments | what is known when the view loads |

Reach for a fragment first when a widget is part of a static layout: it
keeps the screen declarative. Reach for `tesserae.widgets` when the widget
is made at run time, such as a count decided by data, or one that only
some code path builds.

## `list_` and `repeat:`

`list_` takes pre-built `Node`s and lays them out. In a view, a list of
`ListItem` fragments is a container with N children, and
[`repeat:`](component-fragments.md#repeating-a-fragment-repeat) saves
writing N blocks by hand. For a list that changes while the app runs, use
a [Repeater](repeater.md).

## Layout

For rows, columns, wrapping, exact placement and a scrolling `ScrollView`,
see [Layout](layout.md).
