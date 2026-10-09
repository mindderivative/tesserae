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
path). The app's `transition` plays between routed screens. Not built: a push/pop stack apart from the history.

A route can be written as a mapping, `route: {path: admin, guard: signed_in, redirect: "", lazy: true}`:

| Key | Meaning |
| --- | --- |
| `path` | the route (`""` for the home screen) |
| `guard` | an expression read when the app goes to the screen (`navigate`, `navigate_to`, `back`, `forward`); falsy keeps the app where it is. `show()` is a jump and skips it |
| `redirect` | a route to go to when the guard says no |
| `lazy` | the view is built when the screen is first reached (its route exists from the start), then kept; it cannot have an `if:` |

A routed call inside a routed view is a nested screen: its path is under its parent's (`settings` holding `profile` is `settings/profile`; a path that starts with `/` is from the root),
the parent shows while a child is current, a parent's guard covers its children, and the app's `transition` plays between screens of one parent. In Python, `app.guard(screen, check)`
adds a check, `check(params)` giving `True`, `False` or a route to go to instead; guards that send the app round in a circle are an error after 8 steps.

This component has no `component:` fragment: build it in Python.

## See also

- [Windows And Docks](../guide/windows-and-docks.md)
- [Apps And Screens](../guide/apps-and-screens.md)
- [Python API reference](../api/python.md)
- [YAML reference](../api/yaml.md)
