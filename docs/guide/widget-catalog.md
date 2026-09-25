# Widget Catalog (`tesserae.widgets`)

`tesserae.widgets` is Tesserae's own namespace for `tre`'s full MD3
(Material Design 3) widget catalog -- one Python function per widget,
called **imperatively** against a live `Window`:

```python
from tesserae.widgets import button

save = button(window, "Save", width=120, height=40, variant="filled")
```

Every function here is a **thin, faithful delegate** straight to the
matching `Window.add_*` factory in `tre` itself -- same parameter
names, order, and defaults. This is deliberate, not a placeholder:
`tre`'s own factories already resolve MD3 color/shape/elevation
correctly against the live theme, and some widgets
(`split_button`/`button_group`) have real hover/press
shape-tightening and reflow animation driven by internal `tre` state
(`PaintProperties.button_group_reflow`/`shape`/
`press_interactive_shape`) that no public Python API exposes -- a
from-scratch Python port could only ever reproduce their rest state.
Delegating keeps full fidelity for every widget and gives every
Tesserae app one consistent `tesserae.widgets` surface to import from,
whether or not `tre` happens to implement a given widget as a
composition under the hood.

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
| `switch` | `on=` | `selected=` (read back with `node.get_selected()`) |
| `divider` | `vertical=True` | `orientation="vertical"` |
| `link` | `text` | `content` |
| `dialog` | `text` | `supporting_text` |
| `toolbar` | `tone="vibrant"` | `vibrant=True` |

`slider`'s position is read back as `node.get("value")` (was
`"thumb_position"`). `icon` and `loading_indicator` keep `foreground=`.

One function isn't a pure delegate: `image(window, path, ...)` decodes
the file itself (with Pillow) and calls `tre`'s
`add_image_from_bytes`, so `tre` only ever receives pixels, never a
file path. Its parameters and its `OSError` on a missing or undecodable
file are unchanged.

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
