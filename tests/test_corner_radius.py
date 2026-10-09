"""#220: `corner_radius` per corner -- a list of four, or a mapping of corners and edges -- beside the one radius and the shape tokens."""

import pytest

from tesserae import View, tokens
from tesserae.spec.build import SpecBuildError

SEED = (103, 80, 164, 255)


def radius(value, kind="Rect", transition=None):
    style = {"width": 40, "height": 40, "background": "#336699", "corner_radius": value}
    node = {"id": "n", "kind": kind, "style": style}
    view = View({"id": "root", "kind": "Container", "style": {"width": 100, "height": 100}, "children": [node]}, theme_seed=SEED)
    return view.node("n").get("corner_radius")


def test_one_radius_is_every_corner():
    assert radius(8) == 8.0 and radius("medium") == tokens.SHAPES["medium"]


def test_a_list_is_top_left_top_right_bottom_right_bottom_left():
    assert radius([1, 2, 3, 4]) == (1.0, 2.0, 3.0, 4.0)
    assert radius(["none", "small", "medium", "large"]) == tuple(float(tokens.SHAPES[n]) for n in ("none", "small", "medium", "large"))


def test_four_equal_radii_are_one():
    assert radius([6, 6, 6, 6]) == 6.0 and radius({"top": 6, "bottom": 6}) == 6.0


def test_a_mapping_names_corners_and_leaves_the_rest_square():
    assert radius({"top_left": 12}) == (12.0, 0.0, 0.0, 0.0)
    assert radius({"bottom_right": 4, "top_left": 8}) == (8.0, 0.0, 4.0, 0.0)


@pytest.mark.parametrize("edge, expected", [
    ("top", (9.0, 9.0, 0.0, 0.0)), ("right", (0.0, 9.0, 9.0, 0.0)), ("bottom", (0.0, 0.0, 9.0, 9.0)), ("left", (9.0, 0.0, 0.0, 9.0)),
])
def test_an_edge_is_its_two_corners(edge, expected):
    assert radius({edge: 9}) == expected


def test_a_corner_beats_its_edge_whatever_the_order():
    assert radius({"top_left": 0, "top": 12}) == (0.0, 12.0, 0.0, 0.0)
    assert radius({"top": 12, "top_left": 0}) == (0.0, 12.0, 0.0, 0.0)


def test_full_is_a_pill_on_the_corners_it_names():
    assert radius({"left": "full"}) == (tokens.FULL_RADIUS, 0.0, 0.0, tokens.FULL_RADIUS)


@pytest.mark.parametrize("value, message", [
    ([1, 2, 3], "takes four radii .* not 3"), ([1, 2, 3, 4, 5], "takes four radii .* not 5"),
    ({"middle": 3}, 'has no "middle"'), ({"top": "huge"}, 'unknown style.corner_radius token "huge"'),
    ([1, 2, 3, True], "pixels or a shape token, not True"), ([1, 2, 3, None], "pixels or a shape token, not None"),
    ({"top": [1, 2]}, "pixels or a shape token, not"), ({"top": -3}, "non-negative"),
])
def test_a_wrong_radius_names_the_widget(value, message):
    with pytest.raises((SpecBuildError, ValueError), match=message):
        radius(value)


def test_a_radius_changes_on_a_patch_between_one_and_four_values():
    view = View({"id": "root", "kind": "Container", "style": {"width": 100, "height": 100},
                 "children": [{"id": "n", "kind": "Rect", "style": {"width": 40, "height": 40, "background": "#336699", "corner_radius": 4}}]}, theme_seed=SEED)
    assert view.node("n").get("corner_radius") == 4.0
    view.reconcile({"id": "root", "kind": "Container", "style": {"width": 100, "height": 100},
                    "children": [{"id": "n", "kind": "Rect", "style": {"width": 40, "height": 40, "background": "#336699",
                                                                       "corner_radius": {"top": 8}}}]})
    assert view.node("n").get("corner_radius") == (8.0, 8.0, 0.0, 0.0)
    view.reconcile({"id": "root", "kind": "Container", "style": {"width": 100, "height": 100},
                    "children": [{"id": "n", "kind": "Rect", "style": {"width": 40, "height": 40, "background": "#336699", "corner_radius": 2}}]})
    assert view.node("n").get("corner_radius") == 2.0


def test_a_view_and_a_stylesheet_rule_can_give_per_corner_radii(tmp_path):
    from tesserae import App, ViewModel

    class VM(ViewModel):
        views = "main"

    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Main_View.yaml").write_text(
        "name: main\nwidget: Container\nstyle: {width: 100, height: 100}\nchildren:\n"
        "  - {widget: Container, name: a, style: {width: 40, height: 40, background: '#336699', corner_radius: {left: 20}}}\n"
        "  - {widget: Container, name: b, classes: [round], style: {width: 40, height: 40, background: '#336699'}}\n")
    app = App(root=tmp_path, stylesheet_spec={"styles": [{"classes": ["round"], "style": {"corner_radius": [1, 2, 3, 4]}}]})
    app.bind(VM)
    view = app.open_view("Main")
    assert view.node("root.a").get("corner_radius") == (20.0, 0.0, 0.0, 20.0)
    assert view.node("root.b").get("corner_radius") == (1.0, 2.0, 3.0, 4.0)
