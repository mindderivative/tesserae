"""#231: screen transitions -- fade through, shared axis and container transform between the screens of an app."""

import pytest

from tesserae import App, ViewModel
from tesserae.screen_transition import DISTANCE, IN_MS, OUT_MS, TRANSITIONS


class A(ViewModel):
    views = "a"


class B(ViewModel):
    views = "b"


def make_project(tmp_path):
    (tmp_path / "Views").mkdir(exist_ok=True)
    for name, colour in (("a", "primary"), ("b", "secondary")):
        (tmp_path / "Views" / f"{name.upper()}_View.yaml").write_text(
            f"name: {name}\nwidget: Container\nstyle: {{width: 300, height: 200, background: {colour}}}\nchildren:\n"
            f"  - {{widget: Container, name: card, style: {{width: 60, height: 40, background: tertiary}}}}\n")


def opened(tmp_path, **kwargs):
    make_project(tmp_path)
    app = App(root=tmp_path, width=300, height=200, **kwargs)
    app.bind(A)
    app.bind(B)
    a, b = app.open_view("A"), app.open_view("B")
    app.show("a")
    app.window.advance(16)
    return app, a, b


def roots(app):
    return app.screen("a")[0].root, app.screen("b")[0].root


def attached(node):
    return node.parent() is not None


