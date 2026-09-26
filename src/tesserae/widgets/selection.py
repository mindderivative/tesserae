"""Tesserae's own namespace for the Selection & Input category --
`checkbox`, `slider`, `radio_button`, `switch`, `spin_box`.

Since M40 each returns a Tesserae control (`tesserae.controls`), not a
bare `tre.Node` (the one break M34 wrote down, P6): `.node` is its node,
already attached to the window's root, and its state is a `Signal`
(`checkbox(...).checked`). Each takes `theme=` (a `tesserae.Theme`;
MD3's baseline colours without one) and `label=`. `background` is the
selected colour, as before.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from tesserae import controls
from tesserae.widgets._controls import place

if TYPE_CHECKING:
    from tre import Window


def checkbox(
    window: "Window",
    background: tuple[int, int, int, int],
    width: float,
    height: float,
    checked: bool = False,
    x: float | None = None,
    y: float | None = None,
    **kwargs: Any,
) -> controls.Checkbox:
    """MD3's checkbox, `width`×`height` its touch target. A click, Space or
    Enter toggles it; `.checked` is its state."""
    return place(window, controls.Checkbox(window, checked=checked, color=background, width=width, height=height,
                                           **kwargs), x, y)


def slider(
    window: "Window",
    background: tuple[int, int, int, int],
    width: float,
    height: float,
    value: float = 0.0,
    x: float | None = None,
    y: float | None = None,
    **kwargs: Any,
) -> controls.Slider:
    """MD3's slider; `value` in 0.0..=1.0 unless `min=`/`max=` say
    otherwise. Dragging and the arrow keys set `.value`."""
    return place(window, controls.Slider(window, value=value, color=background, width=width, height=height,
                                         **kwargs), x, y)


def radio_button(
    window: "Window",
    size: float = 48.0,
    selected: bool = False,
    x: float | None = None,
    y: float | None = None,
    group: Optional[controls.RadioGroup] = None,
    **kwargs: Any,
) -> controls.RadioButton:
    """MD3's radio button, `size` its touch target; pass a shared
    `controls.RadioGroup()` as `group=` for buttons that exclude each other."""
    return place(window, controls.RadioButton(window, selected=selected, group=group, size=size, **kwargs), x, y)


def switch(
    window: "Window",
    width: float = 52.0,
    height: float = 48.0,
    selected: bool = False,
    x: float | None = None,
    y: float | None = None,
    **kwargs: Any,
) -> controls.Switch:
    """MD3's switch, `width`×`height` its touch target (the track is MD3's
    52×32); `.selected` is its state."""
    return place(window, controls.Switch(window, selected=selected, width=width, height=height, **kwargs), x, y)


def spin_box(
    window: "Window",
    value: float | str = 0,
    x: float | None = None,
    y: float | None = None,
    **kwargs: Any,
) -> controls.SpinBox:
    """A number field between − and + buttons (`min=`, `max=`, `step=`).
    `value` may be a number or its text, as `tre`'s took."""
    number = float(value) if isinstance(value, str) else value
    if isinstance(number, float) and number.is_integer() and isinstance(kwargs.get("step", 1), int):
        number = int(number)
    return place(window, controls.SpinBox(window, value=number, **kwargs), x, y)
