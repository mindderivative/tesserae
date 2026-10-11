"""0.5.0 (#106) phases 2 and 3: the halves of a split as mini zones of the Dock -- a tab strip over each half, a dragged panel dropped
onto one (the middle adds it as a tab, an edge splits the half), a tab of a half dragged out to a zone or another half, a half a
split made collapsing when it empties, the "Move to" menu, and a reload leaving all of it where the user put it. Driven headlessly
with `simulate`; a real window was checked for the one thing it decides (the root's `pointer_move`s keep arriving during a tre drag:
tools/spikes/drag_events.py)."""

import pytest
import yaml

from tesserae.docking import DRAG_THRESHOLD, HALF, HALF_EDGE, TAB_HEIGHT
from tesserae.dockhost import HANDLE_SPAN, MIN_SPLIT
from test_dock_view import DOCK, _reload, _view


def _centre(node):
    return node.get("layout_x") + node.get("layout_width") / 2, node.get("layout_y") + node.get("layout_height") / 2


def _point(node, where):
    """A point in `node`: its `middle`, or 6 px inside an edge (`left`, `right`, `top`, `bottom`)."""
    x, y, w, h = (node.get(k) for k in ("layout_x", "layout_y", "layout_width", "layout_height"))
    cx, cy = x + w / 2, y + h / 2
    return {"middle": (cx, cy), "left": (x + 6, cy), "right": (x + w - 6, cy), "top": (cx, y + 6), "bottom": (cx, y + h - 6)}[where]


def _slot(host, name):
    """The column a half stands in (its strip and its body): what a drop is aimed at."""
    return host.dock.half_slot(name)


def _tab(host, side, title):
    zone = host.dock._zones[side]
    return zone.tabs[host.dock.titles(side).index(title)].node


def _half_tab(host, half, title):
    return _tab(host, HALF + half, title)


def _pick_up(app, tab):
    """Presses `tab` and moves it past the drag threshold: a drag has begun."""
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


def _join(app, host, half, panel="Outline", side="left"):
    """Drags the tab `panel` in `side` onto the middle of `half`."""
    _drag_to(app, _tab(host, side, panel), _point(_slot(host, half), "middle"))
    app.window.advance(16)


def _split(app, host, half, band, panel="Outline", side="left"):
    _drag_to(app, _tab(host, side, panel), _point(_slot(host, half), band))
    app.window.advance(32)


def _outside(host):
    """A point in no zone and no half: the resize handle between the left zone and the middle."""
    return _centre(host._handles["left"].node)


def _menu_items(host):
    menu = host.dock._menu
    return [menu.widget.part(f"item{i}.label").get("text") for i in range(len(menu.items))]


# -- a half is a mini zone: a tab strip over its content -----------------------------------------------

def test_each_half_is_a_column_with_a_tab_strip_over_its_content_titled_by_its_panel():
    app, view = _view()
    host = view.dock_host("dock")
    for name in ("left_half", "right_half"):
        zone = host.dock._zones[HALF + name]
        assert zone.strip.get("role") == "tablist" and zone.strip.get("layout_height") == TAB_HEIGHT
        assert host.dock.titles(HALF + name) == [name]  # a lone panel has its title on a tab too
        assert zone.tabs[0].node.get("selected") and zone.body == view.node(name)
        assert zone.node.get("fill") == app.theme.role("surface")
    column, body = _slot(host, "left_half"), view.node("left_half")
    assert column.get("layout_width") == 300.0 and body.get("layout_width") == 300.0  # the column keeps the half's width
    assert body.get("layout_y") == column.get("layout_y") + TAB_HEIGHT + 1  # under the strip and its divider
    assert body.get("layout_height") == column.get("layout_height") - TAB_HEIGHT - 1
    assert view.node("left_text").get("visible")
    assert [c == view.node("editor.split.0") for c in view.node("editor").children()] == [False, True, False]


def test_a_halfs_title_is_the_panels_title():
    spec = yaml.safe_load(DOCK)
    spec["children"][0]["children"][2]["children"][0]["title"] = "Source"
    app, view = _view(yaml.safe_dump(spec))
    assert view.dock_host("dock").dock.titles(HALF + "left_half") == ["Source"]


