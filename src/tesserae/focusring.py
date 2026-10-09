"""The focus ring as a turning gradient (tre 0.5.4's sweep `Gradient`).

With `App(focus_ring="gradient")` the ring of the keyboard-focused node is a sweep gradient through `secondary`, `primary` and `tertiary` that turns once
every `PERIOD_MS`. tre does not animate a gradient on a *stroke* ("set it again"), so Python sets a new start angle every `TICK_MS` while a ring is
showing; one ring shows at a time (the focus is in one place), and an app that asks for reduced motion gets the gradient standing still.
"""

from __future__ import annotations

from typing import Any

import tre

from tesserae import motion

__all__ = ["GradientRing", "use_gradient", "uses_gradient"]

TICK_MS = 33
PERIOD_MS = 3000

_WINDOWS: dict[int, Any] = {}  # a window's id -> the window (an entry holds its window, so a live entry's id is that window's)


def use_gradient(window: Any, on: bool = True) -> None:
    """Gradient focus rings for the nodes on `window` (or, with `on=False`, solid ones). Takes effect for interactions made afterwards."""
    if on:
        _WINDOWS[id(window)] = window
    else:
        _WINDOWS.pop(id(window), None)


def uses_gradient(window: Any) -> bool:
    return id(window) in _WINDOWS


class GradientRing:
    """Turns the `stroke_color` of one ring node while it shows."""

    def __init__(self, window: Any, ring: Any, colors: tuple[Any, Any, Any]) -> None:
        self.window = window
        self.ring = ring
        self.colors = colors
        self.angle = 0.0
        self._timer: Any = None

    def _gradient(self) -> Any:
        first, second, third = self.colors
        return tre.Gradient.sweep([first, second, third, first], start=self.angle % 360.0)

    def recolor(self, colors: tuple[Any, Any, Any], paint: bool = True) -> None:
        self.colors = colors
        if paint:
            self.ring.set(stroke_color=self._gradient())

    def show(self) -> None:
        """Paints the gradient and, unless motion is reduced, starts turning it."""
        self.ring.set(stroke_color=self._gradient())
        if self._timer is None and not motion.reduced(self.window):
            self._timer = self.window.every(TICK_MS, self._tick)

    def hide(self) -> None:
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None

    @property
    def turning(self) -> bool:
        return self._timer is not None

    def _tick(self) -> None:
        self.angle = (self.angle + 360.0 * TICK_MS / PERIOD_MS) % 360.0
        self.ring.set(stroke_color=self._gradient())
