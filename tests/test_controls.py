"""M40: Tesserae's MD3 controls (`tesserae.controls`) -- Phase 1's
foundation, proved on the checkbox; Phase 2's radio buttons (with
`RadioGroup`) and switch; Phase 3's slider and spin box; Phase 4's
progress and loading indicators and time picker dial. Driven headlessly
with `simulate`/`advance`.
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


# == M40 Phase 2: radio buttons and switches =========================================

from tesserae.controls import DISABLED_CONTAINER, RadioButton, RadioGroup, Switch  # noqa: E402


def _radios(n=3, **kwargs):
    window, before = _window()
    group = RadioGroup()
    buttons = [_placed(RadioButton(window, group=group, label=f"Option {i}", **kwargs), window) for i in range(n)]
    return buttons, group, window, before


def test_a_radio_button_is_md3s_ring_and_dot():
    (radio,), _, window, _ = _radios(1)
    assert (radio.node.get("role"), radio.node.get("checked")) == ("radio", False)
    assert (radio.ring.get("layout_width"), radio.ring.get("corner_radius"), radio.ring.get("stroke_width")) == (
        20.0, 10.0, 2.0)
    assert radio.ring.get("stroke_color") == tokens.BASELINE["on_surface_variant"]
    assert radio.dot.get("layout_width") == 10.0 and radio.dot.get("scale") == 0.0


def test_clicking_a_radio_selects_it_and_it_never_deselects_itself():
    window, _ = _window()
    radio = _placed(RadioButton(window), window)
    seen = []
    radio.on_change(seen.append)
    window.simulate("click", node=radio.node)
    _frames(window, Theme.duration("medium1") + 16)
    assert radio.selected.get() is True and radio.node.get("checked") is True
    assert radio.dot.get("scale") == 1.0 and radio.ring.get("stroke_color") == tokens.BASELINE["primary"]
    window.simulate("click", node=radio.node)
    assert radio.selected.get() is True and seen == [True]


def test_a_group_selects_one_at_a_time():
    buttons, group, window, _ = _radios()
    window.simulate("click", node=buttons[0].node)
    window.simulate("click", node=buttons[2].node)
    assert [b.selected.get() for b in buttons] == [False, False, True] and group.selected is buttons[2]
    buttons[1].selected.set(True)  # the app selecting one does the same
    window.advance(16)
    assert [b.selected.get() for b in buttons] == [False, True, False]


def test_a_group_is_one_tab_stop_and_the_arrows_move_the_selection():
    buttons, group, window, before = _radios()
    assert [b.node.get("focusable") for b in buttons] == [True, False, False]  # none selected: the first
    window.simulate("click", node=buttons[1].node)
    assert [b.node.get("focusable") for b in buttons] == [False, True, False]  # the selected one
    before.focus()
    window.simulate("key_down", key="tab")
    window.advance(16)
    assert buttons[1].node.get("focused") is True
    seen = []
    buttons[2].on_change(seen.append)
    window.simulate("key_down", key="arrow_down")
    assert [b.selected.get() for b in buttons] == [False, False, True]
    assert buttons[2].node.get("focused") is True and seen == [True]  # moved by the user: a change
    window.simulate("key_down", key="arrow_right")
    assert group.selected is buttons[0]  # wraps
    window.simulate("key_down", key="arrow_up")
    window.simulate("key_down", key="arrow_left")
    assert group.selected is buttons[1]


def test_the_arrows_skip_a_disabled_radio():
    buttons, group, window, _ = _radios()
    buttons[1].disabled.set(True)
    window.simulate("click", node=buttons[0].node)
    buttons[0].node.focus()
    window.simulate("key_down", key="arrow_down")
    assert group.selected is buttons[2]
    assert buttons[1].node.get("focusable") is False


def test_a_disabled_radio_draws_disabled_and_ignores_clicks():
    window, _ = _window()
    radio = _placed(RadioButton(window, selected=True, disabled=True), window)
    off = (*tokens.BASELINE["on_surface"][:3], round(255 * DISABLED_CONTENT))
    assert radio.ring.get("stroke_color") == off and radio.dot.get("fill") == off
    assert radio.node.get("focusable") is False


def test_a_radio_leaving_its_group_hands_on_the_tab_stop():
    buttons, group, window, _ = _radios()
    buttons[0].destroy()
    assert group.buttons == buttons[1:] and buttons[1].node.get("focusable") is True


def _switch(**kwargs):
    window, before = _window()
    return _placed(Switch(window, **kwargs), window), window, before


def test_a_switch_is_md3s_track_and_handle():
    sw, window, _ = _switch(label="Wi-Fi")
    node = sw.node
    assert (node.get("layout_width"), node.get("layout_height"), node.get("role")) == (52.0, 48.0, "switch")
    assert (sw.track.get("layout_width"), sw.track.get("layout_height"), sw.track.get("corner_radius")) == (
        52.0, 32.0, 16.0)
    assert sw.track.get("fill") == tokens.BASELINE["surface_container_highest"]
    assert sw.track.get("stroke_color") == tokens.BASELINE["outline"] and sw.track.get("stroke_width") == 2.0
    assert sw.handle.get("fill") == tokens.BASELINE["outline"]
    assert sw.handle.get("scale") * Switch.HANDLE == pytest.approx(16.0)
    assert sw.handle.get("translate_x") == 0.0


def test_switching_it_on_slides_and_grows_the_handle():
    sw, window, _ = _switch()
    seen = []
    sw.on_change(seen.append)
    window.simulate("click", node=sw.node)
    _frames(window, 64)
    assert 0.0 < sw.handle.get("translate_x") < Switch.TRAVEL  # sliding
    _frames(window, Theme.duration("medium2"))
    assert sw.selected.get() is True and sw.node.get("checked") is True and seen == [True]
    assert sw.handle.get("translate_x") == Switch.TRAVEL and sw.surface.get("translate_x") == Switch.TRAVEL
    assert sw.handle.get("scale") * Switch.HANDLE == pytest.approx(24.0)
    assert sw.track.get("fill") == tokens.BASELINE["primary"] and sw.handle.get("fill") == tokens.BASELINE["on_primary"]


def test_pressing_grows_the_handle_to_28px():
    sw, window, _ = _switch()
    x, y = sw.node.get("layout_x"), sw.node.get("layout_y")
    window.simulate("pointer_down", x=x + 16, y=y + 24)
    _frames(window, Theme.duration("short2") + 16)
    assert sw.handle.get("scale") * Switch.HANDLE == pytest.approx(28.0)
    window.simulate("pointer_up", x=x + 16, y=y + 24)
    _frames(window, Theme.duration("medium2") + 16)
    assert sw.selected.get() is True  # the press was a click
    assert sw.handle.get("scale") * Switch.HANDLE == pytest.approx(24.0)


def test_the_switchs_state_layer_follows_the_handle_and_its_ring_the_track():
    sw, window, before = _switch(selected=True)
    x = sw.node.get("layout_x")
    assert sw.surface.get("layout_x") - x == pytest.approx(16 + Switch.TRAVEL - 20)  # centred on the handle
    before.focus()
    window.simulate("key_down", key="tab")
    window.advance(16)
    out = interaction.RING_OFFSET + interaction.RING_WIDTH
    assert sw.interaction.ring.parent() == sw.track
    assert sw.interaction.ring.get("layout_width") == 52 + 2 * out
    window.simulate("key_down", key="space")
    window.simulate("key_up", key="space")
    assert sw.selected.get() is False


def test_a_disabled_switch_uses_md3s_disabled_colours():
    sw, window, _ = _switch(selected=True, disabled=True)
    on_surface = tokens.BASELINE["on_surface"]
    assert sw.track.get("fill") == (*on_surface[:3], round(255 * DISABLED_CONTAINER))
    assert sw.handle.get("fill") == tokens.BASELINE["surface"]
    assert sw.node.get("focusable") is False
    window.simulate("click", node=sw.node)
    assert sw.selected.get() is True
    off, _, _ = _switch(disabled=True)
    assert off.handle.get("fill") == (*on_surface[:3], round(255 * DISABLED_CONTENT))


def test_switch_and_radio_follow_the_theme():
    light, dark = Theme.resolve(theme_seed=SEED), Theme.resolve(theme_seed=SEED, dark=True)
    sw, window, _ = _switch(selected=True, theme=light)
    radio = _placed(RadioButton(window, selected=True, theme=light), window)
    assert sw.track.get("fill") == light.role("primary") and radio.dot.get("fill") == light.role("primary")
    sw.set_theme(dark)
    radio.set_theme(dark)
    assert sw.track.get("fill") == dark.role("primary") and radio.ring.get("stroke_color") == dark.role("primary")


# == M40 Phase 3: the slider and the spin box ===========================================

from tesserae.controls import Slider, SpinBox  # noqa: E402


def _slider(**kwargs):
    window, before = _window()
    window.root.set(flex_direction="vertical")
    return _placed(Slider(window, **kwargs), window), window, before


def test_a_slider_is_md3s_track_and_handle():
    s, window, _ = _slider(value=0.25, label="Volume")
    x = s.node.get("layout_x")
    assert (s.node.get("layout_width"), s.node.get("layout_height"), s.node.get("role")) == (200.0, 48.0, "slider")
    assert (s.node.get("value"), s.node.get("value_min"), s.node.get("value_max")) == (0.25, 0.0, 1.0)
    assert (s.inactive.get("layout_height"), s.inactive.get("layout_width")) == (4.0, 180.0)
    assert s.inactive.get("fill") == tokens.BASELINE["surface_container_highest"]
    assert s.active.get("fill") == tokens.BASELINE["primary"] and s.active.get("layout_width") == 45.0
    assert s.handle.get("layout_width") == 20.0 and s.handle.get("translate_x") == 45.0
    assert s.surface.get("layout_x") - x == pytest.approx(10 - 20 + 45)  # the state layer rides the handle


def test_pressing_and_dragging_set_the_value_and_change_fires_once_at_the_end():
    s, window, _ = _slider()
    seen = []
    s.on_change(seen.append)
    x, y = s.node.get("layout_x"), s.node.get("layout_y")
    window.simulate("pointer_down", x=x + 10 + 90, y=y + 24)  # the middle of the track
    assert s.value.get() == pytest.approx(0.5) and s.interaction.dragged
    window.simulate("pointer_move", x=x + 10 + 45, y=y + 24)
    assert s.value.get() == pytest.approx(0.25) and seen == []
    window.simulate("pointer_move", x=x + 900, y=y + 300)  # captured: the drag can leave the slider
    assert s.value.get() == 1.0
    window.simulate("pointer_up", x=x + 900, y=y + 300)
    assert seen == [1.0] and not s.interaction.dragged
    window.advance(16)
    assert s.interaction.layer.get("opacity") != pytest.approx(interaction.DRAGGED)


def test_the_dragged_state_layer_is_16_percent():
    s, window, _ = _slider()
    x, y = s.node.get("layout_x"), s.node.get("layout_y")
    window.simulate("pointer_down", x=x + 10, y=y + 24)
    _frames(window, 32)
    assert s.interaction.layer.get("opacity") == pytest.approx(interaction.DRAGGED)


def test_the_keys_step_the_value():
    s, window, _ = _slider(value=0.5)
    seen = []
    s.on_change(seen.append)
    s.node.focus()
    for key, expected in (("arrow_right", 0.51), ("arrow_up", 0.52), ("arrow_left", 0.51), ("arrow_down", 0.50),
                          ("page_up", 0.60), ("page_down", 0.50), ("end", 1.0), ("home", 0.0)):
        window.simulate("key_down", key=key)
        assert s.value.get() == pytest.approx(expected), key
    window.simulate("key_down", key="arrow_left")  # already at the start: no change
    assert len(seen) == 8


def test_a_stepped_range_snaps():
    s, window, _ = _slider(min=0, max=10, step=2, value=5)
    assert s.value.get() == 6.0  # halfway snaps up, as HTML's range input does
    x, y = s.node.get("layout_x"), s.node.get("layout_y")
    window.simulate("pointer_down", x=x + 10 + 180 * 0.33, y=y + 24)
    assert s.value.get() == 4.0
    s.node.focus()
    window.simulate("key_down", key="arrow_right")
    assert s.value.get() == 6.0 and s.node.get("value_step") == 2.0


def test_assistive_technology_can_set_and_step_the_value():
    s, window, _ = _slider(value=0.5)
    seen = []
    s.on_change(seen.append)
    window.simulate("a11y_action", node=s.node, action="increment")
    window.simulate("a11y_action", node=s.node, action="decrement")
    window.simulate("a11y_action", node=s.node, action="set_value", value=2.0)  # clamped
    assert seen == [pytest.approx(0.51), pytest.approx(0.5), 1.0]


def test_a_disabled_slider_ignores_the_pointer_and_keys():
    s, window, _ = _slider(value=0.5, disabled=True)
    on_surface = tokens.BASELINE["on_surface"]
    assert s.handle.get("fill") == (*on_surface[:3], round(255 * DISABLED_CONTENT))
    assert s.inactive.get("fill") == (*on_surface[:3], round(255 * DISABLED_CONTAINER))
    x, y = s.node.get("layout_x"), s.node.get("layout_y")
    window.simulate("pointer_down", x=x + 10, y=y + 24)
    window.simulate("key_down", key="home")
    assert s.value.get() == 0.5 and s.node.get("focusable") is False


def test_setting_the_value_moves_the_handle_at_once():
    s, window, _ = _slider()
    s.value.set(0.75)
    assert s.handle.get("translate_x") == pytest.approx(135.0) and s.node.get("value") == 0.75


def test_a_bad_range_or_step_is_an_error():
    window, _ = _window()
    with pytest.raises(ValueError, match="max > min"):
        Slider(window, min=1, max=1)
    with pytest.raises(ValueError, match="step must be positive"):
        Slider(window, step=0)


def _spin(**kwargs):
    window, before = _window()
    return _placed(SpinBox(window, **kwargs), window), window, before


def test_a_spin_box_is_two_buttons_and_a_field():
    sb, window, _ = _spin(value=5, label="Copies")
    assert [c == n for c, n in zip(sb.node.children(), (sb.decrement, sb.field, sb.increment))] == [True] * 3
    assert (sb.input.get("text"), sb.input.get("role"), sb.input.get("label")) == ("5", "textbox", "Copies")
    assert (sb.decrement.get("role"), sb.decrement.get("label"), sb.increment.get("label")) == (
        "button", "Decrease", "Increase")
    assert sb.field.get("fill") == tokens.BASELINE["surface_container_highest"]
    assert (sb.decrement.get("layout_width"), sb.field.get("layout_width")) == (40.0, 64.0)


def test_the_buttons_arrows_and_assistive_technology_step_it():
    sb, window, _ = _spin(value=5)
    seen = []
    sb.on_change(seen.append)
    window.simulate("click", node=sb.increment)
    window.simulate("click", node=sb.decrement)
    window.simulate("click", node=sb.decrement)
    sb.input.focus()
    window.simulate("key_down", key="arrow_up")
    window.simulate("a11y_action", node=sb.input, action="increment")
    assert seen == [6, 5, 4, 5, 6] and sb.input.get("text") == "6"


def test_typing_a_number_sets_it_and_leaving_restores_bad_text():
    sb, window, before = _spin(value=5, min=0, max=10)
    seen = []
    sb.on_change(seen.append)
    sb.input.focus()
    window.simulate("key_down", key="end")
    window.simulate("key_down", key="backspace")
    window.simulate("input", text="8")
    assert sb.value.get() == 8 and seen == [8]
    window.simulate("input", text="0")  # "80" is past max: not taken
    assert sb.value.get() == 8 and sb.input.get("text") == "80"
    before.focus()
    window.advance(16)
    assert sb.input.get("text") == "8"


def test_a_bound_disables_the_button_that_would_pass_it():
    sb, window, _ = _spin(value=9, max=10)
    window.simulate("click", node=sb.increment)
    window.advance(16)
    assert sb.value.get() == 10
    assert (sb.increment.get("focusable"), sb.increment.get("disabled")) == (False, True)
    window.simulate("click", node=sb.increment)
    assert sb.value.get() == 10
    assert sb.decrement.get("focusable") is True


def test_fractional_steps_and_disabled():
    sb, window, _ = _spin(value=0.5, step=0.25)
    window.simulate("click", node=sb.increment)
    assert sb.value.get() == 0.75 and sb.input.get("text") == "0.75"
    sb.disabled.set(True)
    window.advance(16)
    assert sb.input.get("focusable") is False and sb.increment.get("disabled") is True
    window.simulate("click", node=sb.increment)
    assert sb.value.get() == 0.75


def test_the_spin_box_follows_the_theme():
    light, dark = Theme.resolve(theme_seed=SEED), Theme.resolve(theme_seed=SEED, dark=True)
    sb, window, _ = _spin(theme=light)
    assert sb.field.get("fill") == light.role("surface_container_highest")
    sb.set_theme(dark)
    assert sb.field.get("fill") == dark.role("surface_container_highest")
    assert sb.input.get("fill") == dark.role("on_surface")


# == M40 Phase 4: progress, loading, the time picker dial =================================

from tesserae.controls import CircularProgress, LinearProgress, LoadingIndicator, TimePickerDial  # noqa: E402


def _numbers(data):
    import re
    return [float(n) for n in re.findall(r"-?\d+(?:\.\d+)?(?:e-?\d+)?", data)]


def _indicator(cls, **kwargs):
    window = tre.Window(width=400, height=300)
    window.root.set(padding_top=0, padding_right=0, padding_bottom=0, padding_left=0, align_items="flex_start")
    ind = cls(window, **kwargs)
    window.root.add_child(ind.node)
    window.advance(16)
    return ind, window


def test_linear_progress_is_md3s_track_and_bar():
    lp, window = _indicator(LinearProgress, value=0.5, label="Upload")
    assert (lp.node.get("role"), lp.node.get("label"), lp.node.get("value")) == ("progressbar", "Upload", 0.5)
    assert (lp.node.get("layout_width"), lp.node.get("layout_height")) == (240.0, 4.0)
    assert lp.node.get("fill") == tokens.BASELINE["surface_container_highest"] and lp.node.get("focusable") is False
    assert lp.bar.get("fill") == tokens.BASELINE["primary"]
    assert lp.bar.get("translate_x") == -120.0 and lp.node.get("clip_children") is True  # half shows


def test_linear_progress_slides_to_a_new_value():
    lp, window = _indicator(LinearProgress, value=0.0)
    lp.value.set(0.75)
    _frames(window, 64)
    assert -240.0 < lp.bar.get("translate_x") < -60.0
    _frames(window, Theme.duration("medium1"))
    assert lp.bar.get("translate_x") == pytest.approx(-60.0) and lp.node.get("value") == 0.75


def test_indeterminate_linear_progress_sweeps_forever_and_settles_on_a_value():
    lp, window = _indicator(LinearProgress)
    assert lp.indeterminate and lp.node.get("value") is None
    assert lp.bar.get("layout_width") == pytest.approx(0.4 * 240)
    wraps, last = 0, lp.bar.get("translate_x")
    for _ in range(3 * LinearProgress.SWEEP_MS // 16 + 8):
        window.advance(16)
        now = lp.bar.get("translate_x")
        wraps += now < last - 100  # jumped back to the start
        last = now
    assert wraps >= 2  # it sweeps again and again
    lp.value.set(0.25)
    window.advance(16)
    assert lp.bar.get("layout_width") == 240.0 and lp.bar.get("translate_x") == pytest.approx(-180.0)
    _frames(window, LinearProgress.SWEEP_MS * 2)
    assert lp.bar.get("translate_x") == pytest.approx(-180.0)  # the sweep stopped


def test_circular_progress_draws_the_value_clockwise_from_the_top():
    cp, window = _indicator(CircularProgress, value=0.25)
    assert (cp.node.get("layout_width"), cp.node.get("role")) == (48.0, "progressbar")
    # tre reads path data back normalised (arcs as curves), so check where it starts and ends
    assert cp.arc.get("data").startswith("M24,4 C") and cp.arc.get("stroke_width") == 4.0
    assert _numbers(cp.arc.get("data"))[-2:] == pytest.approx([24.0, 4.0])  # round the circle, back to the top
    assert cp.arc.get("trim_end") == 0.25 and cp.arc.get("stroke_color") == tokens.BASELINE["primary"]


def test_indeterminate_circular_progress_spins_and_stretches():
    cp, window = _indicator(CircularProgress)
    angles, arcs = set(), set()
    for _ in range(2 * CircularProgress.TURN_MS // 16):
        window.advance(16)
        angles.add(int(cp.arc.get("rotation_deg") // 45))
        arcs.add(round(cp.arc.get("trim_end"), 1))
    assert len(angles) == 8 and max(arcs) >= 0.7 and min(arcs) <= 0.2
    cp.value.set(0.5)
    window.advance(16)
    assert cp.arc.get("rotation_deg") == 0.0 and cp.arc.get("trim_end") == 0.5


def test_the_loading_indicator_morphs_through_md3s_shapes():
    li, window = _indicator(LoadingIndicator, color=(0xFF, 0, 0, 0xFF))
    assert (li.node.get("layout_width"), li.shape.get("layout_width")) == (48.0, 38.0)
    assert li.shape.get("fill") == (0xFF, 0, 0, 0xFF) and li.node.get("role") == "progressbar"
    assert _numbers(li.shape.get("data"))[:2] == pytest.approx([24.0, 0.0])  # the pentagon's top point
    steps = []
    for _ in range(4 * LoadingIndicator.STEP_MS // 16 + 8):
        window.advance(16)
        steps.append(li._step)
    assert set(steps) == {0, 1, 2, 3}  # every shape, and round again
    assert "C" in LoadingIndicator.SHAPES[1] and "C" in LoadingIndicator.SHAPES[3]  # the defined pill and oval


def test_destroying_an_indicator_stops_its_loop():
    li, window = _indicator(LoadingIndicator)
    li.destroy()
    _frames(window, 2 * LoadingIndicator.STEP_MS)  # no error from a loop on freed nodes


def test_indicators_follow_the_theme():
    light, dark = Theme.resolve(theme_seed=SEED), Theme.resolve(theme_seed=SEED, dark=True)
    lp, _ = _indicator(LinearProgress, value=0.5, theme=light)
    lp.set_theme(dark)
    assert lp.bar.get("fill") == dark.role("primary") != light.role("primary")
    assert lp.node.get("fill") == dark.role("surface_container_highest")


def _dial(**kwargs):
    window = tre.Window(width=400, height=400)
    window.root.set(padding_top=0, padding_right=0, padding_bottom=0, padding_left=0, align_items="flex_start")
    before = window.create("box", width=40, height=40, focusable=True, role="button")
    window.root.add_child(before)
    dial = TimePickerDial(window, **kwargs)
    window.root.add_child(dial.node)
    window.advance(16)
    return dial, window, before


def _on_dial(dial, degrees, radius=90.0):
    x = dial.node.get("layout_x") + 128 + radius * math.sin(math.radians(degrees))
    y = dial.node.get("layout_y") + 128 - radius * math.cos(math.radians(degrees))
    return x, y


def test_a_dial_is_md3s_face_hand_selector_and_numbers():
    dial, window, _ = _dial(hour=15, minute=30, label="Hour")
    assert (dial.node.get("layout_width"), dial.node.get("role"), dial.node.get("label")) == (256.0, "slider", "Hour")
    assert (dial.node.get("value"), dial.node.get("value_max")) == (15.0, 23.0)
    assert dial.face.get("fill") == tokens.BASELINE["surface_container_highest"]
    assert [n.get("text") for n in dial.numbers] == ["12"] + [str(i) for i in range(1, 12)]
    assert dial.numbers[3].get("fill") == tokens.BASELINE["on_primary"]  # 3 sits under the selector
    assert dial.numbers[4].get("fill") == tokens.BASELINE["on_surface"]
    assert (dial.selector.get("translate_x"), dial.selector.get("translate_y")) == pytest.approx((dial.RADIUS, 0.0))
    assert dial.selector.get("fill") == tokens.BASELINE["primary"] and dial.selector.get("layout_width") == 48.0
    assert _numbers(dial.hand.get("data")) == pytest.approx([128.0, 128.0, 128 + dial.RADIUS, 128.0])


def test_pressing_the_face_points_the_hour_and_moves_on_to_minutes():
    dial, window, _ = _dial(hour=14, minute=30)
    seen = []
    dial.on_change(seen.append)
    x, y = _on_dial(dial, 100)  # nearest 3 o'clock
    window.simulate("pointer_down", x=x, y=y)
    assert dial.hour.get() == 15 and dial.interaction.dragged  # kept PM
    x, y = _on_dial(dial, 185)
    window.simulate("pointer_move", x=x, y=y)
    assert dial.hour.get() == 18 and seen == []
    window.simulate("pointer_up", x=x, y=y)
    assert seen == [(18, 30)] and dial.mode.get() == "minute"
    window.advance(16)
    assert [n.get("text") for n in dial.numbers][:3] == ["00", "05", "10"]
    assert dial.node.get("value_max") == 59.0 and dial.numbers[6].get("fill") == tokens.BASELINE["on_primary"]


def test_minutes_snap_to_fives():
    dial, window, _ = _dial(mode="minute")
    x, y = _on_dial(dial, 6 * 22)  # 22 minutes
    window.simulate("pointer_down", x=x, y=y)
    window.simulate("pointer_up", x=x, y=y)
    assert dial.minute.get() == 20 and dial.mode.get() == "minute"


def test_the_keys_and_assistive_technology_step_the_active_hand():
    dial, window, before = _dial(hour=11, minute=55)
    before.focus()
    window.simulate("key_down", key="tab")
    window.advance(16)
    assert dial.node.get("focused") and dial.interaction.ring_visible
    assert dial.interaction.ring.parent() == dial.face
    window.simulate("key_down", key="arrow_up")
    assert dial.hour.get() == 0  # 11 → 12 in the AM half
    window.simulate("a11y_action", node=dial.node, action="decrement")
    assert dial.hour.get() == 11
    dial.mode.set("minute")
    window.simulate("key_down", key="arrow_right")
    assert dial.minute.get() == 0


def test_a_disabled_dial_ignores_input():
    dial, window, _ = _dial(hour=3, disabled=True)
    x, y = _on_dial(dial, 180)
    window.simulate("pointer_down", x=x, y=y)
    window.simulate("key_down", key="arrow_up")
    assert dial.hour.get() == 3 and dial.node.get("focusable") is False
    assert dial.selector.get("fill") == (*tokens.BASELINE["on_surface"][:3], round(255 * DISABLED_CONTENT))


def test_setting_the_hour_moves_the_hand():
    dial, window, _ = _dial(hour=0)
    dial.hour.set(6)
    _frames(window, Theme.duration("medium1") + 16)
    assert (dial.selector.get("translate_x"), dial.selector.get("translate_y")) == pytest.approx(
        (0.0, dial.RADIUS), abs=0.01)


def test_a_bad_dial_mode_is_an_error():
    window = tre.Window(width=100, height=100)
    with pytest.raises(ValueError, match="'hour' or 'minute'"):
        TimePickerDial(window, mode="second")
