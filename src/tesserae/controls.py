"""MD3's stateful controls, built by Tesserae from `tre` 0.3.4's building
blocks, since `tre` 0.3.5 removes its own.

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
from tesserae.follow import initial_theme, unfollow
from tesserae.icons import icon_path, icon_view_box
from tesserae.interaction import Interaction
from tesserae.listeners import Listeners, handled, listen_window
from tesserae.reactive import Effect, Signal, untrack
from tesserae.theme import Theme
from tesserae import motion

__all__ = [
    "DISABLED_CONTAINER", "DISABLED_CONTENT", "Checkbox", "Control", "RadioButton", "RadioGroup", "STATE_LAYER_SIZE",
    "CircularProgress", "LinearProgress", "LoadingIndicator", "RangeSlider", "Slider", "SpinBox", "Switch", "TARGET_SIZE",
    "TimePickerDial",
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
                 disabled: bool = False, listen: Optional[Listen] = None, size: Optional[float] = None,
                 width: Optional[float] = None, height: Optional[float] = None) -> None:
        self.window = window
        self.theme = initial_theme(window, theme, self)  # the app's, followed, without one (M50)
        self.disabled = Signal(bool(disabled))
        self._listen: Listen = listen if listen is not None else Listeners().listen
        self._changes: list[Callable[[Any], None]] = []
        self._undo: list[Callable[[], None]] = []
        self._painted = False
        width = float(width if width is not None else size if size is not None else self.target[0])
        height = float(height if height is not None else size if size is not None else self.target[1])
        self.target = (width, height)
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
        self._undo.append(self._listen(self.node, "click", handled(self._on_click)))  # its click alone, even disabled (M49)
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

    def dispose(self) -> None:
        """Stops the control (its repainting and listeners) but leaves its
        node, for a caller about to free the tree it sits in."""
        unfollow(self.window, self)
        self._effect.dispose()
        for undo in self._undo:
            undo()
        self._undo = []
        self.interaction.detach()

    def destroy(self) -> None:
        """Stops the control and frees its nodes."""
        self.dispose()
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
        return Theme.duration(token) if animate and not motion.reduced(self.window) else 0

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
    DASH = "M4,9 L14,9"  # a checkbox that is neither on nor off (a parent of some checked children)

    def __init__(self, window: Any, *, checked: Optional[bool] = False, color: Optional[RGBA] = None, error: bool = False, **kwargs: Any) -> None:
        self.checked = Signal(None if checked is None else bool(checked))  # None is indeterminate
        self.error = Signal(bool(error))
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
        return self.color("error") if self.error.get() else (self._color or self.color("primary"))

    def _tint(self) -> RGBA:
        # MD3: a selected control's hover and focus layers are `primary` (`error` in error)
        return self._selected() if self.checked.get() is not False else self.color("error") if self.error.get() else self.color("on_surface")

    def _paint(self, animate: bool) -> None:
        checked, disabled, error = self.checked.get(), self.disabled.get(), self.error.get()
        mixed = checked is None
        on = checked is not False
        self.node.set(checked=checked)
        off = with_alpha(self.color("on_surface"), DISABLED_CONTENT)
        if on:
            fill = off if disabled else self._selected()
            stroke = fill
            mark = self.color("surface") if disabled else self.color("on_error" if error else "on_primary")
        else:
            fill, stroke = _CLEAR, off if disabled else self.color("error" if error else "on_surface_variant")
            mark = self.mark.get("stroke_color") or _CLEAR
        colour_ms = self._ms(animate, "short3")
        self._to(self.box, "fill", fill, colour_ms)
        self._to(self.box, "stroke_color", stroke, colour_ms)
        self.mark.set(stroke_color=mark, data=self.DASH if mixed else self.CHECK)
        if on:
            self._to(self.mark, "trim_end", 1.0, self._ms(animate, "medium1"), Theme.easing("emphasized_decelerate"))
        else:
            self._to(self.mark, "trim_end", 0.0, self._ms(animate, "short3"), Theme.easing("emphasized_accelerate"))

    def _activate(self) -> None:
        self.checked.set(not self.checked.get())  # off or in between becomes on; on becomes off
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
        """The radio button that is selected, or `None`."""
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
                 color: Optional[RGBA] = None, error: bool = False, **kwargs: Any) -> None:
        self.selected = Signal(bool(selected))
        self.error = Signal(bool(error))
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
        return self.color("error") if self.error.get() else (self._color or self.color("primary"))

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
        colour = off if disabled else (self._on_colour() if selected else self.color("error" if self.error.get() else "on_surface_variant"))
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

    def __init__(self, window: Any, *, selected: bool = False, color: Optional[RGBA] = None, icons: bool = False, **kwargs: Any) -> None:
        self.selected = Signal(bool(selected))
        self._color = color
        self.icons = bool(icons)  # a check on the handle when on, a cross when off; the off handle is then as big as the on one
        self._pressed = False
        super().__init__(window, **kwargs)
        self._undo.append(self._listen(self.node, "pointer_down", lambda e: self._press(True)))
        self._undo.append(self._listen(self.node, "pointer_up", lambda e: self._press(False)))
        self._undo.append(self._listen(self.node, "pointer_cancel", lambda e: self._press(False)))  # 0.3.0 M2
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
        self.icon = self.window.create("path", data=icon_path("check"), view_box=icon_view_box("check"), width=16.0, height=16.0,
                                       position="absolute", x=(self.HANDLE - 16.0) / 2, y=(self.HANDLE - 16.0) / 2,
                                       visible=self.icons, hit_testable=False, a11y_hidden=True)
        self.handle.add_child(self.icon)
        self.node.add_child(self.track)
        # the state layer's circle rides on the handle
        offset = (self.target[1] - self.HEIGHT) / 2  # the track is centred in the target
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
        return self.ON if self.selected.get() or self.icons else self.OFF

    def _paint(self, animate: bool) -> None:
        selected, disabled = self.selected.get(), self.disabled.get()
        self.node.set(checked=selected)
        on_surface = self.color("on_surface")
        if self.icons:
            self.icon.set(data=icon_path("check" if selected else "close"),
                          fill=with_alpha(on_surface, DISABLED_CONTENT) if disabled else
                          self.color("on_primary_container" if selected else "surface_container_highest"))
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


_max, _min = max, min  # a Slider has parameters named `min` and `max`


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
    the handle's state layer shows MD3's dragged opacity.

    `vertical` stands it up: the value grows upwards (the bottom is `min`),
    `width` is then the touch target's and `height` the length. `size`
    (`xs` to `xl`) is MD3 Expressive's: a thicker track in two pieces with a
    gap, and a thin 4 px handle across it; `icon` is a glyph inset at the
    start of the track (from size `s` up, where it fits)."""

    role = "slider"
    TRACK = 4.0
    HANDLE = 20.0
    #: MD3 Expressive's sizes: the track's thickness, the handle's length across the track, and the inset icon's size (0: none fits).
    #: Written from memory of the spec, not checked against it (#250).
    SIZES = {"xs": (16.0, 44.0, 0.0), "s": (24.0, 44.0, 16.0), "m": (40.0, 52.0, 24.0), "l": (56.0, 68.0, 24.0), "xl": (96.0, 108.0, 32.0)}
    HANDLE_WIDTH = 4.0  # an Expressive handle's length along the track
    GAP = 6.0           # between an Expressive handle and each piece of track

    def __init__(self, window: Any, *, value: float = 0.0, min: float = 0.0, max: float = 1.0,
                 step: Optional[float] = None, width: Optional[float] = None, height: Optional[float] = None,
                 color: Optional[RGBA] = None, ticks: bool = False, value_indicator: bool = False,
                 vertical: bool = False, size: Optional[str] = None, icon: Optional[str] = None, **kwargs: Any) -> None:
        node_size = self._configure(min, max, step, width, height, color, ticks, value_indicator, vertical, size, icon)
        self._start: float = 0.0
        self.value = Signal(self._snap(value))
        super().__init__(window, **node_size, **kwargs)
        for event, handler in (("pointer_down", self._on_down), ("pointer_move", self._on_move),
                               ("pointer_up", self._on_up), ("pointer_cancel", self._on_up),
                               ("key_down", self._on_key)):
            self._undo.append(self._listen(self.node, event, handler))
        self._undo.append(a11y.on_action(self.node, {
            "increment": lambda e: self._user_set(self.value.get() + self._key_step()),
            "decrement": lambda e: self._user_set(self.value.get() - self._key_step()),
            "set_value": lambda e: self._user_set(float(e.value)) if e.value is not None else None,
        }, listen=self._listen))
        self._follow_layout()

    def _configure(self, min: float, max: float, step: Optional[float], width: Optional[float], height: Optional[float], color: Optional[RGBA],
                   ticks: bool, value_indicator: bool, vertical: bool, size: Optional[str], icon: Optional[str]) -> dict[str, float]:
        """What a slider and a range slider share: the range, the look and the geometry. Returns the node's `width` and `height`."""
        if not max > min:
            raise ValueError(f"a slider needs max > min, got min={min!r}, max={max!r}")
        if step is not None and not step > 0:
            raise ValueError(f"a slider's step must be positive, got {step!r}")
        if size is not None and size not in self.SIZES:
            raise ValueError(f"a slider's size is one of {', '.join(self.SIZES)}, got {size!r}")
        if icon is not None and (size is None or not self.SIZES[size][2]):
            raise ValueError("a slider's inset icon needs a size with room for it (s, m, l or xl)" + (f", not {size!r}" if size else ""))
        self.min, self.max, self.step = float(min), float(max), step
        self.vertical = bool(vertical)
        self.size = size
        self.icon_name = icon
        self._thick, self._across, self._icon_px = self.SIZES[size] if size else (self.TRACK, self.HANDLE, 0.0)
        self._hl = self.HANDLE_WIDTH if size else self.HANDLE  # the handle's length along the track
        room = _max(TARGET_SIZE, self._across)  # the touch target across the track
        if self.vertical:
            across, self.length = (float(width) if width is not None else room), (float(height) if height is not None else 200.0)
            node_size = {"width": across, "height": self.length}
        else:
            self.length, across = (float(width) if width is not None else 200.0), (float(height) if height is not None else room)
            node_size = {"width": self.length, "height": across}
        self.cross = across
        self._color = color
        self.ticks = bool(ticks and step)  # a mark at each step (a discrete slider); without a step there is nothing to mark
        self.value_indicator = bool(value_indicator)  # a bubble over the handle with the value, while it is dragged or has the keyboard
        self._live: list[Callable[[Any], None]] = []
        self._shown = False
        self._dragging = False
        return node_size

    def _follow_layout(self) -> None:
        """A slider laid out longer or shorter than it was built (flex, a percentage, a resized window) takes the room it was given (#252);
        layout is settled when a frame has been drawn, and `_fit_length` does nothing while the length is the same."""
        for event in ("frame", "resize"):
            self._undo.append(listen_window(self.window, event, lambda e: untrack(lambda: self._fit_length() and self._paint(animate=False))))

    @property
    def width(self) -> float:
        """The node's width: its length, or (stood up) the touch target's."""
        return self.cross if self.vertical else self.length

    @property
    def _span(self) -> float:
        """How far the handle's centre travels."""
        return self.length - self._hl

    @property
    def _edge(self) -> float:
        """From the start of the track to the handle's centre at `min`."""
        return self._hl / 2

    # -- the axis: the track starts at the left, or (stood up) at the bottom -------------------------------------------------

    def _place(self, node: Any, start: float, extent: float, across: float, thickness: float, **more: Any) -> None:
        """Puts a box that begins `start` from the track's start and runs `extent` along it, `across` from the target's edge and `thickness` thick."""
        if self.vertical:
            node.set(x=across, y=self.length - start - extent, width=thickness, height=extent, **more)
        else:
            node.set(x=start, y=across, width=extent, height=thickness, **more)

    def _slide(self, node: Any, offset: float) -> None:
        """Moves a node `offset` along the track from where `_place` put it, at once."""
        self._to(node, "translate_y" if self.vertical else "translate_x", -offset if self.vertical else offset, 0)

    def _fit_length(self) -> bool:
        """Takes the length the node was laid out at (the engine reads pending layout), moving the track and the tick marks with it; whether it changed."""
        laid = float(self.node.get("layout_height" if self.vertical else "layout_width") or 0.0)
        if laid <= self._hl or abs(laid - self.length) < 0.5:
            return False
        self.length = laid
        mid = self.cross / 2
        if not self.size:
            self._place(self.inactive, self._edge, self._span, mid - self._thick / 2, self._thick)
        self._place_ticks()
        self._place_start()
        return True

    def _place_start(self) -> None:
        """What sits at the start of the track and moves with its end when the length changes: the handle, the state layer, the bubble."""
        mid = self.cross / 2
        self._place(self.handle, 0.0, self._hl, mid - self._across / 2, self._across)
        self._place(self.bubble, self._edge - 14.0, 28.0, mid - self._across / 2 - 8.0 - 28.0, 28.0)
        if self.vertical:
            self.surface.set(y=self.length - self._edge - STATE_LAYER_SIZE / 2)
        else:
            self.surface.set(x=self._edge - STATE_LAYER_SIZE / 2)

    def _place_ticks(self) -> None:
        mid = self.cross / 2
        count = len(self.tick_marks) - 1
        for i, mark in enumerate(self.tick_marks):
            self._place(mark, self._edge + self._span * i / count - 1.0, 2.0, mid - 1.0, 2.0)

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
        mid = self.cross / 2
        thick, round_ = self._thick, self._thick / 2
        self.inactive = self.window.create("box", position="absolute", corner_radius=round_, hit_testable=False, a11y_hidden=True)
        self.active = self.window.create("box", position="absolute", corner_radius=round_, hit_testable=False, a11y_hidden=True)
        self.handle = self.window.create("box", position="absolute", corner_radius=min(self._hl, self._across) / 2, hit_testable=False,
                                         a11y_hidden=True)
        self._place(self.inactive, self._edge, self._span, mid - thick / 2, thick)
        self._place(self.active, self._edge, 0.0, mid - thick / 2, thick)
        for child in (self.inactive, self.active, self.handle):
            self.node.add_child(child)
        self.tick_marks: list[Any] = []
        count = round((self.max - self.min) / self.step) if self.ticks else 0
        if 0 < count <= 100:
            for i in range(count + 1):
                mark = self.window.create("box", position="absolute", corner_radius=1.0, hit_testable=False, a11y_hidden=True)
                self.node.add_child(mark)
                self.tick_marks.append(mark)
        self._place_ticks()
        self.icon = None
        if self.icon_name is not None:  # at the start of the track, centred in its thickness
            px = self._icon_px
            self.icon = self.window.create("path", data=icon_path(self.icon_name), view_box=icon_view_box(self.icon_name), position="absolute",
                                           hit_testable=False, a11y_hidden=True)
            self._place(self.icon, (thick - px) / 2, px, mid - px / 2, px)
            self.node.add_child(self.icon)
        self.bubble = self.window.create("box", corner_radius=14.0, align_items="center", justify_content="center", visible=False,
                                         position="absolute", hit_testable=False, a11y_hidden=True)
        self.bubble_text = self.window.create("text", text="", font_family="Roboto", font_size=12.0, font_weight=500.0, hit_testable=False,
                                              a11y_hidden=True)
        self.bubble.add_child(self.bubble_text)
        self.node.add_child(self.bubble)
        self._place_start()  # the handle, the bubble and the state layer, centred on the handle at the start
        for event, shown in (("focus", True), ("unfocus", False)):
            self._undo.append(self._listen(self.node, event, lambda e, shown=shown: self._show_bubble(shown and bool(getattr(e, "focus_visible", True)))))

    def _on_colour(self) -> RGBA:
        return self._color or self.color("primary")

    def _tint(self) -> RGBA:
        return self._on_colour()

    def _paint(self, animate: bool) -> None:
        self._fit_length()
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
        mid, thick = self.cross / 2, self._thick
        if self.size:  # two pieces of track, each a gap from the handle
            centre = self._edge + offset
            active_end = _max(centre - self._hl / 2 - self.GAP, 0.0)
            inactive_start = centre + self._hl / 2 + self.GAP
            self._place(self.active, 0.0, active_end, mid - thick / 2, thick)
            self._place(self.inactive, inactive_start, _max(self.length - inactive_start, 0.0), mid - thick / 2, thick)
        else:
            self._place(self.active, self._edge, offset, mid - thick / 2, thick)
        self._slide(self.handle, offset)
        self._slide(self.surface, offset)
        if self.icon is not None:  # over the active piece it is on the colour, else on the track
            covered = self.size and active_end >= (thick - self._icon_px) / 2 + self._icon_px
            self.icon.set(fill=with_alpha(on_surface, DISABLED_CONTENT) if disabled
                          else self.color("on_primary") if covered else self.color("on_surface_variant"))
        count = len(self.tick_marks) - 1
        for i, mark in enumerate(self.tick_marks):  # a mark over the active part is the on-colour, over the rest the variant
            reached = count > 0 and i / count <= self._fraction() + 1e-9
            mark.set(fill=self.color("on_primary") if reached and not disabled else self.color("on_surface_variant"))
        self.bubble.set(fill=self.color("inverse_surface"))
        self.bubble_text.set(text=f"{value:g}", fill=self.color("inverse_on_surface"))
        self._slide(self.bubble, offset)

    def _activate(self) -> None:
        pass  # a click has already set the value, at pointer_down

    def on_input(self, fn: Callable[[float], None]) -> Callable[[], None]:
        """Calls `fn(value)` on every change the user makes, while a drag is still going (`on_change` hears the end of one). Returns the function
        that stops it."""
        self._live.append(fn)
        return lambda: self._live.remove(fn) if fn in self._live else None

    def _input(self) -> None:
        for fn in list(self._live):
            fn(self.value.get())

    def _show_bubble(self, shown: bool) -> None:
        self._shown = shown
        self.bubble.set(visible=self.value_indicator and (shown or self._dragging))

    def _user_set(self, value: float) -> None:
        before = self.value.get()
        self.value.set(self._snap(value))
        if self.value.get() != before:
            self._input()
            self._changed(self.value.get())

    def _at(self, event: Any) -> Optional[float]:
        """How far along the track, from its start, the pointer is (`None` for a key's click, which has no place)."""
        point = event.y if self.vertical else event.x
        if point is None:
            return None
        return self.length - point if self.vertical else point

    def _from_event(self, event: Any) -> float:
        if self._fit_length():
            untrack(lambda: self._paint(animate=False))  # the handle and the fill go to the new length even if the value stays
        return self.min + _clamp((self._at(event) - self._edge) / self._span, 0.0, 1.0) * (self.max - self.min)

    def _on_down(self, event: Any) -> None:
        if self.disabled.get() or self._at(event) is None:
            return
        self._dragging = True
        self._start = self.value.get()
        self.node.capture_pointer()
        self.interaction.set_dragged(True)
        self._show_bubble(self._shown)
        before = self.value.get()
        self.value.set(self._snap(self._from_event(event)))
        if self.value.get() != before:
            self._input()

    def _on_move(self, event: Any) -> None:
        if self._dragging and self._at(event) is not None:
            before = self.value.get()
            self.value.set(self._snap(self._from_event(event)))
            if self.value.get() != before:
                self._input()

    def _on_up(self, event: Any) -> None:
        if not self._dragging:
            return
        self._dragging = False
        self.node.release_pointer()
        self.interaction.set_dragged(False)
        self._show_bubble(self._shown)
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


