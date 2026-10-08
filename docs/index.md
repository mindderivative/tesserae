# Tesserae

**Write desktop apps in Python and YAML.** A Tesserae app is **YAML views** (what the screen looks
like), each paired with a Python **ViewModel** (what it does), drawn by the
[Tesserae Render Engine](https://github.com/mindderivative/tre) (`tre`): rendering, layout, animation
and accessibility in Rust underneath, which you never have to touch.

```yaml
# Counter_View.yaml
id: root
kind: Container
style: {flex_direction: vertical, gap: 12, padding: 24, background: surface}
children:
  - id: label
    kind: Text
    text: {content: "Count: 0", typography_role: headline_medium}
    style: {foreground: on_surface}
    bindings: {text: "{{ label_text.get() }}"}
  - id: button
    component: ButtonFilled
    with: {label: Count, width: 120, height: 40, corner_radius: 20}
    handlers: {on_click: increment}
```

```python
# Counter_ViewModel.py
from tesserae import Computed, Signal, ViewModel

class CounterViewModel(ViewModel):
    def __init__(self, view):
        self.count = Signal(0)
        self.label_text = Computed(lambda: f"Count: {self.count.get()}")
        super().__init__(view)

    def increment(self):
        self.count.update(lambda n: n + 1)
```

```python
# app.py
from tesserae import App
from Counter_ViewModel import CounterViewModel

app = App(width=240, height=160, title="Counter")
app.load("Counter_View.yaml", CounterViewModel)
app.show("Counter")
app.run(hot_reload=True)   # edit the view while the app runs
```

Tesserae is on PyPI as [`tesserae-ui`](https://pypi.org/project/tesserae-ui/), pre-alpha, and runs on
Linux, macOS and Windows.

## What you get

- **Screens and components.** An `App` owns the window and a registry of screens; a screen is a view and
  ViewModel pair, checked by [naming convention](guide/naming-convention.md). Embed other pairs as
  [components](guide/components.md), or reuse structure as [fragments](guide/component-fragments.md).
- **Reactive state.** `Signal`, `Computed`, `Effect` and `ViewModel`: [bindings](guide/bindings.md) keep
  the screen in step with them. See [Reactivity](guide/reactivity.md) and [Repeater](guide/repeater.md).
- **Material Design 3.** Every MD3 [component](components/index.md) with its YAML, a
  [stylesheet](stylesheets/index.md) for each, and [themes](themes/index.md): a seed colour makes the
  palette, and light and dark follow the OS.
- **Real desktop behaviour.** [Keyboard, state layers and screen-reader support](guide/interaction.md),
  [overlays](guide/overlays.md), a [window, docks and embedded views](guide/windows-and-docks.md), and
  [custom title bars](guide/custom-title-bars.md).
- **Fast iteration.** [Hot reload](guide/hot-reload.md) updates a running app when a view, a stylesheet or
  a theme changes, and [editor support](guide/editor-support.md) completes and checks your YAML.
- **Shipping.** `tesserae build` makes one executable, or an installer: [Releasing](guide/releasing.md).

## Where to go

| | |
| --- | --- |
| [Installation](installation.md) | `pip install tesserae-ui` |
| [Getting Started](getting-started.md) | Your first window and node, declaratively and from Python |
| [Tutorial](tutorial.md) and [the same as a project](tutorial-project.md) | A Tasks app in six steps: components, styling, screens, a custom window; in one flat folder, then as a `tesserae new` project |
| [Guide](guide/apps-and-screens.md) | How each part works |
| [Components](components/index.md) and [Stylesheets](stylesheets/index.md) | Every MD3 component, its YAML and its look |
| [Themes](themes/index.md) | Colour, shape, type, light and dark |
| [Python API](api/python.md) and [YAML reference](api/yaml.md) | Every class, function and key |
| [Architecture](architecture.md) | How it fits together |
| [Changelog](changelog.md) and [Migrating](migration.md) | What changed, release by release |

## Files: Tesserae reads them, `tre` gets data

You always give Tesserae file paths: views, fragments, `include:`d files, images, themes, stylesheets and
fonts. Tesserae reads, parses, decodes and watches them itself and hands `tre` only data. Every error
names the file you wrote, and a view and everything it is built from can be hot-reloaded.
