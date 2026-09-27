"""Widgets that follow their app's theme (M50).

A `tesserae.widgets` widget or control made with no `theme=` on an
`App`'s window takes the app's theme and follows it: `App.set_dark`, the
OS switching light and dark, and `App.set_theme_specs` re-colour it with
the app's views (M50 Q1). An explicit `theme=` pins it (Q2). On a window
no `App` owns, it keeps MD3's baseline, as before.

The app is found by its window. `tre`'s `Window` can't be weakly
referenced, so each app is kept as a weak reference keyed by `id()` of
its window; an app keeps its window alive, so a live entry's window
can't have been replaced. An app holds its followers strongly, so a
widget no one kept a variable for still follows while its nodes are on
screen; one leaves when it's destroyed (`destroy`/`dispose` call
`unfollow`), or at the next re-theme once its node is gone (`alive`).
"""

from __future__ import annotations

import weakref
from typing import Any, Optional

from tesserae.theme import Theme

__all__ = ["alive", "app_of", "initial_theme", "register_app", "retheme", "unfollow"]

_APPS: dict[int, "weakref.ReferenceType[Any]"] = {}


def register_app(app: Any) -> None:
    """Makes `app` the owner of its window, for widgets made on it."""
    for key in [key for key, ref in _APPS.items() if ref() is None]:
        del _APPS[key]  # apps that are gone
    _APPS[id(app.window)] = weakref.ref(app)


def app_of(window: Any) -> Optional[Any]:
    """The live `App` whose window this is, or `None`."""
    ref = _APPS.get(id(window))
    return ref() if ref is not None else None  # a live app's window is alive, so its id isn't reused


def initial_theme(window: Any, theme: Optional[Theme], owner: Any) -> Theme:
    """The theme a widget starts with: `theme` if given (it's pinned);
    else, on an app's window, the app's theme, and `owner` follows it;
    else MD3's baseline."""
    if theme is not None:
        return theme
    app = app_of(window)
    if app is None:
        return Theme.resolve()
    app._followers[owner] = None
    return app.theme


def retheme(owner: Any, theme: Theme, view_theme: dict[str, Any]) -> None:
    """Re-themes a follower: its own `_follow_theme(theme, view_theme)` if
    it has one (a view, which takes the app's theme arguments; a shell,
    which leaves the widgets it was given alone), else `set_theme(theme)`."""
    follow = getattr(owner, "_follow_theme", None)
    if follow is not None:
        follow(theme, view_theme)
    else:
        owner.set_theme(theme)


def unfollow(window: Any, owner: Any) -> None:
    """`owner` stops following its app's theme (it's being destroyed)."""
    app = app_of(window)
    if app is not None:
        app._followers.pop(owner, None)


def alive(owner: Any) -> bool:
    """Whether a follower's node still exists: a node destroyed without
    the widget's own `destroy` raises `ValueError` when read. A follower
    with its own `_follow_alive` (a view) answers for itself; one with no
    node (a `Dock`) lives as long as its window."""
    check = getattr(owner, "_follow_alive", None)
    if check is not None:
        return check()
    node = getattr(owner, "node", None)
    if node is None:
        return True
    try:
        node.get("visible")
    except ValueError:
        return False
    return True
