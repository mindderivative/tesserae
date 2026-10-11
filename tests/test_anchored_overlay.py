"""#262 (part of #257): placing a node against another node is an `Overlay` today -- four sides, following the anchor with no lag. What it cannot do
(a corner, staying in the tree) is asked of tre in `design/tre-requests/anchored-layout.md`; the tests say what the engine does today."""

import pytest
import tre

from tesserae import App, Signal, ViewModel


class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.x = Signal(100)
        self.placement = Signal("above")


VIEW = """name: main
widget: Container
style: {width: 400, height: 300}
children:
  - {widget: Rect, name: target, style: {position: absolute, x: "{{ x }}", y: 100, width: 60, height: 40, background: primary}}
  - widget: Overlay
    name: tag
    anchor: target
    placement: "{{ placement }}"
    open: true
    dismissible: false
    children:
      - {widget: Rect, name: dot, style: {width: 12, height: 12, background: error}}
"""


def opened(tmp_path, text=VIEW):
    (tmp_path / "Views").mkdir(exist_ok=True)
    (tmp_path / "Views" / "Main_View.yaml").write_text(text)
    app = App(root=tmp_path)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    view.window.advance(32)
    return view, app.bindings.viewmodel_for("main")


def rect(node):
    return tuple(round(node.get(k)) for k in ("layout_x", "layout_y", "layout_width", "layout_height"))


def test_an_overlay_sits_against_a_named_node_and_follows_it_with_no_lag(tmp_path):
    view, vm = opened(tmp_path)
    assert rect(view.node("root.target")) == (100, 100, 60, 40) and rect(view.node("root.tag.dot")) == (100, 88, 12, 12)  # above, from the target's start
    vm.x.set(250)
    view.window.advance(32)  # one advance: the engine re-places the layer at that layout
    assert rect(view.node("root.target"))[0] == 250 and rect(view.node("root.tag.dot"))[:2] == (250, 88)


@pytest.mark.parametrize("placement, expected", [("below", (150, 160)), ("above", (150, 108)), ("start", (138, 120)), ("end", (210, 120))])
def test_the_four_sides_each_start_at_the_anchors_start_edge(placement, expected):
    window = tre.Window(width=400, height=300)
    window.root.set(padding_top=0, padding_left=0, padding_right=0, padding_bottom=0)
    anchor = window.create("box", position="absolute", x=150.0, y=120.0, width=60.0, height=40.0)
    window.root.add_child(anchor)
    layer = window.create("box", width=12.0, height=12.0)
    window.advance(16)
    window.show_layer(layer, anchor=anchor, placement=placement, dismissible=False)
    window.advance(16)
    assert rect(layer)[:2] == expected


@pytest.mark.parametrize("placement", ["top_end", "above_end", "bottom_start", "center", "over"])
def test_there_is_no_corner_or_centre_placement(placement):
    window = tre.Window(width=400, height=300)
    anchor = window.create("box", position="absolute", x=150.0, y=120.0, width=60.0, height=40.0)
    window.root.add_child(anchor)
    with pytest.raises(ValueError, match="`placement` must be one of: below, above, start, end"):
        window.show_layer(window.create("box", width=12.0, height=12.0), anchor=anchor, placement=placement)


def test_a_layer_flips_to_fit_which_a_marker_on_a_corner_would_not_want():
    window = tre.Window(width=400, height=300)
    window.root.set(padding_top=0, padding_left=0, padding_right=0, padding_bottom=0)
    anchor = window.create("box", position="absolute", x=150.0, y=4.0, width=60.0, height=40.0)
    window.root.add_child(anchor)
    layer = window.create("box", width=12.0, height=12.0)
    window.advance(16)
    window.show_layer(layer, anchor=anchor, placement="above", dismissible=False)
    window.advance(16)
    assert rect(layer)[1] == 44  # no room above, so below the anchor (4 + 40)


def test_a_layer_is_not_cut_by_a_clipping_ancestor():
    window = tre.Window(width=400, height=300)
    window.root.set(padding_top=0, padding_left=0, padding_right=0, padding_bottom=0)
    clip = window.create("box", position="absolute", x=100.0, y=100.0, width=80.0, height=60.0, clip_children=True)
    window.root.add_child(clip)
    anchor = window.create("box", position="absolute", x=60.0, y=20.0, width=20.0, height=20.0)
    clip.add_child(anchor)
    layer = window.create("box", width=40.0, height=40.0, fill=(255, 0, 0, 255))
    window.advance(16)
    window.show_layer(layer, anchor=anchor, placement="end", dismissible=False)
    window.advance(16)
    assert rect(layer)[0] == 180 == rect(clip)[0] + rect(clip)[2]  # it starts at the clip's right edge, outside the clipping box
    rgba, width, _ = window.snapshot()
    i = (140 * width + 200) * 4  # a point inside the layer and outside the clip box
    assert tuple(rgba[i:i + 3]) == (255, 0, 0)  # drawn, not cut
