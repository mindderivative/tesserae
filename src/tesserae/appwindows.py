"""More than one OS window: `app.open_window("Settings")`.

`app.window` stays the app's main window. Every other window is an `AppWindow`: its `tre` window, the view built in it, and what it takes to open, close
and (for a dialog) block its parent. Closing the main window closes the others and ends the app; closing another leaves the app running.

A view in another window is composed like any other (its ViewModel is the one that serves its name; the theme, the stylesheet and `app` are the app's), and a
`widget: Window` at its root sets that window's title, size, minimum size, borderless and flags. What a second window does not have: screens and routes (those
belong to the main window's frame), and a title bar whose maximize button follows its own window (the bar reads `app.maximized`, the main window's).

tre opens a window while the app runs since 0.5.6; before `run()` a window waits and opens with the others. It has no owner or modal window, so `modal=True` is done
here: the parent shows a scrim layer that takes its input until the child closes.
"""

from __future__ import annotations

from typing import Any, Callable, Optional

from tesserae.reactive import Signal

__all__ = ["AppWindow"]


class AppWindow:
    """One window of an app besides the main one. `name` is how `app.window_of(name)` finds it; `view` is the `ComposedView` built in it."""

    def __init__(self, app: Any, name: str, window: Any, view: Any, parent: Optional[Any] = None, modal: bool = False) -> None:
        self.app = app
        self.name = name
        self.window = window
        self.view = view
        self.parent = parent
        self.modal = modal
        self.closed = Signal(False)
        self._on_closed: list[Callable[[], None]] = []
        self._scrim: Any = None
        self._maximized = Signal(False)
        self.maximized = self._maximized.get

    # -- what a window does ----------------------------------------------------------------------------------------

    def close(self) -> None:
        """Closes the window as the user's close would (`close_requested` first, which can cancel it)."""
        self.window.close()

    def minimize(self) -> None:
        self.window.minimize()

    def maximize(self) -> None:
        self.window.maximize()

    def restore(self) -> None:
        self.window.restore()

    def toggle_maximized(self) -> None:
        self.restore() if self.window.get("maximized") else self.maximize()

    def center(self) -> bool:
        """Centres the window on its monitor, where the system lets an app place a window (not Wayland); False when it cannot."""
        try:
            return bool(self.window.center())
        except (ValueError, TypeError, RuntimeError):
            return False

    def on_close(self, fn: Callable[[], None]) -> None:
        """Calls `fn()` once the window has closed."""
        self._on_closed.append(fn)

    # -- the app's side ----------------------------------------------------------------------------------------------

    def _block_parent(self) -> None:
        """A modal window's parent takes no input while it is open: a full-window scrim in a modal layer, which tre keeps the focus inside."""
        parent = self.parent.window if self.parent is not None else self.app.window
        scrim = parent.create("box", position="absolute", x=0, y=0, width=float(parent.get("width")), height=float(parent.get("height")),
                              fill=(0, 0, 0, 82), a11y_hidden=True)
        parent.show_layer(scrim, modal=True, dismissible=False)
        self._scrim = (parent, scrim)

    def _closed(self) -> None:
        if self.closed.get():
            return
        self.closed.set(True)
        if self._scrim is not None:
            parent, scrim = self._scrim
            self._scrim = None
            try:
                parent.hide_layer(scrim)
            except (ValueError, RuntimeError):
                pass  # the parent is gone too
        try:
            self.view.close()
        except (ValueError, RuntimeError):
            pass
        for fn in self._on_closed:
            fn()
