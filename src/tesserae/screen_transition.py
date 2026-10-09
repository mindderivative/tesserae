"""Screen transitions (#231): how one screen leaves and the next arrives -- Material 3's fade through, shared axis and container transform.

```python
app.transition = "shared_axis_x"             # every navigate(), back() and forward() slides and fades
app.navigate_with("detail", transition="container_transform", origin=card_node, params={"id": 3})
```

`TRANSITIONS` names them. Each is two animations built from what tre animates (opacity, translate, scale), 300 ms in all at MD3's durations: the
outgoing screen leaves in 90 ms and the incoming one arrives in 210 ms after it (container transform is one 300 ms move). While they run both screens
are laid over each other (`position: absolute`), and when they finish the outgoing one is taken away and both are put back as they were. Going back
reverses the direction. An app that reduces motion swaps at once, and a new navigation while one is playing finishes it first.
"""

from __future__ import annotations

from typing import Any, Callable, Optional

from tesserae import motion
from tesserae.spec.transition import EASINGS

__all__ = ["DISTANCE", "OUT_MS", "IN_MS", "ScreenTransition", "TRANSITIONS", "play"]

TRANSITIONS = ("none", "fade_through", "shared_axis_x", "shared_axis_y", "shared_axis_z", "container_transform")
#: how far a shared axis slides, in pixels
DISTANCE = 30.0
OUT_MS, IN_MS = 90, 210
_LEAVE, _ARRIVE = EASINGS["emphasized_accelerate"], EASINGS["emphasized_decelerate"]
_MOVE = EASINGS["emphasized"]
_PROPS = ("opacity", "translate_x", "translate_y", "scale")
_REST = {"opacity": 1.0, "translate_x": 0.0, "translate_y": 0.0, "scale": 1.0}


class ScreenTransition:
    """One transition in progress. `finish()` ends it where it was going: the outgoing screen gone, the incoming one at rest."""

    def __init__(self, window: Any, outgoing: Any, incoming: Any, hide_outgoing: Callable[[], None]) -> None:
        self.window, self.outgoing, self.incoming = window, outgoing, incoming
        self._hide, self.done = hide_outgoing, False
        self._placement = {id(n): (n.get("position"), n.get("x"), n.get("y")) for n in (outgoing, incoming) if n is not None}
        self._on_finish: list[Callable[[], None]] = []

    def lay_over(self) -> None:
        for node in (self.outgoing, self.incoming):
            if node is not None:
                node.set(position="absolute", x=0.0, y=0.0)

    def finish(self) -> None:
        if self.done:
            return
        self.done = True
        for node in (self.outgoing, self.incoming):
            if node is None:
                continue
            for prop in _PROPS:
                node.stop_animation(prop)
        self._hide()
        for node in (self.outgoing, self.incoming):
            if node is not None:
                position, x, y = self._placement[id(node)]
                node.set(**_REST, position=position, x=x, y=y)
        for fn in self._on_finish:
            fn()

    def on_finish(self, fn: Callable[[], None]) -> None:
        self._on_finish.append(fn)


def _glide(node: Any, ms: int, easing: Any, **to: float) -> None:
    for prop, value in to.items():
        node.animate(prop, value, ms, easing)


def play(window: Any, outgoing: Any, incoming: Any, kind: str, *, forward: bool = True, origin: Any = None,
         reveal: Callable[[], None], hide_outgoing: Callable[[], None]) -> Optional[ScreenTransition]:
    """Runs `kind` from `outgoing` (a node, or `None`) to `incoming`. `reveal()` puts the incoming screen where it shows (the caller's to do) and
    `hide_outgoing()` takes the outgoing one away. Returns the running transition, or `None` when it all happened at once (`kind` is `none`, the
    app is to reduce motion, or there was no outgoing screen)."""
    if kind not in TRANSITIONS:
        raise ValueError(f"a screen transition is one of {', '.join(TRANSITIONS)}, not {kind!r}")
    if kind == "none" or outgoing is None or motion.reduced(window):
        if outgoing is not None:
            hide_outgoing()
        reveal()
        return None
    run = ScreenTransition(window, outgoing, incoming, hide_outgoing)
    run.lay_over()
    reveal()
    sign = 1.0 if forward else -1.0
    if kind == "container_transform":
        _container_transform(run, origin, forward)
        return run

    start_in: dict[str, float] = {"opacity": 0.0}
    leave: dict[str, float] = {"opacity": 0.0}
    arrive: dict[str, float] = {"opacity": 1.0}
    if kind == "fade_through":
        start_in["scale"] = 0.92
        arrive["scale"] = 1.0
    elif kind in ("shared_axis_x", "shared_axis_y"):
        axis = "translate_x" if kind.endswith("x") else "translate_y"
        leave[axis] = -sign * DISTANCE
        start_in[axis] = sign * DISTANCE
        arrive[axis] = 0.0
    else:  # shared_axis_z: the screen grows away as the next one grows in
        leave["scale"] = 1.1 if forward else 0.8
        start_in["scale"] = 0.8 if forward else 1.1
        arrive["scale"] = 1.0
    incoming.set(**{**_REST, **start_in})

    def arrive_now() -> None:
        if not run.done:
            _glide(incoming, motion.duration(window, IN_MS), _ARRIVE, **arrive)
            incoming.animate("opacity", 1.0, motion.duration(window, IN_MS), _ARRIVE, on_complete=run.finish)

    for prop in [p for p in leave if p != "opacity"]:
        outgoing.animate(prop, leave[prop], motion.duration(window, OUT_MS), _LEAVE)
    outgoing.animate("opacity", 0.0, motion.duration(window, OUT_MS), _LEAVE, on_complete=arrive_now)
    return run


def _container_transform(run: ScreenTransition, origin: Any, forward: bool) -> None:
    """The incoming screen grows from `origin` (a node: where it was, how big) to fill its place; going back it shrinks to it. With no origin it
    grows from the middle."""
    window, incoming, outgoing = run.window, run.incoming, run.outgoing
    width, height = float(incoming.get("layout_width") or 1.0), float(incoming.get("layout_height") or 1.0)
    if origin is not None and origin.get("layout_width"):
        scale = max(float(origin.get("layout_width")) / width, float(origin.get("layout_height")) / height, 0.05)
        dx = float(origin.get("layout_x")) + float(origin.get("layout_width")) / 2 - (float(incoming.get("layout_x") or 0.0) + width / 2)
        dy = float(origin.get("layout_y")) + float(origin.get("layout_height")) / 2 - (float(incoming.get("layout_y") or 0.0) + height / 2)
    else:
        scale, dx, dy = 0.8, 0.0, 0.0
    ms = motion.duration(window, OUT_MS + IN_MS)
    if forward:
        incoming.set(**{**_REST, "opacity": 0.0, "scale": scale, "translate_x": dx, "translate_y": dy})
        _glide(incoming, ms, _MOVE, scale=1.0, translate_x=0.0, translate_y=0.0)
        incoming.animate("opacity", 1.0, motion.duration(window, OUT_MS + 10), _ARRIVE)
        outgoing.animate("opacity", 0.0, ms, _LEAVE, on_complete=run.finish)
    else:  # back: the screen being left shrinks into where it came from
        incoming.set(**{**_REST, "opacity": 0.0})
        incoming.animate("opacity", 1.0, ms, _ARRIVE)
        _glide(outgoing, ms, _MOVE, scale=scale, translate_x=dx, translate_y=dy)
        outgoing.animate("opacity", 0.0, ms, _LEAVE, on_complete=run.finish)
