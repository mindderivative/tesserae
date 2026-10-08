# Docking from Python

Panels docked around an app's content (a file tree on the left, an inspector on the right, a console at the bottom) that the
user can drag between zones are a `Dock`. In a view, write one in YAML: [`kind: Dock` and `kind: DockPanel`](windows-and-docks.md#docks)
are zones, tabs, handles and splits, and `view.dock_host("dock")` reads and sets their sizes and saves and restores the layout.
This page is the `Dock` they are built on, for an app that builds its widgets in Python. `tre` provides the docking mechanism;
Tesserae draws it.

## A dock

```python
from tesserae import App
from tesserae.docking import Dock

app = App(width=1100, height=700, theme_seed=(0x67, 0x50, 0xA4, 0xFF))
window = app.window
dock = Dock(window)
left = dock.add_zone("left", 220)      # a zone's node, to place in your own layout
bottom = dock.add_zone("bottom", 160)
dock.add_panel("left", files_view.root, "Files")
dock.add_panel("bottom", console_view.root, "Console")
```

`add_zone(side, size)` returns the zone's node, which you place in the layout: its `size` is a width for `left` and `right`
and a height for `top` and `bottom`. A window has one `Dock`, since it owns the window's docking events.

A `Dock` made on the app's window with no `theme=` takes the app's theme and follows it: `app.set_dark(...)` and the OS switching
light and dark re-colour it in place. Giving it a `theme=` pins it to that theme.

## Docking panels

A panel is any node (or widget) with a title. Each zone shows its panels as MD3 secondary tabs; one panel shows at a time.

- **Pick a panel:** click its tab, or Enter; the left and right arrows move along the strip, which is one Tab stop.
- **Move a panel:** drag its tab to another zone (the zone under the pointer is highlighted; releasing over no zone leaves it
  where it was). Without a pointer, open the tab's menu — right click, the Menu key or Shift+F10 — and choose "Move to …". From
  code, `dock.move(panel, "right")`.
- **Remove a panel:** `dock.remove_panel(panel)` undocks it. Its tab goes, and if it was shown the zone shows the next panel,
  else the previous. The node is kept, so `dock.add_panel` can dock it again.
- `dock.show(panel)`, `dock.panels(side)`, `dock.titles(side)`, `dock.shown(side)`, `dock.side_of(panel)`, `dock.panel(title)`
  and `dock.on_move(fn)`, which hears `fn(panel, side)` when a panel changes zone.

## Not yet covered

- Panels are found by title, so two panels with the same title can't be told apart.
- Dragging a panel onto one half of a split isn't supported: a dragged panel docks in the five zones.
