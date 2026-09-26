"""Tesserae's own namespace for the Cards, Lists, Chips & Structural Rows
category -- `card`, `list_`, `list_item`, `chip`, `badge`, `divider`,
`link`, `accordion_header`, `tree_node`.

Same thin-delegate shape as `buttons.py`/`selection.py`. None of these 9
expose an ambiguous color kwarg -- `add_card`/`add_chip`/`add_badge`/
`add_list_item`/`add_divider`/`add_accordion_header`/`add_tree_node` only
take the already-clear `border_color` (verified directly against
`window_factory.rs`), and `add_list`/`add_link` take no color at all --
so no naming translation from `buttons.py`'s module docstring applies
here. `list_` (trailing underscore) avoids shadowing the builtin `list`,
matching `tre`'s own `add_list` factory name it delegates to.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Optional

from tesserae import a11y
from tesserae.reactive import Effect, Signal
from tesserae.widgets._composed import Widget, fragment
from tesserae.widgets.buttons import _borders, _hex, _variant

if TYPE_CHECKING:
    from tesserae.theme import Theme
    from tre import Node, Window


_CARDS = {"elevated": "CardElevated", "filled": "CardFilled", "outlined": "CardOutlined"}


def card(
    window: "Window",
    width: float,
    height: float,
    variant: str = "elevated",
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
    *,
    theme: "Theme | None" = None,
    on_click: Callable[[], Any] | None = None,
) -> Widget:
    """MD3's card (M41: built from its fragment): elevated, filled or
    outlined. Content-free: add to `.node`. `on_click` makes it an
    actionable card, with MD3's feedback."""
    widget = Widget(window, _variant("card", variant, _CARDS), {"width": width, "height": height}, theme=theme,
                    x=x, y=y, edit=_borders([None], border_color, border_width), name="card")
    if on_click is not None:
        widget.interactive(None, "on_surface")
        widget.on_click(on_click)
    return widget


def list_(
    window: "Window",
    items: list[Any],
    width: float = 360.0,
    x: float | None = None,
    y: float | None = None,
    *,
    theme: "Theme | None" = None,
) -> Widget:
    """Lays out `list_item(...)`s (or any nodes) as MD3's list: a column
    `width` wide. The items move into it. An empty list is an error, as
    `tre`'s was."""
    if not items:
        raise ValueError("a list needs at least one item")
    widget = Widget(window, spec={"id": "list", "kind": "Container",
                                  "style": {"width": width, "flex_direction": "vertical"}},
                    theme=theme, x=x, y=y, name="list")
    a11y.describe(widget.node, role="list")
    for item in items:
        node = getattr(item, "node", item)
        node.set(width=float(width))
        widget.node.add_child(node)
        a11y.describe(node, role="listitem")
    return widget


def list_item(
    window: "Window",
    headline: str,
    leading_icon: str | None = None,
    trailing_icon: str | None = None,
    supporting_text: str | None = None,
    width: float = 360.0,
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
    *,
    theme: "Theme | None" = None,
    on_click: Callable[[], Any] | None = None,
) -> Widget:
    """One MD3 list row (M41: built from its fragment): a `body_large`
    headline, 56 px tall, or 72 with `supporting_text` (`body_medium`,
    `on_surface_variant`) under it; 24 px `on_surface_variant` icons either
    side. Parts: `headline`, `supporting`, `leading`, `trailing`."""
    border = _borders([None], border_color, border_width)

    def edit(spec: dict[str, Any]) -> None:
        name = spec["id"]
        headline_spec = spec["children"][0]
        text_part = headline_spec
        if supporting_text is not None:
            spec["style"]["height"] = 72
            text_part = {"id": f"{name}.text", "kind": "Container",
                         "style": {"flex_direction": "vertical", "flex_grow": 1},
                         "children": [headline_spec, {
                             "id": f"{name}.supporting", "kind": "Text",
                             "text": {"content": supporting_text, "typography_role": "body_medium"},
                             "style": {"foreground": "on_surface_variant"}}]}
        else:
            headline_spec.setdefault("style", {})["flex_grow"] = 1
        children = [text_part]
        if leading_icon is not None:
            children.insert(0, _icon_spec(f"{name}.leading", leading_icon))
        if trailing_icon is not None:
            children.append(_icon_spec(f"{name}.trailing", trailing_icon))
        spec["children"] = children
        spec["style"].update(gap=16, padding={"left": 16, "right": 24 if trailing_icon else 16, "top": 8, "bottom": 8})
        if border is not None:
            border(spec)

    widget = Widget(window, "ListItem", {"headline": headline, "width": width}, theme=theme, x=x, y=y, edit=edit,
                    name="list_item")
    if on_click is not None:
        widget.interactive(None, "on_surface")
        widget.on_click(on_click)
    return widget