def test_a_halfs_own_tab_does_not_drag_close_or_open_a_menu():
    app, view = _view()
    host = view.dock_host("dock")
    tab = _half_tab(host, "left_half", "left_half")
    _pick_up(app, tab)
    assert host.dock._dragging is None and not host.dock._own_drag
    x, y = _centre(tab)
    app.window.simulate("pointer_up", x=x, y=y)
    app.window.simulate("secondary_click", x=x, y=y)
    assert host.dock._menu is None
    with pytest.raises(ValueError, match="own content"):
        host.dock.move(view.node("left_half"), "left")
    assert host.dock.panel("left_half") is None and host.dock.panels(HALF + "left_half") == []


# -- finding the half and the band ------------------------------------------------------------------

def test_a_tab_over_a_halfs_middle_highlights_the_whole_half_strip_and_all():
    app, view = _view()
    host = view.dock_host("dock")
    half = _slot(host, "left_half")
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
    half = _slot(host, "right_half")
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
    left, right = _slot(host, "left_half"), _slot(host, "right_half")
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
    _move_to(app, _point(_slot(host, "left_half"), "left"))
    _drop_at(app, (5, 5))  # outside every zone and half: tre leaves the panel where it was
    assert host.dock.highlight.parent() is None and host.dock._half_target is None and host.dock._tracking == []
    assert host.layout()["zones"]["left"]["panels"] == ["Files", "Outline"]


def test_a_panel_is_not_offered_the_halves_inside_itself():
    app, view = _view()
    host = view.dock_host("dock")
    _pick_up(app, _tab(host, "center", "Editor"))  # the panel the two halves are in
    _move_to(app, _point(_slot(host, "left_half"), "middle"))
    assert host.dock._half_target is None
    _drop_at(app, _point(_slot(host, "left_half"), "middle"))
    assert host.halves()["left_half"] == {"panels": [], "shown": None}
    assert host.layout()["zones"]["center"]["panels"] == ["Editor"]


def test_a_dock_without_a_halves_handler_takes_no_drops_on_them():
    app, view = _view()
    host = view.dock_host("dock")
    host.dock.on_half_drop(None)
    _pick_up(app, _tab(host, "left", "Outline"))
    _move_to(app, _point(_slot(host, "left_half"), "middle"))
    assert host.dock._half_target is None
    assert host.dock.highlight.parent() == host.dock._zones["center"].body


# -- dropping on the middle: the panel joins the half as a tab ---------------------------------------

def test_a_drop_on_a_halfs_middle_adds_the_panel_as_a_tab_and_shows_it():
    app, view = _view()
    host = view.dock_host("dock")
    half = view.node("left_half")
    _join(app, host, "left_half")
    assert view.node("outline").parent() == half
    assert host.halves()["left_half"] == {"panels": ["outline"], "shown": "outline"}
    assert host.half_of("outline") == "left_half"
    assert host.dock.titles(HALF + "left_half") == ["left_half", "Outline"]  # its own content is the first tab
    assert [t.node.get("selected") for t in host.dock._zones[HALF + "left_half"].tabs] == [False, True]
    assert host.layout()["zones"]["left"]["panels"] == ["Files"]  # out of its zone
    assert view.node("left_text").get("visible") is False  # the half's own content gives way
    assert view.node("outline").get("visible") and view.node("outline").get("layout_width") == half.get("layout_width")
    assert host.dock.highlight.parent() is None


def test_a_drop_on_a_halfs_strip_adds_the_panel_too():
    app, view = _view()
    host = view.dock_host("dock")
    strip = host.dock._zones[HALF + "right_half"].strip
    _pick_up(app, _tab(host, "left", "Outline"))
    _move_to(app, _centre(strip))
    assert host.dock._half_target == ("right_half", "top")  # the strip is the top of the column: a top edge splits
    _move_to(app, (_centre(strip)[0], _centre(_slot(host, "right_half"))[1]))
    _drop_at(app, _point(_slot(host, "right_half"), "middle"))
    assert host.half_of("outline") == "right_half"