class RangeSlider(Slider):
    """A slider with two handles: `low` and `high`, two `Signal`s, never crossing (`low <= high`). Each handle is its own stop for Tab, has the
    arrow, Page and Home/End keys (Home and End go to the ends of what that handle may reach), is its own slider for a screen reader
    (minimum and maximum) and has its own state layer and focus ring; the control itself is the group around them. A press on the track moves the
    nearer handle there, and a drag keeps hold of the handle it began on. The track between the handles is `primary`; the rest is
    `surface_container_highest`. `size`, `vertical`, `ticks` and `value_indicator` are the slider's.

    `on_input(fn)` and `on_change(fn)` hear `(low, high)`; a bound `low` or `high` is written the same way a slider's `value` is."""

    role = "group"
    THUMB = 48.0  # a handle's touch target along the track

    def __init__(self, window: Any, *, low: float = 0.0, high: float = 1.0, min: float = 0.0, max: float = 1.0,
                 step: Optional[float] = None, width: Optional[float] = None, height: Optional[float] = None,
                 color: Optional[RGBA] = None, ticks: bool = False, value_indicator: bool = False,
                 vertical: bool = False, size: Optional[str] = None, icon: Optional[str] = None, label: Optional[str] = None,
                 **kwargs: Any) -> None:
        node_size = self._configure(min, max, step, width, height, color, ticks, value_indicator, vertical, size, icon)
        self._label = label
        self.low = Signal(self._snap(low))
        self.high = Signal(_max(self._snap(high), self.low.get()))  # a `high` below `low` is raised to it
        self._drag: Optional[int] = None  # the handle a drag holds (0: low, 1: high)
        self._began: tuple[float, float] = (self.low.get(), self.high.get())
        self._shown_for = [False, False]
        Control.__init__(self, window, label=label, **node_size, **kwargs)
        self._undo.append(self._listen(self.node, "pointer_down", self._on_down))
        self._undo.append(self._listen(self.node, "pointer_move", self._on_move))
        self._undo.append(self._listen(self.node, "pointer_up", self._on_up))
        self._undo.append(self._listen(self.node, "pointer_cancel", self._on_up))
        for i, thumb in enumerate(self.thumbs):
            self._undo.append(self._listen(thumb.node, "key_down", lambda e, i=i: self._on_key_for(i, e)))
            self._undo.append(a11y.on_action(thumb.node, {
                "increment": lambda e, i=i: self._user_set(i, self._of(i) + self._key_step()),
                "decrement": lambda e, i=i: self._user_set(i, self._of(i) - self._key_step()),
                "set_value": lambda e, i=i: self._user_set(i, float(e.value)) if e.value is not None else None,
            }, listen=self._listen))
        self._follow_layout()

    # -- the two values ------------------------------------------------------------------------------------------------------

    def _of(self, i: int) -> float:
        return (self.low, self.high)[i].get()

    def _pair(self) -> tuple[float, float]:
        """The two values, snapped and in order, whatever the Signals were last set to."""
        low = self._snap(self.low.get())
        return low, _max(self._snap(self.high.get()), low)

    def _bounds(self, i: int) -> tuple[float, float]:
        """What handle `i` may reach: the low one up to the high one, the high one down to the low one."""
        low, high = self._pair()
        return (self.min, high) if i == 0 else (low, self.max)

    def _set_handle(self, i: int, value: float) -> None:
        lo, hi = self._bounds(i)
        (self.low, self.high)[i].set(_clamp(self._snap(value), lo, hi))

    def _user_set(self, i: int, value: float) -> None:
        before = self._pair()
        self._set_handle(i, value)
        if self._pair() != before:
            self._input()
            self._changed(self._pair())

    def _input(self) -> None:
        for fn in list(self._live):
            fn(self._pair())

    def _fractions(self) -> tuple[float, float]:
        low, high = self._pair()
        return (low - self.min) / (self.max - self.min), (high - self.min) / (self.max - self.min)

    # -- building --------------------------------------------------------------------------------------------------------------

    def _build(self) -> None:
        from types import SimpleNamespace

        mid = self.cross / 2
        thick = self._thick
        self.inactive = self.window.create("box", position="absolute", corner_radius=thick / 2, hit_testable=False, a11y_hidden=True)
        self.inactive_high = self.window.create("box", position="absolute", corner_radius=thick / 2, hit_testable=False, a11y_hidden=True)
        self.active = self.window.create("box", position="absolute", corner_radius=thick / 2, hit_testable=False, a11y_hidden=True)
        self._place(self.inactive, self._edge, self._span, mid - thick / 2, thick)
        self._place(self.active, self._edge, 0.0, mid - thick / 2, thick)
        for piece in (self.inactive, self.inactive_high, self.active):
            self.node.add_child(piece)
        self.tick_marks: list[Any] = []
        count = round((self.max - self.min) / self.step) if self.ticks else 0
        if 0 < count <= 100:
            for i in range(count + 1):
                mark = self.window.create("box", position="absolute", corner_radius=1.0, hit_testable=False, a11y_hidden=True)
                self.node.add_child(mark)
                self.tick_marks.append(mark)
        self._place_ticks()
        self.icon = None
        if self.icon_name is not None:  # at the start of the track: over the low piece of it
            px = self._icon_px
            self.icon = self.window.create("path", data=icon_path(self.icon_name), view_box=icon_view_box(self.icon_name), position="absolute",
                                           hit_testable=False, a11y_hidden=True)
            self._place(self.icon, (thick - px) / 2, px, mid - px / 2, px)
            self.node.add_child(self.icon)
        self.thumbs: list[Any] = []
        names = ("minimum", "maximum")
        for i in range(2):
            handle = self.window.create("box", position="absolute", corner_radius=_min(self._hl, self._across) / 2, hit_testable=False, a11y_hidden=True)
            bubble = self.window.create("box", corner_radius=14.0, align_items="center", justify_content="center", visible=False, position="absolute",
                                        hit_testable=False, a11y_hidden=True)
            bubble_text = self.window.create("text", text="", font_family="Roboto", font_size=12.0, font_weight=500.0, hit_testable=False, a11y_hidden=True)
            bubble.add_child(bubble_text)
            node = self.window.create("box", position="absolute", focusable=True, role="slider", cursor="pointer")
            a11y.describe(node, label=self._handle_label(i))
            surface = self.window.create("box", position="absolute", x=(self.THUMB - STATE_LAYER_SIZE) / 2 if not self.vertical else (self.cross - STATE_LAYER_SIZE) / 2,
                                         y=(self.cross - STATE_LAYER_SIZE) / 2 if not self.vertical else (self.THUMB - STATE_LAYER_SIZE) / 2,
                                         width=STATE_LAYER_SIZE, height=STATE_LAYER_SIZE, corner_radius=STATE_LAYER_SIZE / 2, hit_testable=False,
                                         a11y_hidden=True)
            node.add_child(surface)
            for part in (handle, node, bubble):
                self.node.add_child(part)
            thumb = SimpleNamespace(node=node, surface=surface, handle=handle, bubble=bubble, bubble_text=bubble_text, interaction=None)
            thumb.interaction = Interaction(self.window, node, self._tint(), self._listen, self.color("secondary"), surface=surface)
            self.thumbs.append(thumb)
            self._undo.append(self._listen(node, "focus", lambda e, i=i: self._show_bubble_for(i, bool(getattr(e, "focus_visible", True)))))
            self._undo.append(self._listen(node, "unfocus", lambda e, i=i: self._show_bubble_for(i, False)))
        self.handle, self.handle_high = self.thumbs[0].handle, self.thumbs[1].handle  # the two handles, by their old and their new names
        self._place_start()

    def _handle_label(self, i: int) -> str:
        name = ("minimum", "maximum")[i]
        return f"{self._label}, {name}" if self._label else name.capitalize()

    def relabel(self, label: Optional[str]) -> None:
        """Names the handles from the group's new `label`."""
        if label != self._label:
            self._label = label
            for i, thumb in enumerate(self.thumbs):
                a11y.describe(thumb.node, label=self._handle_label(i))

    def _place_start(self) -> None:
        mid = self.cross / 2
        for thumb in self.thumbs:
            self._place(thumb.handle, 0.0, self._hl, mid - self._across / 2, self._across)
            self._place(thumb.bubble, self._edge - 14.0, 28.0, mid - self._across / 2 - 8.0 - 28.0, 28.0)
            self._place(thumb.node, self._edge - self.THUMB / 2, self.THUMB, 0.0, self.cross)

    def _tint(self) -> RGBA:
        return self._on_colour()

    def _render(self) -> None:
        disabled = self.disabled.get()
        self.node.set(focusable=False, disabled=disabled, cursor="default" if disabled else "pointer")  # the group is not a stop; its handles are
        self.interaction.enabled = False  # the group itself shows no feedback: each handle does
        for thumb in self.thumbs:
            thumb.node.set(focusable=not disabled, disabled=disabled, cursor="default" if disabled else "pointer")
            thumb.interaction.enabled = not disabled
        self._paint(animate=self._painted)
        for thumb in self.thumbs:
            thumb.interaction.retint(self._tint(), self.color("secondary"))
        self._painted = True

    def set_theme(self, theme: Theme) -> None:
        super().set_theme(theme)
        for thumb in self.thumbs:
            thumb.interaction.retint(self._tint(), self.color("secondary"))

    def dispose(self) -> None:
        for thumb in getattr(self, "thumbs", ()):
            thumb.interaction.detach()
        super().dispose()

    # -- painting --------------------------------------------------------------------------------------------------------------

    def _paint(self, animate: bool) -> None:
        self._fit_length()
        low, high = self._pair()
        disabled = self.disabled.get()
        on_surface = self.color("on_surface")
        if disabled:
            active = handle = with_alpha(on_surface, DISABLED_CONTENT)
            inactive = with_alpha(on_surface, DISABLED_CONTAINER)
        else:
            active = handle = self._on_colour()
            inactive = self.color("surface_container_highest")
        ms = self._ms(animate, "short3")
        for piece, colour in ((self.active, active), (self.inactive, inactive), (self.inactive_high, inactive)):
            self._to(piece, "fill", colour, ms)
        fractions = self._fractions()
        offsets = [f * self._span for f in fractions]
        mid, thick, hl = self.cross / 2, self._thick, self._hl
        centres = [self._edge + o for o in offsets]
        if self.size:  # three pieces of track, each a gap from a handle
            low_end = _max(centres[0] - hl / 2 - self.GAP, 0.0)
            active_start, active_end = centres[0] + hl / 2 + self.GAP, centres[1] - hl / 2 - self.GAP
            high_start = centres[1] + hl / 2 + self.GAP
            self._place(self.inactive, 0.0, low_end, mid - thick / 2, thick)
            self._place(self.active, active_start, _max(active_end - active_start, 0.0), mid - thick / 2, thick)
            self._place(self.inactive_high, high_start, _max(self.length - high_start, 0.0), mid - thick / 2, thick)
        else:  # the full track lies under, and the active part is drawn between the two handle centres
            self._place(self.active, centres[0], offsets[1] - offsets[0], mid - thick / 2, thick)
        for i, thumb in enumerate(self.thumbs):
            value = (low, high)[i]
            lo, hi = self._bounds(i)
            thumb.node.set(value=value, value_min=lo, value_max=hi, value_step=self._key_step())
            self._to(thumb.handle, "fill", handle, ms)
            self._slide(thumb.handle, offsets[i])
            self._slide(thumb.node, offsets[i])
            thumb.bubble.set(fill=self.color("inverse_surface"))
            thumb.bubble_text.set(text=f"{value:g}", fill=self.color("inverse_on_surface"))
            self._slide(thumb.bubble, offsets[i])
        if self.icon is not None:
            self.icon.set(fill=with_alpha(on_surface, DISABLED_CONTENT) if disabled else self.color("on_surface_variant"))
        count = len(self.tick_marks) - 1
        for i, mark in enumerate(self.tick_marks):  # a mark between the handles is the on-colour, outside them the variant
            inside = count > 0 and fractions[0] - 1e-9 <= i / count <= fractions[1] + 1e-9
            mark.set(fill=self.color("on_primary") if inside and not disabled else self.color("on_surface_variant"))

    def _show_bubble_for(self, i: int, shown: bool) -> None:
        self._shown_for[i] = shown
        self.thumbs[i].bubble.set(visible=self.value_indicator and (shown or self._drag == i))

    # -- the pointer -----------------------------------------------------------------------------------------------------------

    def _nearer(self, along: float) -> int:
        """The handle nearer a press `along` the track; on a tie the one on the press's side."""
        centres = [self._edge + f * self._span for f in self._fractions()]
        near_low, near_high = abs(along - centres[0]), abs(along - centres[1])
        if near_low == near_high:
            return 0 if along < centres[0] else 1
        return 0 if near_low < near_high else 1

    def _on_down(self, event: Any) -> None:
        along = self._at(event)
        if self.disabled.get() or along is None:
            return
        self._drag = self._nearer(along)
        self._began = self._pair()
        self.node.capture_pointer()
        thumb = self.thumbs[self._drag]
        thumb.interaction.set_dragged(True)
        thumb.node.focus()
        self._show_bubble_for(self._drag, self._shown_for[self._drag])
        self._move_to(event)

    def _on_move(self, event: Any) -> None:
        if self._drag is not None and self._at(event) is not None:
            self._move_to(event)

    def _move_to(self, event: Any) -> None:
        before = self._pair()
        self._set_handle(self._drag, self._from_event(event))
        if self._pair() != before:
            self._input()

    def _on_up(self, event: Any) -> None:
        if self._drag is None:
            return
        held, self._drag = self._drag, None
        self.node.release_pointer()
        for thumb in self.thumbs:
            thumb.interaction.release()  # a press that began on a handle's own node was released to the group, which held the pointer
        self.thumbs[held].interaction.set_dragged(False)
        self._show_bubble_for(held, self._shown_for[held])
        if self._pair() != self._began:
            self._changed(self._pair())

    # -- the keys --------------------------------------------------------------------------------------------------------------

    def _on_key_for(self, i: int, event: Any) -> None:
        if self.disabled.get():
            return
        step = self._key_step()
        moves = {"arrow_right": step, "arrow_up": step, "arrow_left": -step, "arrow_down": -step, "page_up": 10 * step, "page_down": -10 * step}
        lo, hi = self._bounds(i)
        if event.key in moves:
            self._user_set(i, self._pair()[i] + moves[event.key])
        elif event.key == "home":
            self._user_set(i, lo)
        elif event.key == "end":
            self._user_set(i, hi)


