"""#202: a node graph that snaps to a grid, ends its edges in arrows, fits its nodes into view, and chooses one node."""

import pytest

from tesserae import App, ViewModel, tokens


class VM(ViewModel):
    views = "main"


def opened(tmp_path, props="", nodes=None):
    (tmp_path / "Views").mkdir(exist_ok=True)
    lines = "\n    ".join(props.split(", ")) if props else ""
    nodes = nodes or [("a", 40, 40), ("b", 300, 120)]
    kids = "\n".join(f"      - {{widget: GraphNode, name: {n}, label: {n.upper()}, x: {x}, y: {y}, style: {{width: 120, height: 80}}}}" for n, x, y in nodes)
    (tmp_path / "Views" / "Main_View.yaml").write_text(f"""name: main
widget: Container
style: {{width: 600, height: 500, align_content: top_left}}
children:
  - widget: NodeGraph
    name: g
    edges: [{{from: root.g.a, to: root.g.b}}]
    {lines}
    style: {{width: 500, height: 300}}
    children:
{kids}
""")
    app = App(root=tmp_path, width=600, height=500)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    for _ in range(8):
        view.window.advance(16)
    return view


def graph(view):
    return view._built.controls["root.g"]


def gnode(view, name):
    return view._built.controls[f"root.g.{name}"]


def role(view, name):
    return (view._scheme or tokens.BASELINE)[name]


def test_a_node_the_user_moves_lands_on_the_grid(tmp_path):
    view = opened(tmp_path, "snap: 20")
    assert graph(view).snap.get() == 20.0
    a = gnode(view, "a")
    a.node.focus()
    view.window.simulate("key_down", key="arrow_right")  # a key steps one grid square
    assert a.position.get() == (60.0, 40.0)
    view.window.simulate("key_down", key="arrow_down")
    assert a.position.get() == (60.0, 60.0)


def test_without_snap_a_move_is_free(tmp_path):
    view = opened(tmp_path)
    a = gnode(view, "a")
    a.node.focus()
    view.window.simulate("key_down", key="arrow_right")
    assert a.position.get() == (48.0, 40.0)


def test_arrows_add_an_arrowhead_to_each_edge(tmp_path):
    view = opened(tmp_path)
    plain = graph(view).edges[0][2].get("data")
    assert "L" not in plain
    (tmp_path / "w").mkdir()
    arrowed = opened(tmp_path / "w", "arrows: true")
    data = graph(arrowed).edges[0][2].get("data")
    assert data.count("M") == 2 and " L" in data


def test_fit_pans_and_zooms_so_every_node_shows(tmp_path):
    view = opened(tmp_path, "fit: true", nodes=[("a", 0, 0), ("b", 1400, 900)])
    for _ in range(4):
        view.window.advance(16)
    g = graph(view)
    zoom = g.zoom.get()
    assert zoom < 0.5
    ox, oy = g.offset.get()
    b = gnode(view, "b")
    right, bottom = (b.position.get()[0] + b.size[0]) * zoom + ox, (b.position.get()[1] + b.size[1]) * zoom + oy
    assert 0 <= ox and 0 <= oy and right <= 500 and bottom <= 300


def test_fit_never_zooms_in_past_actual_size(tmp_path):
    view = opened(tmp_path, "fit: true")
    for _ in range(4):
        view.window.advance(16)
    assert graph(view).zoom.get() == 1.0


def test_no_fit_leaves_the_view_where_it_is(tmp_path):
    view = opened(tmp_path, nodes=[("a", 0, 0), ("b", 1400, 900)])
    assert graph(view).zoom.get() == 1.0 and graph(view).offset.get() == (0.0, 0.0)


def test_pressing_a_node_chooses_it_with_a_primary_border_and_pressing_the_background_chooses_nothing(tmp_path):
    view = opened(tmp_path)
    a, b = gnode(view, "a"), gnode(view, "b")
    view.window.simulate("pointer_down", x=a.node.get("layout_x") + 20, y=a.node.get("layout_y") + 40)
    view.window.simulate("pointer_up", x=a.node.get("layout_x") + 20, y=a.node.get("layout_y") + 40)
    assert graph(view).selected.get() is a and a.node.get("stroke_width") == 2.0 and a.node.get("stroke_color") == role(view, "primary")
    assert a.node.get("selected") is True and b.node.get("stroke_width") == 1.0 and b.node.get("selected") is False
    view.window.simulate("pointer_down", x=view.node("root.g").get("layout_x") + 450, y=view.node("root.g").get("layout_y") + 250)
    view.window.simulate("pointer_up", x=view.node("root.g").get("layout_x") + 450, y=view.node("root.g").get("layout_y") + 250)
    assert graph(view).selected.get() is None and a.node.get("stroke_width") == 1.0


def test_a_node_dragged_to_a_place_between_grid_lines_lands_on_the_nearest_one(tmp_path):
    view = opened(tmp_path, "snap: 20")
    a = gnode(view, "a")
    x, y = a.node.get("layout_x") + 20, a.node.get("layout_y") + 40
    view.window.simulate("pointer_down", x=x, y=y)
    view.window.simulate("pointer_move", x=x + 13, y=y + 7)
    view.window.simulate("pointer_up", x=x + 13, y=y + 7)
    assert a.position.get() == (60.0, 40.0)  # 53 is nearer 60 than 40; 47 is nearer 40 than 60
