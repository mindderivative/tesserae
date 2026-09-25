"""Tesserae's own namespace for the Cards, Lists, Chips & Structural Rows
category -- `card`, `list_`, `list_item`, `chip`, `badge`, `divider`,
`link`, `accordion_header`, `tree_node`.

Same thin-delegate shape as `buttons.py`/`selection.py`. None of these 9
expose an ambiguous color kwarg -- `add_card`/`add_chip`/`add_badge`/
`add_list_item`/`add_divider`/`add_accordion_header`/`add_tree_node` only
take the already-clear `border_color` (verified directly against
`window_factory.rs`), and `add_list`/`add_link` take no color at all --
so no naming translation from `buttons.py`'s module docstring applies
here. `list_` (trailing underscore) avoids shadowing the builtin `list`,
matching `tre`'s own `add_list` factory name it delegates to.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tre import Node, Window


def card(
    window: "Window",
    width: float,
    height: float,
    variant: str = "elevated",
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
) -> "Node":
    """A real MD3 card. `variant`: elevated/filled/outlined. Content-free
    -- populate via `Node.add_child`."""
    return window.add_card(
        width, height, variant=variant, x=x, y=y, border_color=border_color, border_width=border_width
    )


def list_(
    window: "Window",
    items: list["Node"],
    width: float = 360.0,
    x: float | None = None,
    y: float | None = None,
) -> "Node":
    """Lays out already-built `list_item(...)` nodes as a column."""
    return window.add_list(items, width=width, x=x, y=y)


def list_item(
    window: "Window",
    headline: str,
    leading_icon: str | None = None,
    trailing_icon: str | None = None,
    supporting_text: str | None = None,
    width: float = 360.0,
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
) -> "Node":
    """One real MD3 list row."""
    return window.add_list_item(
        headline,
        leading_icon=leading_icon,
        trailing_icon=trailing_icon,
        supporting_text=supporting_text,
        width=width,
        x=x,
        y=y,
        border_color=border_color,
        border_width=border_width,
    )


def chip(
    window: "Window",
    label: str,
    width: float,
    variant: str = "assist",
    icon: str | None = None,
    selected: bool = False,
    removable: bool = False,
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
) -> "Node":
    """A real MD3 chip. `variant`: assist/filter/input/suggestion."""
    return window.add_chip(
        label,
        width,
        variant=variant,
        icon=icon,
        selected=selected,
        removable=removable,
        x=x,
        y=y,
        border_color=border_color,
        border_width=border_width,
    )


def badge(
    window: "Window",
    label: str | None = None,
    width: float | None = None,
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
) -> "Node":
    """A real MD3 badge -- a square dot when `label=None`, otherwise a
    pill sized to `width`. Caller positions it via `x`/`y`, same contract
    as `Rect`."""
    return window.add_badge(
        label=label, width=width, x=x, y=y, border_color=border_color, border_width=border_width
    )


def divider(
    window: "Window",
    length: float,
    orientation: str = "horizontal",
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
) -> "Node":
    """A single hairline. `orientation`: "horizontal" or "vertical"."""
    return window.add_divider(
        length, orientation=orientation, x=x, y=y, border_color=border_color, border_width=border_width
    )


def link(
    window: "Window",
    content: str,
    width: float,
    x: float | None = None,
    y: float | None = None,
) -> "Node":
    """Styled, clickable text -- call `set_on_click` for navigation."""
    return window.add_link(content, width, x=x, y=y)


def accordion_header(
    window: "Window",
    title: str,
    expanded: bool = False,
    width: float = 360.0,
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
) -> tuple["Node", "Node"]:
    """Returns `(header, chevron)`. Pairs with app-managed content shown/
    hidden on click."""
    return window.add_accordion_header(
        title,
        expanded=expanded,
        width=width,
        x=x,
        y=y,
        border_color=border_color,
        border_width=border_width,
    )


def tree_node(
    window: "Window",
    title: str,
    depth: int = 0,
    expanded: bool = False,
    leaf: bool = False,
    width: float = 360.0,
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
) -> tuple["Node", "Node | None"]:
    """Returns `(node, chevron)` -- `chevron` is `None` when `leaf=True`.
    `depth` drives indentation; the app owns real tree structure/
    recursion."""
    return window.add_tree_node(
        title,
        depth=depth,
        expanded=expanded,
        leaf=leaf,
        width=width,
        x=x,
        y=y,
        border_color=border_color,
        border_width=border_width,
    )
