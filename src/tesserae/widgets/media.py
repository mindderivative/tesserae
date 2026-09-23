"""Tesserae's own namespace for the Media & Graphics category --
`image`, `video`, `icon`, `graph_node`, `node_graph`.

`icon` gets the real naming translation M8 first identified as the true
target: `tre`'s own `add_icon(color=...)` is the glyph's own paint (an
icon has no background of its own -- confirmed directly against
`window_factory.rs`, matching `docs/guide/components.md`'s own "No
`background` param, same reasoning as `Image`" note). Tesserae's own
`icon(...)` calls it `foreground=`, translating internally.

`image`/`video` take no color at all (an image/video's content IS its
own pixels -- no meaningful "behind it" fill). `graph_node`/`node_graph`
only take the already-clear `border_color`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

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
    """Loads and decodes a real file from disk (png/jpeg) at call time,
    uploaded as a GPU texture. `fit`: cover/contain/fill. Raises
    `OSError` if the file can't be read or decoded."""
    return window.add_image(path, width, height, fit=fit, x=x, y=y)


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
    `foreground` (`tre`'s own `add_icon` calls this `color=`, which we
    translate). Currently curated icon names: home/search/menu/close/
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
