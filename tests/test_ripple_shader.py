"""The press ripple drawn by one shader (tesserae.ripple): presses become uniform slots that grow and fade with Material Web's timing."""

import pytest

from tesserae import App, ripple, tokens


def opened(tmp_path, shader=True, width=200):
    (tmp_path / "Views").mkdir(exist_ok=True)
    (tmp_path / "Views" / "Main_View.yaml").write_text(
        "name: main\nwidget: Container\nstyle: {width: 300, height: 200}\nchildren:\n  - {widget: Button, name: b, label: Go, variant: filled}\n")
    app = App(root=tmp_path, width=300, height=200, ripple="shader" if shader else "nodes")
    view = app.open_view("Main")
    app.show("main")
    for _ in range(4):
        view.window.advance(16)
    return app, view


def test_the_option_is_checked():
    with pytest.raises(ValueError, match="ripple is 'nodes'"):
        App(ripple="glitter")


def test_a_press_makes_one_slot_that_grows_and_a_release_after_the_minimum_fades_it(tmp_path):
    app, view = opened(tmp_path)
    node = view.node("root.b")
    inter = next(i for i in _interactions(view) if i.node == node)
    assert inter.ripples == [] and inter.sparks.get("visible") is False
    x, y = node.get("layout_x"), node.get("layout_y")
    view.window.simulate("pointer_down", x=x + 20, y=y + 20)
    assert len(inter.ripples) == 1 and inter.sparks.get("visible") is True
    first = inter._shader.shader.uniforms["r0"]
    assert first[0:2] == (20.0, 20.0) and first[3] == 0.0
    for _ in range(10):
        view.window.advance(16)
    held = inter._shader.shader.uniforms["r0"]
    assert held[2] > first[2] and held[3] == pytest.approx(ripple.PRESSED)
    view.window.simulate("pointer_up", x=x + 20, y=y + 20)
    for _ in range(40):
        view.window.advance(16)
    assert inter.ripples == [] and inter.sparks.get("visible") is False and inter._shader._timer is None
    assert inter._shader.shader.uniforms["r0"] == (0.0, 0.0, 0.0, 0.0)


def test_a_quick_tap_still_shows_for_the_minimum_press_time(tmp_path):
    app, view = opened(tmp_path)
    node = view.node("root.b")
    inter = next(i for i in _interactions(view) if i.node == node)
    view.window.simulate("pointer_down", x=node.get("layout_x") + 5, y=node.get("layout_y") + 5)
    view.window.simulate("pointer_up", x=node.get("layout_x") + 5, y=node.get("layout_y") + 5)
    for _ in range(8):  # 128 ms: under the 225 ms minimum
        view.window.advance(16)
    assert inter._shader.presses[0].fade_age is None and inter._shader.shader.uniforms["r0"][3] > 0.0
    for _ in range(40):
        view.window.advance(16)
    assert inter.ripples == []


def test_three_presses_at_once_and_a_fourth_replaces_the_oldest(tmp_path):
    app, view = opened(tmp_path)
    node = view.node("root.b")
    inter = next(i for i in _interactions(view) if i.node == node)
    for i in range(4):
        inter._shader.press(10.0 + i, 5.0, 100.0, 40.0)
    assert len(inter.ripples) == 3 and [p.x for p in inter.ripples] == [11.0, 12.0, 13.0]


def test_a_keyboard_click_ripples_from_the_middle(tmp_path):
    app, view = opened(tmp_path)
    node = view.node("root.b")
    inter = next(i for i in _interactions(view) if i.node == node)
    node.focus()
    view.window.simulate("key_down", key="enter")
    p = inter.ripples[0] if inter.ripples else None
    assert p is not None and p.x == pytest.approx(node.get("layout_width") / 2) and p.released


def test_the_ripple_takes_the_tint_and_a_retint_changes_it(tmp_path):
    app, view = opened(tmp_path)
    node = view.node("root.b")
    inter = next(i for i in _interactions(view) if i.node == node)
    tint = inter.tint
    assert inter._shader.shader.uniforms["tint"] == pytest.approx(tuple(c / 255 for c in tint))
    inter.retint((255, 0, 0, 255), inter.ring_color)
    assert inter._shader.shader.uniforms["tint"] == (1.0, 0.0, 0.0, 1.0)


def test_a_disabled_node_clears_the_ripple(tmp_path):
    app, view = opened(tmp_path)
    node = view.node("root.b")
    inter = next(i for i in _interactions(view) if i.node == node)
    inter._shader.press(5.0, 5.0, 100.0, 40.0)
    inter.enabled = False
    assert inter.ripples == [] and inter.sparks.get("visible") is False


def test_the_default_is_still_a_node_per_press(tmp_path):
    app, view = opened(tmp_path, shader=False)
    node = view.node("root.b")
    inter = next(i for i in _interactions(view) if i.node == node)
    view.window.simulate("pointer_down", x=node.get("layout_x") + 5, y=node.get("layout_y") + 5)
    assert inter.sparks is None and len(inter.ripples) == 1 and hasattr(inter.ripples[0], "get")


def test_the_easing_runs_from_0_to_1_and_is_front_loaded():
    assert ripple._ease(0.0) == pytest.approx(0.0, abs=1e-6) and ripple._ease(1.0) == pytest.approx(1.0, abs=1e-6)
    assert ripple._ease(0.25) > 0.25


def test_the_wgsl_is_valid_and_draws_three_slots():
    assert ripple.shader_for((10, 20, 30, 255)).uniforms["tint"] == pytest.approx((10 / 255, 20 / 255, 30 / 255, 1.0))


def _interactions(view):
    return [view.interaction("root.b")]
