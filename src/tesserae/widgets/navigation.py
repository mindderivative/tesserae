"""Tesserae's own namespace for the Navigation & Shell Composition
category -- `tabs`, `navigation_rail`, `navigation_drawer`, `toolbar`,
`top_app_bar`, `status_bar` (M41) and `pagination` (M42), built by
Tesserae, the fixed-shape ones from their fragments.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Optional

from tesserae import a11y
from tesserae.follow import app_of
from tesserae.reactive import Effect, Signal, ViewModel
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
    overlay with `tesserae.overlays.NavigationDrawer`. `.selected`,
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


#: A disabled control's content: `on_surface` at 38% (MD3).
DISABLED_ALPHA = round(0.38 * 255)


def pagination(
    window: "Window",
    page_count: int,
    current: int = 0,
    x: float | None = None,
    y: float | None = None,
    *,
    max_visible: int = 7,
    theme: "Theme | None" = None,
) -> Widget:
    """Previous, a numbered button per page, and next (M42): 40 px circles
    4 px apart, `label_large` numbers in `on_surface_variant`, the current
    page `primary` with an `on_primary` number. `.current` is a `Signal`
    (0-based) and `.on_change(fn)` hears the user's moves. Previous and
    next are disabled at the first and last page (`on_surface` at 38%, not
    focusable, announced disabled). Parts `previous`, `page0`, ...,
    `next`.

    More than `max_visible` pages (at least 5) are windowed (M62): that
    many slots, `slot0`, ..., show the first and last pages, the current
    one amid its neighbours, and an inert `…` for each run left out
    (`1 … 6 7 [8] 9 10 … 42`), redrawn as the page moves. `.shown` is
    each slot's page, `None` for an ellipsis."""
    if page_count < 1:
        raise ValueError(f"pagination needs at least one page, got {page_count}")
    if not 0 <= current < page_count:
        raise ValueError(f"current={current} is out of range for {page_count} pages")
    if not isinstance(max_visible, int) or max_visible < 5:
        raise ValueError(f"max_visible is a whole number of at least 5, got {max_visible!r}")
    name = "pagination"
    windowed = page_count > max_visible
    slots = max_visible if windowed else page_count
    slot = "slot" if windowed else "page"

    def circle(part: str, child: dict[str, Any]) -> dict[str, Any]:
        return {"id": f"{name}.{part}", "kind": "Rect",
                "style": {"width": 40, "height": 40, "corner_radius": 20, "background": "transparent",
                          "align_items": "center", "justify_content": "center"},
                "children": [child]}

    def arrow(part: str) -> dict[str, Any]:  # `chevron_right`, turned for previous
        return circle(part, {"id": f"{name}.{part}.icon", "kind": "Icon", "icon": {"name": "chevron_right"},
                             "style": {"width": 24, "height": 24, "foreground": "on_surface_variant"}})

    pages = [circle(f"{slot}{i}", {"id": f"{name}.{slot}{i}.label", "kind": "Text",
                                   "text": {"content": str(i + 1), "typography_role": "label_large"},
                                   "style": {"foreground": "on_surface_variant"}}) for i in range(slots)]
    spec = {"id": name, "kind": "Container",
            "style": {"flex_direction": "horizontal", "align_items": "center", "gap": 4},
            "children": [arrow("previous"), *pages, arrow("next")]}
    parts = ["previous", *(f"{slot}{i}" for i in range(slots)), "next"]
    widget = Widget(window, spec=spec, theme=theme, x=x, y=y,
                    interactive={p: "on_surface_variant" for p in parts}, name=name)
    a11y.describe(widget.node, role="group", label="Pagination")
    widget.current = Signal(current)
    changes: list[Callable[[int], Any]] = []
    widget.on_change = lambda fn: (changes.append(fn), lambda: changes.remove(fn) if fn in changes else None)[1]

    def go(page: int | None) -> None:
        if page is None or not 0 <= page < page_count or page == widget.current.get():
            return
        focused = any(widget.part(f"{slot}{k}").get("focused") for k in range(slots))
        widget.current.set(page)
        if focused:  # the page may have moved to another slot: focus follows it
            widget.part(f"{slot}{widget.shown.index(page)}").focus()
        for fn in list(changes):
            fn(page)

    def draw() -> None:
        now = widget.current.get()
        widget.shown = _pages_shown(page_count, now, slots)
        for k, page in enumerate(widget.shown):
            on = page == now
            node = widget.part(f"{slot}{k}")
            node.set(fill=widget.color("primary") if on else (0, 0, 0, 0), selected=on)
            widget.part(f"{slot}{k}.label").set(fill=widget.color("on_primary" if on else "on_surface_variant"))
            if windowed:  # a slot's page changes as the current page moves; an ellipsis is inert
                gap = page is None
                widget.part(f"{slot}{k}.label").set(text="…" if gap else str(page + 1))
                node.set(focusable=not gap, a11y_hidden=gap, cursor="default" if gap else "pointer",
                         label="" if gap else f"Page {page + 1}")
                widget.interaction(f"{slot}{k}").enabled = not gap
        for part, enabled in (("previous", now > 0), ("next", now < page_count - 1)):
            ink = widget.color("on_surface_variant")
            if not enabled:
                r, g, b, _ = widget.color("on_surface")
                ink = (r, g, b, DISABLED_ALPHA)
            widget.part(part).set(focusable=enabled, disabled=not enabled,
                                  cursor="pointer" if enabled else "default")
            widget.part(f"{part}.icon").set(fill=ink)
            widget.interaction(part).enabled = enabled

    widget.on_click(lambda: go(widget.current.get() - 1), part="previous")
    widget.on_click(lambda: go(widget.current.get() + 1), part="next")
    a11y.describe(widget.part("previous"), label="Previous page")
    a11y.describe(widget.part("next"), label="Next page")
    for k in range(slots):
        widget.on_click(lambda k=k: go(widget.shown[k]), part=f"{slot}{k}")
        a11y.describe(widget.part(f"{slot}{k}"), label=f"Page {k + 1}")
    effect = Effect(draw)  # after `on_click`, which makes previous and next focusable
    widget._undo.append(effect.dispose)
    widget.part("previous.icon").set(rotation_deg=180.0)  # not a style property, so a re-colour keeps it
    widget.after_theme(draw)
    return widget


