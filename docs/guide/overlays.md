# Overlays

`tesserae.overlays` shows MD3's dialogs, menus, snackbars, tooltips,
side sheets and modal navigation drawers over a window's content (M41).
They're built from Tesserae's fragments and shown with `tre`'s layers,
since `tre` 0.3.5 removes its own `open_dialog`, `open_menu` and so on.

```python
from tesserae.overlays import Dialog, Menu, Snackbar, Tooltip

confirm = Dialog(window, "Discard draft?", "It won't be saved.",
                 actions=[("Cancel", None), ("Discard", viewmodel.discard)], theme=app.theme)
confirm.open()                      # modal: focus moves into it
confirm.on_close(lambda: print("closed"))
```

Every overlay has `open()`, `close()`, `is_open`, `on_close(fn)` and
`set_theme(theme)`. When it closes, focus goes back to where it was.

## Which closes how

| Overlay | Where it opens | Outside press | Escape | Modal |
| --- | --- | --- | --- | --- |
| `Menu` | below its anchor (flipped above if it won't fit), or at a point | closes | closes | no |
| `Dialog` | centred over a scrim | -- | closes | yes |
| `SideSheet` | the window's end, over a scrim, sliding in | -- | closes | yes |
| `NavigationDrawer` | the window's start, over a scrim, sliding in | -- | closes | yes |
| `Snackbar` | 24 px in, 72 px from the bottom | no | no | no |
| `Tooltip` | below its anchor | closes | closes | no |
| `SearchView` | below its search bar | closes | closes | no |

A modal overlay's scrim (black at 32%) fills the window, so a press
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
`menu`, `tooltip` and `search_view` return these.

## Not yet covered

- A scrim is sized when its overlay opens. If the window is resized while
  the overlay is open, the scrim keeps its old size.
- Dialog and snackbar text is one line. Long supporting text doesn't
  wrap yet.
- Submenus: `menu_item(submenu=True)` draws the chevron, and opening a
  nested menu is up to you.
