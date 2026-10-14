"""Typing effects on a text input (#248): what the engine's `caret_move` event and `text_rects` make possible.

`typing_effect` is drawn over the characters just typed, from the geometry the engine gives (the rectangle of the byte range an edit inserted):

- `flash`: a tint of the primary colour over the new characters that fades away.
- `fade_in`: a cover in the background colour over the new characters that fades away, so the text seems to fade in. The background is the first
  opaque fill found going up from the input (the theme's `surface` when there is none).

`caret_effect: glide` hides the engine's caret and draws one of Tesserae's own, which glides to the new place whenever the caret moves, blinks like
the engine's (solid while typing), and shows only while the input has the focus.

Both are drawn as children of the input (it takes children), never take the pointer, and are hidden from a screen reader. With reduced motion asked for,
there is no flash and no fade, and the caret jumps and does not blink.
"""

from __future__ import annotations

from typing import Any, Callable, Optional

from tesserae import tokens
from tesserae.timers import Timers

__all__ = ["CARET_EFFECTS", "OPTIONS", "TYPING_EFFECTS", "TypingEffects"]

TYPING_EFFECTS = ("none", "flash", "fade_in")
CARET_EFFECTS = ("none", "glide")

#: A flash is the primary colour at this opacity, easing out over this many milliseconds; a fade-in is the background easing out over its own.
FLASH_ALPHA = 0.24
FLASH_MS = 260
FADE_MS = 180
#: The caret glides to its new place in this time, and blinks as the engine's does: solid for a moment after it moves, then on and off.
GLIDE_MS = 120
HOLD_MS = 500
BLINK_MS = 530
EASE_OUT = (0.0, 0.0, 0.2, 1.0)  # emphasized decelerate, near enough
CARET_WIDTH = 1.5
#: The properties that set the looks; each is `None` when left out, and then the constants above are what is used.
OPTIONS = ("typing_duration", "flash_color", "flash_opacity", "glide_duration", "caret_blink")


