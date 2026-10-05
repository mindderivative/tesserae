"""Motion that follows the user's wish for less of it.

The OS says whether the user asked to reduce motion (`App.reduced_motion`). Where it did, an animation's duration is
0, so the thing it moves is where it is going at once, and an animation that would repeat for ever is not started.
"""

from __future__ import annotations

from typing import Any

from tesserae.follow import app_of

__all__ = ["duration", "reduced"]


def reduced(window: Any) -> bool:
    """Whether the app that owns `window` is to reduce motion."""
    app = app_of(window)
    return bool(app is not None and app.reduced_motion)


def duration(window: Any, ms: float) -> int:
    """`ms`, or 0 when the app is to reduce motion."""
    return 0 if reduced(window) else int(ms)
