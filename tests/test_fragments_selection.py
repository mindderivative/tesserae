"""Real coverage for the Selection & Input component fragments
(`Checkbox`/`Slider`/`SpinBox`). `radio_button`/`switch` have no
fragment yet -- `engine-spec` has no declarative `NodeKindSpec` variant
for either (a real, deliberately deferred gap, matching `tre`'s own
M74 scope boundary -- see `BUILD_TRACKER.md`).
"""

import pytest
from tre import View, Window

from tesserae.spec import ComponentError, expand_components
from tesserae.widgets import spin_box

THEME_SEED = (0x67, 0x50, 0xA4, 0xFF)


def test_checkbox_matches_native_add_checkbox():
    yaml_text = """
id: root
kind: Container
style: {width: 200, height: 100}
children:
  - id: cb
    component: Checkbox
    with: {background: "#6750A4FF", width: 24, height: 24, checked: true}
"""
    expanded = expand_components(yaml_text)
    view = View("T.yaml", source=expanded)
    node = view.node("cb")
    assert node.get_checked() is True


def test_checkbox_checked_is_a_required_param_not_silently_defaulted():
    # Real, deliberate: `checked` has real semantic meaning, unlike a
    # style literal, so an author states it explicitly rather than
    # relying on an implicit default.
    yaml_text = """
id: root
kind: Container
children:
  - id: cb
    component: Checkbox
    with: {background: "#6750A4FF", width: 24, height: 24}
"""
    with pytest.raises(ComponentError, match=r"missing parameter"):
        expand_components(yaml_text)


def test_slider_matches_native_add_slider():
    yaml_text = """
id: root
kind: Container
style: {width: 200, height: 100}
children:
  - id: sl
    component: Slider
    with: {background: "#03DAC6FF", width: 200, height: 32, value: 0.7}
"""
    expanded = expand_components(yaml_text)
    view = View("T.yaml", source=expanded)
    node = view.node("sl")
    assert node.get("thumb_position") == 0.7


def test_spin_box_matches_the_imperative_catalog():
    yaml_text = """
id: root
kind: Container
style: {width: 200, height: 100}
children:
  - id: sb
    component: SpinBox
    with: {value: "3"}
"""
    expanded = expand_components(yaml_text)
    view = View("T.yaml", source=expanded, theme_seed=THEME_SEED)
    decrement = view.node("sb.decrement")
    field = view.node("sb.field")
    increment = view.node("sb.increment")

    window = Window(width=200, height=100)
    window.set_theme(THEME_SEED)
    imp_field, imp_minus, imp_plus = spin_box(window, "3")

    assert decrement.get("corner_radius") == imp_minus.get("corner_radius")
    assert field.get("corner_radius") == imp_field.get("corner_radius")
    assert increment.get("corner_radius") == imp_plus.get("corner_radius")
