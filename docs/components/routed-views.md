# Routed views

*Windows and docking*

## In Material Design 3

Material Design 3's navigation rail and bar move between an app's destinations. A routed view is a destination whose
content is a view of its own.

## In Tesserae

A `view:` node with a `route:` in the window view. It is registered as a screen of the app under its file's name, and
shown while it is current; the others are hidden, with their state. `NavigationRailScreens` is a rail whose
destinations navigate.

```yaml
- id: nav
  component: NavigationRailScreens
  with:
    items:
      - {label: Notes, icon: home, screen: Main}
      - {label: Settings, icon: settings, screen: Settings}
- {id: main, view: Main_View.yaml, route: ""}
- {id: settings, view: Settings_View.yaml, route: settings}
```

```python
app.navigate("Settings")
app.navigate_to("settings")
```

In a view written in the current language, a call with a `route:` is the screen, named for the view it calls (`- {widget: Settings, name: settings, route: settings}`
is the screen `Settings`). A route can read params from the path (`notes/{id:int}`), and the screen showing reads the ones it was reached with as
`app.params` (`{{ app.params.get('id') }}`); going back or forward restores each step's params, and `show()` clears them. Handlers: `navigate.Settings`,
`navigate.back`, `navigate.forward`, `navigate_to('Note', {'id': 3})` (a screen by name, with params) and `navigate_route('notes/' + str(id))` (a route by its
path). The app's `transition` plays between routed screens. Not built: nested routes, navigation guards, loading a screen's view only when it is first reached, a
push/pop stack apart from the history.

This component has no `component:` fragment: build it in Python.

## See also

- [Windows And Docks](../guide/windows-and-docks.md)
- [Apps And Screens](../guide/apps-and-screens.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
