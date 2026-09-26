"""M42 Phase 3: `image` and `video`, built by Tesserae (`window.create
("image")` with decoded pixels), off `tre`'s `add_image_from_bytes`,
`add_video` and `push_frame`, which 0.3.5 removes.
"""

from pathlib import Path

import pytest
import tre

from tesserae import Theme
from tesserae.images import decode_image
from tesserae.widgets import image, video

PIXEL_PNG = str(Path(__file__).parent / "fixtures" / "pixel.png")
SEED = (0x67, 0x50, 0xA4, 0xFF)


def _window():
    window = tre.Window(width=400, height=300)
    window.root.set(padding_top=0, padding_right=0, padding_bottom=0, padding_left=0, align_items="flex_start")
    return window


def test_an_image_shows_the_files_decoded_pixels():
    window = _window()
    im = image(window, PIXEL_PNG, 60, 40, fit="contain")
    window.advance(16)
    rgba, width, height = decode_image(PIXEL_PNG)
    assert (im.node.get("layout_width"), im.node.get("layout_height")) == (60.0, 40.0)
    assert (im.node.get("pixel_width"), im.node.get("pixel_height"), im.node.get("fit")) == (width, height, "contain")
    assert bytes(im.node.get("rgba")) == rgba
    assert im.node.parent() == window.root


def test_an_image_is_decorative_unless_labelled():
    window = _window()
    assert image(window, PIXEL_PNG, 10, 10).node.get("a11y_hidden") is True
    logo = image(window, PIXEL_PNG, 10, 10, label="Logo")
    assert (logo.node.get("role"), logo.node.get("label")) == ("img", "Logo")


def test_an_image_rejects_a_bad_fit_or_file():
    window = _window()
    with pytest.raises(ValueError, match="'cover', 'contain' or 'fill'"):
        image(window, PIXEL_PNG, 10, 10, fit="stretch")
    with pytest.raises(OSError):
        image(window, "does/not/exist.png", 10, 10)


def test_a_video_starts_blank_and_shows_frames():
    window = _window()
    v = video(window, 80, 60)
    window.advance(16)
    assert (v.node.get("pixel_width"), v.node.get("pixel_height")) == (1, 1)
    v.frame(bytes([10, 20, 30, 255] * 6), 3, 2)
    assert (v.node.get("pixel_width"), v.node.get("pixel_height")) == (3, 2)
    assert bytes(v.node.get("rgba"))[:4] == bytes([10, 20, 30, 255])
    v.frame(bytes([0, 0, 0, 255] * 16), 4, 4)  # frames can change size
    assert v.node.get("pixel_width") == 4


def test_a_video_frame_must_be_its_size_in_rgba():
    window = _window()
    v = video(window, 80, 60)
    with pytest.raises(ValueError, match="a 2x2 frame is 16 bytes of RGBA, got 12"):
        v.frame(bytes(12), 2, 2)


def test_a_re_colour_keeps_the_latest_video_frame():
    window = _window()
    v = video(window, 80, 60)
    v.frame(bytes([1, 2, 3, 255] * 4), 2, 2)
    v.set_theme(Theme.resolve(theme_seed=SEED))
    assert (v.node.get("pixel_width"), v.node.get("pixel_height")) == (2, 2)
    assert bytes(v.node.get("rgba"))[:4] == bytes([1, 2, 3, 255])


# == M42 Phase 4: the node graph ===============================================================

from tesserae import tokens  # noqa: E402
from tesserae.widgets import graph_node, node_graph  # noqa: E402
from tesserae.widgets.media import ZOOM_RANGE, ZOOM_STEP  # noqa: E402

BASE = tokens.baseline_scheme()


def _graph():
    window = tre.Window(width=600, height=400)
    window.root.set(padding_top=0, padding_right=0, padding_bottom=0, padding_left=0, align_items="flex_start")
    g = node_graph(window, 500, 300)
    a = graph_node(window, g, "Input", 20, 20, 120, 80)
    b = graph_node(window, g, "Output", 300, 150, 120, 80)
    window.advance(16)
    return window, g, a, b


def _numbers(data):
    import re
    return [float(n) for n in re.findall(r"-?\d+(?:\.\d+)?", data)]


