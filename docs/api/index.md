# API Reference

Tesserae's own real, additive public surface:

| | |
| --- | --- |
| [`App`](app.md) | The single entry point -- a named screen registry + one live window. |
| [`instantiate`](instantiate.md) | Embeds a reusable, independently-stateful `Component`. |
| [`Repeater`](repeater.md) | Automatic keyed add/remove diffing over a list `Signal`. |
| [`tesserae.spec` (`load_view`/`expand_components`)](spec.md) | Declarative `component:`/`with:`/`repeat:` macro expansion -- see the [Component Fragments](../guide/component-fragments.md) guide. |
| [`tesserae.widgets`](../guide/widget-catalog.md) | Imperative, thin-delegate access to all ~68 real MD3 widgets. |
| [`tesserae.spec.ViewWatcher`](spec.md#viewwatcher) | Hot reload: watches every file a view was built from and updates it in place (`App.run(hot_reload=True)` uses it). |
| [`tesserae.spec.load_theme` / `load_stylesheet`](spec.md#load_theme-load_stylesheet) | Read a theme or stylesheet file into the dict `tre`'s `*_spec=` arguments take. |
| `tesserae.configure_logging(level="INFO", *, sink=sys.stderr, format=DEFAULT_FORMAT, capture_warnings=True) -> int` | Sends log messages at `level` and above to `sink` in Tesserae's format, replacing loguru's default stderr handler; shows Python warnings through loguru too. Returns the handler id. See [Logging](../guide/logging.md). |
| `tesserae.Theme` | A resolved MD3 theme: `role`, `shape`/`elevation` (from `components:`), `typography`, and the motion tokens `easing`/`duration`. `app.theme` and `view.theme` return one. See [Themes & Fonts](../guide/themes-and-fonts.md#reading-the-theme-from-code). |
| `tesserae.interaction.Interaction` | MD3's state layer, ripple and focus ring on a node; `view.interaction(id)` returns a clickable node's. See [Interaction & Accessibility](../guide/interaction.md#from-code). |
| `tesserae.a11y` | `describe(node, role=, label=, ...)` checks and sets what a node tells assistive technology; `on_action(node, {action: fn})` routes `a11y_action` requests; `ROLES`, `LIVE`, `ACTIONS` are `tre`'s lists. See [Interaction & Accessibility](../guide/interaction.md#for-widgets-tesseraea11y). |
| `tesserae.controls` | MD3's stateful controls, built by Tesserae (M40, in progress): so far `Checkbox(window, checked=, label=, disabled=, theme=, color=)`. `.node` is its 48 px touch target, `.checked` and `.disabled` are `Signal`s, `on_change(fn)` hears the user's changes, and `set_theme(theme)` re-tints it. Built on `Control`. |
| `tesserae.register_font(path) -> list[str]` | Reads a font file and registers it with `tre`; returns its family names. See [Themes & Fonts](../guide/themes-and-fonts.md). |

Reactivity (`Signal`, `ViewModel`, `Computed`, `Effect`, `batch`,
`untrack`) is Tesserae's own (`tesserae.reactive`, M35); see
[Reactivity](../guide/reactivity.md). `View` and `Component` are
Tesserae's own too (`tesserae.view`, M37): Tesserae builds, reconciles
and wires views on `tre`'s building blocks. The names at a glance:

| | |
| --- | --- |
| `Signal` | The basic reactive cell. |
| `View` | A loaded `*_View.yaml`, the node tree it built, and its own hot-reload. |
| `ViewModel` | Base class wiring `bindings:`/`handlers:`/`two_way:` against `self`. |
| `Component` | One embedded, independently-removable instance (`instantiate`'s own return value). |
| `Computed` | A derived, cached value. |
| `Effect` | A side-effect-only reaction. |
| `batch` | Collapses several `Signal` writes into one notification pass. |
| `untrack` | Reads without recording a dependency. |
