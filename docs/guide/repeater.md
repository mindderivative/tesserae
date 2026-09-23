# Repeater (Lists)

`Repeater` automates the add/remove bookkeeping
[`instantiate`/`Component.remove()`](components.md) otherwise need by
hand: point it at a list `Signal` and it keeps exactly one `Component`
+ `ViewModel` alive per item currently present, diffed by a real key.

```python
from tesserae import Repeater, Signal

items = Signal([])  # the single source of truth

repeater = Repeater(view, items, "Card_View.yaml", CardViewModel, container)

items.update(lambda lst: [*lst, new_id])              # adds one
items.update(lambda lst: [i for i in lst if i != id])  # removes one
```

- `key` (default: the item itself) -- for items that are dicts/
  dataclasses rather than bare ids, give a function extracting a
  stable, hashable key.
- `args` (default: `lambda item: (item,)`, forwarded to
  `viewmodel_cls(component, *args)`) -- override for a `ViewModel` that
  needs more than the bare item (see `examples/todo_list/`'s own
  `Todo_ViewModel.py` in the repository, which also forwards the
  shared `items` `Signal` itself so an item can remove itself).

## Real, deliberate scope boundary

`Repeater` only ever adds or removes instances to match the *set* of
keys present:

- It **never reorders** an already-present key's own position. This
  isn't a Tesserae limitation specifically -- `tre`'s own
  `engine_core::Tree` has no child-reorder primitive at all today, and
  `tre`'s own declarative `Reconciler` carries the identical real
  limitation for the same reason.
- It **never re-applies a changed item's own data** to an existing
  instance. An item's own mutable fields are that item's own
  `ViewModel`'s job, via its own `Signal`s -- `Repeater` only ever asks
  "which keys are currently present."

`Repeater.remove()` tears every remaining instance down and
unsubscribes, mirroring `Component.remove()`'s own real "unsubscribe
before tearing down" ordering.

## Iterating

```python
len(repeater)               # how many instances are currently alive
for key, component, vm in repeater:
    ...
repeater[key]                # (component, viewmodel) for one specific key
```

## Why not a YAML-level `for_each:` keyword?

Considered and set aside: it would need a genuinely new per-item
binding-resolution scoping layer inside `tre`'s own `engine-spec`
(today every binding resolves against exactly one `ViewModel`-shaped
object) -- a much bigger, riskier feature than reusing the already-real
`instantiate`/`Component.remove()` primitives `Repeater` is built on
entirely in Python, with zero new `tre`-side work.
