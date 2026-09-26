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


# == M41 Phase 3: containment and lists ======================================================

from tesserae.widgets import (  # noqa: E402
    accordion_header, badge, card, chip, divider, icon, link, list_, list_item, tree_node,
)


@pytest.mark.parametrize("variant, fill", [("elevated", "surface_container_low"),
                                           ("filled", "surface_container_highest"), ("outlined", "surface")])
def test_cards_are_md3s_and_actionable_ones_get_feedback(variant, fill):
    window = _window()
    plain = card(window, 200, 100, variant=variant)
    clicks = []
    actionable = card(window, 200, 100, variant=variant, on_click=lambda: clicks.append(1))
    window.advance(16)
    assert plain.node.get("fill") == BASE[fill] and plain.node.get("corner_radius") == 12.0
    assert plain.interaction() is None and plain.node.get("focusable") is False
    assert actionable.interaction() is not None and actionable.node.get("role") == "button"
    window.simulate("click", node=actionable.node)
    assert clicks == [1]


def test_a_chips_content_is_padded_and_centred():
    window = _window()
    c = chip(window, "Help", 100)
    window.advance(16)
    label = c.part("label")
    assert c.node.get("layout_height") == 32.0 and c.node.get("stroke_color") == BASE["outline"]
    x, y = _offset(label, c.node)
    assert x == 16.0 and y == pytest.approx((32 - label.get("height")) / 2, abs=1.0)


def test_a_filter_chip_toggles_its_selection():
    window = _window()
    c = chip(window, "Wi-Fi", 110, variant="filter")
    window.advance(16)
    assert c.selected.get() is False and c.part("check").parent() is None
    assert c.node.get("role") == "checkbox" and c.node.get("checked") is False
    window.simulate("click", node=c.node)
    window.advance(16)
    assert c.selected.get() is True and c.node.get("checked") is True
    assert c.node.get("fill") == BASE["secondary_container"] and c.node.get("stroke_width") == 0.0
    assert c.part("check").parent() == c.node and c.part("label").get("fill") == BASE["on_secondary_container"]
    window.simulate("key_down", key="space")
    window.simulate("key_up", key="space")
    assert c.selected.get() is False and c.part("check").parent() is None


def test_a_filter_chip_keeps_its_selection_through_a_theme_change():
    window = _window()
    c = chip(window, "On", 100, variant="filter", selected=True)
    dark = Theme.resolve(theme_seed=SEED, dark=True)
    c.set_theme(dark)
    assert c.node.get("fill") == dark.role("secondary_container")


def test_a_removable_input_chip_has_a_close_button():
    window = _window()
    removed = []
    c = chip(window, "Ana", 100, variant="input", removable=True, on_remove=lambda: removed.append(1))
    window.advance(16)
    close = c.part("remove")
    assert (close.get("role"), close.get("label")) == ("button", "Remove Ana")
    window.simulate("click", node=close)
    assert removed == [1]


def test_badges_are_md3s():
    window = _window()
    dot, labelled, fitted = badge(window), badge(window, "3", width=20), badge(window, "999+")
    window.advance(16)
    assert (dot.node.get("layout_width"), dot.node.get("fill")) == (6.0, BASE["error"])
    assert labelled.node.get("layout_height") == 16.0 and labelled.part("label").get("fill") == BASE["on_error"]
    assert fitted.node.get("width") == pytest.approx(fitted.part("label").get("width") + 8.0)


def test_dividers():
    window = _window()
    h, v = divider(window, 200), divider(window, 40, orientation="vertical", border_width=2)
    window.advance(16)
    assert (h.node.get("layout_width"), h.node.get("layout_height"), h.node.get("fill")) == (
        200.0, 1.0, BASE["outline_variant"])
    assert (v.node.get("layout_width"), v.node.get("layout_height")) == (2.0, 40.0)
    assert h.node.get("a11y_hidden") is True
    with pytest.raises(ValueError, match="'horizontal' or 'vertical'"):
        divider(window, 10, orientation="diagonal")


