# Reactivity

Tesserae's reactivity lives in `tesserae.reactive` and is exported from
`tesserae` itself. It used to be `tre`'s, re-exported; Tesserae took it
over in M35, because `tre` 0.3.5 removes it (`tre` D5). The behaviour is
the same, and app code imports it the same way.

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
so a `{{ }}` binding in a `*_View.yaml` can point straight at a
`Computed.get()` value with no special handling:

```yaml
bindings: {text: "{{ total.get() }}"}
```

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
- **Use Tesserae's classes, not `tre`'s.** `tesserae.Signal` and friends
  track only each other. A `tre.Signal` read inside a
  `tesserae.Computed` isn't recorded.
- **Bindings, for now:** until Tesserae evaluates `{{ }}` bindings itself
  (M36), `tre` does, and Tesserae's signals feed `tre`'s dependency
  tracking so bound nodes update as before.
