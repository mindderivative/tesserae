"""M45 Phase 2: `tesserae.docking.Dock`, docking's presentation on `tre`
0.3.5's bare mechanism -- MD3 secondary tabs per zone, the tab as the drag
handle, a highlight over the target zone, and a "Move to" menu for the
keyboard (M45 Q2). Driven headlessly with `simulate`, as `tre`'s docking
guide does.
"""

import pytest
import tre

from tesserae import Theme, tokens
from tesserae.docking import DRAG_THRESHOLD, TAB_HEIGHT, Dock

BASE = tokens.baseline_scheme()


def _dock(theme=None):
    window = tre.Window(width=900, height=500)
    window.root.set(padding_top=0, padding_right=0, padding_bottom=0, padding_left=0, gap=0, align_items="stretch")
    dock = Dock(window, theme=theme)
    for side, size in (("left", 220), ("center", 400), ("right", 220)):
        window.root.add_child(dock.add_zone(side, size))
    panels = {name: window.create("box", width=10, height=10) for name in ("Files", "Search", "Properties")}
    dock.add_panel("left", panels["Files"], "Files")
    dock.add_panel("left", panels["Search"], "Search")
    dock.add_panel("right", panels["Properties"], "Properties")
    window.advance(16)
    return window, dock, panels


def _menu_labels(menu):
    return [menu.widget.part(f"item{i}.label").get("text") for i in range(len(menu.items))]


def _tabs(dock, side):
    return [t.node for t in dock._zones[side].tabs]


def _centre(node):
    return node.get("layout_x") + node.get("layout_width") / 2, node.get("layout_y") + node.get("layout_height") / 2


def _drag(window, tab, target, *, release=True):
    x, y = _centre(tab)
    tx, ty = _centre(target)
    window.simulate("pointer_down", x=x, y=y)
    window.simulate("pointer_move", x=x + DRAG_THRESHOLD + 2, y=y)
    window.simulate("pointer_move", x=tx, y=ty)
    if release:
        window.simulate("pointer_up", x=tx, y=ty)
        window.advance(16)


def test_zones_are_tab_strips_over_the_area_tre_docks_into():
    window, dock, _ = _dock()
    left, center = dock._zones["left"], dock._zones["center"]
    assert left.node.get("layout_width") == 220.0 and center.node.get("layout_width") == 900 - 440.0
    assert left.strip.get("layout_height") == TAB_HEIGHT and left.strip.get("role") == "tablist"
    assert left.strip.get("label") == "Left panels"
    assert left.node.get("fill") == BASE["surface_container_low"] and center.node.get("fill") == BASE["surface"]
    assert left.divider.get("fill") == BASE["surface_variant"] and left.divider.get("layout_height") == 1.0


def test_each_panel_gets_a_tab_and_the_last_docked_is_shown():
    window, dock, panels = _dock()
    files, search = _tabs(dock, "left")
    assert (files.get("label"), files.get("role"), search.get("label")) == ("Files", "tab", "Search")
    style = tokens.type_style("title_small")
    text = window.measure_text("Files", font_family=style.font_family, font_size=style.font_size,
                               font_weight=style.font_weight, line_height=style.line_height)[0]
    assert files.get("layout_width") == pytest.approx(text + 32, abs=1)  # 16 px either side
    assert dock.shown("left") == panels["Search"] and dock.panels("left") == [panels["Files"], panels["Search"]]
    assert (files.get("selected"), search.get("selected")) == (False, True)
    assert (files.get("focusable"), search.get("focusable")) == (False, True)  # one Tab stop, the shown tab
    shown, other = dock._zones["left"].tabs[1], dock._zones["left"].tabs[0]
    assert shown.indicator.get("visible") and not other.indicator.get("visible")
    assert shown.indicator.get("fill") == BASE["primary"] and shown.indicator.get("layout_height") == 2.0
    assert shown.label.get("fill") == BASE["on_surface"] and other.label.get("fill") == BASE["on_surface_variant"]
    assert (panels["Files"].get("role"), panels["Files"].get("label")) == ("tabpanel", "Files")


