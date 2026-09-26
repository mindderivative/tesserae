"""M40 Phase 1: the control foundation (`tesserae.controls.Control`),
proved on MD3's checkbox. Driven headlessly with `simulate`/`advance`.
"""

import math

import pytest
import tre

from tesserae import Effect, Signal, Theme, interaction, tokens
from tesserae.controls import DISABLED_CONTENT, STATE_LAYER_SIZE, TARGET_SIZE, Checkbox
from tesserae.listeners import Listeners

SEED = (0x67, 0x50, 0xA4, 0xFF)


def _window():
    window = tre.Window(width=300, height=200)
    window.root.set(padding_top=0, padding_right=0, padding_bottom=0, padding_left=0, gap=0,
                    align_items="flex_start", flex_direction="horizontal")
    before = window.create("box", width=40, height=40, focusable=True, role="button")
    window.root.add_child(before)  # something to Tab from, and to move the control off the origin
    return window, before


def _placed(control, window):
    window.root.add_child(control.node)
    window.advance(16)
    return control


def _frames(window, ms):
    for _ in range(math.ceil(ms / 16)):
        window.advance(16)


def _checkbox(**kwargs):
    window, before = _window()
    return _placed(Checkbox(window, **kwargs), window), window, before


# -- structure -----------------------------------------------------------------

def test_a_checkbox_is_an_md3_checkbox_in_a_48px_target():
    cb, window, _ = _checkbox(label="Accept terms")
    node = cb.node
    assert (node.get("layout_width"), node.get("layout_height")) == (TARGET_SIZE, TARGET_SIZE)
    assert (node.get("role"), node.get("label"), node.get("checked"), node.get("focusable")) == (
        "checkbox", "Accept terms", False, True)
    x, y = node.get("layout_x"), node.get("layout_y")
    inset = (TARGET_SIZE - STATE_LAYER_SIZE) / 2
    assert (cb.surface.get("layout_x") - x, cb.surface.get("layout_y") - y) == (inset, inset)
    assert cb.surface.get("corner_radius") == STATE_LAYER_SIZE / 2  # a circle
    assert (cb.box.get("layout_x") - x, cb.box.get("layout_width")) == ((TARGET_SIZE - 18) / 2, 18.0)
    assert (cb.box.get("corner_radius"), cb.box.get("stroke_width")) == (2.0, 2.0)
    assert cb.box.get("stroke_color") == tokens.BASELINE["on_surface_variant"]
    assert cb.box.get("fill") == (0, 0, 0, 0) and cb.mark.get("trim_end") == 0.0
    for decoration in (cb.surface, cb.box, cb.mark):
        assert decoration.get("hit_testable") is False and decoration.get("a11y_hidden") is True


def test_clicking_toggles_it_and_draws_the_check_in():
    cb, window, _ = _checkbox()
    seen = []
    cb.on_change(seen.append)
    window.simulate("click", node=cb.node)
    _frames(window, 64)
    assert cb.checked.get() is True and cb.node.get("checked") is True
    assert 0.0 < cb.mark.get("trim_end") < 1.0  # drawing in
    _frames(window, Theme.duration("medium1"))
    assert cb.mark.get("trim_end") == 1.0
    assert cb.box.get("fill") == tokens.BASELINE["primary"]
    assert cb.mark.get("stroke_color") == tokens.BASELINE["on_primary"]
    window.simulate("click", node=cb.node)
    _frames(window, Theme.duration("short3") + 16)
    assert cb.checked.get() is False and cb.mark.get("trim_end") == 0.0 and cb.box.get("fill") == (0, 0, 0, 0)
    assert seen == [True, False]


def test_setting_the_signal_repaints_it_without_a_change_event():
    cb, window, _ = _checkbox()
    seen = []
    cb.on_change(seen.append)
    cb.checked.set(True)
    _frames(window, 400)
    assert cb.node.get("checked") is True and cb.mark.get("trim_end") == 1.0
    assert seen == []  # on_change is the user's changes only, as HTML's `change`


def test_it_starts_in_the_state_given_without_animating():
    cb, window, _ = _checkbox(checked=True)
    assert cb.mark.get("trim_end") == 1.0 and cb.box.get("fill") == tokens.BASELINE["primary"]


def test_an_effect_can_follow_the_state():
    cb, window, _ = _checkbox()
    heard = []
    Effect(lambda: heard.append(cb.checked.get()))
    window.simulate("click", node=cb.node)
    assert heard == [False, True]


def test_on_changes_remover_stops_it():
    cb, window, _ = _checkbox()
    seen = []
    stop = cb.on_change(seen.append)
    stop()
    window.simulate("click", node=cb.node)
    assert seen == [] and cb.checked.get() is True


# -- keyboard and feedback ---------------------------------------------------------

def test_tab_focuses_it_with_a_ring_and_space_and_enter_toggle_it():
    cb, window, before = _checkbox()
    before.focus()
    window.simulate("key_down", key="tab")
    window.advance(16)
    assert cb.node.get("focused") is True and cb.interaction.ring_visible
    out = interaction.RING_OFFSET + interaction.RING_WIDTH
    assert cb.interaction.ring.get("layout_width") == STATE_LAYER_SIZE + 2 * out  # around the circle
    window.simulate("key_down", key="space")
    window.simulate("key_up", key="space")
    assert cb.checked.get() is True
    window.simulate("key_down", key="enter")
    assert cb.checked.get() is False


