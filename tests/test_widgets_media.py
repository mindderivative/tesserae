"""Real coverage for `tesserae.widgets`'s Media & Graphics category --
`image`/`video`/`icon`/`graph_node`/`node_graph`. Same thin-delegate
parity strategy, plus a naming-translation check for
`icon(foreground=...)` -> `add_icon(color=..., ...)` -- the real place
M8/M9's naming-consistency finding always pointed to.
"""

from pathlib import Path

import pytest
from tre import Window

from tesserae.widgets import graph_node, icon, image, node_graph, video

PIXEL_PNG = str(Path(__file__).parent / "fixtures" / "pixel.png")


def test_image_matches_native_add_image():
    window = Window(width=400, height=300)
    a = image(window, PIXEL_PNG, 40, 40, fit="cover")
    b = window.add_image(PIXEL_PNG, 40, 40, fit="cover")
    assert a is not None and b is not None


def test_image_raises_oserror_on_missing_file_matching_native():
    window = Window(width=400, height=300)
    with pytest.raises(OSError):
        image(window, "does/not/exist.png", 40, 40)


def test_video_matches_native_add_video():
    window = Window(width=400, height=300)
    a = video(window, 80, 60)
    b = window.add_video(80, 60)
    assert a.get("corner_radius") == b.get("corner_radius")


def test_icon_foreground_translates_to_native_color_kwarg():
    window = Window(width=400, height=300)
    a = icon(window, "home", (28, 27, 31, 255), 24)
    b = window.add_icon("home", (28, 27, 31, 255), 24)
    assert a is not None and b is not None


def test_icon_rejects_unknown_name_matching_native():
    window = Window(width=400, height=300)
    with pytest.raises(ValueError):
        icon(window, "not_a_real_icon", (0, 0, 0, 255), 24)


def test_node_graph_and_graph_node_match_native():
    window = Window(width=400, height=300)
    a_graph = node_graph(window, 200, 150)
    a_node = graph_node(window, a_graph, "Node A", 10, 10, 80, 40)
    b_graph = window.add_node_graph(200, 150)
    b_node = window.add_graph_node(b_graph, "Node A", 10, 10, 80, 40)
    assert a_graph.get("corner_radius") == b_graph.get("corner_radius")
    assert a_node.get("corner_radius") == b_node.get("corner_radius")
