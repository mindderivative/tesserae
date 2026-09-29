"""What a `ScrollView` (M71) does beyond `tre`'s `scroll_view`: the keys,
revealing a focused child, `scroll_into_view`, and telling a two-way
binding when it scrolls.

`tre` 0.4's `scroll_view` scrolls with the wheel and clamps its
`scroll_offset`, but ignores the keyboard, doesn't answer
`scroll_into_view`, doesn't scroll to a child that takes focus, and sends
no event when it scrolls (`tre` #24). Its `wheel`, `key_down`, `focus`
and `a11y_action` events all reach it, so a `Scroller` listening there
supplies the rest: when focused, the arrows move a line, Page Up/Down a
viewport, Home/End to the ends; a focused or `scroll_into_view` child is
brought into view; and `on_scroll(fn)` hears every change of offset, from
the wheel, the keys or a reveal.
"""

from __future__ import annotations

from typing import Any, Callable, Optional

#: How far an arrow key scrolls, in pixels.
LINE = 40.0


class Scroller:
    """The behaviour of one `ScrollView`: `node` is its `scroll_view`,
    `content` the box its children are laid out in. `listen(node, event,
    fn)` is the owning view's shared dispatcher; `detach()` stops it."""

    def __init__(self, node: Any, content: Any, listen: Callable[..., Callable[[], None]]) -> None:
        self.node, self.content = node, content
        self._followers: list[Callable[[float], Any]] = []
        self._undo = [
            listen(node, "key_down", self._key),
            listen(node, "focus", self._focus),
            listen(node, "a11y_action", self._a11y),
            listen(node, "wheel", lambda event: self._moved()),  # `tre` has already scrolled
        ]

    @property
    def offset(self) -> float:
        return float(self.node.get("scroll_offset"))

    def on_scroll(self, fn: Callable[[float], Any]) -> Callable[[], None]:
        """Calls `fn(offset)` after each change of offset; returns the undo."""
        self._followers.append(fn)
        return lambda: self._followers.remove(fn) if fn in self._followers else None

    @property
    def extent(self) -> float:
        """The furthest it scrolls: the content's height past the viewport."""
        return max(0.0, float(self.content.get("layout_height")) - float(self.node.get("layout_height")))

    def scroll_to(self, offset: float) -> None:
        """Scrolls to `offset`, kept within the content. (`tre` clamps the far
        end only at its next layout, so it's clamped here first: what
        `on_scroll` reports is where it stops.)"""
        before = self.offset
        self.node.set(scroll_offset=min(max(0.0, float(offset)), self.extent))
        if self.offset != before:
            self._moved()

    def reveal(self, target: Any) -> None:
        """Scrolls just enough to show `target`, a node inside the content."""
        top = _top_within(target, self.content)
        if top is None:
            return
        bottom = top + float(target.get("layout_height"))
        viewport, offset = float(self.node.get("layout_height")), self.offset
        if top < offset:
            self.scroll_to(top)
        elif bottom > offset + viewport:
            self.scroll_to(bottom - viewport)

    def detach(self) -> None:
        for undo in self._undo:
            undo()
        self._undo, self._followers = [], []

    def _moved(self) -> None:
        offset = self.offset
        for fn in list(self._followers):
            fn(offset)

    def _key(self, event: Any) -> None:
        if event.target != self.node or event.alt or event.ctrl or event.meta:
            return  # a key for a child (a text field's arrows), or a shortcut
        viewport = float(self.node.get("layout_height"))
        moves = {"arrow_down": self.offset + LINE, "arrow_up": self.offset - LINE,
                 "page_down": self.offset + viewport, "page_up": self.offset - viewport,
                 "home": 0.0, "end": self.extent}
        if event.key in moves:
            self.scroll_to(moves[event.key])

    def _focus(self, event: Any) -> None:  # (the scroll view itself is always in its own view)
        if event.target is not None:
            self.reveal(event.target)

    def _a11y(self, event: Any) -> None:
        if event.action == "scroll_into_view" and event.target is not None:
            self.reveal(event.target)


def _top_within(target: Any, content: Any) -> Optional[float]:
    """`target`'s top in `content`'s coordinates, or `None` if it isn't
    inside `content`. `layout_y` is in window space and already moved by
    every scroll above it, so the difference is where `target` sits in
    the content now -- a scroll view in between included."""
    node = target.parent()
    while node is not None and node != content:
        node = node.parent()
    if node is None:
        return None
    return float(target.get("layout_y")) - float(content.get("layout_y"))
