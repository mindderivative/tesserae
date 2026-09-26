"""Tesserae's own namespace for the Media & Graphics category --
`image`, `video`, `icon`, `graph_node`, `node_graph`.

`icon(foreground=)` is the glyph's own paint (an icon has no background
of its own). `tre` 0.3.3 uses the same name, so it passes straight
through; before M32, `tre` called it `color=` and Tesserae translated.

`image`/`video` take no color at all (an image/video's content IS its
own pixels -- no meaningful "behind it" fill). `graph_node`/`node_graph`
only take the already-clear `border_color`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from tesserae.images import decode_image

if TYPE_CHECKING:
    from tesserae.theme import Theme
    from tesserae.widgets._composed import Widget
    from tre import Node, Window


def _image_spec(node_id: str, width: float, height: float, fit: str) -> dict[str, Any]:
    if fit not in ("cover", "contain", "fill"):
        raise ValueError(f"an image's fit is 'cover', 'contain' or 'fill', got {fit!r}")
    return {"id": node_id, "kind": "Image", "image": {"fit": fit}, "style": {"width": width, "height": height}}


def image(
    window: "Window",
    path: str,
    width: float,
    height: float,
    fit: str = "fill",
    x: float | None = None,
    y: float | None = None,
    *,
    label: str | None = None,
) -> "Widget":
    """An image from a file, `width`x`height`, `fit` cover, contain or
    fill. Tesserae decodes the file (Pillow) and M42 builds the node itself
    (`window.create("image")` with the pixels), off `tre`'s
    `add_image_from_bytes`, which 0.3.5 removes. Raises `OSError` if the
    file can't be read or decoded. Decorative unless given `label=`, then
    `role="img"`."""
    from tesserae import a11y
    from tesserae.widgets._composed import Widget

    rgba, pixel_width, pixel_height = decode_image(path)
    widget = Widget(window, spec=_image_spec("image", width, height, fit), x=x, y=y, name="image",
                    frames={"image": (rgba, pixel_width, pixel_height)})
    a11y.describe(widget.node, **({"role": "img", "label": label} if label is not None else {"hidden": True}))
    return widget


def video(
    window: "Window",
    width: float,
    height: float,
    fit: str = "fill",
    x: float | None = None,
    y: float | None = None,
    *,
    label: str | None = None,
) -> "Widget":
    """A surface for video frames (M42: an `image` node Tesserae builds,
    off `tre`'s `add_video`). `video.frame(rgba, width, height)` shows a
    frame (RGBA bytes, `width*height*4` of them); frames can change size.
    It starts blank. Decorative unless given `label=`."""
    from tesserae import a11y
    from tesserae.widgets._composed import Widget

    widget = Widget(window, spec=_image_spec("video", width, height, fit), x=x, y=y, name="video",
                    frames={"video": (bytes(4), 1, 1)})
    a11y.describe(widget.node, **({"role": "img", "label": label} if label is not None else {"hidden": True}))

    def frame(rgba: bytes, frame_width: int, frame_height: int) -> None:
        if len(rgba) != int(frame_width) * int(frame_height) * 4:
            raise ValueError(f"a {frame_width}x{frame_height} frame is {frame_width * frame_height * 4} bytes of "
                             f"RGBA, got {len(rgba)}")
        widget.node.set(rgba=bytes(rgba), pixel_width=int(frame_width), pixel_height=int(frame_height))
        # a re-colour re-applies the view's frames: keep the latest there
        widget.view._frames["video"] = (bytes(rgba), int(frame_width), int(frame_height))

    widget.frame = frame
    return widget


def icon(
    window: "Window",
    name: str,
    foreground: tuple[int, int, int, int],
    size: float,
    x: float | None = None,
    y: float | None = None,
    *,
    theme: "Theme | None" = None,
    label: str | None = None,
) -> "Widget":
    """One of Tesserae's icons (`tesserae.icons`: home, search, menu,
    close, check, arrow_back, add, settings, expand_more, remove,
    arrow_forward, chevron_right), `size` square in `foreground`. M41:
    Tesserae's own Icon, not `tre`'s. An unknown name raises `ValueError`.
    Decorative unless given a `label=`."""
    from tesserae import a11y
    from tesserae.icons import icon_path
    from tesserae.widgets._composed import Widget
    from tesserae.widgets.buttons import _hex

    if icon_path(name) is None:
        from tesserae.icons import ICONS

        raise ValueError(f"unknown icon {name!r}; expected one of {sorted(ICONS)}")
    widget = Widget(window, spec={"id": "icon", "kind": "Icon", "icon": {"name": name},
                                  "style": {"width": size, "height": size, "foreground": _hex(foreground)}},
                    theme=theme, x=x, y=y, name="icon")
    a11y.describe(widget.node, **({"label": label, "role": "img"} if label is not None else {"hidden": True}))
    return widget


#: `node_graph`'s zoom range, and how far one wheel notch zooms.
ZOOM_RANGE = (0.25, 4.0)
ZOOM_STEP = 1.1
#: The coordinate space an edge's `path` spans, centred on the graph's origin.
_EDGE_SPACE = 20000.0


def node_graph(
    window: "Window",
    width: float,
    height: float,
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
    *,
    theme: "Theme | None" = None,
) -> "Widget":
    """A node graph's viewport (M42: built from its fragment, off `tre`'s
    `add_node_graph`): a clipped `surface_container_low` area whose
    content pans and zooms. Drag the background to pan; the wheel zooms
    about the pointer (`ZOOM_RANGE`). `.offset` (x, y) and `.zoom` are
    `Signal`s. Add nodes with `graph_node(window, graph, ...)` and connect
    them with `graph.edge(a, b)`. `.content` holds them."""
    from tesserae import a11y
    from tesserae.reactive import Effect, Signal
    from tesserae.widgets._composed import Widget
    from tesserae.widgets.buttons import _borders

    widget = Widget(window, "NodeGraph", {"width": width, "height": height}, theme=theme, x=x, y=y,
                    edit=_borders([None], border_color, border_width), name="node_graph")
    viewport = widget.node
    viewport.set(clip_children=True)
    a11y.describe(viewport, role="group", label="Node graph")
    # a 0x0 box scales about its own origin, so a graph point p shows at offset + p * zoom
    content = window.create("box", position="absolute", x=0.0, y=0.0, width=0.0, height=0.0, hit_testable=False)
    edges = window.create("box", position="absolute", x=0.0, y=0.0, width=0.0, height=0.0, hit_testable=False,
                          a11y_hidden=True)
    content.add_child(edges)
    viewport.add_child(content)
    widget.content, widget._edges_layer = content, edges
    widget.offset, widget.zoom = Signal((0.0, 0.0)), Signal(1.0)
    widget.graph_nodes: list[Any] = []
    widget.edges: list[tuple[Any, Any, Any]] = []

    def apply() -> None:
        ox, oy = widget.offset.get()
        content.set(translate_x=float(ox), translate_y=float(oy), scale=float(widget.zoom.get()))

    effect = Effect(apply)
    widget._undo.append(effect.dispose)
    drag: dict[str, Any] = {}

    def in_a_node(target: Any) -> bool:
        node = target
        while node is not None and node != viewport:
            if any(node == n.node for n in widget.graph_nodes):
                return True
            node = node.parent()
        return False

    def down(event: Any) -> None:
        if event.window_x is None or in_a_node(event.target):
            return
        drag.update(start=(event.window_x, event.window_y), offset=widget.offset.get())
        viewport.capture_pointer()

    def move(event: Any) -> None:
        if drag and event.window_x is not None:
            (sx, sy), (ox, oy) = drag["start"], drag["offset"]
            widget.offset.set((ox + event.window_x - sx, oy + event.window_y - sy))

    def up(event: Any) -> None:
        if drag:
            drag.clear()
            viewport.release_pointer()

    def wheel(event: Any) -> None:
        if event.delta_y is None or event.x is None:
            return
        zoom = widget.zoom.get()
        target = min(max(zoom * ZOOM_STEP ** (-float(event.delta_y)), ZOOM_RANGE[0]), ZOOM_RANGE[1])
        if target == zoom:
            return
        # keep the graph point under the pointer where it is
        ox, oy = widget.offset.get()
        ratio = target / zoom
        widget.offset.set((event.x - (event.x - ox) * ratio, event.y - (event.y - oy) * ratio))
        widget.zoom.set(target)

    listen = widget.view._listen
    for name, fn in (("pointer_down", down), ("pointer_move", move), ("pointer_up", up), ("wheel", wheel)):
        widget._undo.append(listen(viewport, name, fn))

    def route(a: Any, b: Any, path: Any) -> None:
        (ax, ay), (bx, by) = a.position.get(), b.position.get()
        x1, y1 = ax + a.size[0], ay + a.size[1] / 2
        x2, y2 = bx, by + b.size[1] / 2
        bend = max(40.0, abs(x2 - x1) / 2)
        path.set(data=f"M{x1:.2f},{y1:.2f} C{x1 + bend:.2f},{y1:.2f} {x2 - bend:.2f},{y2:.2f} {x2:.2f},{y2:.2f}")

    def edge(a: Any, b: Any) -> Any:
        """A curve from `a`'s right side to `b`'s left, following them as
        they move. Returns its `path` node."""
        half = _EDGE_SPACE / 2
        path = window.create("path", position="absolute", x=-half, y=-half, width=_EDGE_SPACE, height=_EDGE_SPACE,
                             view_box=(-half, -half, _EDGE_SPACE, _EDGE_SPACE), fill=(0, 0, 0, 0),
                             stroke_width=2.0, stroke_color=widget.color("outline"), hit_testable=False,
                             a11y_hidden=True, data="M0,0")
        edges.add_child(path)
        widget.edges.append((a, b, path))
        route(a, b, path)
        return path

    def reroute(moved: Any) -> None:
        for a, b, path in widget.edges:
            if moved is a or moved is b:
                route(a, b, path)

    widget.edge = edge
    widget._reroute = reroute
    widget.after_theme(lambda: [p.set(stroke_color=widget.color("outline")) for _, _, p in widget.edges])
    return widget


def graph_node(
    window: "Window",
    graph: "Widget",
    label: str,
    x: float,
    y: float,
    width: float,
    height: float,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
    *,
    theme: "Theme | None" = None,
) -> "Widget":
    """A node in a `node_graph` (M42, off `tre`'s `add_graph_node`): a
    `surface_container_high` card with 12 px corners and an
    `outline_variant` border, a 32 px `title_small` title bar
    (`surface_container_highest`) over its body, at `x`, `y` in the
    graph's coordinates. Drag it to move it (its edges follow); focused,
    the arrow keys move it 8 px. `.position` (x, y) is a `Signal`, and
    `.on_move(fn)` hears the user's moves. Put content in `.part("body")`."""
    from tesserae import a11y
    from tesserae.reactive import Effect, Signal
    from tesserae.widgets._composed import Widget
    from tesserae.widgets.buttons import _borders

    name = "graph_node"
    spec = {"id": name, "kind": "Container",
            "style": {"width": width, "height": height, "flex_direction": "vertical",
                      "background": "surface_container_high", "corner_radius": "medium",
                      "border_color": "outline_variant", "border_width": 1.0},
            "children": [
                {"id": f"{name}.title", "kind": "Container",
                 "style": {"height": 32, "background": "surface_container_highest", "align_items": "center",
                           "padding": {"left": 12, "right": 12, "top": 0, "bottom": 0}},
                 "children": [{"id": f"{name}.label", "kind": "Text",
                               "text": {"content": label, "typography_role": "title_small"},
                               "style": {"foreground": "on_surface"}}]},
                {"id": f"{name}.body", "kind": "Container", "style": {"flex_grow": 1}},
            ]}
    widget = Widget(window, spec=spec, theme=theme if theme is not None else graph.theme, name=name, attach=False,
                    edit=_borders([None], border_color, border_width))
    node = widget.node
    node.set(position="absolute", clip_children=True, focusable=True, cursor="grab")
    a11y.describe(node, role="group", label=label)
    graph.content.add_child(node)
    graph.graph_nodes.append(widget)
    widget.graph = graph
    widget.size = (float(width), float(height))
    widget.position = Signal((float(x), float(y)))
    moves: list[Any] = []
    widget.on_move = lambda fn: (moves.append(fn), lambda: moves.remove(fn) if fn in moves else None)[1]

    def place() -> None:
        px, py = widget.position.get()
        node.set(x=float(px), y=float(py))
        graph._reroute(widget)

    effect = Effect(place)  # a re-colour leaves it: its place isn't in its style
    widget._undo.append(effect.dispose)

    def user_move(to: tuple[float, float]) -> None:
        if widget.position.get() != to:
            widget.position.set(to)
            for fn in list(moves):
                fn(to)

    drag: dict[str, Any] = {}

    def down(event: Any) -> None:
        if event.window_x is None:
            return
        drag.update(start=(event.window_x, event.window_y), position=widget.position.get())
        node.capture_pointer()
        node.set(cursor="grabbing")

    def move(event: Any) -> None:
        if drag and event.window_x is not None:
            (sx, sy), (px, py) = drag["start"], drag["position"]
            zoom = graph.zoom.get()
            user_move((px + (event.window_x - sx) / zoom, py + (event.window_y - sy) / zoom))

    def up(event: Any) -> None:
        if drag:
            drag.clear()
            node.release_pointer()
            node.set(cursor="grab")

    def key(event: Any) -> None:
        step = {"arrow_left": (-8, 0), "arrow_right": (8, 0), "arrow_up": (0, -8), "arrow_down": (0, 8)}.get(event.key)
        if step is not None:
            px, py = widget.position.get()
            user_move((px + step[0], py + step[1]))

    listen = widget.view._listen
    for event_name, fn in (("pointer_down", down), ("pointer_move", move), ("pointer_up", up), ("key_down", key)):
        widget._undo.append(listen(node, event_name, fn))
    return widget
