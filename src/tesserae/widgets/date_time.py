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
    *,
    on_click: Any = None,
    theme: Any = None,
) -> Any:
    """MD3's date-picker day (M42: built from its fragment): a 48 px
    target holding a 40 px circle with a `body_large` number. Selected,
    the circle is `primary` with `on_primary`; today (unselected) is
    outlined in `primary`; outside the month the number is
    `on_surface_variant`. `.selected`, `.today` and `.outside_month` are
    `Signal`s the app sets; a click or Enter calls `on_click(day)` (the
    grid's selection is the app's). `role="button"`, named by the day."""
    from tesserae import a11y
    from tesserae.reactive import Effect, Signal
    from tesserae.widgets._composed import Widget
    from tesserae.widgets.buttons import _borders

    name = "date_picker_day"
    border = _borders([None], border_color, border_width)

    def edit(spec: dict[str, Any]) -> None:
        label = spec["children"][0]
        spec["children"] = [{"id": f"{name}.indicator", "kind": "Rect",
                             "style": {"width": 40, "height": 40, "corner_radius": 20, "background": "transparent",
                                       "align_items": "center", "justify_content": "center"},
                             "children": [label]}]
        if border is not None:
            border(spec)

    widget = Widget(window, "DatePickerDay", {"day": str(day)}, theme=theme, x=x, y=y, edit=edit, name=name,
                    interactive={"indicator": "on_surface"})
    widget.day = int(day)
    widget.selected, widget.today, widget.outside_month = Signal(bool(selected)), Signal(bool(today)), Signal(
        bool(outside_month))
    a11y.describe(widget.node, label=str(day))
    indicator, label = widget.part("indicator"), widget.part("label")

    def paint() -> None:
        on, now, outside = widget.selected.get(), widget.today.get(), widget.outside_month.get()
        widget.node.set(selected=on)
        indicator.set(fill=widget.color("primary") if on else (0, 0, 0, 0),
                      stroke_color=widget.color("primary") if (now and not on) else (0, 0, 0, 0),
                      stroke_width=1.0 if (now and not on) else 0.0)
        ink = ("on_primary" if on else "primary" if now else "on_surface_variant" if outside else "on_surface")
        label.set(fill=widget.color(ink))

    effect = Effect(paint)
    widget._undo.append(effect.dispose)
    widget.after_theme(paint)
    widget.on_click(lambda: on_click(widget.day) if on_click else None)
    return widget


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
    *,
    theme: Any = None,
) -> Any:
    """MD3's AM/PM period selector (M42: built from its fragment): 52x80,
    two 40 px halves in a 1 px `outline` frame with 8 px corners; the
    selected half `tertiary_container`/`on_tertiary_container`, the other
    `on_surface_variant`. `.period` (`"AM"`/`"PM"`) is a `Signal`; a click,
    Enter or the arrow keys switch it; `.on_change(fn)` hears the user's
    switches. Parts `am`, `pm`."""
    from tesserae import a11y
    from tesserae.reactive import Effect, Signal
    from tesserae.widgets._composed import Widget

    if selected not in ("AM", "PM"):
        raise ValueError(f"a period selector's selected is 'AM' or 'PM', got {selected!r}")
    name = "period_selector"

    def edit(spec: dict[str, Any]) -> None:
        spec["style"].update(height=80, corner_radius="small", border_color="outline",
                             border_width=float(border_width) if border_width is not None else 1.0)
        for half in spec["children"]:
            half["style"].update(height=40, corner_radius=0)
        if border_color is not None:
            spec["style"]["border_color"] = "#" + "".join(f"{c:02X}" for c in border_color)

    widget = Widget(window, "PeriodSelectorAM", {}, theme=theme, x=x, y=y, edit=edit, name=name,
                    interactive={"am": "on_surface", "pm": "on_surface"})
    widget.node.set(clip_children=True)
    widget.period = Signal(selected)
    changes: list[Any] = []
    widget.on_change = lambda fn: (changes.append(fn), lambda: changes.remove(fn) if fn in changes else None)[1]
    a11y.describe(widget.node, role="group", label="Period")

    def choose(period: str) -> None:
        if widget.period.get() != period:
            widget.period.set(period)
            for fn in list(changes):
                fn(period)

    def paint() -> None:
        chosen = widget.period.get()
        for period in ("am", "pm"):
            on = chosen == period.upper()
            half = widget.part(period)
            half.set(fill=widget.color("tertiary_container") if on else (0, 0, 0, 0), selected=on,
                     focusable=on)
            widget.part(f"{period}_label").set(fill=widget.color("on_tertiary_container" if on else
                                                                 "on_surface_variant"))

    effect = Effect(paint)
    widget._undo.append(effect.dispose)
    widget.after_theme(paint)
    for period in ("am", "pm"):
        widget.on_click(lambda p=period.upper(): choose(p), part=period, role="tab")
        other = "PM" if period == "am" else "AM"

        def on_key(event: Any, other: str = other) -> None:
            if event.key in ("arrow_up", "arrow_down", "arrow_left", "arrow_right"):
                choose(other)
                widget.part(other.lower()).focus()
        widget._undo.append(widget.view._listen(widget.part(period), "key_down", on_key))
    paint()
    return widget


