# Tesserae

A declarative Python GUI framework, powered by the [Tesserae Render
Engine](https://github.com/mindderivative/tre) (`tre`) -- a Rust/Python
hybrid rendering, layout, animation, and accessibility engine.

Tesserae's own shape follows [pyCopper](https://github.com/mindderivative/pycopper)
(an earlier, standalone framework by the same author, powered by a direct
GLFW/wgpu-py stack instead): app authors write **YAML views**, not Python
widget-class trees, paired with a Python `ViewModel` per view -- a plain
`Signal`-driven MVVM layer, not a whole-tree reconcile.

**Status: pre-alpha, first vertical slice.** `App`/`Signal`/`View`/
`ViewModel` exist and are exercised end to end by `examples/counter/`, but
the widget catalog, wider live-bindable properties, and richer reactivity
are all real, deliberately deferred follow-ups -- see below.

## Install (development)

Tesserae depends on `tre`, currently installed as a local editable checkout
(not yet published) since it needs a capability (`Window.show_view`,
`Window.from_view`) only just landed:

```bash
pip install -e /path/to/tre
pip install -e ".[dev]"
```

## The real, first vertical slice

```bash
python examples/counter/app.py
```

A real `Signal`-bound counter: a `Counter_View.yaml` + `Counter_
ViewModel.py` pair, registered and shown via `App`, a real dispatched
click incrementing a bound label, then a genuine render loop.

## Naming convention

Every real view is a `*_View.yaml` + `*_ViewModel.py` pair -- enforced by
convention (mirroring pyCopper's own real MVVM naming, matched here by
the same name-pair, not by an enforced runtime check yet). `app.py` is
the real entry point: it loads each pair, registers it with `App`, and
calls `App.show(name)` to pick which one is currently on screen --
switching later (another `App.show(other_name)` call, typically from a
registered handler) doesn't re-parse the YAML or re-construct the
`ViewModel`; both stay alive, `Signal` subscriptions intact, for the
life of the app.

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md).

## Explicitly deferred

Named for the record, not designed in detail yet -- each is real, future
work once this foundation is proven further:

- Richer reactivity (`Computed`, general-purpose `Effect`, `batch()`/
  `untrack()`) beyond `tre.Signal`'s own dependency-recording primitive.
- Widening which properties are live-bindable beyond `opacity`/
  `corner_radius`/`checked`/`text` (`tre`'s own current real set).
- A broad widget/component catalog beyond what `tre`'s own `add_*`
  factories and `engine-spec`'s YAML builder already expose.
- App-level state stores, multi-screen routing beyond `App.show(name)`,
  a `tesserae new` CLI scaffolding tool.
- Publishing to PyPI (not relevant until there's a real, wider vertical
  slice worth shipping).
