"""M39 Phase 3: MD3's focus ring on keyboard focus, YAML's `a11y:` field,
and `tesserae.a11y` for Tesserae's widgets (M40).
"""

import math

import pytest
import tre

import tesserae
from tesserae import View, a11y, interaction
from tesserae.spec.build import SpecBuildError

SEED = (0x67, 0x50, 0xA4, 0xFF)


def _rect(node_id, width=200, height=80, radius=20, **extra):
    return {"id": node_id, "kind": "Rect",
            "style": {"width": width, "height": height, "background": "#DDDDDD", "corner_radius": radius}, **extra}


def _spec(*children):
    return {"id": "root", "kind": "Container", "style": {"gap": 20}, "children": list(children)}


class VM(tesserae.ViewModel):
    def go(self):
        pass


def _built(*children, **kwargs):
    view = View(_spec(*children), **kwargs)
    view.window.advance(16)
    VM(view)
    return view, view.window


def _tab(window, times=1):
    for _ in range(times):
        window.simulate("key_down", key="tab")
        window.advance(16)


# -- the focus ring ------------------------------------------------------------

def test_keyboard_focus_shows_md3s_focus_ring_outside_the_node():
    view, window = _built(_rect("btn", handlers={"on_click": "go"}), theme_seed=SEED)
    it = view.interaction("btn")
    assert it.ring_visible is False
    _tab(window)
    ring = it.ring
    assert it.ring_visible is True
    out = interaction.RING_OFFSET + interaction.RING_WIDTH  # a box's stroke is drawn inside it
    assert (ring.get("layout_x"), ring.get("layout_y")) == (-out, -out)
    assert (ring.get("layout_width"), ring.get("layout_height")) == (200 + 2 * out, 80 + 2 * out)
    assert ring.get("stroke_width") == 3.0 and ring.get("corner_radius") == 20 + out
    assert ring.get("stroke_color") == view.theme.role("secondary")
    assert ring.get("hit_testable") is False and ring.get("a11y_hidden") is True


def test_the_ring_hides_when_focus_moves_on_and_never_shows_for_a_click():
    view, window = _built(_rect("a", handlers={"on_click": "go"}), _rect("b", handlers={"on_click": "go"}))
    _tab(window)
    assert view.interaction("a").ring_visible
    _tab(window)
    assert not view.interaction("a").ring_visible and view.interaction("b").ring_visible
    window.simulate("click", node=view.node("a"))
    window.advance(16)
    assert view.node("a").get("focused") is True
    assert not view.interaction("a").ring_visible and not view.interaction("b").ring_visible


def test_a_square_node_gets_a_square_ring_and_a_resized_node_a_resized_ring():
    view, window = _built(_rect("btn", radius=0, handlers={"on_click": "go"}))
    view.reconcile(_spec(_rect("btn", width=120, radius=0, handlers={"on_click": "go"})))
    window.advance(16)
    _tab(window)
    ring = view.interaction("btn").ring
    assert ring.get("corner_radius") == 0.0
    assert ring.get("layout_width") == 120 + 2 * (interaction.RING_OFFSET + interaction.RING_WIDTH)


def test_per_corner_radii_each_grow_by_the_ring():
    window = tre.Window(width=300, height=200)
    node = window.create("box", width=100, height=40, corner_radius=(8, 0, 8, 0), focusable=True)
    window.root.add_child(node)
    window.advance(16)
    it = interaction.Interaction(window, node, (0, 0, 0, 255), lambda n, e, f: (n.on(e, f), lambda: n.off(e))[1],
                                 (255, 0, 0, 255))
    out = interaction.RING_OFFSET + interaction.RING_WIDTH
    assert tuple(it.ring.get("corner_radius")) == (8 + out, 0.0, 8 + out, 0.0)
    assert tuple(it.clip.get("corner_radius")) == (8.0, 0.0, 8.0, 0.0)


def test_the_clip_follows_the_nodes_corners_and_the_ring_the_theme():
    view, window = _built(_rect("btn", handlers={"on_click": "go"}), theme_seed=SEED)
    view.reconcile(_spec(_rect("btn", radius=8, handlers={"on_click": "go"})))
    assert view.interaction("btn").clip.get("corner_radius") == 8.0
    light = view.theme.role("secondary")
    view.set_theme(theme_seed=SEED, dark=True)
    assert view.interaction("btn").ring.get("stroke_color") == view.theme.role("secondary") != light


def test_without_a_theme_the_ring_is_md3s_baseline_secondary():
    view, _ = _built(_rect("btn", handlers={"on_click": "go"}))
    assert view.interaction("btn").ring.get("stroke_color") == (0x62, 0x5B, 0x71, 0xFF)


def test_a_clickable_nodes_children_are_no_longer_clipped():
    child = _rect("wide", width=400, height=20, radius=0)
    view, _ = _built(_rect("btn", handlers={"on_click": "go"}, children=[child]))
    assert view.node("btn").get("clip_children") is False
    ripple_host = view.interaction("btn").clip
    window = view.window
    window.simulate("pointer_down", x=10, y=10)
    window.advance(16)
    (circle,) = view.interaction("btn").ripples
    assert circle.parent() == ripple_host  # the ripple is still clipped, inside the clip box


# -- YAML's a11y: field ------------------------------------------------------------

