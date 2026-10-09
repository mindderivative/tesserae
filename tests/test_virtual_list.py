"""#228: `widget: VirtualList` -- a long list that builds only the rows in view, and builds more as it scrolls."""

import pytest

from tesserae import App, Signal, ViewModel
from tesserae.spec.compose import Virtual
from tesserae.spec.nodes import LoadError


class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.rows = Signal([{"id": i, "name": f"Row {i}"} for i in range(10000)])
        self.top = Signal(True)
        self.end = Signal(False)
        self.offset = Signal(0.0)
        self.picked = Signal(-1)


VIEW = """name: main
widget: Container
style: {flex_direction: vertical, width: 300, height: 200}
children:
  - widget: VirtualList
    name: list
    item_height: 40
    scroll_offset: "{{ offset }}"
    at_top: "{{ top }}"
    at_end: "{{ end }}"
    style: {width: 300, height: 200}
    children:
      - widget: Container
        for: row in rows
        key: row.id
        name: row
        style: {background: surface}
        handlers: {on_click: "picked = row.id"}
        children:
          - {widget: Text, name: label, text: "{{ row.name }}", typography_role: body_large, style: {foreground: on_surface}}
"""


def opened(tmp_path, text=VIEW):
    (tmp_path / "Views").mkdir(exist_ok=True)
    (tmp_path / "Views" / "Main_View.yaml").write_text(text)
    app = App(root=tmp_path)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    for _ in range(4):
        view.window.advance(16)
    return view, app.bindings.viewmodel_for("main")


def scroll_to(view, vm, offset):
    vm.offset.set(float(offset))
    for _ in range(4):
        view.window.advance(16)


def built(view):
    return sorted(int(i.rsplit("row", 1)[1].strip("[]")) for i in view._built.specs if ".row[" in i and i.count(".") == 2)


def list_node(view):
    return view._built.outer["root.list"]


def test_only_the_rows_in_view_are_built(tmp_path):
    view, _ = opened(tmp_path)
    rows = built(view)
    assert rows[0] == 0 and rows[-1] <= 5 + 3 + 1 and len(rows) <= 12  # 200 / 40 = 5 in view, 3 more past the edge
    assert len(view._built.specs) < 60


def test_the_list_is_as_tall_as_all_its_rows(tmp_path):
    view, _ = opened(tmp_path)
    assert view._built.nodes["root.list"].get("layout_height") == 10000 * 40.0


def test_rows_sit_at_their_place_in_the_list(tmp_path):
    view, _ = opened(tmp_path)
    for index in (0, 1, 4):
        assert view.node(f"root.list.row[{index}]").get("layout_y") == index * 40.0
    assert view.node("root.list.row[3]").get("layout_height") == 40.0 and view.node("root.list.row[3].label").get("text") == "Row 3"


def test_scrolling_builds_the_rows_that_come_into_view_and_drops_the_ones_that_leave(tmp_path):
    view, vm = opened(tmp_path)
    scroll_to(view, vm, 4000)  # row 100 at the top
    rows = built(view)
    assert 100 in rows and 104 in rows and 0 not in rows and len(rows) <= 14
    assert min(rows) >= 100 - 3 - 1
    assert view.node("root.list.row[100]").get("layout_y") == 0.0 and view.node("root.list.row[102]").get("layout_y") == 80.0  # placed in the list, shown at its scroll position
    assert view.node("root.list.row[100].label").get("text") == "Row 100"


def test_a_row_far_down_is_reached_and_the_scroll_state_follows(tmp_path):
    view, vm = opened(tmp_path)
    scroll_to(view, vm, 10000 * 40 - 200)
    assert vm.end.get() is True and vm.top.get() is False
    assert 9999 in built(view) and len(built(view)) <= 14


def test_a_row_handles_its_own_events_with_its_own_values(tmp_path):
    view, vm = opened(tmp_path)
    scroll_to(view, vm, 2000)
    view.window.simulate("click", node=view.node("root.list.row[52]"))
    assert vm.picked.get() == 52


