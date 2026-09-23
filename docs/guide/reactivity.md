# Reactivity

`Signal` is Tesserae's basic reactive cell, re-exported unmodified from
`tre`:

```python
from tesserae import Signal

count = Signal(0)
count.get()          # 0 -- records a read-dependency when called during a binding's evaluation
count.set(5)          # notifies subscribers, only if the value actually changed
count.update(lambda v: v + 1)
```

`tre`'s own richer reactivity layer (built on `Signal`'s dependency-
recording primitive) is also real and re-exported unmodified:

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
