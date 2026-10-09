# Title bar

*Windows and docking*

## In Material Design 3

Material Design 3's top app bar sits inside the window; a title bar is the window's own strip. A desktop app that
draws its own keeps the OS's behaviour: drag to move, double-click to maximize.

## In Tesserae

The `TitleBar` kind (`widget: TitleBar` in a view), or `title_bar:` on a `Window`. Its buttons are the handlers `window.minimize`,
`window.maximize`, `window.close` and the like, which need no ViewModel; in a dialog or a sheet `dismiss` closes it. Each button says what it does
when the pointer rests on it (Minimize, Maximize, Close). The bar's children sit between the title and the buttons, so tabs, a search field or
icon buttons can live there; the window's `flex_direction: vertical` puts the bar above the content. Not built: the Windows 11 snap layouts on the
maximize button, the system menu, and a different glyph set for the buttons.

This component has no `component:` fragment: build it in Python.

## Using it

In a view:

```yaml
# Home_View.yaml
id: root
kind: Container
children:
  - id: bar
    kind: TitleBar
    title: Notes
    icon: home
    buttons: [minimize, maximize, close]
```

## See also

- [Custom Title Bars](../guide/custom-title-bars.md)
- [Windows And Docks](../guide/windows-and-docks.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
