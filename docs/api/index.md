# API Reference

Tesserae's own real, additive public surface:

| | |
| --- | --- |
| [`App`](app.md) | The single entry point -- a named screen registry + one live window. |
| [`instantiate`](instantiate.md) | Embeds a reusable, independently-stateful `Component`. |
| [`Repeater`](repeater.md) | Automatic keyed add/remove diffing over a list `Signal`. |
| [`tesserae.spec` (`load_view`/`expand_components`)](spec.md) | Declarative `component:`/`with:`/`repeat:` macro expansion -- see the [Component Fragments](../guide/component-fragments.md) guide. |
| [`tesserae.widgets`](../guide/widget-catalog.md) | Imperative, thin-delegate access to all ~68 real MD3 widgets. |

`tre`'s own real, already-working primitives, re-exported unmodified
rather than duplicated -- see [`tre`'s own Python API reference](https://mindderivative.github.io/tre/api/python/index/)
for these:

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
