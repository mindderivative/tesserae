"""M41: `tesserae.widgets`' composed widgets, built from their fragments
by Tesserae's compiler (`tesserae.widgets._composed.Widget`). Phase 1:
the base, proved on `button`.
"""

import math

import pytest
import tre

from tesserae import Theme, interaction, tokens
from tesserae.spec import expand_components
from tesserae.widgets import button
from tesserae.widgets._composed import Widget

SEED = (0x67, 0x50, 0xA4, 0xFF)
BASE = tokens.baseline_scheme()


def _window():
    window = tre.Window(width=500, height=300)
    window.root.set(padding_top=0, padding_right=0, padding_bottom=0, padding_left=0, gap=0,
                    align_items="flex_start")
    return window


@pytest.mark.parametrize("variant, fill, ink", [
    ("filled", "primary", "on_primary"),
    ("filled_tonal", "secondary_container", "on_secondary_container"),
    ("elevated", "surface_container_low", "primary"),
    ("outlined", None, "primary"),
    ("text", None, "primary"),
])
def test_each_variant_is_md3s_button(variant, fill, ink):
    window = _window()
    b = button(window, "Save", 120, 40, variant=variant)
    window.advance(16)
    assert b.node.parent() == window.root
    assert (b.node.get("layout_width"), b.node.get("layout_height"), b.node.get("corner_radius")) == (120.0, 40.0, 20.0)
    assert b.node.get("fill") == (BASE[fill] if fill else (0, 0, 0, 0))
    label = b.part("label")
    assert label.get("text") == "Save" and label.get("fill") == BASE[ink]
    assert b.interaction().layer.get("fill") == BASE[ink]  # MD3: the state layer is the content's colour
    if variant == "outlined":
        assert (b.node.get("stroke_color"), b.node.get("stroke_width")) == (BASE["outline"], 1.0)


def test_the_label_is_sized_to_its_text_and_centred():
    window = _window()
    b = button(window, "Save", 120, 40)
    window.advance(16)
    label = b.part("label")
    # label_large: Roboto 14/20, 500; tre's line_height is a multiple of the font size
    width, height = window.measure_text("Save", font_family="Roboto", font_size=14.0, font_weight=500.0,
                                        line_height=20.0 / 14.0)
    assert (label.get("width"), label.get("height")) == pytest.approx((width, 20.0), abs=0.01)
    x = label.get("layout_x") - b.node.get("layout_x")
    assert x == pytest.approx((120 - width) / 2, abs=1.0)  # centred (layout rounds to whole pixels)


def test_on_click_makes_it_a_keyboard_button():
    window = _window()
    clicks = []
    before = window.create("box", width=10, height=10, focusable=True, role="button")
    window.root.add_child(before)
    b = button(window, "Save", 120, 40, on_click=lambda: clicks.append("save"))
    window.advance(16)
    assert (b.node.get("role"), b.node.get("focusable")) == ("button", True)
    window.simulate("click", node=b.node)
    before.focus()
    window.simulate("key_down", key="tab")
    window.advance(16)
    assert b.node.get("focused") and b.interaction().ring_visible
    window.simulate("key_down", key="enter")
    assert clicks == ["save", "save"]


def test_stopping_on_click():
    window = _window()
    clicks = []
    b = button(window, "Save", 120, 40)
    stop = b.on_click(lambda: clicks.append(1))
    stop()
    window.simulate("click", node=b.node)
    assert clicks == []


def test_a_press_ripples_in_the_content_colour():
    window = _window()
    b = button(window, "Save", 120, 40, on_click=lambda: None)
    window.advance(16)
    window.simulate("pointer_down", node=b.node)
    window.advance(16)
    (circle,) = b.interaction().ripples
    assert circle.get("fill") == BASE["on_primary"]


def test_a_theme_colours_it_and_set_theme_follows():
    window = _window()
    light, dark = Theme.resolve(theme_seed=SEED), Theme.resolve(theme_seed=SEED, dark=True)
    b = button(window, "Save", 120, 40, theme=light)
    assert b.node.get("fill") == light.role("primary")
    b.set_theme(dark)
    assert b.node.get("fill") == dark.role("primary") != light.role("primary")
    assert b.part("label").get("fill") == dark.role("on_primary")
    assert b.interaction().layer.get("fill") == dark.role("on_primary")


def test_arguments_reach_the_button():
    window = _window()
    b = button(window, "Go", 80, 32, variant="outlined", x=5, y=6, border_color=(255, 0, 0, 255), border_width=2,
               corner_radius=4)
    assert (b.node.get("position"), b.node.get("x"), b.node.get("y")) == ("absolute", 5.0, 6.0)
    assert (b.node.get("stroke_color"), b.node.get("stroke_width"), b.node.get("corner_radius")) == (
        (255, 0, 0, 255), 2.0, 4.0)
    with pytest.raises(ValueError, match="unknown button variant 'huge'"):
        button(window, "x", 10, 10, variant="huge")


def test_the_python_and_yaml_paths_are_one_definition():
    """`button()` expands the same fragment a `component: ButtonFilled` does."""
    from tesserae import View

    window = _window()
    b = button(window, "Save", 120, 40)
    spec = expand_components('''
id: root
kind: Container
children:
  - id: button
    component: ButtonFilled
    with: {label: Save, width: 120, height: 40, corner_radius: 20}
''')
    import yaml
    view = View(yaml.safe_load(spec)["children"][0], theme_seed=tokens.BASELINE["primary"])
    view._use_scheme(BASE)
    for prop in ("fill", "corner_radius", "width", "height", "align_items", "justify_content"):
        assert view.root.get(prop) == b.node.get(prop), prop


def test_a_widget_has_named_parts_and_can_be_destroyed():
    window = _window()
    b = button(window, "Save", 120, 40, on_click=lambda: None)
    node = b.node
    with pytest.raises(ValueError, match="no part 'icon'"):
        b._spec_of(b.spec, "icon")
    b.destroy()
    assert node not in interaction._INTERACTIVE


def test_without_a_theme_every_role_has_a_colour():
    scheme = tokens.baseline_scheme()
    assert set(tokens.ROLES) <= set(scheme)
    assert scheme["primary"] == tokens.BASELINE["primary"] and scheme["on_surface"] == (0x1D, 0x1B, 0x20, 0xFF)
