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

import math
from typing import Any, Callable, Optional

from tesserae import a11y, tokens
from tesserae.icons import ICON_VIEW_BOX, icon_path
from tesserae.interaction import Interaction
from tesserae.listeners import Listeners
from tesserae.reactive import Effect, Signal, untrack
from tesserae.theme import Theme

__all__ = [
    "DISABLED_CONTAINER", "DISABLED_CONTENT", "Checkbox", "Control", "RadioButton", "RadioGroup", "STATE_LAYER_SIZE",
    "Slider", "SpinBox", "Switch", "TARGET_SIZE",
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


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


class Slider(Control):
    """MD3's slider: a 4 px track, `primary` up to the value and
    `surface_container_highest` after it, and a 20 px `primary` handle.
    Dragging the handle, or pressing anywhere on the track, sets the value
    (the pointer is captured, so a drag can leave the slider). The arrow
    keys step it, Page Up/Down by ten steps, Home/End to the ends, and
    assistive technology's increment/decrement/set_value work too.
    `on_change` fires once a drag ends, and after each key.

    `value` runs from `min` to `max`, snapped to `step` when one is given;
    the keys move by `step`, else a hundredth of the range. While dragged,
    the handle's state layer shows MD3's dragged opacity."""

    role = "slider"
    TRACK = 4.0
    HANDLE = 20.0

    def __init__(self, window: Any, *, value: float = 0.0, min: float = 0.0, max: float = 1.0,
                 step: Optional[float] = None, width: float = 200.0, color: Optional[RGBA] = None,
                 **kwargs: Any) -> None:
        if not max > min:
            raise ValueError(f"a slider needs max > min, got min={min!r}, max={max!r}")
        if step is not None and not step > 0:
            raise ValueError(f"a slider's step must be positive, got {step!r}")
        self.min, self.max, self.step = float(min), float(max), step
        self.width = float(width)
        self.target = (self.width, TARGET_SIZE)
        self._color = color
        self._dragging = False
        self._start: float = 0.0
        self.value = Signal(self._snap(value))
        super().__init__(window, **kwargs)
        for event, handler in (("pointer_down", self._on_down), ("pointer_move", self._on_move),
                               ("pointer_up", self._on_up), ("key_down", self._on_key)):
            self._undo.append(self._listen(self.node, event, handler))
        self._undo.append(a11y.on_action(self.node, {
            "increment": lambda e: self._user_set(self.value.get() + self._key_step()),
            "decrement": lambda e: self._user_set(self.value.get() - self._key_step()),
            "set_value": lambda e: self._user_set(float(e.value)) if e.value is not None else None,
        }, listen=self._listen))

    @property
    def _span(self) -> float:
        """How far the handle's centre travels."""
        return self.width - self.HANDLE

    def _snap(self, value: float) -> float:
        value = _clamp(float(value), self.min, self.max)
        if self.step:
            # half rounds up, as HTML's range input does (Python's round() goes to even)
            value = self.min + math.floor((value - self.min) / self.step + 0.5) * self.step
            value = _clamp(round(value, 10), self.min, self.max)
        return value

    def _key_step(self) -> float:
        return self.step or (self.max - self.min) / 100

    def _fraction(self) -> float:
        return (self._snap(self.value.get()) - self.min) / (self.max - self.min)

    def _build(self) -> None:
        centre_y = TARGET_SIZE / 2
        radius = self.HANDLE / 2
        self.inactive = self.window.create("box", position="absolute", x=radius, y=centre_y - self.TRACK / 2,
                                           width=self._span, height=self.TRACK, corner_radius=self.TRACK / 2,
                                           hit_testable=False, a11y_hidden=True)
        self.active = self.window.create("box", position="absolute", x=radius, y=centre_y - self.TRACK / 2,
                                         width=0.0, height=self.TRACK, corner_radius=self.TRACK / 2,
                                         hit_testable=False, a11y_hidden=True)
        self.handle = self.window.create("box", position="absolute", x=0.0, y=centre_y - radius, width=self.HANDLE,
                                         height=self.HANDLE, corner_radius=radius, hit_testable=False,
                                         a11y_hidden=True)
        for child in (self.inactive, self.active, self.handle):
            self.node.add_child(child)
        self.surface.set(x=radius - STATE_LAYER_SIZE / 2)  # centred on the handle at the start

    def _on_colour(self) -> RGBA:
        return self._color or self.color("primary")

    def _tint(self) -> RGBA:
        return self._on_colour()

    def _paint(self, animate: bool) -> None:
        value, disabled = self._snap(self.value.get()), self.disabled.get()
        self.node.set(value=value, value_min=self.min, value_max=self.max, value_step=self._key_step())
        on_surface = self.color("on_surface")
        if disabled:
            active = handle = with_alpha(on_surface, DISABLED_CONTENT)
            inactive = with_alpha(on_surface, DISABLED_CONTAINER)
        else:
            active = handle = self._on_colour()
            inactive = self.color("surface_container_highest")
        ms = self._ms(animate, "short3")
        self._to(self.active, "fill", active, ms)
        self._to(self.inactive, "fill", inactive, ms)
        self._to(self.handle, "fill", handle, ms)
        # position follows the value at once: a drag mustn't lag behind the pointer
        offset = self._fraction() * self._span
        self.active.set(width=offset)
        self._to(self.handle, "translate_x", offset, 0)
        self._to(self.surface, "translate_x", offset, 0)

    def _activate(self) -> None:
        pass  # a click has already set the value, at pointer_down

    def _user_set(self, value: float) -> None:
        before = self.value.get()
        self.value.set(self._snap(value))
        if self.value.get() != before:
            self._changed(self.value.get())

    def _from_x(self, x: float) -> float:
        return self.min + _clamp((x - self.HANDLE / 2) / self._span, 0.0, 1.0) * (self.max - self.min)

    def _on_down(self, event: Any) -> None:
        if self.disabled.get() or event.x is None:
            return
        self._dragging = True
        self._start = self.value.get()
        self.node.capture_pointer()
        self.interaction.set_dragged(True)
        self.value.set(self._snap(self._from_x(event.x)))

    def _on_move(self, event: Any) -> None:
        if self._dragging and event.x is not None:
            self.value.set(self._snap(self._from_x(event.x)))

    def _on_up(self, event: Any) -> None:
        if not self._dragging:
            return
        self._dragging = False
        self.node.release_pointer()
        self.interaction.set_dragged(False)
        if self.value.get() != self._start:
            self._changed(self.value.get())

    def _on_key(self, event: Any) -> None:
        if self.disabled.get():
            return
        step = self._key_step()
        moves = {"arrow_right": step, "arrow_up": step, "arrow_left": -step, "arrow_down": -step,
                 "page_up": 10 * step, "page_down": -10 * step}
        if event.key in moves:
            self._user_set(self.value.get() + moves[event.key])
        elif event.key == "home":
            self._user_set(self.min)
        elif event.key == "end":
            self._user_set(self.max)


class SpinBox:
    """A number field between − and + buttons, as `tre`'s spin box was
    (MD3 has no spin box of its own, so it's built from MD3's parts: two
    40 px icon buttons and a filled field).

    `value` (a `Signal`) steps by `step` with the buttons, the up and down
    arrows in the field, and assistive technology's increment/decrement;
    typing a number sets it once it parses and fits `min`..`max`, and
    leaving the field puts back the value's text if what was typed didn't.
    A button whose step would pass a bound is disabled. `on_change` hears
    the user's changes. Not a `Control`: it's three targets, not one."""

    BUTTON = 40.0
    FIELD = (64.0, 40.0)

    def __init__(self, window: Any, *, value: float = 0, min: Optional[float] = None, max: Optional[float] = None,
                 step: float = 1, theme: Optional[Theme] = None, label: Optional[str] = None,
                 disabled: bool = False, listen: Optional[Listen] = None) -> None:
        if step <= 0:
            raise ValueError(f"a spin box's step must be positive, got {step!r}")
        if min is not None and max is not None and max < min:
            raise ValueError(f"a spin box needs max >= min, got min={min!r}, max={max!r}")
        self.window = window
        self.theme = theme if theme is not None else Theme.resolve()
        self.min, self.max, self.step = min, max, step
        self.value = Signal(self._fit(value))
        self.disabled = Signal(bool(disabled))
        self._listen: Listen = listen if listen is not None else Listeners().listen
        self._changes: list[Callable[[Any], None]] = []
        self._undo: list[Callable[[], None]] = []
        self.node = window.create("box", flex_direction="horizontal", align_items="center", gap=4.0)
        self.decrement, self._dec_icon, self._dec_it = self._button("remove", "Decrease", -1)
        self.field = window.create("box", width=self.FIELD[0], height=self.FIELD[1], corner_radius=8.0,
                                   padding_left=8.0, padding_right=8.0, align_items="center")
        self.input = window.create("text_input", text=self._format(self.value.get()), font_family="Roboto",
                                   font_size=14.0, flex_grow=1.0, focusable=True, role="textbox")
        self.field.add_child(self.input)
        if label is not None:
            a11y.describe(self.input, label=label)
        self.increment, self._inc_icon, self._inc_it = self._button("add", "Increase", 1)
        for child in (self.decrement, self.field, self.increment):
            self.node.add_child(child)
        for event, handler in (("change", self._on_typed), ("unfocus", self._on_leave_field),
                               ("key_down", self._on_key)):
            self._undo.append(self._listen(self.input, event, handler))
        self._undo.append(a11y.on_action(self.input, {"increment": lambda e: self._bump(1),
                                                     "decrement": lambda e: self._bump(-1)}, listen=self._listen))
        self._effect = Effect(self._render)

    # -- for app code -------------------------------------------------------------

    def on_change(self, fn: Callable[[Any], None]) -> Callable[[], None]:
        self._changes.append(fn)
        return lambda: self._changes.remove(fn) if fn in self._changes else None

    def color(self, role: str) -> RGBA:
        return self.theme.role(role) or tokens.BASELINE[role]

    def set_theme(self, theme: Theme) -> None:
        self.theme = theme
        for it in (self._dec_it, self._inc_it):
            it.retint(self.color("on_surface_variant"), self.color("secondary"))
        untrack(self._paint)

    def destroy(self) -> None:
        self._effect.dispose()
        for undo in self._undo:
            undo()
        self._undo = []
        for it in (self._dec_it, self._inc_it):
            it.detach()
        self.node.destroy()

    # -- internals -----------------------------------------------------------------

    def _button(self, icon: str, label: str, direction: int) -> tuple[Any, Any, Interaction]:
        button = self.window.create("box", width=self.BUTTON, height=self.BUTTON, corner_radius=self.BUTTON / 2,
                                    align_items="center", justify_content="center", focusable=True,
                                    role="button", label=label, cursor="pointer")
        glyph = self.window.create("path", data=icon_path(icon), view_box=ICON_VIEW_BOX, width=24.0, height=24.0,
                                   hit_testable=False, a11y_hidden=True)
        button.add_child(glyph)
        it = Interaction(self.window, button, self.color("on_surface_variant"), self._listen, self.color("secondary"))
        self._undo.append(self._listen(button, "click", lambda e: self._bump(direction)))
        return button, glyph, it

    def _fit(self, value: float) -> float:
        """`value` held within `min`..`max`."""
        if self.min is not None and value < self.min:
            value = self.min
        if self.max is not None and value > self.max:
            value = self.max
        return value

    def _format(self, value: float) -> str:
        whole = all(isinstance(n, int) or float(n).is_integer() for n in (value, self.step))
        return str(int(value)) if whole else f"{value:g}"

    def _can(self, direction: int) -> bool:
        if self.disabled.get():
            return False
        bound = self.max if direction > 0 else self.min
        return bound is None or (self.value.get() + direction * self.step) * direction <= bound * direction

    def _bump(self, direction: int) -> None:
        if self._can(direction):
            self._user_set(self.value.get() + direction * self.step)

    def _user_set(self, value: float) -> None:
        before = self.value.get()
        value = round(value, 10)
        if isinstance(self.step, int) and float(value).is_integer():
            value = int(value)
        self.value.set(self._fit(value))
        self.input.set(text=self._format(self.value.get()))
        if self.value.get() != before:
            for fn in list(self._changes):
                fn(self.value.get())

    def _parse(self, text: str) -> Optional[float]:
        try:
            number = float(text)
        except ValueError:
            return None
        if (self.min is not None and number < self.min) or (self.max is not None and number > self.max):
            return None
        return int(number) if number.is_integer() and isinstance(self.step, int) else number

    def _on_typed(self, event: Any) -> None:
        number = self._parse(self.input.get("text") or "")
        if number is not None and number != self.value.get():
            self.value.set(number)
            for fn in list(self._changes):
                fn(number)

    def _on_leave_field(self, event: Any) -> None:
        if self._parse(self.input.get("text") or "") != self.value.get():
            self.input.set(text=self._format(self.value.get()))

    def _on_key(self, event: Any) -> None:
        if event.key == "arrow_up":
            self._bump(1)
        elif event.key == "arrow_down":
            self._bump(-1)

    def _render(self) -> None:
        self.value.get()
        self.disabled.get()
        self._paint()

    def _paint(self) -> None:
        value, disabled = self.value.get(), self.disabled.get()
        if not self.input.get("focused") or self._parse(self.input.get("text") or "") != value:
            self.input.set(text=self._format(value))
        on_surface = self.color("on_surface")
        text = with_alpha(on_surface, DISABLED_CONTENT) if disabled else on_surface
        field = (with_alpha(on_surface, DISABLED_CONTAINER) if disabled
                 else self.color("surface_container_highest"))
        self.field.set(fill=field)
        self.input.set(fill=text, caret_color=self.color("primary"), focusable=not disabled, disabled=disabled)
        for direction, button, glyph, it in ((-1, self.decrement, self._dec_icon, self._dec_it),
                                             (1, self.increment, self._inc_icon, self._inc_it)):
            usable = self._can(direction)
            glyph.set(fill=self.color("on_surface_variant") if usable else with_alpha(on_surface, DISABLED_CONTENT))
            button.set(focusable=usable, disabled=not usable, cursor="pointer" if usable else "default")
            it.enabled = usable
