# Tesserae Architecture

Honest about what's real vs. planned, matching `tre`'s own
`BUILD_TRACKER.md` documentation discipline -- this file describes what
exists today, not an aspirational design.

## Layering

```
app.py                 -- the real entry point (owns one App instance)
  |
tesserae.App            -- registry of named (View, ViewModel) pairs +
  |                          one live tre.Window; App.show(name) switches
  |                          which pair that Window currently renders
  |
tesserae.instantiate    -- embeds a Component with its own ViewModel
  |                          into a View/Component, enforcing the same
  |                          naming convention as App.load (below)
  |
tesserae.Repeater       -- one list Signal as the single source of
  |                          truth; keeps one Component+ViewModel alive
  |                          per item present, via instantiate (above)
  |
tesserae.{Signal,View,ViewModel,Component,
  |        Computed,Effect,batch,untrack}       -- thin re-exports of tre's
  |                                               own real, already-
  |                                               working MVVM + reactivity
  |                                               primitives (tre's M45)
  |
tre (Rust/Python hybrid engine)   -- Tree/layout/paint/dispatch/render,
                                        the declarative YAML+binding layer
                                        (engine-spec), the live-window
                                        wiring (Window.from_view/show_view,
                                        tre's own M42), and real
                                        multi-instance component embedding
                                        (View.instantiate/Component,
                                        tre's own M43)
```

Tesserae does not duplicate `tre`'s own real capability in slower,
less-tested Python -- `Signal`/`View`/`ViewModel`/`Component` are `tre`'s
own classes, imported unmodified. Tesserae's own real, additive value is
`App` (the real "one entry point, named-screen registry, switch without
re-bootstrapping" layer neither `tre` nor pyCopper's own `App`/`Engine`
split provide in this exact shape), `instantiate` (the same real
enforced-naming discipline, applied to embedded components), and
`Repeater` (automatic keyed add/remove diffing over `instantiate`, built
entirely in Python on top of it -- no new `engine-spec`/`engine-core`
work needed; see its own module doc comment for why a YAML-level
`for_each:` keyword was considered and set aside).

## `*_View.yaml` / `*_ViewModel.py`

Mirrors pyCopper's own real, validated convention (see its
`ARCHITECTURE.md`/`LESSONS_LEARNED.md`): a `ViewModel` is scoped
one-per-view-file, so a self-contained, independently-loadable pair is
what lets `app.py` register several and switch which one is currently
shown without re-bootstrapping each one from scratch. **Enforced at
runtime** (`tesserae.naming.check_naming_convention`, checked via
`inspect.getfile` against the `ViewModel` class's own defining file),
by both `App.load` (top-level screens) and `instantiate` (embedded
components) -- a mismatched pair raises `ValueError` immediately rather
than failing later when a handler name doesn't resolve.

## `App`

```python
app = App(width=240, height=120, title="My App")
view, viewmodel = app.load("Counter_View.yaml", CounterViewModel)  # or register() directly
app.show("Counter")   # opens the real Window (tre.Window.from_view)
...
app.show("Settings")  # switches the same live Window (tre.Window.show_view)
app.run(max_frames=...)
```

`App.show`'s first call opens the real `tre.Window` via `Window.
from_view`; every call after that switches the same live window via
`Window.show_view` -- both real, already-shipped `tre` capabilities
(M42, both phases). Neither call re-parses YAML or re-attaches a
`ViewModel`.

`App.load` is the enforced-naming-convention path (`*_View.yaml`/
`*_ViewModel.py`, checked via `inspect.getfile` against the
`ViewModel` class's own defining file -- `tre.View` has no `path`
getter of its own, confirmed by reading `view.rs` before designing
this, so `load` takes the path directly rather than trying to recover
it from an already-constructed `View`); `App.register` is the lower-
level path for a `ViewModel` that needs a live `app` reference at
construction time (to call `app.show(...)` from its own handler --
`examples/multi_screen/`'s own real reason for using it instead).

## Components

```python
component, viewmodel = instantiate(view, "Card_View.yaml", CardViewModel, container)
```

`instantiate(parent, path, viewmodel_cls, into, *args, **kwargs)`
(`tesserae.component`) checks the naming convention, then calls
`parent.instantiate(str(path), into)` (real `tre` M43 capability --
`parent` is a `View` or another `Component`, so components nest for
free) and constructs `viewmodel_cls(component, *args, **kwargs)`.
Extra `*args`/`**kwargs` are the real, common case a bare `App.load`
call doesn't need: a component's own `ViewModel` often needs data (an
item's own id) or a reference to shared state (`examples/todo_list/`'s
own `TodoItemViewModel` takes the shared `items` `Signal`, so its own
`remove_self` can mutate the single source of truth directly).

Multiple simultaneous instances of the same component are fully
independent -- each `instantiate()` call gets its own `Component`, its
own `ViewModel`, and (confirmed by `tre`'s own M43 investigation) its
own real `NodeId`s, even for widget ids repeated identically across
instances.

## Repeater

```python
items = Signal([])
repeater = Repeater(view, items, "Card_View.yaml", CardViewModel, container)
items.update(lambda lst: [*lst, new_id])   # adds; a removed id drops it
```

`Repeater.__init__` checks the naming convention once, subscribes to
`items_signal` (via its own real `_subscribe`, the same mechanism
`View._attach`'s bindings already use), and does an initial sync. On
every change, it diffs the new list's own keys (`key(item)`, default
identity) against the previously-rendered set: new keys call
`instantiate` (above); keys no longer present call `component.remove()`.

**Real, deliberate scope boundary:** no reordering (an already-present
key keeps its prior position in the shared `Tree` -- `engine_core::Tree`
has no child-reorder primitive today, confirmed by reading its source;
`tre`'s own `Reconciler` carries the identical real limitation), and no
re-application of a changed item's own *data* to an already-alive
instance (that's the item's own `ViewModel`'s job, via its own
`Signal`s -- see `examples/todo_list/`'s own `TodoItemViewModel`).
`Repeater.remove()` tears every remaining instance down and
unsubscribes, mirroring `Component.remove()`'s own real "unsubscribe
before tearing down" ordering.

## What's real today

- `App.register`/`load`/`show`/`run`, exercised end to end by
  `examples/counter/` (single screen, `load`) and
  `examples/multi_screen/` (two screens switching via `App.show()`
  from inside a real dispatched handler, `register`).
- `instantiate`/`Component.remove()`/`Repeater`, exercised end to end
  by `examples/todo_list/` -- a real dynamic list driven by one list
  `Signal`, `Repeater` adding/removing components automatically.
- Everything `tre.View`/`tre.Signal`/`tre.ViewModel`/`tre.Component`
  already provide: `{{ }}` binding expressions (a strict, non-`eval`
  whitelist), real `on_click`/`on_hover_enter`/`on_hover_exit`/
  `on_change` handler wiring, two-way binding for `checked`/
  `thumb_position`/`text`, hot-reload via `View.poll_reload()`.
- `tre.Computed`/`Effect`/`batch`/`untrack` (M45), re-exported
  unmodified -- derived/cached values, side-effect-only reactions, and
  collapsing related writes into one notification pass, all duck-typed
  against `Signal`'s own subscribe shape so a `{{ }}` binding can depend
  on a `Computed` with no special handling. See `README.md`'s own
  Reactivity section.

## Explicitly deferred

See `README.md`'s own "Explicitly deferred" section -- a wider widget
catalog, app-level state/routing beyond `App.show`, PyPI publishing.
`Repeater`'s own real, stated scope boundaries (no reordering, no
per-item data re-application) are named directly above, not repeated
here.
