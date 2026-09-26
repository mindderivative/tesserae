"""M39 Phase 2: MD3's state layer and ripple (`tesserae.interaction`), which
`tre` 0.3.5 no longer draws, applied to clickable YAML nodes (M39 Q2, Q3).
Driven headlessly with `simulate`/`advance`, as M34's checkbox spike was.
"""

import math

import pytest

import tesserae
from tesserae import View, interaction
from tesserae.spec.build import SpecBuildError

SEED = (0x67, 0x50, 0xA4, 0xFF)


def _rect(node_id, width=200, height=80, **extra):
    return {"id": node_id, "kind": "Rect",
            "style": {"width": width, "height": height, "background": "#DDDDDD", "corner_radius": 20}, **extra}


def _spec(*children):
    return {"id": "root", "kind": "Container", "children": list(children)}


class VM(tesserae.ViewModel):
    def __init__(self, view):
        self.clicks = 0
        super().__init__(view)

    def go(self):
        self.clicks += 1


def _frames(window, ms, step=16):
    for _ in range(math.ceil(ms / step)):
        window.advance(step)


def _built(*children, **kwargs):
    view = View(_spec(*children), **kwargs)
    view.window.advance(16)
    return view, view.window


def test_a_clickable_node_gets_a_state_layer_covering_it():
    view, window = _built(_rect("btn", handlers={"on_click": "go"}), _rect("plain"))
    it = view.interaction("btn")
    node = view.node("btn")
    assert it is not None and view.interaction("plain") is None
    assert node.children()[-1] == it.layer  # after the content, so it paints over it
    assert (it.layer.get("layout_x"), it.layer.get("layout_y")) == (0.0, 0.0)
    assert (it.layer.get("layout_width"), it.layer.get("layout_height")) == (200.0, 80.0)
    assert it.layer.get("hit_testable") is False and it.layer.get("opacity") == 0.0
    assert node.get("clip_children") is True  # clipped to the node's rounded box


def test_opting_out_and_in():
    view, _ = _built(
        _rect("off", handlers={"on_click": "go"}, interaction=False),
        _rect("on", interaction=True),
        {"id": "label", "kind": "Text", "text": {"content": "Hi", "font_family": "Roboto", "font_size": 14},
         "style": {"foreground": "#000000"}, "handlers": {"on_click": "go"}},
    )
    assert view.interaction("off") is None
    assert view.interaction("on") is not None  # `interaction: true` needs no on_click
    assert view.interaction("label") is None  # a text node can't hold the layer


@pytest.mark.parametrize("value", [5, {"colour": "primary"}])
def test_a_bad_interaction_field_is_an_error(value):
    with pytest.raises(SpecBuildError, match=r"takes true, false or \{color: \.\.\.\}"):
        View(_spec(_rect("btn", interaction=value)))


def test_interaction_needs_a_box():
    text = {"id": "t", "kind": "Text", "text": {"content": "Hi", "font_family": "Roboto", "font_size": 14},
            "style": {"foreground": "#000000"}, "interaction": {"color": "primary"}}
    with pytest.raises(SpecBuildError, match="needs a Rect or Container, not a Text"):
        View(_spec(text))


def test_hover_raises_the_layer_to_8_percent_including_over_children():
    child = {"id": "inner", "kind": "Rect", "style": {"width": 40, "height": 20, "background": "#000000"}}
    view, window = _built(_rect("btn", handlers={"on_click": "go"}, children=[child]))
    layer = view.interaction("btn").layer
    assert view.node("btn").children() == [view.node("inner"), layer]  # over the content
    window.simulate("pointer_move", x=150, y=60)
    _frames(window, 32)
    assert layer.get("opacity") == pytest.approx(interaction.HOVERED)
    window.simulate("pointer_move", x=10, y=10)  # onto the child: still hovering the node
    _frames(window, 32)
    assert layer.get("opacity") == pytest.approx(interaction.HOVERED)
    window.simulate("pointer_move", x=390, y=290)
    _frames(window, 32)
    assert layer.get("opacity") == 0.0


def test_a_press_ripples_from_the_press_point_and_covers_the_node():
    view, window = _built(_rect("btn", handlers={"on_click": "go"}))
    it = view.interaction("btn")
    window.simulate("pointer_down", x=10, y=10)
    window.advance(16)
    (circle,) = it.ripples
    radius = math.hypot(200 - 10, 80 - 10)  # to the farthest corner
    assert circle.get("width") == pytest.approx(2 * radius, abs=0.01)
    assert (circle.get("x") + radius, circle.get("y") + radius) == pytest.approx((10, 10), abs=0.01)
    assert circle.get("hit_testable") is False
    assert circle.get("scale") < 0.2  # starting small
    _frames(window, interaction.PRESS_GROW_MS)
    assert circle.get("scale") == pytest.approx(1.0)
    assert circle.get("opacity") == pytest.approx(interaction.PRESSED)  # held: it stays
    window.simulate("pointer_up", x=10, y=10)
    _frames(window, interaction.RELEASE_FADE_MS + 32)
    assert it.ripples == []
    assert view.node("btn").children() == [it.layer]  # the circle is freed


