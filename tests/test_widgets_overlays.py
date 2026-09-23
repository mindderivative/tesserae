"""Real coverage for `tesserae.widgets`'s Overlays category -- `dialog`/
`snackbar`/`side_sheet`/`menu`/`menu_item`/`tooltip`. Same thin-delegate
parity strategy as the other widget test modules.
"""

import pytest
from tre import Window

from tesserae.widgets import dialog, menu, menu_item, side_sheet, snackbar, tooltip


def test_dialog_matches_native_add_dialog():
    window = Window(width=400, height=300)
    a = dialog(window, "Delete?", "This can't be undone.", 360, 180)
    b = window.add_dialog("Delete?", "This can't be undone.", 360, 180)
    assert a.get("corner_radius") == b.get("corner_radius")


def test_snackbar_matches_native_add_snackbar_with_action_and_close():
    window = Window(width=400, height=300)
    a_container, a_action, a_close = snackbar(window, "Saved", 300, action_label="Undo", closable=True)
    b_container, b_action, b_close = window.add_snackbar("Saved", 300, action_label="Undo", closable=True)
    assert a_container.get("corner_radius") == b_container.get("corner_radius")
    assert a_action is not None and b_action is not None
    assert a_close is not None and b_close is not None


def test_snackbar_without_action_or_close_matches_native_none_shape():
    window = Window(width=400, height=300)
    a_container, a_action, a_close = snackbar(window, "Saved", 300)
    assert a_action is None
    assert a_close is None


def test_side_sheet_matches_native_add_side_sheet():
    window = Window(width=400, height=300)
    a = side_sheet(window, width=320)
    b = window.add_side_sheet(width=320)
    assert a.get("corner_radius") == b.get("corner_radius")


def test_menu_matches_native_build_menu():
    window = Window(width=400, height=300)
    a_item = menu_item(window, "Open")
    a = menu(window, [a_item])
    b_item = window.add_menu_item("Open")
    b = window.build_menu([b_item])
    assert a.get("corner_radius") == b.get("corner_radius")


def test_menu_rejects_empty_items_matching_native():
    window = Window(width=400, height=300)
    with pytest.raises(ValueError, match="at least 1 item"):
        menu(window, [])


def test_tooltip_matches_native_add_tooltip():
    window = Window(width=400, height=300)
    a = tooltip(window, "Hint", 100)
    b = window.add_tooltip("Hint", 100)
    assert a.get("corner_radius") == b.get("corner_radius")