def test_a11y_labels_and_roles_from_yaml():
    view, _ = _built(
        _rect("save", handlers={"on_click": "go"}, a11y={"label": "Save"}),
        _rect("tab", handlers={"on_click": "go"}, a11y={"role": "tab", "label": "Inbox"}),
        _rect("title", a11y={"role": "heading", "level": 2, "label": "Settings"}),
        _rect("status", a11y={"live": "polite"}),
        _rect("art", a11y={"hidden": True}),
    )
    save, tab, title = view.node("save"), view.node("tab"), view.node("title")
    assert (save.get("role"), save.get("label")) == ("button", "Save")
    assert (tab.get("role"), tab.get("label"), tab.get("focusable")) == ("tab", "Inbox", True)
    assert (title.get("role"), title.get("level"), title.get("focusable")) == ("heading", 2, False)
    assert view.node("status").get("live") == "polite"
    assert view.node("art").get("a11y_hidden") is True


def test_a_text_fields_a11y_goes_on_its_input():
    field = {"id": "name", "kind": "TextField", "text": {"content": "", "font_family": "Roboto", "font_size": 14},
             "style": {"width": 200, "height": 40, "background": "#FFFFFF"}, "a11y": {"label": "Name"}}
    view, _ = _built(field)
    assert view.node("name").get("label") == "Name"  # the text_input
    assert view.node("name").get("role") == "textbox"


def test_reconcile_resets_dropped_a11y_fields():
    view, _ = _built(_rect("t", a11y={"role": "heading", "level": 1, "label": "Hi", "live": "polite",
                                      "hidden": True}))
    view.reconcile(_spec(_rect("t")))
    node = view.node("t")
    assert (node.get("role"), node.get("level"), node.get("label"), node.get("live"), node.get("a11y_hidden")) == (
        "none", None, None, None, False)
    view.reconcile(_spec(_rect("t", handlers={"on_click": "go"}, a11y={"role": "tab"})))
    assert (node.get("role"), node.get("focusable")) == ("tab", True)
    view.reconcile(_spec(_rect("t", handlers={"on_click": "go"})))
    assert node.get("role") == "button"


@pytest.mark.parametrize("value, message", [
    ("Save", "`a11y:` takes a mapping"),
    ({"name": "Save"}, r"unknown a11y field\(s\) \['name'\]"),
    ({"checked": True}, r"unknown a11y field\(s\) \['checked'\]"),  # widget state: M40's
    ({"role": "banner"}, "a11y role 'banner' isn't one of"),
    ({"level": 0}, "a11y level must be a positive whole number"),
    ({"live": "rude"}, "a11y live 'rude' isn't one of"),
    ({"hidden": "yes"}, "a11y hidden must be true or false"),
    ({"label": 3}, "a11y label must be a string"),
])
def test_a_bad_a11y_field_is_an_error_naming_the_widget(value, message):
    with pytest.raises(SpecBuildError, match=message) as info:
        View(_spec(_rect("btn", a11y=value)))
    assert 'widget "btn"' in str(info.value)


def test_a_link_keeps_its_role():
    link = {"id": "more", "kind": "Link", "text": {"content": "More", "font_family": "Roboto", "font_size": 14},
            "style": {"foreground": "#0000FF"}, "a11y": {"role": "button"}}
    with pytest.raises(SpecBuildError, match="a Link has its own role"):
        View(_spec(link))


# -- tesserae.a11y, for widgets ------------------------------------------------------------

def test_describe_checks_every_field_before_setting_any():
    window = tre.Window(width=100, height=100)
    node = window.create("box", width=10, height=10)
    a11y.describe(node, role="switch", label="Wi-Fi", checked=True, value=1)
    assert (node.get("role"), node.get("label"), node.get("checked"), node.get("value")) == (
        "switch", "Wi-Fi", True, 1.0)
    with pytest.raises(ValueError, match="a11y checked must be true or false"):
        a11y.describe(node, label="Changed", checked="no")
    assert node.get("label") == "Wi-Fi"
    with pytest.raises(ValueError, match="unknown a11y field 'kind'"):
        a11y.describe(node, kind="x")


def test_the_role_and_action_lists_are_tres():
    window = tre.Window(width=100, height=100)
    node = window.create("box", width=10, height=10)
    for role in a11y.ROLES:
        node.set(role=role)
    for live in a11y.LIVE:
        node.set(live=live)
    window.root.add_child(node)
    for action in a11y.ACTIONS:
        window.simulate("a11y_action", node=node, action=action)


def test_on_action_routes_each_action_and_can_share_a_views_dispatcher():
    view, window = _built(_rect("slider", a11y={"role": "slider"}))
    node = view.node("slider")
    seen = []
    view._listen(node, "a11y_action", lambda e: seen.append(("other", e.action)))
    undo = a11y.on_action(node, {"increment": lambda e: seen.append("up"),
                                 "set_value": lambda e: seen.append(("set", e.value))}, listen=view._listen)
    window.simulate("a11y_action", node=node, action="increment")
    window.simulate("a11y_action", node=node, action="decrement")  # no handler: ignored
    window.simulate("a11y_action", node=node, action="set_value", value=0.5)
    assert seen == [("other", "increment"), "up", ("other", "decrement"), ("other", "set_value"), ("set", 0.5)]
    undo()
    seen.clear()
    window.simulate("a11y_action", node=node, action="increment")
    assert seen == [("other", "increment")]
    with pytest.raises(ValueError, match=r"unknown a11y action\(s\) \['click'\]"):
        a11y.on_action(node, {"click": print})


def test_ring_geometry_uses_md3s_numbers():
    assert (interaction.RING_WIDTH, interaction.RING_OFFSET) == (3.0, 2.0)
    assert math.isclose(interaction.FOCUSED, 0.10)


def test_the_ring_fits_a_node_resized_outside_a_reconcile():
    view, window = _built(_rect("btn", handlers={"on_click": "go"}))
    view.node("btn").set(width=150)  # as a width binding does
    window.advance(16)
    _tab(window)
    assert view.interaction("btn").ring.get("layout_width") == 150 + 2 * (
        interaction.RING_OFFSET + interaction.RING_WIDTH)
