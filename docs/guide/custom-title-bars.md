# Custom Title Bars

An app can turn off the operating system's title bar and draw its own,
in its theme, with its own controls in it: a search field, tabs, a
menu.
`examples/custom_title_bar/` in the repository shows each way below.

## An undecorated window

```python
app = App(width=960, height=640, title="Notes", theme_seed=(0x67, 0x50, 0xA4, 0xFF),
          decorations=False, min_width=480, min_height=320)
```

`decorations=False` takes away the OS's title bar and borders. The app
then draws a title bar, and the window is still:

- **moved** by dragging the bar, and maximized by double-clicking it;
- **resized** from within `resize_border` (6 px) of any edge or corner;
- **snapped** by the OS (Aero Snap on Windows, edge tiling on Linux
  desktops that have it), since the drag is the OS's own;
- **outlined** by a 1 px [border](#the-window-border), since nothing else
  marks where it ends.

`min_width` and `min_height` keep the user from resizing it so small
that the bar's buttons crush.

The options (`decorations`, `resize_border`, `min_width`, `system_menu`, `icon`, `fullscreen`), the
window's actions and the `app.maximized` and `app.active` values a binding can follow are in
[The window](apps-and-screens.md#the-window), and the [Python API](../api/python.md).

`tesserae new notes --shell --custom-title-bar` makes an app like this
([The `tesserae` command](cli.md)).

## `kind: TitleBar`

The simplest title bar is one node in a view:

```yaml
children:
  - id: bar
    kind: TitleBar
    title: Notes
    icon: home                              # optional: an icon name
    buttons: [minimize, maximize, close]    # the default; any of them, each once
    children:                               # the app's own, between the
      - {id: search, kind: TextField, ...}  # title and the buttons
  - id: body
    ...
```

It's a bar that moves the window when it's dragged (from anywhere but
its buttons and the app's own controls) and maximizes on a double-click.
It holds the icon and title at its start, the app's children in the
middle, and minimize, maximize and close at the right. Maximize shows
the restore glyph while the window is maximized, and its buttons call
the app's actions with no ViewModel method needed. Its parts' ids are
after the bar's: `bar.title`, `bar.close` and so on.

### In a dialog or a sheet

A `TitleBar` is a header for any surface, not only a window. With `buttons: [dismiss]` it has no window buttons, no room for the
OS's controls and no drag region (a press on it doesn't move the window), and its one button closes the dialog or sheet the bar is
in (`surface.dismiss`). Use it in a [`ViewDialog`](overlays.md#a-dialog-with-a-view-of-its-own). `dismiss` is on its own: a bar is
for a window or for a surface.

```yaml
- {id: bar, kind: TitleBar, title: Settings, icon: settings, buttons: [dismiss]}
```

### Height and look

It's 40 px high unless its `style: {height: ...}` says otherwise, and
every part follows, its glyphs staying centred. Its colours are Material
3 roles (`surface`, `on_surface`): with a `theme_seed=` it follows the theme,
light and dark, and an app with no theme gets MD3's baseline palette (light). The title, icon and buttons fade
while the window isn't the focused one, and close's hover is red
(`error`). Each part has a class, so a stylesheet or theme restyles it (see
[Stylesheets](../stylesheets/index.md) and [Themes](../themes/index.md)):

| Class | Part |
|---|---|
| `title_bar` | The bar |
| `title_bar_icon`, `title_bar_title` | The icon and title |
| `title_bar_content` | The app's children |
| `title_bar_buttons`, `title_bar_button`, `title_bar_close` | The buttons |
| `title_bar_glyph` | Each button's glyph |

```yaml
styles:
  - classes: [title_bar]
    style: {background: surface_container}
  - classes: [title_bar_title]
    style: {foreground: primary}
```

The bar's own look is the cascade's first layer, under every theme and
stylesheet, so any of them can change it, and an app's own default theme
doesn't take it away.

### macOS

On macOS an undecorated window keeps the OS's title bar, transparent,
with the traffic lights. A TitleBar leaves room for them at its start
and hides its own buttons. `app.titlebar_inset` (the `(height, width)`
they take, `(0, 0)` elsewhere and in fullscreen) and
`app.native_controls` (whether they show) are read-only Computeds, for a
bar of your own:

```yaml
- id: inset
  kind: Rect
  bindings: {width: "{{ app.titlebar_inset.get()[1] }}"}
  style: {height: 36}
```

## A bar of your own

A bar of your own is any node marked as the window's drag region, with
buttons whose handlers are the window's actions:

```yaml
- id: my_bar
  kind: Container
  window_region: drag          # a press here moves the window
  style: {height: 36, background: surface_container}
  children:
    - {id: tabs, kind: Container, window_region: none, ...}   # not a handle
    - id: close
      kind: Rect
      handlers: {on_click: window.close}
      ...
```

`window_region: drag` covers the node and everything in it that isn't
interactive: a node with a click handler, a focusable one or a text
field is pressed as usual. `none` keeps a node, and what's in it, from
moving the window. The handlers are `window.minimize`,
`window.maximize`, `window.restore`, `window.toggle_maximized` and
`window.close`; they need the view to be on an `App`'s window.
`app.close()` closes the window as the user's close would, so a "save
changes?" check on `close_requested` still runs and can cancel it.

A binding follows the window's state like any Signal's:

```yaml
bindings:
  text: "{{ app.maximized.get() and 'Restore' or 'Maximize' }}"
```

### `pointer_cancel`

When the OS takes a press (moving the window from its bar, maximizing it
on a double-click), the pressed node gets `pointer_cancel` instead of
`pointer_up`, and no click. Every Tesserae widget releases its press on
it; a widget of your own that tracks a press should listen for both.

## The app shell's top bar

In an undecorated app, an [app shell](app-shell.md#the-top-bar-as-the-title-bar)'s
top bar is the title bar: the window's drag region, with the window
buttons after its trailing icons, whether it's made in code with
`top_app_bar` or in a shell file. `top_app_bar(..., window_controls=)`
asks for it or refuses it.

## The window border

An undecorated window would blend into what's behind it, so Tesserae
draws a 1 px border around it, in the theme's `outline_variant` (an
unthemed app gets the baseline colour). It lies over every screen and
the shell, but takes no presses: a press reaches whatever is under it,
and one within `resize_border` of an edge resizes the window. It hides
while the window is maximized or fullscreen, and it isn't drawn on
macOS, where the OS keeps the frame. It follows the app's theme, light
and dark.

`App(window_border=False)`, or `app.window_border = False`, turns it
off. Its class is `window_border`, so a stylesheet or theme restyles it:

```yaml
styles:
  - classes: [window_border]
    style: {border_color: "#FF0000", border_width: 2}   # 0 hides it too
```

Rounded corners and a drawn shadow aren't possible: they need
transparent windows.

## Hot reload

A TitleBar hot-reloads like the rest of its view: an edit to its title,
icon, buttons or content shows while the app runs, and the buttons keep
working. So does a shell file's top bar. See [Hot Reload](hot-reload.md).

## On each platform

| | Windows | macOS | Linux (Wayland, X11) |
|---|---|---|---|
| Title bar | The app's | The OS's, transparent, under the app's | The app's |
| Window buttons | The app's | The traffic lights | The app's |
| Resizing | `resize_border` | The OS's frame | `resize_border` |
| Border | Tesserae's | The OS's frame | Tesserae's |
| Right-click on the bar | The app's, or the OS's window menu with `system_menu=True` | The app's | The app's, or (on Wayland compositors that have one) the window menu with `system_menu=True` |
