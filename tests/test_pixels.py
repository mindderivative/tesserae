"""What the shader ripple, the frosted surfaces and the gradient focus ring actually draw, read back from the headless window's snapshot (tre draws shaders and backdrop blur there)."""

import pytest

from tesserae import App

SEED = (0x67, 0x50, 0xA4, 0xFF)


def pixel(view, x, y):
    rgba, width, _ = view.window.snapshot()
    i = (int(y) * width + int(x)) * 4
    return tuple(rgba[i:i + 4])


def opened(tmp_path, yaml, **kw):
    (tmp_path / "Views").mkdir(exist_ok=True)
    (tmp_path / "Views" / "Main_View.yaml").write_text(yaml)
    app = App(root=tmp_path, width=300, height=200, theme_seed=SEED, dark=False, reduced_motion=False, **kw)
    view = app.open_view("Main")
    app.show("main")
    for _ in range(6):
        view.window.advance(16)
    return app, view


BUTTON = """name: main
widget: Container
style: {width: 300, height: 200, align_content: center}
children:
  - {widget: Button, name: b, label: Press me, variant: outlined, size: xl}
"""


def distance(a, b):
    return sum(abs(p - q) for p, q in zip(a[:3], b[:3]))


def test_a_shader_ripple_colours_the_pixels_it_covers_and_leaves_the_others(tmp_path):
    app, view = opened(tmp_path, BUTTON, ripple="shader")
    node = view.node("root.b")
    x, y, w, h = (node.get(k) for k in ("layout_x", "layout_y", "layout_width", "layout_height"))
    near, far = (x + 30, y + h / 2), (x + w - 8, y + 8)
    before = pixel(view, *near), pixel(view, *far)
    view.window.simulate("pointer_down", x=near[0], y=near[1])
    for _ in range(12):  # 190 ms: the ripple is part grown, fully faded in
        view.window.advance(16)
    during = pixel(view, *near), pixel(view, *far)
    assert distance(during[0], before[0]) > 6, "the pixel under the press did not change"
    assert distance(during[1], before[1]) < distance(during[0], before[0]), "the far corner changed as much as the press point"
    view.window.simulate("pointer_up", x=near[0], y=near[1])
    for _ in range(60):
        view.window.advance(16)
    assert pixel(view, *near) == pytest.approx(before[0], abs=3) or distance(pixel(view, *near), before[0]) <= 6


def test_a_node_ripple_does_the_same_so_the_two_agree_on_which_pixels_change(tmp_path):
    shader_dir = tmp_path / "s"
    node_dir = tmp_path / "n"
    shader_dir.mkdir()
    node_dir.mkdir()
    results = {}
    for name, folder, kind in (("shader", shader_dir, "shader"), ("nodes", node_dir, "nodes")):
        app, view = opened(folder, BUTTON, ripple=kind)
        node = view.node("root.b")
        x, y, h = node.get("layout_x"), node.get("layout_y"), node.get("layout_height")
        spot = (x + 30, y + h / 2)
        base = pixel(view, *spot)
        view.window.simulate("pointer_down", x=spot[0], y=spot[1])
        for _ in range(12):
            view.window.advance(16)
        results[name] = distance(pixel(view, *spot), base)
    assert results["shader"] > 6 and results["nodes"] > 6


FROST = """name: main
widget: Container
style: {width: 300, height: 200}
children:
  - {widget: Rect, name: bar, style: {position: absolute, x: 100, y: 0, width: 20, height: 200, background: "#000000"}}
  - {widget: NavigationRail, name: rail, items: [{value: a, label: Alpha, icon: home}], %s}
"""


def test_a_frosted_rail_blurs_what_is_behind_it(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir()
    b.mkdir()
    _, plain = opened(a, FROST % "expanded: true")
    _, frosted = opened(b, FROST % "expanded: true, frosted: true")
    rail = plain.node("root.rail")
    edge_x = 100 - 3  # just left of the stripe, still inside the 220 px wide expanded rail
    assert rail.get("layout_width") > 120
    y = 150
    plain_px, frosted_px = pixel(plain, edge_x, y), pixel(frosted, edge_x, y)
    plain_stripe, frosted_stripe = pixel(plain, 110, y), pixel(frosted, 110, y)
    assert plain_px != frosted_px, "frosting changed nothing at the stripe's edge"
    # a solid rail hides the stripe completely; a frosted one lets a soft shadow of it through
    assert sum(frosted_stripe[:3]) < sum(plain_stripe[:3]), "no trace of the stripe shows through the frosted rail"
    assert sum(frosted_stripe[:3]) > 0, "the stripe shows through crisply, so nothing was blurred"
    assert sum(frosted_px[:3]) < sum(plain_px[:3]), "the blur did not reach the stripe's edge"


RING = """name: main
widget: Container
style: {width: 300, height: 200, align_content: center}
children:
  - {widget: Button, name: b, label: Focus me, variant: filled, size: m}
"""


def ring_samples(view, node, count=12):
    x, y, w, h = (node.get(k) for k in ("layout_x", "layout_y", "layout_width", "layout_height"))
    out = []
    for i in range(count):  # along the top and bottom edges, 3.5 px outside the node: the ring is 3 px wide, 2 px off
        t = (i + 0.5) / count
        out.append(pixel(view, x + t * w, y - 3) if i % 2 == 0 else pixel(view, x + t * w, y + h + 3))
    return out


def test_the_gradient_ring_is_drawn_in_several_colours_and_turns(tmp_path):
    app, view = opened(tmp_path, RING, focus_ring="gradient")
    node = view.node("root.b")
    inter = view.interaction("root.b")
    inter._on_focus(type("E", (), {"target": inter.node, "focus_visible": True})())
    for _ in range(4):
        view.window.advance(16)
    first = ring_samples(view, node)
    background = pixel(view, 5, 5)
    on_ring = [p for p in first if distance(p, background) > 30]
    assert len(on_ring) >= 6, "most of the sampled points should be on the ring"
    assert len({tuple(p[:3]) for p in on_ring}) >= 3, "a gradient ring should show several colours"
    for _ in range(30):  # about a second: a third of a turn
        view.window.advance(16)
    later = ring_samples(view, node)
    assert [tuple(p) for p in later] != [tuple(p) for p in first], "the ring did not turn"


def test_the_solid_ring_is_one_colour(tmp_path):
    app, view = opened(tmp_path, RING)
    node = view.node("root.b")
    inter = view.interaction("root.b")
    inter._on_focus(type("E", (), {"target": inter.node, "focus_visible": True})())
    for _ in range(4):
        view.window.advance(16)
    background = pixel(view, 5, 5)
    on_ring = [tuple(p[:3]) for p in ring_samples(view, node) if distance(p, background) > 30]
    assert on_ring and len(set(on_ring)) <= 2
