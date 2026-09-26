"""MD3's stateful controls, built by Tesserae from `tre` 0.3.4's building
blocks (M40), since `tre` 0.3.5 removes its own.

A control is a small object (M34 P6):

- `.node` is its touch target: a focusable `box` with the control's role,
  48 px square by default, that goes in a tree like any node;
- its state is a `Signal` (`Checkbox.checked`), so code reads it, sets it
  and reacts to it, and a view's bindings go straight to it;
- `on_change(fn)` hears changes the *user* makes (a click, Space, Enter),
  not ones the app makes by setting the `Signal` -- as HTML's `change`;
- `disabled` is a `Signal` too. A disabled control can't be focused or
  used and draws in MD3's disabled colours (content 38%, containers 12%).

Feedback is M39's `Interaction`: the state layer and ripple in a 40 px
circle at the centre of the target, and the focus ring around it on
keyboard focus. Colours are the theme's roles (MD3's baseline without a
theme); `set_theme` re-tints. Motion uses MD3's duration and easing tokens.
"""

from __future__ import annotations

from typing import Any, Callable, Optional

from tesserae import a11y, tokens
from tesserae.interaction import Interaction
from tesserae.listeners import Listeners
from tesserae.reactive import Effect, Signal, untrack
from tesserae.theme import Theme

__all__ = ["DISABLED_CONTAINER", "DISABLED_CONTENT", "Checkbox", "Control", "STATE_LAYER_SIZE", "TARGET_SIZE"]

RGBA = tuple[int, int, int, int]
Listen = Callable[[Any, str, Callable[[Any], None]], Callable[[], None]]

#: MD3's touch target and selection controls' state-layer circle, in px.
TARGET_SIZE = 48.0
STATE_LAYER_SIZE = 40.0
#: MD3's disabled opacities: content, and containers.
DISABLED_CONTENT, DISABLED_CONTAINER = 0.38, 0.12
_CLEAR: RGBA = (0, 0, 0, 0)


def with_alpha(color: RGBA, opacity: float) -> RGBA:
    return (color[0], color[1], color[2], round(color[3] * opacity))


class Control:
    """The shared part of every control. A subclass sets `role`, builds
    its drawing in `_build()`, paints its state in `_paint(animate)`
    (reading its `Signal`s, so a change repaints), and acts in
    `_activate()` when the user clicks it or presses Space or Enter."""

    role = "none"

    def __init__(self, window: Any, *, theme: Optional[Theme] = None, label: Optional[str] = None,
                 disabled: bool = False, listen: Optional[Listen] = None, size: float = TARGET_SIZE) -> None:
        self.window = window
        self.theme = theme if theme is not None else Theme.resolve()
        self.disabled = Signal(bool(disabled))
        self._listen: Listen = listen if listen is not None else Listeners().listen
        self._changes: list[Callable[[Any], None]] = []
        self._undo: list[Callable[[], None]] = []
        self._painted = False
        self.node = window.create("box", width=size, height=size, align_items="center",
                                  justify_content="center", focusable=True, role=self.role, cursor="pointer")
        if label is not None:
            a11y.describe(self.node, label=label)
        inset = (size - STATE_LAYER_SIZE) / 2
        self.surface = window.create("box", position="absolute", x=inset, y=inset, width=STATE_LAYER_SIZE,
                                     height=STATE_LAYER_SIZE, corner_radius=STATE_LAYER_SIZE / 2,
                                     hit_testable=False, a11y_hidden=True)
        self.node.add_child(self.surface)
        self._build()
        self.interaction = Interaction(window, self.node, self._tint(), self._listen, self.color("secondary"),
                                       surface=self.surface)
        self._undo.append(self._listen(self.node, "click", self._on_click))
        self._effect = Effect(self._render)

    # -- for app code -------------------------------------------------------------

    def on_change(self, fn: Callable[[Any], None]) -> Callable[[], None]:
        """Calls `fn(value)` after each change the user makes. Returns the
        function that stops it."""
        self._changes.append(fn)
        return lambda: self._changes.remove(fn) if fn in self._changes else None

    def color(self, role: str) -> RGBA:
        """A colour role of this control's theme, or MD3's baseline."""
        return self.theme.role(role) or tokens.BASELINE[role]

    def set_theme(self, theme: Theme) -> None:
        """Re-tints the control for `theme`, at once."""
        self.theme = theme
        self.interaction.retint(self._tint(), self.color("secondary"))
        untrack(lambda: self._paint(animate=False))

    def destroy(self) -> None:
        """Stops the control and frees its nodes."""
        self._effect.dispose()
        for undo in self._undo:
            undo()
        self._undo = []
        self.interaction.detach()
        self.node.destroy()

    # -- for subclasses --------------------------------------------------------------

    def _build(self) -> None:
        raise NotImplementedError

    def _paint(self, animate: bool) -> None:
        raise NotImplementedError

    def _activate(self) -> None:
        raise NotImplementedError

    def _tint(self) -> RGBA:
        """The state layer and ripple's colour for the current state."""
        return self.color("on_surface")

    def _changed(self, value: Any) -> None:
        for fn in list(self._changes):
            fn(value)

    def _ms(self, animate: bool, token: str) -> int:
        return Theme.duration(token) if animate else 0

    @staticmethod
    def _to(node: Any, prop: str, value: Any, ms: int, easing: Any = None) -> None:
        """Animates `prop` to `value` over `ms`; with `ms == 0`, sets it now
        (`animate(..., 0)` would wait for the next frame)."""
        if ms:
            node.animate(prop, value, ms, easing=easing)
        else:
            node.stop_animation(prop)
            node.set(**{prop: value})

    # -- internals -----------------------------------------------------------------

    def _render(self) -> None:
        disabled = self.disabled.get()
        self.node.set(focusable=not disabled, disabled=disabled, cursor="default" if disabled else "pointer")
        self.interaction.enabled = not disabled
        self._paint(animate=self._painted)
        self.interaction.retint(self._tint(), self.color("secondary"))
        self._painted = True

    def _on_click(self, event: Any) -> None:
        if not self.disabled.get():
            self._activate()


