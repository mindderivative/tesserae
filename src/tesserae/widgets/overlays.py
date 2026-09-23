"""Tesserae's own namespace for the Overlays category -- `dialog`,
`snackbar`, `side_sheet`, `menu`, `menu_item`, `tooltip`.

Same thin-delegate shape as `buttons.py`/`selection.py`/`structural.py`/
`navigation.py`. None of these 6 expose an ambiguous color kwarg (only
the already-clear `border_color`), so no naming translation applies
here. Deliberately does NOT wrap `Window.open_*`/`close_*` (e.g.
`open_dialog`/`close_dialog`) -- those are already plain, minimal
`Window` methods with no naming ambiguity or construction-time logic to
delegate around, so a `tesserae.widgets` wrapper would add indirection
with no real value. `menu` delegates to `tre`'s own `build_menu` (not
`add_menu`, matching the real factory name)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tre import Node, Window


def dialog(
    window: "Window",
    headline: str,
    text: str,
    width: float,
    height: float,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
) -> "Node":
    """A real MD3 dialog. Modal by default. Show/hide via
    `Window.open_dialog`/`close_dialog`."""
    return window.add_dialog(headline, text, width, height, border_color=border_color, border_width=border_width)


def snackbar(
    window: "Window",
    text: str,
    width: float,
    action_label: str | None = None,
    closable: bool = False,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
) -> tuple["Node", "Node | None", "Node | None"]:
    """Returns `(container, action_button, close_button)` -- the latter
    two are `None` when `action_label`/`closable` weren't given.
    Non-modal; auto-dismiss is the app's own timer."""
    return window.add_snackbar(
        text,
        width,
        action_label=action_label,
        closable=closable,
        border_color=border_color,
        border_width=border_width,
    )


def side_sheet(
    window: "Window",
    width: float = 360.0,
    height: float | None = None,
    modal: bool = False,
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
) -> "Node":
    """Show/hide via `Window.open_side_sheet`/`close_side_sheet`."""
    return window.add_side_sheet(
        width=width, height=height, modal=modal, x=x, y=y, border_color=border_color, border_width=border_width
    )


def menu(window: "Window", items: list["Node"], width: float = 200.0) -> "Node":
    """A panel of `menu_item(...)` rows. Show anchored below a node via
    `Window.open_menu(anchor, menu)`; hide via `close_menu(menu)`.
    `tooltip`'s and the search-results panel's own overlays reuse this
    identical open/close pair, matching `tre`'s own `build_menu`."""
    return window.build_menu(items, width=width)


def menu_item(
    window: "Window",
    label: str,
    icon: str | None = None,
    submenu: bool = False,
    width: float = 200.0,
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
) -> "Node":
    """One row for `menu(...)`. `submenu=True` paints a trailing
    disclosure affordance -- the app still owns opening a nested `menu`
    on click, no automatic nesting."""
    return window.add_menu_item(
        label,
        icon=icon,
        submenu=submenu,
        width=width,
        x=x,
        y=y,
        border_color=border_color,
        border_width=border_width,
    )


def tooltip(
    window: "Window",
    text: str,
    width: float,
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
) -> "Node":
    """Show/hide via the same `Window.open_menu`/`close_menu` pair
    `menu(...)` uses, matching `tre`'s own real design (no dedicated
    tooltip open/close pair)."""
    return window.add_tooltip(text, width, x=x, y=y, border_color=border_color, border_width=border_width)
