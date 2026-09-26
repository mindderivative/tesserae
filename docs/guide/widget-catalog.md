# Widget Catalog (`tesserae.widgets`)

`tesserae.widgets` is Tesserae's MD3 (Material Design 3) widget
catalog -- one Python function per widget, called **imperatively**
against a live `Window`. Since M40 and M41 Tesserae draws almost all of
them itself, on `tre`'s building blocks:

```python
from tesserae.widgets import button

save = button(window, "Save", width=120, height=40, variant="filled")
```

**The stateful ones return Tesserae controls (M40).** `checkbox`,
`radio_button`, `switch`, `slider`, `spin_box`, `circular_progress`,
`linear_progress`, `loading_indicator` and `time_picker_dial` build
Tesserae's own MD3 controls (`tesserae.controls`) and return the control,
not a `tre.Node`:

```python
from tesserae.widgets import checkbox

agree = checkbox(window, (0x67, 0x50, 0xA4, 0xFF), 48, 48, theme=app.theme, label="I agree")
agree.checked.get()        # its state is a Signal
agree.on_change(print)     # the user's changes
agree.node                 # the tre node, attached to the window's root
```

**Migrating:** where you read `node.get_checked()` or `get_selected()`,
read `control.checked.get()` or `control.selected.get()`. Where you called
`set_checked(...)`, call `control.checked.set(...)`, and use the control's
`.node` where you used the node. A checkbox, switch or radio button now
toggles itself when clicked, so an `on_click` that toggled it by hand
should go. `spin_box` returns one `SpinBox` rather than
`(field, minus, plus)`. These controls use the `theme=` you pass
(MD3's baseline colours without one), not the window's. See
[Controls](controls.md).

**The composed ones are built from their fragments (M41).**
So far the buttons and actions (`button`, `icon_button`, `fab`,
`extended_fab`, `split_button`, `button_group`) and the containment and
list widgets (`card`, `chip`, `badge`, `divider`, `link`, `icon`,
`list_`, `list_item`, `accordion_header`, `tree_node`) and navigation
(`tabs`, `navigation_rail`, `navigation_drawer`, `toolbar`,
`top_app_bar`, `status_bar`). Each expands the same `*_Component.yaml` a
`component: ButtonFilled` does and builds it with Tesserae's compiler,
so the Python and YAML paths are one definition. It returns a `Widget`:

```python
from tesserae.widgets import button

save = button(window, "Save", 120, 40, variant="filled", theme=app.theme, on_click=viewmodel.save)
save.node              # the root, attached to the window's root
save.part("label")     # a named piece
save.on_click(fn)      # a focusable button: Enter and Space activate it
save.set_theme(theme)
```

A button is a pill unless you pass `corner_radius=`, with MD3's hover,
press and focus feedback in its content's colour. An `icon_button` is a
circle `size` across, and a `fab` is MD3's small (40), default (56) or
large (96) size. Give the icon-only ones `label=` for screen readers. A
`split_button` has `leading` and `trailing` parts, with `on_click` and
`on_menu`, and its facing corners tighten while it's hovered. A
`button_group` has parts `b0`, `b1` and so on, with `on_click(index)`,
and the pressed button reshapes and widens while its neighbours share the
loss.

A `card` gets feedback when given `on_click`. A filter `chip` toggles
`.selected` (a `Signal`) when clicked, and an input chip with
`removable=True` has a close button that calls `on_remove`. A
`list_item` has `headline`, `supporting`, `leading` and `trailing`
parts, and is 56 px tall, or 72 with `supporting_text`. `list_` takes the
items. An `accordion_header` and a branch `tree_node` have `.expanded` (a
`Signal`) and `.on_change(fn)`: a click, Enter or Space toggles them, a
tree node's right and left arrows set it, and the chevron turns. Show the
content yourself, from `.expanded`. `icon` is Tesserae's own; give it
`label=` if it isn't decorative.

`tabs`, `navigation_rail` and `navigation_drawer` have `.selected` (a
`Signal`, an index or `None`) and `.on_change(fn)`, and parts `item0`,
`item1`, and so on. A click or Enter selects. The group is one Tab stop,
and the arrow keys move the selection (left and right for tabs, up and
down for the rail and drawer). The tabs' indicator slides to the new tab.
`navigation_drawer(modal=True)` has the modal drawer's look; to open one
as an overlay, use `tesserae.overlays.NavigationDrawer`. `dialog`,
`snackbar`, `side_sheet(modal=True)`, `menu` and `tooltip` return
overlays with `open()` and `close()`; see [Overlays](overlays.md). A `toolbar` holds your
action icon buttons (add them to `.node`). The `top_app_bar`'s icons are
buttons: `bar.on_click(fn, part="leading")`, `part="trailing0"`, and so
on.

Where you used the node (or tuple) these returned, use `.node` or
`.part(...)`.

**Search (M42).** `search_bar(window, placeholder, width,
leading_icon="search", trailing_icons=None)` is MD3's search bar: its
`placeholder` is hint text, `.query` is a `Signal` of what's typed, and
`.on_query(fn)` hears it. Its parts are `field`, `leading` and
`trailing0`, and so on. `search_view(window, width, height, bar=bar,
results=[(text, fn)])` is the docked results panel, an overlay that
opens below the bar: see [Overlays](overlays.md#each-one).

**Date and time (M42).** `date_picker_day(window, day, selected=,
today=, outside_month=, on_click=)` is MD3's day: a 48 px target with a
40 px circle, filled `primary` when selected and outlined when it's
today. `.selected`, `.today` and `.outside_month` are `Signal`s, and
`on_click(day)` hears a click; arranging the month and choosing a day is
up to your code. `period_selector(window, "AM")` is MD3's AM/PM toggle,
with `.period` a `Signal`, and a click or the arrows switch it.
`time_input_field(window, value, unit="hour")` is MD3's 96×72 time field:
`.value` is a `Signal` shown as two digits, typing sets it when the number
is in range, and the up and down arrows step it and wrap.

**Still `tre`'s, until later in M42:** `node_graph` and `graph_node`. These are thin delegates to the matching
`Window.add_*` factory in `tre`, with the same parameter names, order and
defaults, and they return `tre` nodes themed by the window's theme. M42
rebuilds them too.

## When to use this vs. a declarative fragment

| | `tesserae.widgets` (this page) | [`component:` fragments](component-fragments.md) |
| --- | --- | --- |
| Called from | Python (`ViewModel`, setup code) | `*_View.yaml` |
| Style | Imperative -- `button(window, ...)` | Declarative -- `component: ButtonFilled` |
| Coverage | All ~68 real MD3 widgets, full fidelity | 67 of ~68 (see fragment page for the 3 real gaps) |
| Runtime data | Trivial -- plain function args | Only what's known at load time (`repeat:` is not reactive) |

Reach for a fragment first when a widget is part of a static
`*_View.yaml` layout -- it keeps the whole screen declarative. Reach
for `tesserae.widgets` when a widget needs to be created dynamically
from Python (a widget count decided at runtime, one only some code path
constructs) or when it's one of the 3 fragment gaps below.

## Full catalog, by category

| Category | Functions |
| --- | --- |
| Buttons & Actions | `button`, `icon_button`, `fab`, `extended_fab`, `split_button`, `button_group` |
| Selection & Input | `checkbox`, `radio_button`, `switch`, `slider`, `spin_box` |
| Cards/Lists/Chips/Structural | `card`, `list_`, `list_item`, `chip`, `badge`, `divider`, `link`, `accordion_header`, `tree_node` |
| Navigation & Shell | `tabs`, `toolbar`, `top_app_bar`, `status_bar`, `navigation_rail`, `navigation_drawer` |
| Overlays | `dialog`, `snackbar`, `tooltip`, `menu`, `menu_item`, `side_sheet` |
| Search | `search_bar`, `search_view` |
| Progress & Status | `circular_progress`, `linear_progress`, `loading_indicator` |
| Media & Graphics | `image`, `video`, `node_graph`, `graph_node`, `icon` |
| Date & Time | `date_picker_day`, `period_selector`, `time_picker_dial` |

Every function's own docstring (in `src/tesserae/widgets/`) states its
real parameter list -- one module per category (`buttons.py`,
`selection.py`, `structural.py`, `navigation.py`, `overlays.py`,
`search.py`, `progress.py`, `media.py`, `date_time.py`), matching the
category split above. Import everything from the top-level
`tesserae.widgets` package; the per-category module a function lives in
is an implementation detail, not part of the stable import path.

```python
from tesserae.widgets import card, checkbox, tabs
```

### Renamed with `tre` 0.3.3

These arguments were renamed to match `tre` 0.3.3's own names. Old
names now raise `TypeError`:

| Function | Before | Now |
| --- | --- | --- |
| `switch` | `on=` | `selected=` (read back with `control.selected.get()` since M40) |
| `divider` | `vertical=True` | `orientation="vertical"` |
| `link` | `text` | `content` |
| `dialog` | `text` | `supporting_text` |
| `toolbar` | `tone="vibrant"` | `vibrant=True` |

`slider`'s position is `control.value.get()` since M40 (it was
`node.get("value")`, and `"thumb_position"` before that). `icon` and
`loading_indicator` keep `foreground=`.

**Images and video (M42).** `image(window, path, width, height,
fit="fill", label=None)` decodes the file itself (with Pillow) and builds
an `image` node from the pixels, so `tre` never receives a file path. A
missing or undecodable file is an `OSError`, and an image is decorative
unless given `label=`. `video(window, width, height)` is a blank surface
until you call `video.frame(rgba, width, height)` with RGBA bytes; frames
can change size. Both return `Widget`s.

## `list_`/`list_item` vs. `repeat:`

`list_` in this catalog takes pre-built `Node`s and does pure layout
composition -- there's no `NodeKind::List` primitive underneath at
all. This is exactly why the [`repeat:`](component-fragments.md#repeating-a-fragment-repeat)
macro construct exists: a static list of `ListItem` fragments is
already fully expressible as a plain `Container` with N children, so
`repeat:` only needed to add the "don't hand-duplicate N blocks" part,
not a new list primitive.

## `video` and `graph_node`: real, structural fragment gaps

Both `video` and `graph_node` (plus `node_graph`, which composes
`graph_node`s) are **not** available as declarative fragments -- see
[Component Fragments](component-fragments.md#what-has-no-fragment-yet-and-why)
for why. Use these two functions directly from `tesserae.widgets`
whenever a screen needs them; there's no declarative equivalent to
reach for instead.
