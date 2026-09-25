# `tesserae.spec` -- `load_view` / `expand_components`

The declarative component-fragment macro layer -- see
[Declarative Component Fragments](../guide/component-fragments.md) for
the full guide. This page is the API surface itself.

Tesserae reads and expands every view file itself and builds the result
into `tre` nodes with its own compiler (M37). `tre` never reads your
`*_View.yaml`, `*_Component.yaml` or `include:` files.

## `load_view`

**`load_view(path, *, component_dirs=None, **view_kwargs) -> tesserae.View`**

Reads `path`, resolves its `include:`s, expands its `component:` usage,
and builds a `tesserae.View` from the result.

- `component_dirs` -- extra fragment directories to search (in order),
  in addition to Tesserae's own built-in `spec/components/`, letting
  an app add or shadow components with its own. Defaults to `None`
  (built-in directory only).
- `stylesheet=`, `default_theme=`, `custom_theme=` -- file paths
  (relative to the current directory). Tesserae reads them and passes
  `tre` the dicts; the matching `*_spec=` arguments take a dict
  directly. Give one form or the other, not both. See
  [Themes & Fonts](../guide/themes-and-fonts.md).
- Other keyword arguments (`theme_seed`, `dark`) are forwarded
  straight to `tesserae.View`.

If `tre` rejects the spec, the `ValueError` is re-raised naming the
file it came from -- the theme or stylesheet file for an error in one
of those, `path` otherwise. `tre` only ever sees dicts, so it can't say
which file the problem came from:

```text
ValueError: app/Settings_View.yaml: spec=: unknown variant `Rectangle`, ...
```

A view with no `include:` or `component:` usage expands to itself
unchanged, so this is a safe drop-in for any existing `View(path)` call.
`App.load()` calls this internally; you only need it directly for a
tool, or for constructing a `View` outside `App`.

`tre` is never given a file path -- not the view's, and not
`tesserae.instantiate`'s component file either. For hot reload, use
[`ViewWatcher`](#viewwatcher) rather than `tre`'s own
`View.poll_reload()`, which has no file to watch.

## Images (`kind: Image` with `src:`)

Tesserae decodes every image a view names -- hand-written
`kind: Image` nodes and the `Image` fragment alike -- and hands `tre`
only the pixels:

1. After expansion, each `kind: Image`'s `image.src:` is removed from
   the spec (`fit:` is kept).
2. Tesserae decodes the file with Pillow to straight-alpha RGBA.
3. `tre` builds the node as a blank image, and Tesserae pushes the
   decoded pixels onto it with `Node.push_frame`.

`src:` follows the same rules `tre` used when it loaded images itself,
so existing views don't change: relative to the top-level view file's
directory (including images inside an `include:`d file), no absolute
paths, and no escaping that directory. A missing or undecodable image
is a `ComponentError` naming the widget and the file:

```text
ComponentError: widget 'logo': image.src: 'assets/logo.png': cannot read ...
```

## `ViewWatcher`

**`ViewWatcher(view, path, *, component_dirs=None)`**

Hot reload for a view built with `load_view`. Pass the same `path` and
`component_dirs`. `App.run(hot_reload=True)` creates and starts one for
every screen registered with `App.load()`.

- **`start(handle)` / `stop()`** -- watch for file-change events
  (`watchfiles`) on a background thread. `handle` is
  `App.thread_handle()`; each reload is rebuilt on the watcher thread
  and applied on the event-loop thread via `handle.call_soon`. A failed
  reload is logged at `ERROR` through loguru, naming the file (traceback
  at `DEBUG`); the view stays as it was and the watcher carries on. Each
  reload is logged at `INFO` (see [Logging](../guide/logging.md)).
  `running` says whether the thread is active.
- **`poll() -> bool`** -- if any file the view was built from changed
  since the last poll, rebuilds it and updates the live view in place
  via `tre`'s `view.reconcile(spec=...)`, then returns `True`.
  Otherwise returns `False`.
- **`files -> frozenset[Path]`** -- every file being watched: the view,
  each `include:`d file, each `*_Component.yaml` fragment it used, and
  each image. Recomputed on every reload, so a newly added include,
  fragment or image is picked up.

With `poll()`, a reload that fails raises (`ComponentError`, or
`ValueError` naming the view file) and leaves the view unchanged;
polling again returns `False` until the next edit. `poll()` can't be
used while `start()`'s thread is running. See [Hot Reload](../guide/hot-reload.md).

## `load_theme` / `load_stylesheet`

**`load_theme(path) -> dict`** · **`load_stylesheet(path) -> dict`**

Read a theme or stylesheet YAML file into the dict `tre`'s `*_spec=`
arguments take -- for `View.set_theme(custom_theme_spec=...)` or
`Window.set_theme(seed, custom_theme_spec=...)`. An empty file is an
empty dict; a file that isn't a mapping, or isn't valid YAML, raises
`ValueError` naming it. `load_theme` also issues a
`FontFallbackWarning` for any `typography:` font family that isn't
available (see [`tesserae.register_font`](index.md)).

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
`params:`/`repeat:` keys remaining -- ready for `tesserae.View(spec)`.

- `base_dir` -- the directory `include:` paths resolve against,
  normally the view file's own directory. With `None`, any `include:`
  raises `ComponentError`.

## `expand_components`

**`expand_components(yaml_text, *, component_dirs=None, base_dir=None) -> str`**

`expand_components_to_spec`, dumped back to YAML text. Useful for
inspecting what a view expands to; nothing on Tesserae's own path to
`tre` uses it.

## `ComponentError`

A `ValueError` subclass raised for any `component:`, `include:` or
image that can't be expanded -- an unknown component name, a missing or
unknown parameter, a missing `id:`, a cycle, exceeding a depth limit, a
malformed `repeat:`, an `include:` that breaks one of the rules above,
or an image that can't be found or decoded. For `component:` errors the
message includes the call chain that led to the failure (e.g.
`Card -> ButtonFilled: ...`), not just the innermost fragment.

```python
from tesserae.spec import ComponentError, load_view

try:
    view = load_view("Dashboard_View.yaml")
except ComponentError as exc:
    print(f"bad component usage: {exc}")
```
