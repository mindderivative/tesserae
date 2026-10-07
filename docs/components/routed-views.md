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

This component has no `component:` fragment: build it in Python.

## See also

- [Windows And Docks](../guide/windows-and-docks.md)
- [Apps And Screens](../guide/apps-and-screens.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
