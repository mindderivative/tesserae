"""`load_view` -- the real integration point between `expand_components`
and `tre.View`. Deliberately a plain function, not a `tre.View` subclass
(`View` is a native `pyo3` class; wrapping it adds real complexity for
uncertain benefit when a function returning the genuine object works
just as well for every real caller so far).

M29 Phase 1: hands `tre` the finished dict via `spec=` -- no more
`yaml.safe_dump` back to text for `tre` to re-parse. Tesserae reads the
file and resolves `include:` itself (`expand.py`).

M29 Phase 2: every `kind: Image`'s `src:` is taken out, decoded by
Tesserae, and pushed onto the built node (`spec/images.py`), so `tre`
never opens an image file either.

M29 Phase 3: `tre` is given no path at all -- `View(spec=...)` only.
The one job the path still had (`tre`'s own `poll_reload` watch target)
is replaced by Tesserae's `ViewWatcher` (`watch.py`), which reuses
`build_view_spec` below so a reload runs the exact same pipeline as the
first load.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tre import View

from tesserae.spec.expand import expand_with_dependencies
from tesserae.spec.images import Frame, extract_images, push_frames

__all__ = ["build_view_spec", "load_view"]


def build_view_spec(
    path: str | Path, *, component_dirs: list[Path] | None = None
) -> tuple[Any, list[Frame], set[Path]]:
    """Reads `path` and runs the whole Tesserae-side pipeline --
    `include:`, `component:`, then image extraction and decoding --
    returning `(spec, frames, dependencies)`: the dict to hand `tre`, the
    decoded images to push once it's built, and every file read along
    the way (the view itself included), resolved."""
    path = Path(path)
    spec, deps = expand_with_dependencies(
        path.read_text(encoding="utf-8"), component_dirs=component_dirs, base_dir=path.parent
    )
    deps.add(path.resolve())
    spec, frames = extract_images(spec, path.parent, dependencies=deps)
    return spec, frames, deps


def load_view(path: str | Path, *, component_dirs: list[Path] | None = None, **view_kwargs: Any) -> View:
    """Reads `path`, resolves its `include:`s and expands its
    `component:` usage, and constructs a real `tre.View` from the
    resulting dict via `spec=`. `**view_kwargs` (`theme_seed`,
    `custom_theme`, `dark`, `stylesheet`) forward straight to `tre.View`.

    A view with no `include:`/`component:` usage expands to itself
    unchanged, so this is a safe drop-in for any existing `View(path)`
    call, not just ones that use the new capability.

    Every `kind: Image`'s `src:` is decoded by Tesserae and pushed onto
    the built node; a missing or undecodable image is a
    `ComponentError` naming the widget and file.

    A `ValueError` from `tre` (a spec it rejects) is re-raised naming
    `path` -- `tre` only ever sees a dict, so it can't say which file
    the problem came from.
    """
    path = Path(path)
    spec, frames, _ = build_view_spec(path, component_dirs=component_dirs)
    try:
        view = View(spec=spec, **view_kwargs)
    except ValueError as exc:
        raise ValueError(f"{path}: {exc}") from exc
    push_frames(view, frames)
    return view
