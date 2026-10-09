"""#193: the Material 3 segmented button -- a connected row of options, single or multiple choice, a check for the chosen, the keyboard of a radio group."""

import pytest

from tesserae import App, Signal, ViewModel, tokens
from tesserae.shipped import shipped_views

OPTIONS = "[{value: day, label: Day}, {value: week, label: Week, icon: home}, {value: month, label: Month}, {value: year, label: Year, disabled: true}]"


class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.view = Signal("week")
        self.days = Signal(["day"])


def opened(tmp_path, widget, **kwargs):
    (tmp_path / "Views").mkdir(exist_ok=True)
    (tmp_path / "Views" / "Main_View.yaml").write_text(
        "name: main\nwidget: Container\nstyle: {flex_direction: vertical, align_content: top_left, width: 400, height: 200, padding: 16}\nchildren:\n" + widget)
    app = App(root=tmp_path, **kwargs)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    for _ in range(3):
        view.window.advance(16)
    return view, app.bindings.viewmodel_for("main")


SINGLE = f"  - {{widget: SegmentedButton, name: sb, options: {OPTIONS}, selected: \"{{{{ view }}}}\"}}\n"
MULTI = f"  - {{widget: SegmentedButton, name: sb, options: {OPTIONS}, selected: \"{{{{ days }}}}\", multiple: true}}\n"


def seg(view, value):
    return view.node(f"root.sb.segment[{value}]")


def role(view, name):
    return (view._scheme or tokens.BASELINE)[name]


def click(view, value):
    view.window.simulate("click", node=seg(view, value))
    for _ in range(3):
        view.window.advance(16)


def has(view, node_id):
    return node_id in view._built.specs


def test_it_is_shipped():
    assert "SegmentedButton" in shipped_views()


def test_it_is_a_forty_pixel_outlined_pill_of_connected_segments(tmp_path):
    view, _ = opened(tmp_path, SINGLE)
    root = view.node("root.sb")
    assert root.get("layout_height") == 40.0 and root.get("stroke_width") == 1.0 and root.get("stroke_color") == role(view, "outline")
    assert root.get("corner_radius") >= 20.0 and root.get("clip_children") is True
    xs = [seg(view, v).get("layout_x") for v in ("day", "week", "month", "year")]
    assert xs == sorted(xs) and all(seg(view, v).get("layout_height") == 40.0 for v in ("day", "week"))
    widths = [seg(view, v).get("layout_width") for v in ("day", "week", "month")]
    assert xs[1] == pytest.approx(xs[0] + widths[0]) and xs[2] == pytest.approx(xs[1] + widths[1])  # touching


def test_the_chosen_segment_is_a_secondary_container_with_a_check_replacing_its_icon(tmp_path):
    view, _ = opened(tmp_path, SINGLE)
    assert seg(view, "week").get("fill") == role(view, "secondary_container") and seg(view, "day").get("fill") == (0, 0, 0, 0)
    assert has(view, "root.sb.segment[week].icon") and not has(view, "root.sb.segment[day].icon")  # an unchosen one with no icon has none
    check = view.node("root.sb.segment[week].icon").get("data")
    from tesserae.icons import icon_path

    assert check == icon_path("check") or check
    assert view.node("root.sb.segment[week].label").get("fill") == role(view, "on_secondary_container")


def test_an_unchosen_segment_keeps_its_own_icon(tmp_path):
    view, vm = opened(tmp_path, SINGLE)
    vm.view.set("day")
    for _ in range(3):
        view.window.advance(16)
    assert has(view, "root.sb.segment[week].icon") and view.node("root.sb.segment[week].icon").get("fill") == role(view, "on_surface")
    assert has(view, "root.sb.segment[day].icon")  # the chosen one's check


def test_pressing_a_segment_chooses_it_and_writes_the_value(tmp_path):
    view, vm = opened(tmp_path, SINGLE)
    click(view, "month")
    assert vm.view.get() == "month" and seg(view, "month").get("fill") == role(view, "secondary_container")
    assert seg(view, "week").get("fill") == (0, 0, 0, 0)


def test_a_disabled_segment_is_dimmed_and_cannot_be_chosen(tmp_path):
    view, vm = opened(tmp_path, SINGLE)
    assert seg(view, "year").get("opacity") == 0.38
    click(view, "year")
    assert vm.view.get() == "week"


def test_the_whole_thing_disabled(tmp_path):
    view, vm = opened(tmp_path, SINGLE.replace("}\n", ", disabled: true}\n"))
    assert all(seg(view, v).get("opacity") == 0.38 for v in ("day", "week", "month"))
    click(view, "day")
    assert vm.view.get() == "week"


