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


# == M41 Phase 2: icon buttons, FABs, split buttons, button groups ==========================

from tesserae.widgets import button_group, extended_fab, fab, icon_button, split_button  # noqa: E402
from tesserae.widgets.buttons import GROUP_GROWTH, SPLIT_TIGHTENED  # noqa: E402


def _frames(window, ms):
    for _ in range(math.ceil(ms / 16)):
        window.advance(16)


def _offset(node, parent):
    return node.get("layout_x") - parent.get("layout_x"), node.get("layout_y") - parent.get("layout_y")


@pytest.mark.parametrize("variant, fill, ink", [
    ("standard", None, "on_surface_variant"),
    ("filled", "primary", "on_primary"),
    ("filled_tonal", "secondary_container", "on_secondary_container"),
    ("outlined", None, "on_surface_variant"),
])
def test_icon_buttons_are_md3s(variant, fill, ink):
    window = _window()
    ib = icon_button(window, "close", variant=variant, label="Close")
    window.advance(16)
    assert (ib.node.get("layout_width"), ib.node.get("corner_radius"), ib.node.get("label")) == (40.0, 20.0, "Close")
    assert ib.node.get("fill") == (BASE[fill] if fill else (0, 0, 0, 0))
    assert ib.part("icon").get("fill") == BASE[ink] and ib.interaction().layer.get("fill") == BASE[ink]
    assert _offset(ib.part("icon"), ib.node) == (8.0, 8.0)  # centred


@pytest.mark.parametrize("size, box, radius, glyph", [("small", 40, 12, 24), ("default", 56, 16, 24),
                                                      ("large", 96, 28, 36)])
def test_fab_sizes_are_md3s(size, box, radius, glyph):
    window = _window()
    f = fab(window, "add", size=size, variant="primary")
    window.advance(16)
    assert (f.node.get("layout_width"), f.node.get("corner_radius")) == (box, radius)
    assert f.part("icon").get("layout_width") == glyph
    assert _offset(f.part("icon"), f.node) == ((box - glyph) / 2, (box - glyph) / 2)
    assert f.node.get("fill") == BASE["primary_container"] and f.part("icon").get("fill") == BASE["on_primary_container"]


def test_fab_rejects_an_unknown_size_or_variant():
    window = _window()
    with pytest.raises(ValueError, match="unknown FAB size 'huge'"):
        fab(window, "add", size="huge")
    with pytest.raises(ValueError, match="unknown FAB variant 'pink'"):
        fab(window, "add", variant="pink")


def test_an_extended_fab_with_and_without_an_icon():
    window = _window()
    with_icon = extended_fab(window, "Compose", 160, icon="add")
    without = extended_fab(window, "Go", 100)
    window.advance(16)
    assert with_icon.part("icon").get("layout_width") == 24.0 and with_icon.node.get("layout_height") == 56.0
    with pytest.raises(ValueError):
        without.part("icon")
    label = without.part("label")
    assert _offset(label, without.node)[0] == pytest.approx((100 - label.get("width")) / 2, abs=1.0)  # centred


def test_a_split_buttons_facing_corners_tighten_while_hovered():
    window = _window()
    actions = []
    sb = split_button(window, "Send", 100, 40, on_click=lambda: actions.append("send"),
                      on_menu=lambda: actions.append("menu"))
    window.advance(16)
    leading, trailing = sb.part("leading"), sb.part("trailing")
    x, y = leading.get("layout_x"), leading.get("layout_y")
    window.simulate("pointer_move", x=x + 10, y=y + 10)
    _frames(window, 150)
    tight = SPLIT_TIGHTENED
    assert tuple(leading.get("corner_radius")) == (20.0, tight, tight, 20.0)
    assert tuple(trailing.get("corner_radius")) == (tight, 20.0, 20.0, tight)
    assert tuple(sb.interaction("leading").clip.get("corner_radius")) == (20.0, tight, tight, 20.0)  # feedback follows
    window.simulate("pointer_move", x=490, y=290)
    _frames(window, 150)
    assert tuple(leading.get("corner_radius")) == (20.0,) * 4
    window.simulate("click", node=leading)
    assert actions == ["send"]
    window.simulate("click", node=trailing)
    assert actions == ["send", "menu"]


def test_a_button_group_reshapes_and_reflows_the_pressed_button_and_restores_it():
    window = _window()
    heard = []
    bg = button_group(window, ["A", "B", "C"], 60, 40, on_click=heard.append)
    window.advance(16)
    b1 = bg.part("b1")
    x, y = b1.get("layout_x"), b1.get("layout_y")
    window.simulate("pointer_down", x=x + 5, y=y + 5)
    _frames(window, 150)
    widths = [bg.part(f"b{i}").get("width") for i in range(3)]
    assert widths == [60 - GROUP_GROWTH / 2, 60 + GROUP_GROWTH, 60 - GROUP_GROWTH / 2] and sum(widths) == 180
    assert b1.get("corner_radius") == 12.0  # tightened, for a 40 px button
    window.simulate("pointer_up", x=x + 5, y=y + 5)
    _frames(window, 150)
    assert [bg.part(f"b{i}").get("width") for i in range(3)] == [60.0] * 3 and b1.get("corner_radius") == 20.0
    assert heard == [1]


def test_pressing_an_end_button_takes_from_its_one_neighbour():
    window = _window()
    bg = button_group(window, ["A", "B", "C"], 60, 32)
    window.advance(16)
    b0 = bg.part("b0")
    window.simulate("pointer_move", x=b0.get("layout_x") + 5, y=b0.get("layout_y") + 5)  # the pointer arrives first
    window.simulate("pointer_down", x=b0.get("layout_x") + 5, y=b0.get("layout_y") + 5)
    _frames(window, 150)
    assert [bg.part(f"b{i}").get("width") for i in range(3)] == [72.0, 48.0, 60.0]
    assert b0.get("corner_radius") == 8.0  # up to 38 px: 8
    window.simulate("pointer_move", x=490, y=290)  # dragged away: released
    assert [bg.part(f"b{i}").get("width") for i in range(3)] == [60.0] * 3


def test_repeated_presses_dont_compound():
    """`tre`'s reflow compounded on every layout pass; this one doesn't."""
    window = _window()
    bg = button_group(window, ["A", "B"], 60, 40)
    window.advance(16)
    b0 = bg.part("b0")
    for _ in range(3):
        window.simulate("pointer_down", x=b0.get("layout_x") + 5, y=b0.get("layout_y") + 5)
        _frames(window, 50)
    assert bg.part("b0").get("width") == 72.0
