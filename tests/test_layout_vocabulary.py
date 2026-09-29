"""M71 (#21): the rest of `tre`'s flexbox in a view's style -- `flex_wrap`,
`align_self`, `min_`/`max_width`/`height`, `aspect_ratio`, `position`
with `x`/`y`, `z_index` and `clip_children`. Each lays out exactly as the
same tree built with `tre` directly. A style sets one only when it gives
it, and a patch resets one only when the style gave it before, so what
Python code sets on a spec-built node (a widget's `x`/`y`) survives a
re-theme. And `tre`'s layout errors name the widget.
"""

import pytest
import tre

from tesserae import View, ViewModel
from tesserae.spec.build import SpecBuildError

SEED = (0x67, 0x50, 0xA4, 0xFF)
BOX = ("layout_x", "layout_y", "layout_width", "layout_height")


def _rect(node_id, **style):
    return {"id": node_id, "kind": "Rect", "style": {"background": "#000000", **style}}


def _view(parent_style, *children):
    spec = {"id": "root", "kind": "Container", "style": {"width": 300, "height": 200},
            "children": [{"id": "p", "kind": "Container", "style": parent_style, "children": list(children)}]}
    view = View(spec, theme_seed=SEED)
    view.window.advance(16)
    return view


def _tre_boxes(parent_style, *children):
    """The same tree built with `tre` directly: the reference layout."""
    window = tre.Window(width=300, height=200)
    window.root.set(padding=0.0, gap=0.0, align_items="stretch")
    root = window.create("box", width=300.0, height=200.0)
    window.root.add_child(root)
    parent = window.create("box", **parent_style)
    root.add_child(parent)
    nodes = []
    for child in children:
        style = {k: v for k, v in child["style"].items() if k != "background"}
        node = window.create("box", **style)
        parent.add_child(node)
        nodes.append(node)
    window.advance(16)
    return [tuple(n.get(k) for k in BOX) for n in nodes]


def _boxes(view, *ids):
    return [tuple(view.node(i).get(k) for k in BOX) for i in ids]


CASES = {
    "flex_wrap": ({"width": 100.0, "flex_wrap": "wrap"},
                  [_rect("a", width=40.0, height=20.0), _rect("b", width=40.0, height=20.0), _rect("c", width=40.0, height=20.0)]),
    "align_self": ({"width": 200.0, "height": 100.0, "flex_direction": "vertical", "align_items": "flex_start"},
                   [_rect("a", width=40.0, height=20.0, align_self="center"), _rect("b", width=40.0, height=20.0, align_self="flex_end")]),
    "min_and_max_width": ({"width": 200.0, "height": 40.0},
                          [_rect("a", height=20.0, flex_grow=1.0, max_width=50.0), _rect("b", width=10.0, height=20.0, min_width=70.0)]),
    "min_and_max_height": ({"width": 200.0, "height": 100.0, "flex_direction": "vertical"},
                           [_rect("a", width=20.0, flex_grow=1.0, max_height=30.0), _rect("b", width=20.0, height=5.0, min_height=25.0)]),
    "aspect_ratio": ({"width": 200.0, "height": 100.0, "align_items": "flex_start"},
                     [_rect("a", width=80.0, aspect_ratio=2.0)]),
    "position": ({"width": 200.0, "height": 100.0},
                 [_rect("a", width=40.0, height=20.0), _rect("b", width=30.0, height=30.0, position="absolute", x=50.0, y=10.0),
                  _rect("c", width=10.0, height=10.0, position="absolute", x="50%", y="50%")]),
}


@pytest.mark.parametrize("case", sorted(CASES))
def test_each_key_lays_out_as_tre_does(case):
    parent, children = CASES[case]
    view = _view(parent, *children)
    assert _boxes(view, *(c["id"] for c in children)) == _tre_boxes(parent, *children)


def test_wrapping_really_wraps():
    parent, children = CASES["flex_wrap"]
    view = _view(parent, *children)
    a, b, c = (view.node(i) for i in "abc")
    assert a.get("layout_y") == b.get("layout_y") == 0.0 and b.get("layout_x") == 40.0
    assert c.get("layout_x") == 0.0 and c.get("layout_y") > 0.0  # the third starts a second row


def test_z_index_and_clip_children_reach_the_node():
    view = _view({"width": 100.0, "clip_children": True}, _rect("a", width=10.0, height=10.0, z_index=3))
    assert view.node("p").get("clip_children") is True and view.node("a").get("z_index") == 3


def test_a_stylesheet_can_give_them():
    spec = {"id": "root", "kind": "Container", "style": {"width": 100, "flex_wrap": "wrap"},
            "children": [_rect("a", width=60.0, height=10.0), _rect("b", width=60.0, height=10.0)]}
    view = View(spec, theme_seed=SEED, stylesheet_spec={"styles": [{"kind": "Rect", "style": {"z_index": 2}}]})
    assert view.node("a").get("z_index") == 2
    view.set_stylesheet(None)  # the stylesheet no longer gives it: reset
    assert view.node("a").get("z_index") == 0
    view.window.advance(16)
    assert view.node("b").get("layout_y") == 10.0  # the node's own style still wraps