def _pages_shown(page_count: int, current: int, slots: int) -> list[int | None]:
    """Each of `slots` slots' page, `None` for an ellipsis (M62): every page
    if they fit; else the first and last, the current page centred in a
    run of `slots - 4`, and an ellipsis for each run left out. At either
    end the run joins the first or last page instead, so an ellipsis never
    stands for a single page."""
    if page_count <= slots:
        return list(range(page_count))
    run = slots - 4
    start = current - (run - 1) // 2
    if start <= 2:  # near the start: 1 2 3 4 5 … 42
        return [*range(slots - 2), None, page_count - 1]
    if start + run - 1 >= page_count - 3:  # near the end: 1 … 38 39 40 41 42
        return [0, None, *range(page_count - (slots - 2), page_count)]
    return [0, None, *range(start, start + run), None, page_count - 1]


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
    window_controls: bool | None = None,
) -> Widget:
    """MD3's small top app bar (M41: built from its fragment): 64 px of
    `surface`, a `title_large` title, an optional leading icon button
    (`on_surface`) and trailing ones (`on_surface_variant`), each 48 px.
    Parts: `title`, `leading`, `trailing0`, ...; wire them with
    `on_click(fn, part="leading")`.

    `window_controls` (0.3.0 M4) makes it the window's title bar: a drag
    region, with the window buttons after its trailing icons and, on
    macOS, room for the traffic lights -- a `TitleBar`'s
    (`tesserae.spec.title_bar.window_parts`). It defaults to whether the
    app's window is undecorated, so an app shell's top bar is the title
    bar of an `App(decorations=False)`."""
    name = "top_app_bar"
    app = app_of(window)
    if window_controls is None:
        window_controls = app is not None and not app.decorations
    if window_controls and app is None:
        raise ValueError("top_app_bar: window_controls needs the window to be an App's")
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
        if window_controls:
            from tesserae.spec.title_bar import _DIM, window_parts

            inset, controls = window_parts(name)
            spec["window_region"] = "drag"
            spec["children"].insert(0, inset)
            spec["children"].append(controls)
            title = next(c for c in spec["children"] if c.get("id") == f"{name}.title")
            title.setdefault("bindings", {})["opacity"] = _DIM
        if border is not None:
            border(spec)

    parts = (["leading"] if leading_icon else []) + [f"trailing{i}" for i in range(len(trailing))]
    widget = Widget(window, "TopAppBar", {"title": title, "width": width if width is not None else 360},
                    theme=theme, x=x, y=y, interactive={p: None for p in parts}, edit=edit, name=name)
    for part in parts:
        node = widget.part(part)
        node.set(focusable=True, role="button", cursor="pointer")
        a11y.describe(node, label=leading_icon if part == "leading" else trailing[int(part[8:])])
    if window_controls:
        widget.viewmodel = ViewModel(widget.view)  # wires the window parts' bindings and handlers to the app
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