def test_a_click_or_enter_shows_a_panel_and_the_arrows_move_along_the_strip():
    window, dock, panels = _dock()
    files, search = _tabs(dock, "left")
    window.simulate("click", node=files)
    assert dock.shown("left") == panels["Files"] and files.get("selected") and files.get("focusable")
    files.focus()
    window.simulate("key_down", key="arrow_right")
    assert dock.shown("left") == panels["Search"] and search.get("focused")
    window.simulate("key_down", key="arrow_right")  # wraps
    assert dock.shown("left") == panels["Files"] and files.get("focused")


def test_dragging_a_tab_highlights_the_zone_under_the_pointer_and_drops_the_panel_there():
    window, dock, panels = _dock()
    moves = []
    dock.on_move(lambda node, side: moves.append((node, side)))
    tab = dock._zones["left"].tabs[0]
    right = dock._zones["right"]
    _drag(window, tab.node, right.body, release=False)
    assert dock.highlight.parent() == right.body and tab.interaction.dragged
    assert dock.highlight.get("fill") == (*BASE["primary"][:3], 0x1F) and dock.highlight.get("stroke_width") == 2.0
    window.simulate("pointer_up", x=_centre(right.body)[0], y=_centre(right.body)[1])
    window.advance(16)
    assert dock.side_of(panels["Files"]) == "right" and moves == [(panels["Files"], "right")]
    assert [t.get("label") for t in _tabs(dock, "right")] == ["Properties", "Files"]
    assert [t.get("label") for t in _tabs(dock, "left")] == ["Search"]
    assert dock.shown("right") == panels["Files"] and _tabs(dock, "right")[1].get("focused")
    assert dock.highlight.parent() is None


def test_a_press_that_barely_moves_is_a_click_not_a_drag():
    window, dock, panels = _dock()
    files = _tabs(dock, "left")[0]
    x, y = _centre(files)
    window.simulate("pointer_down", x=x, y=y)
    window.simulate("pointer_move", x=x + DRAG_THRESHOLD - 1, y=y)
    assert not dock._zones["left"].tabs[0].interaction.dragged  # no drag started
    window.simulate("pointer_up", x=x + DRAG_THRESHOLD - 1, y=y)
    window.advance(16)
    assert dock.side_of(panels["Files"]) == "left" and dock.shown("left") == panels["Files"]  # clicked: shown
    assert not dock._zones["left"].tabs[0].interaction.dragged


def test_a_drop_over_no_zone_leaves_the_panel_where_it_was():
    window, dock, panels = _dock()
    tab = _tabs(dock, "left")[0]
    strip = dock._zones["right"].strip  # a tab strip isn't a dock zone
    _drag(window, tab, strip)
    assert dock.side_of(panels["Files"]) == "left" and dock.highlight.parent() is None
    assert not dock._zones["left"].tabs[0].interaction.dragged  # the same tab, its dragged state cleared


def test_move_and_the_keyboard_menu_move_a_panel_without_a_pointer():
    window, dock, panels = _dock()
    files = _tabs(dock, "left")[0]
    files.focus()
    window.simulate("key_down", key="context_menu")
    menu = dock._menu
    assert menu.is_open and _menu_labels(menu) == ["Move to center", "Move to right"]
    window.simulate("click", node=menu.items[1])
    window.advance(16)
    assert not menu.is_open and dock.side_of(panels["Files"]) == "right" and dock.shown("right") == panels["Files"]
    moved = _tabs(dock, "right")[1]
    moved.focus()
    window.simulate("key_down", key="f10", shift=True)
    assert _menu_labels(dock._menu) == ["Move to left", "Move to center"]
    dock.move(panels["Files"], "center")
    window.advance(16)
    assert dock.side_of(panels["Files"]) == "center" and dock.panels("center") == [panels["Files"]]


def test_move_uses_tres_dock_panel_not_a_simulated_drag():
    """`tre` 0.3.5.1 fixed `dock_panel` for a docked panel (`tre` issue
    #14), so `move` sends no pointer events and hears no `dock_drop`."""
    window, dock, panels = _dock()
    pointer = []
    target = dock._zones["right"].body
    target.on("pointer_up", lambda e: pointer.append("up"))
    moves = []
    dock.on_move(lambda node, side: moves.append(side))
    dock.move(panels["Files"], "right")
    assert pointer == [] and moves == ["right"]
    assert dock.panels("left") == [panels["Search"]] and dock.shown("right") == panels["Files"]
    dock.show(panels["Search"])  # the old zone's list is right: index 0 is Search
    assert dock.shown("left") == panels["Search"]


