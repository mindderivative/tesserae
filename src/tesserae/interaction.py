"""MD3 interaction feedback (M39): a state layer and a ripple, built from
`tre` 0.3.4's building blocks, since `tre` 0.3.5 draws none (`tre` D7).

A node that gets an `Interaction` holds two extra children, after its
content, absolutely positioned, never hit-tested and hidden from
assistive technology:

- **A clip box** covering the node, clipped to the node's rounded box,
  holding:
  - **the state layer**, in the tint. Its opacity is the strongest state
    the node is in: dragged 16%, else focused 10% (keyboard focus only,
    `focus_visible`), else hovered 8%;
  - **ripples**, one per press: a circle centred on the press point that
    grows until it covers the node while the press is held, at the
    pressed opacity (10%), and fades once it's released. A keyboard
    click (Enter or Space) ripples from the centre.
- **The focus ring**, shown on keyboard focus only: MD3's focus indicator,
  3 px in `secondary`, 2 px outside the node and following its corners.

The opacities and the ring are MD3's; the ripple's timing is Material
Web's (`md-ripple`), MD3's reference implementation. The layer and ripples
paint over the node's content, as in Material Web and Compose. The node
itself isn't clipped, so its children and the ring can overflow it. Views
apply this to clickable YAML nodes (`tesserae.view`); M40's widgets use
it directly.
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
#: MD3's focus indicator, in px: its thickness, and its gap outside the node.
RING_WIDTH = 3.0
RING_OFFSET = 2.0
#: The ripple starts at this fraction of the node's larger side.
INITIAL_SCALE = 0.2
#: MD3's standard easing, which `md-ripple` grows with.
STANDARD = (0.2, 0.0, 0.0, 1.0)


class Interaction:
    """The state layer, ripple and focus ring on one `box` node: the layer
    and ripple tinted `tint`, the ring `ring_color`.

    `listen` registers the pointer and focus listeners (see `Listen`).
    `surface`, a child of `node`, is where the layer, ripples and ring are
    drawn and sized, when that isn't the node itself: a selection
    control's 40 px circle inside its 48 px touch target (M40). Events
    still come from `node`. `ring_around` is where the focus ring goes,
    when that isn't the surface (a switch's track, not its moving handle). `enabled = False` shows no feedback (a
    disabled control). Call `refresh()` after the surface's corners
    change, and `detach()` to remove everything this added."""

    def __init__(self, window: Any, node: Any, tint: RGBA, listen: Listen, ring_color: RGBA,
                 surface: Any = None, ring_around: Any = None) -> None:
        self.window = window
        self.node = node
        self.surface = node if surface is None else surface
        self.ring_around = self.surface if ring_around is None else ring_around
        self._enabled = True
        self.tint = tint
        self.ring_color = ring_color
        self.hovered = self.focused = self.dragged = False
        self._ripples: list[_Ripple] = []
        decoration = dict(position="absolute", hit_testable=False, a11y_hidden=True)
        self.clip = window.create("box", x=0, y=0, width="100%", height="100%", clip_children=True,
                                  **decoration)
        self.layer = window.create("box", x=0, y=0, width="100%", height="100%", fill=tint, opacity=0.0,
                                   **decoration)
        self.ring = window.create("box", stroke_color=ring_color, stroke_width=RING_WIDTH, visible=False,
                                  **decoration)
        self.clip.add_child(self.layer)
        self.surface.add_child(self.clip)
        self.ring_around.add_child(self.ring)
        self.refresh()
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
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, enabled: bool) -> None:
        """Turning it off clears the feedback at once and shows none until
        it's turned on again."""
        self._enabled = enabled
        if not enabled:
            self.hovered = self.focused = self.dragged = False
            self.ring.set(visible=False)
            for ripple in self._ripples:
                ripple.circle.set(opacity=0.0)
                ripple.release()
            self.layer.animate("opacity", 0.0, 0)

    @property
    def ripples(self) -> list[Any]:
        """The live ripples' circle nodes, oldest first."""
        return [ripple.circle for ripple in self._ripples]

    def set_dragged(self, dragged: bool) -> None:
        """For widgets that drag (M40): MD3's dragged state."""
        self.dragged = dragged
        self._update()

    @property
    def ring_visible(self) -> bool:
        return bool(self.ring.get("visible"))

    def retint(self, tint: RGBA, ring_color: RGBA) -> None:
        """New colours (a theme change), for the layer, live ripples and ring."""
        self.tint, self.ring_color = tint, ring_color
        self.layer.set(fill=tint)
        self.ring.set(stroke_color=ring_color)
        for ripple in self._ripples:
            ripple.circle.set(fill=tint)

    def refresh(self) -> None:
        """Follows the node's corners (and, for the ring, its size)."""
        radius = self.surface.get("corner_radius") or 0.0
        self.clip.set(corner_radius=radius)
        self._place_ring()

    def _place_ring(self) -> None:
        # A box's stroke is drawn inside it, so the ring's box starts the
        # gap and the stroke's width outside the node.
        out = RING_OFFSET + RING_WIDTH
        radius = self.ring_around.get("corner_radius") or 0.0
        grown = (tuple(r + out if r else 0.0 for r in radius) if isinstance(radius, (tuple, list))
                 else radius + out if radius else 0.0)
        width, height = self.ring_around.get("layout_width") or 0.0, self.ring_around.get("layout_height") or 0.0
        self.ring.set(x=-out, y=-out, width=width + 2 * out, height=height + 2 * out, corner_radius=grown)

    def detach(self) -> None:
        """Removes the listeners, the layer and any ripples. Safe after the
        node itself was destroyed."""
        for undo in self._undo:
            _quietly(undo)
        self._undo = []
        for node in (self.clip, self.ring):
            _quietly(node.destroy)
        self._ripples = []
        if self.node in _INTERACTIVE:
            _INTERACTIVE.remove(self.node)

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
        if not self._enabled:
            return
        self.hovered = True
        self._update()

    def _on_leave(self, event: Any) -> None:
        self.hovered = False
        self._update()
        self._release_all()  # a press dragged off the node is cancelled

    def _on_down(self, event: Any) -> None:
        if self._enabled and self._mine(event) and event.x is not None:
            x, y = event.x, event.y
            if self.surface is not self.node:  # the event is local to the node; layout is window-wide
                x -= (self.surface.get("layout_x") or 0.0) - (self.node.get("layout_x") or 0.0)
                y -= (self.surface.get("layout_y") or 0.0) - (self.node.get("layout_y") or 0.0)
            self._ripples.append(_Ripple(self, x, y))

    def _on_up(self, event: Any) -> None:
        self._release_all()

    def _on_click(self, event: Any) -> None:
        # A keyboard click has no position, and no press came first.
        if self._enabled and event.x is None and self._mine(event):
            ripple = _Ripple(self, None, None)
            self._ripples.append(ripple)
            ripple.release()

    def _on_focus(self, event: Any) -> None:
        if event.target == self.node and self._enabled:
            self.focused = bool(event.focus_visible)
            if self.focused:
                self._place_ring()  # the node may have been resized since
            self.ring.set(visible=self.focused)
            self._update()

    def _on_unfocus(self, event: Any) -> None:
        if event.target == self.node:
            self.focused = False
            self.ring.set(visible=False)
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
        node = owner.surface
        width, height = node.get("layout_width") or 0.0, node.get("layout_height") or 0.0
        if x is None:
            x, y = width / 2, height / 2
        # Big enough to cover the node from the press point.
        radius = max(math.hypot(x - cx, y - cy) for cx in (0.0, width) for cy in (0.0, height)) or 1.0
        start = min(1.0, INITIAL_SCALE * max(width, height) / (2 * radius))
        self.circle = owner.window.create(
            "box", position="absolute", x=x - radius, y=y - radius, width=2 * radius, height=2 * radius,
            corner_radius=radius, fill=owner.tint, opacity=0.0, scale=start, hit_testable=False,
            a11y_hidden=True)
        owner.clip.add_child(self.circle)
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
