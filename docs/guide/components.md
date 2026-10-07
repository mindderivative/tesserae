# Components & Embedding

!!! note
    This page covers `tesserae.instantiate` -- embedding a whole,
    independently-stateful `*_View.yaml` + `*_ViewModel.py` pair. For
    reusing one of Tesserae's built-in MD3 components
    (a button, a card, a checkbox, ...) declaratively inside a
    `*_View.yaml`, see
    [Declarative Component Fragments](component-fragments.md) and
    [Components](../components/index.md) instead.

`tesserae.instantiate(parent, path, viewmodel_cls, into, *args,
**kwargs)` (see the [Python API](../api/python.md)) embeds another view's own YAML as a real, independent
`Component` with its own `ViewModel`, built by Tesserae in the host's
window, with the same `*_View.yaml`/`*_ViewModel.py` naming check
`App.load` makes.

```python
from tesserae import instantiate

component, viewmodel = instantiate(view, "Card_View.yaml", CardViewModel, container)

# in a project, a name is enough: Views/Card_View.yaml, and CardViewModel found by the view's name
component, viewmodel = instantiate(view, "Card", into=container)
```

- `parent` is a `View` or another `Component` -- they nest, so a
  component can itself hold further nested components the same way.
- `into` is the `Node` to embed under (e.g. `view.node("item_list")`).
- `path` is a file or a name found in the app's [project](projects.md); `viewmodel_cls` left out is found by the
  view's name. A name with no app to look in is an error saying so.
- Extra positional and keyword args are forwarded to
  `viewmodel_cls(component, *args, **kwargs)`: for a component that needs
  its own data, or a callback to notify its parent when it removes itself.

Call `instantiate` once per instance for multiple simultaneous
instances (a list where each row is its own independent component) --
each call is fully independent, even reusing the same `path`
repeatedly. Every instance gets its own `NodeId`s, even when widget `id`s
repeat across instances.

A component is built in its host's window with the host's theme and
stylesheet, so the host's `styles:` rules and theme roles style it too.
When the host is re-themed or re-styled, including by hot reload, the
component follows. Its own `*_View.yaml` is hot-reloaded too: editing it
reloads every live instance in place, including ones added while the app
runs (see [Hot Reload](hot-reload.md#components-added-at-run-time)).

## In YAML: `view:`

A `view:` node shows another view where it is, with no Python. It is the YAML form of `instantiate`, for a view that is part
of the layout and not made from data:

```yaml
id: root
kind: Container
style: {flex_direction: horizontal, width: 480, height: 200}
children:
  - {id: sidebar, view: Sidebar_View.yaml, style: {width: 160}}
  - {id: counter, view: Counter, with: {start: 5}}     # a name, found in the project
```

- The view is a view of its own, so its ids don't clash with the host's: `Sidebar_View.yaml` and the host can both have `id: root`.
- It has its own ViewModel when there is one, `Sidebar_ViewModel.py` beside it or in the project's `ViewModels/`, and **it needs
  none**: a view with no ViewModel is static (a layout, a header, a panel of text). A static view can't have `bindings:`,
  `handlers:` or `two_way:`, and it can't be given `with:`: the error names the file and the node.
- `with:` is given to the ViewModel's constructor as keyword arguments: `CounterViewModel(view, start=5)`.
- `style:` on the node places the embedded view in its parent, as on any node. A relative file is relative to the file that names it.
- It takes the host's theme and follows it, and a view embedded in a view works too.
- From Python, `view.embedded("counter")` is the embedded view (`.node(...)`, `.viewmodel`) and `view.viewmodel` is a view's
  own ViewModel.
- Hot reload watches the embedded file. Editing the host keeps an embedded view whose `view:` and `with:` didn't change, with its
  state, and builds a new one when they did.

### Routed views

Give a `view:` node a `route:` and the view is a screen of the app, not just a part of the layout. This is for the
[window view](../api/yaml.md#the-window) (the `kind: Window` root), where the screens are:

```yaml
id: root
kind: Window
style: {width: 900, height: 600}
children:
  - id: nav
    component: NavigationRailScreens
    with:
      items:
        - {label: Tasks, icon: home, screen: Main}
        - {label: Settings, icon: settings, screen: Settings}
  - id: screens
    kind: Container
    style: {flex: fill}
    children:
      - {id: main, view: Main_View.yaml, route: ""}
      - {id: settings, view: Settings_View.yaml, route: settings}
```

- The screen's name is the view's file name without `_View.yaml` (`Settings`): `app.show("Settings")`, `app.navigate("Settings")`,
  `app.navigate_to("settings")` and `app.screen("Settings")` all work, and the view keeps its ViewModel and its state while another
  screen shows (it is hidden, out of the layout, not rebuilt).
- Nothing shows until a route is current: call `app.navigate_to("")` (or `app.show(...)`) after loading the window.
- `handlers: {on_click: navigate.Settings}` on any node goes to a screen; `navigate.back` and `navigate.forward` move in the history.
  `app.current_screen` is a value a binding can read: `{{ app.current_screen.get() == 'Settings' }}`.
- `NavigationRailScreens` is a navigation rail whose destinations navigate and are filled while their screen is current.
- A `route:` is an error outside the window view; a view can be routed once; editing the window view while the app runs adds or removes screens.

## Tearing a component down

```python
component.remove()
```

Removes the instance, unsubscribing its own `Signal`s first, so a later
write to a `Signal` it read from can't reach a `NodeId` that no longer
exists.

## An example

```yaml
# TodoItem_View.yaml
id: root
kind: Container
style: {flex_direction: horizontal, width: 260, height: 36, gap: 8}
children:
  - id: label
    kind: Text
    text: {content: "", font_family: Roboto, font_size: 16}
    style: {width: 180, height: 32, foreground: "#FFFFFF"}
    bindings: {text: "{{ label.get() }}"}
  - id: remove_button
    kind: Rect
    style: {width: 60, height: 32, background: "#B3261E", corner_radius: 4}
    handlers: {on_click: "remove_self"}
```

```python
# TodoItem_ViewModel.py
from tesserae import Signal, ViewModel


class TodoItemViewModel(ViewModel):
    def __init__(self, component, item_id, items_signal):
        self.label = Signal(item_id)
        self._item_id = item_id
        self._items_signal = items_signal
        super().__init__(component)

    def remove_self(self):
        self._items_signal.update(lambda items: [i for i in items if i != self._item_id])
```

```python
component, vm = instantiate(
    parent_view, "TodoItem_View.yaml", TodoItemViewModel, container,
    item_id, items_signal,  # forwarded to TodoItemViewModel(component, ...)
)
```

For a dynamic list, with items added and removed over time and driven by
one `Signal`, see [Repeater](repeater.md), which does this bookkeeping
for you.
