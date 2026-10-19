# Architecture

Tesserae is a Python framework for desktop interfaces. You write screens in YAML and logic in
Python; Tesserae builds the interface and keeps it up to date. It draws nothing itself: the
engine, `tre`, owns the window, layout, painting, text, input and the event loop. Tesserae is
everything above that.

## The layers

```
 your code      app.py (App)   *_View.yaml   *_ViewModel.py   tesserae.widgets
                    |               |               |               |
 Tesserae       registry,  ---> parse -> compose -> lower     controls, composed
                routing,        (nodes)  (instances) (spec)   widgets, overlays,
                bindings            |        |      |         docking
                    |               |        +------+---> View: nodes, reconciler
                    |               |      Signal / Computed / Effect (reactive)
                    |          tokens + Theme (colour, shape, type, motion) + rule sheets
                    v               v
 tre            Window: create / set / get / animate / on / show_layer
                (node tree, flex layout, paint, text, input, accessibility)
```

**App code.** [`App`](api/python.md) owns one window and a registry of named screens. A
`*_ViewModel.py` holds state in `Signal`s and `Computed`s (`tesserae.reactive`: `Signal`,
`Computed`, `Effect`, `batch`, `untrack`, `ViewModel`) and the methods a view's handlers call. A
ViewModel serves the views that name it: `views = "Counter"` in the class, `name: Counter` at the top of
the view, `app.bind(CounterViewModel)` and `app.open_view("Counter")` to join and open them. One instance
serves every view that names it. See [Apps and screens](guide/apps-and-screens.md), the
[naming convention](guide/naming-convention.md) and [Reactivity](guide/reactivity.md).

**The spec pipeline** (`tesserae.spec`) turns a view file into live nodes in four steps:

1. **Parse** (`spec/nodes.py`). A `*_View.yaml` is read with its line and column kept. Every key of every
   node is checked against the node's widget, every property against its declaration, and every `{{ }}`
   expression and handler is compiled by `tesserae.expr`. The first mistake is an error that names the
   file, line and column. A widget is a built-in (`spec/builtin_widgets.py`), or a view: one with `params:`
   is declared from them, and found by name in the project or among the views Tesserae ships
   (`tesserae/views`, with a `*_Stylesheet.yaml` of rules beside each).
2. **Compose** (`spec/compose.py`). The parsed views become a tree of instances: a view call is replaced
   by the called view's root with the call's keys as its params, slots are filled, `for:` and `if:` make
   or drop instances, and `state:` makes a Signal for each name. An expression written at a call is
   read where it is written, and a name is looked up in the loop variables, local state, params, the
   ViewModel, then the app.
3. **Lower** (`spec/lower.py`). The instances become the node mappings the builder has always taken, with
   each property's current value.
4. **Build** (`spec/build.py`, with the cascade). The builder creates `tre` nodes: `Rect`/`Container`
   become a `box`, `Text` and `Link` a `text`, `Icon` a `path`, `Image` an `image`, a text input a
   `text_input`. The stateful kinds (`Checkbox`, `RadioButton`, `Switch`, `Slider`,
   `RangeSlider`, `SpinBox`, `CircularProgress`, `LinearProgress`, `LoadingIndicator`, `TimePickerDial`) become Tesserae's own
   controls. Image `src:` files are decoded to pixels (Pillow). Every property is set explicitly, defaults
   included, so a later patch can reset it.

**Styles.** A node's style is built from layers, lowest first: the rules Tesserae ships with each view,
the app's stylesheet (`styles:` rules that name a `widget`, and may narrow it by `variant`, `size`,
`shape`, `classes`, `name`, `part` and `state`), then the node's inline `style:`. The most specific rule
in a layer wins, and a later rule wins a tie; a value in a rule may be an expression over the widget's
properties. See [Themes](themes/index.md) and [Stylesheets](stylesheets/index.md).

**Tokens and `Theme`.** `tesserae.tokens` holds the MD3 values: the 49 colour roles from a seed
(light and dark, via `materialyoucolor`) with `colors:` overrides, the shape scale, elevation
(as key and ambient shadows), the 15 type roles, and colour-string parsing. `tesserae.Theme` is
one resolved theme, which style values like `primary`, `extra_large`, `level_3` or
`typography_role` resolve through. Widgets and views follow their app's theme: `App.set_dark`,
the OS light/dark switch and `App.set_theme_specs` re-colour them in place. See
[Themes](themes/index.md) and [Stylesheets](stylesheets/index.md).

**Widgets.** `tesserae.controls` are the stateful MD3 controls (`Checkbox`, `Switch`, `Slider`,
`SpinBox`, progress indicators, the time dial); each keeps its state in `Signal`s and fires
`on_change` for the user's edits only. `tesserae.widgets` has one function per MD3 widget, for code that
makes nodes at run time, each returning a control, a `Widget` (with `.node` and its parts) or an overlay. `tesserae.interaction` draws what the
engine does not: state layers, the ripple and focus rings. `tesserae.a11y` sets roles and states.
`tesserae.overlays` (`Dialog`, `Menu`, `Snackbar`, `Tooltip`, `Popover`, `SearchView`,
`NavigationDrawer`) show nodes with `window.show_layer`. A `widget: Window` view frames the screens with a title
bar, a rail and docked panels, and `Dock` manages the panels in its zones.
See the [widget catalog](guide/widget-catalog.md), [controls](guide/controls.md),
[overlays](guide/overlays.md), [windows and docks](guide/windows-and-docks.md) and the
[component gallery](components/index.md).

