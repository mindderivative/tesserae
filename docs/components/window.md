# Window

*Windows and docking*

## In Material Design 3

Material Design 3 describes how an app's content adapts to a window, not the window itself. `widget: Window` is the OS
window as a view: the root of `Window_View.yaml`, with its title, size and title bar.

## In Tesserae

Before the view is built, the `Window` becomes a vertical container holding the `TitleBar` and a content container;
`App` reads its title, size, `borderless` and minimum size when it loads the view. A `Window` is the root of its view: it can't be nested or embedded. There is
one `Window` per window view. The app's own window is the window view it opens with `app.open_view("Window")` (an app has one), and a second OS window is another view whose
root is a `Window`, opened with `app.open_window`.

| Property | Meaning |
| --- | --- |
| `title`, `borderless`, `min_width`, `min_height` | the OS window's title, whether it has no OS title bar or borders, and the least the user can resize it to |
| `title_bar` | a `{title, icon, buttons}` mapping for the window's title bar; in a window that is not `borderless` it is a plain header, with no buttons of its own (the OS draws them) |
| `style` | `width` and `height` are the window's size (a second window whose view has no `Window` root is 480 by 320), and `background` its fill; the rest lays out the content |
| `remember` | true, or a name: the size, the place (where the platform lets an app say: not Wayland) and the maximized state are kept in a small file in the user's config directory (named for the title, or the name) and put back next run; a maximized window keeps the size it had before. The app's own window only |
| `fullscreen`, `maximized` | set when the view loads, only when written (in a second window too) |
| `transparent`, `blur_behind`, `click_through` | set before the window opens, only when written; the platform may refuse one, and says so |

A view branches on the window's size with `app.width_class` and `app.height_class` (Material 3's size classes).

**Several windows.** `app.open_window("Prefs")` builds `Prefs_View.yaml` in a new OS window and returns its `AppWindow`; `app.windows` holds the others by name,
`app.window_of("prefs")` finds one and `app.close_window("prefs")` closes it. The view's `Window` root gives that window its title, size, minimum size, `borderless` and flags.
`modal=True` puts a dimming layer over the parent (the app's window, or `parent=` another `AppWindow`) that takes its input until the child closes. From a view,
the handler `open_window('Prefs')` does the same, and `open_window('Prefs', True)` opens a modal one. A second window has no screens or routes, and closing it leaves the
app running; closing the app's own window closes them all. Not built: a native menu bar.

```yaml
name: window
widget: Window
title: Notes
borderless: true
style: {width: 960, height: 600, flex_direction: vertical}
title_bar: {title: Notes, buttons: [minimize, maximize, close]}
children:
  - {widget: Main, name: main, route: "", style: {flex: fill}}
```

```python
app = App(title="Notes", root=HERE)
app.open_view("Window")     # Views/Window_View.yaml: the app's window
```

```python
prefs = app.open_window("Prefs", modal=True)   # Prefs_View.yaml, in a window of its own
prefs.on_close(save)
prefs.center()                                 # where the system lets an app place a window
```

## How it is built

### `Window`

The root of an app window.

| Property | Type | Default | Meaning |
| --- | --- | --- | --- |
| `title` | `str` | required | The OS window's title. |
| `borderless` | `bool` |  |  |
| `remember` | `any` |  | true, or a name: the window's size, place (where the platform lets an app say) and maximized state are kept between runs. |
| `fullscreen` | `bool` |  | The window fills its monitor, borderless (set when the view loads). |
| `maximized` | `bool` |  | The window opens maximized. |
| `transparent` | `bool` |  | A see-through window that draws only what the view paints; the OS fixes it before the window opens. |
| `blur_behind` | `bool` |  | The desktop behind a transparent window is blurred (where the compositor does it). |
| `click_through` | `bool` |  | Clicks go to the window beneath; the window takes none. |
| `min_width` | `float` |  |  |
| `min_height` | `float` |  |  |
| `title_bar` | `dict` |  | Title, icon and buttons of a custom title bar. |

## See also

- [Windows And Docks](../guide/windows-and-docks.md)
- [Custom Title Bars](../guide/custom-title-bars.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
