"""0.5.0 (#106) phase 2: dropping a dragged panel onto a split half -- the half and band under the pointer, the highlight, and a
drop that adds the panel to the half (the middle) or splits it (an edge). Driven headlessly with `simulate`; a real window was
checked for the one thing it decides (the root's `pointer_move`s keep arriving during a drag: tools/spikes/drag_events.py)."""

import pytest
import yaml

from tesserae.docking import DRAG_THRESHOLD, HALF_EDGE
from tesserae.dockhost import HANDLE_SPAN, MIN_SPLIT
from test_dock_view import DOCK, _view


def _centre(node):
    return node.get("layout_x") + node.get("layout_width") / 2, node.get("layout_y") + node.get("layout_height") / 2


def _point(node, where):
    """A point in `node`: its `middle`, or 6 px inside an edge (`left`, `right`, `top`, `bottom`)."""
    x, y, w, h = (node.get(k) for k in ("layout_x", "layout_y", "layout_width", "layout_height"))
    cx, cy = x + w / 2, y + h / 2
    return {"middle": (cx, cy), "left": (x + 6, cy), "right": (x + w - 6, cy), "top": (cx, y + 6), "bottom": (cx, y + h - 6)}[where]


def _tab(host, side, title):
    zone = host.dock._zones[side]
    return zone.tabs[host.dock.titles(side).index(title)].node


def _pick_up(app, tab):
    """Presses `tab` and moves it past the drag threshold: tre's panel drag has begun."""
    x, y = _centre(tab)
    app.window.simulate("pointer_down", x=x, y=y)
    app.window.simulate("pointer_move", x=x + DRAG_THRESHOLD + 2, y=y)


def _move_to(app, point):
    app.window.simulate("pointer_move", x=point[0], y=point[1])


def _drop_at(app, point):
    app.window.simulate("pointer_move", x=point[0], y=point[1])
    app.window.simulate("pointer_up", x=point[0], y=point[1])
    app.window.advance(16)


def _drag_to(app, tab, point):
    _pick_up(app, tab)
    _drop_at(app, point)


def _new_half(host):
    return next(name for name in host.halves() if name not in ("left_half", "right_half"))


# -- finding the half and the band -----------------------------------------------------------------

def test_a_tab_over_a_halfs_middle_highlights_the_whole_half():
    app, view = _view()
    host = view.dock_host("dock")
    half = view.node("left_half")
    _pick_up(app, _tab(host, "left", "Outline"))
    _move_to(app, _point(half, "middle"))
    assert host.dock._half_target == ("left_half", "middle")
    highlight = host.dock.highlight
    assert highlight.parent() == half
    assert (highlight.get("x"), highlight.get("y")) == (0.0, 0.0)
    assert (highlight.get("width"), highlight.get("height")) == (half.get("layout_width"), half.get("layout_height"))


@pytest.mark.parametrize("band", ["left", "right", "top", "bottom"])
def test_a_tab_near_a_halfs_side_highlights_that_edge_band(band):
    app, view = _view()
    host = view.dock_host("dock")
    half = view.node("right_half")
    width, height = half.get("layout_width"), half.get("layout_height")
    _pick_up(app, _tab(host, "left", "Outline"))
    _move_to(app, _point(half, band))
    assert host.dock._half_target == ("right_half", band)
    h = host.dock.highlight
    assert h.parent() == half
    if band in ("left", "right"):
        assert h.get("width") == pytest.approx(width * HALF_EDGE) and h.get("height") == height
        assert h.get("x") == (0.0 if band == "left" else pytest.approx(width - width * HALF_EDGE))
    else:
        assert h.get("height") == pytest.approx(height * HALF_EDGE) and h.get("width") == width
        assert h.get("y") == (0.0 if band == "top" else pytest.approx(height - height * HALF_EDGE))


def test_the_other_half_and_the_zone_take_the_highlight_as_the_pointer_moves():
    app, view = _view()
    host = view.dock_host("dock")
    left, right = view.node("left_half"), view.node("right_half")
    _pick_up(app, _tab(host, "left", "Outline"))
    _move_to(app, _point(left, "middle"))
    assert host.dock.highlight.parent() == left
    _move_to(app, _point(right, "middle"))
    assert host.dock._half_target == ("right_half", "middle") and host.dock.highlight.parent() == right
    handle = view.node("editor.split.0")  # between the halves: in the centre zone, in no half
    _move_to(app, _centre(handle))
    assert host.dock._half_target is None
    assert host.dock.highlight.parent() == host.dock._zones["center"].body
    assert host.dock.highlight.get("width") == "100%"  # the zone's highlight is the whole zone again
    _move_to(app, _centre(host.dock._zones["bottom"].body))
    assert host.dock.highlight.parent() == host.dock._zones["bottom"].body


