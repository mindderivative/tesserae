"""`instantiate`: embeds a component -- a `*_View.yaml` +
`*_ViewModel.py` pair -- in a Tesserae `View` or `Component` (M37:
built by Tesserae in the host's window). For a component whose `ViewModel`
needs extra constructor arguments beyond the component itself (the
real, common case: an item's own data, or a callback letting it remove
itself from its parent's own bookkeeping), `tre`'s raw `parent
.instantiate(path, into)` plus a manual `viewmodel_cls(component, ...)`
call already works; this adds the same real `*_View.yaml`/
`*_ViewModel.py` check `App.load` already enforces for top-level
screens, so a mismatched component pair fails immediately at
instantiation time instead of much later when a handler name doesn't
resolve.

Also applies `component:` macro-expansion (`tesserae.spec`) before
handing off to `parent.instantiate`, now via `spec=` rather than the
`source=` override `tre`'s own M73 gave `View.instantiate`/`Component.instantiate` --
previously only reachable for a top-level `View` (via `App.load`'s own
`load_view`), never for an embedded component.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tesserae.follow import app_of
from tesserae.naming import check_naming_convention
from tesserae.project import project_of, resolve_embedded, resolve_view
from tesserae.spec import expand_components_to_spec
from tesserae.spec.images import extract_images


def _build_component(parent: Any, path: Path, into: Any) -> Any:
    """The view at `path` built as a component of `parent`, into the node `into`, in `parent`'s window with its theme."""
    host = app_of(getattr(parent, "window", None))
    spec = expand_components_to_spec(path.read_text(encoding="utf-8"), base_dir=path.parent,
                                     project=host.project if host is not None else None)
    spec, frames = extract_images(spec, path.parent)
    try:
        # M37: Tesserae builds it, in the host's window with the host's theme and stylesheet
        component = parent.instantiate(path, into, spec=spec,
                                       frames={node_id: (rgba, w, h) for node_id, rgba, w, h in frames})
    except ValueError as exc:
        raise ValueError(f"{path}: {exc}") from exc
    if component.spec.get("window") is not None:  # a Window is the whole OS window: there is one, and it is the app's
        component.remove()
        raise ValueError(f"{path}: a `kind: Window` view is the app's window and can't be embedded or instantiated "
                         "(load it with `app.load`)")
    return component


def _watch(component: Any, path: Path) -> None:
    app = app_of(getattr(component, "window", None))
    if app is not None:
        app._instances.add(component)  # found for hot reload in any view (M61)
        app.watch_component(path)  # hot reload, if it's on (M51)


def embed(parent: Any, ref: str | Path, into: Any, arguments: dict[str, Any] | None = None,
          base: Path | None = None) -> tuple[Any, Any]:
    """The view `ref` (a file, or a name found in the project) built into the node `into` of `parent`, as a `view:`
    node in a view does; returns `(component, viewmodel)`. The ViewModel is `Name_ViewModel.py`'s `NameViewModel`, built
    as `NameViewModel(component, **arguments)`, and a view with no ViewModel file is built with none (`viewmodel` is
    `None`). A view with no ViewModel can't have bindings, `two_way:`, or handlers other than `window.*` and `surface.*`, or be
    given `arguments`. A relative
    path is the folder `base`'s (where the file that names it is)."""
    path, viewmodel_cls = resolve_embedded(project_of(parent), ref, base)
    arguments = dict(arguments or {})
    if viewmodel_cls is not None:
        check_naming_convention(path, viewmodel_cls)
    component = _build_component(parent, path, into)
    if viewmodel_cls is None:
        wired = wired_nodes(component.spec)
        if wired:
            component.remove()
            raise ValueError(f"{path}: {', '.join(wired[:3])}{' ...' if len(wired) > 3 else ''} use bindings or handlers, "
                             f"but there is no {path.name.removesuffix('_View.yaml')}_ViewModel.py for them (a view with "
                             "no ViewModel is static)")
        if arguments:
            component.remove()
            raise ValueError(f"{path}: `with:` {sorted(arguments)} is for a ViewModel, and this view has none")
        viewmodel = None
    else:
        try:
            viewmodel = viewmodel_cls(component, **arguments)
        except TypeError as exc:
            component.remove()
            raise ValueError(f"{path}: {viewmodel_cls.__name__}(component, **{sorted(arguments)}): {exc}") from exc
    _watch(component, path)
    return component, viewmodel


def wired_nodes(spec: dict[str, Any]) -> list[str]:
    """The ids of the nodes in `spec` that need a ViewModel: they have `bindings:`, `handlers:` or `two_way:`."""
    found: list[str] = []

    def walk(node: dict[str, Any]) -> None:
        own = [h for h in (node.get("handlers") or {}).values() if not str(h).startswith(("window.", "surface.", "navigate."))]
        if node.get("bindings") or own or node.get("two_way"):
            found.append(str(node.get("id")))
        for child in node.get("children") or []:
            if isinstance(child, dict):
                walk(child)

    walk(spec)
    return found


def instantiate(
    parent: Any, path: str | Path, viewmodel_cls: type | None = None, into: Any = None, *args: Any, **kwargs: Any
) -> tuple[Any, Any]:
    """Instantiates the component at `path` into `into` (a `Node`, e.g.
    from `parent.node(widget_id)`), constructs `viewmodel_cls(component,
    *args, **kwargs)`, and returns `(component, viewmodel)`.

    `path` is a file, or a name found in the app's project (`"TaskItem"` is `Views/TaskItem_View.yaml`);
    `viewmodel_cls` left out is found by the view's name (`TaskItem_ViewModel.py`, class `TaskItemViewModel`),
    beside the view or in `ViewModels/`.

    `parent` is whatever already has a real `instantiate(path, into)` of
    its own -- a `View` or another `Component` (they nest, so a
    component can itself hold further nested components this same way,
    and `component:` usage inside a nested component's own YAML expands
    the identical way).

    `path`'s real content is expanded for `include:`/`component:` usage
    and handed to `tre` as a dict via `spec=`, the same
    as `load_view` -- a true no-op expansion for a file with neither.
    Every `kind: Image`'s `src:` is decoded by Tesserae and pushed onto
    the built node, so `tre` is given no file path at all
    -- `path=""` is `tre`'s own "no base directory" value, and with
    `include:` and `image.src:` both handled here, `tre` has nothing
    left to resolve against one. A `ValueError` from `tre` is re-raised
    naming `path`.
    """
    if into is None:
        raise TypeError("instantiate() needs `into`: the node the component goes in")
    path, viewmodel_cls = resolve_view(project_of(parent), path, viewmodel_cls)
    check_naming_convention(path, viewmodel_cls)
    component = _build_component(parent, path, into)
    viewmodel = viewmodel_cls(component, *args, **kwargs)
    _watch(component, path)
    return component, viewmodel
