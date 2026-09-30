"""M74: CSS Grid in a view's style, on `tre` 0.4.2 (`tre` #23) --
`display: grid`, track templates, auto tracks and flow, placement, row and
column gaps, and grid alignment. Each lays out exactly as the same tree
built with `tre` directly. As M71's keys: set only when a style gives
them, reset when it drops them (a dropped row or column gap goes back to
the style's `gap`), in stylesheets too, and a ScrollView's content can be
a grid.
"""

import pytest
import tre
import yaml

from tesserae import View
from tesserae.spec.build import SpecBuildError

SEED = (0x67, 0x50, 0xA4, 0xFF)
BOX = ("layout_x", "layout_y", "layout_width", "layout_height")


def _cell(node_id, **style):
    return {"id": node_id, "kind": "Rect", "style": {"background": "#000000", **style}}


def _cells(n, **style):
    return [_cell(f"c{i}", **style) for i in range(n)]


def _view(grid_style, children):
    spec = {"id": "root", "kind": "Container", "style": {"width": 400, "height": 300},
            "children": [{"id": "g", "kind": "Container", "style": grid_style, "children": children}]}
    view = View(spec, theme_seed=SEED)
    view.window.advance(16)
    return view


def _tre_boxes(grid_style, children):
    window = tre.Window(width=400, height=300)
    window.root.set(padding=0.0, gap=0.0, align_items="stretch")
    root = window.create("box", width=400.0, height=300.0)
    window.root.add_child(root)
    grid = window.create("box", **grid_style)
    root.add_child(grid)
    nodes = []
    for child in children:
        node = window.create("box", **{k: v for k, v in child["style"].items() if k != "background"})
        grid.add_child(node)
        nodes.append(node)
    window.advance(16)
    return [tuple(n.get(k) for k in BOX) for n in nodes]


def _boxes(view, children):
    return [tuple(view.node(c["id"]).get(k) for k in BOX) for c in children]


GRID = {"width": 300.0, "height": 200.0, "display": "grid"}
CASES = {
    "columns_and_fr": ({**GRID, "grid_template_columns": "100 1fr"}, _cells(4)),
    "a_list_of_tracks": ({**GRID, "grid_template_columns": [80, "1fr", "2fr"]}, _cells(3)),
    "repeat_and_minmax": ({**GRID, "grid_template_columns": "repeat(3, minmax(50, 1fr))", "grid_template_rows": "40 auto"},
                          _cells(5)),
    "auto_rows": ({**GRID, "grid_template_columns": "1fr 1fr", "grid_auto_rows": "30"}, _cells(6)),
    "column_flow": ({**GRID, "grid_template_rows": "50 50", "grid_auto_flow": "column", "grid_auto_columns": "70"},
                    _cells(5)),
    "dense_flow": ({**GRID, "grid_template_columns": "repeat(3, 1fr)", "grid_auto_flow": "row dense"},
                   [_cell("wide", grid_column="span 2"), _cell("x"), _cell("y"), _cell("z", grid_column="span 3"), _cell("w")]),
    "placement": ({**GRID, "grid_template_columns": "repeat(4, 1fr)", "grid_template_rows": "repeat(3, 50)"},
                  [_cell("a", grid_column="1 / 3", grid_row=2), _cell("b", grid_column=-2), _cell("c", grid_row="span 2")]),
    "gaps": ({**GRID, "grid_template_columns": "1fr 1fr", "row_gap": 20.0, "column_gap": 6.0}, _cells(4)),
    "gap_with_a_row_gap_winning": ({**GRID, "grid_template_columns": "1fr 1fr", "gap": 10.0, "row_gap": 30.0}, _cells(4)),
    "alignment": ({**GRID, "grid_template_columns": "100 100", "grid_template_rows": "60 60", "justify_items": "center",
                   "align_content": "center"},
                  [_cell("a", width=40.0, height=20.0), _cell("b", width=40.0, height=20.0, justify_self="end"),
                   _cell("c", width=40.0, height=20.0)]),
}


@pytest.mark.parametrize("case", sorted(CASES))
def test_each_grid_lays_out_as_tre_does(case):
    grid, children = CASES[case]
    assert _boxes(_view(grid, children), children) == _tre_boxes(grid, children)


def test_a_grid_really_is_one():
    grid, children = CASES["columns_and_fr"]
    view = _view(grid, children)
    c = [view.node(f"c{i}") for i in range(4)]
    assert [n.get("layout_width") for n in c] == [100.0, 200.0, 100.0, 200.0]
    assert c[2].get("layout_x") == c[0].get("layout_x") and c[2].get("layout_y") > c[0].get("layout_y")


def _spec(grid_extra, **child_extra):
    return {"id": "root", "kind": "Container", "style": {"width": 400, "height": 300},
            "children": [{"id": "g", "kind": "Container", "style": {"width": 300, "height": 200, **grid_extra},
                          "children": [_cell("a", **child_extra), _cell("b")]}]}


