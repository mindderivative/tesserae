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

**Status: pre-alpha, 0.3.0.** Tesserae is on PyPI as
[`tesserae-ui`](https://pypi.org/project/tesserae-ui/) and runs on Linux,
macOS and Windows. Screens, components, the MD3 widget catalog, themes,
hot reload, app shells with docking, custom title bars, and building an
app into one executable or an installer are all real, exercised by the
examples and the test suite. [Getting Started](getting-started.md) takes
you from a fresh install to your first window.

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
  every widget built by Tesserae from `tre`'s building blocks, for
  widgets built dynamically from Python.
- **`Repeater`** -- automatic keyed add/remove diffing over a list
  `Signal`, no hand-rolled bookkeeping.
- **Hot reload** -- `app.run(hot_reload=True)` updates a running app in
  place when a view, or anything it's built from, changes on disk --
  and when a theme or stylesheet file does. See
  [Hot Reload](guide/hot-reload.md).
- **Themes, stylesheets and custom fonts** -- loaded from files, with a
  warning when a font would silently fall back. See
  [Themes & Fonts](guide/themes-and-fonts.md).
- **MD3 controls** -- checkboxes, radio buttons, switches, sliders, spin
  boxes, progress and loading indicators and the time picker dial, drawn
  by Tesserae and working with the pointer, keyboard and screen readers.
  See [Controls](guide/controls.md).
- **Interaction and accessibility** -- a node with `on_click` is a
  keyboard-reachable button with MD3's hover tint, press ripple and
  focus ring, and `a11y:` labels it for screen readers -- a label can
  follow the ViewModel, like any binding. See
  [Interaction & Accessibility](guide/interaction.md).
- **An app shell with docking** -- a top bar, navigation and status bar
  around docked panels the user drags between zones and resizes, with
  screens as tabs if you like. See [App Shell & Docking](guide/app-shell.md).
- **A full reactivity layer** -- `Signal`, `Computed`, `Effect`,
  `batch`, `untrack` and `ViewModel`, Tesserae's own since M35. See
  [Reactivity](guide/reactivity.md).
- **Custom title bars** (0.3.0) -- an undecorated window whose title bar
  the app draws: `kind: TitleBar` in a view, the app shell's top bar, or
  a bar of your own with `window_region` and the `window.*` handlers,
  with a window border, light and dark theming, and macOS's traffic
  lights. See [Custom Title Bars](guide/custom-title-bars.md).
- **`tesserae new`, `tesserae add` and `tesserae build`** -- start an app
  and add screens from the command line, and build an app into one
  executable, or a `.dmg`, setup `.exe`, AppImage, `.deb`, `.rpm`,
  pacman package or Flatpak. See [Getting Started](getting-started.md)
  and [Releasing Your App](guide/releasing.md).
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

- **[Installation](installation.md)** -- `pip install tesserae-ui`, and
  setting up a checkout to work on Tesserae itself.
- **[Getting Started](getting-started.md)** -- from a fresh Linux
  install to your first window and node, declaratively and from Python.
- **[Guide](guide/apps-and-screens.md)** -- apps and screens,
  components, [declarative component fragments](guide/component-fragments.md),
  the [widget catalog](guide/widget-catalog.md), lists, reactivity,
  and the naming convention that ties it together.
- **[API Reference](api/index.md)** -- every real, public class and
  function.
- **[Architecture](architecture.md)** -- how Tesserae layers on top of
  `tre`, and what's real vs. planned.

## Project status

Work is planned and tracked, release by release, in the GitHub project
[Tesserae UI Framework](https://github.com/users/mindderivative/projects/2):
each release is a milestone whose issues are its steps. The complete,
phase-by-phase history of everything before it (milestones M1–M82, up to
0.2.1) is in [`BUILD_TRACKER_ARCHIVE_0.2.md`](https://github.com/mindderivative/tesserae/blob/main/BUILD_TRACKER_ARCHIVE_0.2.md);
0.3.0's (custom windowing) is in the project, under
[#24](https://github.com/mindderivative/tesserae/issues/24). What changed in
each release is in the [changelog](changelog.md).