def _icon_spec(node_id: str, name: str, size: float = 24.0, foreground: str = "on_surface_variant") -> dict[str, Any]:
    return {"id": node_id, "kind": "Icon", "icon": {"name": name},
            "style": {"width": size, "height": size, "foreground": foreground}}


_CHIPS = {"assist": "ChipAssist", "filter": "ChipFilter", "input": "ChipInput", "suggestion": "ChipSuggestion"}


def chip(
    window: "Window",
    label: str,
    width: float,
    variant: str = "assist",
    icon: str | None = None,
    selected: bool = False,
    removable: bool = False,
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
    *,
    theme: "Theme | None" = None,
    on_click: Callable[[], Any] | None = None,
    on_remove: Callable[[], Any] | None = None,
) -> Widget:
    """MD3's chip (M41: built from its fragment): assist, filter, input or
    suggestion, 32 px tall, with an optional leading `icon`.

    A filter chip toggles when clicked: `.selected` is a `Signal`, and
    selected it's `secondary_container` with a check and no border. An
    input chip with `removable=True` has a trailing close button that calls
    `on_remove`. The chip itself is a button (a filter chip a checkbox)."""
    fragment_name = _variant("chip", variant, _CHIPS)
    border = _borders([None], border_color, border_width)

    def edit(spec: dict[str, Any]) -> None:
        name = spec["id"]
        ink = spec["children"][0]["style"]["foreground"]
        if icon is not None:
            spec["children"].insert(0, _icon_spec(f"{name}.icon", icon, 18.0, "primary"))
        if variant == "filter":
            spec["children"].insert(0, _icon_spec(f"{name}.check", "check", 18.0, "on_secondary_container"))
        if removable:
            spec["children"].append({"id": f"{name}.remove", "kind": "Rect",
                                     "style": {"width": 18, "height": 18, "background": "transparent",
                                               "corner_radius": 9, "align_items": "center",
                                               "justify_content": "center"},
                                     "children": [_icon_spec(f"{name}.remove.icon", "close", 18.0, ink)]})
        if icon is not None or variant == "filter":
            spec["style"]["padding"] = {"left": 8, "right": 8 if removable else 16, "top": 0, "bottom": 0}
        elif removable:
            spec["style"]["padding"] = {"left": 16, "right": 8, "top": 0, "bottom": 0}
        if border is not None:
            border(spec)

    widget = Widget(window, fragment_name, {"label": label, "width": width}, theme=theme, x=x, y=y,
                    interactive={None: None}, edit=edit, name="chip")
    widget.selected = Signal(bool(selected))
    if variant == "filter":
        check = widget.part("check")

        def paint() -> None:
            on = widget.selected.get()
            widget.node.set(fill=widget.color("secondary_container") if on else (0, 0, 0, 0),
                            stroke_width=0.0 if on else float(border_width or 1.0),
                            checked=on)
            widget.part("label").set(fill=widget.color("on_secondary_container" if on else "on_surface_variant"))
            if on and check.parent() is None:
                widget.node.insert_child(0, check)
            elif not on and check.parent() is not None:
                check.remove()
            widget.node.set(padding_left=8.0 if on or icon else 16.0)

        effect = Effect(paint)
        widget._undo.append(effect.dispose)
        widget.after_theme(lambda: paint())
        widget.on_click(lambda: widget.selected.set(not widget.selected.get()), role="checkbox")
    if on_click is not None:
        widget.on_click(on_click, role="checkbox" if variant == "filter" else "button")
    if removable:
        remove = widget.part("remove")
        a11y.describe(remove, label=f"Remove {label}")
        widget.on_click(on_remove or (lambda: None), part="remove")
    return widget


def badge(
    window: "Window",
    label: str | None = None,
    width: float | None = None,
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
    *,
    theme: "Theme | None" = None,
) -> Widget:
    """MD3's badge (M41: built from its fragment): a 6 px `error` dot when
    `label=None`, otherwise a 16 px pill with a `label_small` `on_error`
    label (`width` defaults to fit it)."""
    border = _borders([None], border_color, border_width)
    if label is None:
        widget = Widget(window, "BadgeDot", {}, theme=theme, x=x, y=y, edit=border, name="badge")
    else:
        widget = Widget(window, "BadgeLabeled", {"label": label, "width": width if width is not None else 16.0},
                        theme=theme, x=x, y=y, edit=border, name="badge")
        if width is None:  # fit the label: 4 px either side, at least a circle
            widget.node.set(width=max(16.0, widget.part("label").get("width") + 8.0))
    return widget


