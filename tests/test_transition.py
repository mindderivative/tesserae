"""#214: `transition:` in a style -- a change eases instead of jumping; the first draw does not; reduced motion snaps; layout waits for the engine."""

import pytest

from tesserae import View, motion
from tesserae.composed import open_composed
from tesserae.spec.build import SpecBuildError
from tesserae.spec.nodes import parse_view
from tesserae.spec.rules import RuleSheet
from tesserae.spec.transition import EASINGS, TRANSITIONABLE, plan
from tesserae.viewmodel import Bindings

SEED = (103, 80, 164, 255)
RED, BLUE = (255, 0, 0, 255), (0, 0, 255, 255)


def spec(style, kind="Rect", **extra):
    base = {"width": 60, "height": 30} if kind in ("Text", "Link") else {"width": 60, "height": 30, "background": "#FF0000"}  # a Text has a foreground, not a fill
    node = {"id": "n", "kind": kind, "style": {**base, **style}, **extra}
    return {"id": "root", "kind": "Container", "style": {"width": 200, "height": 100}, "children": [node]}


def fill(view):
    return view.node("n").get("fill")


# -- the plan ----------------------------------------------------------------------------------------------------------------


def test_a_number_is_a_duration_with_the_standard_easing_and_a_mapping_says_more():
    got = plan("n", "Rect", {"transition": {"opacity": 150, "corner_radius": {"duration": 200, "easing": "emphasized_decelerate"},
                                            "scale": {"duration": 300, "easing": "spring", "bounce": 0.3}, "border_width": {"duration": 90, "easing": [0.1, 0.2, 0.3, 0.4]}}})
    assert got["opacity"] == (150.0, EASINGS["standard"]) and got["corner_radius"] == (200.0, EASINGS["emphasized_decelerate"])
    assert got["scale"] == (300.0, ("spring", 0.3)) and got["stroke_width"] == (90.0, (0.1, 0.2, 0.3, 0.4))
    assert plan("n", "Rect", {"transition": {"opacity": {"duration": 10, "easing": "spring"}}})["opacity"] == (10.0, "spring")
    assert plan("n", "Rect", {}) == {} and plan("n", "Rect", {"transition": None}) == {}


def test_each_style_field_is_the_node_property_it_changes_and_background_or_foreground_is_the_fill_by_kind():
    every = {field: 10 for field in TRANSITIONABLE if field != "foreground"}
    assert set(plan("n", "Rect", {"transition": every})) == {"fill", "stroke_color", "stroke_width", "corner_radius", "shadows", "opacity", "blur",
                                                              "backdrop_blur", "scale", "translate_x", "translate_y", "rotation_deg"}
    assert "fill" in plan("n", "Rect", {"transition": {"background": 5}}) and "fill" not in plan("n", "Rect", {"transition": {"foreground": 5}})
    assert "fill" in plan("n", "Text", {"transition": {"foreground": 5}}) and "fill" not in plan("n", "Text", {"transition": {"background": 5}})


def test_all_covers_what_can_ease_and_a_named_field_wins():
    got = plan("n", "Rect", {"transition": {"all": 100, "opacity": {"duration": 400, "easing": "linear"}}})
    assert got["opacity"] == (400.0, "linear") and got["fill"] == (100.0, EASINGS["standard"]) and got["scale"][0] == 100.0 and len(got) == 12


@pytest.mark.parametrize("transition, message", [
    ("slow", "is a mapping of style fields to durations"), ({"width": 100}, "'width' cannot ease"), ({"opacity": True}, "a duration in milliseconds"),
    ({"opacity": -5}, "duration is milliseconds, 0 or more"), ({"opacity": "fast"}, "a duration in milliseconds"),
    ({"opacity": {"duration": 10, "easing": "wobble"}}, "easing is one of"), ({"opacity": {"duration": 10, "easing": [1, 2, 3]}}, "easing is one of"),
    ({"opacity": {"duration": 10, "bounce": 0.3}}, "bounce goes with easing: spring"),
    ({"opacity": {"duration": 10, "easing": "spring", "bounce": 1.5}}, "bounce is a number between -1 and 1"),
    ({"opacity": {"duration": 10, "speed": 3}}, "unknown key"), ({"opacity": {"easing": "linear"}}, "duration is milliseconds"),
])
def test_a_wrong_transition_names_the_widget_the_field_and_the_fix(transition, message):
    with pytest.raises(ValueError, match=f'widget "n": style.transition.*{message}|widget "n": style.transition {message}'):
        plan("n", "Rect", {"transition": transition})


# -- in the builder ---------------------------------------------------------------------------------------------------------


def test_a_change_eases_and_the_first_draw_does_not():
    view = View(spec({"transition": {"background": 200}}), theme_seed=SEED)
    assert fill(view) == RED  # drawn where it says
    view.reconcile(spec({"background": "#0000FF", "transition": {"background": 200}}))
    assert fill(view) == RED and view.node("n").get_target("fill") == BLUE  # on its way
    view.window.advance(100)
    assert fill(view) not in (RED, BLUE)
    view.window.advance(200)
    assert fill(view) == BLUE


def test_without_a_transition_a_change_is_at_once():
    view = View(spec({}), theme_seed=SEED)
    view.reconcile(spec({"background": "#0000FF"}))
    assert fill(view) == BLUE


def test_only_the_named_properties_ease():
    view = View(spec({"transition": {"opacity": 200}}), theme_seed=SEED)
    view.reconcile(spec({"background": "#0000FF", "opacity": 0.5, "transition": {"opacity": 200}}))
    assert fill(view) == BLUE and view.node("n").get("opacity") == 1.0 and view.node("n").get_target("opacity") == 0.5
    view.window.advance(300)
    assert view.node("n").get("opacity") == 0.5


