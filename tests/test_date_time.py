"""M42 Phase 2: MD3's date-picker day, period selector and time input
field, Tesserae's since M42 (`tesserae.widgets.date_time`).
"""

import pytest
import tre

from tesserae import Theme, tokens
from tesserae.widgets import date_picker_day, period_selector, time_input_field

BASE = tokens.baseline_scheme()
SEED = (0x67, 0x50, 0xA4, 0xFF)
CLEAR = (0, 0, 0, 0)


def _window():
    window = tre.Window(width=600, height=400)
    window.root.set(padding_top=0, padding_right=0, padding_bottom=0, padding_left=0, gap=8,
                    align_items="flex_start")
    return window


def test_a_day_is_a_48px_target_with_md3s_40px_circle():
    window = _window()
    d = date_picker_day(window, 15)
    window.advance(16)
    indicator = d.part("indicator")
    assert d.node.get("layout_width") == 48.0 and indicator.get("layout_width") == 40.0
    assert indicator.get("corner_radius") == 20.0 and indicator.get("fill") == CLEAR
    assert d.part("label").get("fill") == BASE["on_surface"] and d.part("label").get("font_size") == 16.0
    assert (d.node.get("role"), d.node.get("label")) == ("button", "15")


@pytest.mark.parametrize("state, fill, stroke, ink", [
    ({"selected": True}, "primary", None, "on_primary"),
    ({"today": True}, None, "primary", "primary"),
    ({"selected": True, "today": True}, "primary", None, "on_primary"),
    ({"outside_month": True}, None, None, "on_surface_variant"),
])
def test_a_days_states(state, fill, stroke, ink):
    window = _window()
    d = date_picker_day(window, 3, **state)
    indicator = d.part("indicator")
    assert indicator.get("fill") == (BASE[fill] if fill else CLEAR)
    assert indicator.get("stroke_width") == (1.0 if stroke else 0.0)
    assert d.part("label").get("fill") == BASE[ink]


def test_a_days_state_follows_its_signals_and_a_click_reports_the_day():
    window = _window()
    heard = []
    d = date_picker_day(window, 9, on_click=heard.append)
    d.selected.set(True)
    assert d.part("indicator").get("fill") == BASE["primary"] and d.node.get("selected") is True
    window.simulate("click", node=d.node)
    assert heard == [9]


def test_the_period_selector_is_md3s():
    window = _window()
    ps = period_selector(window, "AM")
    window.advance(16)
    assert (ps.node.get("layout_width"), ps.node.get("layout_height")) == (52.0, 80.0)
    assert (ps.node.get("stroke_color"), ps.node.get("stroke_width"), ps.node.get("corner_radius")) == (
        BASE["outline"], 1.0, 8.0)
    assert ps.part("am").get("layout_height") == 40.0
    assert ps.part("am").get("fill") == BASE["tertiary_container"]
    assert ps.part("am_label").get("fill") == BASE["on_tertiary_container"]
    assert ps.part("pm").get("fill") == CLEAR and ps.part("pm_label").get("fill") == BASE["on_surface_variant"]
    assert ps.node.get("role") == "group" and ps.part("am").get("selected") is True


def test_the_period_switches_by_click_and_arrows():
    window = _window()
    ps = period_selector(window, "AM")
    heard = []
    ps.on_change(heard.append)
    window.simulate("click", node=ps.part("pm"))
    assert ps.period.get() == "PM" and ps.part("pm").get("fill") == BASE["tertiary_container"]
    ps.part("pm").focus()
    window.simulate("key_down", key="arrow_up")
    assert ps.period.get() == "AM" and ps.part("am").get("focused")
    assert heard == ["PM", "AM"]
    assert [ps.part(p).get("focusable") for p in ("am", "pm")] == [True, False]  # one Tab stop
    with pytest.raises(ValueError, match="'AM' or 'PM'"):
        period_selector(window, "noon")


def test_the_time_input_field_is_md3s():
    window = _window()
    tf = time_input_field(window, 7, "hour", label="Hour")
    window.advance(16)
    field = tf.part()
    assert (tf.box.get("layout_width"), tf.box.get("layout_height"), tf.box.get("corner_radius")) == (96.0, 72.0, 8.0)
    assert tf.box.get("fill") == BASE["surface_container_highest"]
    assert field.get("text") == "07" and field.get("font_size") == 45.0 and field.get("fill") == BASE["on_surface"]
    assert (field.get("role"), field.get("label"), field.get("value_max")) == ("textbox", "Hour", 23.0)
    left = field.get("layout_x") - tf.box.get("layout_x")
    assert left == pytest.approx((96 - field.get("layout_width")) / 2, abs=1.0)  # centred


def test_focus_takes_md3s_focused_colours():
    window = _window()
    tf = time_input_field(window, 5, "minute")
    tf.part().focus()
    window.advance(16)
    assert tf.box.get("fill") == BASE["primary_container"] and tf.box.get("stroke_width") == 2.0
    assert tf.part().get("fill") == BASE["on_primary_container"]


def test_the_arrows_step_and_wrap_and_typing_sets_a_valid_value():
    window = _window()
    tf = time_input_field(window, 0, "hour")
    heard = []
    tf.on_change(heard.append)
    field = tf.part()
    field.focus()
    window.simulate("key_down", key="arrow_down")
    assert tf.value.get() == 23 and field.get("text") == "23"  # wraps
    window.simulate("key_down", key="arrow_up")
    assert tf.value.get() == 0
    window.simulate("a11y_action", node=field, action="increment")
    assert tf.value.get() == 1
    field.set(text="")
    window.simulate("input", text="1")
    window.simulate("input", text="9")
    assert tf.value.get() == 19
    window.simulate("input", text="9")  # 199: out of range, not taken
    assert tf.value.get() == 19
    other = window.create("box", width=10, height=10, focusable=True)
    window.root.add_child(other)
    other.focus()
    window.advance(16)
    assert field.get("text") == "19"  # put back on leaving
    assert heard == [23, 0, 1, 19]  # typing "1" over a 1 is no change


def test_a_time_input_field_rejects_bad_values():
    window = _window()
    with pytest.raises(ValueError, match="'hour' or 'minute'"):
        time_input_field(window, 1, "second")
    with pytest.raises(ValueError, match="60 isn't a valid minute"):
        time_input_field(window, 60, "minute")


def test_date_and_time_follow_the_theme():
    window = _window()
    light, dark = Theme.resolve(theme_seed=SEED), Theme.resolve(theme_seed=SEED, dark=True)
    d = date_picker_day(window, 1, selected=True, theme=light)
    d.set_theme(dark)
    assert d.part("indicator").get("fill") == dark.role("primary")
    tf = time_input_field(window, 3, theme=light)
    window.advance(16)
    tf.set_theme(dark)
    window.advance(16)
    field = tf.part()
    assert tf.box.get("fill") == dark.role("surface_container_highest")
    digits = window.measure_text("00", font_family="Roboto", font_size=45.0, font_weight=400.0)[0]
    assert field.get("layout_width") == pytest.approx(digits + 4.0, abs=1.0)  # still two digits wide...
    assert field.get("layout_x") - tf.box.get("layout_x") == pytest.approx((96 - digits - 4.0) / 2, abs=1.0)  # centred
