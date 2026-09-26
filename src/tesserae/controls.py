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

__all__ = [
    "DISABLED_CONTAINER", "DISABLED_CONTENT", "Checkbox", "Control", "RadioButton", "RadioGroup", "STATE_LAYER_SIZE",
    "Switch", "TARGET_SIZE",
]

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
    #: The touch target's width and height.
    target = (TARGET_SIZE, TARGET_SIZE)

    def __init__(self, window: Any, *, theme: Optional[Theme] = None, label: Optional[str] = None,
                 disabled: bool = False, listen: Optional[Listen] = None, size: Optional[float] = None) -> None:
        self.window = window
        self.theme = theme if theme is not None else Theme.resolve()
        self.disabled = Signal(bool(disabled))
        self._listen: Listen = listen if listen is not None else Listeners().listen
        self._changes: list[Callable[[Any], None]] = []
        self._undo: list[Callable[[], None]] = []
        self._painted = False
        width, height = (size, size) if size is not None else self.target
        self.node = window.create("box", width=width, height=height, align_items="center",
                                  justify_content="center", focusable=True, role=self.role, cursor="pointer")
        if label is not None:
            a11y.describe(self.node, label=label)
        self.surface = window.create("box", position="absolute", x=(width - STATE_LAYER_SIZE) / 2,
                                     y=(height - STATE_LAYER_SIZE) / 2, width=STATE_LAYER_SIZE,
                                     height=STATE_LAYER_SIZE, corner_radius=STATE_LAYER_SIZE / 2,
                                     hit_testable=False, a11y_hidden=True)
        self.node.add_child(self.surface)
        self._build()
        self.interaction = Interaction(window, self.node, self._tint(), self._listen, self.color("secondary"),
                                       surface=self.surface, ring_around=self._ring_around())
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

    def _focusable(self) -> bool:
        """Whether Tab stops here now (a radio group has one stop)."""
        return not self.disabled.get()

    def _ring_around(self) -> Any:
        """The node the focus ring surrounds (default: the state layer's circle)."""
        return None

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
        self.node.set(focusable=self._focusable(), disabled=disabled, cursor="default" if disabled else "pointer")
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


class RadioGroup:
    """Radio buttons that exclude each other, as HTML's same-`name` radios.
    Selecting one deselects the rest. The group is one Tab stop (the
    selected button, else the first enabled one), and the arrow keys move
    the selection, and focus, to the next or previous enabled button."""

    def __init__(self) -> None:
        self.buttons: list["RadioButton"] = []
        self._syncing = False

    @property
    def selected(self) -> Optional["RadioButton"]:
        return next((b for b in self.buttons if b.selected.get()), None)

    def _add(self, button: "RadioButton") -> None:
        self.buttons.append(button)
        if button.selected.get():
            self._select(button)
        else:
            self._refocus()

    def _remove(self, button: "RadioButton") -> None:
        if button in self.buttons:
            self.buttons.remove(button)
        self._refocus()

    def _select(self, button: "RadioButton") -> None:
        if self._syncing:
            return
        self._syncing = True
        try:
            for other in self.buttons:
                if other is not button:
                    other.selected.set(False)
        finally:
            self._syncing = False
        self._refocus()

    def _tab_stop(self) -> Optional["RadioButton"]:
        enabled = [b for b in self.buttons if not b.disabled.get()]
        chosen = next((b for b in enabled if b.selected.get()), None)
        return chosen or (enabled[0] if enabled else None)

    def _refocus(self) -> None:
        stop = self._tab_stop()
        for b in self.buttons:
            b.node.set(focusable=b is stop)

    def _step(self, button: "RadioButton", by: int) -> None:
        enabled = [b for b in self.buttons if not b.disabled.get()]
        if button not in enabled or len(enabled) < 2:
            return
        target = enabled[(enabled.index(button) + by) % len(enabled)]
        target.selected.set(True)
        target.node.set(focusable=True)
        target.node.focus()
        target._changed(True)


class RadioButton(Control):
    """MD3's radio button: a 20 px ring, 2 px wide, in `on_surface_variant`,
    and when selected a `primary` ring with a 10 px `primary` dot that grows
    in. A click selects it (it never deselects itself); in a `group`, it
    deselects the others. `color` replaces `primary`."""

    role = "radio"
    SIZE = 20.0
    DOT = 10.0

    def __init__(self, window: Any, *, selected: bool = False, group: Optional[RadioGroup] = None,
                 color: Optional[RGBA] = None, **kwargs: Any) -> None:
        self.selected = Signal(bool(selected))
        self.group = group
        self._color = color
        super().__init__(window, **kwargs)
        if group is not None:
            group._add(self)
            self._undo.append(self._listen(self.node, "key_down", self._on_key))
            self._undo.append(lambda: group._remove(self))

    def _build(self) -> None:
        self.ring = self.window.create("box", width=self.SIZE, height=self.SIZE, corner_radius=self.SIZE / 2,
                                       stroke_width=2.0, align_items="center", justify_content="center",
                                       hit_testable=False, a11y_hidden=True)
        self.dot = self.window.create("box", width=self.DOT, height=self.DOT, corner_radius=self.DOT / 2, scale=0.0,
                                      hit_testable=False, a11y_hidden=True)
        self.ring.add_child(self.dot)
        self.node.add_child(self.ring)

    def _on_colour(self) -> RGBA:
        return self._color or self.color("primary")

    def _tint(self) -> RGBA:
        return self._on_colour() if self.selected.get() else self.color("on_surface")

    def _focusable(self) -> bool:
        if self.disabled.get():
            return False
        if self.group is None:
            return True
        return untrack(self.group._tab_stop) is self

    def _paint(self, animate: bool) -> None:
        selected, disabled = self.selected.get(), self.disabled.get()
        self.node.set(checked=selected)
        off = with_alpha(self.color("on_surface"), DISABLED_CONTENT)
        colour = off if disabled else (self._on_colour() if selected else self.color("on_surface_variant"))
        ms = self._ms(animate, "short3")
        self._to(self.ring, "stroke_color", colour, ms)
        self._to(self.dot, "fill", off if disabled else self._on_colour(), ms)
        if selected:
            self._to(self.dot, "scale", 1.0, self._ms(animate, "medium1"), Theme.easing("emphasized_decelerate"))
        else:
            self._to(self.dot, "scale", 0.0, ms, Theme.easing("emphasized_accelerate"))
        if selected and self.group is not None:
            untrack(lambda: self.group._select(self))
        elif self.group is not None:
            untrack(self.group._refocus)

    def _activate(self) -> None:
        if not self.selected.get():
            self.selected.set(True)
            self._changed(True)

    def _on_key(self, event: Any) -> None:
        if self.disabled.get() or self.group is None:
            return
        step = {"arrow_down": 1, "arrow_right": 1, "arrow_up": -1, "arrow_left": -1}.get(event.key)
        if step is not None:
            self.group._step(self, step)


