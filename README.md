# Tesserae

A declarative Python GUI framework, powered by the [Tesserae Render
Engine](https://github.com/mindderivative/tre) (`tre`) -- a Rust/Python
hybrid rendering, layout, animation, and accessibility engine.

Tesserae's own shape follows [pyCopper](https://github.com/mindderivative/pycopper)
(an earlier, standalone framework by the same author, powered by a direct
GLFW/wgpu-py stack instead): app authors write **YAML views**, not Python
widget-class trees, paired with a Python `ViewModel` per view -- a plain
`Signal`-driven MVVM layer, not a whole-tree reconcile.

**Status: pre-alpha, first two vertical slices.** `App`/`Signal`/`View`/
`ViewModel` exist and are exercised end to end by `examples/counter/`
(a single screen) and `examples/multi_screen/` (two screens, switched
via `App.show()` from inside a real dispatched handler), but the widget
catalog, wider live-bindable properties, and richer reactivity are all
real, deliberately deferred follow-ups -- see below.

## Install (development)

Tesserae depends on `tre`, currently installed as a local editable checkout
(not yet published) since it needs a capability (`Window.show_view`,
`Window.from_view`) only just landed:

```bash
pip install -e /path/to/tre
pip install -e ".[dev]"
```

## The real vertical slices

```bash
python examples/counter/app.py
python examples/multi_screen/app.py
```

`counter/`: a real `Signal`-bound counter -- a `Counter_View.yaml` +
`Counter_ViewModel.py` pair, loaded via `App.load()` and shown via
`App`, a real dispatched click incrementing a bound label, then a
genuine render loop.

`multi_screen/`: two independent screens (`Home`/`Settings`), each its
own `*_View.yaml`/`*_ViewModel.py` pair, switched via `App.show(name)`
from inside each screen's own real dispatched `on_click` handler --
proving a switch works even when triggered *reentrantly*, from the
handler `App.show` itself is dispatching into.

## Naming convention

Every real view is a `*_View.yaml` + `*_ViewModel.py` pair (mirroring
pyCopper's own real MVVM naming) -- enforced at runtime by
`App.load(view_path, viewmodel_cls, name=None)`:

```python
from tesserae import App
from Counter_ViewModel import CounterViewModel

app = App(width=240, height=120, title="My App")
view, viewmodel = app.load("Counter_View.yaml", CounterViewModel)
app.show("Counter")  # registered under the inferred prefix
```

Raises `ValueError` immediately if the view file doesn't end in
`_View.yaml`, the `ViewModel`'s own defining file doesn't end in
`_ViewModel.py`, or the two prefixes don't match -- catching a
mismatched pair at load time rather than a cryptic failure later when a
handler name doesn't resolve. `App.register(name, view, viewmodel)`
stays available directly for the real cases `load()` doesn't cover (a
`ViewModel` that needs a live reference to `App` itself at construction
time, e.g. to call `app.show(...)` from its own handler -- see
`examples/multi_screen/`).

`app.py` is the real entry point: it loads (or registers) each pair and
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
- App-level state stores shared across screens, routing beyond a plain
  named `App.show(name)` (history/back-stack, URL-style deep links), a
  `tesserae new` CLI scaffolding tool.
- Publishing to PyPI (not relevant until there's a real, wider vertical
  slice worth shipping).
