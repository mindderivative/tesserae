"""Tesserae's own namespace for the Date & Time Pickers category --
`date_picker_day`, `time_picker_dial`, `period_selector`. Same
thin-delegate shape as the other widget modules. None of these 3 expose
an ambiguous color kwarg. Named `date_time.py` (not `datetime.py`) to
avoid shadowing the standard library module.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from tre import Node, Window


def date_picker_day(
    window: "Window",
    day: int,
    selected: bool = False,
    today: bool = False,
    outside_month: bool = False,
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
) -> "Node":
    """One real calendar cell; the app arranges a grid of them."""
    return window.add_date_picker_day(
        day,
        selected=selected,
        today=today,
        outside_month=outside_month,
        x=x,
        y=y,
        border_color=border_color,
        border_width=border_width,
    )


def time_picker_dial(
    window: "Window",
    hour: int = 0,
    minute: int = 0,
    size: float = 256.0,
    x: float | None = None,
    y: float | None = None,
    **kwargs: Any,
) -> "controls.TimePickerDial":
    """MD3's time picker dial (a Tesserae control since M40): `.hour`,
    `.minute` and `.mode` are `Signal`s."""
    from tesserae import controls
    from tesserae.widgets._controls import place

    return place(window, controls.TimePickerDial(window, hour=hour, minute=minute, size=size, **kwargs), x, y)


def period_selector(
    window: "Window",
    selected: str = "AM",
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
) -> tuple["Node", "Node"]:
    """The AM/PM toggle pairing with `time_picker_dial`. Returns
    `(am_button, pm_button)`. Raises `ValueError` if `selected` isn't
    `"AM"` or `"PM"`."""
    return window.add_period_selector(
        selected=selected, x=x, y=y, border_color=border_color, border_width=border_width
    )