**The engine, `tre`.** It provides the node tree (`create`, `set`, `get`, `animate`, `on`,
`add_child`, `insert_child`, `remove`, `destroy`), layout, painting, text, input, accessibility,
layers and the render loop. It has no widgets, theme, stylesheets or reactivity of its own.

**What Tesserae hands `tre`: specs and bytes, never files.** Tesserae reads, parses, decodes and
watches every file. `tre` receives nodes built through its API, colours as RGBA tuples, image
pixels as `rgba` on an `image` node, and font files as bytes (`register_font`). It is never
given a path.

## A screen load

`app.bind(CounterViewModel)` and `app.open_view("Counter")`:

1. `bind` records that `CounterViewModel` serves the view named `Counter`. Nothing is made yet.
2. `open_view` finds `Counter_View.yaml` (a path, or a name in the project), and parses it together with
   the views it calls.
3. The ViewModel is made, once, with no arguments, and composed with the view into instances. Each
   expression is static (worked out once) or reactive (a binding that follows the Signals it reads).
4. `ComposedView` lowers the instances and builds them with the app's theme and rules into nodes in the
   app's window, then wires each handler to its node. The view is registered as `"Counter"`.
5. `app.show("Counter")` attaches the view's root to `window.root` and detaches the previous
   screen's root. A detached screen keeps its state and bindings. Nothing is parsed again.
   `navigate`, `route` and `back` add a history of named screens on top of `show`.

## A signal change

A binding such as `text: "{{ count }}"` is an expression in a restricted subset of Python
(`tesserae.expr`: arithmetic, comparisons, comprehensions, a short list of functions; never `eval`).
While it is evaluated, `tesserae.reactive` notes every `Signal` or `Computed` it reads. When one changes
(`vm.count.set(5)`), `ComposedView` lowers its instances again and `View.reconcile` patches the live nodes:
a node whose id is unchanged keeps its identity, focus and running animations, and only the fields that
differ are set. `batch` defers notifications so each subscriber runs once. Going the other way, a
handler (`on_click: increment`) is a listener on the node that runs the ViewModel method, or the
statements written there, in the names where they were written; a model property given a bare reference
(`checked: "{{ done }}"`) writes the user's edit back to that Signal. See [Bindings](guide/bindings.md).

## Reconciling and hot reload

`View.reconcile` matches children by id, which is the node's path from the root: its `name:`, or its place,
with the `key:` added under a `for:`. An unchanged node keeps its identity, focus and
running animations, a changed one is patched in place, a changed kind is rebuilt, a missing one
is destroyed, and children follow the new spec's order. Bindings and handlers are wired again
after each update, without doubling listeners. A node that keeps its `name` or `key` keeps its `state:`.

`App.run(hot_reload=True)` uses the same machinery. It watches the theme files and the app's stylesheet file given to the app, a
`ComposedWatcher` per view opened with `open_view` or `open_window` (the file and every view, stylesheet and theme it was built from), and a
`ViewWatcher` per screen built from a file by `app.load` in the older syntax (`watchfiles`, on a background thread). On a change it reruns the pipeline off the main thread
and hands the result to the event loop through `tre`'s thread-safe loop handle, which reconciles the live
view. A failed reload is logged and the app keeps running. See [Hot reload](guide/hot-reload.md) for what is
watched.

## Design rules

- **Specs and bytes, never files.** See above; it keeps all file handling and watching in one
  place.
- **YAML is data.** No `eval`: expressions are a small checked grammar and handlers name
  ViewModel methods or are short statements. Mistakes (an unknown property, a name no ViewModel has, a
  mismatched naming pair) fail at load with a message that names the spot.
- **One source of truth per state.** State lives in `Signal`s; the UI is a function of them.
  A programmatic `set` never fires `on_change`, so reloads and bindings do not echo back.
- **Everything is built from the engine's primitives** (`create`, `set`, `on`,
  `show_layer`), so the engine stays small and each widget's look sits in a stylesheet you can
  override.
- **Themes are data.** Seed colour, `colors:`, `components:` shape and elevation, and
  `typography:` overrides in a theme file re-resolve the colours and re-colour live views.
- **Screens are long-lived.** Switching screens detaches, never rebuilds.
- **Proven against recorded answers.** Binding, cascade, colour and tree-building tests replay
  reference results recorded from `tre` (`tests/reference/*.json`), so a regression in those
  parts fails a test.

For the full list of names and signatures see the [Python API](api/python.md) and the
[YAML reference](api/yaml.md).