def test_text_colour_corner_radius_border_and_elevation_ease():
    view = View(spec({"foreground": "#000000", "corner_radius": 0, "border_width": 0, "elevation": 0,
                      "transition": {"all": 200}}, kind="Text", text={"content": "hi", "font_family": "Roboto", "font_size": 16}), theme_seed=SEED)
    node = view.node("n")
    view.reconcile(spec({"foreground": "#FFFFFF", "corner_radius": 12, "border_width": 3, "elevation": 3, "transition": {"all": 200}}, kind="Text",
                        text={"content": "hi", "font_family": "Roboto", "font_size": 16}))
    assert node.get_target("fill") == (255, 255, 255, 255) and node.get_target("corner_radius") == 12.0
    assert node.get_target("stroke_width") == 3.0 and node.get_target("shadows") != node.get("shadows")
    view.window.advance(400)
    assert node.get("fill") == (255, 255, 255, 255) and node.get("corner_radius") == 12.0


def test_a_spring_and_a_bezier_are_accepted_by_the_engine():
    view = View(spec({"transition": {"scale": {"duration": 300, "easing": "spring", "bounce": 0.4}, "opacity": {"duration": 100, "easing": [0.2, 0, 0, 1]}}}),
                theme_seed=SEED)
    view.reconcile(spec({"scale": 1.5, "opacity": 0.5, "transition": {"scale": {"duration": 300, "easing": "spring", "bounce": 0.4},
                                                                         "opacity": {"duration": 100, "easing": [0.2, 0, 0, 1]}}}))
    assert view.node("n").get_target("scale") == 1.5
    view.window.advance(1500)
    assert abs(view.node("n").get("scale") - 1.5) < 0.01


def test_an_app_that_reduces_motion_gets_the_new_value_at_once(monkeypatch):
    monkeypatch.setattr(motion, "reduced", lambda window: True)
    view = View(spec({"transition": {"background": 500}}), theme_seed=SEED)
    view.reconcile(spec({"background": "#0000FF", "transition": {"background": 500}}))
    assert fill(view) == BLUE


def test_a_zero_duration_is_a_jump():
    view = View(spec({"transition": {"background": 0}}), theme_seed=SEED)
    view.reconcile(spec({"background": "#0000FF", "transition": {"background": 0}}))
    assert fill(view) == BLUE


def test_a_bad_transition_stops_the_build_naming_the_widget():
    with pytest.raises(SpecBuildError, match='widget "n": style.transition: .width. cannot ease'):
        View(spec({"transition": {"width": 100}}), theme_seed=SEED)


def test_a_transform_is_drawn_changed_and_put_back_when_dropped_and_a_python_one_is_left_alone():
    view = View(spec({"scale": 1.5, "translate_x": 8, "translate_y": -4, "rotation_deg": 45}), theme_seed=SEED)
    node = view.node("n")
    assert (node.get("scale"), node.get("translate_x"), node.get("translate_y"), node.get("rotation_deg")) == (1.5, 8.0, -4.0, 45.0)
    view.reconcile(spec({}))
    assert (node.get("scale"), node.get("translate_x"), node.get("translate_y"), node.get("rotation_deg")) == (1.0, 0.0, 0.0, 0.0)
    node.set(rotation_deg=180.0)  # a widget turned it from Python
    view.reconcile(spec({"background": "#00FF00"}))
    assert node.get("rotation_deg") == 180.0
    with pytest.raises(SpecBuildError):
        View(spec({"scale": "big"}), theme_seed=SEED)


def test_a_links_transform_is_on_its_box_not_its_text():
    view = View(spec({"scale": 1.5, "foreground": "#000000"}, kind="Link", text={"content": "go", "font_family": "Roboto", "font_size": 16}), theme_seed=SEED)
    assert view.node("n").get("scale") == 1.5 and view._built.nodes["n"].get("scale") == 1.0


# -- in the new syntax -------------------------------------------------------------------------------------------------------


def test_a_rule_can_carry_the_transition_and_a_state_change_eases():
    sheet = RuleSheet.of({"styles": [
        {"widget": "Rect", "style": {"background": "#FF0000", "transition": {"background": 200}}},
        {"widget": "Rect", "state": "hovered", "style": {"background": "#0000FF"}}]})
    view = open_composed(parse_view("widget: Rect\nstyle: {width: 100, height: 60}\n", "T_View.yaml"), Bindings(), rules=[sheet], theme_seed=SEED)
    view.window.advance(16)
    node = view.node("root")
    assert node.get("fill") == RED
    view.window.simulate("pointer_move", x=20, y=20)
    assert node.get("fill") == RED and node.get_target("fill") == BLUE  # hovered: easing to blue
    view.window.advance(400)
    assert node.get("fill") == BLUE
    view.window.simulate("pointer_move", x=900, y=900)
    assert node.get_target("fill") == RED


def test_the_loader_takes_transform_and_transition_as_style_fields_and_names_a_bad_one():
    node = parse_view("widget: Rect\nstyle: {scale: 1.1, transition: {opacity: 100}}\n", "T_View.yaml").root
    assert node.style["scale"] == 1.1 and node.style["transition"] == {"opacity": 100}
    RuleSheet.of({"styles": [{"widget": "Rect", "style": {"translate_y": 4, "transition": {"all": 100}}}]})
    with pytest.raises(SpecBuildError, match="style.transition"):
        open_composed(parse_view("widget: Rect\nstyle: {width: 10, height: 10, background: '#112233', transition: {width: 100}}\n", "T_View.yaml"), Bindings(), theme_seed=SEED)