def divider(
    window: "Window",
    length: float,
    orientation: str = "horizontal",
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
    *,
    theme: "Theme | None" = None,
) -> Widget:
    """MD3's divider (M41: built from its fragment): a 1 px `outline_variant`
    line `length` long. `border_color`/`border_width` recolour or thicken it."""
    if orientation not in ("horizontal", "vertical"):
        raise ValueError(f"a divider's orientation is 'horizontal' or 'vertical', got {orientation!r}")
    thickness = float(border_width) if border_width is not None else 1.0
    size = (length, thickness) if orientation == "horizontal" else (thickness, length)

    def edit(spec: dict[str, Any]) -> None:
        if border_color is not None:
            spec["style"]["background"] = _hex(border_color)

    widget = Widget(window, "Divider", {"width": size[0], "height": size[1]}, theme=theme, x=x, y=y, edit=edit,
                    name="divider")
    a11y.describe(widget.node, hidden=True)
    return widget


def link(
    window: "Window",
    content: str,
    width: float,
    x: float | None = None,
    y: float | None = None,
    *,
    theme: "Theme | None" = None,
    on_click: Callable[[], Any] | None = None,
) -> Widget:
    """A link (M41: built from its fragment): `body_large` text in
    `primary`, `role="link"`, a Tab stop that Enter follows (`on_click`)."""
    widget = Widget(window, "Link", {"text": content, "width": width, "height": 24}, theme=theme, x=x, y=y,
                    name="link")
    if on_click is not None:
        widget.on_click(on_click, role="link")
    return widget


class _Expandable:
    """The expanded state of an accordion header or tree node: a `Signal`
    toggled by a click, Enter or Space; the chevron turns with it; the
    arrow keys (a tree node's) and assistive technology's expand/collapse
    set it."""

    def __init__(self, widget: Widget, expanded: bool, chevron: Any, open_deg: float, closed_deg: float,
                 arrows: bool) -> None:
        widget.expanded = Signal(bool(expanded))
        changes: list[Callable[[bool], Any]] = []
        widget.on_change = lambda fn: (changes.append(fn), lambda: changes.remove(fn) if fn in changes else None)[1]

        def user_set(value: bool) -> None:
            if widget.expanded.get() != value:
                widget.expanded.set(value)
                for fn in list(changes):
                    fn(value)

        painted = [False]

        def paint() -> None:
            on = widget.expanded.get()
            widget.node.set(expanded=on)
            if chevron is not None:
                chevron.animate("rotation_deg", open_deg if on else closed_deg, 150 if painted[0] else 0)
            painted[0] = True

        effect = Effect(paint)
        widget._undo.append(effect.dispose)
        widget.on_click(lambda: user_set(not widget.expanded.get()), role=widget.node.get("role") or "button")
        widget._undo.append(a11y.on_action(widget.node, {"expand": lambda e: user_set(True),
                                                         "collapse": lambda e: user_set(False)},
                                           listen=widget.view._listen))
        if arrows:
            keys = {"arrow_right": True, "arrow_left": False}
            widget._undo.append(widget.view._listen(
                widget.node, "key_down", lambda e: user_set(keys[e.key]) if e.key in keys else None))


def accordion_header(
    window: "Window",
    title: str,
    expanded: bool = False,
    width: float = 360.0,
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
    *,
    theme: "Theme | None" = None,
) -> Widget:
    """An accordion header (M41: built from its fragment): a title and a
    chevron that turns over when `.expanded` (a `Signal`) is on. A click,
    Enter or Space toggles it; `.on_change(fn)` hears the user's toggles.
    Show and hide the content yourself, from `.expanded`."""
    widget = Widget(window, "AccordionHeader", {"title": title, "width": width}, theme=theme, x=x, y=y,
                    interactive={None: "on_surface"}, edit=_borders([None], border_color, border_width),
                    name="accordion_header")
    _Expandable(widget, expanded, widget.part("chevron"), 180.0, 0.0, arrows=False)
    return widget


def tree_node(
    window: "Window",
    title: str,
    depth: int = 0,
    expanded: bool = False,
    leaf: bool = False,
    width: float = 360.0,
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
    *,
    theme: "Theme | None" = None,
) -> Widget:
    """A tree row (M41: built from its fragment), indented 16 px plus 24
    per `depth`, `role="treeitem"` at `level` `depth + 1`. A branch has a
    chevron (pointing right, down when `.expanded`), toggled by a click,
    Enter or Space, and set by the right and left arrows. Build the tree's
    structure yourself, from `.expanded`."""
    padding = 16 + 24 * int(depth)
    widget = Widget(window, "TreeNodeLeaf" if leaf else "TreeNodeBranch",
                    {"title": title, "width": width, "left_padding": padding}, theme=theme, x=x, y=y,
                    interactive={None: "on_surface"}, edit=_borders([None], border_color, border_width),
                    name="tree_node")
    a11y.describe(widget.node, role="treeitem", level=int(depth) + 1)
    if leaf:
        widget.expanded = None
        widget.node.set(focusable=True)
    else:
        _Expandable(widget, expanded, widget.part("chevron"), 0.0, -90.0, arrows=True)
    return widget
