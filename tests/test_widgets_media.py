"""`tesserae.widgets`'s Media & Graphics category: `image`'s missing-file
error, and `node_graph`/`graph_node`, still `tre`'s until M42 Phase 4.
`image` and `video` are Tesserae's since M42 (`tests/test_media.py`), and
`icon` since M41 (`tests/test_composed_widgets.py`).
"""

from pathlib import Path

import pytest
from tre import Window

from tesserae.widgets import graph_node, image, node_graph

PIXEL_PNG = str(Path(__file__).parent / "fixtures" / "pixel.png")


def test_image_raises_oserror_on_missing_file_matching_native():
    window = Window(width=400, height=300)
    with pytest.raises(OSError):
        image(window, "does/not/exist.png", 40, 40)


def test_node_graph_and_graph_node_match_native():
    window = Window(width=400, height=300)
    a_graph = node_graph(window, 200, 150)
    a_node = graph_node(window, a_graph, "Node A", 10, 10, 80, 40)
    b_graph = window.add_node_graph(200, 150)
    b_node = window.add_graph_node(b_graph, "Node A", 10, 10, 80, 40)
    assert a_graph.get("corner_radius") == b_graph.get("corner_radius")
    assert a_node.get("corner_radius") == b_node.get("corner_radius")
