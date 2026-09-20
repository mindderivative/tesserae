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
tesserae.{Signal,View,ViewModel,Component}   -- thin re-exports of tre's
  |                                               own real, already-
  |                                               working MVVM primitives
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
split provide in this exact shape) and `instantiate` (the same real
enforced-naming discipline, applied to embedded components).

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
item's own text) or a callback (to notify its parent when it removes
itself via `component.remove()`) -- see `examples/todo_list/`'s own
`TodoViewModel.add_item`/`TodoItemViewModel.remove_self`.

Multiple simultaneous instances of the same component are fully
independent -- each `instantiate()` call gets its own `Component`, its
own `ViewModel`, and (confirmed by `tre`'s own M43 investigation) its
own real `NodeId`s, even for widget ids repeated identically across
instances.

## What's real today

- `App.register`/`load`/`show`/`run`, exercised end to end by
  `examples/counter/` (single screen, `load`) and
  `examples/multi_screen/` (two screens switching via `App.show()`
  from inside a real dispatched handler, `register`).
- `instantiate`/`Component.remove()`, exercised end to end by
  `examples/todo_list/` -- a real dynamic list, each item its own
  component, added and removed via real dispatched clicks.
- Everything `tre.View`/`tre.Signal`/`tre.ViewModel`/`tre.Component`
  already provide: `{{ }}` binding expressions (a strict, non-`eval`
  whitelist), real `on_click`/`on_hover_enter`/`on_hover_exit`/
  `on_change` handler wiring, two-way binding for `checked`/
  `thumb_position`/`text`, hot-reload via `View.poll_reload()`.

## Explicitly deferred

See `README.md`'s own "Explicitly deferred" section -- richer
reactivity, a wider bindable-property/widget surface, app-level
state/routing beyond `App.show`, PyPI publishing.
