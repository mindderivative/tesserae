"""Easing layout properties by hand (#239), until tre can: tre refuses to animate `width`, `height`, `x`, `y`, `gap`, `padding` and `margin`
(requested: mindderivative/tre#161), so the framework sets them each frame.

A step is a private, detached box whose `stroke_width` animates 0 to 1 over the duration (the engine's own clock, so `window.advance` drives it in
tests and reduced motion is respected before it starts) and a timer that reads that progress on every frame, applies the easing curve, and sets the
property to the value between where it was and where it is going. `patch` tries `node.animate` first and falls back to this only when the engine
says the property cannot be animated, so a tre that can will be used without a change here.
"""

from __future__ import annotations

from typing import Any, Callable

from tesserae.timers import Timers

__all__ = ["Steps", "curve", "steps_of"]

_REGISTRY: dict[int, "Steps"] = {}


def curve(easing: Any) -> Callable[[float], float]:
    """The easing as a function of progress 0 to 1: `linear`, a cubic bezier `(x1, y1, x2, y2)` as CSS has it, or a spring (drawn as the
    emphasized decelerate curve, which is what a spring settles like without the overshoot)."""
    if easing == "linear":
        return lambda t: min(max(t, 0.0), 1.0)
    if isinstance(easing, tuple) and len(easing) == 4:
        x1, y1, x2, y2 = easing
    else:
        x1, y1, x2, y2 = 0.05, 0.7, 0.1, 1.0

    def bezier(a: float, b: float, t: float) -> float:
        return 3 * a * (1 - t) ** 2 * t + 3 * b * (1 - t) * t * t + t ** 3

    def ease(progress: float) -> float:
        if progress <= 0.0:
            return 0.0
        if progress >= 1.0:
            return 1.0
        low, high = 0.0, 1.0
        for _ in range(24):  # solve x(t) = progress by bisection; x is monotonic for the curves here
            mid = (low + high) / 2
            if bezier(x1, x2, mid) < progress:
                low = mid
            else:
                high = mid
        return bezier(y1, y2, (low + high) / 2)

    return ease


class Steps:
    """The layout transitions running in one window."""

    def __init__(self, window: Any) -> None:
        self.window = window
        self.timers = Timers(window)
        self._running: dict[str, tuple[Any, Any]] = {}  # name -> (clock node, finish)

    @staticmethod
    def _name(target: Any, prop: str) -> str:
        return f"layout:{hash(target)}:{prop}"

    def start(self, target: Any, prop: str, to: Any, ms: float, easing: Any) -> None:
        """Eases `target`'s `prop` from where it is to `to` over `ms`; a value that is not a number (`auto`, a percentage) is set at once."""
        name = self._name(target, prop)
        self.cancel(target, prop)
        start = target.get(prop)
        numbers = all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in (start, to))
        if not numbers or start == to or ms <= 0:
            target.set(**{prop: to})
            return
        shape = curve(easing)
        clock = self.window.create("box", width=0.0, height=0.0)

        def place(progress: float) -> None:
            target.set(**{prop: float(start) + (float(to) - float(start)) * shape(progress)})

        def finish() -> None:
            self.timers.cancel(name)
            self._running.pop(name, None)
            target.set(**{prop: to})

        def tick() -> None:
            place(float(clock.get("stroke_width")))

        clock.animate("stroke_width", 1.0, int(ms), "linear", on_complete=finish)
        self._running[name] = (clock, finish)
        self.timers.every(1, tick, name=name)

    def cancel(self, target: Any, prop: str) -> None:
        name = self._name(target, prop)
        running = self._running.pop(name, None)
        if running is not None:
            running[0].stop_animation("stroke_width")
            self.timers.cancel(name)

    def running(self) -> int:
        return len(self._running)


def steps_of(window: Any) -> Steps:
    """The window's `Steps` (made on first use)."""
    key = id(window)
    steps = _REGISTRY.get(key)
    if steps is None or steps.window is not window:
        steps = _REGISTRY[key] = Steps(window)
    return steps
