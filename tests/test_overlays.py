"""M41 Phase 5: `tesserae.overlays`, MD3's overlays on `tre` 0.3.4's
layers (`show_layer`/`hide_layer`), since `tre` 0.3.5 removes its
`open_*`/`close_*`. Driven headlessly with `simulate`/`advance`.
"""

import math

import pytest
import tre

from tesserae import Theme, tokens
from tesserae.overlays import Dialog, Menu, NavigationDrawer, SideSheet, Snackbar, Tooltip
from tesserae.widgets import dialog, menu, menu_item, side_sheet, snackbar, tooltip

BASE = tokens.baseline_scheme()
SEED = (0x67, 0x50, 0xA4, 0xFF)


def _window():
    window = tre.Window(width=800, height=600)
    window.root.set(padding_top=0, padding_right=0, padding_bottom=0, padding_left=0, gap=0,
                    align_items="flex_start")
    anchor = window.create("box", width=100, height=40, focusable=True, role="button")
    window.root.add_child(anchor)
    window.advance(16)
    return window, anchor


def _frames(window, ms):
    for _ in range(math.ceil(ms / 16)):
        window.advance(16)


def _outside(window):
    window.simulate("pointer_down", x=700, y=500)
    window.simulate("pointer_up", x=700, y=500)
    window.advance(16)


# -- Dialog ----------------------------------------------------------------------

def test_a_dialog_is_md3s_and_modal():
    window, anchor = _window()
    anchor.focus()
    d = Dialog(window, "Discard draft?", "It won't be saved.", actions=[("Cancel", None), ("Discard", None)])
    d.open()
    window.advance(16)
    panel = d.widget.part("panel")
    assert d.is_open and d.node.parent() is None  # a layer, not in the tree
    assert (d.node.get("layout_width"), d.node.get("layout_height")) == (800.0, 600.0)  # the scrim fills the window
    assert d.node.get("fill") == (0, 0, 0, 0x52)
    assert (panel.get("role"), panel.get("label")) == ("dialog", "Discard draft?")
    assert panel.get("fill") == BASE["surface_container_high"] and panel.get("corner_radius") == 28.0
    assert d.widget.part("headline").get("font_size") == 24.0  # headline_small
    action = d.widget.part("panel.action1")
    assert action.get("role") == "button" and d.widget.part("panel.action1.label").get("text") == "Discard"
    window.simulate("key_down", key="tab")
    window.advance(16)
    assert not anchor.get("focused")  # focus stays inside a modal layer


def test_an_action_runs_and_closes_the_dialog_and_escape_closes_it():
    window, anchor = _window()
    log = []
    d = Dialog(window, "Delete?", "Gone for good.", actions=[("Delete", lambda: log.append("delete"))])
    d.on_close(lambda: log.append("closed"))
    d.open()
    window.simulate("click", node=d.widget.part("panel.action0"))
    assert log == ["delete", "closed"] and not d.is_open
    d.open()
    window.simulate("key_down", key="escape")
    window.advance(16)
    assert not d.is_open and log[-1] == "closed"


def test_pressing_a_dialogs_scrim_doesnt_close_it():
    window, _ = _window()
    d = Dialog(window, "Hi", "There")
    d.open()
    _outside(window)  # lands on the scrim, inside the layer
    assert d.is_open


def test_focus_goes_back_when_a_dialog_closes():
    window, anchor = _window()
    anchor.focus()
    d = Dialog(window, "Hi", "There", actions=[("OK", None)])
    d.open()
    window.advance(16)
    d.close()
    window.advance(16)
    assert anchor.get("focused")


# -- Menu ------------------------------------------------------------------------

def test_a_menu_opens_below_its_anchor_with_focus_on_the_first_item():
    window, anchor = _window()
    m = Menu(window, [("Copy", None), ("Paste", None)])
    m.open(anchor)
    window.advance(16)
    assert m.node.get("layout_y") == 40.0 and m.node.get("layout_x") == 0.0
    assert (m.node.get("role"), m.items[0].get("role")) == ("menu", "menuitem")
    assert m.node.get("fill") == BASE["surface_container"] and m.node.get("corner_radius") == 4.0
    assert m.items[0].get("layout_height") == 48.0 and m.items[0].get("focused")