def test_a_right_click_opens_the_menu_at_the_pointer():
    window, dock, _ = _dock()
    tab = _tabs(dock, "left")[0]
    x, y = _centre(tab)
    window.simulate("secondary_click", x=x, y=y)
    window.advance(16)
    assert dock._menu.is_open and dock._menu.node.get("layout_x") == pytest.approx(x, abs=1)


def test_show_uses_the_right_index_after_panels_move():
    window, dock, panels = _dock()
    dock.move(panels["Search"], "right")
    window.advance(16)
    dock.show(panels["Properties"])
    assert dock.shown("right") == panels["Properties"]
    dock.show(panels["Search"])
    assert dock.shown("right") == panels["Search"]
    assert [t.get("selected") for t in _tabs(dock, "right")] == [False, True]


def test_a_dock_takes_a_theme_and_re_colours():
    theme = Theme.resolve(theme_seed=(0x00, 0x66, 0x88, 0xFF))
    window, dock, _ = _dock()
    dock.set_theme(theme)
    left = dock._zones["left"]
    assert left.node.get("fill") == theme.role("surface_container_low")
    assert left.tabs[1].indicator.get("fill") == theme.role("primary")
    assert left.tabs[0].label.get("fill") == theme.role("on_surface_variant")
    assert left.tabs[0].interaction.layer.get("fill") == theme.role("on_surface")
    assert dock.highlight.get("stroke_color") == theme.role("primary")


@pytest.mark.parametrize("call, message", [
    (lambda d, w: d.add_zone("middle", 100), "a dock zone's side is one of"),
    (lambda d, w: d.add_zone("left", 100), "already has a left zone"),
    (lambda d, w: d.add_panel("top", w.create("box"), "X"), "has no top zone"),
    (lambda d, w: d.add_panel("left", d.panels("left")[0], "Again"), "already docked"),
    (lambda d, w: d.show(w.create("box")), "isn't docked here"),
])
def test_a_dock_rejects_what_it_cant_do(call, message):
    window, dock, _ = _dock()
    with pytest.raises(ValueError, match=message):
        call(dock, window)


# -- M53: remove_panel, on tre 0.3.5.2's undock_panel (#3) --------------------


def test_remove_panel_undocks_it_and_shows_the_next_or_previous():
    window, dock, panels = _dock()
    dock.add_panel("left", window.create("box", width=10, height=10), "Outline")
    dock.show(panels["Search"])
    assert dock.remove_panel(panels["Search"]) == panels["Search"]
    assert dock.titles("left") == ["Files", "Outline"] and dock.side_of(panels["Search"]) is None
    assert panels["Search"].parent() is None
    assert dock.shown("left") == dock.panel("Outline")  # the next one
    assert [t.label.get("text") for t in dock._zones["left"].tabs] == ["Files", "Outline"]
    dock.remove_panel(dock.panel("Outline"))
    assert dock.shown("left") == panels["Files"]  # the previous one, with no next
    dock.show(panels["Files"])  # the indexes still match tre's list
    assert dock.shown("left") == panels["Files"]
    dock.add_panel("left", panels["Search"], "Search")  # it can be docked again
    assert dock.titles("left") == ["Files", "Search"] and dock.shown("left") == panels["Search"]


def test_removing_a_panel_that_isnt_docked_raises():
    window, dock, panels = _dock()
    dock.remove_panel(panels["Files"])
    with pytest.raises(ValueError, match="isn't docked"):
        dock.remove_panel(panels["Files"])


def test_removing_the_panel_being_dragged_ends_the_drag():
    window, dock, panels = _dock()
    tab = _tabs(dock, "left")[0]
    _drag(window, tab, dock._zones["right"].body, release=False)
    assert dock._dragging is not None and dock.highlight.parent() is not None
    dock.remove_panel(panels["Files"])
    assert dock._dragging is None and dock._press is None and dock.highlight.parent() is None
    assert dock.titles("left") == ["Search"]
