# Overlays

An overlay is a layer over the window: a dialog, a menu, a snackbar, a side sheet. There are two ways to make one.
In a view, a `widget: Overlay` shows its children while its `open` is true. From Python, `tesserae.overlays` has MD3's
dialogs, menus, snackbars, tooltips, popovers, side sheets and modal navigation drawers, ready made, built from Tesserae's
fragments and shown with `tre`'s layers.

## An Overlay in a view

`widget: Overlay` takes no room where it is written. Its children are drawn in a layer over the window while `open` is
true. Bind `open` to a Signal (or a `state:` name) and the layer follows it, and the user's Escape or outside press writes
`false` back:

```yaml
widget: Container
name: page
state: {confirm: false}
style: {flex_direction: vertical, width: 400, height: 300, padding: 20}
children:
  - {widget: Button, name: delete, label: Delete, handlers: {on_click: "confirm = True"}}
  - widget: Overlay
    open: "{{ confirm }}"
    modal: true
    children:
      - widget: Container
        name: dialog
        style: {flex_direction: vertical, gap: 16, padding: 24, width: 312, background: surface_container_high, corner_radius: 28}
        a11y: {role: dialog, label: Delete this file}
        children:
          - {widget: Text, text: "Delete this file?", typography_role: headline_small, style: {foreground: on_surface}}
          - widget: Container
            style: {flex_direction: horizontal, gap: 8, align_content: right}
            children:
              - {widget: Button, name: cancel, label: Cancel, variant: text, handlers: {on_click: "confirm = False"}}
              - {widget: Button, name: confirm_it, label: Delete, variant: text, handlers: {on_click: "confirm = False; delete_file()"}}
```

