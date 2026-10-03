# Repeater (Lists)

`Repeater` keeps one `Component` and `ViewModel` alive for each item of a
list `Signal`, matched by a key. It does the add and remove bookkeeping
that [`instantiate` and `Component.remove()`](components.md) otherwise
need by hand. Its signature is in the [Python API](../api/python.md).

```python
from tesserae import Repeater, Signal

items = Signal([])  # the single source of truth

repeater = Repeater(view, items, "Card_View.yaml", CardViewModel, container)

items.update(lambda lst: [*lst, new_id])               # adds one
items.update(lambda lst: [i for i in lst if i != id])  # removes one
```

| Argument | Default | Use |
|---|---|---|
| `key` | the item itself | for items that are dicts or dataclasses: a function returning a stable, hashable key |
| `args` | `lambda item: (item,)` | what is forwarded to `viewmodel_cls(component, *args)`: override it for a ViewModel that needs more than the item |

`examples/todo_list/` in the repository forwards the shared `items`
`Signal` too, so an item can remove itself.

## What it does and doesn't do

`Repeater` adds or removes instances to match the *set* of keys present:

- It **never reorders** an instance that is already there. The engine's
  tree has no child-reorder operation.
- It **never re-applies a changed item's data** to an existing instance.
  An item's mutable fields belong to that item's own `ViewModel`, through
  its own `Signal`s. `Repeater` only asks which keys are present.

`Repeater.remove()` tears every remaining instance down and unsubscribes,
the way `Component.remove()` does.

## Iterating

```python
len(repeater)               # how many instances are alive
for key, component, vm in repeater:
    ...
repeater[key]               # (component, viewmodel) for one key
```

## In a scrolling list

Put the container the `Repeater` fills inside a `ScrollView`: see
[Layout](layout.md#scrolling).