def test_reconcile_sets_changes_and_resets_them():
    def spec(**extra):
        return {"id": "root", "kind": "Container", "style": {"width": 100, **extra},
                "children": [_rect("a", width=60.0, height=10.0), _rect("b", width=60.0, height=10.0, **({} if not extra else {"position": "absolute", "x": 5.0}))]}

    view = View(spec(), theme_seed=SEED)
    root, b = view.node("root"), view.node("b")
    view.reconcile(spec(flex_wrap="wrap"))
    assert view.node("root") == root and root.get("flex_wrap") == "wrap" and b.get("position") == "absolute"
    view.reconcile(spec())  # both gone from the spec: back to tre's defaults
    assert root.get("flex_wrap") == "no_wrap" and (b.get("position"), b.get("x")) == ("relative", "auto")


def test_what_python_sets_survives_a_re_theme():
    view = _view({"width": 200.0}, _rect("a", width=10.0, height=10.0))
    node = view.node("a")
    node.set(position="absolute", x=40.0, clip_children=True, z_index=5)  # a widget placing itself
    view.set_theme(theme_seed=SEED, dark=True)
    assert (node.get("position"), node.get("x"), node.get("clip_children"), node.get("z_index")) == ("absolute", 40.0, True, 5)


def test_a_control_takes_placement_and_resets_it():
    def spec(**style):
        return {"id": "root", "kind": "Container", "style": {"width": 200, "height": 100},
                "children": [{"id": "s", "kind": "Switch", "style": style}]}

    view = View(spec(position="absolute", x=30.0, y=10.0, z_index=2), theme_seed=SEED)
    node = view.control("s").node
    assert (node.get("position"), node.get("x"), node.get("z_index")) == ("absolute", 30.0, 2)
    view.reconcile(spec())
    assert (node.get("position"), node.get("x"), node.get("z_index")) == ("relative", "auto", 0)


def test_a_link_box_takes_its_size_limits():
    link = {"id": "go", "kind": "Link", "text": {"content": "Go", "font_family": "Roboto", "font_size": 14},
            "style": {"foreground": "#0000FF", "min_width": 80.0, "z_index": 1}}
    view = View({"id": "root", "kind": "Container", "style": {"width": 200}, "children": [link]}, theme_seed=SEED)
    box = view._built.outer["go"]
    assert (box.get("min_width"), box.get("z_index")) == (80.0, 1)


def test_a_links_text_keeps_its_own_keys_and_their_resets():
    def spec(**extra):
        link = {"id": "go", "kind": "Link", "text": {"content": "Go", "font_family": "Roboto", "font_size": 14},
                "style": {"foreground": "#0000FF", **extra}}
        return {"id": "root", "kind": "Container", "style": {"width": 200}, "children": [link]}

    view = View(spec(clip_children=True), theme_seed=SEED)
    text = view._built.nodes["go"]
    assert text.get("clip_children") is True  # not a placement key: the text, not its box
    view.reconcile(spec())
    assert text.get("clip_children") is False


class Echo(ViewModel):
    pass


@pytest.mark.parametrize("style, message", [
    ({"flex_wrap": "sideways"}, r'widget "a": node property `flex_wrap` must be one of: no_wrap, wrap'),
    ({"position": "fixed"}, r'widget "a": node property `position` must be one of: relative, absolute'),
    ({"aspect_ratio": 0}, r'widget "a": node property `aspect_ratio` must be a positive number'),
    ({"flex_direction": "diagonal"}, r'widget "a": node property `flex_direction` must be one of'),  # the old keys too
])
def test_tres_layout_errors_name_the_widget(style, message):
    with pytest.raises(SpecBuildError, match=message):
        View({"id": "root", "kind": "Container", "children": [_rect("a", width=1, height=1, **style)]})


def test_a_bad_value_from_a_stylesheet_is_named_too():
    view = View({"id": "root", "kind": "Container", "children": [_rect("a", width=1, height=1)]}, theme_seed=SEED)
    with pytest.raises(SpecBuildError, match='widget "a": node property `z_index` must be an int'):
        view.set_stylesheet({"styles": [{"kind": "Rect", "style": {"z_index": 1.5}}]})


def test_a_bad_value_in_a_reconcile_is_named_and_leaves_the_view():
    good = {"id": "root", "kind": "Container", "children": [_rect("a", width=1, height=1)]}
    view = View(good, theme_seed=SEED)
    with pytest.raises(SpecBuildError, match='widget "a": node property `z_index` must be an int'):
        view.reconcile({"id": "root", "kind": "Container", "children": [_rect("a", width=1, height=1, z_index=1.5)]})
    assert view.node("a").get("z_index") == 0
