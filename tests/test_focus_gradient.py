"""The focus ring as a turning gradient (tesserae.focusring)."""

import pytest
import tre

from tesserae import App, tokens


def opened(tmp_path, ring="gradient", **kw):
    (tmp_path / "Views").mkdir(exist_ok=True)
    (tmp_path / "Views" / "Main_View.yaml").write_text(
        "name: main\nwidget: Container\nstyle: {width: 300, height: 200, flex_direction: vertical}\nchildren:\n"
        "  - {widget: Button, name: a, label: One, variant: filled}\n  - {widget: Button, name: b, label: Two, variant: filled}\n")
    app = App(root=tmp_path, width=300, height=200, focus_ring=ring, **kw)
    view = app.open_view("Main")
    app.show("main")
    for _ in range(4):
        view.window.advance(16)
    return app, view


def focus_by_key(view, name):
    view.node(f"root.{name}").focus()
    view.window.simulate("key_down", key="tab")  # a keyboard focus (focus_visible)
    for _ in range(2):
        view.window.advance(16)


def ring_of(view, name):
    return view.interaction(f"root.{name}")


def keyboard_focus(view, name):
    inter = ring_of(view, name)
    view.window.simulate("key_down", key="tab")
    view.node(f"root.{name}").focus()
    return inter


def test_the_option_is_checked():
    with pytest.raises(ValueError, match="focus_ring is 'solid'"):
        App(focus_ring="rainbow")


def test_the_default_ring_is_a_plain_colour(tmp_path):
    app, view = opened(tmp_path, ring="solid")
    inter = ring_of(view, "a")
    assert inter._glow is None and isinstance(inter.ring.get("stroke_color"), tuple)


def test_a_focused_node_gets_a_sweep_gradient_ring_that_turns(tmp_path):
    app, view = opened(tmp_path)
    inter = ring_of(view, "a")
    event = type("E", (), {"target": inter.node, "focus_visible": True})()
    inter._on_focus(event)
    first = inter.ring.get("stroke_color")
    assert isinstance(first, tre.Gradient) and inter._glow.turning and inter.ring_visible
    scheme = view._scheme or tokens.BASELINE
    assert inter.glow[0] == scheme["primary"]
    assert [c[:3] for _, c in first.stops] == [tuple(c[:3]) for c in (inter.ring_color, *inter.glow, inter.ring_color)]
    for _ in range(20):
        view.window.advance(16)
    later = inter.ring.get("stroke_color")
    assert later.start != first.start and 0 <= later.start < 360


def test_losing_the_focus_stops_the_turning_and_hides_the_ring(tmp_path):
    app, view = opened(tmp_path)
    inter = ring_of(view, "a")
    inter._on_focus(type("E", (), {"target": inter.node, "focus_visible": True})())
    inter._on_unfocus(type("E", (), {"target": inter.node})())
    assert not inter._glow.turning and not inter.ring_visible


def test_a_pointer_focus_shows_no_ring_and_so_no_turning(tmp_path):
    app, view = opened(tmp_path)
    inter = ring_of(view, "a")
    inter._on_focus(type("E", (), {"target": inter.node, "focus_visible": False})())
    assert not inter._glow.turning and not inter.ring_visible


def test_a_full_turn_takes_three_seconds(tmp_path):
    app, view = opened(tmp_path)
    inter = ring_of(view, "a")
    inter._on_focus(type("E", (), {"target": inter.node, "focus_visible": True})())
    for _ in range(int(3000 / 33)):
        view.window.advance(33)
    assert inter._glow.angle == pytest.approx(0.0, abs=12.0) or inter._glow.angle > 348.0


def test_reduced_motion_holds_the_gradient_still(tmp_path):
    app, view = opened(tmp_path, reduced_motion=True)
    inter = ring_of(view, "a")
    inter._on_focus(type("E", (), {"target": inter.node, "focus_visible": True})())
    assert isinstance(inter.ring.get("stroke_color"), tre.Gradient) and not inter._glow.turning


def test_a_theme_change_recolours_the_gradient(tmp_path):
    app, view = opened(tmp_path)
    inter = ring_of(view, "a")
    inter._on_focus(type("E", (), {"target": inter.node, "focus_visible": True})())
    before = [c for _, c in inter.ring.get("stroke_color").stops]
    view.set_theme(theme_seed=(0x00, 0x66, 0x44, 0xFF), dark=False)
    after = [c for _, c in inter.ring.get("stroke_color").stops]
    assert after != before