def test_a_panel_dropped_from_the_centre_zone_comes_out_of_it_too():
    """tre moves the dragged panel to the zone it reports (centre, here) before the drop; the half takes it from there."""
    app, view = _view()
    host = view.dock_host("dock")
    host.dock.move(view.node("outline"), "center")  # a second centre panel, with a tab of its own
    app.window.advance(16)
    _drag_to(app, _tab(host, "center", "Outline"), _point(_slot(host, "right_half"), "middle"))
    assert host.half_of("outline") == "right_half" and view.node("outline").parent() == view.node("right_half")
    assert host.layout()["zones"]["center"]["panels"] == ["Editor"]
    assert host.dock.shown_title("center") == "Editor"


def test_a_click_or_the_arrows_switch_between_a_halfs_own_content_and_its_panels():
    app, view = _view()
    host = view.dock_host("dock")
    _join(app, host, "left_half", "Outline")
    _join(app, host, "left_half", "Files")
    assert host.halves()["left_half"] == {"panels": ["outline", "files"], "shown": "files"}
    app.window.simulate("click", node=_half_tab(host, "left_half", "left_half"))
    app.window.advance(16)
    assert view.node("left_text").get("visible") and not view.node("files").get("visible") and not view.node("outline").get("visible")
    assert host.halves()["left_half"]["shown"] is None
    app.window.simulate("click", node=_half_tab(host, "left_half", "Outline"))
    assert view.node("outline").get("visible") and not view.node("left_text").get("visible") and not view.node("files").get("visible")
    _half_tab(host, "left_half", "Outline").focus()
    app.window.simulate("key_down", key="arrow_right")
    assert host.halves()["left_half"]["shown"] == "files"
    app.window.simulate("key_down", key="arrow_right")  # wraps to the half's own content
    assert host.halves()["left_half"]["shown"] is None


def test_show_in_half_and_its_errors():
    app, view = _view()
    host = view.dock_host("dock")
    _join(app, host, "left_half")
    host.show_in_half("left_half", None)
    assert view.node("left_text").get("visible") and not view.node("outline").get("visible")
    host.show_in_half("left_half", "outline")
    assert view.node("outline").get("visible") and not view.node("left_text").get("visible")
    with pytest.raises(ValueError, match="isn't in"):
        host.show_in_half("left_half", "console")
    with pytest.raises(ValueError, match="no half"):
        host.show_in_half("editor", None)


def test_a_panel_in_a_half_goes_back_to_a_zone_with_move():
    app, view = _view()
    host = view.dock_host("dock")
    _join(app, host, "left_half")
    host.move("outline", "bottom")
    app.window.advance(16)
    assert host.half_of("outline") is None and host.layout()["zones"]["bottom"]["panels"] == ["Console", "Outline"]
    assert host.halves()["left_half"] == {"panels": [], "shown": None}
    assert view.node("left_text").get("visible")  # the half shows its own content again
    assert view.node("outline").get("visible")


def test_a_hidden_panel_leaving_a_half_is_shown_again_in_its_zone():
    app, view = _view()
    host = view.dock_host("dock")
    _join(app, host, "left_half", "Outline")
    _join(app, host, "left_half", "Files")  # Files shows; Outline is hidden behind it
    assert not view.node("outline").get("visible")
    host.move("outline", "bottom")
    app.window.advance(16)
    assert view.node("outline").get("visible") and view.node("files").get("visible")
    assert host.halves()["left_half"] == {"panels": ["files"], "shown": "files"}  # the one that was shown stays shown


def test_closing_a_panel_in_a_half_leaves_the_half_and_it_reopens_in_its_zone():
    spec = yaml.safe_load(DOCK)
    spec["children"][0]["children"][1]["closable"] = True  # Outline
    app, view = _view(yaml.safe_dump(spec))
    host = view.dock_host("dock")
    _join(app, host, "left_half")
    close_button = next(c for c in host.dock._zones[HALF + "left_half"].tabs[1].node.children() if c.get("role") == "button")
    app.window.simulate("click", node=close_button)
    assert host.closed() == ["outline"] and host.halves()["left_half"] == {"panels": [], "shown": None}
    assert view.node("left_text").get("visible")
    host.reopen("outline")  # back in the zone it was dragged from
    assert host.layout()["zones"]["left"]["panels"] == ["Files", "Outline"]


# -- dropping on an edge: the half splits ---------------------------------------------------------------

@pytest.mark.parametrize("band, horizontal, new_first", [("left", True, True), ("right", True, False),
                                                         ("top", False, True), ("bottom", False, False)])
