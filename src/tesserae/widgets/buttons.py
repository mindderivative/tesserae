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

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tre import Node, Window


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
) -> "Node":
    """A real MD3 button. `variant`: elevated/filled/filled_tonal/outlined/text."""
    return window.add_button(
        label,
        width,
        height,
        variant=variant,
        x=x,
        y=y,
        border_color=border_color,
        border_width=border_width,
    )


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
