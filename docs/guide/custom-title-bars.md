# Custom Title Bars

An app can turn off the operating system's title bar and draw its own,
in its theme, with its own controls in it: a search field, tabs, a
menu.
`examples/custom_title_bar/` in the repository shows each way below.

## A borderless window

```python
app = App(width=960, height=640, title="Notes", theme_seed=(0x67, 0x50, 0xA4, 0xFF),
          borderless=True, min_width=480, min_height=320)
```

`borderless=True` takes away the OS's title bar and borders (in a [window view](windows-and-docks.md#the-window), `borderless: true`). The app
then draws a title bar, and the window is still:

- **moved** by dragging the bar, and maximized by double-clicking it;
- **resized** from within `resize_border` (6 px) of any edge or corner;
- **snapped** by the OS (Aero Snap on Windows, edge tiling on Linux
  desktops that have it), since the drag is the OS's own;
- **outlined** by a 1 px [border](#the-window-border), since nothing else
  marks where it ends.

`min_width` and `min_height` keep the user from resizing it so small
that the bar's buttons crush.

The options (`borderless`, `resize_border`, `min_width`, `system_menu`, `icon`, `fullscreen`), the
window's actions and the `app.maximized` and `app.active` values a binding can follow are in
[The window](apps-and-screens.md#the-window), and the [Python API](../api/python.md).

`tesserae new notes --window --custom-title-bar` makes an app like this
([The `tesserae` command](cli.md)); the window is a [`widget: Window`](windows-and-docks.md) with `borderless: true` and a `title_bar:`
(the generated files are in the older syntax, which `tesserae migrate-yaml` moves over: [Migrating](../migration.md)).

## `widget: TitleBar`

The simplest title bar is one node in a view:

```yaml
name: window
widget: Window
title: Notes
borderless: true
style: {width: 960, height: 640, flex_direction: vertical}
children:
  - widget: TitleBar
    name: bar
    title: Notes
    icon: home                              # optional: an icon name
    buttons: [minimize, maximize, close]    # the default; any of them, each once
    children:                               # the app's own, between the title and the buttons
      - widget: TextInput
        name: search
        placeholder: Search
        typography_role: body_medium
        style: {width: 200, height: 28, background: surface_container_high}
  - {widget: Container, name: body, style: {flex: fill}}
```

A window's own `title_bar: {title: Notes, icon: home}` makes the same bar for you; write the node when the bar has children of its own, or sits
somewhere other than the top of the window.

It's a bar that moves the window when it's dragged (from anywhere but
its buttons and the app's own controls) and maximizes on a double-click.
It holds the icon and title at its start, the app's children in the
middle, and minimize, maximize and close at the right. Maximize shows
the restore glyph while the window is maximized, and its buttons call
the app's actions with no ViewModel method needed, and say what they do
when the pointer rests on them. Its parts' ids are
after the bar's: `bar.title`, `bar.close` and so on, and the app's own
children keep the names they were given (`bar.search`).

### In a dialog or a sheet

A `TitleBar` is a header for any surface, not only a window. With `buttons: [dismiss]` it has no window buttons, no room for the
OS's controls and no drag region (a press on it doesn't move the window), and its one button closes the dialog or sheet the bar is
in (`surface.dismiss`), which closes the overlay the bar is in, the nearest one up the tree (see [Overlays](overlays.md)). A bar in no overlay does
nothing when it is pressed: a `Dialog` written in a view is closed by its own `open` and `actions`. `dismiss` is on its own: a bar is for a
window or for a surface.

```yaml
- {widget: TitleBar, name: bar, title: Settings, icon: settings, buttons: [dismiss]}
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
| `title_bar_inset` | The room at the start for macOS's traffic lights |
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
doesn't take it away. A `style:` on the bar itself (`style: {height: 48}`) sets its height, and every part follows.

### macOS

On macOS a borderless window keeps the OS's title bar, transparent,
with the traffic lights. A TitleBar leaves room for them at its start
and hides its own buttons. `app.titlebar_inset` (the `(height, width)`
they take, `(0, 0)` elsewhere and in fullscreen) and
`app.native_controls` (whether they show) are read-only Computeds, for a
bar of your own:

```yaml
- widget: Rect
  name: inset
  style: {height: 36, width: "{{ app.titlebar_inset[1] }}", background: transparent}
```

## A bar of your own

A bar of your own is any node marked as the window's drag region, with
buttons whose handlers are the window's actions:

```yaml
- widget: Container
  name: my_bar
  window_region: drag          # a press here moves the window
  style: {height: 36, background: surface_container, flex_direction: horizontal, align_content: center}
  children:
    - widget: Container
      name: tabs
      window_region: none      # not a handle
      style: {width: 200, height: 30}
      children: []
    - widget: Rect
      name: toggle
      style: {width: 80, height: 30, background: primary}
      handlers: {on_click: window.toggle_maximized}
      children:
        - widget: Text
          name: label
          text: "{{ 'Restore' if app.maximized else 'Maximize' }}"
          typography_role: label_large
          style: {foreground: on_primary}
    - widget: Rect
      name: close
      style: {width: 46, height: 30, background: error}
      handlers: {on_click: window.close}
```

`window_region: drag` covers the node and everything in it that isn't
interactive: a node with a click handler, a focusable one or a text
field is pressed as usual. `none` keeps a node, and what's in it, from
moving the window. The handlers are `window.minimize`,
`window.maximize`, `window.restore`, `window.toggle_maximized` and
`window.close`; they need the view to be on an `App`'s window.
`app.close()` closes the window as the user's close would, so a "save
changes?" check on `close_requested` still runs and can cancel it.

An expression follows the window's state like any Signal's: `app.maximized` and `app.active` (the toggle above shows
`Restore` while the window is maximized).

### `pointer_cancel`

When the OS takes a press (moving the window from its bar, maximizing it
on a double-click), the pressed node gets a `pointer_cancel` event instead of
`pointer_up`, and no click. Every Tesserae widget releases its press on
it, and the `pressed` state of an `interaction` clears. In a view, `on_release` is the
pointer-up only, so it does not run for a press the OS took; a widget of your own built in Python that
tracks a press should listen for both events.

## A top app bar as the title bar

In a borderless app, a `top_app_bar` made in code is the title bar: the window's drag region, with the window
buttons after its trailing icons. `top_app_bar(..., window_controls=)` asks for it or refuses it. In a view, use
a `widget: TitleBar` or a window's `title_bar:` instead: the `TopAppBar` view is not a title bar.

## The window border

A borderless window would blend into what's behind it, so Tesserae
draws a 1 px border around it, in the theme's `outline_variant` (an
unthemed app gets the baseline colour). It lies over every screen
and panel, but takes no presses: a press reaches whatever is under it,
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

Rounded corners and a drawn shadow are not done for you: they need a
transparent window (`transparent: true` on the `Window`, see
[Window Options](window-options.md)) and a view that draws its own edge.

## On each platform

| | Windows | macOS | Linux (Wayland, X11) |
|---|---|---|---|
| Title bar | The app's | The OS's, transparent, under the app's | The app's |
| Window buttons | The app's | The traffic lights | The app's |
| Resizing | `resize_border` | The OS's frame | `resize_border` |
| Border | Tesserae's | The OS's frame | Tesserae's |
| Right-click on the bar | The app's, or the OS's window menu with `system_menu=True` | The app's | The app's, or (on Wayland compositors that have one) the window menu with `system_menu=True` |
