"""`load_view` -- the real integration point between `expand_components`
and `tre.View`. Deliberately a plain function, not a `tre.View` subclass
(`View` is a native `pyo3` class; wrapping it adds real complexity for
uncertain benefit when a function returning the genuine object works
just as well for every real caller so far).

M29 Phase 1: hands `tre` the finished dict via `spec=` -- no more
`yaml.safe_dump` back to text for `tre` to re-parse. Tesserae reads the
file and resolves `include:` itself (`expand.py`).

`path` is still passed to `tre`, for now, for exactly two reasons, both
removed later in M29: it's the base directory `tre` resolves a
`kind: Image`'s `src:` against (Phase 2 moves image decoding into
Tesserae), and it's the file `tre`'s own `poll_reload` watches (Phase 3
replaces that with Tesserae-owned watching). `tre` never *reads* the
view file itself any more -- with `spec=` given, it only uses `path` for
those two things.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tre import View

from tesserae.spec.expand import expand_components_to_spec

__all__ = ["load_view"]


def load_view(path: str | Path, *, component_dirs: list[Path] | None = None, **view_kwargs: Any) -> View:
    """Reads `path`, resolves its `include:`s and expands its
    `component:` usage, and constructs a real `tre.View` from the
    resulting dict via `spec=`. `**view_kwargs` (`theme_seed`,
    `custom_theme`, `dark`, `stylesheet`) forward straight to `tre.View`.

    A view with no `include:`/`component:` usage expands to itself
    unchanged, so this is a safe drop-in for any existing `View(path)`
    call, not just ones that use the new capability.

    A `ValueError` from `tre` (a spec it rejects) is re-raised naming
    `path` -- `tre` only ever sees a dict, so it can't say which file
    the problem came from.
    """
    path = Path(path)
    spec = expand_components_to_spec(
        path.read_text(encoding="utf-8"), component_dirs=component_dirs, base_dir=path.parent
    )
    try:
        return View(str(path), spec=spec, **view_kwargs)
    except ValueError as exc:
        raise ValueError(f"{path}: {exc}") from exc