class SpinBox:
    """A number field between − and + buttons, as `tre`'s spin box was
    (MD3 has no spin box of its own, so it's built from MD3's parts: two
    40 px icon buttons and a filled field).

    `value` (a `Signal`) steps by `step` with the buttons, the up and down
    arrows in the field, and assistive technology's increment/decrement;
    typing a number sets it once it parses and fits `min`..`max`, and
    leaving the field puts back the value's text if what was typed didn't.
    A button whose step would pass a bound is disabled, unless `wrap` is
    on (a step past one bound lands on the other). Holding a button
    repeats the step after `HOLD` milliseconds, every `REPEAT`; Page Up and
    Page Down step by ten. `decimals` fixes
    how many places show, and `prefix` and `suffix` (a unit, a currency
    sign) are shown with the number and accepted, or not, when it is typed.
    `on_change` hears the user's changes. Not a `Control`: it's three
    targets, not one."""

    BUTTON = 40.0
    FIELD = (64.0, 40.0)
    #: how long a held button waits before it repeats, and how often it then steps (milliseconds)
    HOLD, REPEAT = 400.0, 80.0

    def __init__(self, window: Any, *, value: float = 0, min: Optional[float] = None, max: Optional[float] = None,
                 step: float = 1, theme: Optional[Theme] = None, label: Optional[str] = None,
                 disabled: bool = False, listen: Optional[Listen] = None, decimals: Optional[int] = None,
                 prefix: str = "", suffix: str = "", wrap: bool = False) -> None:
        if step <= 0:
            raise ValueError(f"a spin box's step must be positive, got {step!r}")
        if min is not None and max is not None and max < min:
            raise ValueError(f"a spin box needs max >= min, got min={min!r}, max={max!r}")
        self.window = window
        self.theme = initial_theme(window, theme, self)  # the app's, followed, without one (M50)
        self.min, self.max, self.step = min, max, step
        self.decimals, self.prefix, self.suffix, self.wrap = decimals, prefix, suffix, bool(wrap)
        self._holds: dict[int, Any] = {}  # direction -> the running timer of a held button
        self._repeated = False  # a hold stepped: the click that ends it must not step again
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
        """Calls `fn(value)` after each change the user makes. Returns the function that stops it."""
        self._changes.append(fn)
        return lambda: self._changes.remove(fn) if fn in self._changes else None

    def color(self, role: str) -> RGBA:
        """A colour role of this control's theme, or MD3's baseline."""
        return self.theme.role(role) or tokens.BASELINE[role]

    def set_theme(self, theme: Theme) -> None:
        """Re-tints the spin box for `theme`, at once."""
        self.theme = theme
        for it in (self._dec_it, self._inc_it):
            it.retint(self.color("on_surface_variant"), self.color("secondary"))
        untrack(self._paint)

    def dispose(self) -> None:
        """Stops the spin box (its repainting and listeners) but leaves its
        nodes, for a caller about to free the tree it sits in -- as a view
        does with its controls."""
        unfollow(self.window, self)
        self._effect.dispose()
        for undo in self._undo:
            undo()
        self._undo = []
        for it in (self._dec_it, self._inc_it):
            it.detach()

    def destroy(self) -> None:
        """Stops the spin box and frees its nodes."""
        self.dispose()
        self.node.destroy()

    # -- internals -----------------------------------------------------------------

    def _button(self, icon: str, label: str, direction: int) -> tuple[Any, Any, Interaction]:
        button = self.window.create("box", width=self.BUTTON, height=self.BUTTON, corner_radius=self.BUTTON / 2,
                                    align_items="center", justify_content="center", focusable=True,
                                    role="button", label=label, cursor="pointer")
        glyph = self.window.create("path", data=icon_path(icon), view_box=icon_view_box(icon), width=24.0, height=24.0,
                                   hit_testable=False, a11y_hidden=True)
        button.add_child(glyph)
        it = Interaction(self.window, button, self.color("on_surface_variant"), self._listen, self.color("secondary"))
        self._undo.append(self._listen(button, "click", handled(lambda e: self._clicked(direction))))
        self._undo.append(self._listen(button, "pointer_down", lambda e: self._hold(direction)))
        for event in ("pointer_up", "pointer_cancel", "pointer_leave", "touch_end", "touch_cancel"):
            self._undo.append(self._listen(button, event, lambda e: self._release()))
        return button, glyph, it

    def _clicked(self, direction: int) -> None:
        if self._repeated:  # the press was a hold that has already stepped: the release is not another step
            self._repeated = False
            return
        self._bump(direction)

    def _hold(self, direction: int) -> None:
        """A button held down steps again, after `HOLD` ms and then every `REPEAT` ms, until it is let go or cannot step."""
        self._release()
        self._repeated = False

        def start() -> None:
            def step() -> None:
                if not self._can(direction):
                    self._release()
                    return
                self._repeated = True
                self._bump(direction)

            self._holds[direction] = self.window.every(self.REPEAT, step)
            step()

        self._holds[direction] = self.window.after(self.HOLD, start)

    def _release(self) -> None:
        for timer in self._holds.values():
            timer.cancel()
        self._holds.clear()

    def _fit(self, value: float) -> float:
        """`value` held within `min`..`max`."""
        if self.min is not None and value < self.min:
            value = self.min
        if self.max is not None and value > self.max:
            value = self.max
        return value

    def _format(self, value: float) -> str:
        if self.decimals is not None:
            body = f"{value:.{self.decimals}f}"
        else:
            whole = all(isinstance(n, int) or float(n).is_integer() for n in (value, self.step))
            body = str(int(value)) if whole else f"{value:g}"
        return f"{self.prefix}{body}{self.suffix}"

    def _can(self, direction: int) -> bool:
        if self.disabled.get():
            return False
        if self.wrap and self.min is not None and self.max is not None:
            return True
        bound = self.max if direction > 0 else self.min
        return bound is None or (self.value.get() + direction * self.step) * direction <= bound * direction

    def _bump(self, direction: int, times: int = 1) -> None:
        if not self._can(direction):
            return
        target = self.value.get() + direction * self.step * times
        if self.wrap and self.min is not None and self.max is not None:
            if target > self.max:
                target = self.min
            elif target < self.min:
                target = self.max
        self._user_set(target)

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
        text = text.strip()
        if self.prefix and text.startswith(self.prefix.strip()):
            text = text[len(self.prefix.strip()):]
        if self.suffix and text.endswith(self.suffix.strip()):
            text = text[:-len(self.suffix.strip())]
        try:
            number = float(text.strip())
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
        key = str(event.key).lower()
        if key == "arrow_up":
            self._bump(1)
        elif key == "arrow_down":
            self._bump(-1)
        elif key == "page_up":
            self._bump(1, 10)
        elif key == "page_down":
            self._bump(-1, 10)


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