def test_the_arrows_and_enter_choose_and_close():
    window, anchor = _window()
    chosen = []
    m = Menu(window, [("Copy", lambda: chosen.append("copy")), ("Paste", lambda: chosen.append("paste"))])
    m.open(anchor)
    window.simulate("key_down", key="arrow_down")
    assert m.items[1].get("focused")
    window.simulate("key_down", key="arrow_down")
    assert m.items[0].get("focused")  # wraps
    window.simulate("key_down", key="arrow_up")
    window.simulate("key_down", key="enter")
    window.advance(16)
    assert chosen == ["paste"] and not m.is_open


def test_an_outside_press_or_escape_closes_a_menu():
    window, anchor = _window()
    m = Menu(window, [("A", None)])
    m.open(anchor)
    _outside(window)
    assert not m.is_open
    m.open(anchor)
    window.simulate("key_down", key="escape")
    window.advance(16)
    assert not m.is_open


def test_a_context_menu_opens_at_the_pointer():
    window, anchor = _window()
    m = Menu(window, [("Rename", None)])
    m.attach_context(anchor)
    window.simulate("secondary_click", x=30, y=12)
    window.advance(16)
    assert m.is_open and (m.node.get("layout_x"), m.node.get("layout_y")) == (30.0, 12.0)


def test_a_menu_of_menu_item_widgets():
    window, anchor = _window()
    chosen = []
    items = [menu_item(window, "Settings", icon="settings", on_click=lambda: chosen.append("settings")),
             menu_item(window, "More", submenu=True)]
    m = menu(window, items)
    m.open(anchor)
    window.advance(16)
    assert items[0].node.parent() is not None and items[0].part("icon") is not None and items[1].part("submenu")
    window.simulate("click", node=items[0].node)
    assert chosen == ["settings"] and not m.is_open
    with pytest.raises(ValueError, match="at least one item"):
        Menu(window, [])


# -- Snackbar ---------------------------------------------------------------------

def test_a_snackbar_sits_at_the_bottom_and_hides_itself_after_4s():
    window, _ = _window()
    s = Snackbar(window, "Saved", action="Undo", closable=True)
    s.open()
    window.advance(16)
    assert (s.node.get("layout_x"), s.node.get("layout_y")) == (24.0, 600 - 72.0)
    assert (s.node.get("role"), s.node.get("live"), s.node.get("fill")) == ("alert", "polite", BASE["inverse_surface"])
    assert s.widget.part("action.label").get("fill") == BASE["inverse_primary"]
    window.simulate("key_down", key="escape")
    _outside(window)
    assert s.is_open  # neither dismisses a snackbar
    _frames(window, 3800)
    assert s.is_open
    _frames(window, 300)
    assert not s.is_open


def test_a_snackbars_action_and_close_button():
    window, _ = _window()
    undone = []
    s = Snackbar(window, "Deleted", action="Undo", on_action=lambda: undone.append(1), closable=True,
                 duration=None)
    s.open()
    window.simulate("click", node=s.widget.part("action"))
    assert undone == [1] and not s.is_open
    s.open()
    close = s.widget.part("close")
    assert close.get("label") == "Close"
    window.simulate("click", node=close)
    assert not s.is_open
    s.open()
    _frames(window, 6000)
    assert s.is_open  # duration=None keeps it


def test_reopening_a_snackbar_restarts_its_timer():
    window, _ = _window()
    s = Snackbar(window, "Saved")
    s.open()
    _frames(window, 3000)
    s.close()
    s.open()
    _frames(window, 3000)
    assert s.is_open  # the first opening's timer doesn't close the second


# -- Tooltip -----------------------------------------------------------------------

def test_a_tooltip_opens_after_500ms_of_hover_and_hides_on_leave():
    window, anchor = _window()
    t = Tooltip(window, "Save")
    t.attach(anchor)
    window.simulate("pointer_move", x=50, y=20)
    _frames(window, 400)
    assert not t.is_open
    _frames(window, 200)
    assert t.is_open and t.node.get("layout_y") == 40.0
    assert t.node.get("fill") == BASE["inverse_surface"] and t.node.get("layout_height") == 24.0
    window.simulate("pointer_move", x=700, y=500)
    window.advance(16)
    assert not t.is_open


