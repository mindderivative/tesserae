# `tesserae.spec` -- `load_view` / `expand_components`

The declarative component-fragment macro layer -- see
[Declarative Component Fragments](../guide/component-fragments.md) for
the full guide. This page is the API surface itself.

Tesserae reads and expands every view file itself and hands `tre` the
finished result as a plain dict (`tre.View(spec=...)`). `tre` never
reads your `*_View.yaml`, `*_Component.yaml` or `include:` files.

## `load_view`

**`load_view(path, *, component_dirs=None, **view_kwargs) -> tre.View`**

Reads `path`, resolves its `include:`s, expands its `component:` usage,
and constructs a real `tre.View` from the resulting dict via `spec=`.

- `component_dirs` -- extra fragment directories to search (in order),
  in addition to Tesserae's own built-in `spec/components/`, letting
  an app add or shadow components with its own. Defaults to `None`
  (built-in directory only).
- `**view_kwargs` -- forwarded straight to `tre.View` (`theme_seed`,
  `custom_theme`, `dark`, `stylesheet`).

If `tre` rejects the spec, the `ValueError` is re-raised with `path` at
the front of the message -- `tre` only ever sees a dict, so it can't
say which file the problem came from:

```text
ValueError: app/Settings_View.yaml: spec=: unknown variant `Rectangle`, ...
```

A view with no `include:` or `component:` usage expands to itself
unchanged, so this is a safe drop-in for any existing `View(path)` call.
`App.load()` calls this internally; you only need it directly for a
tool, or for constructing a `View` outside `App`.

!!! note "Still passed to `tre`, for now"
    `path` is still given to `tre` as the base directory a
    `kind: Image`'s `src:` resolves against, and as the file `tre`'s
    own `poll_reload` watches. Both go away once image decoding and hot
    reload move into Tesserae (M29 Phases 2 and 3 in
    [`BUILD_TRACKER.md`](https://github.com/mindderivative/tesserae/blob/main/BUILD_TRACKER.md)).

## `include:`

A mapping whose only key is `include:` is replaced by that file's
parsed YAML, anywhere in a view:

```yaml
id: root
kind: Container
children:
  - include: parts/header.yaml
```

- The path is relative to the file that contains the `include:` -- an
  included file's own `include:`s resolve against *its* directory.
- It must stay inside that directory: absolute paths and `../`
  escapes are rejected.
- Cycles are rejected, and so is nesting more than 8 deep.
- `include:` must be the node's only key.
- An included file may use `component:`; it's expanded like the rest
  of the view.
- `include:` is not allowed inside a `*_Component.yaml` fragment --
  use a nested `component:` there instead.

These are the same rules `tre`'s own `include:` has always used, so a
view that loaded before still loads.

## `expand_components_to_spec`

**`expand_components_to_spec(yaml_text, *, component_dirs=None, base_dir=None) -> dict`**

The function `load_view` and `tesserae.instantiate` build on: resolves
every `include:` and expands every `component:` entry in `yaml_text` (a
raw YAML string, not a path), returning the finished
`WidgetSpec`-shaped dict with no `include:`/`component:`/`with:`/
`params:`/`repeat:` keys remaining -- ready for `tre.View(spec=...)`.

- `base_dir` -- the directory `include:` paths resolve against,
  normally the view file's own directory. With `None`, any `include:`
  raises `ComponentError`.

## `expand_components`

**`expand_components(yaml_text, *, component_dirs=None, base_dir=None) -> str`**

`expand_components_to_spec`, dumped back to YAML text. Useful for
inspecting what a view expands to; nothing on Tesserae's own path to
`tre` uses it.

## `ComponentError`

A `ValueError` subclass raised for any `component:` or `include:` that
can't be expanded -- an unknown component name, a missing or unknown
parameter, a missing `id:`, a cycle, exceeding a depth limit, a
malformed `repeat:`, or an `include:` that breaks one of the rules
above. For `component:` errors the message includes the call chain that
led to the failure (e.g. `Card -> ButtonFilled: ...`), not just the
innermost fragment.

```python
from tesserae.spec import ComponentError, load_view

try:
    view = load_view("Dashboard_View.yaml")
except ComponentError as exc:
    print(f"bad component usage: {exc}")
```
