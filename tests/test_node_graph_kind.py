"""M60 (#7): a declarative node graph. `NodeGraph` and `GraphNode` are
YAML kinds the compiler builds with `tesserae.widgets`' `node_graph` and
`graph_node`, so they pan, zoom, drag and draw edges as the widgets do.
A GraphNode takes `label`, `x` and `y` (its content goes in its body);
a NodeGraph takes `edges: [{from, to}]`. A reload patches nodes by id:
a place the user dragged a node to stays unless the file moves it.
"""

import pytest

import tesserae
from tesserae import Theme, View
from tesserae.spec.build import SpecBuildError

SEED = (0x67, 0x50, 0xA4, 0xFF)


class VM(tesserae.ViewModel):
    def __init__(self, view):
        self.moves = []
        super().__init__(view)

    def moved(self):
        self.moves.append(1)


def _node(node_id, x, y, label=None, **extra):
    return {"id": node_id, "kind": "GraphNode", "label": label or node_id.upper(), "x": x, "y": y,
            "style": {"width": 120, "height": 80}, **extra}


def _graph(*nodes, edges=None):
    return {"id": "root", "kind": "Container", "children": [
        {"id": "g", "kind": "NodeGraph", "style": {"width": 600, "height": 400}, "children": list(nodes),
         **({"edges": edges} if edges is not None else {})}]}


def _view(spec):
    view = View(spec, theme_seed=SEED)
    vm = VM(view)
    view.window.advance(16)
    return view, vm


def test_a_graph_builds_its_nodes_edges_and_content():
    body = {"id": "note", "kind": "Text", "text": {"content": "hi", "typography_role": "body_small"},
            "style": {"foreground": "on_surface"}}
    view, _ = _view(_graph(_node("a", 10, 20, children=[body]), _node("b", 300, 40), edges=[{"from": "a", "to": "b"}]))
    graph, a, b = view.control("g"), view.control("a"), view.control("b")
    assert graph.graph_nodes == [a, b] and a.position.get() == (10.0, 20.0) and a.part("label").get("text") == "A"
    assert len(graph.edges) == 1 and graph.edges[0][:2] == (a, b)
    assert view.node("note").parent() == a.part("body")  # its content is in its body
    assert a.node.parent() == graph.content and view.node("g") == graph.node
    assert graph.node.parent() == view.root and graph.node.parent() != view.window.root  # in the view, not loose


def test_the_widgets_behaviour_comes_with_it():
    view, vm = _view(_graph(_node("a", 10, 20, handlers={"on_change": "moved"}), _node("b", 300, 40)))
    a = view.control("a")
    a.node.focus()
    view.window.simulate("key_down", key="arrow_right")
    assert a.position.get() == (18.0, 20.0) and vm.moves == [1]  # on_change hears the user's moves
    graph = view.control("g")
    view.window.simulate("wheel", x=50, y=50, delta_y=-1.0)
    assert graph.zoom.get() > 1.0  # it zooms, as the widget does


def test_a_reload_patches_nodes_by_id_and_keeps_the_users_moves():
    spec = _graph(_node("a", 10, 20), _node("b", 300, 40), edges=[{"from": "a", "to": "b"}])
    view, _ = _view(spec)
    a, b = view.control("a"), view.control("b")
    a.position.set((50.0, 60.0))  # the user dragged it
    view.reconcile(_graph(_node("a", 10, 20, label="Alpha"), _node("b", 310, 40), edges=[{"from": "a", "to": "b"}]))
    assert view.control("a") is a and a.part("label").get("text") == "Alpha"
    assert a.position.get() == (50.0, 60.0)  # the file didn't move it: the user's place stays
    assert view.control("b") is b and b.position.get() == (310.0, 40.0)  # the file moved it


def test_a_reload_adds_and_removes_nodes_and_redraws_edges():
    view, _ = _view(_graph(_node("a", 10, 20), _node("b", 300, 40), edges=[{"from": "a", "to": "b"}]))
    graph, a, b = view.control("g"), view.control("a"), view.control("b")
    view.reconcile(_graph(_node("a", 10, 20), _node("c", 200, 200), edges=[{"from": "c", "to": "a"}]))
    c = view.control("c")
    assert graph.graph_nodes == [a, c] and c.node.parent() == graph.content
    assert [(x, y) for x, y, _ in graph.edges] == [(c, a)]
    assert len(graph._edges_layer.children()) == 1  # the old edge's path is gone, not left drawn
    with pytest.raises(ValueError):
        view.control("b")
    with pytest.raises(ValueError):
        b.node.get("x")  # its node is gone
    assert view.control("g") is graph  # the graph itself was patched, not rebuilt


def test_a_new_size_rebuilds_a_node():
    view, _ = _view(_graph(_node("a", 10, 20)))
    a = view.control("a")
    view.reconcile(_graph({**_node("a", 10, 20), "style": {"width": 200, "height": 80}}))
    assert view.control("a") is not a and view.control("a").size == (200.0, 80.0)
    assert view.control("g").graph_nodes == [view.control("a")]


def test_it_follows_the_views_theme():
    view, _ = _view(_graph(_node("a", 10, 20)))
    a = view.control("a")
    view.set_theme(theme_seed=SEED, dark=True)
    dark = Theme.resolve(theme_seed=SEED, dark=True)
    assert a.node.get("fill") == dark.role("surface_container_high")
    assert view.control("g").node.get("fill") == dark.role("surface_container_low")


@pytest.mark.parametrize("spec, message", [
    ({"id": "root", "kind": "Container", "children": [_node("a", 0, 0)]}, "a GraphNode belongs inside a NodeGraph"),
    (_graph({"id": "t", "kind": "Rect", "style": {"width": 1, "height": 1, "background": "#000000"}}),
     "a NodeGraph's children are GraphNodes"),
    (_graph(_node("a", 0, 0), edges=[{"from": "a", "to": "zz"}]), "edges\\[0\\] names no GraphNode 'zz'"),
    (_graph(_node("a", 0, 0), edges=[{"from": "a"}]), "edges\\[0\\] is \\{from: id, to: id\\}"),
    (_graph({**_node("a", 0, 0), "style": {}}), "a GraphNode needs a numeric style width and height"),
])
def test_mistakes_are_named(spec, message):
    with pytest.raises(SpecBuildError, match=message):
        View(spec, theme_seed=SEED)


def test_a_reload_updates_a_nodes_content_in_its_body():
    text = lambda i, content: {"id": i, "kind": "Text", "text": {"content": content, "typography_role": "body_small"},
                               "style": {"foreground": "on_surface"}}
    view, _ = _view(_graph(_node("a", 10, 20, children=[text("t1", "one")])))
    body = view.control("a").part("body")
    view.reconcile(_graph(_node("a", 10, 20, children=[text("t1", "one"), text("t2", "two")])))
    assert view.node("t2").parent() == body and body.children() == [view.node("t1"), view.node("t2")]