class Indicator:
    """The shared part of the progress and loading indicators: a node with
    `role="progressbar"` that isn't focusable or interactive. `value` is
    a `Signal`, 0..1, or `None` for indeterminate (animated forever until
    it gets a value). Colours are theme roles; `color` replaces `primary`."""

    def __init__(self, window: Any, *, value: Optional[float] = None, theme: Optional[Theme] = None,
                 label: Optional[str] = None, color: Optional[RGBA] = None, track: Optional[str] = None) -> None:
        self.window = window
        self.track = track  # the colour role of the track behind the indicator; each kind has its own when this is None
        self.theme = initial_theme(window, theme, self)  # the app's, followed, without one (M50)
        self.value = Signal(value)
        self._color = color
        self._painted = False
        self._generation = 0  # bumped to stop a running loop
        self._looping = False
        self.node = self._build()
        a11y.describe(self.node, role="progressbar", value_min=0.0, value_max=1.0)
        if label is not None:
            a11y.describe(self.node, label=label)
        self._effect = Effect(self._render)

    def color(self, role: str) -> RGBA:
        return self.theme.role(role) or tokens.BASELINE[role]

    def _on_colour(self) -> RGBA:
        return self._color or self.color("primary")

    def set_theme(self, theme: Theme) -> None:
        self.theme = theme
        untrack(lambda: self._paint(animate=False))

    def dispose(self) -> None:
        """Stops the indicator's repainting and loop but leaves its node."""
        unfollow(self.window, self)
        self._effect.dispose()
        self._generation += 1

    def destroy(self) -> None:
        self.dispose()
        self.node.destroy()

    @property
    def indeterminate(self) -> bool:
        return self.value.get() is None

    def _render(self) -> None:
        value = self.value.get()
        if value is not None:
            value = _clamp(float(value), 0.0, 1.0)
        self.node.set(value=value)
        # a screen reader hears a wait with no end as busy, and a value as a percentage (states tre may not have yet are skipped)
        a11y.apply_extras(self.node, {"busy": value is None, "value_text": None if value is None else f"{round(value * 100)}%"})
        self._paint(animate=self._painted)
        if value is None and not self._looping:
            self._looping = True
            self._generation += 1
            untrack(lambda: self._loop(self._generation))
        elif value is not None and self._looping:
            self._looping = False
            self._generation += 1
            untrack(self._settle)
        self._painted = True

    def _alive(self, generation: int) -> bool:
        return generation == self._generation

    # subclasses
    def _build(self) -> Any:
        raise NotImplementedError

    def _paint(self, animate: bool) -> None:
        raise NotImplementedError

    def _loop(self, generation: int) -> None:
        raise NotImplementedError

    def _settle(self) -> None:
        """Leaves the indeterminate animation for the determinate look."""


