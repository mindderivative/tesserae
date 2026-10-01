# App Shell & Docking

An app shell is the frame around an app's screens: a top app bar, a
navigation rail or drawer, a status bar, and panels docked around the
content — a file tree on the left, an inspector on the right, a console
at the bottom — that the user can drag between zones and resize. `tre`
provides the docking mechanism; Tesserae draws it and composes the shell.
`examples/app_shell/` in the repository builds it in Python, and
`examples/app_shell_file/` declares the same studio in a `*_Shell.yaml`
([From a shell file](#from-a-shell-file)).

## The shell

```python
from tesserae import App
from tesserae.shell import AppShell
from tesserae.widgets import navigation_rail, status_bar, top_app_bar

app = App(width=1100, height=700, theme_seed=(0x67, 0x50, 0xA4, 0xFF))
window = app.window
shell = AppShell(
    window,
    top_bar=top_app_bar(window, "Studio", width=1100),
    navigation=navigation_rail(window, ["Home", "Notes"], ["home", "search"], selected=0),
    status_bar=status_bar(window, "Ready", width=1100),
    zones={"left": 220, "right": 260, "bottom": 160},
)
app.use_shell(shell)  # screens now show in shell.content
```

Everything here is made on the app's window with no `theme=`, so it takes
the app's theme and follows it (M50): `app.set_dark(True)` re-colours the
bars, rail, shell, dock and screens together, and so does the OS switching
light and dark. A panel built as `tesserae.View(spec, window=app.window)`
with no theme argument follows too. Giving any of them `theme=` (or a view
`theme_seed=`/`dark=`) pins it to that theme. A following shell re-colours
itself and the dock it made. A dock or widget you gave it follows the app
itself, or keeps the theme it was pinned to.

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

## The top bar as the title bar

In an app with `decorations=False` (see [The window](apps-and-screens.md#the-window)),
the shell's top bar is the window's title bar. `top_app_bar` sees the
app is undecorated and makes the bar the window's drag region, with
minimize, maximize and close after its trailing icons, the maximize
glyph swap, and the fade while the window isn't focused. On macOS it
leaves room for the traffic lights and hides its own buttons. The
leading and trailing icons are still buttons and work as before.

```python
app = App(width=1100, height=700, theme_seed=(0x67, 0x50, 0xA4, 0xFF),
          decorations=False, min_width=640, min_height=400)
shell = AppShell(app.window, top_bar=top_app_bar(app.window, "Studio", width=1100), ...)
```

`window_controls=True` or `False` asks for it or refuses it, whatever
the decorations; `True` needs the window to be an `App`'s. A shell
file's `top_bar` does the same in an undecorated app, and hot-reloads
as the title bar. `tesserae new notes --shell --custom-title-bar` makes
such an app ([Getting Started](../getting-started.md)).

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
- **Remove a panel:** `dock.remove_panel(panel)` undocks it (M53). Its
  tab goes, and if it was shown the zone shows the next panel, else the
  previous. The node is kept, so `dock.add_panel` can dock it again.
- `dock.show(panel)`, `dock.panels(side)`, `dock.titles(side)`,
  `dock.shown(side)`, `dock.side_of(panel)`, and `dock.on_move(fn)`,
  which hears `fn(panel, side)` when a panel changes zone.

A `Dock` can be used without a shell — `Dock(window)`, `add_zone(side,
size)` returning a zone to place yourself. A window has one `Dock`,
since it owns the window's docking events.

## From a shell file

The same shell can be described in a `*_Shell.yaml` next to the app's
views and loaded with `app.load_shell(path)` (M52), with no widgets built
in Python:

```yaml
# Studio_Shell.yaml
top_bar: {title: Studio, trailing_icons: [settings]}
navigation:
  items:
    - {screen: Home, icon: home}
    - {screen: Notes, icon: search}
status_bar: {text: Ready}
zones: {left: 220, right: 260, bottom: 160}
center: true
panels: {left: [Files, Outline], right: [Properties], bottom: [Console]}
```

```python
shell = app.load_shell(directory / "Studio_Shell.yaml")  # built and used, as use_shell does
```

Every key is optional. `top_bar` takes a `title`, and optionally a
`leading_icon` and `trailing_icons`. `navigation.items` lists screens by
name, each with an icon, and they become the rail. `status_bar` takes
its `text`. `zones` gives each side zone's size, and `center: true` makes
screens center tabs. The bars stretch across the window as it resizes,
and everything follows the app's theme.

**Panels are named like screens.** `panels:` lists each zone's panels by
name. A name is the screen already registered under it, or else
`<Name>_View.yaml` next to the shell file, with `<Name>_ViewModel.py`'s
`<Name>ViewModel` if that file exists (constructed with just the view).
It's loaded and registered under its name, so:

- its tab's title is its name, and `layout()` and `restore()` use it;
- it's hot-reloaded like any screen;
- `app.show("Files")` brings its tab forward where it's docked, rather
  than moving it into the content. A screen that's showing when the file
  names it as a panel moves into its zone.

A panel whose ViewModel needs more than the view (the `app`, say) is
registered in Python first, before `load_shell`, and the file places it.
`app.screen("Console")` returns a panel's `(view, viewmodel)`, including
a ViewModel the app built from a file.

**Navigation shows screens.** Choosing a rail item calls
`app.show(screen)`, and `app.show` from anywhere else moves the rail's
selection to match, without calling it back. To decide for yourself,
name a method with `on_navigate:`. The rail then calls it on the
`viewmodel` passed to `load_shell`, with the screen's name, instead:

```yaml
navigation:
  on_navigate: navigate
  items: [{screen: Home, icon: home}, {screen: Notes, icon: search}]
```

```python
class ShellViewModel:
    def navigate(self, screen):
        if not self.unsaved_changes():
            app.show(screen)

app.load_shell(directory / "Studio_Shell.yaml", viewmodel=ShellViewModel())
```

A panel with no screen or file, or an `on_navigate` with no such method,
is an error before anything is built, so the app is left as it was.

A mistake names the file and the key, for example:

```text
Studio_Shell.yaml: zones.middle: not a side (zones are left, right, top, bottom)
```

It's the same `AppShell` a Python-built one is: `app._shell`, its `dock`,
`layout()` and `restore()` all work as above.

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
- Hot reload of a shell file can't add or remove a zone or bar, or
  change `center`; those edits are logged as needing a restart. See
  [Hot Reload](hot-reload.md#the-shell-file).
