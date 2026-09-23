# `Repeater`

## `Repeater`

**`Repeater(parent, items_signal, path, viewmodel_cls, into,
key=lambda item: item, args=lambda item: (item,))`**

Watches `items_signal` (a `Signal` of a list) as the single source of
truth and keeps exactly one `Component` + `ViewModel`
([`instantiate`](instantiate.md)) alive per item currently present,
diffed by `key(item)`. Does an initial sync immediately at
construction time.

- `key` -- extracts a stable, hashable identity from an item (default:
  the item itself).
- `args` -- builds the positional args forwarded to
  `viewmodel_cls(component, *args(item))` (default: just the item).

See [Repeater (Lists)](../guide/repeater.md) for the full real scope
boundaries (no reordering, no per-item data re-application) and a
worked example.

## `__getitem__`

**`repeater[key] -> (component, viewmodel)`**

## `__iter__`

**`iter(repeater) -> Iterator[(key, component, viewmodel)]`**

Yields `(item_key, component, viewmodel)` in current order.

## `__len__`

**`len(repeater) -> int`**

How many instances are currently alive.

## `remove`

**`remove() -> None`**

Tears every currently-tracked instance down and unsubscribes from
`items_signal`.