def test_a_link_is_a_box_holding_its_text():
    window = _window()
    followed = []
    ln = link(window, "Docs", 60, on_click=lambda: followed.append(1))
    window.advance(16)
    assert (ln.node.get("role"), ln.node.get("label")) == ("link", "Docs")
    window.simulate("pointer_down", node=ln.node)
    window.simulate("pointer_up", node=ln.node)
    assert followed == [1]


def test_list_items_are_md3s_one_and_two_line_rows():
    window = _window()
    one = list_item(window, "Inbox", leading_icon="home", trailing_icon="chevron_right", width=300)
    two = list_item(window, "Drafts", supporting_text="3 messages", width=300)
    window.advance(16)
    assert one.node.get("layout_height") == 56.0 and two.node.get("layout_height") == 72.0
    headline = one.part("headline")
    assert headline.get("font_size") == 16.0 and headline.get("fill") == BASE["on_surface"]  # body_large
    assert one.part("leading").get("fill") == BASE["on_surface_variant"] and one.part("trailing") is not None
    assert _offset(one.part("leading"), one.node)[0] == 16.0
    supporting = two.part("supporting")
    assert supporting.get("text") == "3 messages" and supporting.get("fill") == BASE["on_surface_variant"]


def test_a_list_holds_its_items():
    window = _window()
    items = [list_item(window, "A"), list_item(window, "B")]
    ls = list_(window, items, width=240)
    window.advance(16)
    assert ls.node.get("role") == "list" and [c == i.node for c, i in zip(ls.node.children(), items)] == [True] * 2
    assert all(i.node.get("role") == "listitem" and i.node.get("width") == 240.0 for i in items)
    with pytest.raises(ValueError, match="at least one item"):
        list_(window, [])


def test_an_accordion_header_expands_and_its_chevron_turns():
    window = _window()
    acc = accordion_header(window, "Details")
    heard = []
    acc.on_change(heard.append)
    window.advance(16)
    chevron = acc.part("chevron")
    assert acc.expanded.get() is False and acc.node.get("expanded") is False and chevron.get("rotation_deg") == 0.0
    window.simulate("click", node=acc.node)
    _frames(window, 200)
    assert acc.expanded.get() is True and acc.node.get("expanded") is True and chevron.get("rotation_deg") == 180.0
    window.simulate("a11y_action", node=acc.node, action="collapse")
    assert acc.expanded.get() is False and heard == [True, False]
    acc.expanded.set(True)  # the app's change: no on_change
    assert heard == [True, False]


def test_a_tree_node_is_a_treeitem_and_the_arrows_expand_it():
    window = _window()
    branch = tree_node(window, "src", depth=1)
    leaf = tree_node(window, "a.py", depth=2, leaf=True)
    window.advance(16)
    assert (branch.node.get("role"), branch.node.get("level"), leaf.node.get("level")) == ("treeitem", 2, 3)
    assert branch.part("chevron").get("rotation_deg") == -90.0  # collapsed: pointing right
    assert _offset(branch.part("title"), branch.node)[0] == 16 + 24
    branch.node.focus()
    window.simulate("key_down", key="arrow_right")
    _frames(window, 200)
    assert branch.expanded.get() is True and branch.part("chevron").get("rotation_deg") == 0.0
    window.simulate("key_down", key="arrow_left")
    assert branch.expanded.get() is False
    assert leaf.expanded is None and leaf.node.get("focusable") is True


def test_icon_is_tesseraes_own():
    window = _window()
    ic = icon(window, "home", (1, 2, 3, 255), 24)
    named = icon(window, "search", (0, 0, 0, 255), 24, label="Search")
    assert ic.node.get("fill") == (1, 2, 3, 255) and ic.node.get("a11y_hidden") is True
    assert (named.node.get("role"), named.node.get("label")) == ("img", "Search")
    with pytest.raises(ValueError, match="unknown icon 'nope'"):
        icon(window, "nope", (0, 0, 0, 255), 24)


# == M41 Phase 4: navigation ===================================================================

from tesserae.widgets import navigation_drawer, navigation_rail, status_bar, tabs, toolbar, top_app_bar  # noqa: E402


