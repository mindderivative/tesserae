"""M54 (#1): an open overlay follows the window's size. A modal
overlay's scrim covers the whole window even after a resize, and an edge
sheet and a snackbar stay at their edge. Overlays listen through one
shared dispatcher per window (`listeners.listen_window`), while open.
"""

import tre

from tesserae import listeners
from tesserae.listeners import listen_window
from tesserae.overlays import Dialog, NavigationDrawer, SideSheet, Snackbar


def _window():
    window = tre.Window(width=800, height=600)
    window.root.set(padding_top=0, padding_right=0, padding_bottom=0, padding_left=0, gap=0,
                    align_items="flex_start")
    window.advance(16)
    return window


def _resize(window, width, height):
    """What a live OS resize does: the size, then the event."""
    window.resize(width, height)
    window.simulate("resize", width=width, height=height)
    window.advance(16)


def _size(node):
    return node.get("layout_width"), node.get("layout_height")


def test_a_dialogs_scrim_covers_the_window_after_it_grows_or_shrinks():
    window = _window()
    d = Dialog(window, "Discard draft?", "It won't be saved.", actions=[("Cancel", None)])
    d.open()
    window.advance(16)
    assert _size(d.node) == (800.0, 600.0)
    _resize(window, 1000, 700)
    assert _size(d.node) == (1000.0, 700.0)
    panel = d.widget.part("panel")
    assert abs(panel.get("layout_x") + panel.get("layout_width") / 2 - 500.0) < 1  # still centred
    _resize(window, 500, 400)
    assert _size(d.node) == (500.0, 400.0)


def test_edge_sheets_keep_their_scrim_and_edge():
    window = _window()
    sheet = SideSheet(window, width=300, label="Filters")
    drawer = NavigationDrawer(window, ["Inbox"], ["home"])
    sheet.open()
    drawer.open()  # two open at once share the window's one dispatcher
    window.advance(400)
    _resize(window, 1000, 700)
    window.advance(400)
    for overlay in (sheet, drawer):
        assert _size(overlay.node) == (1000.0, 700.0) and overlay.panel.get("layout_height") == 700.0
    assert sheet.panel.get("layout_x") + sheet.panel.get("layout_width") == 1000.0  # at the end edge
    assert drawer.panel.get("layout_x") == 0.0  # at the start edge


def test_the_resize_event_alone_refits_it():
    """What a live OS resize delivers: the event (`tre` has already laid
    the root out at the new size when it arrives)."""
    window = _window()
    d = Dialog(window, "Discard draft?", "It won't be saved.", actions=[("Cancel", None)])
    d.open()
    window.simulate("resize", width=1200, height=900)  # the event alone
    assert (d.node.get("width"), d.node.get("height")) == (1200.0, 900.0)


def test_a_snackbar_stays_near_the_bottom():
    window = _window()
    s = Snackbar(window, "Saved", duration=None)
    s.open()
    _resize(window, 800, 900)
    assert s.node.get("y") == 900 - 72.0


def test_a_closed_overlay_stops_listening():
    window = _window()
    d = Dialog(window, "Discard draft?", "It won't be saved.", actions=[("Cancel", None)])
    d.open()
    assert id(window) in listeners._WINDOWS
    d.close()
    assert id(window) not in listeners._WINDOWS  # nothing left listening, the window let go
    _resize(window, 1000, 700)
    assert _size(d.node) == (800.0, 600.0)  # untouched while closed
    d.open()  # and it fits the window as it is now when it opens again
    window.advance(16)
    assert _size(d.node) == (1000.0, 700.0)


def test_listen_window_shares_one_dispatcher_per_window():
    a, b = _window(), _window()
    heard = []
    undo_1 = listen_window(a, "resize", lambda e: heard.append(("a1", e.width)))
    undo_2 = listen_window(a, "resize", lambda e: heard.append(("a2", e.width)))
    undo_3 = listen_window(b, "resize", lambda e: heard.append(("b", e.width)))
    a.simulate("resize", width=10, height=10)
    b.simulate("resize", width=20, height=20)
    assert heard == [("a1", 10), ("a2", 10), ("b", 20)]
    undo_1()
    a.simulate("resize", width=11, height=11)
    assert heard[-1] == ("a2", 11) and len(heard) == 4
    undo_2()
    undo_3()
    assert id(a) not in listeners._WINDOWS and id(b) not in listeners._WINDOWS  # both let go
