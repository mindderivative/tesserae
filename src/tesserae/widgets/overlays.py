"""Tesserae's own namespace for the Overlays category -- `dialog`,
`snackbar`, `side_sheet`, `menu`, `menu_item`, `tooltip`, `popover`.

Each (but `menu_item`, and a standard `side_sheet`) returns one of
`tesserae.overlays`' overlays (M41; `popover` M42), built by Tesserae on
`tre`'s layers: `open()` shows it and `close()` hides it."""

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
    """MD3's dialog (`tesserae.overlays.Dialog`). `open()` it; Escape
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
    """MD3's snackbar (`tesserae.overlays.Snackbar`). `open()` it; it
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
    the layout. Put content in `.panel`/`.node`."""
    if modal:
        return overlays.SideSheet(window, width=width, theme=theme)
    widget = Widget(window, "SideSheetStandard", {"width": width, "height": height if height is not None else 400},
                    theme=theme, x=x, y=y, edit=_borders([None], border_color, border_width), name="side_sheet")
    widget.panel = widget.node
    return widget


def menu(window: "Window", items: list[Any], width: float = 200.0, *,
         theme: "Theme | None" = None) -> overlays.Menu:
    """MD3's menu (`tesserae.overlays.Menu`) of `menu_item(...)`s or
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
    """One of MD3's 48 px menu items, for
    `menu(...)`: a `label_large` label, an optional 24 px leading `icon`,
    and a trailing chevron when `submenu`. `on_click` runs when it's
    chosen (the menu closes)."""
    name = "menu_item"

    def edit(spec: dict[str, Any]) -> None:
        spec["style"].update(height=48, gap=12, padding={"left": 12, "right": 12, "top": 0, "bottom": 0})
        spec["children"][0].setdefault("style", {})["flex"] = "expand_horizontal"
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
    """MD3's plain tooltip (`tesserae.overlays.Tooltip`).
    `attach(anchor)` (or `anchor=`) shows it on hover and keyboard focus."""
    t = overlays.Tooltip(window, text, width=width, theme=theme)
    if anchor is not None:
        t.attach(getattr(anchor, "node", anchor))
    return t


def popover(
    window: "Window",
    supporting_text: str,
    subhead: str | None = None,
    width: float = 312.0,
    *,
    actions: list[tuple[str, Optional[Callable[[], Any]]]] | None = None,
    anchor: Any = None,
    theme: "Theme | None" = None,
) -> overlays.Popover:
    """MD3's rich tooltip, `tre`'s popover (`tesserae.overlays.Popover`).
    `open(anchor)` it, or `attach(anchor)` (or `anchor=`) to open and close
    it on the anchor's click; an outside press, Escape or an action closes it."""
    p = overlays.Popover(window, supporting_text, subhead=subhead, width=width, actions=actions, theme=theme)
    if anchor is not None:
        p.attach(getattr(anchor, "node", anchor))
    return p
