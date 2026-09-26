"""Real coverage for `tesserae.widgets`'s Selection & Input category --
`checkbox`/`slider`/`radio_button`/`switch`/`spin_box`. Since M40 each
returns a Tesserae control (P6), attached to the window's root; these
check the factory's arguments reach it.
"""

from tre import Window

from tesserae import controls
from tesserae.widgets import checkbox, radio_button, slider, spin_box, switch

PURPLE = (0x67, 0x50, 0xA4, 0xFF)


def test_checkbox_returns_a_checkbox_control_on_the_root():
    window = Window(width=200, height=100)
    box = checkbox(window, (0xFF, 0, 0, 0xFF), 24, 24, checked=True)
    assert isinstance(box, controls.Checkbox) and box.checked.get() is True
    assert box.node.parent() == window.root and box.node.get("width") == 24.0
    assert box.box.get("fill") == (0xFF, 0, 0, 0xFF)  # `background` is the selected colour
    window.simulate("click", node=box.node)
    assert box.checked.get() is False  # it toggles itself now


def test_checkbox_default_unchecked_and_placed_at_x_y():
    window = Window(width=200, height=100)
    box = checkbox(window, (0, 0, 0, 255), 24, 24, x=30, y=40)
    assert box.checked.get() is False
    assert (box.node.get("position"), box.node.get("x"), box.node.get("y")) == ("absolute", 30.0, 40.0)


def test_slider_returns_a_slider_control():
    window = Window(width=300, height=100)
    s = slider(window, (0x03, 0xDA, 0xC6, 0xFF), 200, 32, value=0.7)
    assert isinstance(s, controls.Slider) and s.value.get() == 0.7 and s.node.get("value") == 0.7
    assert (s.node.get("width"), s.node.get("height")) == (200.0, 32.0)


def test_radio_buttons_can_share_a_group():
    window = Window(width=200, height=100)
    group = controls.RadioGroup()
    a = radio_button(window, selected=True, group=group)
    b = radio_button(window, group=group)
    window.advance(16)
    window.simulate("click", node=b.node)
    assert (a.selected.get(), b.selected.get()) == (False, True)


def test_switch_returns_a_switch_control():
    window = Window(width=200, height=100)
    s = switch(window, selected=True)
    assert isinstance(s, controls.Switch) and s.selected.get() is True and s.node.get("checked") is True


def test_spin_box_takes_its_value_as_text_or_a_number():
    window = Window(width=300, height=100)
    a = spin_box(window, "3")
    b = spin_box(window, 2.5, step=0.5)
    assert isinstance(a, controls.SpinBox) and a.value.get() == 3 and a.input.get("text") == "3"
    assert b.value.get() == 2.5 and b.input.get("text") == "2.5"
