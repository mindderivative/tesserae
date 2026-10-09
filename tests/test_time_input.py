"""#194: the keyboard form of the time picker -- hour and minute fields, a colon and an AM / PM selector."""

import pytest

from tesserae import App, Signal, ViewModel, tokens
from tesserae.shipped import shipped_views


class VM(ViewModel):
    views = "main"
    start = (14, 5)

    def __init__(self):
        super().__init__()
        self.h = Signal(self.start[0])
        self.m = Signal(self.start[1])


def opened(tmp_path, props="", hour=14, minute=5):
    (tmp_path / "Views").mkdir(exist_ok=True)
    lines = "\n    ".join(props.split(", ")) if props else ""
    (tmp_path / "Views" / "Main_View.yaml").write_text(f"""name: main
widget: Container
style: {{width: 500, height: 200, align_content: top_left}}
children:
  - widget: TimeInput
    name: ti
    hour: "{{{{ h }}}}"
    minute: "{{{{ m }}}}"
    {lines}
""")
    VM.start = (hour, minute)
    app = App(root=tmp_path)
    app.bind(VM)
    view = app.open_view("Main")
    vm = app.bindings.viewmodel_for("main")
    app.show("main")
    for _ in range(6):
        view.window.advance(16)
    return view, vm


def role(view, name):
    return (view._scheme or tokens.BASELINE)[name]


def field(view, which):
    return view.node(f"root.ti.{which}_field.box.body.input")


def type_into(view, which, text):
    node = field(view, which)
    node.focus()
    view.window.advance(16)
    node.set(text="")
    view.window.simulate("input", text=text)
    for _ in range(6):
        view.window.advance(16)


def test_it_is_shipped():
    assert {"TimeInput", "PeriodSelector"} <= set(shipped_views())


def test_the_fields_start_from_the_time_in_twelve_hour_form_with_the_period(tmp_path):
    view, _ = opened(tmp_path)
    assert field(view, "hour").get("text") == "02" and field(view, "minute").get("text") == "05"
    assert view.node("root.ti.period_selector.half[PM]").get("checked") is True


def test_a_morning_time_starts_as_am(tmp_path):
    view, _ = opened(tmp_path, hour=9, minute=30)
    assert field(view, "hour").get("text") == "09" and view.node("root.ti.period_selector.half[AM]").get("checked") is True


def test_midnight_and_noon_read_as_twelve(tmp_path):
    view, _ = opened(tmp_path, hour=0)
    assert field(view, "hour").get("text") == "12" and view.node("root.ti.period_selector.half[AM]").get("checked") is True
    (tmp_path / "n").mkdir()
    noon, _ = opened(tmp_path / "n", hour=12)
    assert field(noon, "hour").get("text") == "12" and noon.node("root.ti.period_selector.half[PM]").get("checked") is True


def test_typing_an_hour_sets_it_keeping_the_period(tmp_path):
    view, vm = opened(tmp_path)  # 14:05 is PM
    type_into(view, "hour", "9")
    assert vm.h.get() == 21
    type_into(view, "hour", "12")
    assert vm.h.get() == 12  # 12 PM is noon
    type_into(view, "hour", "10")
    assert vm.h.get() == 22


def test_an_hour_that_does_not_fit_is_left_out(tmp_path):
    view, vm = opened(tmp_path)
    type_into(view, "hour", "13")
    assert vm.h.get() == 14
    type_into(view, "hour", "0")
    assert vm.h.get() == 14


def test_typing_a_minute_sets_it_and_a_minute_over_fifty_nine_is_left_out(tmp_path):
    view, vm = opened(tmp_path)
    type_into(view, "minute", "42")
    assert vm.m.get() == 42
    type_into(view, "minute", "75")
    assert vm.m.get() == 42


def test_choosing_pm_or_am_moves_the_hour_by_twelve(tmp_path):
    view, vm = opened(tmp_path)  # 14:05
    view.window.simulate("click", node=view.node("root.ti.period_selector.half[AM]"))
    for _ in range(6):
        view.window.advance(16)
    assert vm.h.get() == 2
    view.window.simulate("click", node=view.node("root.ti.period_selector.half[PM]"))
    for _ in range(6):
        view.window.advance(16)
    assert vm.h.get() == 14


def test_twenty_four_hour_time_has_no_period_and_takes_zero_to_twenty_three(tmp_path):
    view, vm = opened(tmp_path, "twelve: false")
    assert field(view, "hour").get("text") == "14" and "root.ti.period_selector" not in view._built.specs
    type_into(view, "hour", "23")
    assert vm.h.get() == 23
    type_into(view, "hour", "0")
    assert vm.h.get() == 0
    type_into(view, "hour", "24")
    assert vm.h.get() == 0


def test_the_fields_are_labelled_and_the_colon_sits_between_them(tmp_path):
    view, _ = opened(tmp_path)
    assert field(view, "hour").get("label") == "Hour" and field(view, "minute").get("label") == "Minute"
    hour, colon, minute = (view.node(f"root.ti.{n}") for n in ("hour_field", "colon", "minute_field"))
    assert hour.get("layout_x") < colon.get("layout_x") < minute.get("layout_x") and hour.get("layout_width") == 96.0
    assert colon.get("font_size") == 45.0 and colon.get("fill") == role(view, "on_surface")


def test_a_disabled_input_cannot_be_edited(tmp_path):
    view, vm = opened(tmp_path, "disabled: true")
    assert field(view, "hour").get("disabled") is True
    view.window.simulate("click", node=view.node("root.ti.period_selector.half[AM]"))
    for _ in range(6):
        view.window.advance(16)
    assert vm.h.get() == 14
