"""Tesserae's own namespace for the Navigation & Shell Composition
category -- `tabs`, `navigation_rail`, `navigation_drawer`, `toolbar`,
`top_app_bar`, `status_bar`.

Same thin-delegate shape as `buttons.py`/`selection.py`/`structural.py`.
One real naming translation here: `tre`'s own `add_toolbar(color=...)`
isn't an RGBA color at all -- it's a named container-tone selector
(`"standard"`/`"vibrant"`, verified directly against `window_factory.rs`),
genuinely confusing under the name `color` (a caller would reasonably
expect an RGBA tuple, like every other `color`/`background` kwarg in this
catalog takes). Tesserae's own `toolbar(...)` calls it `tone=` instead,
translating internally when it delegates.
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
    tone: str | None = None,
    width: float | None = None,
    height: float | None = None,
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
) -> "Node":
    """A floating or docked action-icon bar. `variant`: docked/floating.
    `tone`: standard/vibrant (named container tone, not an RGBA color --
    `tre`'s own `add_toolbar` calls this `color=`, which we translate)."""
    return window.add_toolbar(
        variant=variant,
        orientation=orientation,
        color=tone,
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
