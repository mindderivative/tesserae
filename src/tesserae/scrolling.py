"""What a `ScrollView` (M71) adds to `tre`'s `scroll_view`: telling a
two-way binding when it scrolls.

Since `tre` 0.4.2 (`tre` #24) a `scroll_view` does the rest itself: the
arrows, Page Up/Down and Home/End scroll the one around the focused node;
focusing a node scrolls it into view; it answers `scroll_into_view`; and
it fires a `scroll` event (`old_value`/`new_value`) on every change of
offset, from the wheel, the keys, a reveal or a `set`. (M71's `Scroller`
did the keys and reveals itself on 0.4.0-0.4.1; M73 handed them back,
since its `key_down` listener on the scroll view kept every key from
`tre`, so a focused child's keys didn't scroll.) A `Scroller` follows
that event, for `two_way: scroll_offset`.
"""

from __future__ import annotations

from typing import Any, Callable


class Scroller:
    """One `ScrollView`'s offset, followed: `node` is its `scroll_view`.
    `listen(node, event, fn)` is the owning view's shared dispatcher;
    `detach()` stops it."""

    def __init__(self, node: Any, listen: Callable[..., Callable[[], None]]) -> None:
        self.node = node
        self._followers: list[Callable[[float], Any]] = []
        self._undo = listen(node, "scroll", self._scrolled)

    @property
    def offset(self) -> float:
        return float(self.node.get("scroll_offset"))

    def on_scroll(self, fn: Callable[[float], Any]) -> Callable[[], None]:
        """Calls `fn(offset)` after each change of offset; returns the undo."""
        self._followers.append(fn)
        return lambda: self._followers.remove(fn) if fn in self._followers else None

    def detach(self) -> None:
        self._undo()
        self._followers = []

    def _scrolled(self, event: Any) -> None:
        offset = float(event.new_value)
        for fn in list(self._followers):
            fn(offset)
