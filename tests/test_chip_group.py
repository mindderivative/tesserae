"""#182 and the chip groups of #179 to #183: wrapping rows of chips that act, filter, or are entered."""

import pytest

from tesserae import App, Signal, ViewModel, tokens
from tesserae.shipped import shipped_views

CHIPS = "[{value: a, label: Alpha}, {value: b, label: Beta, icon: home}, {value: c, label: Gamma}]"


class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.one = Signal("b")
        self.many = Signal(["a"])
        self.last = Signal("")
        self.tags = Signal([{"value": "x", "label": "Ex"}, {"value": "y", "label": "Why"}])
        self.typed = Signal("")


def opened(tmp_path, props="", width=500):
    (tmp_path / "Views").mkdir(exist_ok=True)
    (tmp_path / "Views" / "Main_View.yaml").write_text(f"""name: main
widget: Container
style: {{flex_direction: vertical, align_content: top_left, width: {width}, height: 300}}
children:
  - {{widget: ChipGroup, name: g, {props or 'chips: ' + CHIPS}}}
""")
    app = App(root=tmp_path)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    for _ in range(4):
        view.window.advance(16)
    return view, app.bindings.viewmodel_for("main")


def role(view, name):
    return (view._scheme or tokens.BASELINE)[name]


def chip(view, value):
    return view.node(f"root.g.chip[{value}]")


def settle(view, n=40):
    for _ in range(n):
        view.window.advance(16)


def click(view, node):
    view.window.simulate("click", node=node)
    settle(view, 10)


def test_it_is_shipped():
    assert {"Chip", "ChipGroup"} <= set(shipped_views())


def test_chips_stand_8_pixels_apart_in_a_row_and_wrap_onto_a_new_row(tmp_path):
    view, _ = opened(tmp_path)
    a, b, c = chip(view, "a"), chip(view, "b"), chip(view, "c")
    assert a.get("layout_y") == b.get("layout_y") == c.get("layout_y")
    assert b.get("layout_x") == a.get("layout_x") + a.get("layout_width") + 8
    (tmp_path / "n").mkdir()
    narrow, _ = opened(tmp_path / "n", width=140)
    assert chip(narrow, "c").get("layout_y") > chip(narrow, "a").get("layout_y")
    assert chip(narrow, "c").get("layout_y") == chip(narrow, "a").get("layout_y") + 32 + 8 or chip(narrow, "b").get("layout_y") > chip(narrow, "a").get("layout_y")


def test_none_mode_chips_are_assist_chips_that_report_the_one_pressed(tmp_path):
    view, vm = opened(tmp_path, "chips: " + CHIPS + ', chosen: "{{ last }}"')
    assert chip(view, "a").get("role") == "button" and chip(view, "a").get("stroke_width") == 1.0
    click(view, chip(view, "c"))
    assert vm.last.get() == "c"


def test_suggestion_variant_and_elevated(tmp_path):
    view, _ = opened(tmp_path, "chips: " + CHIPS + ", variant: suggestion, elevated: true")
    assert chip(view, "a").get("fill") == role(view, "surface_container_low") and chip(view, "a").get("shadows")


def test_single_mode_shows_the_chosen_chip_selected_and_choosing_moves_it(tmp_path):
    view, vm = opened(tmp_path, "chips: " + CHIPS + ', mode: single, selected: "{{ one }}"')
    assert [chip(view, v).get("checked") for v in "abc"] == [False, True, False]
    assert chip(view, "b").get("fill") == role(view, "secondary_container")
    click(view, chip(view, "c"))
    assert vm.one.get() == "c" and [chip(view, v).get("checked") for v in "abc"] == [False, False, True]
    click(view, chip(view, "c"))
    assert vm.one.get() == "c" and chip(view, "c").get("checked") is True  # a radio-like choice stays chosen


def test_multiple_mode_toggles_each_chip(tmp_path):
    view, vm = opened(tmp_path, "chips: " + CHIPS + ', mode: multiple, selected: "{{ many }}"')
    assert [chip(view, v).get("checked") for v in "abc"] == [True, False, False]
    click(view, chip(view, "c"))
    assert vm.many.get() == ["a", "c"]
    click(view, chip(view, "a"))
    assert vm.many.get() == ["c"] and chip(view, "a").get("checked") is False


def test_one_tab_stop_and_the_arrows_move_the_choice_in_single_mode(tmp_path):
    view, vm = opened(tmp_path, "chips: " + CHIPS + ', mode: single, selected: "{{ one }}"')
    assert [chip(view, v).get("tab_index") for v in "abc"] == [-1, 0, -1]
    chip(view, "b").focus()
    view.window.simulate("key_down", key="arrow_right")
    settle(view, 10)
    assert vm.one.get() == "c"


def test_a_disabled_chip_in_a_group_does_not_respond(tmp_path):
    view, vm = opened(tmp_path, "chips: [{value: a, label: Alpha, disabled: true}, {value: b, label: Beta}], mode: single, selected: \"{{ one }}\"")
    click(view, chip(view, "a"))
    assert vm.one.get() == "b"


def test_input_mode_chips_have_a_close_that_removes_them_from_the_list(tmp_path):
    view, vm = opened(tmp_path, 'mode: input, chips: "{{ tags }}"')
    assert chip(view, "x").get("layout_width") > 0 and "root.g.chip[x].close" in view._built.specs
    click(view, view.node("root.g.chip[x].close"))
    assert vm.tags.get() == [{"value": "y", "label": "Why"}]
    assert "root.g.chip[x]" not in view._built.specs and "root.g.chip[y]" in view._built.specs


def press_enter_in_the_field(view):
    field = view.node("root.g.entry.box.body.input")
    field.focus()
    view.window.advance(16)
    view.window.simulate("key_down", key="Enter")
    settle(view, 6)


def test_typing_in_the_field_and_pressing_enter_adds_a_chip(tmp_path):
    view, vm = opened(tmp_path, 'mode: input, chips: "{{ tags }}", entry: "{{ typed }}"')
    vm.typed.set("Zed")
    settle(view, 4)
    press_enter_in_the_field(view)
    assert [t["value"] for t in vm.tags.get()] == ["x", "y", "Zed"] and vm.typed.get() == ""
    assert "root.g.chip[Zed]" in view._built.specs


def test_a_repeated_entry_is_not_added_twice_and_an_empty_one_not_at_all(tmp_path):
    view, vm = opened(tmp_path, 'mode: input, chips: "{{ tags }}", entry: "{{ typed }}"')
    vm.typed.set("x")
    settle(view, 4)
    press_enter_in_the_field(view)
    assert [t["value"] for t in vm.tags.get()] == ["x", "y"] and vm.typed.get() == ""
    press_enter_in_the_field(view)
    assert [t["value"] for t in vm.tags.get()] == ["x", "y"]


def test_a_group_with_no_bound_list_still_removes_chips_from_its_own_copy(tmp_path):
    view, _ = opened(tmp_path, "mode: input, chips: " + CHIPS)
    click(view, view.node("root.g.chip[b].close"))
    assert "root.g.chip[b]" not in view._built.specs and "root.g.chip[a]" in view._built.specs