def run(app, ms):
    for _ in range(max(1, ms // 16)):
        app.window.advance(16)


def test_the_default_is_a_plain_swap(tmp_path):
    app, a, b = opened(tmp_path)
    assert app.transition == "none"
    app.navigate("b")
    ra, rb = roots(app)
    assert attached(rb) and not attached(ra) and app._playing is None


def test_show_is_a_jump_even_when_the_app_has_a_transition(tmp_path):
    app, a, b = opened(tmp_path, transition="fade_through")
    app.show("b")
    ra, rb = roots(app)
    assert attached(rb) and not attached(ra) and app._playing is None


@pytest.mark.parametrize("kind", [k for k in TRANSITIONS if k != "none"])
def test_both_screens_are_there_while_it_plays_and_one_afterwards(tmp_path, kind):
    app, a, b = opened(tmp_path, transition=kind)
    app.navigate("b")
    ra, rb = roots(app)
    assert attached(ra) and attached(rb) and app._playing is not None
    assert ra.get("position") == "absolute" and rb.get("position") == "absolute"
    run(app, OUT_MS + IN_MS + 200)
    assert not attached(ra) and attached(rb)
    assert (rb.get("opacity"), rb.get("scale"), rb.get("translate_x"), rb.get("translate_y")) == (1.0, 1.0, 0.0, 0.0)
    assert (ra.get("opacity"), ra.get("scale")) == (1.0, 1.0) and ra.get("position") == "relative" and rb.get("position") == "relative"


def test_fade_through_fades_the_old_out_before_the_new_comes_in(tmp_path):
    app, a, b = opened(tmp_path, transition="fade_through")
    app.navigate("b")
    ra, rb = roots(app)
    assert rb.get("opacity") == 0.0 and rb.get("scale") == pytest.approx(0.92)
    run(app, 48)
    assert 0.0 < ra.get("opacity") < 1.0 and rb.get("opacity") == 0.0  # still leaving: the new one waits
    run(app, OUT_MS)
    assert ra.get("opacity") == 0.0 or not attached(ra) or rb.get("opacity") > 0.0
    run(app, 100)
    assert 0.0 < rb.get("opacity") < 1.0 and 0.92 < rb.get("scale") < 1.0


def test_a_shared_axis_slides_the_old_one_out_and_the_new_one_in_from_the_other_side(tmp_path):
    app, a, b = opened(tmp_path, transition="shared_axis_x")
    app.navigate("b")
    ra, rb = roots(app)
    assert rb.get("translate_x") == DISTANCE
    run(app, 48)
    assert ra.get("translate_x") < 0.0


def test_going_back_reverses_the_direction(tmp_path):
    app, a, b = opened(tmp_path, transition="shared_axis_x")
    app.navigate("b")
    run(app, 400)
    app.back()
    ra, rb = roots(app)
    assert ra.get("translate_x") == -DISTANCE  # back to a, which comes in from the left
    assert app.current == "a"
    run(app, 400)
    assert attached(ra) and not attached(rb)


def test_shared_axis_y_slides_vertically(tmp_path):
    app, a, b = opened(tmp_path, transition="shared_axis_y")
    app.navigate("b")
    assert roots(app)[1].get("translate_y") == DISTANCE and roots(app)[1].get("translate_x") == 0.0


def test_shared_axis_z_grows_the_new_screen_in(tmp_path):
    app, a, b = opened(tmp_path, transition="shared_axis_z")
    app.navigate("b")
    assert roots(app)[1].get("scale") == pytest.approx(0.8)
    run(app, 100)
    assert roots(app)[0].get("scale") > 1.0  # the old one grows away as it goes


def test_a_container_transform_grows_the_new_screen_from_the_node_it_came_from(tmp_path):
    app, a, b = opened(tmp_path)
    card = a.node("root.card")
    app.navigate_with("b", transition="container_transform", origin=card)
    ra, rb = roots(app)
    assert rb.get("scale") < 0.5 and rb.get("opacity") == 0.0  # a 60 x 40 card into a 300 x 200 screen
    run(app, 400)
    assert rb.get("scale") == 1.0 and rb.get("translate_x") == 0.0 and not attached(ra)


def test_a_container_transform_back_shrinks_the_screen_into_where_it_came_from(tmp_path):
    app, a, b = opened(tmp_path)
    app.navigate_with("b", transition="container_transform", origin=a.node("root.card"))
    run(app, 400)
    app.back()
    ra, rb = roots(app)
    assert attached(ra) and attached(rb)
    run(app, 100)
    assert rb.get("scale") < 1.0
    run(app, 400)
    assert not attached(rb) and rb.get("scale") == 1.0


def test_one_shot_transitions_do_not_stick(tmp_path):
    app, a, b = opened(tmp_path)
    app.navigate_with("b", transition="fade_through")
    run(app, 400)
    app.navigate("a")
    assert app._playing is None and attached(roots(app)[0])


def test_a_navigation_while_one_plays_finishes_it_first(tmp_path):
    app, a, b = opened(tmp_path, transition="fade_through")
    app.navigate("b")
    run(app, 32)
    app.navigate("a")
    ra, rb = roots(app)
    assert ra.get("opacity") == 0.0 and rb.get("opacity") == 1.0 and rb.get("translate_x") == 0.0  # the first ended where it was going (b in place), a begins
    run(app, 600)
    assert attached(ra) and not attached(rb) and ra.get("opacity") == 1.0 and rb.get("opacity") == 1.0


def test_an_app_that_reduces_motion_swaps_at_once(tmp_path):
    app, a, b = opened(tmp_path, transition="shared_axis_x", reduced_motion=True)
    app.navigate("b")
    ra, rb = roots(app)
    assert app._playing is None and attached(rb) and not attached(ra) and rb.get("translate_x") == 0.0


def test_a_wrong_name_is_refused(tmp_path):
    app, a, b = opened(tmp_path)
    with pytest.raises(ValueError, match="App.transition: one of none, fade_through"):
        app.transition = "spin"
    with pytest.raises(ValueError, match="navigate_with: transition is one of"):
        app.navigate_with("b", transition="spin")
    with pytest.raises(ValueError, match="App.transition"):
        App(root=tmp_path, transition="spin")


from test_routed_views import _app as routed_app, _shown, project  # noqa: E402,F401  (the window view with two routed screens)


def test_the_routed_screens_of_a_window_view_change_the_same_way(project):
    _, home, settings = project
    app, view = routed_app(project)
    app.transition = "fade_through"
    app.navigate_to("")
    app.window.advance(16)
    main, other = view.node("main"), view.node("settings")
    app.navigate_to("settings")
    assert _shown(view) == {"main": True, "settings": True} and other.get("opacity") == 0.0  # both there while it plays
    assert main.get("position") == "absolute"
    run(app, 600)
    assert _shown(view) == {"main": False, "settings": True}
    assert (main.get("opacity"), other.get("opacity")) == (1.0, 1.0) and other.get("position") == "relative"
    app.back()
    run(app, 600)
    assert _shown(view) == {"main": True, "settings": False}


def test_a_container_transform_with_no_origin_grows_from_the_middle(tmp_path):
    app, a, b = opened(tmp_path, transition="container_transform")
    app.navigate("b")
    rb = roots(app)[1]
    assert rb.get("scale") == pytest.approx(0.8) and rb.get("translate_x") == 0.0 and rb.get("translate_y") == 0.0