def test_changing_the_data_updates_the_rows_in_view_and_the_length(tmp_path):
    view, vm = opened(tmp_path)
    scroll_to(view, vm, 400)
    vm.rows.set([{"id": i, "name": f"New {i}"} for i in range(50)])
    for _ in range(4):
        view.window.advance(16)
    assert view.node("root.list.row[12].label").get("text") == "New 12"
    assert view._built.nodes["root.list"].get("layout_height") == 50 * 40.0
    assert max(built(view)) <= 49


def test_an_empty_list_builds_nothing(tmp_path):
    view, vm = opened(tmp_path)
    vm.rows.set([])
    for _ in range(4):
        view.window.advance(16)
    assert built(view) == [] and view._built.nodes["root.list"].get("layout_height") == 0.0


def test_a_short_list_builds_all_its_rows(tmp_path):
    view, vm = opened(tmp_path)
    vm.rows.set([{"id": i, "name": f"Row {i}"} for i in range(3)])
    for _ in range(4):
        view.window.advance(16)
    assert built(view) == [0, 1, 2]


@pytest.mark.parametrize("children, message", [
    ("    children:\n      - {widget: Container, name: a}\n", "one child, and it has a 'for:'"),
    ("    children:\n      - {widget: Container, for: r in rows, name: a}\n", "a reactive 'for:' needs a 'key:'"),
    ("    children:\n      - {widget: Container, for: r in rows, key: r.id, name: a}\n      - {widget: Container, for: r in rows, key: r.id, name: b}\n", "one child"),
])
def test_a_virtual_list_needs_one_looped_child_with_a_key(tmp_path, children, message):
    text = VIEW[:VIEW.index("    children:")] + children
    with pytest.raises(LoadError, match=message):
        opened(tmp_path, text)


def test_item_height_is_required(tmp_path):
    with pytest.raises(LoadError, match="'item_height' is required"):
        opened(tmp_path, VIEW.replace("    item_height: 40\n", ""))


def test_the_rows_built_are_those_in_view_and_the_overscan_each_side(tmp_path):
    view, vm = opened(tmp_path)
    scroll_to(view, vm, 4000)  # rows 100 to 105 are in view (200 / 40 = 5, and the one starting at the bottom edge)
    assert built(view) == list(range(97, 109))


def test_the_overscan_is_a_property(tmp_path):
    view, vm = opened(tmp_path, VIEW.replace("    item_height: 40\n", "    item_height: 40\n    overscan: 0\n"))
    scroll_to(view, vm, 4000)
    assert built(view) == list(range(100, 106))


def test_a_row_put_in_front_moves_the_ones_after_it_down(tmp_path):
    view, vm = opened(tmp_path)
    assert view.node("root.list.row[0]").get("layout_y") == 0.0
    vm.rows.set([{"id": -1, "name": "First"}] + vm.rows.get())
    for _ in range(4):
        view.window.advance(16)
    assert view.node("root.list.row[0]").get("layout_y") == 40.0 and view.node("root.list.row[-1]").get("layout_y") == 0.0


def test_setting_the_window_it_already_has_does_nothing():
    window, seen = Virtual(lambda: 40.0, lambda: 3), []
    window._reconcile = lambda: seen.append(1)
    window.set_window(0, Virtual.INITIAL - 1)
    assert seen == []
    window.set_window(5, 20)
    window.set_window(5, 20)
    assert seen == [1]


def test_the_window_for_a_viewport_is_clamped_to_the_list():
    window = Virtual(lambda: 40.0, lambda: 3)
    window.count = 10
    assert window.window_for(0, 200) == (0, 8) and window.window_for(360, 200) == (6, 9)
    window.count = 0
    assert window.window_for(0, 200)[1] < window.window_for(0, 200)[0]  # nothing to build