class LinearProgress(Indicator):
    """MD3's linear progress indicator: a 4 px `surface_container_highest`
    track and a `primary` bar. Determinate, the bar fills to the value
    (sliding in over `medium1`); indeterminate, a bar 40% of the width
    sweeps across again and again (MD3's two-bar sweep, simplified to one).

    `two_bar` is the sweep MD3 draws: a long bar and, a little behind it, a
    shorter one, each crossing the track again and again. The widths are
    fixed (the engine cannot animate a width), so it is an approximation of
    MD3's, whose bars grow and shrink as they go. `thickness` is the bar's
    height (MD3 Expressive's thicker ones).

    `wavy` draws the bar (or bars) as a sine wave that flows along the
    track, which stays straight beneath it (MD3 Expressive's wavy
    indicator): the control is `thickness` plus twice the wave's amplitude
    tall. The amplitude, wavelength and speed are written from memory of
    the spec and have not been checked against it (#249)."""

    HEIGHT = 4.0
    SWEEP_MS = 1500
    SWEEP = 0.4
    STOP = 4.0
    #: the two-bar sweep: each bar's share of the width, how long it takes to cross, and how long after the first it starts
    TWO_BARS = ((0.55, 1900, 0), (0.3, 1900, 650))
    AMPLITUDE = 3.0     # a wavy bar's wave, from the middle to a crest
    WAVELENGTH = 40.0
    FLOW_MS = 1000      # a wave flows one wavelength in this long

    def __init__(self, window: Any, *, width: float = 240.0, stop_indicator: bool = False, buffer: Optional[float] = None,
                 thickness: float = HEIGHT, two_bar: bool = False, wavy: bool = False, **kwargs: Any) -> None:
        if not thickness > 0:
            raise ValueError(f"a progress bar's thickness is above 0, got {thickness!r}")
        self.width = float(width)
        self.thickness = float(thickness)  # MD3 Expressive's thicker bars (4 is the standard one)
        self.two_bar = bool(two_bar)
        self.wavy = bool(wavy)
        self.box = self.thickness + (2 * self.AMPLITUDE if self.wavy else 0.0)  # the control's height: a wavy bar's crests stand clear of the track
        self.waves: list[Any] = []
        self._flowing = False
        self._flow_generation = 0
        self.stop_indicator = bool(stop_indicator)  # MD3's dot at the track's end
        self.buffer = Signal(buffer)  # a second, lighter bar behind the first: how much has loaded, 0..1
        super().__init__(window, **kwargs)

    def _build(self) -> Any:
        box, thick, wavy = self.box, self.thickness, self.wavy
        node = self.window.create("box", width=self.width, height=box, corner_radius=0.0 if wavy else thick / 2, clip_children=True)
        # a wavy bar's track is a straight bar of its own, in the middle
        self.track_line = self.window.create("box", position="absolute", x=0.0, y=(box - thick) / 2, width=self.width, height=thick,
                                             corner_radius=thick / 2, hit_testable=False, a11y_hidden=True, visible=wavy)
        node.add_child(self.track_line)
        self.loaded = self.window.create("box", position="absolute", x=0.0, y=(box - thick) / 2, width=self.width, height=thick,
                                         corner_radius=thick / 2, translate_x=-self.width, hit_testable=False, a11y_hidden=True)
        node.add_child(self.loaded)  # behind the bar
        # the bar is full width, slid left out of the clip by the unfilled part
        self.bar = self._bar(node)
        self.bar2 = self._bar(node, visible=False)  # the second bar of a two-bar sweep
        dot = min(self.STOP, self.thickness)  # a thin bar's dot is no taller than it
        self.stop = self.window.create("box", position="absolute", x=self.width - dot - 0.0, y=(box - dot) / 2,
                                       width=dot, height=dot, corner_radius=dot / 2, hit_testable=False,
                                       a11y_hidden=True, visible=self.stop_indicator)
        node.add_child(self.stop)
        return node

    def _bar(self, node: Any, visible: bool = True) -> Any:
        """A bar: a box that slides, and (wavy) holds the wave that flows inside it, clipped to the bar."""
        bar = self.window.create("box", position="absolute", x=0.0, y=0.0, width=self.width, height=self.box,
                                 corner_radius=0.0 if self.wavy else self.thickness / 2, clip_children=self.wavy, translate_x=-self.width,
                                 hit_testable=False, a11y_hidden=True, visible=visible)
        if self.wavy:
            wave = self.window.create("path", data=self._wave_data(self.width + self.WAVELENGTH), position="absolute", x=0.0, y=0.0,
                                      width=self.width + self.WAVELENGTH, height=self.box, stroke_width=self.thickness, fill=_CLEAR,
                                      hit_testable=False, a11y_hidden=True)
            bar.add_child(wave)
            self.waves.append(wave)
        node.add_child(bar)
        return bar

    def _wave_data(self, length: float) -> str:
        """A sine wave `length` long, a crest every `WAVELENGTH`, along the middle of the control, as a polyline of 16 steps a wavelength."""
        steps = max(int(length / self.WAVELENGTH * 16), 16)
        mid = self.box / 2
        points = [(length * n / steps, mid - self.AMPLITUDE * math.sin(2 * math.pi * (length * n / steps) / self.WAVELENGTH)) for n in range(steps + 1)]
        return "M" + " L".join(f"{x:.2f},{y:.2f}" for x, y in points)

    def _flow(self, generation: int) -> None:
        """The waves flow along their bars, a wavelength at a time (the wave is periodic, so the jump back is not seen)."""
        if generation != self._flow_generation:
            return
        for wave in self.waves:
            wave.stop_animation("translate_x")
            wave.set(translate_x=0.0)
        self.waves[0].animate("translate_x", -self.WAVELENGTH, self.FLOW_MS, easing="linear", on_complete=lambda: self._flow(generation))
        for wave in self.waves[1:]:
            wave.animate("translate_x", -self.WAVELENGTH, self.FLOW_MS, easing="linear")

    def dispose(self) -> None:
        self._flow_generation += 1
        super().dispose()

    def _paint(self, animate: bool) -> None:
        track = self.color(self.track or "surface_container_highest")
        if self.wavy:
            self.track_line.set(fill=track)
            for wave in self.waves:
                wave.set(stroke_color=self._on_colour())
            if not self._flowing and not motion.reduced(self.window):
                self._flowing = True
                self._flow(self._flow_generation)
        else:
            self.node.set(fill=track)
            self.bar.set(fill=self._on_colour())
            self.bar2.set(fill=self._on_colour())
        self.stop.set(fill=self._on_colour())
        self.loaded.set(fill=self._on_colour() if self.buffer.get() is None else self._on_colour()[:3] + (96,), visible=self.buffer.get() is not None)
        if self.buffer.get() is not None:
            self.loaded.set(translate_x=(_clamp(float(self.buffer.get()), 0.0, 1.0) - 1.0) * self.width)
        value = self.value.get()
        if value is not None:
            Control._to(self.bar, "translate_x", (_clamp(float(value), 0.0, 1.0) - 1.0) * self.width,
                        Theme.duration("medium1") if animate else 0, Theme.easing("standard"))

    def _loop(self, generation: int) -> None:
        if not self._alive(generation):
            return
        if motion.reduced(self.window):  # no sweep: a still bar across the middle
            self.bar.set(width=self.SWEEP * self.width, translate_x=(1.0 - self.SWEEP) * self.width / 2)
            return
        if self.two_bar:
            self.bar2.set(visible=True)
            for bar, share, ms, delay in zip((self.bar, self.bar2), *zip(*self.TWO_BARS)):
                self._cross(bar, share, ms, delay, generation)
            return
        self.bar.set(width=self.SWEEP * self.width)
        self.bar.stop_animation("translate_x")
        self.bar.set(translate_x=-self.SWEEP * self.width)
        self.bar.animate("translate_x", self.width, self.SWEEP_MS, easing=Theme.easing("standard"),
                         on_complete=lambda: self._loop(generation))

    def _cross(self, bar: Any, share: float, ms: int, delay: int, generation: int) -> None:
        """One bar of a two-bar sweep, crossing the track again and again, starting `delay` ms from now."""
        width = share * self.width
        bar.stop_animation("translate_x")
        bar.set(width=width, translate_x=-width)  # off the left end until it is its turn

        def go() -> None:
            if not self._alive(generation):
                return
            bar.set(translate_x=-width)
            bar.animate("translate_x", self.width, ms, easing=Theme.easing("standard"), on_complete=go)

        if delay:
            self.window.after(delay, go)
        else:
            go()

    def _settle(self) -> None:
        self.bar2.stop_animation("translate_x")
        self.bar2.set(visible=False, translate_x=-self.width)
        self.bar.set(width=self.width)
        self._paint(animate=False)


