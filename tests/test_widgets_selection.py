"""Real coverage for `tesserae.widgets`'s Selection & Input category --
`checkbox`/`slider`/`radio_button`/`switch`/`spin_box`. Same thin-delegate
parity strategy as `test_widgets_buttons.py`: construct the same widget
two ways and assert the real, gettable state matches.
"""

from tre import Window

from tesserae.widgets import checkbox, radio_button, slider, spin_box, switch


def test_checkbox_matches_native_add_checkbox():
    window = Window(width=200, height=100)
    a = checkbox(window, (0x67, 0x50, 0xA4, 0xFF), 24, 24, checked=True)
    b = window.add_checkbox((0x67, 0x50, 0xA4, 0xFF), 24, 24, checked=True)
    assert a.get_checked() == b.get_checked() is True


def test_checkbox_default_unchecked_matches_native():
    window = Window(width=200, height=100)
    a = checkbox(window, (0, 0, 0, 255), 24, 24)
    b = window.add_checkbox((0, 0, 0, 255), 24, 24)
    assert a.get_checked() == b.get_checked() is False


def test_slider_matches_native_add_slider():
    window = Window(width=200, height=100)
    a = slider(window, (0x03, 0xDA, 0xC6, 0xFF), 200, 32, value=0.7)
    b = window.add_slider((0x03, 0xDA, 0xC6, 0xFF), 200, 32, value=0.7)
    assert a.get("thumb_position") == b.get("thumb_position") == 0.7


def test_radio_button_matches_native_add_radio_button():
    window = Window(width=200, height=100)
    a = radio_button(window, size=24.0, selected=True)
    b = window.add_radio_button(size=24.0, selected=True)
    assert a.get("select_progress") == b.get("select_progress")


def test_switch_matches_native_add_switch():
    window = Window(width=200, height=100)
    a = switch(window, on=True)
    b = window.add_switch(on=True)
    assert a.get("toggle_progress") == b.get("toggle_progress")


def test_spin_box_matches_native_add_spin_box():
    window = Window(width=200, height=100)
    a_field, a_minus, a_plus = spin_box(window, "3")
    b_field, b_minus, b_plus = window.add_spin_box("3")
    assert a_field.get("corner_radius") == b_field.get("corner_radius")
    assert a_minus.get("corner_radius") == b_minus.get("corner_radius")
