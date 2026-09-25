"""`App` -- the real, single Tesserae entry point every real `app.py`
owns exactly one of, per the user's own explicit design requirement:
"app.py should be the entry point for the app... this allows for
switching of current views without needing to bootstrap each
view/viewModel."

Owns a registry of named `(View, ViewModel)` pairs -- each `*_View.yaml`
+ `*_ViewModel.py` file pair a real app registers once, up front -- and
exactly one live `tre.Window`. `App.show(name)` switches which
registered pair that one `Window` currently renders, via `tre.Window
.show_view` (TRE M42 Phase 2) on every call after the first (which
instead builds the `Window` for real, via `tre.Window.from_view`, TRE
M42 Phase 1). Neither a `View` nor its `ViewModel` is ever re-parsed,
re-attached, or otherwise re-bootstrapped by a later `show()` call --
each stays alive, its own `Signal` subscriptions intact, for the whole
life of the `App`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tre import App as _TreApp
from tre import Window

from tesserae.naming import check_naming_convention
from tesserae.spec import ViewWatcher, load_view


@dataclass
class _Registered:
    view: Any
    viewmodel: Any
    #: The `*_View.yaml` it was loaded from -- set by `load()`, so
    #: `run(hot_reload=True)` knows what to watch. `None` for a pair
    #: given to `register()` directly.
    path: Path | None = None


class App:
    """`width`/`height`/`title` describe the one real `Window` this
    `App` opens the first time `show()` is called -- every registered
    view is shown inside that same window, at whatever size it already
    is, not its own independent size (matching `Window.show_view`'s own
    real, stated scope: only the *currently* active view's `width`/
    `height` are kept in sync with the window).
    """

    def __init__(self, width: int = 480, height: int = 320, title: str = "Tesserae App") -> None:
        self._width = width
        self._height = height
        self._title = title
        self._registered: dict[str, _Registered] = {}
        self._window: Window | None = None
        self._current: str | None = None
        self._tre_app: _TreApp | None = None

    def register(self, name: str, view: Any, viewmodel: Any) -> None:
        """Registers `view` (already loaded, e.g. `tesserae.spec.load_view("Foo_View.yaml")`)
        and its already-`_attach`ed `viewmodel` (e.g. `FooViewModel(view)`)
        under `name`, for a later `show(name)` to display. Raises if
        `name` is already registered -- a real, load-bearing collision a
        caller should know about immediately, not silently overwrite.
        """
        if name in self._registered:
            raise ValueError(f"a view named {name!r} is already registered")
        self._registered[name] = _Registered(view, viewmodel)

    def load(
        self, view_path: str | Path, viewmodel_cls: type, name: str | None = None
    ) -> tuple[Any, Any]:
        """Loads a `*_View.yaml` + `*_ViewModel.py` pair and registers it
        -- the real, enforced-at-runtime counterpart to `README.md`'s own
        documented naming convention (previously convention-only, not
        checked). Mirrors pyCopper's own real, validated design (see
        `ARCHITECTURE.md`): a `ViewModel` is scoped one-per-view-file, so
        catching a mismatched pair immediately, at load time, is worth
        more than a cryptic failure much later when a handler name
        doesn't resolve.

        `tre.View` doesn't expose its own source path back to Python
        (confirmed by reading `view.rs` before writing this -- `path` is
        a private Rust field), so this takes `view_path` directly rather
        than trying to recover it from an already-constructed `View` --
        the caller already has it (it's what they'd otherwise pass to
        `View(...)` themselves).

        `name` defaults to the shared prefix (e.g. `"Counter"` for
        `Counter_View.yaml`/`Counter_ViewModel.py`) -- only needed
        explicitly if two different pairs would otherwise collide on it.

        Constructed via `tesserae.spec.load_view` (not `tre.View`
        directly) -- transparent `component: Name`/`with: {...}` macro
        expansion for any screen that uses it, a true no-op for one that
        doesn't (`load_view`'s own real design). Real, current scope
        limit: no `theme_seed`/`custom_theme`/`stylesheet`/`dark`
        forwarding here yet -- `App.load()` never accepted any of those
        before this change either, so this is a real, additive widening
        for `component:` support, not a narrowing of anything that
        already worked.

        Returns the constructed `(view, viewmodel)` pair -- most real
        `app.py` scripts won't need it (everything from here on happens
        through `show()`/registered handlers), but a caller that wants a
        `Node` handle to dispatch a synthetic click/test against, or the
        `ViewModel` itself to read a `Signal` back, still can.
        """
        view_path = Path(view_path)
        prefix = check_naming_convention(view_path, viewmodel_cls)

        view = load_view(view_path)
        viewmodel = viewmodel_cls(view)
        self.register(name or prefix, view, viewmodel)
        self._registered[name or prefix].path = view_path
        return view, viewmodel

    def show(self, name: str) -> Window:
        """Shows the view registered under `name`. The very first call
        opens the real `Window` (`Window.from_view`); every call after
        that switches the same live `Window` to `name`'s own view
        (`Window.show_view`) instead of opening a second one.
        """
        registered = self._registered.get(name)
        if registered is None:
            raise KeyError(f"no view registered under {name!r} -- call register() first")
        if self._window is None:
            self._window = Window.from_view(
                registered.view, width=self._width, height=self._height, title=self._title
            )
        else:
            self._window.show_view(registered.view)
        self._current = name
        return self._window

    @property
    def current(self) -> str | None:
        """The name last passed to `show()`, or `None` before the first
        real call -- lets a registered handler ask "which screen is this,
        anyway" without the app keeping its own separate bookkeeping.
        """
        return self._current

    def thread_handle(self) -> Any:
        """`tre`'s thread-safe `LoopHandle` for this app (tre M87): the one
        object that may cross threads. `handle.call_soon(fn)` runs `fn`
        (no arguments) on the event-loop thread at the next frame, waking
        an idle loop -- the way for a background thread to touch a view,
        since views may only be used from the thread that created them.
        Usable before `run()`; a callable queued then runs on the first
        frame.
        """
        if self._tre_app is None:
            self._tre_app = _TreApp()
        return self._tre_app.thread_handle()

    def run(self, max_frames: int | None = None, *, hot_reload: bool = False) -> None:
        """The one blocking call -- opens the real `Window` `show()` has
        already built and runs `tre`'s own real render loop. `max_frames`
        is the identical headless-CI-safe convention `tre`'s own examples
        already use (TRE v1 finding #261) -- omit it for a real,
        interactive run that exits only when the window closes.

        `hot_reload=True` (M29) watches every screen registered through
        `load()` -- its view file and everything it was built from -- and
        reloads it in place while the app runs. Each screen gets a
        `ViewWatcher` on a background thread (`watchfiles`), which hands
        its reloads to the event loop through `tre`'s thread-safe
        `App.thread_handle()` (tre M87). A failed reload is logged by
        `tre` like a handler's exception; the app keeps running. Screens
        given to `register()` directly have no known file and aren't
        watched.
        """
        if self._window is None:
            raise RuntimeError("App.run() called before show() -- nothing to display yet")
        if self._tre_app is None:
            self._tre_app = _TreApp()
        tre_app = self._tre_app
        tre_app.add_window(self._window)
        watchers: list[ViewWatcher] = []
        try:
            if hot_reload:
                handle = tre_app.thread_handle()
                for registered in self._registered.values():
                    if registered.path is not None:
                        watcher = ViewWatcher(registered.view, registered.path)
                        watcher.start(handle)
                        watchers.append(watcher)
            tre_app.run(max_frames=max_frames)
        finally:
            for watcher in watchers:
                watcher.stop()
            # A later run() starts from a fresh tre App, as before
            # thread_handle() existed; a handle from this run is spent.
            self._tre_app = None
