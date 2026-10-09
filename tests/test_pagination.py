"""#200: page navigation -- previous and next, the numbers with an ellipsis, a compact form and dots."""

import pytest

from tesserae import App, Signal, ViewModel, tokens
from tesserae.shipped import shipped_views


class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.page = Signal(1)
        self.total = Signal(12)


def opened(tmp_path, props="", page=1):
    (tmp_path / "Views").mkdir(exist_ok=True)
    (tmp_path / "Views" / "Main_View.yaml").write_text(f"""name: main
widget: Container
style: {{flex_direction: vertical, align_content: top_left, width: 600, height: 200}}
children:
  - {{widget: Pagination, name: p, page: "{{{{ page }}}}", pages: "{{{{ total }}}}"{', ' + props if props else ''}}}
""")
    app = App(root=tmp_path)
    app.bind(VM)
    view = app.open_view("Main")
    vm = app.bindings.viewmodel_for("main")
    vm.page.set(page)
    app.show("main")
    for _ in range(6):
        view.window.advance(16)
    return view, vm


def role(view, name):
    return (view._scheme or tokens.BASELINE)[name]


def shown(view):
    """The page numbers showing, with '…' for each gap, left to right."""
    cells = []
    for key in view._built.specs:
        if key.startswith("root.p.slot[") and key.endswith("].number.label"):
            n = int(key[len("root.p.slot["):key.index("]")])
            cells.append((view.node(key).get("layout_x"), n))
        if key.startswith("root.p.slot[") and key.endswith("].gap"):
            n = int(key[len("root.p.slot["):key.index("]")])
            cells.append((view.node(key).get("layout_x"), "…"))
    return [c for _, c in sorted(cells, key=lambda t: t[0])]


def settle(view, n=40):
    for _ in range(n):
        view.window.advance(16)


def test_it_is_shipped():
    assert "Pagination" in shipped_views()


@pytest.mark.parametrize("page, expected", [
    (1, [1, 2, "…", 12]), (2, [1, 2, 3, "…", 12]), (4, [1, 2, 3, 4, 5, "…", 12]), (5, [1, "…", 4, 5, 6, "…", 12]),
    (6, [1, "…", 5, 6, 7, "…", 12]), (9, [1, "…", 8, 9, 10, 11, 12]), (11, [1, "…", 10, 11, 12]), (12, [1, "…", 11, 12]),
])
def test_the_numbers_are_the_first_the_last_and_the_neighbours_with_an_ellipsis_for_what_is_left_out(tmp_path, page, expected):
    view, _ = opened(tmp_path, page=page)
    assert shown(view) == expected


def test_a_short_range_shows_every_page(tmp_path):
    view, vm = opened(tmp_path, page=3)
    vm.total.set(7)
    settle(view, 6)
    assert shown(view) == [1, 2, 3, 4, 5, 6, 7]


def test_a_single_page_is_just_page_one(tmp_path):
    view, vm = opened(tmp_path)
    vm.total.set(1)
    settle(view, 6)
    assert shown(view) == [1]


def test_the_current_page_is_a_filled_button_and_the_others_are_text(tmp_path):
    view, _ = opened(tmp_path, page=6)
    assert view.node("root.p.slot[6].number").get("fill") == role(view, "primary") and view.node("root.p.slot[6].number").get("current") == "page"
    assert view.node("root.p.slot[7].number").get("fill")[3] == 0 and view.node("root.p.slot[7].number").get("current") is False


def test_each_number_is_named_as_a_page(tmp_path):
    view, _ = opened(tmp_path, page=6)
    assert view.node("root.p.slot[7].number").get("label") == "Page 7" and view.node("root.p").get("label") == "Pagination"


def test_pressing_a_number_goes_to_that_page(tmp_path):
    view, vm = opened(tmp_path, page=6)
    view.window.simulate("click", node=view.node("root.p.slot[7].number"))
    settle(view, 6)
    assert vm.page.get() == 7 and shown(view) == [1, "…", 6, 7, 8, "…", 12]
    view.window.simulate("click", node=view.node("root.p.slot[12].number"))
    settle(view, 6)
    assert vm.page.get() == 12


def test_previous_and_next_step_and_are_disabled_at_the_ends(tmp_path):
    view, vm = opened(tmp_path)
    assert view.node("root.p.previous").get("disabled") is True and view.node("root.p.next").get("disabled") is False
    view.window.simulate("click", node=view.node("root.p.next"))
    settle(view, 6)
    assert vm.page.get() == 2 and view.node("root.p.previous").get("disabled") is False
    view.window.simulate("click", node=view.node("root.p.previous"))
    settle(view, 6)
    assert vm.page.get() == 1
    view.window.simulate("click", node=view.node("root.p.previous"))
    settle(view, 6)
    assert vm.page.get() == 1  # no page 0
    vm.page.set(12)
    settle(view, 6)
    assert view.node("root.p.next").get("disabled") is True


def test_previous_and_next_are_named(tmp_path):
    view, _ = opened(tmp_path)
    assert view.node("root.p.previous").get("label") == "Previous page" and view.node("root.p.next").get("label") == "Next page"


def test_compact_is_a_text_between_the_arrows(tmp_path):
    view, vm = opened(tmp_path, "compact: true", page=3)
    assert view.node("root.p.summary").get("text") == "3 of 12" and not shown(view)
    assert view.node("root.p.previous").get("layout_x") < view.node("root.p.summary").get("layout_x") < view.node("root.p.next").get("layout_x")
    vm.page.set(4)
    settle(view, 6)
    assert view.node("root.p.summary").get("text") == "4 of 12"
    view.window.simulate("click", node=view.node("root.p.next"))
    settle(view, 6)
    assert vm.page.get() == 5


def test_dots_are_one_to_a_page_with_the_current_one_primary(tmp_path):
    view, vm = opened(tmp_path, "dots: true", page=2)
    vm.total.set(5)
    settle(view, 6)
    assert [view.node(f"root.p.dot[{n}].mark").get("fill") == role(view, "primary") for n in range(1, 6)] == [False, True, False, False, False]
    view.window.simulate("click", node=view.node("root.p.dot[4]"))
    settle(view, 6)
    assert vm.page.get() == 4 and view.node("root.p.dot[4].mark").get("fill") == role(view, "primary")
    assert view.node("root.p.dot[3]").get("label") == "Page 3" and view.node("root.p.dot[4]").get("current") == "page"
