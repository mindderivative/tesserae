"""Tesserae's own namespace for the Progress & Status category --
`circular_progress`, `linear_progress`, `loading_indicator`.

Since M40 each returns a Tesserae indicator (`tesserae.controls`), not a
bare `tre.Node`: `.node` is attached to the window's root, and `.value`
is a `Signal` (0.0..=1.0, or `None` for indeterminate). `foreground=`
replaces `primary`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from tesserae import controls
from tesserae.widgets._controls import place

if TYPE_CHECKING:
    from tre import Window


def circular_progress(
    window: "Window",
    size: float = 48.0,
    value: Optional[float] = 0.0,
    x: float | None = None,
    y: float | None = None,
    foreground: tuple[int, int, int, int] | None = None,
    **kwargs: Any,
) -> controls.CircularProgress:
    """MD3's circular progress; `value=None` spins indeterminately."""
    return place(window, controls.CircularProgress(window, size=size, value=value, color=foreground, **kwargs), x, y)


def linear_progress(
    window: "Window",
    width: float,
    height: float = 4.0,
    value: Optional[float] = 0.0,
    x: float | None = None,
    y: float | None = None,
    foreground: tuple[int, int, int, int] | None = None,
    **kwargs: Any,
) -> controls.LinearProgress:
    """MD3's linear progress; `value=None` sweeps indeterminately."""
    bar = controls.LinearProgress(window, width=width, value=value, color=foreground, **kwargs)
    if height != controls.LinearProgress.HEIGHT:
        bar.node.set(height=height)
        bar.bar.set(height=height)
    return place(window, bar, x, y)


def loading_indicator(
    window: "Window",
    size: float = 48.0,
    foreground: tuple[int, int, int, int] | None = None,
    x: float | None = None,
    y: float | None = None,
    **kwargs: Any,
) -> controls.LoadingIndicator:
    """MD3's loading indicator: a shape morphing forever."""
    return place(window, controls.LoadingIndicator(window, size=size, color=foreground, **kwargs), x, y)
