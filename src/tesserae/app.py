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
from typing import Any

from tre import App as _TreApp
from tre import Window


@dataclass
class _Registered:
    view: Any
    viewmodel: Any


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

    def register(self, name: str, view: Any, viewmodel: Any) -> None:
        """Registers `view` (already loaded, e.g. `View("Foo_View.yaml")`)
        and its already-`_attach`ed `viewmodel` (e.g. `FooViewModel(view)`)
        under `name`, for a later `show(name)` to display. Raises if
        `name` is already registered -- a real, load-bearing collision a
        caller should know about immediately, not silently overwrite.
        """
        if name in self._registered:
            raise ValueError(f"a view named {name!r} is already registered")
        self._registered[name] = _Registered(view, viewmodel)

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

    def run(self, max_frames: int | None = None) -> None:
        """The one blocking call -- opens the real `Window` `show()` has
        already built and runs `tre`'s own real render loop. `max_frames`
        is the identical headless-CI-safe convention `tre`'s own examples
        already use (TRE v1 finding #261) -- omit it for a real,
        interactive run that exits only when the window closes.
        """
        if self._window is None:
            raise RuntimeError("App.run() called before show() -- nothing to display yet")
        tre_app = _TreApp()
        tre_app.add_window(self._window)
        tre_app.run(max_frames=max_frames)
