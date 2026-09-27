# App Shell & Docking

An app shell is the frame around an app's screens: a top app bar, a
navigation rail or drawer, a status bar, and panels docked around the
content — a file tree on the left, an inspector on the right, a console
at the bottom — that the user can drag between zones and resize. `tre`
provides the docking mechanism; Tesserae draws it and composes the shell.
`examples/app_shell/` in the repository puts it all together.

## The shell

```python
from tesserae import App
from tesserae.shell import AppShell
from tesserae.widgets import navigation_rail, status_bar, top_app_bar

app = App(width=1100, height=700, theme_seed=(0x67, 0x50, 0xA4, 0xFF))
window, theme = app.window, app.theme
shell = AppShell(
    window,
    top_bar=top_app_bar(window, "Studio", width=1100, theme=theme),
    navigation=navigation_rail(window, ["Home", "Notes"], ["home", "search"], selected=0, theme=theme),
    status_bar=status_bar(window, "Ready", width=1100, theme=theme),
    zones={"left": 220, "right": 260, "bottom": 160},
    theme=theme,
)
app.use_shell(shell)  # screens now show in shell.content
```

The shell fills the window and follows it as it resizes. The top bar,
navigation and status bar are fixed; `zones=` chooses which docked zones
there are — any of `left`, `right`, `top` and `bottom`, each its starting
size in pixels — and they sit around `shell.content`. After
`app.use_shell(shell)`, `app.show(name)` shows screens there, one at a
time.

Each zone has a resize handle between it and the content: drag it, or
focus it and use the arrow keys (16 px a press), Home and End. Its size
stays between 120 px and 70% of the space around it; `shell.size(side)`
and `shell.set_size(side, px)` read and set it.

## Screens as tabs: `center=True`

With `center=True`, the middle is a dock zone too, like an IDE's editor
area. `app.show(name)` opens each screen as a tab there the first time and
brings its tab forward after, so screens stay open side by side — and a
screen can be dragged to an edge zone like any panel, or a panel into the
center.

```python
shell = AppShell(window, zones={"left": 220, "bottom": 160}, center=True)
```

## Docking panels

The shell's `dock` holds the panels. A panel is any node (or widget) with
a title:

```python
shell.dock.add_panel("left", files_view.root, "Files")
shell.dock.add_panel("right", properties_view.root, "Properties")
```

Each zone shows its panels as MD3 secondary tabs; one panel shows at a
time.

- **Pick a panel:** click its tab, or Enter; the left and right arrows
  move along the strip, which is one Tab stop.
- **Move a panel:** drag its tab to another zone (the zone under the
  pointer is highlighted; releasing over no zone leaves it where it
  was). Without a pointer, open the tab's menu — right click, the Menu
  key or Shift+F10 — and choose "Move to …". From code,
  `dock.move(panel, "right")`.
- `dock.show(panel)`, `dock.panels(side)`, `dock.titles(side)`,
  `dock.shown(side)`, `dock.side_of(panel)`, and `dock.on_move(fn)`,
  which hears `fn(panel, side)` when a panel changes zone.

A `Dock` can be used without a shell — `Dock(window)`, `add_zone(side,
size)` returning a zone to place yourself. A window has one `Dock`,
since it owns the window's docking events.

## Saving a layout

`shell.layout()` returns where each panel is, which is shown and each
zone's size, as plain data to save however the app likes;
`shell.restore(layout)` puts it back. Panels are matched by title, and
zones or titles that no longer exist are skipped.

```python
saved = shell.layout()
# {"zones": {"left": {"panels": ["Files"], "shown": "Files", "size": 220.0}, ...}}
shell.restore(saved)
```

## Not yet covered

- A layout is restored by title, so two panels with the same title can't
  be told apart.
- There's no declarative (`*_View.yaml`) form of the shell yet; build it
  in `app.py`.
