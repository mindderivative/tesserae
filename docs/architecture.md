# Architecture

Tesserae is a Python framework for desktop interfaces. You write screens in YAML and logic in
Python; Tesserae builds the interface and keeps it up to date. It draws nothing itself: the
engine, `tre`, owns the window, layout, painting, text, input and the event loop. Tesserae is
everything above that.

## The layers

```
 your code      app.py (App)   *_View.yaml   *_ViewModel.py   tesserae.widgets
                    |               |               |               |
 Tesserae       registry, ----> spec pipeline       |         controls, composed
                routing         expand -> cascade   |         widgets, overlays,
                    |           -> compiler         |         shell, docking
                    |               |               |               |
                    |         View / Component: nodes, reconciler, bindings
                    |               |      Signal / Computed / Effect (reactive)
                    |          tokens + Theme (colour, shape, type, motion)
                    v               v
 tre            Window: create / set / get / animate / on / show_layer
                (node tree, flex layout, paint, text, input, accessibility)
```

**App code.** [`App`](api/python.md) owns one window and a registry of named screens, each a
`View` plus its `ViewModel`. A `*_ViewModel.py` holds state in `Signal`s and `Computed`s
(`tesserae.reactive`: `Signal`, `Computed`, `Effect`, `batch`, `untrack`, `ViewModel`). The
[naming convention](guide/naming-convention.md) pairs `Foo_View.yaml` with `Foo_ViewModel.py`, and
`App.load` and `instantiate` check the pair. `Repeater` keeps one component per item of a list
`Signal`. See [Apps and screens](guide/apps-and-screens.md) and [Reactivity](guide/reactivity.md).

**The spec pipeline** (`tesserae.spec`) turns files into one finished spec dict:

1. `include:` splices other files in, relative to the including file and confined to its
   directory; `component:`/`with:`/`repeat:` expand a `*_Component.yaml` fragment (the built-in
   MD3 fragments live in `tesserae/spec/components`, or your own `component_dirs`), namespacing
   its ids. See [Component fragments](guide/component-fragments.md).
2. Image `src:` files are decoded to pixels (Pillow).
3. The cascade (`spec/cascade.py`) resolves each node's style. Lowest to highest: the default
   theme's `styles:`, the custom theme's, the view's stylesheet, then the node's inline `style:`.
   Inside a sheet a baseline rule loses to a `kind:` rule, then `classes:` (more classes win),
   then `id:`. Rules are indexed, so a node never scans the whole sheet.
4. The compiler (`spec/build.py`) creates `tre` nodes: `Rect`/`Container` become a `box`, `Text`
   and `Link` a `text`, `Icon` a `path`, `Image` an `image`, `TextField` a `box` around a
   `text_input`. The eight stateful kinds (`Checkbox`, `RadioButton`, `Switch`, `Slider`,
   `CircularProgress`, `LinearProgress`, `LoadingIndicator`, `TimePickerDial`) become
   Tesserae's own controls. Every property is set explicitly, defaults included, so a later
   patch can reset it.

**Tokens and `Theme`.** `tesserae.tokens` holds the MD3 values: the 49 colour roles from a seed
(light and dark, via `materialyoucolor`) with `colors:` overrides, the shape scale, elevation
(as key and ambient shadows), the 15 type roles, and colour-string parsing. `tesserae.Theme` is
one resolved theme, which style values like `primary`, `extra_large`, `level_3` or
`typography_role` resolve through. Widgets and views follow their app's theme: `App.set_dark`,
the OS light/dark switch and `App.set_theme_specs` re-colour them in place. See
[Themes](themes/index.md) and [Stylesheets](stylesheets/index.md).

**Widgets.** `tesserae.controls` are the stateful MD3 controls (`Checkbox`, `Switch`, `Slider`,
`SpinBox`, progress indicators, the time dial); each keeps its state in `Signal`s and fires
`on_change` for the user's edits only. `tesserae.widgets` has one function per MD3 widget, built
from a fragment into a `Widget` with `.node` and its parts. `tesserae.interaction` draws what the
engine does not: state layers, the ripple and focus rings. `tesserae.a11y` sets roles and states.
`tesserae.overlays` (`Dialog`, `Menu`, `Snackbar`, `Tooltip`, `Popover`, `SearchView`,
`NavigationDrawer`) show nodes with `window.show_layer`. `AppShell` frames the screens with a top
bar, navigation, a status bar and docked zones, and `Dock` manages the panels in those zones.
See the [widget catalog](guide/widget-catalog.md), [controls](guide/controls.md),
[overlays](guide/overlays.md), [app shell](guide/app-shell.md) and the
[component gallery](components/index.md).

