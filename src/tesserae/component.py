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
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tesserae.naming import check_naming_convention


def instantiate(
    parent: Any, path: str | Path, viewmodel_cls: type, into: Any, *args: Any, **kwargs: Any
) -> tuple[Any, Any]:
    """Instantiates the component at `path` into `into` (a `Node`, e.g.
    from `parent.node(widget_id)`), constructs `viewmodel_cls(component,
    *args, **kwargs)`, and returns `(component, viewmodel)`.

    `parent` is whatever already has a real `instantiate(path, into)` of
    its own -- a `View` or another `Component` (they nest, so a
    component can itself hold further nested components this same way).
    """
    check_naming_convention(path, viewmodel_cls)
    component = parent.instantiate(str(path), into)
    viewmodel = viewmodel_cls(component, *args, **kwargs)
    return component, viewmodel
