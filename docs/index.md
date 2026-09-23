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
- **`Repeater`** -- automatic keyed add/remove diffing over a list
  `Signal`, no hand-rolled bookkeeping.
- **A full reactivity layer** -- `Signal`, plus `tre`'s own richer
  `Computed`/`Effect`/`batch`/`untrack`, re-exported unmodified.
- **An enforced naming convention** -- every real view is a
  `*_View.yaml` + `*_ViewModel.py` pair, checked at load time, not
  discovered as a cryptic failure later.

## Where to go next

- **[Installation](installation.md)** -- set up a development
  environment (Tesserae depends on `tre` as a local editable checkout
  for now).
- **[Getting Started](getting-started.md)** -- build and run your
  first screen in a few lines.
- **[Guide](guide/apps-and-screens.md)** -- apps and screens,
  components, lists, reactivity, and the naming convention that ties
  it together.
- **[API Reference](api/index.md)** -- every real, public class and
  function.
- **[Architecture](architecture.md)** -- how Tesserae layers on top of
  `tre`, and what's real vs. planned.

## Project status

See [`BUILD_TRACKER.md`](https://github.com/mindderivative/tesserae/blob/main/BUILD_TRACKER.md)
in the repository for the complete, phase-by-phase build history.
