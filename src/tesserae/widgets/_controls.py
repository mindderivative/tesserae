"""Placing a `tesserae.controls` control the way `tre`'s `add_*` placed
its widget (M40): attached to the window's root, and at `x`/`y` when given."""

from __future__ import annotations

from typing import Any, Optional


def place(window: Any, control: Any, x: Optional[float], y: Optional[float]) -> Any:
    window.root.add_child(control.node)
    if x is not None or y is not None:
        control.node.set(position="absolute", x=float(x or 0.0), y=float(y or 0.0))
    return control
