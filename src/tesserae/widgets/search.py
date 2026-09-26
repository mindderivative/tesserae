"""Tesserae's own namespace for the Search category -- `search_bar`,
`search_view`. Same thin-delegate shape as the other widget modules.
Neither exposes an ambiguous color kwarg."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Optional

from tesserae.reactive import Signal
from tesserae.widgets._composed import Widget
from tesserae.widgets.buttons import _borders

if TYPE_CHECKING:
    from tesserae.overlays import SearchView
    from tesserae.theme import Theme
    from tre import Node, Window


def search_bar(
    window: "Window",
    placeholder: str,
    width: float,
    leading_icon: str | None = "search",
    trailing_icons: list[str] | None = None,
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
    *,
    theme: "Theme | None" = None,
) -> Widget:
    """MD3's search bar (M42: built from its fragment): a 56 px
    `surface_container_high` pill with elevation, a leading icon
    (`on_surface`), a `body_large` field whose `placeholder` is hint text
    in `on_surface_variant`, and trailing icon buttons
    (`on_surface_variant`). `.query` is a `Signal` of what's typed;
    `.on_query(fn)` hears each change. Parts: `field` (the `text_input`),
    `leading`, `trailing0`, ..."""
    name = "search_bar"
    trailing = list(trailing_icons or [])

    def icon(node_id: str, glyph: str, ink: str, button: bool) -> dict[str, Any]:
        size = 48 if button else 24
        return {"id": node_id, "kind": "Rect",
                "style": {"width": size, "height": size, "corner_radius": size / 2, "background": "transparent",
                          "align_items": "center", "justify_content": "center"},
                "children": [{"id": f"{node_id}.icon", "kind": "Icon", "icon": {"name": glyph},
                              "style": {"width": 24, "height": 24, "foreground": ink}}]}

    border = _borders([None], border_color, border_width)

    def edit(spec: dict[str, Any]) -> None:
        field = spec["children"][0]
        field["text"]["content"] = ""  # the placeholder is hint text, not the field's text (tre's filled it in)
        field["style"]["height"] = 48
        spec["style"].update(gap=16, padding={"left": 16 if leading_icon else 4, "right": 4, "top": 0, "bottom": 0})
        if leading_icon is not None:
            spec["children"].insert(0, icon(f"{name}.leading", leading_icon, "on_surface", button=False))
        for i, glyph in enumerate(trailing):
            spec["children"].append(icon(f"{name}.trailing{i}", glyph, "on_surface_variant", button=True))
        if border is not None:
            border(spec)

    widget = Widget(window, "SearchBar", {"placeholder": placeholder, "width": width, "corner_radius": 28},
                    theme=theme, x=x, y=y, edit=edit, name=name,
                    interactive={f"trailing{i}": None for i in range(len(trailing))})
    field = widget.part("field")

    def paint() -> None:
        field.set(placeholder=placeholder, placeholder_fill=widget.color("on_surface_variant"),
                  fill=widget.color("on_surface"), caret_color=widget.color("primary"),
                  font_size=16.0, label=placeholder)

    paint()
    widget.after_theme(paint)
    for i, glyph in enumerate(trailing):
        node = widget.part(f"trailing{i}")
        node.set(focusable=True, role="button", cursor="pointer", label=glyph)
    widget.query = Signal("")
    queries: list[Callable[[str], Any]] = []

    def typed(event: Any) -> None:
        text = field.get("text") or ""
        widget.query.set(text)
        for fn in list(queries):
            fn(text)

    widget._undo.append(widget.view._listen(field, "change", typed))
    widget.on_query = lambda fn: (queries.append(fn), lambda: queries.remove(fn) if fn in queries else None)[1]
    return widget


def search_view(
    window: "Window",
    width: float,
    height: float,
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
    *,
    bar: Widget | None = None,
    results: list[tuple[str, Optional[Callable[[], Any]]]] | None = None,
    theme: "Theme | None" = None,
) -> "SearchView":
    """MD3's docked search view (M42: `tesserae.overlays.SearchView`): the
    results panel under a `search_bar`, `height` its most. Give it the
    `bar` and it opens and closes with it; `set_results([(text, fn)])`."""
    from tesserae.overlays import SearchView

    view = SearchView(window, bar=bar, width=width, max_height=height, results=results, theme=theme)
    if border_color is not None or border_width is not None:
        view.node.set(**({"stroke_color": tuple(border_color)} if border_color else {}),
                      **({"stroke_width": float(border_width)} if border_width is not None else {}))
    return view
