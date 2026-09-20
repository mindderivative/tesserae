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
tesserae.{Signal,View,ViewModel}   -- thin re-exports of tre's own real,
  |                                     already-working MVVM primitives
  |
tre (Rust/Python hybrid engine)   -- Tree/layout/paint/dispatch/render,
                                        the declarative YAML+binding layer
                                        (engine-spec), and the live-window
                                        wiring (Window.from_view/show_view,
                                        tre's own M42)
```

Tesserae does not duplicate `tre`'s own real capability in slower,
less-tested Python -- `Signal`/`View`/`ViewModel` are `tre`'s own classes,
imported unmodified. Tesserae's own real, additive value is `App`: the
real "one entry point, named-screen registry, switch without
re-bootstrapping" layer neither `tre` nor pyCopper's own `App`/`Engine`
split provide in this exact shape.

## `*_View.yaml` / `*_ViewModel.py`

Mirrors pyCopper's own real, validated convention (see its
`ARCHITECTURE.md`/`LESSONS_LEARNED.md`): a `ViewModel` is scoped
one-per-view-file, so a self-contained, independently-loadable pair is
what lets `app.py` register several and switch which one is currently
shown without re-bootstrapping each one from scratch. Not (yet) enforced
by a runtime check the way pyCopper's own does -- a real, additive
follow-up if it turns out to matter in practice, not manufactured ahead
of a real need.

## `App`

```python
app = App(width=240, height=120, title="My App")
app.register("counter", view, viewmodel)
app.show("counter")   # opens the real Window (tre.Window.from_view)
...
app.show("settings")  # switches the same live Window (tre.Window.show_view)
app.run(max_frames=...)
```

`App.show`'s first call opens the real `tre.Window` via `Window.
from_view`; every call after that switches the same live window via
`Window.show_view` -- both real, already-shipped `tre` capabilities
(M42, both phases). Neither call re-parses YAML or re-attaches a
`ViewModel`.

## What's real today

- `App.register`/`show`/`run`, exercised end to end by
  `examples/counter/`.
- Everything `tre.View`/`tre.Signal`/`tre.ViewModel` already provide:
  `{{ }}` binding expressions (a strict, non-`eval` whitelist), real
  `on_click`/`on_hover_enter`/`on_hover_exit`/`on_change` handler wiring,
  two-way binding for `checked`/`thumb_position`/`text`, hot-reload via
  `View.poll_reload()`.

## Explicitly deferred

See `README.md`'s own "Explicitly deferred" section -- richer
reactivity, a wider bindable-property/widget surface, app-level
state/routing beyond `App.show`, PyPI publishing.
