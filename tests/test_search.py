"""M42 Phase 1: MD3's search bar (`tesserae.widgets.search_bar`, built
from its fragment) and docked search view (`tesserae.overlays.SearchView`).
"""

import pytest
import tre

from tesserae import Theme, tokens
from tesserae.overlays import SearchView
from tesserae.widgets import search_bar, search_view

BASE = tokens.baseline_scheme()
SEED = (0x67, 0x50, 0xA4, 0xFF)


def _window():
    window = tre.Window(width=600, height=500)
    window.root.set(padding_top=0, padding_right=0, padding_bottom=0, padding_left=0, gap=0,
                    align_items="flex_start", flex_direction="vertical")
    return window


def _bar_and_view(results=None):
    window = _window()
    bar = search_bar(window, "Search mail", 360, trailing_icons=["settings"])
    view = search_view(window, 360, 300, bar=bar, results=results)
    window.advance(16)
    return window, bar, view


def test_the_search_bar_is_md3s():
    window, bar, _ = _bar_and_view()
    assert (bar.node.get("layout_height"), bar.node.get("corner_radius")) == (56.0, 28.0)
    assert bar.node.get("fill") == BASE["surface_container_high"]
    assert bar.part("leading.icon").get("fill") == BASE["on_surface"]
    trailing = bar.part("trailing0")
    assert (trailing.get("role"), trailing.get("label"), trailing.get("layout_width")) == ("button", "settings", 48.0)
    assert bar.part("trailing0.icon").get("fill") == BASE["on_surface_variant"]


def test_the_placeholder_is_hint_text_not_the_fields_text():
    """`tre`'s search bar (and the fragment) filled the field with it."""
    window, bar, _ = _bar_and_view()
    field = bar.part("field")
    assert field.get("text") == "" and field.get("placeholder") == "Search mail"
    assert field.get("placeholder_fill") == BASE["on_surface_variant"] and field.get("fill") == BASE["on_surface"]
    assert (field.get("role"), field.get("label")) == ("textbox", "Search mail")


def test_typing_updates_the_query():
    window, bar, _ = _bar_and_view()
    heard = []
    bar.on_query(heard.append)
    bar.part("field").focus()
    window.simulate("input", text="ali")
    assert bar.query.get() == "ali" and heard == ["ali"]


def test_the_view_opens_below_the_bar_on_focus_and_is_md3s():
    window, bar, view = _bar_and_view([("Alice", None), ("Bob", None)])
    assert not view.is_open
    bar.part("field").focus()
    window.advance(16)
    assert view.is_open and view.node.get("layout_y") == 56.0
    assert view.node.get("fill") == BASE["surface_container_high"] and view.node.get("corner_radius") == 28.0
    assert view.node.get("role") == "menu"
    row = view.rows[0]
    assert (row.get("layout_height"), row.get("role"), row.get("label")) == (56.0, "menuitem", "Alice")
    assert view.widget.part("row0.label").get("font_size") == 16.0  # body_large
    assert [r.parent() is not None for r in view.rows[:3]] == [True, True, False]


def test_no_results_no_view():
    window, bar, view = _bar_and_view()
    bar.part("field").focus()
    window.advance(16)
    assert not view.is_open
    view.set_results([("Alice", None)])
    window.simulate("input", text="a")
    assert view.is_open
    view.set_results([("Alice", None), ("Bob", None)])
    view.set_results([("Carol", None)])  # fewer: the rest go
    assert [r.parent() is not None for r in view.rows[:2]] == [True, False]
    view.set_results([])
    assert not view.is_open


def test_the_arrows_move_between_the_field_and_the_rows_and_enter_chooses():
    chosen = []
    window, bar, view = _bar_and_view([("Alice", lambda: chosen.append("alice")),
                                       ("Bob", lambda: chosen.append("bob"))])
    field = bar.part("field")
    field.focus()
    window.simulate("key_down", key="arrow_down")
    assert view.rows[0].get("focused")
    window.simulate("key_down", key="arrow_down")
    assert view.rows[1].get("focused")
    window.simulate("key_down", key="arrow_down")
    assert view.rows[0].get("focused")  # wraps
    window.simulate("key_down", key="arrow_up")
    assert field.get("focused")  # up from the first row: back to the field
    window.simulate("key_down", key="arrow_down")
    window.simulate("key_down", key="arrow_down")
    window.simulate("key_down", key="enter")
    window.advance(16)
    assert chosen == ["bob"] and not view.is_open


def test_a_click_chooses_and_escape_or_an_outside_press_closes():
    chosen = []
    window, bar, view = _bar_and_view([("Alice", lambda: chosen.append("alice"))])
    bar.part("field").focus()
    window.advance(16)
    window.simulate("click", node=view.rows[0])
    assert chosen == ["alice"] and not view.is_open
    window.simulate("input", text="x")
    window.simulate("key_down", key="escape")
    window.advance(16)
    assert not view.is_open
    window.simulate("input", text="y")
    window.simulate("pointer_down", x=590, y=490)
    window.simulate("pointer_up", x=590, y=490)
    window.advance(16)
    assert not view.is_open


def test_a_view_without_a_bar_opens_where_its_told():
    window = _window()
    anchor = window.create("box", width=100, height=30)
    window.root.add_child(anchor)
    view = SearchView(window, results=[("One", None)])
    view.open(anchor)
    window.advance(16)
    assert view.is_open and view.node.get("layout_y") == 30.0
    with pytest.raises(ValueError, match="through its bar"):
        view.on_query(print)


def test_search_follows_the_theme():
    window = _window()
    light, dark = Theme.resolve(theme_seed=SEED), Theme.resolve(theme_seed=SEED, dark=True)
    bar = search_bar(window, "Find", 300, theme=light)
    bar.set_theme(dark)
    assert bar.node.get("fill") == dark.role("surface_container_high")
    assert bar.part("field").get("placeholder_fill") == dark.role("on_surface_variant")
