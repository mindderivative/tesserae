"""One listener per node and event, shared (M40).

`tre`'s `node.on(event, handler)` keeps a single listener per event: a
second `on` replaces the first. Everything in Tesserae that listens on a
node -- a View's handlers and bindings, M39's `Interaction`, M40's
controls -- goes through one `Listeners` per window's tree, so they all
hear the event.
"""

from __future__ import annotations

from typing import Any, Callable

__all__ = ["Listeners", "handled"]


class Listeners:
    """Dispatchers for `node.on`, one per node and event."""

    def __init__(self) -> None:
        self._slots: dict[tuple[int, str], list[Callable[[Any], None]]] = {}

    def listen(self, node: Any, event: str, fn: Callable[[Any], None]) -> Callable[[], None]:
        """Adds `fn` for `node`'s `event`, after any already there; returns
        the function that removes it. The last removal calls `node.off`."""
        key = (id(node), event)
        slot = self._slots.get(key)
        if slot is None:
            slot = self._slots[key] = []
            node.on(event, lambda event_obj: [cb(event_obj) for cb in list(slot)])
        slot.append(fn)

        def undo() -> None:
            if fn in slot:
                slot.remove(fn)
            if not slot and self._slots.get(key) is slot:
                del self._slots[key]
                node.off(event)
        return undo


def handled(fn: Callable[[Any], Any]) -> Callable[[Any], None]:
    """`fn(event)`, then stop the event going on to the node's ancestors
    (M49). `tre`'s `click` and `secondary_click` bubble to every
    ancestor's listener; a clickable inside a clickable -- a button in a
    card, a checkbox in a list row -- takes its click alone, as MD3 (and
    Compose and Flutter) expect. Wraps every activation listener Tesserae
    adds; it stops the event even if `fn` raises, or ignores the click (a
    disabled control still takes it)."""
    def handle(event: Any) -> None:
        try:
            fn(event)
        finally:
            stop = getattr(event, "stop", None)
            if stop is not None:
                stop()
    return handle
