# `tesserae.spec` -- `load_view` / `expand_components`

The declarative component-fragment macro layer -- see
[Declarative Component Fragments](../guide/component-fragments.md) for
the full guide. This page is the API surface itself.

## `load_view`

**`load_view(path, *, component_dirs=None, **view_kwargs) -> tre.View`**

Reads `path`, expands any `component:` usage in it via
`expand_components`, and constructs a real `tre.View` from the result
via `source=`. `path` is still passed through unchanged, so
`include:`/`image.src:` resolve against its real directory exactly as
they would for a plain `tre.View(path)` call.

- `component_dirs` -- extra fragment directories to search (in order),
  in addition to Tesserae's own built-in `spec/components/`, letting
  an app add or shadow components with its own. Defaults to `None`
  (built-in directory only).
- `**view_kwargs` -- forwarded straight to `tre.View` (`theme_seed`,
  `custom_theme`, `dark`, `stylesheet`).

A view with zero `component:` usage expands to itself unchanged, so
this is a safe drop-in for any existing `View(path)` call -- not just
ones that use `component:`. `App.load()` calls this internally; you
only need it directly for a tool, or for constructing a `View` outside
`App`.

## `expand_components`

**`expand_components(yaml_text, *, component_dirs=None) -> str`**

The lower-level function `load_view` builds on: expands every
`component:` entry in `yaml_text` (a raw YAML string, not a path),
returning fully expanded `WidgetSpec`-shaped YAML text with no
`component:`/`with:`/`params:`/`repeat:` keys remaining -- ready for
`tre.View(source=...)`. `tesserae.instantiate` calls this directly
(a component being embedded needs its *content* expanded, not loaded
as a top-level `View`).

## `ComponentError`

A `ValueError` subclass raised for any `component:` reference that
can't be expanded -- an unknown component name, a missing or unknown
parameter, a mismatched `id:`, a cycle, exceeding `MAX_DEPTH`, or a
malformed `repeat:`. Its message includes the call chain that led to
the failure (e.g. `Card -> ButtonFilled: ...`), not just the
innermost fragment.

```python
from tesserae.spec import ComponentError, load_view

try:
    view = load_view("Dashboard_View.yaml")
except ComponentError as exc:
    print(f"bad component usage: {exc}")
```
