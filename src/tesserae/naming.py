"""Real, shared `*_View.yaml`/`*_ViewModel.py` naming-convention
enforcement -- factored out of `App.load` so the new `instantiate()`
(`tesserae.component`) can apply the identical real check to a
`Component`'s own view+viewmodel pair, not just a top-level
`App`-registered screen. Two real call sites justify sharing this
rather than duplicating it.
"""

from __future__ import annotations

import inspect
from pathlib import Path

_VIEW_SUFFIX = "_View.yaml"
_VIEWMODEL_SUFFIX = "_ViewModel.py"


def check_naming_convention(view_path: str | Path, viewmodel_cls: type) -> str:
    """Raises `ValueError` with a clear message if `view_path`/
    `viewmodel_cls` don't follow the `*_View.yaml`/`*_ViewModel.py`
    convention with a shared prefix. Returns the shared prefix on
    success (e.g. `"Counter"` for `Counter_View.yaml`/
    `Counter_ViewModel.py`).
    """
    view_path = Path(view_path)
    if not view_path.name.endswith(_VIEW_SUFFIX):
        raise ValueError(
            f"{view_path.name!r} does not follow the required *{_VIEW_SUFFIX} naming "
            "convention"
        )
    view_prefix = view_path.name[: -len(_VIEW_SUFFIX)]

    viewmodel_file = Path(inspect.getfile(viewmodel_cls))
    if not viewmodel_file.name.endswith(_VIEWMODEL_SUFFIX):
        raise ValueError(
            f"{viewmodel_cls.__name__} (defined in {viewmodel_file.name!r}) does not "
            f"follow the required *{_VIEWMODEL_SUFFIX} naming convention"
        )
    viewmodel_prefix = viewmodel_file.name[: -len(_VIEWMODEL_SUFFIX)]

    if view_prefix != viewmodel_prefix:
        raise ValueError(
            f"{view_path.name!r} and {viewmodel_file.name!r} must share the same "
            f"prefix (got {view_prefix!r} vs {viewmodel_prefix!r})"
        )
    return view_prefix
