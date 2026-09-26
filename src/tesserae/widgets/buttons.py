"""Tesserae's own namespace for the Buttons & Actions category of `tre`'s
MD3 catalog -- `button`, `icon_button`, `fab`, `extended_fab`,
`split_button`, `button_group`.

Each function here is a thin, faithful delegate to the matching
`Window.add_*` factory in `tre` itself: same parameter names, order, and
defaults, `window` as the first positional argument (matching
`tesserae.component.instantiate`'s own established convention). This is
deliberate, not a placeholder -- `tre`'s own factories already resolve MD3
color/shape/elevation correctly against the live theme, and for
`split_button`/`button_group` specifically, only the real Rust factory can
drive their hover/press shape-tightening and reflow animations (no public
Python API reaches `PaintProperties.button_group_reflow`/`shape`/
`press_interactive_shape`; a from-scratch Python reimplementation could
only ever produce a rest-state-only port). Delegating keeps full fidelity
for all six and gives Tesserae apps one consistent `tesserae.widgets`
surface to import from, so a widget "looks like Tesserae's own" whether or
not `tre` happens to implement it as a composition under the hood.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

from tesserae.widgets._composed import Widget

if TYPE_CHECKING:
    from tesserae.theme import Theme
    from tre import Node, Window


#: `button`'s variants: the fragment, and its label's colour role (its feedback's too).
_BUTTONS = {
    "elevated": ("ButtonElevated", "primary"),
    "filled": ("ButtonFilled", "on_primary"),
    "filled_tonal": ("ButtonFilledTonal", "on_secondary_container"),
    "outlined": ("ButtonOutlined", "primary"),
    "text": ("ButtonText", "primary"),
}


def _hex(color: tuple[int, int, int, int]) -> str:
    return "#" + "".join(f"{c:02X}" for c in color)


def button(
    window: "Window",
    label: str,
    width: float,
    height: float,
    variant: str = "filled",
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
    *,
    corner_radius: float | None = None,
    theme: "Theme | None" = None,
    on_click: Callable[[], Any] | None = None,
) -> Widget:
    """MD3's button, built from its fragment (M41). `variant`: elevated,
    filled, filled_tonal, outlined or text. It's a pill (`corner_radius`
    half the height) unless told otherwise. `on_click` makes it a focusable
    button that Enter and Space activate, with MD3's feedback."""
    if variant not in _BUTTONS:
        raise ValueError(f"unknown button variant {variant!r}; expected one of {sorted(_BUTTONS)}")
    fragment, content = _BUTTONS[variant]
    radius = float(height) / 2 if corner_radius is None else float(corner_radius)

    def edit(spec: dict[str, Any]) -> None:
        if border_color is not None:
            spec["style"]["border_color"] = _hex(border_color)
        if border_width is not None:
            spec["style"]["border_width"] = float(border_width)

    widget = Widget(window, fragment, {"label": label, "width": width, "height": height, "corner_radius": radius},
                    theme=theme, x=x, y=y, interactive={None: content}, edit=edit, name="button")
    if on_click is not None:
        widget.on_click(on_click)
    return widget


def icon_button(
    window: "Window",
    icon: str,
    size: float = 40.0,
    variant: str = "standard",
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
) -> "Node":
    """A real MD3 icon button. `variant`: standard/filled/filled_tonal/outlined."""
    return window.add_icon_button(
        icon,
        size=size,
        variant=variant,
        x=x,
        y=y,
        border_color=border_color,
        border_width=border_width,
    )


def fab(
    window: "Window",
    icon: str,
    size: str = "default",
    variant: str = "surface",
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
) -> "Node":
    """A real MD3 floating action button. `size`: small/default/large.
    `variant`: surface/primary/secondary/tertiary."""
    return window.add_fab(
        icon,
        size=size,
        variant=variant,
        x=x,
        y=y,
        border_color=border_color,
        border_width=border_width,
    )


def extended_fab(
    window: "Window",
    label: str,
    width: float,
    icon: str | None = None,
    variant: str = "primary",
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
) -> "Node":
    """A real MD3 extended FAB, an optional leading icon plus a label."""
    return window.add_extended_fab(
        label,
        width,
        icon=icon,
        variant=variant,
        x=x,
        y=y,
        border_color=border_color,
        border_width=border_width,
    )


def split_button(
    window: "Window",
    label: str,
    width: float,
    height: float,
    variant: str = "filled",
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
) -> tuple["Node", "Node", "Node"]:
    """A real MD3 split button (leading action + trailing chevron).
    Returns `(leading, trailing, container)`, matching `tre`'s own
    `add_split_button`. Delegates directly to the native factory, so the
    real hover/press shape-tightening animation is fully live -- unlike a
    from-scratch Python port, which has no public API to reach it."""
    return window.add_split_button(
        label,
        width,
        height,
        variant=variant,
        x=x,
        y=y,
        border_color=border_color,
        border_width=border_width,
    )


def button_group(
    window: "Window",
    labels: list[str],
    width: float,
    height: float,
    variant: str = "filled",
    x: float | None = None,
    y: float | None = None,
) -> tuple["Node", list["Node"]]:
    """A real MD3 connected button group. Returns `(container, buttons)`,
    matching `tre`'s own `add_button_group`. Delegates directly to the
    native factory, so the real hover reflow/regroup animation is fully
    live -- unlike a from-scratch Python port, which has no public API to
    reach it."""
    return window.add_button_group(
        labels,
        width,
        height,
        variant=variant,
        x=x,
        y=y,
    )
