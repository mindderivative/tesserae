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


def graph_node(
    window: "Window",
    graph: "Node",
    label: str,
    x: float,
    y: float,
    width: float,
    height: float,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
) -> "Node":
    """One node inside a `node_graph(...)` canvas. `x`/`y` are graph
    coordinates, not window-absolute."""
    return window.add_graph_node(graph, label, x, y, width, height, border_color=border_color, border_width=border_width)


def node_graph(
    window: "Window",
    width: float,
    height: float,
    x: float | None = None,
    y: float | None = None,
    border_color: tuple[int, int, int, int] | None = None,
    border_width: float | None = None,
) -> "Node":
    """A `Canvas`-backed container for `graph_node(...)` children plus
    app-drawn edges between them."""
    return window.add_node_graph(width, height, x=x, y=y, border_color=border_color, border_width=border_width)
