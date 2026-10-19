# Reactivity

Tesserae's reactivity lives in `tesserae.reactive` and is exported from
`tesserae` itself.

`Signal` is the basic reactive cell:

```python
from tesserae import Signal

count = Signal(0)
count.get()          # 0 -- records a read-dependency when called during a binding's evaluation
count.set(5)          # notifies subscribers, only if the value actually changed
count.update(lambda v: v + 1)
```

On top of it, derived values, side effects and batched writes:

```python
from tesserae import Computed, Effect, batch

price = Signal(10.0)
quantity = Signal(2)

total = Computed(lambda: price.get() * quantity.get())  # derived, cached
Effect(lambda: print(f"total is now {total.get()}"))     # side effect only

def apply_discount():
    price.update(lambda p: p * 0.9)
    quantity.set(quantity.get() + 1)

batch(apply_discount)  # total recomputes once, not twice
```

- **`Computed(fn)`** -- a derived, cached value. Recomputes only when
  one of the `Signal`/`Computed` values `fn` actually reads changes.
- **`Effect(fn)`** -- runs `fn` once immediately, then again whenever
  something it reads changes. Side-effect-only -- has no `.get()` of
  its own to read back.
- **`batch(fn)`** -- runs `fn`, collapsing every `Signal` write inside
  it into one notification pass at the end, instead of one pass per
  write. Use it when a single logical action touches several `Signal`s
  at once.
- **`untrack(fn)`** -- runs `fn` without recording any read-dependency,
  even inside a `Computed`/`Effect`/binding evaluation currently
  tracking reads. Use it to read a `Signal`'s current value without
  making the enclosing `Computed`/`Effect` depend on it.

`Computed`/`Effect` duck-type against `Signal`'s own subscribe shape,
so a `{{ }}` expression in a `*_View.yaml` can point straight at a
`Computed` with no special handling. A Signal or Computed reads as its value in a view, so `{{ total }}` and `{{ total.get() }}` are the same:

```yaml
text: "{{ total }}"
```

A ViewModel is a class whose attributes are the names a view reads. It serves the views that name it, and
is made once, with no arguments, by `app.bind`:

```python
from tesserae import Computed, Signal, ViewModel

class CartViewModel(ViewModel):
    views = "Cart"

    def __init__(self):
        super().__init__()
        self.price = Signal(10.0)
        self.quantity = Signal(2)
        self.total = Computed(lambda: self.price.get() * self.quantity.get())

    def add_one(self):                      # a handler: `handlers: {on_click: add_one}`
        self.quantity.update(lambda q: q + 1)
```

The view that names it starts `name: Cart`, which must match `views` exactly.

See [Binding Expressions](bindings.md) for what a `{{ }}` expression can contain.

## Details worth knowing

- **Unchanged writes don't notify.** `set` and `update` skip notification
  when the new value equals the current one. That's what stops a two-way
  binding recursing.
- **`Computed` is eager.** It recomputes as soon as a dependency changes,
  not when next read, and notifies only if its own value changed.
- **Writing a `Signal` while it's notifying raises.** If a subscriber
  writes back to the signal that's notifying it, directly or through
  other signals, you get a `RuntimeError` saying so rather than endless
  recursion. Often the fix is `untrack(...)` around a read that shouldn't
  be a dependency.
- **Use Tesserae's classes.** `tesserae.Signal` and friends track only
  each other: a signal from another library read inside a
  `tesserae.Computed` isn't recorded.
- **Bindings use them.** A bound node updates when a `Signal` or
  `Computed` its `{{ }}` expression reads changes. See
  [Binding Expressions](bindings.md).
- **A list in a Signal is replaced, not changed in place.** A `for:` and a binding notice `tasks.set([...])` or
  `tasks.update(lambda ts: [*ts, new])`; `tasks.get().append(new)` changes the list without a notification, and nothing updates.
