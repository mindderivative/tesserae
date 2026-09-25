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

from typing import TYPE_CHECKING

from tesserae.images import decode_image

if TYPE_CHECKING:
    from tre import Node, Window


def image(
    window: "Window",
    path: str,
    width: float,
    height: float,
    fit: str = "fill",
    x: float | None = None,
    y: float | None = None,
) -> "Node":
    """Loads and decodes a real file from disk at call time, uploaded
    as a GPU texture. `fit`: cover/contain/fill. Raises `OSError` if the
    file can't be read or decoded.

    M29 Phase 2: Tesserae decodes the file itself (Pillow) and hands
    `tre` only the pixels, via `add_image_from_bytes` -- `tre` never
    opens the file. The one real departure from `tre`'s own `add_image`
    delegation this module otherwise follows."""
    rgba, pixel_width, pixel_height = decode_image(path)
    return window.add_image_from_bytes(
        rgba, pixel_width, pixel_height, width, height, fit=fit, x=x, y=y
    )


def video(
    window: "Window",
    width: float,
    height: float,
    fit: str = "fill",
    x: float | None = None,
    y: float | None = None,
) -> "Node":
    """Same `fit` contract as `image`; frames are pushed at runtime via
    `node.push_frame(...)`, not loaded from a path at construction."""
    return window.add_video(width, height, fit=fit, x=x, y=y)


def icon(
    window: "Window",
    name: str,
    foreground: tuple[int, int, int, int],
    size: float,
    x: float | None = None,
    y: float | None = None,
) -> "Node":
    """One square `size` glyph, rendered as a vector fill in
    `foreground`. Currently curated icon names: home/search/menu/close/
    check/arrow_back/add/settings/expand_more/remove/arrow_forward/
    chevron_right -- an unknown name raises `ValueError` listing the
    real known set."""
    return window.add_icon(name, foreground, size, x=x, y=y)


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
