"""#157, #158: a tree -- branches that open to show their children, and leaves; selection, the keyboard, and levels."""

import pytest

from tesserae import App, Signal, ViewModel, tokens
from tesserae.shipped import shipped_views

NODES = """[{value: docs, label: Documents, icon: folder, children: [{value: a, label: Letter}, {value: b, label: Reports, children: [{value: q, label: Q1}, {value: r, label: Q2}]}]},
        {value: pics, label: Pictures, children: [{value: p, label: Holiday}]}, {value: readme, label: Readme, icon: file}]"""


class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.open = Signal(["docs"])
        self.sel = Signal("a")


def opened(tmp_path, props=""):
    (tmp_path / "Views").mkdir(exist_ok=True)
    lines = "\n    ".join(props.split(", ")) if props else ""
    (tmp_path / "Views" / "Main_View.yaml").write_text(f"""name: main
widget: Container
style: {{flex_direction: vertical, align_content: top_left, width: 400, height: 600}}
children:
  - widget: Tree
    name: t
    nodes: {NODES}
    expanded: "{{{{ open }}}}"
    selected: "{{{{ sel }}}}"
    {lines}
""")
    app = App(root=tmp_path, width=400, height=600)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    for _ in range(8):
        view.window.advance(16)
    return view, app.bindings.viewmodel_for("main")


def role(view, name):
    return (view._scheme or tokens.BASELINE)[name]


def settle(view, n=20):
    for _ in range(n):
        view.window.advance(16)


def row(view, *path):
    """The row at `path` of values: ('docs', 'b') is Reports inside Documents."""
    base = "root.t.top"
    for value in path[:-1]:
        base += f".entry[{value}].children"
    return view.node(f"{base}.entry[{path[-1]}].row")


def test_they_are_shipped():
    assert {"Tree", "TreeNode", "TreeLevel"} <= set(shipped_views())


def test_the_tree_is_a_tree_and_its_rows_are_tree_items_at_their_levels(tmp_path):
    view, _ = opened(tmp_path)
    assert view.node("root.t").get("role") == "tree"
    assert [row(view, *p).get("role") for p in (("docs",), ("docs", "a"), ("readme",))] == ["treeitem"] * 3
    assert [row(view, *p).get("level") for p in (("docs",), ("docs", "a"), ("docs", "b"))] == [1, 2, 2]


def test_open_branches_show_their_children_one_level_in_and_closed_ones_do_not(tmp_path):
    view, _ = opened(tmp_path)
    assert row(view, "docs").get("expanded") is True and row(view, "pics").get("expanded") is False
    assert "root.t.top.entry[docs].children" in view._built.specs and "root.t.top.entry[pics].children" not in view._built.specs
    assert "root.t.top.entry[docs].children.entry[b].children" not in view._built.specs  # Reports is closed
    assert row(view, "docs", "a").get("layout_x") == row(view, "docs").get("layout_x") and row(view, "docs", "a").get("layout_y") == row(view, "docs").get("layout_y") + 56


def test_a_row_is_56_tall_indented_16_plus_24_a_level_with_the_chevron_and_the_label(tmp_path):
    view, _ = opened(tmp_path)
    top, inner = row(view, "docs"), row(view, "docs", "a")
    assert top.get("layout_height") == 56.0
    assert view.node("root.t.top.entry[pics].row.chevron").get("layout_x") == 16.0  # (a turned one reports its box from the turn)
    assert view.node("root.t.top.entry[docs].children.entry[a].row.label").get("layout_x") == 16 + 24 + 24 + 8
    assert view.node("root.t.top.entry[docs].row.label").get("layout_x") == 16 + 24 + 8 + 24 + 8  # a folder icon after the chevron
    assert view.node("root.t.top.entry[docs].row.label").get("font_size") == 16.0


def test_a_leaf_has_no_chevron_and_a_branch_has_one(tmp_path):
    view, _ = opened(tmp_path)
    assert "root.t.top.entry[docs].row.chevron" in view._built.specs and "root.t.top.entry[readme].row.chevron" not in view._built.specs
    assert "root.t.top.entry[readme].row.chevron_space" in view._built.specs


