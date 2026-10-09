"""Named timers on the window's clock (#217): `after(ms, fn)`, `every(ms, fn)` and cancelling them.

The window's own `after` and `every` (tre 0.5.6) run them, so `window.advance` moves them and an idle window sleeps until the next one. This
adds the names: the handlers of a view reach them as `after(ms, action)`, `every(ms, action)` and `cancel(name)`; Python gets `Timers` directly.

```python
timers = Timers(window)
timers.after(2000, snackbar.dismiss, name="dismiss")     # starting a timer of the same name again restarts it
timers.every(500, tick)
timers.cancel("dismiss")
```

A timer of a given name is one at a time: a second `after` or `every` of that name replaces the first (a debounce or a restartable delay). A
timer with no name cannot be cancelled except with `cancel_all`.
"""

from __future__ import annotations

from typing import Any, Callable, Optional

__all__ = ["Timers"]

class Timers:
    """The timers of one window. `after` and `every` return the timer's name (given, or made up) for `cancel`."""

    def __init__(self, window: Any) -> None:
        self._window = window
        self._timers: dict[str, Any] = {}
        self._count = 0

    def after(self, ms: float, fn: Callable[[], Any], name: Optional[str] = None) -> str:
        """Runs `fn()` once, `ms` milliseconds from now."""
        return self._start(ms, fn, False, name)

    def every(self, ms: float, fn: Callable[[], Any], name: Optional[str] = None) -> str:
        """Runs `fn()` every `ms` milliseconds until cancelled."""
        return self._start(ms, fn, True, name)

    def cancel(self, name: str) -> bool:
        """Stops the timer `name`; `False` when there is none (it already ran, or was cancelled)."""
        timer = self._timers.pop(name, None)
        if timer is None:
            return False
        timer.cancel()
        return True

    def cancel_all(self) -> None:
        for name in list(self._timers):
            self.cancel(name)

    def running(self, name: str) -> bool:
        return name in self._timers

    def _start(self, ms: float, fn: Callable[[], Any], repeat: bool, name: Optional[str]) -> str:
        what = "every" if repeat else "after"
        if isinstance(ms, bool) or not isinstance(ms, (int, float)) or ms != ms or ms < 0 or ms == float("inf"):
            raise ValueError(f"{what}: the time is milliseconds, 0 or more, not {ms!r}")
        if not callable(fn):
            raise ValueError(f"{what}: needs something to run, not {fn!r}")
        if name is None:
            self._count += 1
            name = f"#{self._count}"
        elif not isinstance(name, str) or not name:
            raise ValueError(f"{what}: a timer's name is text, not {name!r}")
        self.cancel(name)

        def fire() -> None:
            if not repeat:
                self._timers.pop(name, None)  # before `fn`, so one that starts the same name again is not undone
            fn()

        start = self._window.every if repeat else self._window.after
        self._timers[name] = start(float(ms), fire)
        return name
