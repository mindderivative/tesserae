# Tesserae

**Write desktop apps in Python and YAML.** A Tesserae app is **YAML views** (what the screen looks like), each paired with a Python
**ViewModel** (what it does), drawn by the [Tesserae Render Engine](https://github.com/mindderivative/tre) (`tre`): a Rust/Python hybrid
for rendering, layout, animation and accessibility.

Tesserae's own shape follows [pyCopper](https://github.com/mindderivative/pycopper) (an earlier, standalone framework by the same author):
app authors write views, not Python widget-class trees, and a plain `Signal`-driven MVVM layer keeps them in step.

**Status: pre-alpha.** The [documentation](https://mindderivative.github.io/tesserae/) is the reference, and the
[changelog](https://mindderivative.github.io/tesserae/changelog/) says what each release changed.

```yaml
# Counter_View.yaml
name: Counter
widget: Container
style: {flex_direction: vertical, gap: 12, padding: 24, background: surface}
children:
  - widget: Text
    name: label
    text: "Count: {{ count }}"
    typography_role: headline_medium
    style: {foreground: on_surface}
  - {widget: Button, name: button, label: Count, style: {width: 120}, handlers: {on_click: increment}}
```

```python
# Counter_ViewModel.py
from tesserae import Signal, ViewModel

class CounterViewModel(ViewModel):
    views = "Counter"             # the view it serves

    def __init__(self):
        super().__init__()
        self.count = Signal(0)

    def increment(self):
        self.count.update(lambda n: n + 1)
```

```python
# app.py
from tesserae import App
from Counter_ViewModel import CounterViewModel

app = App(width=240, height=160, title="Counter", search=["."])
app.bind(CounterViewModel)
app.open_view("Counter")      # Counter_View.yaml
app.show("Counter")
app.run()
```

```bash
python app.py
```

A view is a tree of `widget:` nodes. A view with `params:` is a component, called by its name; `for:` and `if:` build lists and choices from
data; every Material Design 3 component ships as such a view. See the
[view language](https://mindderivative.github.io/tesserae/guide/view-language/), the
[component pages](https://mindderivative.github.io/tesserae/components/) and the
[Getting Started](https://mindderivative.github.io/tesserae/getting-started/) walk-through, then the
[Tasks tutorial](https://mindderivative.github.io/tesserae/tutorial/).

## Files: Tesserae reads them, `tre` gets data

You give Tesserae file paths or names: views, images, themes, stylesheets and fonts. Tesserae reads, parses, decodes and checks them itself and
hands `tre` only data (a finished view on `tre`'s building blocks, RGBA pixels and font bytes). Every error names the file, line and column you
wrote, and the nearest name when you misspelt one.

Tesserae logs through [loguru](https://loguru.readthedocs.io/): hot
reloads, failed reloads naming the file, and warnings. Call
`tesserae.configure_logging()` in `app.py` for its console format, or
`logger.disable("tesserae")` to silence it.

## Install

```bash
pip install tesserae-ui
```

That's all: it installs Tesserae and everything it needs, `tre`'s engine
included, as prebuilt wheels. It needs **Python 3.12 or newer**, on Linux
x86-64, macOS on Apple silicon or Windows x64 (elsewhere, pip builds `tre`
from source, which needs Rust). The PyPI name is `tesserae-ui` (`tesserae`
on PyPI is an unrelated project); the import name is `tesserae`. Start an
app with `tesserae new myapp`. What's new: the [changelog](https://mindderivative.github.io/tesserae/changelog/).

## Release an app

```bash
pip install "tesserae-ui[build]"
tesserae build --check
```

makes the app one executable, `dist/myapp` (`.exe` on Windows), which its
users run with nothing else installed. `tesserae build --installer` makes
each platform's installer instead: a `.dmg` on macOS, a setup `.exe` on
Windows, and an AppImage, `.deb`, pacman package, `.rpm` and Flatpak on
Linux. Build on each platform you release for; signing with your own
certificates, and the rest, is in [Releasing Your App](https://mindderivative.github.io/tesserae/guide/releasing/).

## Install (development)

Tesserae needs **`tre` 0.5.6 or newer, below 0.6**, which is on PyPI as
[`tesserae-engine`](https://pypi.org/project/tesserae-engine/) (still
`import tre`). Installing Tesserae installs it:

```bash
pip install -e ".[dev]"
```

Coming from a GitHub `tre-...` wheel, run `pip uninstall tre` first: pip
treats `tesserae-engine` as a different project, and both would own the
`tre` package. See the [installation guide](https://mindderivative.github.io/tesserae/installation/)
for testing against an unreleased `tre` checkout.

## Examples

```bash
python examples/getting_started/declarative/step4/app.py   # the counter above
python examples/tutorial/step5/app.py                      # the Tasks tutorial
python examples/counter/app.py                             # one view and the ViewModel that serves it
python examples/multi_screen/app.py [settings]             # two screens, shared state, routes and a deep link
python examples/todo_list/app.py                           # a list kept by `for:` and `key:` from one Signal
python examples/custom_title_bar/app.py                    # a window whose title bar the app draws
python examples/window_dock/app.py                         # a window with a title bar, a rail, docked panels and routed screens
python examples/typing_effects/app.py --interactive        # flash, fade-in and a gliding caret on a text field
```

Each checks itself with real dispatched clicks and renders a few frames headless (`--interactive`, where there is one, keeps the window open).

## Reactivity

`Signal`, `Computed`, `Effect`, `batch` and `ViewModel` are Tesserae's own (`tesserae.reactive`):

```python
from tesserae import Computed, Effect, batch

total = Computed(lambda: price.get() * quantity.get())  # derived, cached
Effect(lambda: print(f"total is now {total.get()}"))     # side effect only

def apply_discount():
    price.update(lambda p: p * 0.9)
    quantity.set(quantity.get() + 1)

batch(apply_discount)  # total recomputes once, not twice
```

A `{{ }}` binding in a view can read a `Signal` or a `Computed` directly. See
[Reactivity](https://mindderivative.github.io/tesserae/guide/reactivity/).

## Starting an app

`tesserae new notes` makes a runnable app; `--window` makes the app one window view with a rail and two routed screens.
`tesserae add screen Settings` adds a screen. See [Getting Started](https://mindderivative.github.io/tesserae/getting-started/) and the
[CLI](https://mindderivative.github.io/tesserae/guide/cli/).

## Architecture

See [the architecture page](https://mindderivative.github.io/tesserae/architecture/). To work on Tesserae itself, [DEVELOPING.md](DEVELOPING.md).

**Releasing:** publishing a GitHub Release runs `.github/workflows/release.yml`.
It checks that the tag matches the version and that no dependency is PyPI's
unrelated `tre`, tests the built wheel, and uploads it with trusted
publishing once the `pypi` environment's reviewer approves (0.1.0, 2026-09-28).

Every known gap has a scoped issue: [Tesserae's issues](https://github.com/mindderivative/tesserae/issues).
