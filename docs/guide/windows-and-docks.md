# Windows, Docks and Embedded Views

An app's whole frame can be written in the same YAML as any other view: the window, its title bar, a dock of panels, and the
screens inside it, each a view of its own.

| You want | Write |
| --- | --- |
| The OS window, its title and its size | [`widget: Window`](#the-window) at the root of `Window_View.yaml` |
| A title bar of your own | [`title_bar:`](#the-title-bar) on the window, or `widget: TitleBar` anywhere |
| Another view shown inside this one | [a call](#embedded-views): `widget: Name` |
| Screens you navigate between | [a call with `route:`](#routed-views) |
| Panels around the content, in tabs, that the user can drag | [`widget: Dock`](#docks) with `widget: DockPanel` |
| A second window | [`app.open_window`](#several-windows) |

`tesserae new notes --window` makes a project with a window, a rail and routed screens ([The `tesserae` command](cli.md)), and
`examples/window_dock/` in the repository is a studio with all of it: a title bar, a rail, docked panels, routed screens and a status
bar, in one `Window_View.yaml`. Both are written in the language on this page.

## The window

`widget: Window` is the root of a `Window_View.yaml`. There is one per app, it can't be nested inside another view, and it
needs no ViewModel.

```yaml
name: window
widget: Window
title: Notes                # the OS window's title
borderless: true            # no OS title bar or borders: the title bar below is the window's
min_width: 480
min_height: 320
style: {width: 960, height: 600, background: surface, flex_direction: vertical}   # the window's size, and what it is painted with
title_bar: {title: Notes, icon: home, buttons: [minimize, maximize, close]}
children:
  - widget: Text
    name: content
    text: Hello
    typography_role: headline_small
    style: {foreground: on_surface}
```

```python
app = App(title="Notes", root=HERE, theme_seed=(0x67, 0x50, 0xA4, 0xFF))
app.open_view("Window")      # Views/Window_View.yaml
app.run()
```

- `style:`'s `width` and `height` are the window's size, and `background` its fill. The rest of `style:` lays out the content: the
  content is a column when you write `flex_direction: vertical` (a title bar above a body), and a row otherwise (a rail beside the
  screens).
- `borderless: true` is the same as `App(borderless=True)`: the OS window has no title bar or borders, and the title bar is
  the window's.
- A window with a `title_bar:` that isn't `borderless` has a plain header: the OS draws the window's own buttons, so the bar has none of
  its own unless it lists some in `buttons:`.
- The window's other keys are `min_width`, `min_height`, `remember`, `fullscreen`, `maximized`, `transparent`, `blur_behind` and
  `click_through`. The yes/no options (`fullscreen`, `maximized`, ...) are applied only when written, so one the user changed is not undone by a later
  edit. `transparent`, `blur_behind` and `click_through` are fixed before the window opens, and the platform may refuse one and
  say so ([Window Options](window-options.md)). `remember: true` (or a name) keeps the window's size, its place where the platform lets
  an app say (not Wayland) and whether it is maximized between runs.
- `app.open_view("Window")` is what an app opens as its frame. A Window is the app's one window: another `widget: Window` inside a
  view is an error. A window view is opened with `open_view`; `app.load` and `App(window_view=)` are for views in the older syntax.
- The ids of everything in it are paths from the root: a `Dock` named `dock` that is a child of the window is `root.dock`.

The window's view is served by a ViewModel as any named view is. The screens in it have no ViewModel of their own: they read the names
of the one that serves the window view (see [Components & Embedding](components.md)). A window view with no ViewModel is fine too; its
title bar's buttons still work.

## The title bar

`title_bar:` on a window, and `widget: TitleBar` anywhere, make the same bar: it drags the window, maximizes on a
double-click, and holds the icon and title, your own `children`, and the buttons. Its buttons need no ViewModel method:
`window.minimize`, `window.maximize`, `window.restore`, `window.toggle_maximized` and `window.close` are handlers anyone
can use, on any node, in any view (`handlers: {on_click: window.close}`).

A dialog or a sheet takes one too, with a close button that dismisses it:

```yaml
- widget: TitleBar
  name: bar
  title: Rename
  buttons: [dismiss]
```

`surface.dismiss` is the handler behind it. It closes the overlay the bar is in, the nearest one up the tree (a `widget: Overlay` of the view, else one made by
`tesserae.overlays`), and does nothing when the bar is in none. [Custom Title Bars](custom-title-bars.md) has the rest.

## Embedded views

Another view is shown where it is called, as a part of this one:

```yaml
- {widget: Left, name: left, size: 3, style: {width: 220}}      # Left_View.yaml, found by name
```

It takes the keys of any call: the view's params (`size: 3`), `name`, `style`, `classes`, `a11y`, `handlers`, `route` and the rest. A view
found by name can be anywhere in the project (`Views/`, a feature folder) or one of the views Tesserae ships. Its ids sit under the
call's name (`root.left`), and the host's theme and stylesheet apply to it.

This is the same thing as using a [component](component-fragments.md): a view that is called is part of the view that calls it, with
its params and slots. [Components & Embedding](components.md) says what each can read, and how a ViewModel serves views you open
rather than call.

## Routed views

Give a call a `route:` in the window view and it is a screen of the app:

```yaml
name: window
widget: Window
title: Notes
style: {width: 900, height: 600}
children:
  - widget: NavigationRailScreens
    name: nav
    items:
      - {label: Notes, icon: home, screen: Main}
      - {label: Settings, icon: settings, screen: Settings}
  - widget: Container
    name: screens
    style: {flex: fill}
    children:
      - {widget: Main, name: main, route: "", style: {flex: fill}}
      - {widget: Settings, name: settings, route: settings, style: {flex: fill}}
```

- The screen's name is the name of the view it calls: `app.navigate("Settings")`, `app.navigate_to("settings")` (by route),
  `app.show("Settings")` and `app.screen("Settings")` all work.
- Only the current screen shows; the others are hidden, out of the layout, with their state kept.
- `handlers: {on_click: navigate.Settings}` goes to a screen from any node, `navigate.back` and `navigate.forward` move in the history, and
  `app.current_screen` is a value a binding can read.
- `navigate_to('Note', {'id': 3})` goes to a screen by name with params, and `navigate_route('notes/' + str(id))` goes to a route by its
  path. A route can read params from the path (`route: "notes/{id:int}"`), and the screen showing reads the ones it was reached with as
  `app.params` (`{{ app.params.get('id') }}`). Going back or forward restores each step's params, and `show()` clears them.
- `NavigationRailScreens` is a rail whose destinations navigate and fill while their screen is current.
- A `route:` is an error outside the window view, and a view can be routed once.
- The app's `transition` plays between screens ([The View Language](view-language.md#moving-between-screens)).

A route can be a mapping, `route: {path: admin, guard: signed_in, redirect: "", lazy: true}`:

| Key | Meaning |
| --- | --- |
| `path` | the route (`""` for the home screen) |
| `guard` | an expression read when the app goes to the screen; false keeps the app where it is. `show()` is a jump and skips it |
| `redirect` | a route to go to when the guard says no |
| `lazy` | the view is built when the screen is first reached, then kept |

A routed call inside a routed call is a nested screen, with its path under its parent's.

Call `app.navigate_to("")` after opening the window; nothing shows until a screen is current.

## Several windows

`app.window` is the main window. `app.open_window("Prefs")` builds `Prefs_View.yaml` in a new OS window and returns its `AppWindow` (also
`app.windows`, `app.window_of("prefs")`, `app.close_window("prefs")`). The view's `widget: Window` root gives that window its title, size,
minimum size, `borderless` and flags (without one it is 480 by 320). The view has the ViewModel that serves its name, and the app's theme,
stylesheet and `app`. From a handler: `open_window('Prefs')`, and `open_window('Prefs', True)` for a modal one.

```python
prefs = app.open_window("Prefs", modal=True)   # blocks the window it was opened from until it closes
prefs.on_close(save)
prefs.center()                                 # where the system lets an app place a window
```

- Before `run()` the window opens with the main one; while it runs, on the loop's next turn.
- `window.close`, `window.minimize` and the other window handlers act on the window their view is in.
- `modal=True` puts a dimming layer over the parent (the main window, or `parent=` another `AppWindow`) that takes its clicks and keys
  until the child closes. The operating system is not told the child belongs to the parent (tre has no owner window), so the two can
  still be raised and minimized separately.
- Closing a second window leaves the app running; closing the main window closes every window.
- A second window has no screens or routes (those belong to the main window's frame), and its title bar's maximize button reads
  `app.maximized`, which is the main window's.
- Positions are the system's to give: Wayland does not let an app place or centre a window.

## Docks

`widget: Dock` holds `widget: DockPanel`s around the content. Each panel says where it docks with `zone:`, a style field:

```yaml
- widget: Dock
  name: dock
  style: {flex: fill}
  children:
    - widget: DockPanel
      name: files
      title: Files                          # the panel's tab, when its zone has several
      closable: true                        # a close button on the tab
      style: {zone: left, width: 220}
      children:
        - {widget: FileTree, name: tree}
    - widget: DockPanel
      name: editor
      title: Editor
      style: {zone: center}
      children: [...]
    - widget: DockPanel
      name: output
      title: Output
      style: {zone: bottom, height: 160}
      children: [...]
```

- The zones are `left`, `right`, `top`, `bottom` and `center`. A left or right zone's size is its panel's `width`; a top or
  bottom one's is its `height`.
- Panels in one zone are its tabs. A panel alone has no tab strip. The user drags a tab to another zone, and drags the handles
  between zones to resize them.
- A `DockPanel` inside a `DockPanel` is a split of it: side by side (the parent's `flex_direction: horizontal`, the default)
  or top and bottom (`vertical`), with a handle between the halves. A half with a `width` (or `height`) of its own keeps it, and
  the others share what is left. A panel has either splits or content, not both. Each half is a small zone of its own: a tab
  strip over it, with a tab for the half's own content (titled by the `DockPanel`'s `title:`, else its name).
- `zone:` is an error on anything but a `DockPanel` in a `Dock`; a window has one `Dock`.
- A panel's content is whatever its children are, including a call of a view of your own (`FileTree` above).
- A panel with `closable: true` has a close button on its tab. A Dock's `closed` (a list, two-way) holds the names of the closable panels
  that are shut:

```yaml
- widget: Dock
  name: dock
  closed: "{{ shut }}"          # a list Signal of panel names
```

  The close button adds its panel's `name` to `shut`; taking a name out opens the panel again, as the last tab of its zone; putting a
  name in shuts a panel without the button. A panel that is not `closable` is not shut by the list.

```python
view = app.open_view("Window")
dock = view.dock_host("root.dock")          # the node's id: its path from the root
dock.set_size("left", 280)
saved = dock.layout()      # plain data: where every panel is, which one shows, the sizes, the halves
dock.restore(saved)        # ...put back later, e.g. when the app starts
dock.close("root.dock.files")     # shut a closable panel from code; dock.reopen(id) opens it, dock.closed() lists the shut ones
```

`close()` and `reopen()` act on the dock, not on the `closed` list: write the Signal to change what the list says.

### Dropping a panel on a half of a split

Drag a tab over a half and the highlight shows what a drop will do. The outer quarter of each side of a half is an **edge**: dropping
there splits the half, the panel taking a new half on that side with a handle between the two. The rest, strip included, is the
**middle**: dropping there adds the panel to the half as another tab, and the half shows it. A tab in a half is dragged like any
other, to a zone, to another half or to the edge of one; a half made by a drop that loses its last panel disappears and its neighbour
takes the room back. In the tab menu (right click, the Menu key or Shift+F10), "Move to ..." lists the halves too. You cannot drop
a panel on the halves inside it.

A half is named by its node's id, like a panel.

```python
dock.halves()                       # the panels in each half: {"root.dock.editor.source": {"panels": [...], "shown": None}, ...}
dock.show_in_half("root.dock.editor.source", None)   # show the half's own content; or pass a panel id
dock.half_of("root.dock.outline")   # the half a panel is in, or None if it is in a zone
dock.move("root.dock.outline", "root.dock.editor.source")   # into a half, from code; or "left" for a zone
```

`layout()` records the halves too, so the arrangement the user made survives a restart: `halves` has, for each half, the titles of the
panels in it and the tab it shows (`None`: its own content), and `made` has, for each half of the YAML that the user split, the tree
of the splits, as plain data you can write to a file:

```python
{"halves": {"root.dock.editor.source": {"panels": [], "shown": None},
            "root.dock.editor.source.split1": {"panels": ["Console"], "shown": "Console"}, ...},
 "made": {"root.dock.editor.source": {"axis": "x", "size": 62.0, "first": {"half": "root.dock.editor.source"},
                                      "second": {"half": "root.dock.editor.source.split1"}}}}
```

`restore()` takes the user's splits apart (the panels in them go back to their zones), makes the ones in the layout and puts the panels
in their halves. A split's `size` is its first part's width (`x`) or height (`y`). Halves and titles this dock does not have are
skipped, and a split none of whose panels come back is not made. A half of the YAML is found by its id, so renaming one in the file means
a saved layout no longer finds it.

Not supported: dragging a half's own content (what the YAML put in it) to another place, and tabs of a zone or a half cannot be put in a
different order.

The docks you build in Python, without a view, are in [Docking from Python](docking.md).
