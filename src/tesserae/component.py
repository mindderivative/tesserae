"""Real, enforced-naming counterpart to `tre.View.instantiate`/
`Component.instantiate` (TRE M43) -- for a component whose `ViewModel`
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
handing off to `parent.instantiate`, now via `spec=` (M29) rather than the
`source=` override `tre`'s own M73 gave `View.instantiate`/`Component.instantiate` --
previously only reachable for a top-level `View` (via `App.load`'s own
`load_view`), never for an embedded component.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tesserae.naming import check_naming_convention
from tesserae.spec import expand_components_to_spec
from tesserae.spec.images import extract_images, push_frames


def instantiate(
    parent: Any, path: str | Path, viewmodel_cls: type, into: Any, *args: Any, **kwargs: Any
) -> tuple[Any, Any]:
    """Instantiates the component at `path` into `into` (a `Node`, e.g.
    from `parent.node(widget_id)`), constructs `viewmodel_cls(component,
    *args, **kwargs)`, and returns `(component, viewmodel)`.

    `parent` is whatever already has a real `instantiate(path, into)` of
    its own -- a `View` or another `Component` (they nest, so a
    component can itself hold further nested components this same way,
    and `component:` usage inside a nested component's own YAML expands
    the identical way).

    `path`'s real content is expanded for `include:`/`component:` usage
    and handed to `tre` as a dict via `spec=` (M29 Phase 1), the same
    as `load_view` -- a true no-op expansion for a file with neither.
    Every `kind: Image`'s `src:` is decoded by Tesserae and pushed onto
    the built node (M29 Phase 2), so `tre` is given no file path at all
    -- `path=""` is `tre`'s own "no base directory" value, and with
    `include:` and `image.src:` both handled here, `tre` has nothing
    left to resolve against one. A `ValueError` from `tre` is re-raised
    naming `path`.
    """
    check_naming_convention(path, viewmodel_cls)
    path = Path(path)
    spec = expand_components_to_spec(path.read_text(encoding="utf-8"), base_dir=path.parent)
    spec, frames = extract_images(spec, path.parent)
    try:
        component = parent.instantiate("", into, spec=spec)
    except ValueError as exc:
        raise ValueError(f"{path}: {exc}") from exc
    push_frames(component, frames)
    viewmodel = viewmodel_cls(component, *args, **kwargs)
    return component, viewmodel