**The engine, `tre`.** It provides the node tree (`create`, `set`, `get`, `animate`, `on`,
`add_child`, `insert_child`, `remove`, `destroy`), layout, painting, text, input, accessibility,
layers and the render loop. It has no widgets, theme, stylesheets or reactivity of its own.

**What Tesserae hands `tre`: specs and bytes, never files.** Tesserae reads, parses, decodes and
watches every file. `tre` receives nodes built through its API, colours as RGBA tuples, image
pixels as `rgba` on an `image` node, and font files as bytes (`register_font`). It is never
given a path.

## A screen load

`app.load("Counter_View.yaml", CounterViewModel)`:

1. The naming convention is checked (`Counter_View.yaml` with `Counter_ViewModel`).
2. `build_view_spec` runs the pipeline: file, `include:`, components, images, a finished dict.
3. `View` compiles it with the app's theme and stylesheet into nodes in the app's window, then
   wires bindings and handlers.
4. The `ViewModel` attaches to the view and the pair is registered as `"Counter"`.
5. `app.show("Counter")` attaches the view's root to `window.root` and detaches the previous
   screen's root. A detached screen keeps its state and bindings. Nothing is parsed again.
   `navigate`, `route` and `back` add a history of named screens on top of `show`.

## A signal change

A binding such as `text: "{{ vm.count.get() }}"` is a restricted expression
(`tesserae.binding`: attribute access, indexing, comparison, arithmetic, boolean logic and
zero-argument calls; never `eval`). `View` evaluates it inside a recording frame of
`tesserae.reactive`, which notes every `Signal` or `Computed` it reads. When one changes
(`vm.count.set(5)`), a subscriber re-evaluates the expression, and `View` `set`s the node
property only if the value differs. `batch` defers notifications so each subscriber runs once.
Going the other way, a handler (`on_click: increment`) is a `node.on(...)` listener that calls
a ViewModel method; `two_way:` writes a user's edit back to a `Signal`. See
[Bindings](guide/bindings.md).

## Reconciling and hot reload

`View.reconcile` matches children by `id`: an unchanged node keeps its identity, focus and
running animations, a changed one is patched in place, a changed kind is rebuilt, a missing one
is destroyed, and children follow the new spec's order. Bindings and handlers are wired again
after each update, without doubling listeners.

`App.run(hot_reload=True)` uses this. A `ViewWatcher` per screen (`watchfiles`, on a background
thread) watches the view file and everything it was built from: includes, fragments and
images. On a change it reruns the same pipeline off the main thread and hands the result to the
event loop through `tre`'s thread-safe loop handle, which reconciles the live view. Theme,
stylesheet, component and shell files are watched the same way. A failed reload is logged and the
app keeps running. See [Hot reload](guide/hot-reload.md).

## Design rules

- **Specs and bytes, never files.** See above; it keeps all file handling and watching in one
  place.
- **YAML is data.** No `eval`: expressions are a small checked grammar and handlers name
  ViewModel methods. Mistakes (an unknown property, a missing `foreground`, a mismatched
  naming pair) fail at load with a message that names the spot.
- **One source of truth per state.** State lives in `Signal`s; the UI is a function of them.
  A programmatic `set` never fires `on_change`, so reloads and bindings do not echo back.
- **Everything is built from the engine's primitives** (`create`, `set`, `on`,
  `show_layer`), so the engine stays small and each widget's look sits in a stylesheet you can
  override.
- **Themes are data.** Seed colour, `colors:`, `components:` shape and elevation, and
  `typography:` overrides in a theme file re-resolve the cascade and re-colour live views.
- **Screens are long-lived.** Switching screens detaches, never rebuilds.
- **Proven against recorded answers.** Binding, cascade, colour and tree-building tests replay
  reference results recorded from `tre` (`tests/reference/*.json`), so a regression in those
  parts fails a test.

For the full list of names and signatures see the [Python API](api/python.md) and the
[YAML reference](api/yaml.md).
