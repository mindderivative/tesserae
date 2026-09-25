"""M29 Phase 3: Tesserae-owned hot reload, replacing `tre`'s own
`poll_reload` (which watched a file `tre` itself read -- `tre` now reads
none). A plain poll loop, the user's own choice over a file-watching
dependency: `poll()` compares each file's modification time and size
against what it saw last, so there's nothing to install and nothing
running in the background.

A view depends on more than its own file: every `include:`d file, every
`*_Component.yaml` fragment it expanded, and every image it decodes. A
change to any of them re-runs the whole Tesserae pipeline
(`build_view_spec`, the same one `load_view` runs) and hands `tre` the
result via `view.reconcile(spec=...)`, which keeps unchanged widgets'
`NodeId`s, focus and in-flight animations. Images are pushed again
afterwards. The set of watched files is recomputed on every reload, so
a newly added `include:`, fragment or image is watched from then on.

`tre`'s `View` is single-threaded (`unsendable`), so `poll()` has to be
called on the thread that owns the view -- from the app's own loop. `tre`
doesn't yet offer a hook to run it from inside `App.run()`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional, Tuple

from tesserae.spec.images import push_frames
from tesserae.spec.load import build_view_spec

__all__ = ["ViewWatcher"]

#: `(st_mtime_ns, st_size)`, or `None` for a file that doesn't exist.
_Stamp = Optional[Tuple[int, int]]


def _stamp(path: Path) -> _Stamp:
    try:
        stat = path.stat()
    except OSError:
        return None
    return (stat.st_mtime_ns, stat.st_size)


class ViewWatcher:
    """Watches every file `view` was built from; `poll()` reloads it.

    Create it right after `load_view(path, ...)`, with the same `path`
    and `component_dirs`:

    ```python
    view = load_view("Home_View.yaml")
    watcher = ViewWatcher(view, "Home_View.yaml")
    ...
    if watcher.poll():   # call regularly from the app's own loop
        print("reloaded")
    ```
    """

    def __init__(self, view: Any, path: str | Path, *, component_dirs: list[Path] | None = None) -> None:
        self._view = view
        self._path = Path(path)
        self._component_dirs = component_dirs
        _, _, deps = build_view_spec(self._path, component_dirs=component_dirs)
        self._stamps: dict[Path, _Stamp] = {p: _stamp(p) for p in deps}

    @property
    def files(self) -> frozenset[Path]:
        """Every file currently being watched, resolved."""
        return frozenset(self._stamps)

    def poll(self) -> bool:
        """Reloads the view if any watched file changed since the last
        poll. Returns `True` if it reloaded, `False` if nothing changed.

        A reload that fails (a YAML error, a bad component, a spec `tre`
        rejects) raises, naming the file, and leaves the view as it was.
        It raises once per change -- polling again without a further
        edit returns `False` rather than raising the same error again.
        """
        current = {p: _stamp(p) for p in self._stamps}
        if current == self._stamps:
            return False
        # Record what was seen *before* reading, so a write that lands
        # mid-reload is picked up by the next poll instead of lost.
        self._stamps = current
        spec, frames, deps = build_view_spec(self._path, component_dirs=self._component_dirs)
        self._stamps = {p: current[p] if p in current else _stamp(p) for p in deps}
        try:
            self._view.reconcile(spec=spec)
        except ValueError as exc:
            raise ValueError(f"{self._path}: {exc}") from exc
        push_frames(self._view, frames)
        return True
