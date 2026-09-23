# Components & Embedding

`tesserae.instantiate(parent, path, viewmodel_cls, into, *args,
**kwargs)` embeds another view's own YAML as a real, independent
`Component` with its own `ViewModel` -- the enforced-naming
counterpart to `tre.View.instantiate`/`Component.instantiate`.

```python
from tesserae import instantiate

component, viewmodel = instantiate(view, "Card_View.yaml", CardViewModel, container)
```

- `parent` is a `View` or another `Component` -- they nest, so a
  component can itself hold further nested components the same way.
- `into` is the `Node` to embed under (e.g. `view.node("item_list")`).
- Extra positional/keyword args are forwarded to
  `viewmodel_cls(component, *args, **kwargs)` -- the real, common case
  for a component that needs its own data, or a callback to notify its
  parent when it removes itself.

Call `instantiate` once per instance for multiple simultaneous
instances (a list where each row is its own independent component) --
each call is fully independent, even reusing the same `path`
repeatedly. Confirmed (via `tre`'s own investigation): every instance
gets its own real `NodeId`s, even for widget `id`s repeated identically
across instances.

## Tearing a component down

```python
component.remove()
```

Removes the instance for real -- unsubscribing its own `Signal`s
first, so a later write to a `Signal` it read from can't reach a
`NodeId` that no longer exists.

## A real example

```python
# TodoItem_View.yaml
id: root
kind: Container
style: {flex_direction: Horizontal, width: 260, height: 36, gap: 8}
children:
  - id: label
    kind: Text
    text: {content: "", font_family: Roboto, font_size: 16}
    style: {width: 180, height: 32, background: "#FFFFFF00"}
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

For a real *dynamic* list -- items added and removed over time, driven
by one `Signal` -- see [Repeater](repeater.md), which automates this
add/remove bookkeeping entirely.