def test_a_drop_on_a_halfs_edge_splits_it_with_the_panel_in_the_new_half(band, horizontal, new_first):
    app, view = _view()
    host = view.dock_host("dock")
    old = _slot(host, "right_half")
    x, y, w, h = (old.get(k) for k in ("layout_x", "layout_y", "layout_width", "layout_height"))
    _split(app, host, "right_half", band)
    new = _slot(host, _new_half(host))
    assert host.half_of("outline") == _new_half(host) and view.node("outline").parent() == host._halves[_new_half(host)]
    both = old.parent()
    assert new.parent() == both and both.parent() == view.node("editor")
    # the old half and the new one share the room the old one had, with a handle between
    extent = "layout_width" if horizontal else "layout_height"
    sizes = (old.get(extent), new.get(extent))
    assert sum(sizes) + HANDLE_SPAN == pytest.approx(w if horizontal else h, abs=1.5)
    assert sizes[0] == pytest.approx(sizes[1], abs=1.5)
    axis, other = ("layout_x", "layout_y") if horizontal else ("layout_y", "layout_x")
    assert (new.get(axis) < old.get(axis)) == new_first
    assert new.get(other) == old.get(other)
    assert both.get("layout_x") == x and both.get("layout_y") == y
    assert view.node("outline").get("layout_width") == view.node("outline").parent().get("layout_width")  # the panel fills its half
    assert view.node("right_text").get("visible")  # the old half keeps its content
    assert host.layout()["zones"]["left"]["panels"] == ["Files"]
    assert host.dock.titles(HALF + _new_half(host)) == ["Outline"] and new.get("layout_width") > 0  # its own strip, one tab


def test_the_new_split_has_a_handle_that_resizes_the_half_before_it():
    app, view = _view()
    host = view.dock_host("dock")
    old = _slot(host, "right_half")
    _split(app, host, "right_half", "right")
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
    _split(app, host, "right_half", "right")
    name = _new_half(host)
    node = _slot(host, name)
    assert host.halves()[name] == {"panels": ["outline"], "shown": "outline"}
    _drag_to(app, _tab(host, "left", "Files"), _point(node, "bottom"))  # splits the new half, top and bottom
    app.window.advance(32)
    assert len(host._made_splits) == 2 and host.half_of("files") != name
    assert view.node("files").get("layout_y") > view.node("outline").get("layout_y")


def test_the_split_handle_is_painted_and_follows_the_theme():
    app, view = _view(dark=True)
    host = view.dock_host("dock")
    _split(app, host, "right_half", "left")
    grip = host._made_splits[0].grip
    before = grip.get("fill")
    app.set_dark(False)
    app.window.advance(16)
    assert grip.get("fill") != before and grip.get("fill") == app.theme.role("outline")


def test_a_dock_that_is_disposed_lets_go_of_the_made_splits():
    app, view = _view()
    host = view.dock_host("dock")
    _split(app, host, "right_half", "right")
    view._dispose_controls()
    assert not host._made_splits and not host._handles


# -- dragging a tab of a half ------------------------------------------------------------------------

def test_a_tab_of_a_half_is_dragged_with_the_pointer_captured_not_by_tre():
    app, view = _view()
    host = view.dock_host("dock")
    _join(app, host, "left_half")
    tab = _half_tab(host, "left_half", "Outline")
    _pick_up(app, tab)
    assert host.dock._own_drag and host.dock._dragging.title == "Outline"
    _move_to(app, _centre(host.dock._zones["bottom"].body))
    assert host.dock._zone_target == "bottom" and host.dock.highlight.parent() == host.dock._zones["bottom"].body
    _move_to(app, _point(_slot(host, "right_half"), "left"))
    assert host.dock._half_target == ("right_half", "left") and host.dock.highlight.parent() == _slot(host, "right_half")
    _move_to(app, _outside(host))
    assert host.dock._zone_target is None and host.dock._half_target is None and host.dock.highlight.parent() is None


