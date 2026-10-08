"""Removed: `AppShell`, the Python app shell.

Describe the frame as a `kind: Window` view (a `title_bar:`, a `NavigationRailScreens`, a `kind: Dock`, routed `view:` nodes)
and load it with `app.load("Window")`; to dock panels from Python, use `tesserae.docking.Dock`. This module only says so:
importing `AppShell` from it raises `tesserae._removed.RemovedError`.
"""

from __future__ import annotations

from typing import NoReturn

from tesserae._removed import removed

__all__: list[str] = []


def __getattr__(name: str) -> NoReturn:
    if name == "AppShell":
        raise removed("AppShell")
    raise AttributeError(f"module 'tesserae.shell' has no attribute {name!r}")
