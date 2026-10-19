# Repeater (Lists)

A list on screen is a `for:` in a view. For a list that changes, the node repeats for each element and a `key:` says which
element each built node belongs to:

```yaml
name: main
widget: Container
style: {flex_direction: vertical, width: 300, gap: 4}
children:
  - widget: Rect
    name: add
    style: {width: 80, height: 30, background: primary}
    handlers: {on_click: add}
  - widget: Container
    for: item in items
    key: item.id
    name: row
    state: {done: false}
    style: {height: 30, gap: 8}
    children:
      - {widget: Checkbox, name: box, checked: "{{ done }}"}
      - {widget: Text, name: title, text: "{{ item.title }}", typography_role: body_large, style: {foreground: on_surface}}
      - {widget: Rect, name: remove, style: {width: 24, height: 24, background: error}, handlers: {on_click: "remove(item.id)"}}
```

```python
class MainViewModel(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.items = Signal([{"id": 1, "title": "Milk"}, {"id": 2, "title": "Eggs"}])   # the single source of truth

    def add(self):
        self.items.update(lambda items: [*items, {"id": len(items) + 11, "title": "New"}])

    def remove(self, id):
        self.items.update(lambda items: [i for i in items if i["id"] != id])
```

When the list is replaced, nodes whose key stays are kept (with their `state:`), new keys are built, removed keys are gone, and the order
follows the list. A list changed in place is not noticed: replace it, as `update` does. Each row has its own
`state:` and its own handlers, in which the loop variable (`item`) is in scope. Every row is built; for thousands of equal rows use a
`VirtualList` instead ([Long lists](view-language.md#long-lists)). The rest of `for:` is in
[Repeating, choosing and remembering](view-language.md#repeating-choosing-and-remembering).

## Repeater, from Python

`Repeater` is the Python form of the same thing for a view written in the older syntax (`kind:` and `id:`, loaded by the
compatibility loader): it keeps one `Component` and `ViewModel` alive for each item of a list `Signal`, matched by a key, and does the add and
remove bookkeeping that [`instantiate` and `Component.remove()`](components.md#views-in-the-older-syntax) otherwise need by hand. It
refuses a view written with `widget:`; `tesserae migrate-yaml` moves a project over, after which a `for:` replaces it
([Migrating](../migration.md)). Its signature is in the [Python API](../api/python.md).

```python
from tesserae import Repeater, Signal

items = Signal([])  # the single source of truth

repeater = Repeater(view, items, "Card_View.yaml", CardViewModel, container)

# in a project, a name is enough: Views/Card_View.yaml and CardViewModel (ViewModels/Card_ViewModel.py)
repeater = Repeater(view, items, "Card", into=container)

items.update(lambda lst: [*lst, new_id])               # adds one
items.update(lambda lst: [i for i in lst if i != id])  # removes one
```

| Argument | Default | Use |
|---|---|---|
| `viewmodel_cls` | found by the view's name | the ViewModel class; left out, it is `NameViewModel` in `Name_ViewModel.py`, beside the view or in the [project](projects.md)'s `ViewModels/` |
| `key` | the item itself | for items that are dicts or dataclasses: a function returning a stable, hashable key |
| `args` | `lambda item: (item,)` | what is forwarded to `viewmodel_cls(component, *args)`: override it for a ViewModel that needs more than the item |

`examples/todo_list/` in the repository is the same list written in the current language: the view builds one row for each item by `for:` and `key:`
(see [Components & Embedding](components.md)), and the ViewModel changes the one `items` list.

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

Put the container the `Repeater` fills, or a node with a `for:`, inside a `ScrollView`: see
[Layout](layout.md#scrolling).
