"""Tesserae's own namespace for the Progress & Status category --
`circular_progress`, `linear_progress`, `loading_indicator`. All 3 are
real `NodeKind` primitives in `tre`, wrapped for the same uniform-surface
reason M9 wrapped `checkbox`/`slider`/etc.

`loading_indicator(foreground=)` is the spinner's glyph color (it falls
back to the theme's primary when omitted). `tre` 0.3.3 uses the same
name, so it passes straight through; before M32, `tre` called it
`color=` and Tesserae translated.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tre import Node, Window


def circular_progress(
    window: "Window",
    size: float = 48.0,
    value: float = 0.0,
    x: float | None = None,
    y: float | None = None,
) -> "Node":
    """`value` in 0.0..=1.0; animate it directly with
    `node.animate("value", ...)`."""
    return window.add_circular_progress(size=size, value=value, x=x, y=y)


def linear_progress(
    window: "Window",
    width: float,
    height: float = 4.0,
    value: float = 0.0,
    x: float | None = None,
    y: float | None = None,
) -> "Node":
    """Same `value` contract as `circular_progress`."""
    return window.add_linear_progress(width, height=height, value=value, x=x, y=y)


def loading_indicator(
    window: "Window",
    size: float = 48.0,
    foreground: tuple[int, int, int, int] | None = None,
    x: float | None = None,
    y: float | None = None,
) -> "Node":
    """MD3's newer indeterminate spinner shape. `foreground` (its glyph
    color) falls back to the theme's primary when omitted."""
    return window.add_loading_indicator(size=size, foreground=foreground, x=x, y=y)
