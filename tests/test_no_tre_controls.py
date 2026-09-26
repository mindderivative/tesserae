"""M40 Phase 6: the gate for tre's MD3 controls. `tre` 0.3.5 (its M99)
removes its checkbox, radio button, switch, slider, spin box, progress,
loading indicator and time picker dial with their legacy state methods;
since M40 Tesserae draws its own (`tesserae.controls`). This keeps any use
of them from creeping back into `src/tesserae`: it reads the code, not the
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
SRC = Path(__file__).resolve().parent.parent / "src" / "tesserae"


def _uses():
    for path in sorted(SRC.rglob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(), filename=str(path))):
            if isinstance(node, ast.Attribute) and node.attr in REMOVED:
                yield f"{path.relative_to(SRC)}:{node.lineno}: .{node.attr}"


def test_src_uses_none_of_tres_removed_controls():
    assert list(_uses()) == []


def test_the_check_would_see_one():
    tree = ast.parse("window.add_checkbox((0, 0, 0, 255), 18, 18)\nnode.get_checked()")
    found = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)} & REMOVED
    assert found == {"add_checkbox", "get_checked"}