class CircularProgress(Indicator):
    """MD3's circular progress indicator: a 4 px `primary` arc in a 48 px
    box. Determinate, the arc runs clockwise from 12 o'clock for the
    value's share of the circle; indeterminate, the arc spins (one turn
    per 1568 ms) while it lengthens and shortens (666 ms each way).

    `thickness` is the arc's width (MD3 Expressive's thicker rings; 4 is the
    standard one): the outer edge of the standard ring stays where it is, so
    a thicker arc has a smaller radius. With a `track`, a determinate arc and the track
    are a gap apart (a 4 px gap between the rounded ends), as in MD3.

    `wavy` draws the arc as a wave around the ring, its crests flowing round
    it (MD3 Expressive's wavy indicator); the track stays a plain circle on
    the wave's middle line, and the crests reach where the plain arc would.
    The wave's size and speed are written from memory of the spec and have
    not been checked against it (#249)."""

    SIZE = 48.0
    STROKE = 4.0
    MARGIN = 2.0  # between the standard ring's outer edge and the box (in the box's own 48 units)
    GAP = 4.0     # between the arc and the track
    TURN_MS = 1568
    ARC_MS = 666
    WAVES = 10          # crests round a wavy ring
    AMPLITUDE = 1.5     # a wavy ring's wave, from the middle to a crest, in pixels of a 48 px ring
    FLOW_MS = 1200      # a wave flows one wavelength round in this long
    TICK_MS = 33        # how often the wave moves

    def __init__(self, window: Any, *, size: float = SIZE, thickness: float = STROKE, wavy: bool = False, **kwargs: Any) -> None:
        if not thickness > 0 or thickness > size / 2 - self.MARGIN:
            raise ValueError(f"a progress ring's thickness is above 0 and fits the ring, got {thickness!r} in {size!r}")
        self.size = float(size)
        self.thickness = float(thickness)
        self.wavy = bool(wavy)
        self._phase = 0.0
        self._ticker: Any = None
        super().__init__(window, **kwargs)

    @property
    def radius(self) -> float:
        """The ring's radius in view-box units (the box is 48 across however large the node is; the stroke is in pixels)."""
        k = self.SIZE / self.size  # pixels to view-box units: the stroke is in pixels, the path in the box's
        return (self.SIZE / 2 - self.MARGIN - self.STROKE / 2) + (self.STROKE - self.thickness) * k / 2  # the standard ring's outer edge, kept

    @property
    def _amplitude(self) -> float:
        """A wavy ring's amplitude in view-box units."""
        return self.AMPLITUDE * self.SIZE / self.size if self.wavy else 0.0

    @property
    def _middle(self) -> float:
        """The radius of the ring's middle line: the plain radius, or (wavy) a crest's less."""
        return self.radius - self._amplitude

    @property
    def circle(self) -> str:
        """The ring: clockwise from the top (the track's, and a plain arc's)."""
        c, r = self.SIZE / 2, self._middle
        return f"M{c:g},{c - r:g} A{r:g},{r:g} 0 1,1 {c:g},{c + r:g} A{r:g},{r:g} 0 1,1 {c:g},{c - r:g}"

    def wave(self, phase: float) -> str:
        """The wavy arc's ring for a phase: a crest `WAVES` times round, as a closed polyline of 12 steps a crest."""
        c, r, a = self.SIZE / 2, self._middle, self._amplitude
        steps = self.WAVES * 12
        points = []
        for n in range(steps + 1):
            theta = 2 * math.pi * n / steps
            radius = r + a * math.sin(self.WAVES * theta + phase)
            points.append(f"{c + radius * math.sin(theta):.3f},{c - radius * math.cos(theta):.3f}")
        return "M" + " L".join(points)

    def _flow(self) -> None:
        """Moves the wave on: one crest round the ring per `FLOW_MS`."""
        self._phase = (self._phase - 2 * math.pi * self.TICK_MS / self.FLOW_MS) % (2 * math.pi)
        self.arc.set(data=self.wave(self._phase))

    def dispose(self) -> None:
        if self._ticker is not None:
            self._ticker.cancel()
            self._ticker = None
        super().dispose()

    @property
    def _gap(self) -> float:
        """The gap as a share of the ring's length: the 4 px between the rounded ends, plus the two caps."""
        px = self._middle * self.size / self.SIZE  # the middle line's radius in pixels
        return (self.GAP + self.thickness) / (2 * math.pi * px)

    def _build(self) -> Any:
        node = self.window.create("box", width=self.size, height=self.size)
        self.ring = self.window.create("path", data=self.circle, view_box=(0, 0, self.SIZE, self.SIZE), width=self.size, height=self.size,
                                       stroke_width=self.thickness, fill=_CLEAR, trim_start=0.0, trim_end=1.0, hit_testable=False, a11y_hidden=True,
                                       visible=self.track is not None)  # the track, when there is one: the whole circle behind the arc
        node.add_child(self.ring)
        self.arc = self.window.create("path", data=self.wave(0.0) if self.wavy else self.circle, view_box=(0, 0, self.SIZE, self.SIZE),
                                      width=self.size, height=self.size, stroke_width=self.thickness, fill=_CLEAR,
                                      trim_start=0.0, trim_end=0.0, hit_testable=False, a11y_hidden=True)
        node.add_child(self.arc)
        return node

    def _paint(self, animate: bool) -> None:
        self.arc.set(stroke_color=self._on_colour())
        if self.wavy and self._ticker is None and not motion.reduced(self.window):
            self._ticker = self.window.every(self.TICK_MS, self._flow)
        if self.track is not None:
            self.ring.set(stroke_color=self.color(self.track))
        value = self.value.get()
        if value is not None:
            share = _clamp(float(value), 0.0, 1.0)
            ms, easing = Theme.duration("medium1") if animate else 0, Theme.easing("standard")
            Control._to(self.arc, "trim_end", share, ms, easing)
            if self.track is not None:  # the track starts a gap after the arc and stops a gap before the top again
                gap = self._gap
                start, end = (share + gap, 1.0 - gap) if 0.0 < share < 1.0 else (1.0, 1.0) if share >= 1.0 else (0.0, 1.0)
                Control._to(self.ring, "trim_start", _min(start, end), ms, easing)
                Control._to(self.ring, "trim_end", end, ms, easing)

    def _loop(self, generation: int) -> None:
        if motion.reduced(self.window):  # no spinning: a still arc
            self.arc.set(rotation_deg=0.0, trim_end=0.75)
            return
        self.ring.set(trim_start=0.0, trim_end=1.0)  # a wait has no share to leave a gap after
        self._spin(generation)
        self._stretch(generation, longer=True)

    def _spin(self, generation: int) -> None:
        if not self._alive(generation):
            return
        self.arc.stop_animation("rotation_deg")
        self.arc.set(rotation_deg=0.0)
        self.arc.animate("rotation_deg", 360.0, self.TURN_MS, on_complete=lambda: self._spin(generation))

    def _stretch(self, generation: int, longer: bool) -> None:
        if not self._alive(generation):
            return
        self.arc.animate("trim_end", 0.75 if longer else 0.1, self.ARC_MS, easing=Theme.easing("standard"),
                         on_complete=lambda: self._stretch(generation, not longer))

    def _settle(self) -> None:
        for prop in ("rotation_deg", "trim_end"):
            self.arc.stop_animation(prop)
        self.arc.set(rotation_deg=0.0, trim_start=0.0)
        self._paint(animate=False)


