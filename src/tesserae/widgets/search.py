"""Tesserae's own namespace for the Search category -- `search_bar`,
`search_view`. Same thin-delegate shape as the other widget modules.
Neither exposes an ambiguous color kwarg."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tre import Node, Window


def search_bar(
    window: "Window",
    placeholder: str,
    width: float,
    leading_icon: str | None = None,
    trailing_icons: list[str] | None = None,
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
) -> tuple["Node", "Node", "Node | None", list["Node"]]:
    """Returns `(bar, text_field, leading_icon_node, trailing_icon_nodes)`
    -- unlike most widgets here, the caller needs the inner `TextField`
    node directly to wire `set_on_change`/read `get_text()`."""
    return window.add_search_bar(
        placeholder,
        width,
        leading_icon=leading_icon,
        trailing_icons=trailing_icons,
        x=x,
        y=y,
        border_color=border_color,
        border_width=border_width,
    )


def search_view(
    window: "Window",
    width: float,
    height: float,
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
) -> "Node":
    """The docked suggestions/results panel -- a plain styled surface
    with no fixed content anatomy; populate via `Node.add_child`, same
    contract as `card(...)`. Show/hide via `Window.open_menu`/
    `close_menu` directly, matching `tre`'s own real design."""
    return window.add_search_view(width, height, x=x, y=y, border_color=border_color, border_width=border_width)
