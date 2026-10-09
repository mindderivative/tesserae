"""#239: `transition:` for layout properties -- width, height, x, y, gap, padding and margin ease, stepped by hand until the engine can."""

import pytest

from tesserae import View, motion
from tesserae.spec.layout_steps import Steps, curve, steps_of
from tesserae.spec.transition import EASINGS, LAYOUT_TRANSITIONABLE, plan

SEED = (103, 80, 164, 255)


def page(style, **node):
    child = {"id": "n", "kind": "Rect", "style": {"width": 60, "height": 30, "background": "#FF0000", **style}, **node}
    return {"id": "root", "kind": "Container", "style": {"width": 300, "height": 200, "flex_direction": "vertical", "align_content": "top_left"},
            "children": [child]}


def run(view, ms):
    for _ in range(max(1, ms // 16)):
        view.window.advance(16)


# -- the plan -----------------------------------------------------------------------------------------------------------------


def test_layout_fields_are_planned_as_their_node_properties():
    got = plan("n", "Rect", {"transition": {"width": 200, "padding": {"duration": 100, "easing": "linear"}, "gap": 50}})
    assert got["width"] == (200.0, EASINGS["standard"]) and got["gap"][0] == 50.0
    assert {got[p] for p in LAYOUT_TRANSITIONABLE["padding"]} == {(100.0, "linear")} and len(got) == 6


def test_all_does_not_include_layout():
    got = plan("n", "Rect", {"transition": {"all": 100}})
    assert not set(got) & {p for props in LAYOUT_TRANSITIONABLE.values() for p in props}


# -- the curve ----------------------------------------------------------------------------------------------------------------


def test_linear_is_progress_and_the_ends_are_the_ends():
    f = curve("linear")
    assert [f(t) for t in (0, 0.25, 1)] == [0, 0.25, 1]
    for easing in ("linear", EASINGS["standard"], EASINGS["emphasized"], ("spring", 0.3), "spring"):
        shape = curve(easing)
        assert shape(0.0) == 0.0 and shape(1.0) == 1.0 and shape(-1) == 0.0 and shape(2) == 1.0


def test_a_bezier_matches_the_css_curve_it_names():
    ease = curve((0.25, 0.1, 0.25, 1.0))  # CSS `ease`
    assert ease(0.5) == pytest.approx(0.8024, abs=0.001)
    assert ease(0.1) == pytest.approx(0.0937, abs=0.002)


def test_a_spring_is_drawn_as_a_settling_curve_not_a_straight_line():
    assert curve("spring")(0.3) > 0.5 and curve(("spring", 0.3))(0.3) > 0.5


def test_every_curve_rises_and_ends_where_it_starts_from():
    for easing in (EASINGS["standard"], EASINGS["emphasized_accelerate"], EASINGS["emphasized_decelerate"]):
        shape = curve(easing)
        values = [shape(i / 20) for i in range(21)]
        assert values == sorted(values)


# -- in a view ----------------------------------------------------------------------------------------------------------------


def test_a_width_eases_to_its_new_value_in_steps():
    view = View(page({"transition": {"width": 200}}), theme_seed=SEED)
    node = view.node("n")
    view.reconcile(page({"width": 160, "transition": {"width": 200}}))
    run(view, 48)
    mid = node.get("width")
    assert 60.0 < mid < 160.0
    run(view, 300)
    assert node.get("width") == 160.0 and steps_of(view.window).running() == 0


def test_it_moves_forward_only_for_a_linear_curve():
    view = View(page({"transition": {"width": {"duration": 160, "easing": "linear"}}}), theme_seed=SEED)
    view.reconcile(page({"width": 160, "transition": {"width": {"duration": 160, "easing": "linear"}}}))
    seen = []
    for _ in range(12):
        view.window.advance(16)
        seen.append(view.node("n").get("width"))
    assert seen == sorted(seen) and seen[-1] == 160.0 and len(set(seen)) > 4


@pytest.mark.parametrize("field, prop, before, after", [
    ("height", "height", 30, 90), ("gap", "gap", 4, 20), ("x", "x", 0, 50),
])
def test_the_other_scalars_ease_too(field, prop, before, after):
    base = {"position": "absolute"} if field in ("x", "y") else {}
    view = View(page({**base, field: before, "transition": {field: 200}}), theme_seed=SEED)
    view.reconcile(page({**base, field: after, "transition": {field: 200}}))
    run(view, 48)
    assert before < view.node("n").get(prop) < after
    run(view, 400)
    assert view.node("n").get(prop) == after


def test_padding_eases_on_every_side():
    view = View(page({"padding": 0, "transition": {"padding": 200}}), theme_seed=SEED)
    view.reconcile(page({"padding": 16, "transition": {"padding": 200}}))
    run(view, 48)
    sides = [view.node("n").get(f"padding_{s}") for s in ("top", "right", "bottom", "left")]
    assert all(0.0 < v < 16.0 for v in sides)
    run(view, 400)
    assert [view.node("n").get(f"padding_{s}") for s in ("top", "right", "bottom", "left")] == [16.0] * 4


def test_a_change_to_something_not_a_number_is_made_at_once():
    view = View(page({"transition": {"width": 200}}), theme_seed=SEED)
    view.reconcile(page({"width": "50%", "transition": {"width": 200}}))
    assert view.node("n").get("width") == "50%" and steps_of(view.window).running() == 0


def test_the_first_draw_is_where_it_says_and_an_unchanged_value_does_not_move():
    view = View(page({"width": 120, "transition": {"width": 200}}), theme_seed=SEED)
    assert view.node("n").get("width") == 120.0 and steps_of(view.window).running() == 0
    view.reconcile(page({"width": 120, "transition": {"width": 200}}))
    assert steps_of(view.window).running() == 0


def test_a_new_change_in_the_middle_goes_on_from_where_it_is():
    view = View(page({"transition": {"width": 400}}), theme_seed=SEED)
    view.reconcile(page({"width": 160, "transition": {"width": 400}}))
    run(view, 100)
    partway = view.node("n").get("width")
    view.reconcile(page({"width": 20, "transition": {"width": 400}}))
    run(view, 16)
    assert 20.0 < view.node("n").get("width") <= partway + 1  # turned around from there, not from 60 or 160
    run(view, 600)
    assert view.node("n").get("width") == 20.0 and steps_of(view.window).running() == 0


def test_an_app_that_reduces_motion_gets_the_value_at_once(monkeypatch):
    view = View(page({"transition": {"width": 200}}), theme_seed=SEED)
    monkeypatch.setattr(motion, "reduced", lambda window: True)
    view.reconcile(page({"width": 160, "transition": {"width": 200}}))
    assert view.node("n").get("width") == 160.0 and steps_of(view.window).running() == 0


def test_the_engine_s_own_animation_is_used_when_it_can_do_it(monkeypatch):
    view = View(page({"transition": {"width": 200}}), theme_seed=SEED)
    node = view.node("n")
    seen = []
    real = type(node).animate

    def capable(self, prop, value, ms, easing="linear", **kw):
        if prop == "width":  # a tre that can animate layout
            seen.append((prop, value, ms))
            return None
        return real(self, prop, value, ms, easing, **kw)

    monkeypatch.setattr(type(node), "animate", capable, raising=False)
    view.reconcile(page({"width": 160, "transition": {"width": 200}}))
    assert seen == [("width", 160.0, 200)] and steps_of(view.window).running() == 0


def test_another_error_from_animate_is_not_swallowed(monkeypatch):
    view = View(page({"transition": {"width": 200}}), theme_seed=SEED)
    node = view.node("n")
    real_cls = type(node)
    real = real_cls.animate

    def boom(self, prop, *a, **k):
        if prop == "width":
            raise ValueError("a different problem")
        return real(self, prop, *a, **k)

    monkeypatch.setattr(real_cls, "animate", boom, raising=False)
    with pytest.raises(Exception, match="a different problem"):
        view.reconcile(page({"width": 160, "transition": {"width": 200}}))
