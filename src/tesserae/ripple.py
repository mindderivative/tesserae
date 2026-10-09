"""The press ripple drawn by one shader instead of one node per press (tre 0.5.1's `Shader`).

An `Interaction` normally grows a circle node per press and lets the engine animate its scale and opacity. With `use_shader(window)` (or
`App(ripple="shader")`) the circles are instead one fill shader on a single node, with room for three presses at once: the shader draws each as
a circle with an anti-aliased edge, and Python moves the three `vec4`s (centre x, centre y, radius, opacity) a frame at a time with the same
timing Material Web's `md-ripple` has. Nothing is drawn, and no timer runs, while no ripple is alive. The state layer stays a node: it is a flat
colour whose opacity the engine already eases.

The headless renderer does not draw shaders, so the tests read the uniforms; only a real window shows the pixels.
"""

from __future__ import annotations

import math
from typing import Any

import tre

from tesserae import motion

__all__ = ["RippleShader", "shader_for", "use_shader", "uses_shader"]

SLOTS = 3
TICK_MS = 16
PRESS_GROW_MS = 450
PRESS_FADE_IN_MS = 105
MINIMUM_PRESS_MS = 225
RELEASE_FADE_MS = 375
INITIAL_SCALE = 0.2
PRESSED = 0.10

WGSL = """
fn ring(px: vec2<f32>, r: vec4<f32>) -> f32 {
    let d = distance(px, r.xy);
    return r.w * (1.0 - smoothstep(r.z - 1.0, r.z + 0.5, d));
}

fn shade(p: Pixel) -> vec4<f32> {
    let a0 = ring(p.px, u.r0);
    let a1 = ring(p.px, u.r1);
    let a2 = ring(p.px, u.r2);
    let a = 1.0 - (1.0 - a0) * (1.0 - a1) * (1.0 - a2);
    return vec4<f32>(u.tint.rgb, a * u.tint.a);
}
"""

_WINDOWS: dict[int, Any] = {}  # a window's id -> the window (an entry holds its window, so a live entry's id is that window's)


def use_shader(window: Any, on: bool = True) -> None:
    """Draws the ripples of the nodes on `window` with the shader (or, with `on=False`, back with nodes). Takes effect for interactions made afterwards."""
    if on:
        _WINDOWS[id(window)] = window
    else:
        _WINDOWS.pop(id(window), None)


def uses_shader(window: Any) -> bool:
    return id(window) in _WINDOWS


def shader_for(tint: tuple[int, int, int, int]) -> Any:
    """A new shader for one node (each node has its own uniforms)."""
    return tre.Shader(WGSL, uniforms={"tint": _color(tint), "r0": (0.0,) * 4, "r1": (0.0,) * 4, "r2": (0.0,) * 4})


def _color(tint: tuple[int, int, int, int]) -> tuple[float, float, float, float]:
    return (tint[0] / 255, tint[1] / 255, tint[2] / 255, tint[3] / 255)


def _ease(x: float) -> float:
    """MD3's standard easing, cubic-bezier(0.2, 0, 0, 1), at progress `x`."""
    x = min(1.0, max(0.0, x))
    low, high = 0.0, 1.0
    for _ in range(24):  # solve the curve's x(t) = x by bisection, then read y(t)
        t = (low + high) / 2
        cx = 3 * (1 - t) ** 2 * t * 0.2 + 3 * (1 - t) * t * t * 0.0 + t ** 3
        if cx < x:
            low = t
        else:
            high = t
    t = (low + high) / 2
    return 3 * (1 - t) ** 2 * t * 0.0 + 3 * (1 - t) * t * t * 1.0 + t ** 3


class _Press:
    def __init__(self, x: float, y: float, radius: float, start: float) -> None:
        self.x, self.y, self.radius, self.start = x, y, radius, start
        self.age = 0.0
        self.released = False
        self.fade_age: float | None = None
        self.fade_from = PRESSED

    def opacity(self, window: Any) -> float:
        if self.fade_age is not None:
            fade = max(1.0, motion.duration(window, RELEASE_FADE_MS))
            return self.fade_from * max(0.0, 1.0 - self.fade_age / fade)
        grow = motion.duration(window, PRESS_FADE_IN_MS)
        return PRESSED if grow <= 0 else PRESSED * min(1.0, self.age / grow)

    def size(self, window: Any) -> float:
        grow = motion.duration(window, PRESS_GROW_MS)
        progress = 1.0 if grow <= 0 else _ease(self.age / grow)
        return self.radius * (self.start + (1.0 - self.start) * progress)


class RippleShader:
    """Up to three live presses on `node` (a box in the interaction's clip), drawn by `shader`."""

    def __init__(self, window: Any, node: Any, tint: tuple[int, int, int, int]) -> None:
        self.window = window
        self.node = node
        self.shader = shader_for(tint)
        node.set(shader=self.shader, visible=False)
        self.tint = tint
        self.presses: list[_Press] = []
        self._timer: Any = None

    # -- the presses ---------------------------------------------------------------

    def press(self, x: float | None, y: float | None, width: float, height: float) -> _Press:
        if x is None or y is None:
            x, y = width / 2, height / 2
        radius = max(math.hypot(x - cx, y - cy) for cx in (0.0, width) for cy in (0.0, height)) or 1.0
        start = min(1.0, INITIAL_SCALE * max(width, height) / (2 * radius))
        if len(self.presses) >= SLOTS:  # the oldest gives way
            self.presses.pop(0)
        press = _Press(x, y, radius, start)
        self.presses.append(press)
        self.node.set(visible=True)
        self._write()
        if self._timer is None:
            self._timer = self.window.every(TICK_MS, self._tick)
        return press

    def release(self, press: _Press | None = None) -> None:
        for each in ([press] if press is not None else list(self.presses)):
            each.released = True

    def clear(self) -> None:
        self.presses = []
        self._finish()

    def retint(self, tint: tuple[int, int, int, int]) -> None:
        self.tint = tint
        self._write()

    def detach(self) -> None:
        self.presses = []
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None

    # -- time ------------------------------------------------------------------------

    def _tick(self) -> None:
        for press in list(self.presses):
            press.age += TICK_MS
            held = motion.duration(self.window, MINIMUM_PRESS_MS)
            if press.fade_age is None and press.released and press.age >= held:
                press.fade_from = press.opacity(self.window)
                press.fade_age = 0.0
            elif press.fade_age is not None:
                press.fade_age += TICK_MS
                if press.opacity(self.window) <= 0.0:
                    self.presses.remove(press)
        if not self.presses:
            self._finish()
        else:
            self._write()

    def _finish(self) -> None:
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None
        self._write()
        self.node.set(visible=bool(self.presses))

    def _write(self) -> None:
        slots = [(p.x, p.y, p.size(self.window), p.opacity(self.window)) for p in self.presses]
        slots += [(0.0, 0.0, 0.0, 0.0)] * (SLOTS - len(slots))
        self.shader.set(uniforms={"tint": _color(self.tint), "r0": slots[0], "r1": slots[1], "r2": slots[2]})