def test_tabs_are_md3s_primary_tabs():
    window = _window()
    tb = tabs(window, ["Photos", "Videos", "Music"], selected=0, width=360)
    window.advance(16)
    assert tb.node.get("layout_height") == 48.0 and tb.part("item0").get("layout_width") == 120.0
    assert tb.part("row").get("role") == "tablist"
    assert [tb.part(f"item{i}").get("role") for i in range(3)] == ["tab"] * 3
    assert tb.part("item0.label").get("fill") == BASE["primary"]
    assert tb.part("item1.label").get("fill") == BASE["on_surface_variant"]
    assert tb.part("item0.label").get("font_size") == 14.0  # title_small
    label = tb.part("item0.label")
    assert tb.indicator.get("width") == pytest.approx(label.get("width"))  # it spans the label
    assert tb.indicator.get("layout_height") == 3.0 and tb.indicator.get("fill") == BASE["primary"]
    assert tb.part("divider").get("fill") == BASE["surface_variant"]


def test_clicking_a_tab_selects_it_and_the_indicator_slides():
    window = _window()
    tb = tabs(window, ["A", "B", "C"], selected=0, width=300)
    heard = []
    tb.on_change(heard.append)
    window.advance(16)
    start = tb.indicator.get("translate_x")
    window.simulate("click", node=tb.part("item2"))
    span = tb.indicator.get("width")
    final = 200 + (100 - span) / 2
    _frames(window, 64)
    assert start < tb.indicator.get("translate_x") < final - 5  # sliding, not there yet
    _frames(window, 400)
    assert tb.indicator.get("translate_x") == pytest.approx(final)
    assert tb.selected.get() == 2 and heard == [2] and tb.part("item2").get("selected") is True


def test_tabs_keep_their_selection_colours_through_a_theme_change():
    window = _window()
    tb = tabs(window, ["A", "B"], selected=1, width=200)
    dark = Theme.resolve(theme_seed=SEED, dark=True)
    tb.set_theme(dark)
    assert tb.part("item1.label").get("fill") == dark.role("primary")
    assert tb.part("item0.label").get("fill") == dark.role("on_surface_variant")


def test_tabs_are_one_tab_stop_and_the_arrows_move_the_selection():
    window = _window()
    tb = tabs(window, ["A", "B", "C"], selected=1, width=300)
    window.advance(16)
    assert [tb.part(f"item{i}").get("focusable") for i in range(3)] == [False, True, False]
    tb.part("item1").focus()
    window.simulate("key_down", key="arrow_right")
    assert tb.selected.get() == 2 and tb.part("item2").get("focused")
    window.simulate("key_down", key="arrow_right")
    assert tb.selected.get() == 0  # wraps
    window.simulate("key_down", key="arrow_left")
    assert tb.selected.get() == 2


def test_tabs_with_icons_are_64px_and_the_app_can_select_without_a_change():
    window = _window()
    tb = tabs(window, ["Home", "Find"], icons=["home", "search"], width=200)
    heard = []
    tb.on_change(heard.append)
    window.advance(16)
    assert tb.node.get("layout_height") == 64.0 and tb.selected.get() is None
    assert tb.indicator.get("visible") is False
    tb.selected.set(1)
    window.advance(16)
    assert tb.part("item1.icon").get("fill") == BASE["primary"] and tb.indicator.get("visible") is True
    assert heard == []


def test_navigation_tabs_reject_bad_arguments():
    window = _window()
    with pytest.raises(ValueError, match="out of range"):
        tabs(window, ["A"], selected=3)
    with pytest.raises(ValueError, match="2 icons for 1 tabs"):
        tabs(window, ["A"], icons=["home", "add"])
    with pytest.raises(ValueError, match="a label and an icon per item"):
        navigation_rail(window, ["A", "B"], ["home"])