def time_input_field(
    window: "Window",
    value: int | str = 0,
    unit: str = "hour",
    x: float | None = None,
    y: float | None = None,
    *,
    label: str | None = None,
    theme: Any = None,
) -> Any:
    """MD3's time input field (M42): 96x72, `surface_container_highest`
    with 8 px corners and a centred `display_medium` numeral in
    `on_surface`; focused, `primary_container` with a 2 px `primary`
    outline. `unit` is `"hour"` (0-23) or `"minute"` (0-59). `.value` is a
    `Signal` shown as two digits; typing a number in range sets it and
    leaving the field puts back the digits if it wasn't; the up and down
    arrows (and assistive technology's increment/decrement) step it,
    wrapping. `.on_change(fn)` hears the user's changes."""
    from tesserae import a11y
    from tesserae.reactive import Effect, Signal
    from tesserae.widgets._composed import Widget

    if unit not in ("hour", "minute"):
        raise ValueError(f"a time input field's unit is 'hour' or 'minute', got {unit!r}")
    top = 23 if unit == "hour" else 59
    number = int(value)
    if not 0 <= number <= top:
        raise ValueError(f"{number} isn't a valid {unit} (0-{top})")
    name = "time_input_field"
    spec = {"id": name, "kind": "TextField",
            "text": {"content": f"{number:02d}", "font_family": "Roboto", "font_weight": 400, "font_size": 45},
            "style": {"width": 96, "height": 72, "background": "surface_container_highest", "corner_radius": "small"}}
    widget = Widget(window, spec=spec, theme=theme, x=x, y=y, name=name)
    field = widget.part()  # a TextField's node is its text_input
    widget.box = field.parent()
    widget.value = Signal(number)
    changes: list[Any] = []
    widget.on_change = lambda fn: (changes.append(fn), lambda: changes.remove(fn) if fn in changes else None)[1]
    a11y.describe(field, label=label or unit.capitalize())
    # centred: `text_input` takes no `text_align`, so it's sized to two digits in a centring box
    digits_w, digits_h = window.measure_text("00", font_family="Roboto", font_size=45.0, font_weight=400.0)

    def centre() -> None:  # again after a re-colour, which re-applies the TextField's own layout
        field.set(flex_grow=0.0, align_self="center", width=float(digits_w) + 4.0, height=float(digits_h))
        widget.box.set(align_items="center", justify_content="center")

    centre()
    widget.after_theme(centre)

    def user_set(n: int) -> None:
        if widget.value.get() != n:
            widget.value.set(n)
            for fn in list(changes):
                fn(n)

    def paint() -> None:
        focused = bool(field.get("focused"))
        if not focused or _parse(field.get("text")) != widget.value.get():
            field.set(text=f"{widget.value.get():02d}")
        field.set(value=float(widget.value.get()), value_min=0.0, value_max=float(top),
                  fill=widget.color("on_primary_container" if focused else "on_surface"),
                  caret_color=widget.color("primary"))
        widget.box.set(fill=widget.color("primary_container" if focused else "surface_container_highest"),
                       stroke_color=widget.color("primary") if focused else (0, 0, 0, 0),
                       stroke_width=2.0 if focused else 0.0)

    def _parse(text: Any) -> int | None:
        try:
            n = int(str(text).strip())
        except ValueError:
            return None
        return n if 0 <= n <= top else None

    def typed(event: Any) -> None:
        n = _parse(field.get("text"))
        if n is not None:
            user_set(n)

    def step(by: int) -> None:
        user_set((widget.value.get() + by) % (top + 1))
        field.set(text=f"{widget.value.get():02d}")

    effect = Effect(paint)
    widget._undo.append(effect.dispose)
    widget.after_theme(paint)
    listen = widget.view._listen
    widget._undo += [
        listen(field, "change", typed),
        listen(field, "focus", lambda e: paint()),
        listen(field, "unfocus", lambda e: paint()),
        listen(field, "key_down", lambda e: step({"arrow_up": 1, "arrow_down": -1}[e.key])
               if e.key in ("arrow_up", "arrow_down") else None),
        a11y.on_action(field, {"increment": lambda e: step(1), "decrement": lambda e: step(-1)}, listen=listen),
    ]
    return widget
