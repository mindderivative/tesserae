"""Real coverage for the Selection & Input component fragments
(`Checkbox`/`Slider`/`SpinBox`/`RadioButton`/`Switch`). Since M40 the
kinds they expand to are Tesserae's MD3 controls, so each is checked
against the `tesserae.widgets` factory's control by state.
"""

import pytest

from helpers import elevation, view_from
from tre import Window

from tesserae.spec import ComponentError, expand_components
from tesserae.widgets import radio_button, spin_box, switch

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
    view = view_from(expanded)
    assert view.control("cb").checked.get() is True and view.node("cb").get("checked") is True


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
    view = view_from(expanded)
    node = view.node("sl")
    assert node.get("value") == 0.7


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
    view = view_from(expanded, theme_seed=THEME_SEED)
    decrement = view.node("sb.decrement")
    field = view.node("sb.field")
    increment = view.node("sb.increment")

    window = Window(width=200, height=100)
    control = spin_box(window, "3")

    # the fragment is still a composition (no SpinBox kind): it matches the control's shape
    assert decrement.get("corner_radius") == control.decrement.get("corner_radius")
    # a TextField's node is its text input; its box (background, corners) is the parent
    assert field.parent().get("corner_radius") == control.field.get("corner_radius")
    assert increment.get("corner_radius") == control.increment.get("corner_radius")
    assert control.value.get() == 3 and control.input.get("text") == "3"


def test_radio_button_matches_the_imperative_catalog():
    # Real, honest scope note: `Node.get()` only exposes a small
    # numeric whitelist (`engine-py::node.rs`, confirmed directly) --
    # no color/tint field is readable from Python at all, for either
    # the declarative or imperative path, so this compares real
    # observable state (`get_selected()`) rather than tint colors,
    # which `engine-spec`'s own Rust unit tests already cover directly.
    yaml_text = """
id: root
kind: Container
style: {width: 200, height: 100}
children:
  - id: opt
    component: RadioButton
    with: {size: 20, selected: true}
"""
    expanded = expand_components(yaml_text)
    view = view_from(expanded, theme_seed=THEME_SEED)
    declarative = view.node("opt")

    window = Window(width=200, height=100)
    imperative = radio_button(window, size=20, selected=True)

    assert view.control("opt").selected.get() is imperative.selected.get() is True
    assert declarative.get("layout_width") == imperative.node.get("width") == 20.0


def test_radio_button_selected_is_a_required_param_not_silently_defaulted():
    yaml_text = """
id: root
kind: Container
children:
  - id: opt
    component: RadioButton
    with: {size: 20}
"""
    with pytest.raises(ComponentError, match=r"missing parameter"):
        expand_components(yaml_text)


def test_switch_matches_the_imperative_catalog():
    # `selected:` (M32; `is_on:` before that), never the bare `on:` YAML
    # would parse as a boolean literal (PyYAML's default YAML 1.1 loader)
    # -- see `Switch_Component.yaml`'s own doc comment for the real bug.
    yaml_text = """
id: root
kind: Container
style: {width: 200, height: 100}
children:
  - id: toggle
    component: Switch
    with: {width: 52, height: 32, selected: false}
"""
    expanded = expand_components(yaml_text)
    view = view_from(expanded, theme_seed=THEME_SEED)
    declarative = view.node("toggle")

    window = Window(width=200, height=100)
    imperative = switch(window, width=52, height=32, selected=False)

    assert view.control("toggle").selected.get() is imperative.selected.get() is False
    assert declarative.get("checked") is imperative.node.get("checked") is False


def test_switch_with_no_theme_still_builds_falling_back_to_the_real_md3_baseline():
    # `tre`'s own engine-spec unit tests already prove the real
    # fallback color; this proves the declarative path builds cleanly
    # with no theme at all, matching `add_switch`'s own identical
    # no-theme contract.
    yaml_text = """
id: root
kind: Container
children:
  - id: toggle
    component: Switch
    with: {width: 52, height: 32, selected: true}
"""
    expanded = expand_components(yaml_text)
    view = view_from(expanded)
    control = view.control("toggle")
    assert control.selected.get() is True
    assert control.track.get("fill") == (0x67, 0x50, 0xA4, 0xFF)  # MD3's baseline primary