class LoadingIndicator(Indicator):
    """MD3's loading indicator: a filled `primary` shape, 38 px in a 48 px
    box, morphing forever through a pentagon, a pill, a cookie and an oval,
    650 ms per step, linear. These are the outlines `tre`'s MD3 handover
    defines (its `intended` pill and oval, not the diamonds `tre` drew).
    Always indeterminate; `value` is ignored. `contained` puts the shape in
    a `primary_container` circle the size of the box, the shape then in
    `on_primary_container` (MD3 Expressive's contained loading indicator);
    `color` still replaces the shape's colour."""

    SIZE = 48.0
    SHAPE = 38.0
    STEP_MS = 650
    SHAPES = (
        "M24.00,0.00L46.83,16.58L38.11,43.42L9.89,43.42L1.17,16.58Z",
        "M0.00,24.00C0.00,10.75 10.75,0.00 24.00,0.00L24.00,0.00C37.25,0.00 48.00,10.75 48.00,24.00L48.00,24.00"
        "C48.00,37.25 37.25,48.00 24.00,48.00L24.00,48.00C10.75,48.00 0.00,37.25 0.00,24.00Z",
        "M24.00,0.00L33.84,6.96L44.78,12.00L43.68,24.00L44.78,36.00L33.84,41.04L24.00,48.00L14.16,41.04L3.22,36.00"
        "L4.32,24.00L3.22,12.00L14.16,6.96Z",
        "M48.00,24.00C48.00,30.63 37.25,36.00 24.00,36.00C10.75,36.00 0.00,30.63 0.00,24.00C0.00,17.37 10.75,12.00 "
        "24.00,12.00C37.25,12.00 48.00,17.37 48.00,24.00",
    )

    def __init__(self, window: Any, *, size: float = SIZE, contained: bool = False, **kwargs: Any) -> None:
        kwargs["value"] = None
        self._step = 0
        self.size = float(size)
        self.contained = bool(contained)
        super().__init__(window, **kwargs)

    def _build(self) -> Any:
        node = self.window.create("box", width=self.size, height=self.size, align_items="center",
                                  justify_content="center", corner_radius=self.size / 2)
        shape = self.size * self.SHAPE / self.SIZE  # MD3: 38 of 48
        self.shape = self.window.create("path", data=self.SHAPES[0], view_box=(0, 0, 48, 48), width=shape,
                                        height=shape, hit_testable=False, a11y_hidden=True)
        node.add_child(self.shape)
        return node

    def _paint(self, animate: bool) -> None:
        if self.contained:
            self.node.set(fill=self.color("primary_container"))
            self.shape.set(fill=self._color or self.color("on_primary_container"))
        else:
            self.shape.set(fill=self._on_colour())

    def _loop(self, generation: int) -> None:
        if not self._alive(generation):
            return
        if motion.reduced(self.window):  # no morphing: the first shape, still
            return
        self._step = (self._step + 1) % len(self.SHAPES)
        self.shape.animate("data", self.SHAPES[self._step], self.STEP_MS, on_complete=lambda: self._loop(generation))