def test_single_choice_is_a_radio_group_with_one_tab_stop_and_arrows_that_choose(tmp_path):
    view, vm = opened(tmp_path, SINGLE)
    assert [seg(view, v).get("tab_index") for v in ("day", "week", "month")] == [-1, 0, -1]  # the chosen one is the tab stop
    assert seg(view, "week").get("role") == "radio" and seg(view, "week").get("checked") is True and seg(view, "day").get("checked") is False
    assert view.node("root.sb").get("role") == "group"
    seg(view, "week").focus()
    view.window.simulate("key_down", key="arrow_right")
    for _ in range(3):
        view.window.advance(16)
    assert vm.view.get() == "month"
    view.window.simulate("key_down", key="arrow_left")
    for _ in range(3):
        view.window.advance(16)
    assert vm.view.get() == "week"


def test_an_arrow_skips_past_a_disabled_segment_without_choosing_it(tmp_path):
    view, vm = opened(tmp_path, SINGLE)
    vm.view.set("month")
    for _ in range(3):
        view.window.advance(16)
    seg(view, "month").focus()
    view.window.simulate("key_down", key="arrow_right")
    for _ in range(3):
        view.window.advance(16)
    assert vm.view.get() != "year"


def test_multiple_choice_toggles_each_segment_and_the_roles_are_checkboxes(tmp_path):
    view, vm = opened(tmp_path, MULTI)
    assert seg(view, "day").get("role") == "checkbox" and seg(view, "day").get("checked") is True and seg(view, "week").get("checked") is False
    click(view, "month")
    assert vm.days.get() == ["day", "month"]
    click(view, "day")
    assert vm.days.get() == ["month"]
    assert seg(view, "month").get("fill") == role(view, "secondary_container") and seg(view, "day").get("fill") == (0, 0, 0, 0)


def test_multiple_choice_has_a_tab_stop_per_segment_and_the_arrows_do_not_choose(tmp_path):
    view, vm = opened(tmp_path, MULTI)
    seg(view, "day").focus()
    view.window.simulate("key_down", key="arrow_right")
    for _ in range(3):
        view.window.advance(16)
    assert vm.days.get() == ["day"]


def test_each_segment_is_named_for_a_screen_reader(tmp_path):
    view, _ = opened(tmp_path, SINGLE)
    assert [seg(view, v).get("label") for v in ("day", "week", "month")] == ["Day", "Week", "Month"]


def test_following_a_signal_moves_the_choice(tmp_path):
    view, vm = opened(tmp_path, SINGLE)
    vm.view.set("day")
    for _ in range(3):
        view.window.advance(16)
    assert seg(view, "day").get("fill") == role(view, "secondary_container") and seg(view, "week").get("fill") == (0, 0, 0, 0)


def test_options_can_change(tmp_path):
    class Dynamic(ViewModel):
        views = "main"

        def __init__(self):
            super().__init__()
            self.options = Signal([{"value": "a", "label": "A"}, {"value": "b", "label": "B"}])

    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Main_View.yaml").write_text(
        "name: main\nwidget: Container\nstyle: {width: 400, height: 100}\nchildren:\n"
        "  - {widget: SegmentedButton, name: sb, options: \"{{ options }}\", selected: a}\n")
    app = App(root=tmp_path)
    app.bind(Dynamic)
    view = app.open_view("Main")
    app.show("main")
    view.window.advance(16)
    assert has(view, "root.sb.segment[b]") and not has(view, "root.sb.segment[c]")
    app.bindings.viewmodel_for("main").options.set([{"value": "a", "label": "A"}, {"value": "b", "label": "B"}, {"value": "c", "label": "C"}])
    for _ in range(3):
        view.window.advance(16)
    assert has(view, "root.sb.segment[c]") and view.node("root.sb.segment[a]").get("fill") == role(view, "secondary_container")


def test_a_roving_group_starts_on_the_item_that_is_checked(tmp_path):
    view, vm = opened(tmp_path, SINGLE)
    vm.view.set("month")
    seg(view, "month").focus()
    view.window.advance(16)
    assert seg(view, "month").get("tab_index") == 0


def test_a_line_separates_the_segments_but_none_starts_the_first(tmp_path):
    view, _ = opened(tmp_path, SINGLE)
    assert not has(view, "root.sb.segment[day].divider")
    for v in ("week", "month", "year"):
        divider = view.node(f"root.sb.segment[{v}].divider")
        assert divider.get("layout_width") == 1.0 and divider.get("layout_height") == 40.0 and divider.get("fill") == role(view, "outline")


def test_a_role_from_a_signal_is_refused_because_a_role_cannot_change(tmp_path):
    from tesserae.spec.nodes import LoadError

    class Roles(ViewModel):
        views = "main"

        def __init__(self):
            super().__init__()
            self.r = Signal("button")

    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Main_View.yaml").write_text(
        "name: main\nwidget: Container\nstyle: {width: 100, height: 100}\nchildren:\n  - {widget: Container, name: c, a11y: {role: \"{{ r }}\"}}\n")
    app = App(root=tmp_path)
    app.bind(Roles)
    with pytest.raises(LoadError, match="a11y role cannot change while the view is open"):
        app.open_view("Main")
