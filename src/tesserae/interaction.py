"""MD3 interaction feedback (M39): a state layer and a ripple, built from
`tre` 0.3.4's building blocks, since `tre` 0.3.5 draws none (`tre` D7).

A node that gets an `Interaction` holds two kinds of extra child, both
absolutely positioned, never hit-tested, and clipped to the node's rounded
box (`clip_children`):

- **The state layer**, a box covering the node, in the tint. Its opacity
  is the strongest state the node is in: dragged 16%, else focused 10% (on
  keyboard focus only, `focus_visible`), else hovered 8%.
- **Ripples**, one per press: a circle centred on the press point that
  grows until it covers the node while the press is held, at the pressed
  opacity (10%), and fades once it's released. A keyboard click (Enter or
  Space) ripples from the centre.

The opacities are MD3's state-layer values; the ripple's timing is Material
Web's (`md-ripple`), MD3's reference implementation. Both paint over the
node's content, as in Material Web and Compose. Views apply this to
clickable YAML nodes (`tesserae.view`); M40's widgets use it directly.
"""

from __future__ import annotations

import math
from typing import Any, Callable

__all__ = ["DRAGGED", "FOCUSED", "HOVERED", "Interaction", "PRESSED"]

RGBA = tuple[int, int, int, int]
#: A listener registrar: `listen(node, event, fn)` returns a function
#: that removes the listener (`tre` keeps one listener per event, so the
#: caller shares a dispatcher between everyone listening on a node).
Listen = Callable[[Any, str, Callable[[Any], None]], Callable[[], None]]

#: MD3's state-layer opacities.
HOVERED, FOCUSED, PRESSED, DRAGGED = 0.08, 0.10, 0.10, 0.16

#: Material Web's `md-ripple` timing, in ms.
HOVER_MS = 15
PRESS_GROW_MS = 450
PRESS_FADE_IN_MS = 105
MINIMUM_PRESS_MS = 225
RELEASE_FADE_MS = 375
#: The ripple starts at this fraction of the node's larger side.
INITIAL_SCALE = 0.2
#: MD3's standard easing, which `md-ripple` grows with.
STANDARD = (0.2, 0.0, 0.0, 1.0)


class Interaction:
    """The state layer and ripple on one `box` node, tinted `tint`.

    `listen` registers the pointer and focus listeners (see `Listen`).
    Call `detach()` to remove everything this added."""

    def __init__(self, window: Any, node: Any, tint: RGBA, listen: Listen) -> None:
        self.window = window
        self.node = node
        self.tint = tint
        self.hovered = self.focused = self.dragged = False
        self._ripples: list[_Ripple] = []
        self._clipped = node.get("clip_children")
        node.set(clip_children=True)
        self.layer = window.create("box", position="absolute", x=0, y=0, width="100%", height="100%",
                                   fill=tint, opacity=0.0, hit_testable=False)
        node.add_child(self.layer)
        _INTERACTIVE.append(node)
        self._undo = [listen(node, event, handler) for event, handler in (
            ("pointer_enter", self._on_enter), ("pointer_leave", self._on_leave),
            ("pointer_down", self._on_down), ("pointer_up", self._on_up), ("click", self._on_click),
            ("focus", self._on_focus), ("unfocus", self._on_unfocus),
        )]

    # -- state --------------------------------------------------------------

    @property
    def opacity(self) -> float:
        """The state layer's resting opacity for the current state."""
        if self.dragged:
            return DRAGGED
        if self.focused:
            return FOCUSED
        return HOVERED if self.hovered else 0.0

    @property
    def ripples(self) -> list[Any]:
        """The live ripples' circle nodes, oldest first."""
        return [ripple.circle for ripple in self._ripples]

    def set_dragged(self, dragged: bool) -> None:
        """For widgets that drag (M40): MD3's dragged state."""
        self.dragged = dragged
        self._update()

    def retint(self, tint: RGBA) -> None:
        """A new tint (a theme change), for the layer and live ripples."""
        self.tint = tint
        self.layer.set(fill=tint)
        for ripple in self._ripples:
            ripple.circle.set(fill=tint)

    def detach(self) -> None:
        """Removes the listeners, the layer and any ripples. Safe after the
        node itself was destroyed."""
        for undo in self._undo:
            _quietly(undo)
        self._undo = []
        for node in [self.layer, *self.ripples]:
            _quietly(node.destroy)
        self._ripples = []
        if self.node in _INTERACTIVE:
            _INTERACTIVE.remove(self.node)
        _quietly(lambda: self.node.set(clip_children=self._clipped))

    def _update(self) -> None:
        self.layer.animate("opacity", self.opacity, HOVER_MS)

    # -- events ------------------------------------------------------------

    def _mine(self, event: Any) -> bool:
        """Whether a bubbled event is this node's: no nearer interactive
        node sits between its target and this one."""
        node = event.target
        while node is not None and node != self.node:
            if node in _INTERACTIVE:
                return False
            node = node.parent()
        return True

    def _on_enter(self, event: Any) -> None:
        self.hovered = True
        self._update()

    def _on_leave(self, event: Any) -> None:
        self.hovered = False
        self._update()
        self._release_all()  # a press dragged off the node is cancelled

    def _on_down(self, event: Any) -> None:
        if self._mine(event) and event.x is not None:
            self._ripples.append(_Ripple(self, event.x, event.y))

    def _on_up(self, event: Any) -> None:
        self._release_all()

    def _on_click(self, event: Any) -> None:
        # A keyboard click has no position, and no press came first.
        if event.x is None and self._mine(event):
            ripple = _Ripple(self, None, None)
            self._ripples.append(ripple)
            ripple.release()

    def _on_focus(self, event: Any) -> None:
        if event.target == self.node:
            self.focused = bool(event.focus_visible)
            self._update()

    def _on_unfocus(self, event: Any) -> None:
        if event.target == self.node:
            self.focused = False
            self._update()

    def _release_all(self) -> None:
        for ripple in list(self._ripples):
            ripple.release()


