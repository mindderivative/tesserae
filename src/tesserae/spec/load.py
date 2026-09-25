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

M29 Phase 4: theme and stylesheet files too. `load_view`'s
`stylesheet=`/`default_theme=`/`custom_theme=` still take file paths,
but Tesserae reads them (`themes.py`) and hands `tre` the dicts via
`stylesheet_spec=`/`default_theme_spec=`/`custom_theme_spec=` (tre M86).
Fonts a view or theme names are checked against what `tre` can draw
(`tesserae.fonts`).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tre import View

from tesserae.fonts import check_font_families
from tesserae.spec.expand import expand_with_dependencies
from tesserae.spec.images import Frame, extract_images, push_frames
from tesserae.spec.themes import load_stylesheet, load_theme, view_font_families

__all__ = ["build_view_spec", "load_view"]

#: `load_view` path argument -> (the `tre` dict argument it becomes, the
#: loader that reads it).
_FILE_ARGS = {
    "stylesheet": ("stylesheet_spec", load_stylesheet),
    "default_theme": ("default_theme_spec", load_theme),
    "custom_theme": ("custom_theme_spec", load_theme),
}


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
    check_font_families(view_font_families(spec), str(path))
    return spec, frames, deps


def load_view(path: str | Path, *, component_dirs: list[Path] | None = None, **view_kwargs: Any) -> View:
    """Reads `path`, resolves its `include:`s and expands its
    `component:` usage, and constructs a real `tre.View` from the
    resulting dict via `spec=`.

    `stylesheet=`, `default_theme=` and `custom_theme=` take file paths
    (relative to the current directory, as before); Tesserae reads them
    and passes `tre` the dicts. Their `*_spec=` forms take a dict
    directly -- give one form or the other, not both. Everything else
    (`theme_seed=`, `dark=`) forwards straight to `tre.View`.

    A view with no `include:`/`component:` usage expands to itself
    unchanged, so this is a safe drop-in for any existing `View(path)`
    call, not just ones that use the new capability.

    Every `kind: Image`'s `src:` is decoded by Tesserae and pushed onto
    the built node; a missing or undecodable image is a
    `ComponentError` naming the widget and file.

    A `ValueError` from `tre` (a spec it rejects) is re-raised naming the
    file it came from -- the theme or stylesheet file for an error in
    one of those, `path` otherwise. `tre` only ever sees dicts, so it
    can't say which file a problem came from.
    """
    path = Path(path)
    spec, frames, _ = build_view_spec(path, component_dirs=component_dirs)
    sources: dict[str, Path] = {}
    for file_arg, (spec_arg, loader) in _FILE_ARGS.items():
        file = view_kwargs.pop(file_arg, None)
        if file is None:
            continue
        if view_kwargs.get(spec_arg) is not None:
            raise ValueError(f"load_view: pass {file_arg}= or {spec_arg}=, not both")
        view_kwargs[spec_arg] = loader(file)
        sources[spec_arg] = Path(file)
    try:
        view = View(spec=spec, **view_kwargs)
    except ValueError as exc:
        message = str(exc)
        source = next((f for arg, f in sources.items() if message.startswith(f"{arg}=")), path)
        raise ValueError(f"{source}: {message}") from exc
    push_frames(view, frames)
    return view