def test_the_navigation_rail_is_md3s():
    window = _window()
    rail = navigation_rail(window, ["Home", "Mail", "Chat"], ["home", "search", "menu"], selected=1)
    window.advance(16)
    assert rail.node.get("layout_width") == 80.0
    pill = rail.part("item1.pill")
    assert (pill.get("layout_width"), pill.get("layout_height"), pill.get("corner_radius")) == (56.0, 32.0, 16.0)
    assert pill.get("fill") == BASE["secondary_container"]
    assert rail.part("item1.icon").get("fill") == BASE["on_secondary_container"]
    assert rail.part("item0.pill").get("fill") == (0, 0, 0, 0)
    assert rail.part("item0.label").get("font_size") == 12.0  # label_medium
    rail.part("item1").focus()
    window.simulate("key_down", key="arrow_down")
    assert rail.selected.get() == 2


def test_the_navigation_drawer_is_md3s():
    window = _window()
    drawer = navigation_drawer(window, ["Inbox", "Sent"], ["home", "search"], selected=0)
    window.advance(16)
    assert drawer.node.get("layout_width") == 360.0 and drawer.node.get("fill") == BASE["surface_container_low"]
    item = drawer.part("item0")
    assert (item.get("layout_width"), item.get("layout_height"), item.get("corner_radius")) == (336.0, 56.0, 28.0)
    assert item.get("fill") == BASE["secondary_container"] and drawer.part("item1").get("fill") == (0, 0, 0, 0)
    window.simulate("click", node=drawer.part("item1"))
    window.advance(16)
    assert drawer.selected.get() == 1 and drawer.part("item1.label").get("fill") == BASE["on_secondary_container"]


def test_a_modal_drawer_is_rounded_on_its_end_side_through_a_theme_change():
    window = _window()
    drawer = navigation_drawer(window, ["Inbox"], ["home"], modal=True)
    assert tuple(drawer.node.get("corner_radius")) == (0.0, 16.0, 16.0, 0.0)
    drawer.set_theme(Theme.resolve(theme_seed=SEED, dark=True))
    assert tuple(drawer.node.get("corner_radius")) == (0.0, 16.0, 16.0, 0.0)


def test_toolbars():
    windows = [_window() for _ in range(3)]  # side by side they'd overflow one window and shrink
    docked, floating = toolbar(windows[0]), toolbar(windows[1], variant="floating", vibrant=True)
    upright = toolbar(windows[2], variant="floating", orientation="vertical")
    window = windows[0]
    for w in windows:
        w.advance(16)
    assert (docked.node.get("layout_height"), docked.node.get("fill")) == (64.0, BASE["surface_container"])
    assert floating.node.get("corner_radius") == 32.0 and floating.node.get("fill") == BASE["primary_container"]
    assert (upright.node.get("layout_width"), upright.node.get("flex_direction")) == (64.0, "vertical")
    with pytest.raises(ValueError, match="unknown toolbar variant"):
        toolbar(window, variant="sticky")


def test_the_top_app_bar_is_md3s_small_one():
    window = _window()
    opened = []
    bar = top_app_bar(window, "Inbox", leading_icon="menu", trailing_icons=["search", "settings"])
    bar.on_click(lambda: opened.append("menu"), part="leading")
    window.advance(16)
    assert (bar.node.get("layout_height"), bar.node.get("fill")) == (64.0, BASE["surface"])
    assert bar.part("title").get("font_size") == 22.0  # title_large
    lead = bar.part("leading")
    assert (lead.get("layout_width"), lead.get("role"), lead.get("focusable")) == (48.0, "button", True)
    assert bar.part("leading.icon").get("fill") == BASE["on_surface"]
    assert bar.part("trailing1.icon").get("fill") == BASE["on_surface_variant"]
    assert bar.interaction("trailing0") is not None
    trailing = bar.part("trailing1")  # a button even before anything listens to it
    assert (trailing.get("role"), trailing.get("focusable"), trailing.get("label")) == ("button", True, "settings")
    window.simulate("click", node=lead)
    assert opened == ["menu"]


def test_the_status_bar_announces_its_text():
    window = _window()
    s = status_bar(window, "Ready")
    window.advance(16)
    assert s.node.get("layout_height") == 24.0 and s.node.get("live") == "polite"
    assert s.part("text").get("text") == "Ready" and s.part("text").get("fill") == BASE["on_surface_variant"]