| Property | What it does |
| --- | --- |
| `open` | Whether it is showing. Two-way. With an `open` that is not a Signal, a layer the user closed stays closed until `open` goes false. |
| `anchor` | The `name` of a node in this view to sit against, or `parent` for the node it is written inside. |
| `placement` | `below` (the default), `above`, `start` or `end` of the anchor; it flips or shifts to fit. |
| `modal` | A scrim (the `scrim` colour at 32%) over the whole window, blocking input to what is under it and keeping Tab inside. It follows the window's size and centres its children unless the style places them (`align_content`). A press on the scrim closes a dismissible modal; a press on its content does not. |
| `dismissible` | `true` (the default): Escape and a press outside close it. `false` turns both off. |
| `focus_first` | When it opens, the focus moves to the first thing in it that can take it (a menu's first row). |
| `timeout` | Closes it that many milliseconds after it opens, unless the pointer is over it. 0, the default, never. |
| `handlers` | `on_dismiss` runs when it closes itself or the user closes it. |

Without an `anchor` and not modal, the layer sits at its own `x` and `y` in the window (the top left unless its style says).
Focus goes back to where it was when the layer closes. To close it from inside, write `false` to the Signal `open` is bound
to, as the Cancel button does. The `style:` of the Overlay sizes and paints the layer; put the dialog itself in a child with
its own size and background.

A menu against a button, closed by the same Signal:

```yaml
widget: Container
state: {menu_open: false}
style: {flex_direction: vertical, padding: 20, width: 300, height: 240}
children:
  - {widget: Button, name: trigger, label: Options, handlers: {on_click: "menu_open = not menu_open"}}
  - widget: Overlay
    open: "{{ menu_open }}"
    anchor: trigger
    placement: below
    focus_first: true
    style: {width: 160, background: surface_container}
    children:
      - widget: Container
        name: rename
        style: {height: 40, padding: 12, align_content: left}
        handlers: {on_click: "menu_open = False; rename()"}
        children:
          - {widget: Text, text: Rename, typography_role: label_large, style: {foreground: on_surface}}
      - widget: Container
        name: remove
        style: {height: 40, padding: 12, align_content: left}
        handlers: {on_click: "menu_open = False; remove()"}
        children:
          - {widget: Text, text: Delete, typography_role: label_large, style: {foreground: on_surface}}
```

[The View Language](view-language.md#overlays) has the rest, and a `tooltip:` on any node is the lighter way to show a hint
([Tooltips](view-language.md#tooltips)).

## Overlays from Python

For a dialog, menu or snackbar that code opens, `tesserae.overlays` makes them:

```python
from tesserae.overlays import Dialog, Menu, Snackbar, Tooltip

confirm = Dialog(app.window, "Discard draft?", "It won't be saved.",
                 actions=[("Cancel", None), ("Discard", viewmodel.discard)])
confirm.open()                      # modal: focus moves into it
confirm.on_close(lambda: print("closed"))
```

Made on the app's window with no `theme=`, an overlay takes the app's
theme and follows it, light and dark included. Give `theme=` to pin
it to a theme instead.

Components such as dialogs, menus and snackbars have their own pages under
[Components](../components/index.md); the signatures are in the
[Python API](../api/python.md). This page covers how they open, close and behave.

Every overlay has `open()`, `close()`, `is_open`, `on_close(fn)` and
`set_theme(theme)`. When it closes, focus goes back to where it was.

## A dialog with a view of its own

`ViewDialog(window, "Settings_View.yaml", width=480, height=320)` is a `Dialog` whose content is a view file: its
file, or its name in a project, with its ViewModel if it has one (`arguments={"who": "Ada"}` goes to the constructor) and without one
if it hasn't. `dialog.content` is the view and `dialog.viewmodel` its ViewModel. A `TitleBar` with `buttons: [dismiss]` at
the top of the view is a header with a close button, and a `surface.dismiss` handler on anything closes the dialog.

`ViewDialog` is for a view in the older syntax (`kind:`), read with the older loader, and given one in the current language (`widget:`) it refuses it
with a message that says what to write instead. A dialog in the current language is a modal `widget: Overlay` in a view, as above: its content is the
view you call by name, `open` is bound to a Signal, and a `surface.dismiss` handler closes it. A called view has no ViewModel of its own, so
the `arguments` that `ViewDialog` hands to a ViewModel's constructor are the Overlay's content's params, or names the view's ViewModel serves.

`surface.dismiss` closes the nearest overlay the widget is in. In a view that is the nearest `widget: Overlay` up the tree, closed as a press outside it
would: the layer hides, a bound `open` goes false, and `on_dismiss` runs. A button in a view the Overlay calls dismisses it too, and in nested
Overlays it is the inner one. With no `widget: Overlay` around, it closes the overlay made by `tesserae.overlays` that the view is in, as its `close()`
does (`dismiss_surface(node)` is the same from Python), and does nothing if there is none. Writing `false` to `open` still closes an Overlay.

## Which closes how

| Overlay | Where it opens | Outside press | Escape | Modal |
| --- | --- | --- | --- | --- |
| `Menu` | below its anchor (flipped above if it won't fit), or at a point | closes | closes | no |
| `Dialog` | centred over a scrim | -- | closes | yes |
| `ViewDialog` | centred over a scrim, showing a view | -- | closes | yes |
| `SideSheet` | the window's end, over a scrim, sliding in | -- | closes | yes |
| `NavigationDrawer` | the window's start, over a scrim, sliding in | -- | closes | yes |
| `Snackbar` | 24 px in, 72 px from the bottom | no | no | no |
| `Tooltip` | below its anchor | closes | closes | no |
| `Popover` | below its anchor | closes | closes | no |
| `SearchView` | below its search bar | closes | closes | no |

A modal overlay's scrim (black at 32%) fills the window, even as the
window resizes while it's open, and edge sheets and snackbars keep to
their edge. A press
outside the panel lands on the scrim, and Escape is what closes it. A
modal overlay keeps Tab inside it.

## Each one

- **`Dialog(window, headline, text, width=312, height=200, actions=[(label, fn)])`:**
  MD3's basic dialog, with text-button actions on the right. An action
  calls its `fn` and closes the dialog.
- **`Menu(window, items, width=200)`:** `items` are `(label, fn)` pairs or
  `tesserae.widgets.menu_item(...)` widgets. It opens with
  `open(anchor)`, `open_at(x, y)`, or on a right-click with
  `attach_context(node)`. Focus moves to the first item; the up and down
  arrows move between items; a click or Enter calls the item and closes
  the menu.
- **`Snackbar(window, text, action=None, on_action=None, closable=False, duration=4000)`:**
  it hides itself after `duration` ms, as MD3's does (`None` keeps it
  until closed). The action button calls `on_action` and closes it. It's
  announced politely.
- **`Tooltip(window, text)`:** `attach(anchor)` shows it 500 ms after the
  anchor is hovered, or at once when the anchor gets keyboard focus, and
  hides it when the pointer or focus leaves. It gives the anchor its text
  as a label, since screen readers can't reach a tooltip.
- **`Popover(window, supporting_text, subhead=None, width=312, actions=[(label, fn)])`:**
  MD3's rich tooltip, `tre`'s popover: a `surface_container` panel with
  an optional subhead, the text wrapped to the width, and optional text
  buttons. Unlike a plain tooltip it stays open until an outside press,
  Escape or an action closes it, and with actions, focus moves to the
  first. `open(anchor)` shows it below `anchor`; `attach(anchor)` opens
  and closes it on the anchor's click.
- **`SideSheet(window, width=360, label=None)`:** a modal side sheet. Put
  its content in `.panel`. A standard (non-modal) side sheet isn't an
  overlay: use `tesserae.widgets.side_sheet(modal=False)`.
- **`NavigationDrawer(window, labels, icons, selected=None)`:** the modal
  navigation drawer. `.drawer` is the drawer widget (`.drawer.selected`,
  `.drawer.on_change`), and choosing an item closes it.
- **`SearchView(window, bar=None, width=360, max_height=336, results=None)`:**
  MD3's docked search view, the results under a `search_bar`. Given the
  `bar`, it opens below it when the field has focus or is typed in and
  there are results. The down arrow in the field moves into the rows, up
  from the first row goes back, and a click or Enter calls the row's
  `fn` and closes it. `set_results([(text, fn)])` replaces the rows, and
  `on_query(fn)` hears the bar's typing.

`tesserae.widgets`' `dialog`, `snackbar`, `side_sheet(modal=True)`,
`menu`, `tooltip`, `popover` and `search_view` return these.

## Not yet covered

- Dialog and snackbar text is one line. Long supporting text doesn't
  wrap yet.
- Submenus: `menu_item(submenu=True)` draws the chevron, and opening a
  nested menu is up to you.