def test_a_tab_of_a_half_dropped_on_a_zone_moves_the_panel_there():
    app, view = _view()
    host = view.dock_host("dock")
    moves = []
    host.dock.on_move(lambda node, side: moves.append(side))
    _join(app, host, "left_half")
    _drag_to(app, _half_tab(host, "left_half", "Outline"), _centre(host.dock._zones["bottom"].body))
    assert host.half_of("outline") is None and host.layout()["zones"]["bottom"]["panels"] == ["Console", "Outline"]
    assert host.halves()["left_half"] == {"panels": [], "shown": None} and view.node("left_text").get("visible")
    assert moves == ["bottom"] and host.dock._dragging is None and not host.dock._own_drag
    assert host.dock.highlight.parent() is None


def test_a_tab_of_a_half_dropped_on_another_half_joins_it_or_splits_it():
    app, view = _view()
    host = view.dock_host("dock")
    _join(app, host, "left_half")
    _drag_to(app, _half_tab(host, "left_half", "Outline"), _point(_slot(host, "right_half"), "middle"))
    assert host.half_of("outline") == "right_half" and host.halves()["left_half"]["panels"] == []
    _drag_to(app, _half_tab(host, "right_half", "Outline"), _point(_slot(host, "left_half"), "right"))
    app.window.advance(32)
    assert host.half_of("outline") == _new_half(host) and host.halves()["right_half"]["panels"] == []
    assert _slot(host, _new_half(host)).get("layout_x") > _slot(host, "left_half").get("layout_x")


def test_a_tab_of_a_half_released_outside_everything_stays():
    app, view = _view()
    host = view.dock_host("dock")
    _join(app, host, "left_half")
    _drag_to(app, _half_tab(host, "left_half", "Outline"), _outside(host))
    assert host.half_of("outline") == "left_half" and host.dock._dragging is None


def test_a_halfs_panel_dropped_on_its_own_halfs_middle_stays_and_on_an_edge_splits_it():
    app, view = _view()
    host = view.dock_host("dock")
    _join(app, host, "left_half")
    _pick_up(app, _half_tab(host, "left_half", "Outline"))
    _move_to(app, _point(_slot(host, "left_half"), "middle"))
    assert host.dock._half_target is None  # nothing to do there
    _drop_at(app, _point(_slot(host, "left_half"), "middle"))
    assert host.half_of("outline") == "left_half"
    _drag_to(app, _half_tab(host, "left_half", "Outline"), _point(_slot(host, "left_half"), "bottom"))  # own content + a panel: it splits
    app.window.advance(32)
    assert host.half_of("outline") == _new_half(host) and host.halves()["left_half"]["panels"] == []


def test_the_os_taking_the_press_cancels_a_tab_drag_of_a_half():
    app, view = _view()
    host = view.dock_host("dock")
    _join(app, host, "left_half")
    _pick_up(app, _half_tab(host, "left_half", "Outline"))
    _move_to(app, _centre(host.dock._zones["bottom"].body))
    host.dock._tab_up(False)  # what the tab's `pointer_cancel` listener calls (`simulate` cannot deliver one)
    assert host.half_of("outline") == "left_half" and host.dock._dragging is None and host.dock.highlight.parent() is None


# -- a half a split made collapses when it empties ------------------------------------------------------

def _structure(view, host):
    """Where the right half is and how big, as numbers."""
    old = _slot(host, "right_half")
    return old.parent() == view.node("editor"), round(old.get("layout_width")), round(old.get("layout_x"))


def test_a_made_half_that_loses_its_panel_collapses_into_its_neighbour():
    app, view = _view()
    host = view.dock_host("dock")
    before = _structure(view, host)
    _split(app, host, "right_half", "right")
    assert _structure(view, host) != before
    name = _new_half(host)
    host.move("outline", "bottom")
    app.window.advance(32)
    assert _structure(view, host) == before  # the neighbour is back in the place the pair had, at its size
    assert name not in host.halves() and not host._made_splits and not host._made_halves
    assert HALF + name not in host.dock._zones and host.layout()["zones"]["bottom"]["panels"] == ["Console", "Outline"]
    assert [c == view.node("editor.split.0") for c in view.node("editor").children()] == [False, True, False]


def test_dragging_the_only_panel_of_a_made_half_to_a_zone_collapses_it():
    app, view = _view()
    host = view.dock_host("dock")
    before = _structure(view, host)
    _split(app, host, "right_half", "left")
    _drag_to(app, _half_tab(host, _new_half(host), "Outline"), _centre(host.dock._zones["bottom"].body))
    app.window.advance(32)
    assert _structure(view, host) == before and host.layout()["zones"]["bottom"]["panels"] == ["Console", "Outline"]


