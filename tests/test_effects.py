"""#90: gradients and the engine's visual effects as style keys: `blur`, `backdrop_blur`, `blend_mode`, `filter`,
`sticky` and `cursor`."""

import io

import pytest
import tre
import yaml
from PIL import Image

from tesserae import App, View
from tesserae.spec import effects
from tesserae.spec.build import SpecBuildError

SEED = (0x67, 0x50, 0xA4, 0xFF)


def _view(style, kind="Rect", **node):
    spec = yaml.safe_load("id: root\nkind: Container\nstyle: {width: 200, height: 100}\nchildren: []")
    child = {"id": "x", "kind": kind, "style": {"width": 100, "height": 50, **style}, **node}
    if kind == "Rect":
        child["style"].setdefault("background", "primary")
    if kind in ("Text", "Link"):
        child["text"] = {"content": "Hello", "typography_role": "body_large"}
        child["style"].setdefault("foreground", "on_surface")
    spec["children"] = [child]
    app = App(width=300, height=200, theme_seed=SEED)
    view = View(spec, window=app.window)
    app.window.advance(16)
    return app, view, view.nodes["x"] if hasattr(view, "nodes") else view.node("x")


def _colour(color):
    return lambda raw: {"red": (255, 0, 0, 255), "blue": (0, 0, 255, 255), "green": (0, 255, 0, 255)}.get(raw, (1, 2, 3, 255))


def test_a_linear_gradient_string():
    gradient = effects.make_gradient("linear-gradient(90deg, red, blue)", _colour(None))
    assert gradient.kind == "linear" and gradient.angle == 90.0
    assert [offset for offset, _ in gradient.stops] == [0.0, 1.0]


def test_a_direction_by_name_and_stop_places():
    gradient = effects.make_gradient("linear-gradient(to right, red 0%, green 25%, blue)", _colour(None))
    assert gradient.angle == 90.0
    assert [offset for offset, _ in gradient.stops] == [0.0, 0.25, 1.0]


def test_stops_without_places_are_spread_between_the_ones_with():
    gradient = effects.make_gradient("linear-gradient(red, green, green, blue 100%)", _colour(None))
    assert [round(o, 3) for o, _ in gradient.stops] == [0.0, 0.333, 0.667, 1.0]


def test_a_colour_function_keeps_its_commas():
    gradient = effects.make_gradient("linear-gradient(rgb(255, 0, 0), blue)", lambda raw: (9, 9, 9, 255))
    assert len(gradient.stops) == 2


def test_radial_and_conic():
    radial = effects.make_gradient("radial-gradient(at 30% 40%, red, blue)", _colour(None))
    assert radial.kind == "radial" and radial.center == (0.3, 0.4)
    sweep = effects.make_gradient("conic-gradient(from 90deg, red, blue, red)", _colour(None))
    assert sweep.kind == "sweep" and sweep.start == 90.0


def test_the_mapping_form():
    gradient = effects.make_gradient({"gradient": "linear", "angle": 45, "stops": ["red", [0.7, "green"], "blue"]},
                                     _colour(None))
    assert gradient.angle == 45.0 and gradient.stops[1][0] == pytest.approx(0.7)


@pytest.mark.parametrize("raw", ["linear-gradient(red)", {"gradient": "zigzag", "stops": ["a", "b"]},
                                 {"gradient": "linear"}, "linear-gradient(to nowhere, red, blue)", 5])
def test_a_bad_gradient_is_refused(raw):
    with pytest.raises(ValueError):
        effects.make_gradient(raw, _colour(None))


def test_a_background_gradient_is_the_nodes_fill():
    _, _, node = _view({"background": "linear-gradient(90deg, primary, tertiary)"})
    assert isinstance(node.get("fill"), tre.Gradient)


def test_a_foreground_and_a_border_gradient():
    _, _, text = _view({"foreground": "linear-gradient(to right, primary, error)"}, kind="Text")
    assert isinstance(text.get("fill"), tre.Gradient)
    _, _, box = _view({"border_width": 2, "border_color": {"gradient": "sweep", "stops": ["primary", "secondary"]}})
    assert isinstance(box.get("stroke_color"), tre.Gradient)


def test_the_effects_reach_the_node_and_clear_again():
    app, view, node = _view({"blur": 3, "backdrop_blur": 8, "blend_mode": "multiply", "sticky": 4,
                             "cursor": "grab", "filter": {"grayscale": 1.0}})
    assert (node.get("blur"), node.get("backdrop_blur"), node.get("blend_mode")) == (3.0, 8.0, "multiply")
    assert node.get("sticky") == 4.0 and node.get("cursor") == "grab" and node.get("shader") is not None
    _, _, plain = _view({})
    assert (plain.get("blur"), plain.get("backdrop_blur"), plain.get("blend_mode")) == (0.0, 0.0, "normal")
    assert plain.get("sticky") is None and plain.get("cursor") is None and plain.get("shader") is None


@pytest.mark.parametrize("style", [{"blur": -1}, {"blend_mode": "sparkle"}, {"filter": {"sparkle": 1}},
                                   {"filter": {}}, {"cursor": "nowhere"}, {"background": "linear-gradient(red)"}])
def test_a_bad_effect_names_the_widget(style):
    with pytest.raises((SpecBuildError, ValueError)) as caught:
        _view(style)
    assert "x" in str(caught.value)


def test_a_link_shows_its_own_cursor_on_the_box_that_hears_the_pointer():
    _, _, link = _view({"cursor": "help"}, kind="Link")
    assert link.get("cursor") == "help"
    _, _, plain = _view({}, kind="Link")
    assert plain.get("cursor") == "pointer"


def test_a_cursor_from_a_picture():
    buffer = io.BytesIO()
    Image.new("RGBA", (8, 8), (255, 0, 0, 255)).save(buffer, format="PNG")
    cursor = effects.cursor_value({"rgba": Image.open(io.BytesIO(buffer.getvalue())).convert("RGBA").tobytes(),
                                   "width": 8, "height": 8, "hotspot": [2, 3]}, "x")
    assert isinstance(cursor, tre.CursorImage) and cursor.hotspot == (2, 3)


def test_a_cursor_picture_is_read_with_the_view(tmp_path):
    from tesserae.spec.images import extract_images

    Image.new("RGBA", (6, 6), (0, 0, 255, 255)).save(tmp_path / "c.png")
    spec = {"id": "root", "kind": "Container", "children": [
        {"id": "x", "kind": "Rect", "style": {"cursor": {"src": "c.png", "hotspot": [1, 2]}}}]}
    out, _ = extract_images(spec, tmp_path)
    cursor = out["children"][0]["style"]["cursor"]
    assert (cursor["width"], cursor["height"], cursor["hotspot"]) == (6, 6, [1, 2])
    assert isinstance(effects.cursor_value(cursor, "x"), tre.CursorImage)


def test_a_cursor_picture_must_be_small_and_inside_the_view(tmp_path):
    from tesserae.spec.expand import ComponentError
    from tesserae.spec.images import extract_images

    Image.new("RGBA", (300, 10)).save(tmp_path / "big.png")
    spec = {"id": "x", "kind": "Rect", "style": {"cursor": {"src": "big.png"}}}
    with pytest.raises(ComponentError, match="256"):
        extract_images(spec, tmp_path)
    with pytest.raises(ComponentError):
        extract_images({"id": "x", "kind": "Rect", "style": {"cursor": {"src": "../x.png"}}}, tmp_path)
