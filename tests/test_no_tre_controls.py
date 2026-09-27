"""M40 Phase 6, M41 Phase 6 and M42 Phase 8: the gate for tre's MD3 widgets. `tre`
0.3.5 (its M99) removes its controls (checkbox, radio button, switch,
slider, spin box, progress, loading indicator, time picker dial, with
their legacy state methods), its composed widgets and its overlays'
`open_*`/`close_*`. Tesserae draws its own: `tesserae.controls` (M40),
`tesserae.widgets` and `tesserae.overlays` (M41), and M42's search, date
and time, media, node graph and new widgets, with `App` off the window's
theme. This keeps any use of them from creeping back into `src/tesserae`:
it reads the code, not the docstrings, so a mention in prose is fine.
The names are `tre`'s own removal list (`python/tre/_removed.py`, 0.3.5).
"""

import ast
from pathlib import Path

REMOVED = frozenset({
    "add_checkbox", "add_radio_button", "add_switch", "add_slider", "add_spin_box", "add_circular_progress",
    "add_linear_progress", "add_loading_indicator", "add_time_picker_dial",
    "get_checked", "set_checked", "get_selected", "set_selected", "set_on_change",
    "get_time_picker_dial_time", "set_time_picker_dial_time", "get_time_picker_dial_mode",
    "set_time_picker_dial_mode", "enable_interaction",
})
#: M41: the composed widgets and the overlays' open/close pairs.
REMOVED_M41 = frozenset({
    "add_button", "add_icon_button", "add_fab", "add_extended_fab", "add_split_button", "add_button_group",
    "add_card", "add_chip", "add_badge", "add_divider", "add_list", "add_list_item", "add_accordion_header",
    "add_tree_node", "add_link", "add_icon", "add_tabs", "add_navigation_rail", "add_navigation_drawer",
    "add_toolbar", "add_top_app_bar", "add_status_bar", "add_dialog", "add_menu_item", "build_menu",
    "add_snackbar", "add_tooltip", "add_side_sheet", "open_dialog", "close_dialog", "open_menu", "close_menu",
    "open_snackbar", "close_snackbar", "open_side_sheet", "close_side_sheet", "open_navigation_drawer",
    "close_navigation_drawer", "set_active_tab",
})
#: M42: search, date and time, media, the node graph, the widgets Tesserae
#: never wrapped, their state methods, and the shell.
REMOVED_M42 = frozenset({
    "add_search_bar", "add_search_view", "add_text_field", "add_date_picker_day", "add_period_selector",
    "add_time_input_field", "add_image", "add_image_from_bytes", "add_video", "push_frame", "add_node_graph",
    "add_graph_node", "add_segmented_button", "add_pagination", "add_popover", "add_carousel", "add_splitter",
    "set_carousel_index", "get_carousel_index", "get_carousel_position", "set_carousel_scroll",
    "get_carousel_scroll", "build_shell",
})
REMOVED = REMOVED | REMOVED_M41 | REMOVED_M42
#: M42 Phase 7: the window's theme. Tesserae's own `View`, `Widget` and
#: controls have `set_theme`/`theme` too, so these count only on a window.
WINDOW_ONLY = frozenset({"set_theme", "theme"})
SRC = Path(__file__).resolve().parent.parent / "src" / "tesserae"


def _on_a_window(node: ast.Attribute) -> bool:
    receiver = node.value
    name = receiver.id if isinstance(receiver, ast.Name) else getattr(receiver, "attr", "")
    return "window" in name.lower()


def _found(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and (
                node.attr in REMOVED or node.attr in WINDOW_ONLY and _on_a_window(node)):
            yield node


def _uses():
    for path in sorted(SRC.rglob("*.py")):
        for node in _found(ast.parse(path.read_text(), filename=str(path))):
            yield f"{path.relative_to(SRC)}:{node.lineno}: .{node.attr}"


def test_src_uses_none_of_tres_removed_widgets():
    assert list(_uses()) == []


def test_the_check_would_see_one():
    tree = ast.parse("window.add_checkbox((0, 0, 0, 255), 18, 18)\nnode.get_checked()")
    found = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)} & REMOVED
    assert found == {"add_checkbox", "get_checked"}


def test_the_check_sees_m42s_names_and_a_themed_window_but_not_tesseraes_own_set_theme():
    tree = ast.parse("window.add_node_graph(1, 2)\nself._window.set_theme(seed)\nwindow.theme.role('primary')\n"
                     "view.set_theme(theme)\nwidget.theme.role('primary')")
    assert [n.attr for n in _found(tree)] == ["add_node_graph", "set_theme", "theme"]