def test_dragging_the_only_panel_of_a_made_half_onto_another_half_moves_it_and_collapses_the_first():
    app, view = _view()
    host = view.dock_host("dock")
    _split(app, host, "right_half", "right")
    name = _new_half(host)
    _drag_to(app, _half_tab(host, name, "Outline"), _point(_slot(host, "left_half"), "middle"))
    app.window.advance(32)
    assert host.half_of("outline") == "left_half" and name not in host.halves() and not host._made_splits
    assert view.node("outline").get("layout_width") > 0 and _slot(host, "right_half").parent() == view.node("editor")


def test_closing_the_only_panel_of_a_made_half_collapses_it():
    spec = yaml.safe_load(DOCK)
    spec["children"][0]["children"][1]["closable"] = True
    app, view = _view(yaml.safe_dump(spec))
    host = view.dock_host("dock")
    before = _structure(view, host)
    _split(app, host, "right_half", "bottom")
    host.close("outline")
    app.window.advance(32)
    assert not host._made_halves and host.closed() == ["outline"]
    assert _structure(view, host) == before


def test_a_split_inside_a_split_collapses_from_the_inside_out():
    app, view = _view()
    host = view.dock_host("dock")
    _split(app, host, "right_half", "right", "Outline")
    inner = _new_half(host)
    _drag_to(app, _tab(host, "left", "Files"), _point(_slot(host, inner), "bottom"))
    app.window.advance(32)
    assert len(host._made_splits) == 2
    host.move("files", "bottom")
    app.window.advance(32)
    assert len(host._made_splits) == 1 and list(host.halves()) == ["left_half", "right_half", inner]
    host.move("outline", "left")
    app.window.advance(32)
    assert not host._made_splits and list(host.halves()) == ["left_half", "right_half"]
    assert _slot(host, "right_half").parent() == view.node("editor")


# -- the "Move to" menu lists the halves ----------------------------------------------------------------

def test_the_move_to_menu_offers_every_zone_and_half_but_not_where_the_panel_is_or_its_own_halves():
    app, view = _view()
    host = view.dock_host("dock")
    _tab(host, "left", "Outline").focus()
    app.window.simulate("key_down", key="context_menu")
    assert set(_menu_items(host)) == {"Move to bottom", "Move to center", "Move to left_half", "Move to right_half"}
    host.dock._menu.close()
    _tab(host, "center", "Editor").focus()
    app.window.simulate("key_down", key="context_menu")
    assert not any("half" in label for label in _menu_items(host))  # the halves inside the Editor are not offered to the Editor


def test_choosing_a_half_in_the_move_to_menu_tabs_the_panel_into_it():
    app, view = _view()
    host = view.dock_host("dock")
    _tab(host, "left", "Outline").focus()
    app.window.simulate("key_down", key="context_menu")
    index = _menu_items(host).index("Move to right_half")
    app.window.simulate("click", node=host.dock._menu.items[index])
    app.window.advance(16)
    assert host.half_of("outline") == "right_half" and host.halves()["right_half"]["shown"] == "outline"


def test_a_panel_in_a_half_has_the_menu_too_and_moves_back_to_a_zone():
    app, view = _view()
    host = view.dock_host("dock")
    _join(app, host, "left_half")
    _half_tab(host, "left_half", "Outline").focus()
    app.window.simulate("key_down", key="context_menu")
    items = _menu_items(host)
    assert "Move to left" in items and "Move to left_half" not in items and "Move to right_half" in items
    app.window.simulate("click", node=host.dock._menu.items[items.index("Move to left")])
    app.window.advance(16)
    assert host.half_of("outline") is None and host.layout()["zones"]["left"]["panels"] == ["Files", "Outline"]


# -- a reload leaves it where the user put it ---------------------------------------------------------------

def test_a_reload_leaves_the_strips_and_the_columns_in_place():
    app, view = _view()
    host = view.dock_host("dock")
    slot = _slot(host, "left_half")
    _reload(view, lambda d: None)
    app.window.advance(16)
    assert view.dock_host("dock") is host and _slot(host, "left_half") == slot
    assert slot.parent() == view.node("editor") and view.node("left_half").parent() == slot
    assert [c == view.node("editor.split.0") for c in view.node("editor").children()] == [False, True, False]
    assert view.node("left_half").get("layout_width") == 300.0


