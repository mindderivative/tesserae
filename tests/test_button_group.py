"""#123: the Material 3 button group -- actions, a choice of one, a set, connected or spaced, a row or a column."""

import pytest

from tesserae import App, Signal, ViewModel, tokens
from tesserae.shipped import shipped_views

ITEMS = "[{value: day, label: Day}, {value: week, label: Week}, {value: month, label: Month}]"


class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.one = Signal("week")
        self.many = Signal(["day"])
        self.last = Signal("")


def opened(tmp_path, props="", items=ITEMS):
    (tmp_path / "Views").mkdir(exist_ok=True)
    (tmp_path / "Views" / "Main_View.yaml").write_text(f"""name: main
widget: Container
style: {{flex_direction: vertical, align_content: top_left, width: 500, height: 400}}
children:
  - {{widget: ButtonGroup, name: g, items: {items}, {props}}}
""")
    app = App(root=tmp_path)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    for _ in range(4):
        view.window.advance(16)
    return view, app.bindings.viewmodel_for("main")


def item(view, value):
    return view.node(f"root.g.item[{value}]")


def role(view, name):
    return (view._scheme or tokens.BASELINE)[name]


def click(view, value):
    view.window.simulate("click", node=item(view, value))
    for _ in range(40):
        view.window.advance(16)


def test_it_is_shipped():
    assert "ButtonGroup" in shipped_views()


SINGLE = 'mode: single, selected: "{{ one }}"'
MULTI = 'mode: multiple, selected: "{{ many }}"'


def test_a_group_of_actions_is_a_row_of_buttons_eight_pixels_apart(tmp_path):
    view, _ = opened(tmp_path)
    day, week, month = (item(view, v) for v in ("day", "week", "month"))
    assert day.get("layout_y") == week.get("layout_y") == month.get("layout_y")
    assert week.get("layout_x") == day.get("layout_x") + day.get("layout_width") + 8
    assert month.get("layout_x") == week.get("layout_x") + week.get("layout_width") + 8
    assert view.node("root.g").get("role") == "group"


def test_pressing_an_action_reports_which(tmp_path):
    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Main_View.yaml").write_text(f"""name: main
widget: Container
style: {{width: 500, height: 200}}
children:
  - {{widget: ButtonGroup, name: g, items: {ITEMS}, chosen: "{{{{ last }}}}"}}
""")
    app = App(root=tmp_path)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    view.window.advance(16)
    click(view, "month")
    assert app.bindings.viewmodel_for("main").last.get() == "month"
    assert item(view, "month").get("pressed") is None  # an action is no toggle


def test_an_action_group_needs_nothing_bound(tmp_path):
    view, _ = opened(tmp_path)
    click(view, "week")  # writes the group's own `chosen`; nothing raised
    assert item(view, "week").get("layout_width") > 0


def test_single_mode_shows_the_chosen_button_pressed_and_choosing_moves_it(tmp_path):
    view, vm = opened(tmp_path, SINGLE)
    assert [item(view, v).get("pressed") for v in ("day", "week", "month")] == [False, True, False]
    assert item(view, "week").get("fill") == role(view, "primary") and item(view, "day").get("fill") == role(view, "surface_container_highest")
    click(view, "month")
    assert vm.one.get() == "month"
    assert [item(view, v).get("pressed") for v in ("day", "week", "month")] == [False, False, True]


def test_multiple_mode_toggles_each_button(tmp_path):
    view, vm = opened(tmp_path, MULTI)
    assert [item(view, v).get("pressed") for v in ("day", "week", "month")] == [True, False, False]
    click(view, "month")
    assert vm.many.get() == ["day", "month"]
    click(view, "day")
    assert vm.many.get() == ["month"]


def test_one_tab_stop_and_the_arrows_move_the_choice_in_single_mode(tmp_path):
    view, vm = opened(tmp_path, SINGLE)
    assert [item(view, v).get("tab_index") for v in ("day", "week", "month")] == [-1, 0, -1]
    item(view, "week").focus()
    view.window.simulate("key_down", key="arrow_right")
    for _ in range(10):
        view.window.advance(16)
    assert vm.one.get() == "month"
    view.window.simulate("key_down", key="Home")
    for _ in range(10):
        view.window.advance(16)
    assert vm.one.get() == "day"


def test_the_arrows_only_move_the_focus_in_multiple_mode(tmp_path):
    view, vm = opened(tmp_path, MULTI)
    item(view, "day").focus()
    view.window.simulate("key_down", key="arrow_right")
    for _ in range(10):
        view.window.advance(16)
    assert vm.many.get() == ["day"]


def test_a_connected_group_is_two_pixels_apart_with_square_inner_corners(tmp_path):
    view, _ = opened(tmp_path, "connected: true")
    day, week, month = (item(view, v) for v in ("day", "week", "month"))
    assert week.get("layout_x") == day.get("layout_x") + day.get("layout_width") + 2
    assert day.get("corner_radius") == (9999.0, 4.0, 4.0, 9999.0)
    assert week.get("corner_radius") == 4.0
    assert month.get("corner_radius") == (4.0, 9999.0, 9999.0, 4.0)


def test_a_vertical_group_is_a_column(tmp_path):
    view, _ = opened(tmp_path, "orientation: vertical, connected: true")
    day, week = item(view, "day"), item(view, "week")
    assert week.get("layout_y") == day.get("layout_y") + day.get("layout_height") + 2 and week.get("layout_x") == day.get("layout_x")
    assert day.get("corner_radius") == (9999.0, 9999.0, 4.0, 4.0)


def test_variant_and_size_pass_to_every_button(tmp_path):
    view, _ = opened(tmp_path, "variant: tonal, size: m")
    for v in ("day", "week", "month"):
        assert item(view, v).get("layout_height") == 56.0 and item(view, v).get("fill") == role(view, "secondary_container")


def test_a_disabled_item_and_a_disabled_group_do_not_respond(tmp_path):
    view, vm = opened(tmp_path, SINGLE, items="[{value: day, label: Day, disabled: true}, {value: week, label: Week}, {value: month, label: Month}]")
    click(view, "day")
    assert vm.one.get() == "week"
    view2, vm2 = opened(tmp_path / "b" if (tmp_path / "b").mkdir() is None else tmp_path, SINGLE + ", disabled: true")
    click(view2, "month")
    assert vm2.one.get() == "week"


def test_an_item_can_have_an_icon(tmp_path):
    view, _ = opened(tmp_path, items="[{value: a, label: A, icon: home}, {value: b, label: B}]")
    assert view.node("root.g.item[a].icon").get("layout_width") == 18.0
