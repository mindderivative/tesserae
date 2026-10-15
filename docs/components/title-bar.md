# Title bar

*Windows and docking*

## In Material Design 3

Material Design 3's top app bar sits inside the window; a title bar is the window's own strip. A desktop app that
draws its own keeps the OS's behaviour: drag to move, double-click to maximize.

## In Tesserae

`widget: TitleBar` in a view, or `title_bar:` on a `Window`. It has a `title`, an `icon` and `buttons` (any of `minimize`, `maximize` and `close`, all three by default). It
is 40 pixels high unless its `style` gives another height, and each button is 46 pixels wide. A press on the bar (or its title or icon) moves the window and a double click
maximizes it. Its buttons are the handlers `window.minimize`, `window.toggle_maximized`, `window.close` and the like, which need no ViewModel; in a dialog or a sheet
`buttons: [dismiss]` closes it. The maximize button shows the restore glyph while the window is maximized, and each button says what it does when the pointer rests on it
(Minimize, Maximize, Close). While the window is not the focused one, the title, icon and buttons fade. The bar's children sit between the title and the buttons, so tabs, a
search field or icon buttons can live there; the window's `flex_direction: vertical` puts the bar above the content. On macOS the bar leaves room at its start for the
traffic lights and hides its own buttons. A right click on the bar opens the OS's window menu only if the app was made with `system_menu=True`. Not built: the Windows 11 snap
layouts on the maximize button, and a different glyph set for the buttons.

## How it is built

### `TitleBar`

A custom title bar.

| Property | Type | Default | Meaning |
| --- | --- | --- | --- |
| `title` | `str` |  |  |
| `icon` | `icon` |  |  |
| `buttons` | `list` |  |  |

## Using it

```yaml
name: notes_bar
widget: Container
style: {flex_direction: vertical, width: 640, height: 200}
children:
  - widget: TitleBar
    name: bar
    title: Notes
    icon: home
    buttons: [minimize, maximize, close]
    children:
      - {widget: IconButton, name: find, icon: search, label: Find, handlers: {on_click: find}}
```

## See also

- [Custom Title Bars](../guide/custom-title-bars.md)
- [Windows And Docks](../guide/windows-and-docks.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
