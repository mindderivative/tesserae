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
| `tesserae.register_font(path) -> list[str]` | Reads a font file and registers it with `tre`; returns its family names. See [Themes & Fonts](../guide/themes-and-fonts.md). |

Reactivity (`Signal`, `ViewModel`, `Computed`, `Effect`, `batch`,
`untrack`) is Tesserae's own (`tesserae.reactive`, M35); see
[Reactivity](../guide/reactivity.md). `View` and `Component` are still
`tre`'s, re-exported until Tesserae builds views itself (M37); see
[`tre`'s Python API reference](https://mindderivative.github.io/tre/api/python/index/)
for those:

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
