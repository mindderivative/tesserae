"""#280, step 1: an `Overlay` takes the corner and centre placements, an `offset` and `flip` (tre 0.5.7), and a tooltip takes the corner placements."""

import pytest

from tesserae import App, Signal, ViewModel
from tesserae.spec.nodes import LoadError


class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.shown = Signal(True)


def opened(tmp_path, overlay_lines, anchor="x: 150, y: 120, width: 60, height: 40"):
    (tmp_path / "Views").mkdir(parents=True, exist_ok=True)
    (tmp_path / "Views" / "Main_View.yaml").write_text(
        "name: main\nwidget: Container\nstyle: {width: 400, height: 300, background: surface}\nchildren:\n"
        f"  - {{widget: Rect, name: target, style: {{position: absolute, {anchor}, background: primary}}}}\n"
        "  - widget: Overlay\n    name: badge\n    anchor: target\n    open: \"{{ shown }}\"\n    dismissible: false\n" + overlay_lines +
        "    children:\n      - {widget: Rect, name: dot, style: {width: 12, height: 12, background: error}}\n")
    app = App(root=tmp_path, width=400, height=300)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    view.window.advance(50)
    return view


def dot(view):
    node = view.node("root.badge.dot")
    return node.get("layout_x"), node.get("layout_y")


@pytest.mark.parametrize("placement, expected", [("top_start", (144.0, 114.0)), ("top_end", (204.0, 114.0)), ("bottom_start", (144.0, 154.0)),
                                                 ("bottom_end", (204.0, 154.0)), ("center", (174.0, 134.0))])
def test_a_corner_or_the_centre_puts_the_overlays_centre_on_that_point_of_the_anchor(tmp_path, placement, expected):
    assert dot(opened(tmp_path, f"    placement: {placement}\n")) == expected


def test_an_offset_moves_the_point(tmp_path):
    assert dot(opened(tmp_path, "    placement: top_end\n    offset: [2, -2]\n")) == (206.0, 112.0)


def test_a_side_placement_is_as_it_was(tmp_path):
    assert dot(opened(tmp_path, "    placement: below\n")) == (150.0, 160.0)


def test_a_side_flips_at_the_window_edge_and_flip_false_keeps_it_there(tmp_path):
    near_top = "x: 150, y: 4, width: 60, height: 40"
    flipped = dot(opened(tmp_path / "a", "    placement: above\n", anchor=near_top))
    kept = dot(opened(tmp_path / "b", "    placement: above\n    flip: false\n", anchor=near_top))
    assert flipped[1] > 40 and kept[1] < 0  # flipped below the anchor, or left above it and off the window


def test_a_corner_is_never_moved_to_fit(tmp_path):
    assert dot(opened(tmp_path, "    placement: top_end\n", anchor="x: 394, y: 2, width: 6, height: 6")) == (394.0, -4.0)


def test_the_overlay_follows_its_anchor(tmp_path):
    view = opened(tmp_path, "    placement: top_end\n")
    view.window.advance(16)
    assert dot(view) == (204.0, 114.0)


@pytest.mark.parametrize("offset", ["5", "[1]", "[1, 2, 3]", "[a, b]", "[true, 1]"])
def test_an_offset_that_is_not_a_pair_of_numbers_is_named(tmp_path, offset):
    with pytest.raises(Exception) as caught:
        opened(tmp_path, f"    offset: {offset}\n")
    text = str(caught.value)
    assert "offset is a pair of pixels" in text or ("'offset' takes a list" in text and "Main_View.yaml:" in text)  # a number is refused at load; a wrong list when it is shown


def test_a_placement_that_is_not_one_is_refused_with_the_choices(tmp_path):
    with pytest.raises(LoadError) as caught:
        opened(tmp_path, "    placement: above_end\n")
    assert "top_start" in str(caught.value) and "center" in str(caught.value) and "Main_View.yaml" in str(caught.value)


def test_a_tooltip_may_use_a_corner(tmp_path):
    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Main_View.yaml").write_text(
        "name: main\nwidget: Container\nstyle: {width: 400, height: 300, background: surface}\nchildren:\n"
        "  - {widget: Rect, name: target, style: {width: 60, height: 40, background: primary}, tooltip: {text: hi, placement: top_end}}\n")
    app = App(root=tmp_path, width=400, height=300)
    app.bind(VM)
    view = app.open_view("Main")
    assert view.node("root.target") is not None
    with pytest.raises(LoadError, match="tooltip placement is one of"):
        (tmp_path / "Views" / "Main_View.yaml").write_text(
            "name: main\nwidget: Container\nchildren:\n  - {widget: Rect, name: t, style: {width: 6, height: 6, background: primary}, tooltip: {text: hi, placement: sideways}}\n")
        App(root=tmp_path).open_view("Main")
