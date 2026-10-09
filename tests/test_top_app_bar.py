"""#165: the Material 3 top app bar -- small, centre, medium and large; icons with labels, collapsing and the scrolled colour."""

import pytest

from tesserae import App, Signal, ViewModel, tokens
from tesserae.shipped import shipped_views

ACTIONS = "[{value: search, icon: magnify, label: Search}, {value: more, icon: dots_vertical, label: More}]"


class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.chosen = Signal("")
        self.collapsed = Signal(False)
        self.scrolled = Signal(False)
        self.log = []

    def nav(self):
        self.log.append("nav")


def opened(tmp_path, props="", actions=ACTIONS, leading="menu"):
    (tmp_path / "Views").mkdir(exist_ok=True)
    lines = "\n    ".join(props.split(", ")) if props else ""
    (tmp_path / "Views" / "Main_View.yaml").write_text(f"""name: main
widget: Container
style: {{flex_direction: vertical, align_content: top_left, width: 500, height: 400}}
children:
  - widget: TopAppBar
    name: bar
    title: Inbox
    leading_icon: '{leading}'
    on_leading: nav
    actions: {actions}
    chosen: "{{{{ chosen }}}}"
    {lines}
""")
    app = App(root=tmp_path, width=500, height=400)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    for _ in range(8):
        view.window.advance(16)
    return view, app.bindings.viewmodel_for("main")


def role(view, name):
    return (view._scheme or tokens.BASELINE)[name]


def settle(view, n=30):
    for _ in range(n):
        view.window.advance(16)


def bar(view):
    return view.node("root.bar")


def test_it_is_shipped():
    assert "TopAppBar" in shipped_views()


def test_the_four_sizes(tmp_path):
    heights = {}
    for i, variant in enumerate(("small", "center", "medium", "large")):
        (tmp_path / str(i)).mkdir()
        view, _ = opened(tmp_path / str(i), f"variant: {variant}")
        heights[variant] = bar(view).get("layout_height")
    assert heights == {"small": 64.0, "center": 64.0, "medium": 112.0, "large": 152.0}


def test_a_small_bar_has_the_navigation_icon_the_title_in_title_large_and_the_actions_at_the_end(tmp_path):
    view, _ = opened(tmp_path)
    lead, title, search, more = (view.node("root.bar.row.leading"), view.node("root.bar.row.title"),
                                 view.node("root.bar.row.action[search]"), view.node("root.bar.row.action[more]"))
    assert lead.get("label") == "Navigation" and title.get("text") == "Inbox" and title.get("font_size") == 22.0 and title.get("fill") == role(view, "on_surface")
    assert lead.get("layout_x") == 4.0 and title.get("layout_x") >= lead.get("layout_x") + 40
    assert more.get("layout_x") + more.get("layout_width") == 500 - 4 and search.get("layout_x") + 40 == more.get("layout_x")
    assert title.get("level") == 1


def test_a_centre_aligned_bar_puts_the_title_in_the_middle(tmp_path):
    view, _ = opened(tmp_path, "variant: center")
    title = view.node("root.bar.row.title")
    assert abs((title.get("layout_x") + title.get("layout_width") / 2) - 250) <= 70  # between the icon and the actions, not against the icon


def test_a_medium_bar_has_a_headline_small_title_under_the_icons_and_a_large_one_a_headline_medium(tmp_path):
    view, _ = opened(tmp_path, "variant: medium")
    big = view.node("root.bar.big_title")
    assert big.get("font_size") == 24.0 and big.get("layout_y") >= view.node("root.bar.row").get("layout_y") + 64 and "root.bar.row.title" not in view._built.specs
    (tmp_path / "l").mkdir()
    large, _ = opened(tmp_path / "l", "variant: large")
    assert large.node("root.bar.big_title").get("font_size") == 28.0


def test_collapsing_a_medium_bar_shrinks_it_to_a_small_one_with_the_title_beside_the_icon(tmp_path):
    view, vm = opened(tmp_path, 'variant: large, collapsed: "{{ collapsed }}"')
    assert bar(view).get("layout_height") == 152.0
    vm.collapsed.set(True)
    for _ in range(4):
        view.window.advance(16)
    assert 64.0 < bar(view).get("layout_height") < 152.0  # it eases
    settle(view)
    assert bar(view).get("layout_height") == 64.0 and "root.bar.big_title" not in view._built.specs and "root.bar.row.title" in view._built.specs


def test_the_colour_is_surface_and_becomes_surface_container_once_content_is_under_it(tmp_path):
    view, vm = opened(tmp_path, 'scrolled: "{{ scrolled }}"')
    assert bar(view).get("fill") == role(view, "surface")
    vm.scrolled.set(True)
    settle(view)
    assert bar(view).get("fill") == role(view, "surface_container")


def test_the_navigation_icon_runs_on_leading_and_an_action_sets_chosen(tmp_path):
    view, vm = opened(tmp_path)
    view.window.simulate("click", node=view.node("root.bar.row.leading"))
    assert vm.log == ["nav"]
    view.window.simulate("click", node=view.node("root.bar.row.action[more]"))
    assert vm.chosen.get() == "more"


def test_every_icon_is_a_button_with_a_label_that_is_its_name(tmp_path):
    view, _ = opened(tmp_path)
    assert [view.node(f"root.bar.row.action[{v}]").get("label") for v in ("search", "more")] == ["Search", "More"]
    assert view.node("root.bar.row.action[search]").get("role") == "button"


def test_at_most_three_actions_show(tmp_path):
    many = "[" + ", ".join("{value: a%d, icon: home, label: A%d}" % (n, n) for n in range(5)) + "]"
    view, _ = opened(tmp_path, actions=many)
    assert [k for k in view._built.specs if k.startswith("root.bar.row.action[") and k.count(".") == 3] == [f"root.bar.row.action[a{n}]" for n in range(3)]


def test_without_a_navigation_icon_the_title_starts_16_pixels_in(tmp_path):
    view, _ = opened(tmp_path, leading="")
    assert view.node("root.bar.row.title").get("layout_x") == 4 + 16


def test_the_bar_is_a_group_named_by_the_title(tmp_path):
    view, _ = opened(tmp_path)
    assert bar(view).get("role") == "group" and bar(view).get("label") == "Inbox"