class Checkbox(Control):
    """MD3's checkbox: an 18 px box with a 2 px outline, filled with
    `primary` and a check mark in `on_primary` when checked. `color`
    replaces `primary` (a fragment's `background:`)."""

    role = "checkbox"
    SIZE = 18.0
    CHECK = "M3.5,9.5 L7,13 L14.5,5.5"

    def __init__(self, window: Any, *, checked: bool = False, color: Optional[RGBA] = None, **kwargs: Any) -> None:
        self.checked = Signal(bool(checked))
        self._color = color
        super().__init__(window, **kwargs)

    def _build(self) -> None:
        self.box = self.window.create("box", width=self.SIZE, height=self.SIZE, corner_radius=2.0, stroke_width=2.0,
                                      hit_testable=False, a11y_hidden=True)
        self.mark = self.window.create("path", data=self.CHECK, view_box=(0, 0, self.SIZE, self.SIZE),
                                       width=self.SIZE, height=self.SIZE, stroke_width=2.0, fill=_CLEAR,
                                       trim_end=0.0, hit_testable=False, a11y_hidden=True)
        self.box.add_child(self.mark)
        self.node.add_child(self.box)

    def _selected(self) -> RGBA:
        return self._color or self.color("primary")

    def _tint(self) -> RGBA:
        # MD3: a selected control's hover and focus layers are `primary`
        return self._selected() if self.checked.get() else self.color("on_surface")

    def _paint(self, animate: bool) -> None:
        checked, disabled = self.checked.get(), self.disabled.get()
        self.node.set(checked=checked)
        off = with_alpha(self.color("on_surface"), DISABLED_CONTENT)
        if checked:
            fill = off if disabled else self._selected()
            stroke = fill
            mark = self.color("surface") if disabled else self.color("on_primary")
        else:
            fill, stroke = _CLEAR, off if disabled else self.color("on_surface_variant")
            mark = self.mark.get("stroke_color") or _CLEAR
        colour_ms = self._ms(animate, "short3")
        self._to(self.box, "fill", fill, colour_ms)
        self._to(self.box, "stroke_color", stroke, colour_ms)
        self.mark.set(stroke_color=mark)
        if checked:
            self._to(self.mark, "trim_end", 1.0, self._ms(animate, "medium1"), Theme.easing("emphasized_decelerate"))
        else:
            self._to(self.mark, "trim_end", 0.0, self._ms(animate, "short3"), Theme.easing("emphasized_accelerate"))

    def _activate(self) -> None:
        self.checked.set(not self.checked.get())
        self._changed(self.checked.get())
