"""Tesserae's own namespace for the Navigation & Shell Composition
category -- `tabs`, `navigation_rail`, `navigation_drawer`, `toolbar`,
`top_app_bar`, `status_bar`.

Same thin-delegate shape as `buttons.py`/`selection.py`/`structural.py`,
with no naming translation. `toolbar(vibrant=)` matches `tre` 0.3.3's
`add_toolbar(vibrant=)`; before M32, `tre` took a confusing
`color="standard"|"vibrant"` and Tesserae translated its own `tone=` to it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tre import Node, Window


def tabs(
    window: "Window",
    labels: list[str],
    icons: list[str] | None = None,
    selected: int | None = None,
    width: float | None = None,
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
) -> list["Node"]:
    """A real MD3 tab row with an animated active-indicator. Returns one
    `Node` per tab."""
    return window.add_tabs(
        labels,
        icons=icons,
        selected=selected,
        width=width,
        x=x,
        y=y,
        border_color=border_color,
        border_width=border_width,
    )


def navigation_rail(
    window: "Window",
    labels: list[str],
    icons: list[str],
    selected: int | None = None,
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
) -> list["Node"]:
    """The compact, icon-first side rail. Returns one `Node` per entry."""
    return window.add_navigation_rail(
        labels, icons, selected=selected, x=x, y=y, border_color=border_color, border_width=border_width
    )


def navigation_drawer(
    window: "Window",
    labels: list[str],
    icons: list[str],
    selected: int | None = None,
    modal: bool = False,
    width: float = 360.0,
    height: float | None = None,
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
) -> tuple["Node", list["Node"]]:
    """Returns `(container, entries)`. `modal=True` opens/closes via
    `Window.open_navigation_drawer`/`close_navigation_drawer` as a real
    dismissable overlay; non-modal is a permanent layout child."""
    return window.add_navigation_drawer(
        labels,
        icons,
        selected=selected,
        modal=modal,
        width=width,
        height=height,
        x=x,
        y=y,
        border_color=border_color,
        border_width=border_width,
    )


def toolbar(
    window: "Window",
    variant: str = "docked",
    orientation: str | None = None,
    vibrant: bool = False,
    width: float | None = None,
    height: float | None = None,
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
) -> "Node":
    """A floating or docked action-icon bar. `variant`: docked/floating.
    `vibrant=True` uses MD3's vibrant container tone instead of the
    standard one."""
    return window.add_toolbar(
        variant=variant,
        orientation=orientation,
        vibrant=vibrant,
        width=width,
        height=height,
        x=x,
        y=y,
        border_color=border_color,
        border_width=border_width,
    )


def top_app_bar(
    window: "Window",
    title: str,
    leading_icon: str | None = None,
    trailing_icons: list[str] | None = None,
    width: float | None = None,
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
) -> tuple["Node", "Node | None", list["Node"]]:
    """The window's own top title bar. Returns `(bar, leading_icon_node,
    trailing_icon_nodes)`."""
    return window.add_top_app_bar(
        title,
        leading_icon=leading_icon,
        trailing_icons=trailing_icons,
        width=width,
        x=x,
        y=y,
        border_color=border_color,
        border_width=border_width,
    )


def status_bar(
    window: "Window",
    text: str,
    width: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
) -> "Node":
    """A window-bottom status strip, typically passed to
    `build_shell(status_bar=...)`."""
    return window.add_status_bar(text, width=width, border_color=border_color, border_width=border_width)
