# Window

*Windows and docking*

## In Material Design 3

Material Design 3 describes how an app's content adapts to a window, not the window itself. `kind: Window` is the OS
window as a view: the root of `Window_View.yaml`, with its title, size and title bar.

## In Tesserae

Before the view is built, the `Window` becomes a vertical container holding the `TitleBar` and a content container;
`App` reads its title, size, `borderless` and minimum size when it loads the view. There is one per app, and it
can't be nested or embedded.

| Property | Meaning |
| --- | --- |
| `title`, `borderless`, `min_width`, `min_height`, `title_bar`, `style` | as above; `style`'s `width` and `height` are the window's size |
| `fullscreen`, `maximized` | set when the view loads, only when written |
| `transparent`, `blur_behind`, `click_through` | set before the window opens, only when written; the platform may refuse one, and says so |

A view branches on the window's size with `app.width_class` and `app.height_class` (Material 3's size classes). Not built: several windows, remembering the window's size between runs (`tre` has no window position to restore), a native menu bar.

```yaml
id: root
kind: Window
title: Notes
borderless: true
style: {width: 960, height: 600}
title_bar: {title: Notes, buttons: [minimize, maximize, close]}
children:
  - id: body
    view: Main_View.yaml
    route: ""
```

```python
app = App(title="Notes", root=HERE)
app.load("Window")
```

This component has no `component:` fragment: build it in Python.

## See also

- [Windows And Docks](../guide/windows-and-docks.md)
- [Custom Title Bars](../guide/custom-title-bars.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
