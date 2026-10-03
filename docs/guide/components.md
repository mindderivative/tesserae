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
```

- `parent` is a `View` or another `Component` -- they nest, so a
  component can itself hold further nested components the same way.
- `into` is the `Node` to embed under (e.g. `view.node("item_list")`).
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
