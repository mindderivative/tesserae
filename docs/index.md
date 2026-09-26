# Tesserae

**A declarative Python GUI framework, powered by the [Tesserae Render
Engine](https://github.com/mindderivative/tre) (`tre`).**

Write desktop applications entirely in Python and YAML -- `tre` handles
rendering, layout, animation, and accessibility in Rust underneath, and
Tesserae is the layer that means you never have to touch it directly.
Tesserae's own shape follows [pyCopper](https://github.com/mindderivative/pycopper)
(an earlier, standalone framework by the same author, powered by a
direct GLFW/wgpu-py stack instead): app authors write **YAML views**,
paired with a Python `ViewModel` per view -- a plain `Signal`-driven
MVVM layer, not a whole-tree reconcile.

**Status: pre-alpha.** `App`/`Signal`/`View`/`ViewModel`/`Component`/
`Repeater`/`Computed`/`Effect`/`batch`/`untrack` are real, exercised
end to end by three real vertical-slice examples. See
[Getting Started](getting-started.md) to build your first screen.

## What's built

- **`App`** -- a single entry point owning a named `(View, ViewModel)`
  screen registry and one live window; switching screens never
  re-parses YAML or re-bootstraps a `ViewModel`.
- **Real component embedding** (`instantiate`/`Component`) -- embed
  another view's own YAML as an independent, reusable component with
  its own `ViewModel`; multiple simultaneous instances stay fully
  independent.
- **Declarative component fragments** -- `component: Name` / `with:`
  / `repeat:` in a `*_View.yaml` expands, at load time, to one of 67
  built-in MD3 widget fragments (buttons, cards, chips, progress
  indicators, and more), so a screen never has to hand-write a
  widget's raw `WidgetSpec` shape.
- **A full imperative MD3 widget catalog** (`tesserae.widgets`) --
  thin, faithful delegates to `tre`'s own `Window.add_*` factories,
  for widgets built dynamically from Python.
- **`Repeater`** -- automatic keyed add/remove diffing over a list
  `Signal`, no hand-rolled bookkeeping.
- **Hot reload** -- `app.run(hot_reload=True)` updates a running app in
  place when a view, or anything it's built from, changes on disk --
  and when a theme or stylesheet file does. See
  [Hot Reload](guide/hot-reload.md).
- **Themes, stylesheets and custom fonts** -- loaded from files, with a
  warning when a font would silently fall back. See
  [Themes & Fonts](guide/themes-and-fonts.md).
- **Interaction and accessibility** -- a node with `on_click` is a
  keyboard-reachable button with MD3's hover tint, press ripple and
  focus ring, and `a11y:` labels it for screen readers. See
  [Interaction & Accessibility](guide/interaction.md).
- **A full reactivity layer** -- `Signal`, `Computed`, `Effect`,
  `batch`, `untrack` and `ViewModel`, Tesserae's own since M35. See
  [Reactivity](guide/reactivity.md).
- **An enforced naming convention** -- every real view is a
  `*_View.yaml` + `*_ViewModel.py` pair, checked at load time, not
  discovered as a cryptic failure later.

## Files: Tesserae reads them, `tre` gets data

You always give Tesserae file paths: views, component fragments,
`include:`d files, images, themes, stylesheets and fonts. Tesserae
reads, parses, decodes and watches them itself, and hands `tre` only
data -- a finished view spec, theme and stylesheet dicts, image pixels
and font bytes. Tesserae never gives `tre` a file path, so every error
names the file you wrote, and a view and everything it's built from
(includes, fragments, images) can be hot-reloaded, along with the app's
theme and stylesheet files.

If you use `tre` directly alongside Tesserae, keep to the same rule:
pass `tre` the `*_spec=` forms (e.g. `load_theme(...)` for
`set_theme`), not paths, and use Tesserae's `ViewWatcher` rather than
`tre`'s `poll_reload`.

## Where to go next

- **[Installation](installation.md)** -- set up a development
  environment (Tesserae depends on `tre` as a local editable checkout
  for now).
- **[Getting Started](getting-started.md)** -- build and run your
  first screen in a few lines.
- **[Guide](guide/apps-and-screens.md)** -- apps and screens,
  components, [declarative component fragments](guide/component-fragments.md),
  the [widget catalog](guide/widget-catalog.md), lists, reactivity,
  and the naming convention that ties it together.
- **[API Reference](api/index.md)** -- every real, public class and
  function.
- **[Architecture](architecture.md)** -- how Tesserae layers on top of
  `tre`, and what's real vs. planned.

## Project status

See [`BUILD_TRACKER.md`](https://github.com/mindderivative/tesserae/blob/main/BUILD_TRACKER.md)
in the repository for the complete, phase-by-phase build history.