def test_the_highlight_goes_when_the_drag_ends_and_no_half_is_left_targeted():
    app, view = _view()
    host = view.dock_host("dock")
    _pick_up(app, _tab(host, "left", "Outline"))
    _move_to(app, _point(view.node("left_half"), "left"))
    _drop_at(app, (5, 5))  # outside every zone and half: tre leaves the panel where it was
    assert host.dock.highlight.parent() is None and host.dock._half_target is None and host.dock._tracking == []
    assert host.layout()["zones"]["left"]["panels"] == ["Files", "Outline"]


def test_a_panel_is_not_offered_the_halves_inside_itself():
    app, view = _view()
    host = view.dock_host("dock")
    _pick_up(app, _tab(host, "center", "Editor"))  # the panel the two halves are in
    _move_to(app, _point(view.node("left_half"), "middle"))
    assert host.dock._half_target is None
    _drop_at(app, _point(view.node("left_half"), "middle"))
    assert host.halves()["left_half"] == {"panels": [], "shown": None}
    assert host.layout()["zones"]["center"]["panels"] == ["Editor"]


def test_a_dock_without_halves_behaves_as_it_did():
    app, view = _view()
    host = view.dock_host("dock")
    host.dock.accept_halves(None)
    _pick_up(app, _tab(host, "left", "Outline"))
    _move_to(app, _point(view.node("left_half"), "middle"))
    assert host.dock._half_target is None
    assert host.dock.highlight.parent() == host.dock._zones["center"].body


# -- dropping on the middle: the panel joins the half --------------------------------------------------

def test_a_drop_on_a_halfs_middle_adds_the_panel_to_the_half_and_shows_it():
    app, view = _view()
    host = view.dock_host("dock")
    half = view.node("left_half")
    _drag_to(app, _tab(host, "left", "Outline"), _point(half, "middle"))
    assert view.node("outline").parent() == half
    assert host.halves()["left_half"] == {"panels": ["outline"], "shown": "outline"}
    assert host.half_of("outline") == "left_half"
    assert host.layout()["zones"]["left"]["panels"] == ["Files"]  # out of its zone
    assert host.dock.side_of(view.node("outline")) is None
    assert view.node("left_text").get("visible") is False  # the half's own content gives way
    assert view.node("outline").get("visible") and view.node("outline").get("layout_width") == half.get("layout_width")
    assert host.dock.highlight.parent() is None


def test_a_panel_dropped_from_the_centre_zone_comes_out_of_it_too():
    """tre moves the dragged panel to the zone it reports (centre, here) before the drop; the half takes it from there."""
    app, view = _view()
    host = view.dock_host("dock")
    host.dock.move(view.node("outline"), "center")  # a second centre panel, with a tab of its own
    app.window.advance(16)
    _drag_to(app, _tab(host, "center", "Outline"), _point(view.node("right_half"), "middle"))
    assert host.half_of("outline") == "right_half" and view.node("outline").parent() == view.node("right_half")
    assert host.layout()["zones"]["center"]["panels"] == ["Editor"]
    assert host.dock.shown_title("center") == "Editor"


def test_show_in_half_switches_between_the_halfs_own_content_and_its_panels():
    app, view = _view()
    host = view.dock_host("dock")
    half = view.node("left_half")
    _drag_to(app, _tab(host, "left", "Outline"), _point(half, "middle"))
    _drag_to(app, _tab(host, "left", "Files"), _point(half, "middle"))
    assert host.halves()["left_half"] == {"panels": ["outline", "files"], "shown": "files"}
    host.show_in_half("left_half", None)
    app.window.advance(16)
    assert view.node("left_text").get("visible") and not view.node("files").get("visible") and not view.node("outline").get("visible")
    host.show_in_half("left_half", "outline")
    assert view.node("outline").get("visible") and not view.node("left_text").get("visible")
    with pytest.raises(ValueError, match="isn't in"):
        host.show_in_half("left_half", "console")
    with pytest.raises(ValueError, match="no half"):
        host.show_in_half("editor", None)


def test_a_panel_in_a_half_goes_back_to_a_zone_with_move():
    app, view = _view()
    host = view.dock_host("dock")
    _drag_to(app, _tab(host, "left", "Outline"), _point(view.node("left_half"), "middle"))
    host.move("outline", "bottom")
    app.window.advance(16)
    assert host.half_of("outline") is None and host.layout()["zones"]["bottom"]["panels"] == ["Console", "Outline"]
    assert host.halves()["left_half"] == {"panels": [], "shown": None}
    assert view.node("left_text").get("visible")  # the half shows its own content again
    assert view.node("outline").get("visible")


def test_a_hidden_panel_leaving_a_half_is_shown_again_in_its_zone():
    app, view = _view()
    host = view.dock_host("dock")
    half = view.node("left_half")
    _drag_to(app, _tab(host, "left", "Outline"), _point(half, "middle"))
    _drag_to(app, _tab(host, "left", "Files"), _point(half, "middle"))  # Files shows; Outline is hidden behind it
    assert not view.node("outline").get("visible")
    host.move("outline", "bottom")
    app.window.advance(16)
    assert view.node("outline").get("visible") and view.node("files").get("visible")
    assert host.halves()["left_half"] == {"panels": ["files"], "shown": "files"}  # the one that was shown stays shown