class _Ripple:
    """One press's ripple. `x`/`y` are local to the node; `None` ripples
    from the centre."""

    def __init__(self, owner: Interaction, x: Any, y: Any) -> None:
        self.owner = owner
        self.released = False
        self.held_long_enough = False
        node = owner.node
        width, height = node.get("layout_width") or 0.0, node.get("layout_height") or 0.0
        if x is None:
            x, y = width / 2, height / 2
        # Big enough to cover the node from the press point.
        radius = max(math.hypot(x - cx, y - cy) for cx in (0.0, width) for cy in (0.0, height)) or 1.0
        start = min(1.0, INITIAL_SCALE * max(width, height) / (2 * radius))
        self.circle = owner.window.create(
            "box", position="absolute", x=x - radius, y=y - radius, width=2 * radius, height=2 * radius,
            corner_radius=radius, fill=owner.tint, opacity=0.0, scale=start, hit_testable=False)
        node.add_child(self.circle)
        self.circle.animate("scale", 1.0, PRESS_GROW_MS, easing=STANDARD)
        self.circle.animate("opacity", PRESSED, PRESS_FADE_IN_MS)
        # `tre` has no timers; an invisible animation of the circle's
        # stroke width stands in for one, so a quick tap still shows.
        self.circle.animate("stroke_width", 0.001, MINIMUM_PRESS_MS, on_complete=self._held)

    def _held(self) -> None:
        self.held_long_enough = True
        if self.released:
            self._fade()

    def release(self) -> None:
        if self.released:
            return
        self.released = True
        if self.held_long_enough:
            self._fade()

    def _fade(self) -> None:
        self.circle.animate("opacity", 0.0, RELEASE_FADE_MS, on_complete=self._done)

    def _done(self) -> None:
        if self in self.owner._ripples:
            self.owner._ripples.remove(self)
        _quietly(self.circle.destroy)


#: Every node with an `Interaction`, so a bubbled press ripples only the
#: nearest. Each `Interaction` adds its node, and `detach` removes it.
_INTERACTIVE: list[Any] = []


def _quietly(fn: Callable[[], Any]) -> None:
    try:
        fn()
    except (ValueError, RuntimeError):
        pass  # the node is already gone
