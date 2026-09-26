"""M40 Phase 6 and M41 Phase 6: the gate for tre's MD3 widgets. `tre`
0.3.5 (its M99) removes its controls (checkbox, radio button, switch,
slider, spin box, progress, loading indicator, time picker dial, with
their legacy state methods), its composed widgets and its overlays'
`open_*`/`close_*`. Tesserae draws its own: `tesserae.controls` (M40),
`tesserae.widgets` and `tesserae.overlays` (M41). This keeps any use of
them from creeping back into `src/tesserae`: it reads the code, not the
docstrings, so a mention in prose is fine.
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
REMOVED = REMOVED | REMOVED_M41
SRC = Path(__file__).resolve().parent.parent / "src" / "tesserae"


def _uses():
    for path in sorted(SRC.rglob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(), filename=str(path))):
            if isinstance(node, ast.Attribute) and node.attr in REMOVED:
                yield f"{path.relative_to(SRC)}:{node.lineno}: .{node.attr}"


def test_src_uses_none_of_tres_removed_widgets():
    assert list(_uses()) == []


def test_the_check_would_see_one():
    tree = ast.parse("window.add_checkbox((0, 0, 0, 255), 18, 18)\nnode.get_checked()")
    found = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)} & REMOVED
    assert found == {"add_checkbox", "get_checked"}
