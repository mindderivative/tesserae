# Windows, Docks and Embedded Views

An app's whole frame can be written in the same YAML as any other view: the window, its title bar, a dock of panels, and the
screens inside it, each a view of its own. An app that still has a `*_Shell.yaml` can move over with
[Migrating](../migration.md).

| You want | Write |
| --- | --- |
| The OS window, its title and its size | [`kind: Window`](#the-window) at the root of `Window_View.yaml` |
| A title bar of your own | [`title_bar:`](#the-title-bar) on the window, or `kind: TitleBar` anywhere |
| Another view shown inside this one | [`view:`](#embedded-views) |
| Screens you navigate between | [`view:` with `route:`](#routed-views) |
| Panels around the content, in tabs, that the user can drag | [`kind: Dock`](#docks) with `kind: DockPanel` |

`tesserae new notes --window` makes a project with a window, a rail and routed screens, and `examples/window_dock/` in the repository
is a studio with all of it: a title bar, a rail, docked panels, routed screens and a status bar, in one `Window_View.yaml`.

## The window

`kind: Window` is the root of a `Window_View.yaml`. There is one per app, it can't be nested or embedded, and it needs no
ViewModel (an empty one is made, so its title bar's buttons still work).

```yaml
id: root
kind: Window
title: Notes                # the OS window's title
borderless: true            # no OS title bar or borders: the title bar below is the window's
min_width: 480
min_height: 320
style: {width: 960, height: 600, background: surface}   # the window's size, and what it is painted with
title_bar: {title: Notes, icon: home, buttons: [minimize, maximize, close]}
children:
  - id: content
    kind: Text
    text: {content: Hello, typography_role: headline_small}
```

```python
app = App(title="Notes", root=HERE, theme_seed=(0x67, 0x50, 0xA4, 0xFF))
app.load("Window")      # Views/Window_View.yaml
app.run()
```

- `style:`'s `width` and `height` are the window's size, and `background` its fill. The rest of `style:` lays out the
  content (a `flex_direction: horizontal` puts a rail beside the screens).
- `borderless: true` is the same as `App(borderless=True)`: the OS window has no title bar or borders, and the title bar below is
  the window's.
- A window with a `title_bar:` that isn't `borderless` has a plain header: the OS draws the window's own buttons, so the bar
  has none of its own.
- `app.load("Window")` is what an app loads; `App(window_view="Name")` loads `Name_View.yaml` as the window when the app is
  created.
- Hot reload (`app.run(hot_reload=True)`) applies edits to the window view live.

## The title bar

`title_bar:` on a window, and `kind: TitleBar` anywhere, make the same bar: it drags the window, maximizes on a
double-click, and holds the icon and title, your own `children`, and the buttons. Its buttons need no ViewModel method:
`window.minimize`, `window.maximize`, `window.restore`, `window.toggle_maximized` and `window.close` are handlers anyone
can use, on any node, in any view (`handlers: {on_click: window.close}`).

A dialog or a sheet takes one too, with a close button that dismisses it:

```yaml
- id: bar
  kind: TitleBar
  title: Rename
  buttons: [dismiss]
```

`surface.dismiss` is the handler behind it. [Custom Title Bars](custom-title-bars.md) has the rest.

## Embedded views

`view:` shows another `*_View.yaml` where the node is, as a view of its own: its own ids (two views can both have
`id: root`), and its own ViewModel when it has one.

```yaml
- id: left
  view: Left_View.yaml        # a file, or a name found in the project: `view: Left`
  with: {size: 3}             # optional: what its ViewModel is given, by keyword
  style: {width: 220}         # where it sits and how big, in its parent
```

It takes `id`, `view`, `with`, `route`, `style`, `classes`, `a11y` and `group`, and nothing else. A view with no ViewModel is
fine: it is a fragment of layout with its own ids. `view.embedded("left")` is the embedded view from Python, and
`view.viewmodel` is a view's own ViewModel. Editing the embedded file reloads it; editing the host keeps an embedded view that
didn't change, with its state.

This is not a [component](components.md): a component is a fragment with `params:` expanded into the host, sharing its ids;
an embedded view is a whole view.

## Routed views

Give a `view:` node a `route:` in the window view and it is a screen of the app:

```yaml
children:
  - id: nav
    component: NavigationRailScreens
    with:
      items:
        - {label: Notes, icon: home, screen: Main}
        - {label: Settings, icon: settings, screen: Settings}
  - id: screens
    kind: Container
    style: {flex: fill}
    children:
      - {id: main, view: Main_View.yaml, route: ""}
      - {id: settings, view: Settings_View.yaml, route: settings}
```

- The screen's name is the file's name without `_View.yaml`; `app.navigate("Settings")`, `app.navigate_to("settings")`,
  `app.show("Settings")` and `app.screen("Settings")` all work.
- Only the current screen shows; the others are hidden, out of the layout, with their state and ViewModels kept.
- `handlers: {on_click: navigate.Settings}` goes to a screen from any node, `navigate.back` and `navigate.forward` move in
  the history, and `app.current_screen` is a value a binding can read.
- `NavigationRailScreens` is a rail whose destinations navigate and fill while their screen is current.
- A `route:` is an error outside the window view, and a view can be routed once.
- In the current language a view call with a `route:` is the screen (named for the view it calls), the screen showing reads the params it was reached with as
  `app.params`, and `navigate_to('Note', {'id': 3})` or `navigate_route('notes/' + str(id))` go there from a handler.

Call `app.navigate_to("")` after loading the window; nothing shows until a screen is current.

## Several windows

`app.window` is the main window. `app.open_window("Prefs")` builds `Prefs_View.yaml` in a new OS window and returns its `AppWindow` (also `app.windows`, `app.window_of("prefs")`,
`app.close_window("prefs")`). The view's `widget: Window` root gives that window its title, size, minimum size, `borderless` and flags (without one it is 480 by 320). The view has the ViewModel that
serves its name, and the app's theme, stylesheet and `app`. From a handler: `open_window('Prefs')`, and `open_window('Prefs', True)` for a modal one.

```python
prefs = app.open_window("Prefs", modal=True)   # blocks the window it was opened from until it closes
prefs.on_close(save)
prefs.center()                                 # where the system lets an app place a window
```

- Before `run()` the window opens with the main one; while it runs, on the loop's next turn.
- `window.close`, `window.minimize` and the other window handlers act on the window their view is in.
- `modal=True` puts a dimming layer over the parent (the main window, or `parent=` another `AppWindow`) that takes its clicks and keys until the child closes. The operating system is not told the child
  belongs to the parent (tre has no owner window), so the two can still be raised and minimized separately.
- Closing a second window leaves the app running; closing the main window closes every window.
- A second window has no screens or routes (those belong to the main window's frame), and its title bar's maximize button reads `app.maximized`, which is the main window's.
- Positions are the system's to give: Wayland does not let an app place or centre a window.

## Docks

`kind: Dock` holds `kind: DockPanel`s around the content. Each panel says where it docks with `zone:`, a style field:

```yaml
- id: dock
  kind: Dock
  style: {flex: fill}
  children:
    - id: files
      kind: DockPanel
      title: Files                          # the panel's tab, when its zone has several
      style: {zone: left, width: 220}
      children:
        - {id: tree, view: Files_View.yaml}
    - id: editor
      kind: DockPanel
      title: Editor
      style: {zone: center}
      children: [...]
    - id: output
      kind: DockPanel
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
  the others share what is left. A panel has either splits or content, not both.
- `zone:` is an error on anything but a `DockPanel` in a `Dock`; a window has one `Dock`.
- Editing the YAML while the app runs keeps the layout the user made: which zone each panel is in, which tab shows, the
  sizes.

```python
dock = view.dock_host("dock")
dock.set_size("left", 280)
saved = dock.layout()      # plain data: where every panel is, which one shows, the sizes
dock.restore(saved)        # ...put back later, e.g. when the app starts
```

Dragging a panel onto one half of a split isn't supported: a dragged panel docks in the five zones.