def test_a_quick_tap_still_shows_the_ripple_for_the_minimum_press():
    view, window = _built(_rect("btn", handlers={"on_click": "go"}))
    it = view.interaction("btn")
    window.simulate("pointer_down", x=100, y=40)
    window.advance(16)
    window.simulate("pointer_up", x=100, y=40)
    _frames(window, interaction.PRESS_FADE_IN_MS + 16)
    (circle,) = it.ripples
    assert circle.get("opacity") == pytest.approx(interaction.PRESSED)  # not faded yet
    _frames(window, interaction.MINIMUM_PRESS_MS + interaction.RELEASE_FADE_MS + 32)
    assert it.ripples == []


def test_dragging_a_press_off_the_node_releases_it():
    view, window = _built(_rect("btn", handlers={"on_click": "go"}))
    it = view.interaction("btn")
    window.simulate("pointer_move", x=100, y=40)
    window.simulate("pointer_down", x=100, y=40)
    _frames(window, interaction.MINIMUM_PRESS_MS + 16)
    window.simulate("pointer_move", x=390, y=290)
    _frames(window, interaction.RELEASE_FADE_MS + 32)
    assert it.ripples == [] and it.layer.get("opacity") == 0.0


def test_keyboard_focus_shows_the_focus_layer_and_enter_ripples_from_the_centre():
    view, window = _built(_rect("btn", handlers={"on_click": "go"}))
    vm = VM(view)
    it = view.interaction("btn")
    window.simulate("key_down", key="tab")
    _frames(window, 32)
    assert it.layer.get("opacity") == pytest.approx(interaction.FOCUSED)
    window.simulate("key_down", key="enter")
    window.advance(16)
    assert vm.clicks == 1  # the ViewModel's handler and the ripple share the click
    (circle,) = it.ripples
    radius = circle.get("width") / 2
    assert (circle.get("x") + radius, circle.get("y") + radius) == pytest.approx((100, 40), abs=0.01)
    _frames(window, interaction.MINIMUM_PRESS_MS + interaction.RELEASE_FADE_MS + 32)
    assert it.ripples == []


def test_pointer_focus_shows_no_focus_layer():
    view, window = _built(_rect("btn", handlers={"on_click": "go"}))
    VM(view)
    it = view.interaction("btn")
    window.simulate("click", node=view.node("btn"))  # a press focuses it, but not visibly
    window.simulate("pointer_move", x=390, y=290)
    _frames(window, 32)
    assert view.node("btn").get("focused") is True
    assert it.layer.get("opacity") == 0.0


def test_a_press_on_a_nested_clickable_ripples_only_the_nearest():
    inner = _rect("inner", width=60, height=30, handlers={"on_click": "go"})
    view, window = _built(_rect("outer", handlers={"on_click": "go"}, children=[inner]))
    vm = VM(view)
    window.simulate("pointer_down", x=10, y=10)
    window.advance(16)
    assert len(view.interaction("inner").ripples) == 1
    assert view.interaction("outer").ripples == []
    window.simulate("pointer_up", x=10, y=10)
    assert vm.clicks == 2  # the click itself still bubbles, as before


def test_the_tint_is_the_themes_on_surface_or_the_nodes_colour_and_follows_the_theme():
    view, window = _built(
        _rect("btn", handlers={"on_click": "go"}),
        _rect("brand", handlers={"on_click": "go"}, interaction={"color": "primary"}),
        _rect("hex", handlers={"on_click": "go"}, interaction={"color": "#FF000080"}),
        theme_seed=SEED,
    )
    light = view.theme
    assert view.interaction("btn").layer.get("fill") == light.role("on_surface")
    assert view.interaction("brand").layer.get("fill") == light.role("primary")
    assert view.interaction("hex").layer.get("fill") == (0xFF, 0, 0, 0x80)
    view.set_theme(theme_seed=SEED, dark=True)
    assert view.interaction("btn").layer.get("fill") == view.theme.role("on_surface") != light.role("on_surface")


def test_without_a_theme_the_tint_is_md3s_baseline_on_surface():
    view, _ = _built(_rect("btn", handlers={"on_click": "go"}))
    assert view.interaction("btn").layer.get("fill") == (0x1D, 0x1B, 0x20, 0xFF)


def test_reconcile_adds_and_removes_the_interaction():
    view, window = _built(_rect("btn"))
    VM(view)
    assert view.interaction("btn") is None
    view.reconcile(_spec(_rect("btn", handlers={"on_click": "go"})))
    it = view.interaction("btn")
    assert it is not None and view.node("btn").children()[-1] == it.layer
    view.reconcile(_spec(_rect("btn", handlers={"on_click": "go"},
                               children=[_rect("a", width=10, height=10)])))
    assert view.interaction("btn") is it  # kept, and still after the content
    assert view.node("btn").children() == [view.node("a"), it.layer]
    view.reconcile(_spec(_rect("btn")))
    assert view.interaction("btn") is None
    assert view.node("btn").children() == [] and view.node("btn").get("clip_children") is False


def test_a_removed_component_drops_its_interactions():
    host, window = _built(_rect("slot", width=300, height=200))
    component = host.instantiate(None, host.node("slot"), spec=_spec(_rect("btn", handlers={"on_click": "go"})))
    node = component.node("btn")
    assert node in interaction._INTERACTIVE
    component.remove()
    assert node not in interaction._INTERACTIVE