def test_the_chevron_turns_a_quarter_when_a_branch_is_open(tmp_path):
    view, _ = opened(tmp_path)
    settle(view)
    assert view.node("root.t.top.entry[docs].row.chevron").get("rotation_deg") == 90.0
    assert view.node("root.t.top.entry[pics].row.chevron").get("rotation_deg") == 0.0


def test_the_chosen_row_is_secondary_container(tmp_path):
    view, _ = opened(tmp_path)
    assert row(view, "docs", "a").get("fill") == role(view, "secondary_container") and row(view, "docs", "a").get("selected") is True
    assert row(view, "docs").get("fill")[3] == 0


def test_pressing_a_leaf_chooses_it(tmp_path):
    view, vm = opened(tmp_path)
    view.window.simulate("click", node=row(view, "readme"))
    settle(view, 30)
    assert vm.sel.get() == "readme" and vm.open.get() == ["docs"]


def test_pressing_a_branch_chooses_it_and_opens_or_closes_it(tmp_path):
    view, vm = opened(tmp_path)
    view.window.simulate("click", node=row(view, "pics"))
    settle(view, 6)
    assert vm.sel.get() == "pics" and vm.open.get() == ["docs", "pics"] and "root.t.top.entry[pics].children" in view._built.specs
    view.window.simulate("click", node=row(view, "docs"))
    settle(view, 6)
    assert vm.open.get() == ["pics"] and "root.t.top.entry[docs].children" not in view._built.specs


def test_a_nested_branch_opens_inside_its_parent_and_deeper_rows_are_deeper(tmp_path):
    view, vm = opened(tmp_path)
    view.window.simulate("click", node=row(view, "docs", "b"))
    settle(view, 6)
    assert vm.open.get() == ["docs", "b"]
    q = row(view, "docs", "b", "q")
    assert q.get("level") == 3 and q.get("layout_y") == row(view, "docs", "b").get("layout_y") + 56


def test_the_arrows_move_through_the_rows_that_show_across_levels(tmp_path):
    view, _ = opened(tmp_path)
    row(view, "docs").focus()
    settle(view, 2)
    for expected in (("docs", "a"), ("docs", "b"), ("pics",)):
        view.window.simulate("key_down", key="arrow_down")
        settle(view, 3)
        assert row(view, *expected).get("focused") is True


def test_right_opens_a_branch_and_left_closes_it(tmp_path):
    view, vm = opened(tmp_path)
    row(view, "pics").focus()
    settle(view, 2)
    view.window.simulate("key_down", key="arrow_right")
    settle(view, 6)
    assert vm.open.get() == ["docs", "pics"]
    view.window.simulate("key_down", key="arrow_left")
    settle(view, 6)
    assert vm.open.get() == ["docs"]
    view.window.simulate("key_down", key="arrow_left")  # already closed: nothing
    settle(view, 4)
    assert vm.open.get() == ["docs"]


def test_a_compact_tree_has_40_pixel_rows(tmp_path):
    view, _ = opened(tmp_path, "compact: true")
    assert row(view, "docs").get("layout_height") == 40.0 and row(view, "docs", "a").get("layout_y") == row(view, "docs").get("layout_y") + 40


def test_a_disabled_row_does_not_respond(tmp_path):
    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Main_View.yaml").write_text("""name: main
widget: Container
style: {width: 300, height: 300}
children:
  - {widget: Tree, name: t, nodes: [{value: x, label: X, disabled: true}, {value: y, label: Y}], selected: "{{ sel }}"}
""")
    app = App(root=tmp_path)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    settle(view, 6)
    view.window.simulate("click", node=view.node("root.t.top.entry[x].row"))
    settle(view, 6)
    assert app.bindings.viewmodel_for("main").sel.get() == "a"


def test_a_tree_with_nothing_bound_still_opens_and_chooses(tmp_path):
    (tmp_path / "Views").mkdir(exist_ok=True)
    (tmp_path / "Views" / "Main_View.yaml").write_text(f"""name: main
widget: Container
style: {{width: 400, height: 500}}
children:
  - {{widget: Tree, name: t, nodes: {NODES}}}
""")
    app = App(root=tmp_path)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    settle(view, 6)
    view.window.simulate("click", node=row(view, "pics"))
    settle(view, 6)
    assert "root.t.top.entry[pics].children" in view._built.specs and row(view, "pics").get("selected") is True
