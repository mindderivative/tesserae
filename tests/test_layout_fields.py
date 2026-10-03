"""0.4.0 (#86): where children go and how a node takes room.

`align_content` (nine positions), `spread`, `flex`, `align_self`, `align_wrapped`, `align_tracks` and
`align_cells` replace the engine's `align_items`, `justify_content`, `flex_grow`, `flex_shrink`, `flex_basis`,
`justify_items` and `justify_self`; `tesserae.spec.layout` turns one into the other. These tests check the
translation, that the engine's names are refused with what replaces them, and the layout it makes.
"""

import pytest

from tesserae import App, View
from tesserae.spec.layout import POSITIONS, LayoutError, engine_style

SEED = (0x67, 0x50, 0xA4, 0xFF)
EDGE = {"left": "start", "top": "start", "center": "center", "right": "end", "bottom": "end"}


@pytest.mark.parametrize("position", sorted(POSITIONS))
@pytest.mark.parametrize("direction", ["horizontal", "vertical"])
def test_each_position_is_one_pair_of_the_engines_values(position, direction):
    horizontal, vertical = POSITIONS[position]
    out = engine_style("n", {"flex_direction": direction, "align_content": position})
    main, cross = (horizontal, vertical) if direction == "horizontal" else (vertical, horizontal)
    assert (out["justify_content"], out["align_items"]) == (EDGE[main], EDGE[cross])


def test_a_style_with_no_alignment_leaves_the_engines_defaults():
    out = engine_style("n", {"width": 10})
    assert "align_items" not in out and "justify_content" not in out


def test_spread_shares_the_room_along_the_layout():
    for spread, engine in (("between", "space_between"), ("around", "space_around"), ("evenly", "space_evenly")):
        out = engine_style("n", {"align_content": "bottom", "spread": spread})
        assert out["justify_content"] == engine and out["align_items"] == "end"
    assert engine_style("n", {"align_content": "center", "spread": "none"})["justify_content"] == "center"


def test_a_node_is_not_squeezed_or_grown_unless_it_says_so():
    out = engine_style("n", {})
    assert (out["flex_grow"], out["flex_shrink"]) == (0.0, 0.0)
    assert engine_style("n", {"flex": "none"})["flex_shrink"] == 0.0


def test_expanding_along_the_parents_layout_takes_the_room_left():
    out = engine_style("n", {"flex": "expand_horizontal", "width": 50}, ("horizontal", "flex"))
    assert (out["flex_grow"], out["flex_shrink"], out["width"]) == (1.0, 1.0, 50)  # from its own size
    out = engine_style("n", {"flex": "expand_vertical"}, ("vertical", "flex"))
    assert (out["flex_grow"], out["flex_shrink"]) == (1.0, 1.0)


def test_expanding_across_the_parents_layout_stretches_and_drops_the_size():
    out = engine_style("n", {"flex": "expand_vertical", "height": 30, "width": 50}, ("horizontal", "flex"))
    assert out["align_self"] == "stretch" and "height" not in out and out["width"] == 50 and out["_fill_y"]
    assert (out["flex_grow"], out["flex_shrink"]) == (0.0, 0.0)
    out = engine_style("n", {"flex": "expand_horizontal", "width": 50}, ("vertical", "flex"))
    assert out["align_self"] == "stretch" and "width" not in out and out["_fill_x"]


def test_fill_expands_both_ways():
    out = engine_style("n", {"flex": "fill", "width": 50, "height": 30}, ("horizontal", "flex"))
    assert (out["flex_grow"], out["align_self"], "width" in out, "height" in out) == (1.0, "stretch", True, False)


def test_align_self_places_a_child_across_its_parents_layout():
    assert engine_style("n", {"align_self": "bottom_right"}, ("horizontal", "flex"))["align_self"] == "end"
    assert engine_style("n", {"align_self": "bottom_right"}, ("vertical", "flex"))["align_self"] == "end"
    assert engine_style("n", {"align_self": "top_right"}, ("horizontal", "flex"))["align_self"] == "start"
    assert engine_style("n", {"align_self": "top_right"}, ("vertical", "flex"))["align_self"] == "end"
    out = engine_style("n", {"align_self": "bottom_left"}, ("horizontal", "grid"))
    assert (out["justify_self"], out["align_self"]) == ("start", "end")


def test_a_grid_has_cells_and_tracks_and_a_wrapping_node_has_lines():
    grid = {"display": "grid"}
    out = engine_style("g", {**grid, "align_cells": "bottom_right", "align_tracks": "between"})
    assert (out["justify_items"], out["align_items"]) == ("end", "end")
    assert out["justify_content"] == out["align_content"] == "space_between"
    out = engine_style("w", {"flex_wrap": "wrap", "align_wrapped": "evenly"})
    assert out["align_content"] == "space_evenly"


@pytest.mark.parametrize("style, message", [
    ({"align_wrapped": "start"}, "align_wrapped is for a node with flex_wrap: wrap"),
    ({"align_tracks": "start"}, "are for display: grid"),
    ({"align_cells": "center"}, "are for display: grid"),
    ({"display": "grid", "align_content": "center"}, "a grid places its items with style.align_cells"),
    ({"display": "grid", "spread": "between"}, "a grid places its items with style.align_cells"),
])
def test_a_field_on_a_node_that_cant_use_it_is_one_error(style, message):
    with pytest.raises(LayoutError, match=message):
        engine_style("n", style)


