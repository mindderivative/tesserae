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

from typing import TYPE_CHECKING, Any, Callable, Optional

from tesserae import overlays
from tesserae.widgets._composed import Widget
from tesserae.widgets.buttons import _borders

if TYPE_CHECKING:
    from tesserae.theme import Theme
    from tre import Node, Window


def dialog(
    window: "Window",
    headline: str,
    supporting_text: str,
    width: float,
    height: float,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
    *,
    actions: list[tuple[str, Optional[Callable[[], Any]]]] | None = None,
    theme: "Theme | None" = None,
) -> overlays.Dialog:
    """MD3's dialog (M41: `tesserae.overlays.Dialog`). `open()` it; Escape
    or an action closes it."""
    d = overlays.Dialog(window, headline, supporting_text, width=width, height=height, actions=actions, theme=theme)
    border = _borders([None], border_color, border_width)
    if border is not None:
        panel = d.widget.part("panel")
        panel.set(**({"stroke_color": tuple(border_color)} if border_color else {}),
                  **({"stroke_width": float(border_width)} if border_width is not None else {}))
    return d


def snackbar(
    window: "Window",
    text: str,
    width: float,
    action_label: str | None = None,
    closable: bool = False,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
    *,
    on_action: Callable[[], Any] | None = None,
    duration: int | None = 4000,
    theme: "Theme | None" = None,
) -> overlays.Snackbar:
    """MD3's snackbar (M41: `tesserae.overlays.Snackbar`). `open()` it; it
    hides itself after `duration` ms (`None` keeps it)."""
    s = overlays.Snackbar(window, text, width=width, action=action_label, on_action=on_action, closable=closable,
                          duration=duration, theme=theme)
    if border_color is not None or border_width is not None:
        s.node.set(**({"stroke_color": tuple(border_color)} if border_color else {}),
                   **({"stroke_width": float(border_width)} if border_width is not None else {}))
    return s


def side_sheet(
    window: "Window",
    width: float = 360.0,
    height: float | None = None,
    modal: bool = False,
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
    *,
    theme: "Theme | None" = None,
) -> "Widget | overlays.SideSheet":
    """MD3's side sheet. `modal=True` is `tesserae.overlays.SideSheet` (an
    overlay: `open()` it); otherwise a standard sheet, a `surface` panel in
    the layout, built from its fragment. Put content in `.panel`/`.node`."""
    if modal:
        return overlays.SideSheet(window, width=width, theme=theme)
    widget = Widget(window, "SideSheetStandard", {"width": width, "height": height if height is not None else 400},
                    theme=theme, x=x, y=y, edit=_borders([None], border_color, border_width), name="side_sheet")
    widget.panel = widget.node
    return widget


def menu(window: "Window", items: list[Any], width: float = 200.0, *,
         theme: "Theme | None" = None) -> overlays.Menu:
    """MD3's menu (M41: `tesserae.overlays.Menu`) of `menu_item(...)`s or
    `(label, fn)` pairs. `open(anchor)` below a node, `open_at(x, y)`, or
    `attach_context(node)` for a right-click."""
    return overlays.Menu(window, items, width=width, theme=theme)


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
    *,
    on_click: Callable[[], Any] | None = None,
    theme: "Theme | None" = None,
) -> Widget:
    """One of MD3's 48 px menu items (M41: built from its fragment), for
    `menu(...)`: a `label_large` label, an optional 24 px leading `icon`,
    and a trailing chevron when `submenu`. `on_click` runs when it's
    chosen (the menu closes)."""
    name = "menu_item"

    def edit(spec: dict[str, Any]) -> None:
        spec["style"].update(height=48, gap=12, padding={"left": 12, "right": 12, "top": 0, "bottom": 0})
        spec["children"][0].setdefault("style", {})["flex_grow"] = 1
        glyph = lambda node_id, n: {"id": node_id, "kind": "Icon", "icon": {"name": n},
                                    "style": {"width": 24, "height": 24, "foreground": "on_surface_variant"}}
        if icon is not None:
            spec["children"].insert(0, glyph(f"{name}.icon", icon))
        if submenu:
            spec["children"].append(glyph(f"{name}.submenu", "chevron_right"))
        border = _borders([None], border_color, border_width)
        if border is not None:
            border(spec)

    widget = Widget(window, "MenuItem", {"label": label, "width": width}, theme=theme, x=x, y=y, edit=edit,
                    interactive={None: "on_surface"}, name=name)
    widget._menu_action = on_click
    return widget


def tooltip(
    window: "Window",
    text: str,
    width: float | None = None,
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
    *,
    anchor: Any = None,
    theme: "Theme | None" = None,
) -> overlays.Tooltip:
    """MD3's plain tooltip (M41: `tesserae.overlays.Tooltip`).
    `attach(anchor)` (or `anchor=`) shows it on hover and keyboard focus."""
    t = overlays.Tooltip(window, text, width=width, theme=theme)
    if anchor is not None:
        t.attach(getattr(anchor, "node", anchor))
    return t