def test_reconcile_sets_and_resets_them():
    view = View(_spec({"display": "grid", "grid_template_columns": "1fr 1fr", "gap": 10, "row_gap": 30,
                       "justify_items": "center", "align_content": "end"}, grid_column="span 2"), theme_seed=SEED)
    g, a = view.node("g"), view.node("a")
    view.reconcile(_spec({"display": "grid", "grid_template_columns": "1fr 1fr", "gap": 10}))
    assert g.get("row_gap") == 10.0 and g.get("column_gap") == 10.0  # back to `gap`, not 0
    assert a.get("grid_column") == "auto" and g.get("justify_items") == "stretch" and g.get("align_content") == "stretch"
    view.reconcile(_spec({}))
    assert (g.get("display"), g.get("grid_template_columns"), g.get("row_gap")) == ("flex", "", 0.0)


def test_python_placement_survives_a_re_theme():
    view = View(_spec({"display": "grid", "grid_template_columns": "1fr 1fr"}), theme_seed=SEED)
    view.node("b").set(grid_column="1 / 3")
    view.set_theme(theme_seed=SEED, dark=True)
    assert view.node("b").get("grid_column") == "1 / 3"


def test_a_stylesheet_can_make_a_grid():
    view = View(_spec({}), theme_seed=SEED, stylesheet_spec={
        "styles": [{"kind": "Container", "style": {"display": "grid", "grid_template_columns": "100 100"}}]})
    view.window.advance(16)
    assert view.node("g").get("display") == "grid" and view.node("b").get("layout_x") == 100.0


def test_a_scrolling_grid_is_its_content():
    scroll = {"id": "list", "kind": "ScrollView",
              "style": {"width": 200, "height": 100, "display": "grid", "grid_template_columns": "1fr 1fr",
                        "row_gap": 4, "grid_column": "1 / 3"},
              "children": _cells(8, height=40.0)}
    view = View({"id": "root", "kind": "Container", "style": {"width": 400, "height": 300, "display": "grid",
                                                               "grid_template_columns": "200 200"},
                 "children": [scroll]}, theme_seed=SEED)
    view.window.advance(16)
    content, outer = view.node("list"), view._built.outer["list"]
    assert content.get("display") == "grid" and content.get("row_gap") == 4.0
    assert outer.get("grid_column") == "1 / 3" and outer.get("display") == "flex"  # placement on the scroll view
    assert view.node("c1").get("layout_x") == 100.0 and content.get("layout_height") == 4 * 40 + 3 * 4


def test_a_link_box_and_a_control_take_grid_placement():
    link = {"id": "go", "kind": "Link", "text": {"content": "Go", "font_family": "Roboto", "font_size": 14},
            "style": {"foreground": "#0000FF", "grid_column": 2, "justify_self": "end"}}
    switch = {"id": "s", "kind": "Switch", "style": {"grid_row": 2}}
    view = View({"id": "root", "kind": "Container", "style": {"width": 300, "display": "grid",
                                                               "grid_template_columns": "1fr 1fr"},
                 "children": [link, switch]}, theme_seed=SEED)
    box = view._built.outer["go"]
    assert (box.get("grid_column"), box.get("justify_self")) == ("2", "end")
    assert view.control("s").node.get("grid_row") == "2"


@pytest.mark.parametrize("style, message", [
    ({"display": "table"}, r'widget "g": node property `display` must be one of: flex, grid'),
    ({"grid_template_columns": "wide 1fr"}, r'widget "g": node property `grid_template_columns`: "wide" isn\'t a track size'),
    ({"row_gap": -4}, r'widget "g": node property `row_gap` must be a non-negative number'),
])
def test_tres_grid_errors_name_the_widget(style, message):
    with pytest.raises(SpecBuildError, match=message):
        View(_spec(style))


def test_a_grid_written_in_yaml():
    text = """
id: root
kind: Container
style: {width: 300, height: 120, display: grid, grid_template_columns: "80 1fr", column_gap: 8}
children:
  - {id: label, kind: Text, text: {content: "Name", font_family: Roboto, font_size: 14}, style: {foreground: "#000000"}}
  - {id: field, kind: Rect, style: {height: 24, background: "#EEEEEE"}}
"""
    view = View(yaml.safe_load(text), theme_seed=SEED)
    view.window.advance(16)
    assert view.node("field").get("layout_x") == 88.0 and view.node("field").get("layout_width") == 212.0


def test_a_bare_number_is_one_track():
    """How YAML writes one track (`grid_auto_rows: 96`). `tre` takes it as a
    one-track list since 0.4.3 (`tre` #27, M79); M74's compiler turned it
    into text itself before."""
    view = _view({**GRID, "grid_template_columns": 100, "grid_auto_rows": 30.0}, _cells(2))
    assert view.node("g").get("grid_template_columns") == "100" and view.node("g").get("grid_auto_rows") == "30"
    assert view.node("c1").get("layout_y") == 30.0 and view.node("c0").get("layout_width") == 100.0
    assert _view({**GRID, "grid_template_columns": "100 100", "grid_column": 2}, _cells(1)).node("g").get(
        "grid_column") == "2"  # not a track list: passed as given
