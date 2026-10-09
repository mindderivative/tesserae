"""Timers on the frame loop (#217): `after(ms, fn)`, `every(ms, fn)` and cancelling them.

tre has no timers yet (a request is #235), so a timer is an animation of a private box that is in no tree, which runs with the window's
frames and finishes after the time asked for. The handlers of a view reach them as `after(ms, action)`, `every(ms, action)` and
`cancel(name)`; Python gets `Timers` directly.

```python
timers = Timers(window)
timers.after(2000, snackbar.dismiss, name="dismiss")     # starting a timer of the same name again restarts it
timers.every(500, tick)
timers.cancel("dismiss")
```

A timer of a given name is one at a time: a second `after` or `every` of that name replaces the first (a debounce or a restartable delay). A
timer with no name cannot be cancelled except with `cancel_all`. An exception in `fn` stops that timer and is raised from the frame.
"""

from __future__ import annotations

from typing import Any, Callable, Optional

__all__ = ["Timers"]

class _Timer:
    def __init__(self, window: Any, ms: float, fn: Callable[[], Any], repeat: bool, done: Callable[["_Timer"], None]) -> None:
        self.node = window.create("box", width=0.0, height=0.0)
        self.ms, self.fn, self.repeat, self.done = ms, fn, repeat, done
        self.live = True
        self._arm()

    def _arm(self) -> None:
        self.node.stop_animation("stroke_width")
        self.node.set(stroke_width=0.0)
        self.node.animate("stroke_width", 1.0, int(self.ms), on_complete=self._fire)

    def _fire(self) -> None:
        if not self.live:
            return
        if self.repeat:
            self._arm()  # first, so a `fn` that cancels this timer stops the next round
        else:
            self.live = False
            self.done(self)
        self.fn()

    def stop(self) -> None:
        self.live = False
        self.node.stop_animation("stroke_width")


class Timers:
    """The timers of one window. `after` and `every` return the timer's name (given, or made up) for `cancel`."""

    def __init__(self, window: Any) -> None:
        self._window = window
        self._timers: dict[str, _Timer] = {}
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
        timer.stop()
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

        def done(timer: _Timer) -> None:
            self._timers.pop(name, None)

        self._timers[name] = _Timer(self._window, float(ms), fn, repeat, done)
        return name
