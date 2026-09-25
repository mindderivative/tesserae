"""M29 Phase 3: Tesserae-owned hot reload, replacing `tre`'s own
`poll_reload` (which watched a file `tre` itself read -- `tre` now reads
none).

A view depends on more than its own file: every `include:`d file, every
`*_Component.yaml` fragment it expanded, and every image it decodes. A
change to any of them re-runs the whole Tesserae pipeline
(`build_view_spec`, the same one `load_view` runs) and hands `tre` the
result via `view.reconcile(spec=...)`, which keeps unchanged widgets'
`NodeId`s, focus and in-flight animations. Images are pushed again
afterwards. The set of watched files is recomputed on every reload, so
a newly added `include:`, fragment or image is watched from then on.

Two ways to drive it:

- **`start(handle)`** -- the user's own choice for reloading inside
  `App.run()`: a background thread watches for file-change events with
  `watchfiles`, rebuilds the spec there (all file I/O and expansion stay
  off the UI thread), and hands only `reconcile` + `push_frame` to the
  event loop through `tre`'s thread-safe `LoopHandle.call_soon` (tre M87,
  tre issue #6). `App.run(hot_reload=True)` does this for every screen.
- **`poll()`** -- no thread: checks each file's modification time and
  size. For a loop the app controls itself.

`tre`'s `View` is single-threaded (`unsendable`): only the `LoopHandle`
crosses threads, and the watcher thread never touches the view.
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any, Callable, Optional, Tuple

import watchfiles

from tesserae.spec.images import Frame, push_frames
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


def _reraise(exc: BaseException) -> Callable[[], None]:
    def reraise() -> None:
        raise exc

    return reraise


class ViewWatcher:
    """Watches every file `view` was built from and reloads it on change.

    Create it right after `load_view(path, ...)`, with the same `path`
    and `component_dirs`. Inside `App.run()`, start it with the app's
    thread handle (or just use `App.run(hot_reload=True)`):

    ```python
    watcher = ViewWatcher(view, "Home_View.yaml")
    watcher.start(tre_app.thread_handle())
    ...
    watcher.stop()
    ```

    Or, in a loop the app controls itself, call `poll()` regularly.
    """

    def __init__(self, view: Any, path: str | Path, *, component_dirs: list[Path] | None = None) -> None:
        self._view = view
        self._path = Path(path)
        self._component_dirs = component_dirs
        _, _, deps = self._rebuild()
        self._stamps: dict[Path, _Stamp] = {p: _stamp(p) for p in deps}
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    @property
    def files(self) -> frozenset[Path]:
        """Every file currently being watched, resolved."""
        return frozenset(self._stamps)

    @property
    def running(self) -> bool:
        """Whether `start()`'s background thread is watching."""
        return self._thread is not None and self._thread.is_alive()

    def _rebuild(self) -> tuple[Any, list[Frame], set[Path]]:
        """All the file work -- safe on any thread."""
        return build_view_spec(self._path, component_dirs=self._component_dirs)

    def _apply(self, spec: Any, frames: list[Frame]) -> None:
        """The `tre` part -- only on the thread that owns the view."""
        try:
            self._view.reconcile(spec=spec)
        except ValueError as exc:
            raise ValueError(f"{self._path}: {exc}") from exc
        push_frames(self._view, frames)

    # -- no thread -------------------------------------------------

    def poll(self) -> bool:
        """Reloads the view if any watched file changed since the last
        poll. Returns `True` if it reloaded, `False` if nothing changed.

        A reload that fails (a YAML error, a bad component, a spec `tre`
        rejects) raises, naming the file, and leaves the view as it was.
        It raises once per change -- polling again without a further
        edit returns `False` rather than raising the same error again.
        """
        if self.running:
            raise RuntimeError("ViewWatcher.poll() while start()'s watcher thread is running")
        current = {p: _stamp(p) for p in self._stamps}
        if current == self._stamps:
            return False
        # Record what was seen *before* reading, so a write that lands
        # mid-reload is picked up by the next poll instead of lost.
        self._stamps = current
        spec, frames, deps = self._rebuild()
        self._stamps = {p: current[p] if p in current else _stamp(p) for p in deps}
        self._apply(spec, frames)
        return True

    # -- background thread (watchfiles) -----------------------------

    def start(self, handle: Any) -> None:
        """Starts watching on a background thread. `handle` is
        `tre.App.thread_handle()`'s `LoopHandle`; each reload is queued
        on it with `call_soon`, so it runs on the event-loop thread.

        A failed reload is queued too, as a callable that raises -- `tre`
        logs it the way it logs an input handler's exception, and the
        loop, and the watcher, carry on.
        """
        if self._thread is not None:
            raise RuntimeError("ViewWatcher.start() called twice without stop()")
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._watch, args=(handle,), name=f"tesserae-watch:{self._path.name}", daemon=True
        )
        self._thread.start()

    def stop(self, timeout: float = 5.0) -> None:
        """Stops the background thread and waits for it to finish."""
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout)
            self._thread = None

    def _watch(self, handle: Any) -> None:
        try:
            while not self._stop.is_set():
                dirs = sorted({p.parent for p in self._stamps if p.parent.is_dir()})
                if not dirs:
                    self._stop.wait(0.5)
                    continue
                for _changes in watchfiles.watch(
                    *dirs,
                    watch_filter=lambda _change, changed: Path(changed).resolve() in self._stamps,
                    stop_event=self._stop,
                    recursive=False,
                ):
                    try:
                        spec, frames, deps = self._rebuild()
                    except Exception as exc:
                        handle.call_soon(_reraise(exc))
                        continue
                    self._stamps = {p: _stamp(p) for p in deps}
                    handle.call_soon(lambda spec=spec, frames=frames: self._apply(spec, frames))
                    if sorted({p.parent for p in deps if p.parent.is_dir()}) != dirs:
                        break  # a dependency moved to a new directory: re-watch
        except Exception as exc:  # the watcher itself failed; report it, don't die silently
            handle.call_soon(_reraise(exc))