class Switch(Control):
    """MD3's switch: a 52×32 track and a handle that slides across it.
    Off, the track is `surface_container_highest` with a 2 px `outline`
    border and a 16 px `outline` handle; on, it's `primary` with a 24 px
    `on_primary` handle. Pressed, the handle grows to 28 px. `color`
    replaces `primary`. The state layer follows the handle; the focus ring
    goes around the track."""

    role = "switch"
    target = (52.0, TARGET_SIZE)
    WIDTH, HEIGHT = 52.0, 32.0
    HANDLE = 28.0  # drawn at this size and scaled: 16 off, 24 on, 28 pressed
    OFF, ON, PRESSED = 16.0, 24.0, 28.0

    def __init__(self, window: Any, *, selected: bool = False, color: Optional[RGBA] = None, **kwargs: Any) -> None:
        self.selected = Signal(bool(selected))
        self._color = color
        self._pressed = False
        super().__init__(window, **kwargs)
        self._undo.append(self._listen(self.node, "pointer_down", lambda e: self._press(True)))
        self._undo.append(self._listen(self.node, "pointer_up", lambda e: self._press(False)))
        self._undo.append(self._listen(self.node, "pointer_leave", lambda e: self._press(False)))

    #: The handle's centre travels this far, from `HEIGHT / 2` to `WIDTH - HEIGHT / 2`.
    TRAVEL = WIDTH - HEIGHT

    def _build(self) -> None:
        self.track = self.window.create("box", width=self.WIDTH, height=self.HEIGHT, corner_radius=self.HEIGHT / 2,
                                        stroke_width=2.0, hit_testable=False, a11y_hidden=True)
        centre = self.HEIGHT / 2
        self.handle = self.window.create("box", position="absolute", x=centre - self.HANDLE / 2,
                                         y=centre - self.HANDLE / 2, width=self.HANDLE, height=self.HANDLE,
                                         corner_radius=self.HANDLE / 2, hit_testable=False, a11y_hidden=True)
        self.track.add_child(self.handle)
        self.node.add_child(self.track)
        # the state layer's circle rides on the handle
        offset = (self.target[1] - self.HEIGHT) / 2
        self.surface.set(x=centre - STATE_LAYER_SIZE / 2, y=offset + centre - STATE_LAYER_SIZE / 2)

    def _ring_around(self) -> Any:
        return self.track

    def _on_colour(self) -> RGBA:
        return self._color or self.color("primary")

    def _tint(self) -> RGBA:
        return self._on_colour() if self.selected.get() else self.color("on_surface")

    def _handle_size(self) -> float:
        if self._pressed and not self.disabled.get():
            return self.PRESSED
        return self.ON if self.selected.get() else self.OFF

    def _paint(self, animate: bool) -> None:
        selected, disabled = self.selected.get(), self.disabled.get()
        self.node.set(checked=selected)
        on_surface = self.color("on_surface")
        if selected:
            track = with_alpha(on_surface, DISABLED_CONTAINER) if disabled else self._on_colour()
            border = track
            handle = self.color("surface") if disabled else self.color("on_primary")
        else:
            track = (with_alpha(self.color("surface_container_highest"), DISABLED_CONTAINER) if disabled
                     else self.color("surface_container_highest"))
            border = with_alpha(on_surface, DISABLED_CONTAINER) if disabled else self.color("outline")
            handle = with_alpha(on_surface, DISABLED_CONTENT) if disabled else self.color("outline")
        ms = self._ms(animate, "short3")
        self._to(self.track, "fill", track, ms)
        self._to(self.track, "stroke_color", border, ms)
        self._to(self.handle, "fill", handle, ms)
        travel = self.TRAVEL if selected else 0.0
        slide = self._ms(animate, "medium2")
        easing = Theme.easing("emphasized_decelerate")
        self._to(self.handle, "translate_x", travel, slide, easing)
        self._to(self.surface, "translate_x", travel, slide, easing)
        self._to(self.handle, "scale", self._handle_size() / self.HANDLE, self._ms(animate, "short2"), easing)

    def _press(self, pressed: bool) -> None:
        if pressed == self._pressed:
            return
        self._pressed = pressed
        self._to(self.handle, "scale", self._handle_size() / self.HANDLE, Theme.duration("short2"),
                 Theme.easing("emphasized_decelerate"))

    def _activate(self) -> None:
        self.selected.set(not self.selected.get())
        self._changed(self.selected.get())
