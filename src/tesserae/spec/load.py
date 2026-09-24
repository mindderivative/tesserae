"""`load_view` -- the real integration point between `expand_components`
and `tre.View`. Deliberately a plain function, not a `tre.View` subclass
(`View` is a native `pyo3` class; wrapping it adds real complexity for
uncertain benefit when a function returning the genuine object works
just as well for every real caller so far).

Real, named, deferred follow-ups (not done in this pass): wiring
`App.load()`/`tesserae.instantiate()` to use this by default, and a
`poll_reload`-integrated re-expansion helper for hot reload. Neither is
silently promised as already working -- `tesserae.instantiate()` in
particular can't use `component:` at all yet (`tre.Component.instantiate`
has no `source=` override; see `PLAN.md`).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tre import View

from tesserae.spec.expand import expand_components

__all__ = ["load_view"]


def load_view(path: str | Path, *, component_dirs: list[Path] | None = None, **view_kwargs: Any) -> View:
    """Reads `path`, expands any `component:` usage, and constructs a
    real `tre.View` from the result via `source=` -- `path` is still
    passed through unchanged, so `include:`/`image.src:` resolve against
    its real directory exactly as they would for a plain `tre.View(path)`
    call. `**view_kwargs` (`theme_seed`, `custom_theme`, `dark`,
    `stylesheet`) forward straight to `tre.View`.

    A view with zero `component:` usage expands to itself unchanged
    (`expand_components` is a no-op walk over a tree with nothing to
    expand), so this is a safe drop-in for any existing `View(path)`
    call, not just ones that use the new capability.
    """
    path = Path(path)
    raw_text = path.read_text(encoding="utf-8")
    expanded = expand_components(raw_text, component_dirs=component_dirs)
    return View(str(path), source=expanded, **view_kwargs)