def test_the_state_layer_is_on_surface_unchecked_and_primary_checked():
    cb, window, _ = _checkbox()
    assert cb.interaction.layer.get("fill") == tokens.BASELINE["on_surface"]
    window.simulate("click", node=cb.node)
    window.advance(16)
    assert cb.interaction.layer.get("fill") == tokens.BASELINE["primary"]


def test_hover_shows_the_state_layer_in_the_circle():
    cb, window, _ = _checkbox()
    x, y = cb.node.get("layout_x"), cb.node.get("layout_y")
    window.simulate("pointer_move", x=x + 24, y=y + 24)
    _frames(window, 32)
    assert cb.interaction.layer.get("opacity") == pytest.approx(interaction.HOVERED)
    assert cb.interaction.layer.parent() == cb.interaction.clip and cb.interaction.clip.parent() == cb.surface


def test_a_press_ripples_from_the_press_point_inside_the_circle():
    cb, window, _ = _checkbox()
    x, y = cb.node.get("layout_x"), cb.node.get("layout_y")
    window.simulate("pointer_down", x=x + 14, y=y + 24)  # node-local (14, 24): surface-local (10, 20)
    window.advance(16)
    (circle,) = cb.interaction.ripples
    radius = circle.get("width") / 2
    assert (circle.get("x") + radius, circle.get("y") + radius) == pytest.approx((10, 20), abs=0.01)
    assert radius == pytest.approx(math.hypot(40 - 10, 40 - 20), abs=0.01)


# -- disabled ----------------------------------------------------------------------

def test_a_disabled_checkbox_cant_be_focused_or_used_and_draws_disabled():
    cb, window, before = _checkbox(checked=True, disabled=True)
    assert (cb.node.get("focusable"), cb.node.get("disabled")) == (False, True)
    off = (*tokens.BASELINE["on_surface"][:3], round(255 * DISABLED_CONTENT))
    assert cb.box.get("fill") == off and cb.mark.get("stroke_color") == tokens.BASELINE["surface"]
    window.simulate("click", node=cb.node)
    assert cb.checked.get() is True
    x, y = cb.node.get("layout_x"), cb.node.get("layout_y")
    window.simulate("pointer_move", x=x + 24, y=y + 24)
    window.simulate("pointer_down", x=x + 24, y=y + 24)
    _frames(window, 32)
    assert cb.interaction.layer.get("opacity") == 0.0 and cb.interaction.ripples == []
    cb.disabled.set(False)
    window.advance(16)
    assert cb.node.get("focusable") is True
    window.simulate("click", node=cb.node)
    assert cb.checked.get() is False


def test_disabling_mid_hover_clears_the_feedback():
    cb, window, _ = _checkbox()
    x, y = cb.node.get("layout_x"), cb.node.get("layout_y")
    window.simulate("pointer_move", x=x + 24, y=y + 24)
    _frames(window, 32)
    cb.disabled.set(True)
    window.advance(16)
    assert cb.interaction.layer.get("opacity") == 0.0


def test_unchecked_disabled_outline_is_on_surface_at_38_percent():
    cb, window, _ = _checkbox(disabled=True)
    assert cb.box.get("stroke_color") == (*tokens.BASELINE["on_surface"][:3], round(255 * DISABLED_CONTENT))


# -- theme ---------------------------------------------------------------------------

def test_colours_come_from_the_theme_and_follow_it():
    light = Theme.resolve(theme_seed=SEED)
    cb, window, _ = _checkbox(checked=True, theme=light)
    assert cb.box.get("fill") == light.role("primary")
    assert cb.interaction.ring.get("stroke_color") == light.role("secondary")
    dark = Theme.resolve(theme_seed=SEED, dark=True)
    cb.set_theme(dark)
    assert cb.box.get("fill") == dark.role("primary") != light.role("primary")
    assert cb.mark.get("stroke_color") == dark.role("on_primary")
    assert cb.interaction.layer.get("fill") == dark.role("primary")


def test_a_colour_override_replaces_primary():
    cb, window, _ = _checkbox(checked=True, color=(0xFF, 0x00, 0x00, 0xFF))
    assert cb.box.get("fill") == (0xFF, 0x00, 0x00, 0xFF)
    assert cb.interaction.layer.get("fill") == (0xFF, 0x00, 0x00, 0xFF)


def test_the_baseline_is_md3s_published_colours():
    assert tokens.BASELINE["primary"] == (0x67, 0x50, 0xA4, 0xFF)
    assert tokens.BASELINE["on_surface"] == (0x1D, 0x1B, 0x20, 0xFF)
    assert tokens.BASELINE["secondary"] == (0x62, 0x5B, 0x71, 0xFF)


# -- sharing and teardown ----------------------------------------------------------

def test_a_shared_dispatcher_lets_others_hear_the_same_node():
    window, _ = _window()
    events = Listeners()
    cb = _placed(Checkbox(window, listen=events.listen), window)
    clicks = []
    events.listen(cb.node, "click", lambda e: clicks.append(e))
    window.simulate("click", node=cb.node)
    assert cb.checked.get() is True and len(clicks) == 1


def test_destroy_frees_it_and_stops_following_its_signals():
    cb, window, _ = _checkbox()
    node, checked = cb.node, cb.checked
    cb.destroy()
    assert node not in interaction._INTERACTIVE
    checked.set(True)  # no repaint of freed nodes, no error
    window.advance(16)


def test_signals_are_tesserae_signals():
    cb, _, _ = _checkbox()
    assert isinstance(cb.checked, Signal) and isinstance(cb.disabled, Signal)