def test_a_reload_leaves_a_panel_dropped_on_a_half_and_a_split_where_they_are():
    app, view = _view()
    host = view.dock_host("dock")
    _join(app, host, "left_half", "Outline")
    _split(app, host, "right_half", "right", "Files")
    name = _new_half(host)
    snapshot = (host.halves(), _slot(host, name).get("layout_x"), _slot(host, "right_half").get("layout_width"))
    _reload(view, lambda d: None)
    app.window.advance(32)
    assert host.halves() == snapshot[0]
    assert _slot(host, name).get("layout_x") == snapshot[1] and _slot(host, "right_half").get("layout_width") == snapshot[2]
    assert view.node("outline").parent() == view.node("left_half") and view.node("files").get("layout_width") > 0
    assert view.node("editor.split.0").parent() == view.node("editor")


def test_a_reload_that_edits_a_halfs_content_patches_it_in_place():
    app, view = _view()
    host = view.dock_host("dock")
    _join(app, host, "left_half")

    def change(spec):
        spec["children"][0]["children"][2]["children"][0]["children"][0]["text"]["content"] = "Edited"
    _reload(view, change)
    assert view.node("left_text").get("text") == "Edited" and host.halves()["left_half"] == {"panels": ["outline"], "shown": "outline"}
    assert not view.node("left_text").get("visible")  # still behind the panel the user dropped there


def test_a_reload_that_turns_a_half_into_a_split_gives_the_new_halves_strips_and_drops_the_old_one():
    app, view = _view()
    host = view.dock_host("dock")
    old_strip = host.dock._zones[HALF + "left_half"].strip
    text = lambda i: {"id": i, "kind": "Text", "text": {"content": i, "typography_role": "body_large"}, "style": {"foreground": "on_surface"}}

    def change(spec):
        spec["children"][0]["children"][2]["children"][0]["children"] = [
            {"id": "a", "kind": "DockPanel", "title": "A", "children": [text("a_t")]},
            {"id": "b", "kind": "DockPanel", "title": "B", "children": [text("b_t")]}]
    _reload(view, change)
    app.window.advance(32)
    assert list(host.halves()) == ["right_half", "a", "b"] and HALF + "left_half" not in host.dock._zones
    assert host.dock.titles(HALF + "a") == ["A"] and host.dock.titles(HALF + "b") == ["B"]
    assert not old_strip.get("visible")  # the old half's strip is gone from above the new split
    assert _slot(host, "a").get("layout_width") > 0 and _slot(host, "b").get("layout_x") > _slot(host, "a").get("layout_x")


def test_the_spec_handle_between_halves_resizes_the_column_and_moves_the_next_half():
    app, view = _view()
    host = view.dock_host("dock")
    left, right = _slot(host, "left_half"), _slot(host, "right_half")
    handle = view.node("editor.split.0")
    x, y = _centre(handle)
    right_x = right.get("layout_x")
    app.window.simulate("pointer_down", handle, x=8, y=8)
    app.window.simulate("pointer_move", x=x + 40, y=y)
    app.window.simulate("pointer_up", x=x + 40, y=y)
    app.window.advance(16)
    assert left.get("layout_width") == 340.0 and view.node("left_half").get("layout_width") == 340.0
    assert right.get("layout_x") == right_x + 40
    assert host.layout()["splits"] == {"left_half": 340.0}


def test_a_reload_that_removes_a_half_sends_the_panels_dropped_in_it_back_to_their_zones():
    app, view = _view()
    host = view.dock_host("dock")
    _join(app, host, "right_half", "Outline")
    _split(app, host, "right_half", "bottom", "Files")

    def change(spec):
        spec["children"][0]["children"][2]["children"].pop(1)  # right_half goes
    _reload(view, change)
    app.window.advance(32)
    assert "right_half" not in host.halves() and not host._made_halves and not host._made_splits
    assert set(host.layout()["zones"]["left"]["panels"]) == {"Files", "Outline"}
    assert view.node("outline").get("layout_width") > 0 and host.half_of("outline") is None