@pytest.mark.parametrize("field, value, shown", [
    ("align_content", "middle", "top_left"), ("spread", "wide", "between"), ("flex", "grow", "expand_horizontal"),
    ("align_self", "up", "top_left"),
])
def test_a_wrong_value_names_what_is_allowed(field, value, shown):
    with pytest.raises(LayoutError, match=rf"style\.{field} must be one of .*{shown}.*got '{value}'"):
        engine_style("n", {field: value})


@pytest.mark.parametrize("old, new", [
    ("align_items", "align_content"), ("justify_content", "align_content"), ("justify_self", "align_self"),
    ("justify_items", "align_cells"), ("flex_grow", "flex"), ("flex_shrink", "flex"), ("flex_basis", "flex"),
])
def test_the_engines_names_are_refused_with_what_replaces_them(old, new):
    spec = {"id": "r", "kind": "Container", "style": {old: 1}}
    with pytest.raises(ValueError, match=rf'widget "r": style\.{old} is now {new}'):
        View(spec, theme_seed=SEED)


# -- the layout they make ---------------------------------------------------------------------

def _laid_out(spec):
    app = App(width=600, height=400)
    view = View(spec, window=app.window, theme_seed=SEED)
    app.window.root.add_child(view.root)
    app.window.advance(16)
    return view


def _box(view, node_id):
    node = view.node(node_id)
    return tuple(node.get(k) for k in ("layout_x", "layout_y", "layout_width", "layout_height"))


def _rect(node_id, **style):
    return {"id": node_id, "kind": "Rect", "style": {"width": 40, "height": 20, "background": "#FF0000", **style}}


def _container(children, **style):
    return {"id": "r", "kind": "Container", "style": {"width": 300, "height": 100, **style}, "children": children}


@pytest.mark.parametrize("direction", ["horizontal", "vertical"])
@pytest.mark.parametrize("position, x, y", [
    ("top_left", 0, 0), ("top", 130, 0), ("top_right", 260, 0), ("left", 0, 40), ("center", 130, 40),
    ("right", 260, 40), ("bottom_left", 0, 80), ("bottom", 130, 80), ("bottom_right", 260, 80),
])
def test_a_child_goes_where_the_position_says(direction, position, x, y):
    view = _laid_out(_container([_rect("a")], flex_direction=direction, align_content=position))
    assert _box(view, "a")[:2] == (x, y)


def test_spread_puts_the_room_between_the_children():
    view = _laid_out(_container([_rect("a"), _rect("b"), _rect("c")], spread="between"))
    assert [_box(view, n)[0] for n in "abc"] == [0, 130, 260]


def test_a_node_is_not_squeezed_by_a_crowded_parent():
    view = _laid_out(_container([_rect("a", width=200), _rect("b", width=200)]))
    assert (_box(view, "a")[2], _box(view, "b")[2]) == (200, 200)  # the engine's default would squeeze to 150


def test_expand_horizontal_takes_what_the_others_leave():
    view = _laid_out(_container([_rect("a", width=100), _rect("b", flex="expand_horizontal"),
                                 _rect("c", flex="expand_horizontal")]))
    assert [_box(view, n)[2] for n in "abc"] == [100, 100, 100]  # the 200 left, shared; each starts from its own 40


def test_expand_vertical_in_a_row_fills_its_height_and_fill_does_both():
    view = _laid_out(_container([_rect("a", flex="expand_vertical"), _rect("b", flex="fill")]))
    assert _box(view, "a")[3] == 100 and _box(view, "b")[3] == 100 and _box(view, "b")[2] == 260


def test_a_text_that_expands_across_keeps_its_text_width_as_the_least():
    text = {"id": "t", "kind": "Text", "text": {"content": "Hello", "typography_role": "body_large"},
            "style": {"foreground": "#FFFFFF", "flex": "expand_horizontal"}}
    view = _laid_out(_container([text], flex_direction="vertical"))
    assert _box(view, "t")[2] == 300
    view = _laid_out(_container([text], flex_direction="vertical", width="auto"))
    assert _box(view, "t")[2] > 0  # not 0: a percentage of a parent with no width


def test_a_childs_own_flex_follows_its_parents_direction_when_that_is_restyled():
    spec = _container([_rect("a", width=100, height=100, flex="expand_horizontal")], flex_direction="horizontal")
    view = _laid_out(spec)
    assert _box(view, "a")[2] == 300 and _box(view, "a")[3] == 100  # along the row: wider
    view.set_stylesheet({"styles": [{"id": "r", "style": {"flex_direction": "vertical"}}]})
    view.window.advance(16)
    assert _box(view, "a")[2] == 300 and _box(view, "a")[3] == 100  # across the column: stretched to the width


def test_a_grid_places_its_items_in_cells_and_tracks():
    cell = _rect("a", width=20, height=20)
    spec = _container([cell], display="grid", grid_template_columns="100", grid_template_rows="100",
                      align_cells="bottom_right")
    view = _laid_out(spec)
    assert _box(view, "a")[:2] == (80, 80)


def test_the_shells_parts_take_the_new_names():
    from tesserae.spec.build import style_props

    props = style_props({"align_content": "center", "flex": "none"}, None)
    assert (props["justify_content"], props["align_items"], props["flex_grow"], props["flex_shrink"]) == ("center", "center", 0.0, 0.0)
    with pytest.raises(ValueError, match="style.align_items is now align_content"):
        style_props({"align_items": "center"}, None)