def test_closing_or_removing_a_panel_in_a_half_leaves_the_half():
    spec = yaml.safe_load(DOCK)
    spec["children"][0]["children"][1]["closable"] = True  # Outline
    app, view = _view(yaml.safe_dump(spec))
    host = view.dock_host("dock")
    _drag_to(app, _tab(host, "left", "Outline"), _point(view.node("left_half"), "middle"))
    host.close("outline")
    assert host.closed() == ["outline"] and host.halves()["left_half"] == {"panels": [], "shown": None}
    assert view.node("left_text").get("visible")
    host.reopen("outline")  # back in the zone it was dragged from
    assert host.layout()["zones"]["left"]["panels"] == ["Files", "Outline"]


# -- dropping on an edge: the half splits -------------------------------------------------------------

@pytest.mark.parametrize("band, horizontal, new_first", [("left", True, True), ("right", True, False),
                                                         ("top", False, True), ("bottom", False, False)])
def test_a_drop_on_a_halfs_edge_splits_it_with_the_panel_in_the_new_half(band, horizontal, new_first):
    app, view = _view()
    host = view.dock_host("dock")
    old = view.node("right_half")
    x, y, w, h = (old.get(k) for k in ("layout_x", "layout_y", "layout_width", "layout_height"))
    _drag_to(app, _tab(host, "left", "Outline"), _point(old, band))
    app.window.advance(32)
    outline = view.node("outline")
    new = outline.parent()
    assert new != old and old.parent() == new.parent() and host.half_of("outline") == _new_half(host)
    both = old.parent()
    assert both.parent() == view.node("editor")
    # the old half and the new one share the room the old one had, with a handle between
    extent = "layout_width" if horizontal else "layout_height"
    sizes = (old.get(extent), new.get(extent))
    assert sum(sizes) + HANDLE_SPAN == pytest.approx(w if horizontal else h, abs=1.5)
    assert sizes[0] == pytest.approx(sizes[1], abs=1.5)
    axis, other = ("layout_x", "layout_y") if horizontal else ("layout_y", "layout_x")
    assert (new.get(axis) < old.get(axis)) == new_first
    assert new.get(other) == old.get(other)
    assert both.get("layout_x") == x and both.get("layout_y") == y
    assert outline.get("layout_width") == new.get("layout_width")  # the panel fills its half
    assert view.node("right_text").get("visible")  # the old half keeps its content
    assert host.layout()["zones"]["left"]["panels"] == ["Files"]


def test_the_new_split_has_a_handle_that_resizes_the_half_before_it():
    app, view = _view()
    host = view.dock_host("dock")
    old = view.node("right_half")
    _drag_to(app, _tab(host, "left", "Outline"), _point(old, "right"))
    app.window.advance(32)
    assert len(host._made_splits) == 1
    handle = host._made_splits[0]
    before = old.get("layout_width")
    x, y = _centre(handle.node)
    app.window.simulate("pointer_down", handle.node, x=8, y=8)
    app.window.simulate("pointer_move", x=x + 30, y=y)
    app.window.simulate("pointer_up", x=x + 30, y=y)
    app.window.advance(16)
    assert old.get("layout_width") == pytest.approx(before + 30, abs=1.5)
    low, high = handle.bounds()
    handle.set(0)
    assert handle.get() == MIN_SPLIT and low == MIN_SPLIT and high > low


def test_a_new_half_takes_drops_of_its_own_and_can_be_split_again():
    app, view = _view()
    host = view.dock_host("dock")
    _drag_to(app, _tab(host, "left", "Outline"), _point(view.node("right_half"), "right"))
    app.window.advance(32)
    name = _new_half(host)
    node = view.node("outline").parent()
    assert host._halves[name] == node
    assert host.halves()[name] == {"panels": ["outline"], "shown": "outline"}
    _drag_to(app, _tab(host, "left", "Files"), _point(node, "bottom"))  # splits the new half, top and bottom
    app.window.advance(32)
    assert len(host._made_splits) == 2 and host.half_of("files") != name
    assert view.node("files").parent().parent() == node.parent()
    assert view.node("files").get("layout_y") > node.get("layout_y")


def test_the_split_handle_is_painted_and_follows_the_theme():
    app, view = _view(dark=True)
    host = view.dock_host("dock")
    _drag_to(app, _tab(host, "left", "Outline"), _point(view.node("right_half"), "left"))
    grip = host._made_splits[0].grip
    before = grip.get("fill")
    app.set_dark(False)
    app.window.advance(16)
    assert grip.get("fill") != before and grip.get("fill") == app.theme.role("outline")


def test_a_dock_that_is_disposed_lets_go_of_the_made_splits():
    app, view = _view()
    host = view.dock_host("dock")
    _drag_to(app, _tab(host, "left", "Outline"), _point(view.node("right_half"), "right"))
    view._dispose_controls()
    assert not host._made_splits and not host._handles