class TypingEffects:
    """The effects of one text input `node`. `typing` and `caret` are the property values; `scheme` gives the colours (a dict of roles, or a function that
    gives it, asked each time so a theme change is followed); `reduced` says whether motion is to be left out (read each time); `listen` is the shared
    `Listeners.listen`; `options` are the looks (`OPTIONS`). `detach()` takes it all away and puts the engine's caret back."""

    def __init__(self, window: Any, node: Any, *, typing: str, caret: str, scheme: dict[str, Any], reduced: Callable[[], bool],
                 listen: Callable[[Any, str, Callable[[Any], None]], Callable[[], None]], options: Optional[dict[str, Any]] = None) -> None:
        self.window, self.node, self.reduced = window, node, reduced
        self._scheme_of: Callable[[], dict[str, Any]] = scheme if callable(scheme) else (lambda: scheme)
        self.typing, self.caret = typing, caret
        given = {name: value for name, value in (options or {}).items() if value is not None}
        unknown = sorted(set(given) - set(OPTIONS))
        if unknown:
            raise ValueError(f"unknown typing effect option(s) {unknown}; they are {', '.join(OPTIONS)}")
        # the engine's `animate` takes whole milliseconds, and a number from a view is a float
        self._duration: Optional[int] = round(given["typing_duration"]) if "typing_duration" in given else None
        self._flash_opacity: float = float(given.get("flash_opacity", FLASH_ALPHA))
        self._flash_color_raw = given.get("flash_color")
        if self._flash_color_raw is not None:
            self._resolve(self._flash_color_raw)  # a mistake is found now, not at the first keystroke
        self._glide_ms: int = round(given.get("glide_duration", GLIDE_MS))
        self._blink_ms: float = float(given.get("caret_blink", BLINK_MS))
        self._timers = Timers(window)
        self._undos: list[Callable[[], None]] = []
        self._covers: list[Any] = []
        self._bar: Optional[Any] = None
        self._focused = False
        self._blink_on = True
        if typing not in ("none", None) or caret == "glide":
            self._undos.append(listen(node, "caret_move", self._moved))
        if caret == "glide":
            node.set(caret_visible=False)  # the engine's would be drawn twice
            self._undos.append(listen(node, "focus", self._focus))
            self._undos.append(listen(node, "unfocus", self._unfocus))
            if node.get("focused"):
                self._focus(None)

    # -- the engine's events ---------------------------------------------------

    def _moved(self, event: Any) -> None:
        if self.typing in ("flash", "fade_in") and event.inserted is not None and not self.reduced():
            self._cover(*event.inserted)
        if self.caret == "glide":
            self._glide(event.caret)

    # -- flash and fade-in -----------------------------------------------------

    @property
    def scheme(self) -> dict[str, Any]:
        return self._scheme_of()

    def _resolve(self, raw: Any) -> tuple[int, int, int, int]:
        """`flash_color`: a theme role or a colour (`tokens.resolve_color`), else an error that names the property."""
        if isinstance(raw, str) and raw in self.scheme:
            return tuple(self.scheme[raw])  # type: ignore[return-value]
        try:
            return tuple(tokens.resolve_color(str(raw), self.scheme))  # type: ignore[return-value]
        except ValueError as exc:
            raise ValueError(f"flash_color {raw!r} is not a theme role or a colour: {exc}") from None

    def _background(self) -> tuple[int, int, int, int]:
        """The first opaque fill going up from the input, else the theme's surface."""
        parent = self.node.parent()
        while parent is not None:
            fill = parent.get("fill")
            if fill is not None and len(fill) == 4 and fill[3] == 255:
                return tuple(fill)  # type: ignore[return-value]
            parent = parent.parent()
        return tuple(self.scheme["surface"])  # type: ignore[return-value]

    def _cover(self, start: int, end: int) -> None:
        """A rectangle over each piece of the characters in bytes `start` to `end`, from `flash`'s tint or `fade_in`'s cover to nothing."""
        if self.typing == "flash":
            r, g, b, a = self._resolve(self._flash_color_raw) if self._flash_color_raw is not None else self.scheme["primary"]
            fill, opacity, ms = (r, g, b, a), self._flash_opacity, FLASH_MS
        else:
            fill, opacity, ms = self._background(), 1.0, FADE_MS
        ms = self._duration if self._duration is not None else ms
        if ms <= 0:  # no time to show it in: left out
            return
        for x, y, width, height in self.node.text_rects(start, end):
            cover = self.window.create("box", position="absolute", x=float(x), y=float(y), width=float(width), height=float(height), fill=fill,
                                       opacity=opacity, hit_testable=False, a11y_hidden=True)
            self.node.add_child(cover)
            self._covers.append(cover)
            cover.animate("opacity", 0.0, ms, EASE_OUT, on_complete=lambda cover=cover: self._drop(cover))

    def _drop(self, cover: Any) -> None:
        if cover in self._covers:
            self._covers.remove(cover)
            try:
                cover.destroy()
            except Exception:  # the input went first
                pass

    # -- the gliding caret -----------------------------------------------------

    def _color(self) -> tuple[int, int, int, int]:
        return tuple(self.node.get("caret_color") or self.node.get("fill") or self.scheme["primary"])  # type: ignore[return-value]

    def _bar_node(self, rect: tuple[float, float, float, float]) -> Any:
        if self._bar is None:
            x, y, _, height = rect
            self._bar = self.window.create("box", position="absolute", x=float(x), y=float(y), width=CARET_WIDTH, height=float(height), fill=self._color(),
                                           hit_testable=False, a11y_hidden=True, visible=False)
            self.node.add_child(self._bar)
        return self._bar

    def _glide(self, rect: tuple[float, float, float, float]) -> None:
        bar = self._bar_node(rect)
        x, y, _, height = rect
        old_x, old_y = bar.get("x"), bar.get("y")
        bar.set(x=float(x), y=float(y), height=float(height), fill=self._color())
        if not self.reduced() and self._glide_ms > 0 and isinstance(old_x, float) and isinstance(old_y, float) and (old_x, old_y) != (float(x), float(y)):
            bar.set(translate_x=old_x - float(x), translate_y=old_y - float(y))  # drawn where it was, then eased home: a transform, so no relayout
            bar.animate("translate_x", 0.0, self._glide_ms, EASE_OUT)
            bar.animate("translate_y", 0.0, self._glide_ms, EASE_OUT)
        self._solid()

    def _solid(self) -> None:
        """Solid while the caret moves, and on and off after a moment, while the input has the focus."""
        self._timers.cancel("blink")
        self._timers.cancel("hold")
        self._blink_on = True
        if self._bar is not None:
            self._bar.set(visible=self._focused)
        if self._focused and not self.reduced() and self._blink_ms > 0:
            self._timers.after(HOLD_MS, self._start_blink, name="hold")

    def _start_blink(self) -> None:
        self._timers.every(self._blink_ms, self._toggle, name="blink")

    def _toggle(self) -> None:
        self._blink_on = not self._blink_on
        if self._bar is not None:
            self._bar.set(visible=self._blink_on)

    def _focus(self, event: Any) -> None:
        self._focused = True
        self._glide(self.node.caret_rect())

    def _unfocus(self, event: Any) -> None:
        self._focused = False
        self._timers.cancel("blink")
        self._timers.cancel("hold")
        if self._bar is not None:
            self._bar.set(visible=False)

    # -- ending ----------------------------------------------------------------

    def detach(self) -> None:
        """Stops the effects: the listeners, the timers and everything drawn go, and the engine's own caret is back."""
        for undo in self._undos:
            undo()
        self._undos = []
        self._timers.cancel_all()
        for cover in list(self._covers):
            self._drop(cover)
        if self._bar is not None:
            try:
                self._bar.destroy()
            except Exception:
                pass
            self._bar = None
        if self.caret == "glide":
            try:
                self.node.set(caret_visible=True)
            except Exception:
                pass
