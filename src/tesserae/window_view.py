"""A `kind: Window` view loaded by an app (0.4.4): its ViewModel, and the frame it is.

`app.load("Window")` loads a `Window_View.yaml` whose root is `kind: Window`. It is the app's frame: mounted in the OS window
once, for as long as the app runs, with the screens (`view:` nodes with a `route:`) shown inside it. A window view needs no
ViewModel of its own (its title bar's buttons reach the app through one, so an empty `WindowViewModel` is made when
`Window_ViewModel.py` isn't there). There is one per app.
"""

from __future__ import annotations

from typing import Any

from tesserae.reactive import ViewModel

__all__ = ["Frame", "WindowViewModel"]


class WindowViewModel(ViewModel):
    """What a window view with no `*_ViewModel.py` of its own gets: nothing but `self.app` and `self.state`, which are what a
    title bar's bindings (`app.maximized`, `app.active`, ...) read."""


class Frame:
    """The window view an app is showing: its name, its view, and where screens go in it."""

    def __init__(self, app: Any, name: str, view: Any) -> None:
        self.app = app
        self.name = name
        self.view = view

    def show_screen(self, root: Any, name: str, previous: Any) -> None:
        raise ValueError(f"the window view {self.name!r} has no place for the screen {name!r}: a screen is a `view:` "
                         "with a `route:` in the window view")
