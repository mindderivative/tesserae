# Tesserae

A declarative Python GUI framework, powered by the [Tesserae Render
Engine](https://github.com/mindderivative/tre) (`tre`) -- a Rust/Python
hybrid rendering, layout, animation, and accessibility engine.

Tesserae's own shape follows [pyCopper](https://github.com/mindderivative/pycopper)
(an earlier, standalone framework by the same author, powered by a direct
GLFW/wgpu-py stack instead): app authors write **YAML views**, not Python
widget-class trees, paired with a Python `ViewModel` per view -- a plain
`Signal`-driven MVVM layer, not a whole-tree reconcile.

**Status: pre-alpha, five vertical slices.** `App`/`Signal`/`View`/
`ViewModel`/`Component`/`Repeater` exist and are exercised end to end by
`examples/counter/` (a single screen), `examples/multi_screen/` (two
screens, switched via `App.show()` from inside a real dispatched
handler), `examples/todo_list/` (a real dynamic list, one list
`Signal` as the single source of truth, `Repeater` keeping components in
sync automatically), and `examples/app_shell/` and
`examples/app_shell_file/` (an app shell with docked panels, built in
Python and from a `*_Shell.yaml`). `Signal`/`Computed`/`Effect`/`batch`/`untrack`/
`ViewModel` are Tesserae's own (M35) -- see Reactivity below. The MD3 widget catalog
is real too: 67 declarative `component:` fragments for `*_View.yaml`
files, plus `tesserae.widgets` for building widgets from Python. See the
[documentation](https://mindderivative.github.io/tesserae/) for both.

## Files: Tesserae reads them, `tre` gets data

You give Tesserae file paths -- views, component fragments, `include:`d
files, images, themes, stylesheets, fonts. Tesserae reads, parses,
decodes and watches them itself, and hands `tre` only data: a finished
view built by Tesserae's own compiler onto `tre`'s building blocks
(M37), RGBA pixels and font bytes (`register_font`). Tesserae never gives
`tre` a file path.

That's what lets Tesserae resolve `include:` and `component:` together,
name the right file in every error, warn when a font would silently
fall back, and hot-reload a running app when any of those files change
(`app.run(hot_reload=True)`) -- views, includes, fragments and images,
components added at run time (every row of a `Repeater`, in place), and
the app's theme and stylesheet files.

Tesserae logs through [loguru](https://loguru.readthedocs.io/): hot
reloads, failed reloads naming the file, and warnings. Call
`tesserae.configure_logging()` in `app.py` for its console format, or
`logger.disable("tesserae")` to silence it.

## Install

Tesserae is on PyPI as [`tesserae-ui`](https://pypi.org/project/tesserae-ui/)
(imported as `tesserae`; `tesserae` on PyPI is an unrelated project):

```bash
pip install tesserae-ui
```

## Install

```bash
pip install tesserae-ui
```

That's all: it installs Tesserae and everything it needs, `tre`'s engine
included, as prebuilt wheels. It needs **Python 3.12 or newer**, on Linux
x86-64, macOS on Apple silicon or Windows x64 (elsewhere, pip builds `tre`
from source, which needs Rust). The import name is `tesserae`; start an app
with `tesserae new myapp`. What's new: the [changelog](https://mindderivative.github.io/tesserae/changelog/).

## Install (development)

Tesserae needs **`tre` 0.4.2 or newer**, which is on PyPI as
[`tesserae-engine`](https://pypi.org/project/tesserae-engine/) (still
`import tre`). Installing Tesserae installs it:

```bash
pip install -e ".[dev]"
```

Coming from a GitHub `tre-...` wheel, run `pip uninstall tre` first: pip
treats `tesserae-engine` as a different project, and both would own the
`tre` package. See the [installation guide](https://mindderivative.github.io/tesserae/installation/)
for testing against an unreleased `tre` checkout.

## The real vertical slices

```bash
python examples/counter/app.py
python examples/multi_screen/app.py
python examples/todo_list/app.py
python examples/app_shell/app.py
python examples/app_shell_file/app.py
```

`counter/`: a real `Signal`-bound counter -- a `Counter_View.yaml` +
`Counter_ViewModel.py` pair, loaded via `App.load()` and shown via
`App`, a real dispatched click incrementing a bound label, then a
genuine render loop.

`multi_screen/`: two independent screens (`Home`/`Settings`), each its
own `*_View.yaml`/`*_ViewModel.py` pair: Home navigates to Settings and
Settings goes `back()` (M66), from inside each screen's own real
dispatched `on_click` handler --
proving a switch works even when triggered *reentrantly*, from the
handler `App.show` itself is dispatching into. Both screens show the
app's shared state (`App(state=...)`, M65), which each handler writes, and
routes make `python app.py settings` a deep link.

`todo_list/`: a real dynamic list, driven by `tesserae.Repeater` -- one
list `Signal` of stable item ids (`TodoViewModel.items`) is the single
source of truth; adding a "to-do" appends an id, removing one drops it
-- the `Repeater` keeps exactly one independent `TodoItem` `Component` +
`ViewModel` (`TodoItem_View.yaml`/`TodoItem_ViewModel.py`) alive per id,
instantiating/removing automatically. Proves the full real multi-
instance lifecycle: add, toggle a two-way-bound checkbox, remove
(mutating the shared `items` `Signal` from *inside* the item's own
dispatched handler), add again, all through real dispatched clicks and
one live window.

`app_shell/`: an app framed by a top app bar, a navigation rail and a
status bar, with tool panels docked left, right and bottom and screens as
center tabs (M45), all built in Python with `tesserae.shell.AppShell`
and `tesserae.docking.Dock`.

`app_shell_file/`: the same studio declared in `Studio_Shell.yaml` and
built by `app.load_shell()` (M52). Its panels are views named like
screens, found next to the shell file; its rail shows screens; and the
shell file itself is hot-reloaded.

## Components

`tesserae.instantiate(parent, path, viewmodel_cls, into, *args,
**kwargs)` embeds another view's own YAML as a real, independent
`Component` with its own `ViewModel`, built in its host's window with
the host's theme and stylesheet. `parent` is a `View`
or another `Component` (they nest); `into` is the `Node` to embed under
(e.g. `view.node("item_list")`); extra positional/keyword args are
forwarded to `viewmodel_cls(component, *args, **kwargs)` -- the real,
common case for a component that needs its own data or a callback to
notify its parent when it removes itself (see `examples/todo_list/`).

```python
component, viewmodel = instantiate(view, "Card_View.yaml", CardViewModel, container)
```

Call this once per instance for multiple simultaneous instances (a list
where each row is its own independent component) -- each call is fully
independent, even reusing the same `path` repeatedly. `component.remove()`
tears the instance down for real, unsubscribing its own `Signal`s first.

## Repeater

`Repeater` automates the add/remove bookkeeping `instantiate`/
`Component.remove()` otherwise need by hand: point it at a list `Signal`
and it keeps exactly one `Component` + `ViewModel` alive per item
currently present, diffed by a real key.

```python
from tesserae import Repeater, Signal

items = Signal([])  # the single source of truth
repeater = Repeater(view, items, "Card_View.yaml", CardViewModel, container)

items.update(lambda lst: [*lst, new_id])              # adds one
items.update(lambda lst: [i for i in lst if i != id])  # removes one
```

`key` (default: the item itself) and `args` (default: `lambda item:
(item,)`, forwarded to `viewmodel_cls(component, *args)`) are both
overridable for items that are dicts/dataclasses rather than bare ids
-- see `examples/todo_list/`'s own `Todo_ViewModel.py`.

**Real, deliberate scope boundary:** `Repeater` only ever adds or
removes instances to match the *set* of keys present -- it never
reorders an already-present key's own position, and never re-applies a
changed item's own data to an existing instance (that's the item's own
`ViewModel`'s job, via its own `Signal`s). Reordering isn't supported
for the same real reason `tre`'s own `Reconciler` doesn't: `engine_core
::Tree` has no child-reorder primitive today. `Repeater.remove()` tears
every remaining instance down and unsubscribes, mirroring `Component
.remove()`'s own real teardown ordering.

## Reactivity

Tesserae's reactivity (`tesserae.reactive`, taken over from `tre` in
M35 with the same behaviour):

```python
from tesserae import Computed, Effect, batch

total = Computed(lambda: price.get() * quantity.get())  # derived, cached
Effect(lambda: print(f"total is now {total.get()}"))     # side effect only

def apply_discount():
    price.update(lambda p: p * 0.9)
    quantity.set(quantity.get() + 1)

batch(apply_discount)  # total recomputes once, not twice
```

`Computed`/`Effect` duck-type against `Signal`'s own subscribe shape, so
a `{{ }}` binding can point straight at a `Computed.get()` value with no
special handling. See `tre`'s own `examples/reactivity.py` for a full,
live-window proof of `Computed`-of-`Computed` chains, `Effect`, and
`batch()` composing together.

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
stays available directly for a view and ViewModel built by hand. A
ViewModel doesn't need the app passed in: on the app's window it has
`self.app`, and `self.state` for state the screens share
(`App(state=...)`, M65; see `examples/multi_screen/`).

`app.py` is the real entry point: it loads (or registers) each pair and
calls `App.show(name)` to pick which one is currently on screen --
switching later (another `App.show(other_name)` call, typically from a
registered handler) doesn't re-parse the YAML or re-construct the
`ViewModel`; both stay alive, `Signal` subscriptions intact, for the
life of the app.

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md).

## Starting an app

`tesserae new notes` makes a runnable app (`app.py` and a `Home` pair,
with shared state and routes); `--shell` adds an app shell file and a
Settings screen. `tesserae add screen Settings` adds a pair and loads and
routes it in `app.py` (M67). See [Getting Started](https://mindderivative.github.io/tesserae/getting-started/).

The items once listed here as deferred are done: shared state (M65),
routing with a history and deep links (M66), and this CLI (M67).

**Releasing:** publishing a GitHub Release runs `.github/workflows/release.yml`.
It checks that the tag matches the version and that no dependency is PyPI's
unrelated `tre`, tests the built wheel, and uploads it with trusted
publishing once the `pypi` environment's reviewer approves (0.1.0, 2026-09-28).

Every known gap has a scoped issue: [Tesserae's issues](https://github.com/mindderivative/tesserae/issues).