def test_a_tooltip_opens_at_once_on_keyboard_focus_and_names_its_anchor():
    window, anchor = _window()
    before = window.create("box", width=10, height=10, focusable=True)
    window.root.insert_child(0, before)
    t = Tooltip(window, "Save")
    t.attach(anchor)
    assert anchor.get("label") == "Save"
    before.focus()
    window.simulate("key_down", key="tab")
    window.advance(16)
    assert t.is_open
    window.simulate("key_down", key="tab")
    window.advance(16)
    assert not t.is_open


def test_a_hover_that_leaves_early_never_opens_the_tooltip():
    window, anchor = _window()
    t = tooltip(window, "Save", anchor=anchor)
    window.simulate("pointer_move", x=50, y=20)
    _frames(window, 200)
    window.simulate("pointer_move", x=700, y=500)
    _frames(window, 600)
    assert not t.is_open


# -- Side sheets and drawers ------------------------------------------------------------

def test_a_modal_side_sheet_slides_in_at_the_end_and_escape_closes_it():
    window, _ = _window()
    sheet = SideSheet(window, label="Filters")
    sheet.open()
    window.advance(16)
    assert 0.0 < sheet.panel.get("translate_x") <= 360.0  # sliding in
    _frames(window, 500)
    assert sheet.panel.get("translate_x") == 0.0 and sheet.panel.get("layout_x") == 800 - 360.0
    assert tuple(sheet.panel.get("corner_radius")) == (16.0, 0.0, 0.0, 16.0)
    assert (sheet.panel.get("role"), sheet.panel.get("label")) == ("dialog", "Filters")
    assert sheet.panel.get("fill") == BASE["surface_container_low"]
    window.simulate("key_down", key="escape")
    window.advance(16)
    assert not sheet.is_open


def test_a_standard_side_sheet_is_in_the_layout():
    window, _ = _window()
    sheet = side_sheet(window, width=300, height=400)
    assert sheet.node.parent() == window.root and sheet.node.get("fill") == BASE["surface"]
    assert isinstance(side_sheet(window, modal=True), SideSheet)


def test_a_modal_navigation_drawer_slides_in_at_the_start_and_closes_on_a_choice():
    window, _ = _window()
    nd = NavigationDrawer(window, ["Inbox", "Sent"], ["home", "search"], selected=0)
    nd.open()
    window.advance(16)
    assert nd.panel.get("translate_x") < 0.0  # sliding in from the start
    _frames(window, 500)
    assert nd.panel.get("layout_x") == 0.0 and nd.drawer.part("item0").get("focused")
    assert tuple(nd.drawer.node.get("corner_radius")) == (0.0, 16.0, 16.0, 0.0)
    window.simulate("key_down", key="arrow_down")
    window.advance(16)
    assert nd.drawer.selected.get() == 1 and not nd.is_open


# -- the factories and theming ------------------------------------------------------------

def test_the_factories_return_overlays():
    window, _ = _window()
    assert isinstance(dialog(window, "Hi", "There", 300, 200), Dialog)
    s = snackbar(window, "Saved", 300, action_label="Undo", closable=True)
    assert isinstance(s, Snackbar) and s.widget.part("action") is not None


def test_overlays_follow_the_theme():
    window, _ = _window()
    light, dark = Theme.resolve(theme_seed=SEED), Theme.resolve(theme_seed=SEED, dark=True)
    d = Dialog(window, "Hi", "There", theme=light)
    assert d.widget.part("panel").get("fill") == light.role("surface_container_high")
    d.set_theme(dark)
    assert d.widget.part("panel").get("fill") == dark.role("surface_container_high")
    sheet = SideSheet(window, theme=light)
    sheet.set_theme(dark)
    assert tuple(sheet.panel.get("corner_radius")) == (16.0, 0.0, 0.0, 16.0)
