"""Tesserae's own namespace for the Navigation & Shell Composition
category -- `tabs`, `navigation_rail`, `navigation_drawer`, `toolbar`,
`top_app_bar`, `status_bar`.

Same thin-delegate shape as `buttons.py`/`selection.py`/`structural.py`,
with no naming translation. `toolbar(vibrant=)` matches `tre` 0.3.3's
`add_toolbar(vibrant=)`; before M32, `tre` took a confusing
`color="standard"|"vibrant"` and Tesserae translated its own `tone=` to it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Optional

from tesserae import a11y
from tesserae.reactive import Effect, Signal
from tesserae.theme import Theme
from tesserae.widgets._composed import Widget
from tesserae.widgets.buttons import _borders, _hex, _variant, icon_button

if TYPE_CHECKING:
    from tre import Node, Window


class _Selection:
    """The selected item of tabs, a navigation rail or a drawer (M41):
    `.selected` is a `Signal` (an index, or `None`), a click or Enter
    selects, the arrow keys move the selection and focus (wrapping), and
    the group is one Tab stop, the selected item (else the first).
    `.on_change(fn)` hears the user's selections. `paint(i, on)` draws each
    item's state; `after()` runs once they're drawn."""

    def __init__(self, widget: Widget, count: int, selected: Optional[int], keys: dict[str, int],
                 paint: Callable[[int, bool], None], after: Callable[[], None] = lambda: None) -> None:
        widget.selected = Signal(selected)
        changes: list[Callable[[int], Any]] = []
        widget.on_change = lambda fn: (changes.append(fn), lambda: changes.remove(fn) if fn in changes else None)[1]

        def choose(index: int, focus: bool = False) -> None:
            if widget.selected.get() != index:
                widget.selected.set(index)
                for fn in list(changes):
                    fn(index)
            if focus:
                widget.part(f"item{index}").focus()

        def draw() -> None:
            chosen = widget.selected.get()
            stop = chosen if chosen is not None else 0
            for i in range(count):
                item = widget.part(f"item{i}")
                item.set(selected=i == chosen, focusable=i == stop)
                paint(i, i == chosen)
            after()

        effect = Effect(draw)
        widget._undo.append(effect.dispose)
        widget.after_theme(lambda: draw())
        for i in range(count):
            widget.on_click(lambda i=i: choose(i), part=f"item{i}", role="tab")

            def on_key(event: Any, i: int = i) -> None:
                step = keys.get(event.key)
                if step is not None:
                    choose((i + step) % count, focus=True)
            widget._undo.append(widget.view._listen(widget.part(f"item{i}"), "key_down", on_key))
        draw()


def _check_selected(selected: Optional[int], count: int) -> None:
    if selected is not None and not 0 <= selected < count:
        raise ValueError(f"selected={selected} is out of range for {count} items")


def tabs(
    window: "Window",
    labels: list[str],
    icons: list[str] | None = None,
    selected: int | None = None,
    width: float | None = None,
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
    *,
    theme: "Theme | None" = None,
) -> Widget:
    """MD3's primary tabs (M41): 48 px tall, or 64 with `icons`; the
    labels `title_small`, `primary` when selected and `on_surface_variant`
    otherwise; a 3 px `primary` indicator under the selected label that
    slides to a new one; a 1 px `surface_variant` divider below.
    `.selected` (a `Signal`), `.on_change(fn)`; the left and right arrows
    move the selection. Parts `item0`, `item1`... with `label`/`icon`."""
    count = len(labels)
    if count == 0:
        raise ValueError("tabs need at least one label")
    if icons is not None and len(icons) != count:
        raise ValueError(f"{len(icons)} icons for {count} tabs")
    _check_selected(selected, count)
    total = float(width) if width is not None else 90.0 * count
    item_width = total / count
    height = 64.0 if icons else 48.0
    name = "tabs"
    items = []
    for i, label in enumerate(labels):
        children = [{"id": f"{name}.item{i}.label", "kind": "Text",
                     "text": {"content": label, "typography_role": "title_small"},
                     "style": {"foreground": "on_surface_variant"}}]
        if icons:
            children.insert(0, {"id": f"{name}.item{i}.icon", "kind": "Icon", "icon": {"name": icons[i]},
                                "style": {"width": 24, "height": 24, "foreground": "on_surface_variant"}})
        items.append({"id": f"{name}.item{i}", "kind": "Rect",
                      "style": {"width": item_width, "height": height, "background": "surface",
                                "flex_direction": "vertical", "align_items": "center",
                                "justify_content": "center", "gap": 2},
                      "children": children})
    spec = {"id": name, "kind": "Container",
            "style": {"width": total, "height": height, "flex_direction": "vertical", "background": "surface"},
            "children": [
                {"id": f"{name}.row", "kind": "Container", "style": {"flex_direction": "horizontal"}, "children": items},
                {"id": f"{name}.divider", "kind": "Rect", "style": {"width": total, "height": 1,
                                                                   "background": "surface_variant"}},
            ]}
    widget = Widget(window, spec=spec, theme=theme, x=x, y=y,
                    interactive={f"item{i}": "primary" for i in range(count)},
                    edit=_borders([None], border_color, border_width), name=name)
    a11y.describe(widget.part("row"), role="tablist")
    indicator = window.create("box", position="absolute", x=0.0, y=height - 3.0, width=0.0, height=3.0,
                              corner_radius=(3.0, 3.0, 0.0, 0.0), hit_testable=False, a11y_hidden=True)
    widget.node.add_child(indicator)
    widget.indicator = indicator
    moved = [False]

    def paint(i: int, on: bool) -> None:
        ink = widget.color("primary" if on else "on_surface_variant")
        widget.part(f"item{i}.label").set(fill=ink)
        if icons:
            widget.part(f"item{i}.icon").set(fill=ink)

    def place_indicator() -> None:
        chosen = widget.selected.get()
        indicator.set(fill=widget.color("primary"), visible=chosen is not None)
        if chosen is None:
            return
        label = widget.part(f"item{chosen}.label")
        span = max(label.get("width") or 0.0, 24.0)  # MD3: the indicator spans the label
        offset = chosen * item_width + (item_width - span) / 2
        indicator.set(width=span)
        if moved[0]:
            indicator.animate("translate_x", offset, Theme.duration("medium2"), easing=Theme.easing("emphasized"))
        else:
            indicator.stop_animation("translate_x")
            indicator.set(translate_x=offset)
        moved[0] = True

    _Selection(widget, count, selected, {"arrow_right": 1, "arrow_left": -1}, paint, place_indicator)
    return widget


def navigation_rail(
    window: "Window",
    labels: list[str],
    icons: list[str],
    selected: int | None = None,
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
    *,
    theme: "Theme | None" = None,
) -> Widget:
    """MD3's navigation rail (M41): 80 px wide on `surface`, each item a
    24 px icon over a `label_medium` label; the selected item's icon sits
    in a 56x32 `secondary_container` pill, in `on_secondary_container`.
    `.selected`, `.on_change(fn)`; the up and down arrows move it."""
    count = len(labels)
    if count == 0 or len(icons) != count:
        raise ValueError(f"a navigation rail needs a label and an icon per item, got {count} and {len(icons)}")
    _check_selected(selected, count)
    name = "navigation_rail"
    items = []
    for i, (label, glyph) in enumerate(zip(labels, icons)):
        items.append({"id": f"{name}.item{i}", "kind": "Container",
                      "style": {"width": 80, "height": 56, "flex_direction": "vertical", "align_items": "center",
                                "gap": 4},
                      "children": [
                          {"id": f"{name}.item{i}.pill", "kind": "Rect",
                           "style": {"width": 56, "height": 32, "corner_radius": 16, "background": "transparent",
                                     "align_items": "center", "justify_content": "center"},
                           "children": [{"id": f"{name}.item{i}.icon", "kind": "Icon", "icon": {"name": glyph},
                                         "style": {"width": 24, "height": 24,
                                                   "foreground": "on_surface_variant"}}]},
                          {"id": f"{name}.item{i}.label", "kind": "Text",
                           "text": {"content": label, "typography_role": "label_medium"},
                           "style": {"foreground": "on_surface_variant"}}]})
    spec = {"id": name, "kind": "Container",
            "style": {"width": 80, "flex_direction": "vertical", "align_items": "center", "gap": 12,
                      "padding": {"left": 0, "right": 0, "top": 12, "bottom": 12}, "background": "surface"},
            "children": items}
    widget = Widget(window, spec=spec, theme=theme, x=x, y=y,
                    interactive={f"item{i}.pill": "on_surface" for i in range(count)},
                    edit=_borders([None], border_color, border_width), name=name)
    a11y.describe(widget.node, role="tablist")

    def paint(i: int, on: bool) -> None:
        widget.part(f"item{i}.pill").set(fill=widget.color("secondary_container") if on else (0, 0, 0, 0))
        widget.part(f"item{i}.icon").set(fill=widget.color("on_secondary_container" if on else "on_surface_variant"))
        widget.part(f"item{i}.label").set(fill=widget.color("on_surface" if on else "on_surface_variant"))

    _Selection(widget, count, selected, {"arrow_down": 1, "arrow_up": -1}, paint)
    return widget


def navigation_drawer(
    window: "Window",
    labels: list[str],
    icons: list[str],
    selected: int | None = None,
    modal: bool = False,
    width: float = 360.0,
    height: float | None = None,
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
    *,
    theme: "Theme | None" = None,
) -> Widget:
    """MD3's navigation drawer (M41): `surface_container_low`, 12 px in,
    each item 56 px with a 24 px icon and a `label_large` label; the
    selected one a full-width `secondary_container` pill. `modal=True` is
    the modal drawer's look (rounded on its end side); open it as an
    overlay with `tesserae.overlays` (M41 Phase 5). `.selected`,
    `.on_change(fn)`; the up and down arrows move it."""
    count = len(labels)
    if count == 0 or len(icons) != count:
        raise ValueError(f"a navigation drawer needs a label and an icon per item, got {count} and {len(icons)}")
    _check_selected(selected, count)
    name = "navigation_drawer"
    inner = float(width) - 24.0
    items = [{"id": f"{name}.item{i}", "kind": "Rect",
              "style": {"width": inner, "height": 56, "corner_radius": 28, "background": "transparent",
                        "flex_direction": "horizontal", "align_items": "center", "gap": 12,
                        "padding": {"left": 16, "right": 24, "top": 0, "bottom": 0}},
              "children": [
                  {"id": f"{name}.item{i}.icon", "kind": "Icon", "icon": {"name": glyph},
                   "style": {"width": 24, "height": 24, "foreground": "on_surface_variant"}},
                  {"id": f"{name}.item{i}.label", "kind": "Text",
                   "text": {"content": label, "typography_role": "label_large"},
                   "style": {"foreground": "on_surface_variant"}}]}
             for i, (label, glyph) in enumerate(zip(labels, icons))]
    style = {"width": float(width), "flex_direction": "vertical", "padding": 12, "background": "surface_container_low"}
    if height is not None:
        style["height"] = float(height)
    spec = {"id": name, "kind": "Container", "style": style, "children": items}
    widget = Widget(window, spec=spec, theme=theme, x=x, y=y,
                    interactive={f"item{i}": "on_surface" for i in range(count)},
                    edit=_borders([None], border_color, border_width), name=name)
    if modal:
        # MD3: rounded where it meets the content (a style takes one radius, so set here, and after re-colouring)
        def round_end() -> None:
            widget.node.set(corner_radius=(0.0, 16.0, 16.0, 0.0))
        round_end()
        widget.after_theme(round_end)
    widget.modal = modal
    a11y.describe(widget.node, role="tablist")

    def paint(i: int, on: bool) -> None:
        widget.part(f"item{i}").set(fill=widget.color("secondary_container") if on else (0, 0, 0, 0))
        ink = widget.color("on_secondary_container" if on else "on_surface_variant")
        widget.part(f"item{i}.icon").set(fill=ink)
        widget.part(f"item{i}.label").set(fill=ink)

    _Selection(widget, count, selected, {"arrow_down": 1, "arrow_up": -1}, paint)
    return widget


def toolbar(
    window: "Window",
    variant: str = "docked",
    orientation: str | None = None,
    vibrant: bool = False,
    width: float | None = None,
    height: float | None = None,
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
    *,
    theme: "Theme | None" = None,
) -> Widget:
    """MD3's toolbar (M41: built from its fragment), for action icon
    buttons: add them to `.node`. `docked` spans its width, 64 px tall;
    `floating` is a pill with elevation, horizontal or vertical. Standard
    `surface_container`, or `vibrant` `primary_container`."""
    fragment_name = _variant("toolbar", variant, {"docked": "ToolbarDocked", "floating": "ToolbarFloating"})
    if orientation not in (None, "horizontal", "vertical"):
        raise ValueError(f"a toolbar's orientation is 'horizontal' or 'vertical', got {orientation!r}")
    background = "primary_container" if vibrant else "surface_container"
    vertical = orientation == "vertical"
    params: dict[str, Any] = {"background": background, "width": width if width is not None else (64 if vertical else 360)}
    if variant == "floating":
        params["corner_radius"] = 32
    border = _borders([None], border_color, border_width)

    def edit(spec: dict[str, Any]) -> None:
        if vertical:
            spec["style"].update(flex_direction="vertical", height=height if height is not None else 360, width=64)
        elif height is not None:
            spec["style"]["height"] = height
        if border is not None:
            border(spec)

    widget = Widget(window, fragment_name, params, theme=theme, x=x, y=y, edit=edit, name="toolbar")
    a11y.describe(widget.node, role="group")
    widget.vibrant = vibrant
    return widget


def top_app_bar(
    window: "Window",
    title: str,
    leading_icon: str | None = None,
    trailing_icons: list[str] | None = None,
    width: float | None = None,
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
    *,
    theme: "Theme | None" = None,
) -> Widget:
    """MD3's small top app bar (M41: built from its fragment): 64 px of
    `surface`, a `title_large` title, an optional leading icon button
    (`on_surface`) and trailing ones (`on_surface_variant`), each 48 px.
    Parts: `title`, `leading`, `trailing0`, ...; wire them with
    `on_click(fn, part="leading")`."""
    name = "top_app_bar"
    trailing = list(trailing_icons or [])

    def button(node_id: str, glyph: str, ink: str) -> dict[str, Any]:
        return {"id": node_id, "kind": "Rect",
                "style": {"width": 48, "height": 48, "corner_radius": 24, "background": "transparent",
                          "align_items": "center", "justify_content": "center"},
                "children": [{"id": f"{node_id}.icon", "kind": "Icon", "icon": {"name": glyph},
                              "style": {"width": 24, "height": 24, "foreground": ink}}]}

    border = _borders([None], border_color, border_width)

    def edit(spec: dict[str, Any]) -> None:
        if leading_icon is not None:
            spec["children"].insert(0, button(f"{name}.leading", leading_icon, "on_surface"))
            spec["children"][1]["style"]["margin"] = {"left": 4, "right": 0, "top": 0, "bottom": 0}
        for i, glyph in enumerate(trailing):
            spec["children"].append(button(f"{name}.trailing{i}", glyph, "on_surface_variant"))
        if border is not None:
            border(spec)

    parts = (["leading"] if leading_icon else []) + [f"trailing{i}" for i in range(len(trailing))]
    widget = Widget(window, "TopAppBar", {"title": title, "width": width if width is not None else 360},
                    theme=theme, x=x, y=y, interactive={p: None for p in parts}, edit=edit, name=name)
    for part in parts:
        node = widget.part(part)
        node.set(focusable=True, role="button", cursor="pointer")
        a11y.describe(node, label=leading_icon if part == "leading" else trailing[int(part[8:])])
    return widget


def status_bar(
    window: "Window",
    text: str,
    width: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
    *,
    theme: "Theme | None" = None,
) -> Widget:
    """A window-bottom status strip (M41: built from its fragment): 24 px
    of `surface_container` with `label_small` text in
    `on_surface_variant`, announced politely when its text changes."""
    widget = Widget(window, "StatusBar", {"text": text, "width": width if width is not None else 360},
                    theme=theme, edit=_borders([None], border_color, border_width), name="status_bar")
    a11y.describe(widget.node, live="polite")
    return widget