class TimePickerDial(Control):
    """MD3's time picker dial: a 256 px `surface_container_highest` face
    with the twelve hours (or the minutes, in fives) around it, a `primary`
    hand from the centre to a 48 px `primary` selector, which shows its
    number in `on_primary`.

    `hour` (0..23) and `minute` (0..59) are `Signal`s, and `mode` is
    `"hour"` or `"minute"`: which hand the dial shows and sets. Pressing or
    dragging on the face points the hand; the hour snaps to twelve
    positions and keeps its AM/PM half, the minute snaps to fives. Letting
    go in hour mode moves on to minutes, as MD3's picker does (unless
    `auto_advance=False`). The arrow keys and assistive technology's
    increment/decrement step the hour by one or the minute by five.
    `on_change` gets `(hour, minute)`."""

    role = "slider"
    SELECTOR = 48.0

    def __init__(self, window: Any, *, hour: int = 0, minute: int = 0, mode: str = "hour",
                 auto_advance: bool = True, size: float = 256.0, **kwargs: Any) -> None:
        if mode not in ("hour", "minute"):
            raise ValueError(f"a time picker dial's mode is 'hour' or 'minute', got {mode!r}")
        self.SIZE = float(size)
        # the numbers' circle: the selector sits just inside the face's edge
        self.RADIUS = self.SIZE / 2 - self.SELECTOR / 2 - 4.0
        kwargs["size"] = self.SIZE
        self.hour = Signal(int(hour) % 24)
        self.minute = Signal(int(minute) % 60)
        self.mode = Signal(mode)
        self.auto_advance = auto_advance
        self._mode_listeners: list[Callable[[str], None]] = []
        self._dragging = False
        self._start: tuple[int, int] = (0, 0)
        super().__init__(window, **kwargs)
        for event, handler in (("pointer_down", self._on_down), ("pointer_move", self._on_move),
                               ("pointer_up", self._on_up), ("pointer_cancel", self._on_up),
                               ("key_down", self._on_key)):
            self._undo.append(self._listen(self.node, event, handler))
        self._undo.append(a11y.on_action(self.node, {"increment": lambda e: self._step(1),
                                                    "decrement": lambda e: self._step(-1)}, listen=self._listen))

    # -- geometry ----------------------------------------------------------------

    def _angle(self) -> float:
        """The active hand's angle, in degrees clockwise from 12 o'clock."""
        if self.mode.get() == "hour":
            return (self.hour.get() % 12) * 30.0
        return self.minute.get() * 6.0

    def _tip(self, degrees: float) -> tuple[float, float]:
        rad = math.radians(degrees)
        centre = self.SIZE / 2
        return centre + self.RADIUS * math.sin(rad), centre - self.RADIUS * math.cos(rad)

    def _build(self) -> None:
        centre = self.SIZE / 2
        self.face = self.window.create("box", position="absolute", x=0.0, y=0.0, width=self.SIZE, height=self.SIZE,
                                       corner_radius=centre, hit_testable=False, a11y_hidden=True)
        self.hand = self.window.create("path", position="absolute", x=0.0, y=0.0, width=self.SIZE, height=self.SIZE,
                                       view_box=(0, 0, self.SIZE, self.SIZE), data=f"M{centre},{centre} L{centre},0",
                                       stroke_width=2.0, fill=_CLEAR, hit_testable=False, a11y_hidden=True)
        half = self.SELECTOR / 2
        self.selector = self.window.create("box", position="absolute", x=centre - half, y=centre - half,
                                           width=self.SELECTOR, height=self.SELECTOR, corner_radius=half,
                                           hit_testable=False, a11y_hidden=True)
        self.hub = self.window.create("box", position="absolute", x=centre - 4, y=centre - 4, width=8.0, height=8.0,
                                      corner_radius=4.0, hit_testable=False, a11y_hidden=True)
        self.numbers = []
        for i in range(12):
            x, y = self._tip(i * 30.0)
            number = self.window.create("text", text="", position="absolute", x=x - half, y=y - 12.0,
                                        width=self.SELECTOR, height=24.0, font_family="Roboto", font_size=16.0,
                                        text_align="center", hit_testable=False, a11y_hidden=True)
            self.numbers.append(number)
        for child in (self.face, self.hand, self.selector, self.hub, *self.numbers):
            self.node.add_child(child)
        # the state layer rides on the selector
        self.surface.set(width=self.SELECTOR, height=self.SELECTOR, corner_radius=half,
                         x=centre - half, y=centre - half)

    def _ring_around(self) -> Any:
        return self.face

    def _tint(self) -> RGBA:
        return self.color("primary")

    # -- painting ------------------------------------------------------------------

    def _paint(self, animate: bool) -> None:
        hour, minute, mode, disabled = self.hour.get(), self.minute.get(), self.mode.get(), self.disabled.get()
        maximum = 23 if mode == "hour" else 59
        self.node.set(value=float(hour if mode == "hour" else minute), value_min=0.0, value_max=float(maximum),
                      value_step=1.0 if mode == "hour" else 5.0)
        on_surface = self.color("on_surface")
        accent = with_alpha(on_surface, DISABLED_CONTENT) if disabled else self.color("primary")
        self.face.set(fill=with_alpha(on_surface, DISABLED_CONTAINER) if disabled
                      else self.color("surface_container_highest"))
        self.hand.set(stroke_color=accent)
        self.selector.set(fill=accent)
        self.hub.set(fill=accent)
        chosen = (hour % 12) if mode == "hour" else (minute // 5 if minute % 5 == 0 else None)
        for i, number in enumerate(self.numbers):
            label = str(12 if i == 0 else i) if mode == "hour" else f"{i * 5:02d}"
            ink = self.color("on_primary") if i == chosen and not disabled else (
                with_alpha(on_surface, DISABLED_CONTENT) if disabled else on_surface)
            number.set(text=label, fill=ink)
        x, y = self._tip(self._angle())
        centre = self.SIZE / 2
        ms = self._ms(animate and not self._dragging, "medium1")
        easing = Theme.easing("emphasized_decelerate")
        data = f"M{centre},{centre} L{x:.3f},{y:.3f}"
        if ms:
            self.hand.animate("data", data, ms, easing=easing)
        else:
            self.hand.stop_animation("data")
            self.hand.set(data=data)
        for node in (self.selector, self.surface):
            self._to(node, "translate_x", x - centre, ms, easing)
            self._to(node, "translate_y", y - centre, ms, easing)

    # -- input -----------------------------------------------------------------------

    def _activate(self) -> None:
        pass  # a press has already pointed the hand

    def _point(self, x: float, y: float) -> None:
        centre = self.SIZE / 2
        degrees = math.degrees(math.atan2(x - centre, centre - y)) % 360.0
        if self.mode.get() == "hour":
            position = math.floor(degrees / 30.0 + 0.5) % 12
            self.hour.set(position + (12 if self.hour.get() >= 12 else 0))
        else:
            self.minute.set((math.floor(degrees / 30.0 + 0.5) % 12) * 5)

    def _on_down(self, event: Any) -> None:
        if self.disabled.get() or event.x is None:
            return
        self._dragging = True
        self._start = (self.hour.get(), self.minute.get())
        self.node.capture_pointer()
        self.interaction.set_dragged(True)
        self._point(event.x, event.y)

    def _on_move(self, event: Any) -> None:
        if self._dragging and event.x is not None:
            self._point(event.x, event.y)

    def _on_up(self, event: Any) -> None:
        if not self._dragging:
            return
        self._dragging = False
        self.node.release_pointer()
        self.interaction.set_dragged(False)
        untrack(lambda: self._paint(animate=False))
        if (self.hour.get(), self.minute.get()) != self._start:
            self._changed((self.hour.get(), self.minute.get()))
        if self.mode.get() == "hour" and self.auto_advance:
            self.mode.set("minute")
            for fn in list(self._mode_listeners):
                fn("minute")

    def on_mode(self, fn: Callable[[str], None]) -> Callable[[], None]:
        """Calls `fn(mode)` when the dial moves itself on from the hour to the minutes after the user lets go. Returns the function that stops it."""
        self._mode_listeners.append(fn)
        return lambda: self._mode_listeners.remove(fn) if fn in self._mode_listeners else None

    def _step(self, by: int) -> None:
        if self.disabled.get():
            return
        before = (self.hour.get(), self.minute.get())
        if self.mode.get() == "hour":
            half = 12 if self.hour.get() >= 12 else 0
            self.hour.set(half + (self.hour.get() % 12 + by) % 12)
        else:
            self.minute.set((self.minute.get() // 5 * 5 + 5 * by) % 60)
        if (self.hour.get(), self.minute.get()) != before:
            self._changed((self.hour.get(), self.minute.get()))

    def _on_key(self, event: Any) -> None:
        step = {"arrow_right": 1, "arrow_up": 1, "arrow_left": -1, "arrow_down": -1}.get(event.key)
        if step is not None:
            self._step(step)
