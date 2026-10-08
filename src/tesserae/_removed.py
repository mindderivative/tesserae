"""The names that were removed, and what each says when it is used.

A removed name that just disappears gives an `AttributeError` that tells nobody what to do. Each one here raises
`RemovedError` instead, naming what replaces it and where the migration page is. The stubs are themselves temporary:
they are deleted one release after the names are.

    from tesserae._removed import removed
    raise removed("decorations")
"""

from __future__ import annotations

__all__ = ["MIGRATION", "REMOVED", "RemovedError", "removed"]

MIGRATION = "https://mindderivative.github.io/tesserae/migration/"

#: name -> what to use instead, and how
REMOVED: dict[str, str] = {
    "decorations": "use `borderless=True` instead (`decorations=False` is `borderless=True`), or `borderless: true` on a "
                   "`kind: Window` view",
    "app.decorations": "use `app.borderless` instead (it is the opposite: `app.decorations` was `not app.borderless`)",
    "app.decorated": "bind `app.borderless` instead (it is the opposite of `app.decorated`)",
    "App.load_shell": "describe the frame as a `kind: Window` view with a `title_bar:`, a `NavigationRailScreens`, a `kind: Dock` and "
                      "routed `view:` nodes, and load it with `app.load(\"Window\")`",
    "App.use_shell": "describe the frame as a `kind: Window` view and load it with `app.load(\"Window\")`; to dock panels "
                     "from Python, use `tesserae.docking.Dock`",
    "AppShell": "describe the frame as a `kind: Window` view and load it with `app.load(\"Window\")`; to dock panels from "
                "Python, use `tesserae.docking.Dock`",
    "*_Shell.yaml": "write the same frame as a `kind: Window` view (`Window_View.yaml`): `top_bar` is `title_bar:`, "
                    "`navigation` is a `NavigationRailScreens`, `status_bar` is a `StatusBar`, `zones` and `panels` are a "
                    "`kind: Dock` with `kind: DockPanel`s, and each screen is a `view:` with a `route:`",
    "tesserae new --shell": "use `tesserae new --window`, which makes the app a `kind: Window` view",
}


class RemovedError(ValueError):
    """A name that was removed was used: the message says what replaces it."""

    def __init__(self, name: str, message: str) -> None:
        super().__init__(message)
        self.name = name


def removed(name: str) -> RemovedError:
    """The error for using `name` (a key of `REMOVED`)."""
    try:
        instead = REMOVED[name]
    except KeyError:
        raise KeyError(f"{name!r} isn't a removed name: {sorted(REMOVED)}") from None
    return RemovedError(name, f"`{name}` was removed: {instead}. See {MIGRATION}.")