def test_the_graph_is_a_clipped_viewport_with_md3_nodes():
    window, g, a, b = _graph()
    assert g.node.get("clip_children") is True and g.node.get("fill") == BASE["surface_container_low"]
    assert (g.node.get("role"), g.node.get("label")) == ("group", "Node graph")
    assert (a.node.get("layout_x"), a.node.get("layout_y"), a.node.get("layout_width")) == (20.0, 20.0, 120.0)
    assert a.node.get("fill") == BASE["surface_container_high"] and a.node.get("corner_radius") == 12.0
    assert a.node.get("stroke_color") == BASE["outline_variant"]
    title = a.part("title")
    assert title.get("layout_height") == 32.0 and title.get("fill") == BASE["surface_container_highest"]
    assert a.part("label").get("font_size") == 14.0 and a.part("body") is not None  # title_small
    assert (a.node.get("role"), a.node.get("label")) == ("group", "Input")


def test_an_edge_runs_from_one_nodes_right_to_the_others_left_and_follows_moves():
    window, g, a, b = _graph()
    path = g.edge(a, b)
    nums = _numbers(path.get("data"))
    assert nums[:2] == [140.0, 60.0] and nums[-2:] == [300.0, 190.0]
    assert path.get("stroke_color") == BASE["outline"] and path.get("hit_testable") is False
    b.position.set((350.0, 100.0))
    assert _numbers(path.get("data"))[-2:] == [350.0, 140.0]


def test_dragging_a_node_moves_it_and_reports_the_move():
    window, g, a, b = _graph()
    moved = []
    a.on_move(moved.append)
    path = g.edge(a, b)
    window.simulate("pointer_down", x=60, y=30)
    window.simulate("pointer_move", x=110, y=70)
    window.simulate("pointer_up", x=110, y=70)
    window.advance(16)
    assert a.position.get() == (70.0, 60.0) and a.node.get("layout_x") == 70.0
    assert moved[-1] == (70.0, 60.0) and _numbers(path.get("data"))[:2] == [190.0, 100.0]
    assert g.offset.get() == (0.0, 0.0)  # a node drag doesn't pan


def test_dragging_the_background_pans():
    window, g, a, b = _graph()
    window.simulate("pointer_down", x=450, y=50)
    window.simulate("pointer_move", x=470, y=60)
    window.simulate("pointer_up", x=470, y=60)
    window.advance(16)
    assert g.offset.get() == (20.0, 10.0) and a.node.get("layout_x") == 40.0
    assert a.position.get() == (20.0, 20.0)  # the nodes stay where they are in the graph


def test_the_wheel_zooms_about_the_pointer_within_range():
    window, g, a, b = _graph()
    window.simulate("wheel", x=100, y=100, delta_y=-1)
    window.advance(16)
    assert g.zoom.get() == pytest.approx(ZOOM_STEP)
    # the graph point under the pointer stays put: 100 = offset + 100 * zoom
    ox, oy = g.offset.get()
    assert ox + 100 * g.zoom.get() == pytest.approx(100) and oy + 100 * g.zoom.get() == pytest.approx(100)
    for _ in range(40):
        window.simulate("wheel", x=100, y=100, delta_y=-1)
    assert g.zoom.get() == ZOOM_RANGE[1]
    for _ in range(80):
        window.simulate("wheel", x=100, y=100, delta_y=1)
    assert g.zoom.get() == ZOOM_RANGE[0]


def test_a_drag_while_zoomed_moves_the_node_in_graph_units():
    window, g, a, b = _graph()
    g.zoom.set(2.0)
    window.advance(16)
    x, y = a.node.get("layout_x"), a.node.get("layout_y")
    window.simulate("pointer_down", x=x + 10, y=y + 10)
    window.simulate("pointer_move", x=x + 50, y=y + 10)
    window.simulate("pointer_up", x=x + 50, y=y + 10)
    assert a.position.get() == (40.0, 20.0)  # 40 px on screen at 2x is 20 in the graph


def test_the_arrow_keys_move_a_focused_node():
    window, g, a, b = _graph()
    a.node.focus()
    window.simulate("key_down", key="arrow_right")
    window.simulate("key_down", key="arrow_down")
    assert a.position.get() == (28.0, 28.0)


def test_the_graph_follows_the_theme():
    window, g, a, b = _graph()
    path = g.edge(a, b)
    dark = Theme.resolve(theme_seed=SEED, dark=True)
    g.set_theme(dark)
    a.set_theme(dark)
    assert path.get("stroke_color") == dark.role("outline")
    assert a.node.get("fill") == dark.role("surface_container_high") and a.node.get("layout_x") == 20.0
