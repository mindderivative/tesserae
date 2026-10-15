# Tesserae

**Write desktop apps in Python and YAML.** A Tesserae app is **YAML views** (what the screen looks
like), each paired with a Python **ViewModel** (what it does), drawn by the
[Tesserae Render Engine](https://github.com/mindderivative/tre) (`tre`): rendering, layout, animation
and accessibility in Rust underneath, which you never have to touch.

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

Tesserae is on PyPI as [`tesserae-ui`](https://pypi.org/project/tesserae-ui/), pre-alpha, and runs on
Linux, macOS and Windows.

## What you get

- **Views and ViewModels.** A view is YAML: a tree of nodes, each a `widget:`. A ViewModel is Python, and serves the
  views that name it. A view with `params:` is a component, called by its name; `for:` and `if:` build lists and choices
  from data. See [The View Language](guide/view-language.md), [Apps & Screens](guide/apps-and-screens.md) and
  [Components & Embedding](guide/components.md).
- **Reactive state.** `Signal`, `Computed`, `Effect` and `ViewModel`: [bindings](guide/bindings.md) keep
  the screen in step with them. See [Reactivity](guide/reactivity.md).
- **Material Design 3.** Every MD3 [component](components/index.md) with its YAML, a
  [stylesheet](stylesheets/index.md) for each, and [themes](themes/index.md): a seed colour makes the
  palette, and light and dark follow the OS. High contrast and reduced motion follow it too.
- **Real desktop behaviour.** [Keyboard, state layers and screen-reader support](guide/interaction.md),
  [overlays](guide/overlays.md), [a window, docks, routed screens and several windows](guide/windows-and-docks.md),
  and [custom title bars](guide/custom-title-bars.md). A layout can follow the window's size class.
- **Fast iteration.** [Hot reload](guide/hot-reload.md) shows an edited view, or a theme, in a running app with its state kept,
  and [editor support](guide/editor-support.md) completes and checks your YAML.
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

You always give Tesserae file paths or names: views, images, themes, stylesheets and fonts. Tesserae reads, parses and
decodes them itself and hands `tre` only data. Every error names the file, line and column you wrote, and the nearest
name when you misspelt one.
