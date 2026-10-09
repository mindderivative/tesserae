"""#190, #191, #192, #194: the Material 3 time picker -- the time at the top, the dial, typed fields, Cancel and OK."""

import pytest

from tesserae import App, Signal, ViewModel, tokens
from tesserae.shipped import shipped_views


class VM(ViewModel):
    views = "main"
    start = (14, 35)

    def __init__(self):
        super().__init__()
        self.open = Signal(False)
        self.h = Signal(self.start[0])
        self.m = Signal(self.start[1])
        self.log = []

    def confirmed(self):
        self.log.append("ok")


def opened(tmp_path, props="", hour=14, minute=35, show=True):
    (tmp_path / "Views").mkdir(exist_ok=True)
    lines = "\n    ".join(props.split(", ")) if props else ""
    (tmp_path / "Views" / "Main_View.yaml").write_text(f"""name: main
widget: Container
style: {{width: 600, height: 700}}
children:
  - widget: TimePicker
    name: tp
    open: "{{{{ open }}}}"
    hour: "{{{{ h }}}}"
    minute: "{{{{ m }}}}"
    {lines}
""")
    VM.start = (hour, minute)
    app = App(root=tmp_path, width=600, height=700)
    app.bind(VM)
    view = app.open_view("Main")
    vm = app.bindings.viewmodel_for("main")
    app.show("main")
    settle(view, 4)
    if show:
        vm.open.set(True)
        settle(view, 8)
    return view, vm


def role(view, name):
    return (view._scheme or tokens.BASELINE)[name]


def settle(view, n=20):
    for _ in range(n):
        view.window.advance(16)


def p(view, path):
    return view.node("root.tp.panel" + (("." + path) if path else ""))


def test_it_is_shipped():
    assert {"TimePicker", "TimeInput", "PeriodSelector"} <= set(shipped_views())


def dial(view):
    return view._built.controls["root.tp.panel.dial"]


def press_key_on_dial(view, key, times=1):
    dial(view).node.focus()
    settle(view, 2)
    for _ in range(times):
        view.window.simulate("key_down", key=key)
    settle(view, 4)


def shown(view):
    return p(view, "header.hour_button.hour_text").get("text") + ":" + p(view, "header.minute_button.minute_text").get("text")


def test_it_is_closed_until_open_and_then_a_scrim_with_a_dialog(tmp_path):
    view, vm = opened(tmp_path, show=False)
    assert not view._shown_layers
    vm.open.set(True)
    settle(view, 8)
    assert view._shown_layers and view._built.nodes["root.tp"].get("fill")[3] == round(0.32 * 255)
    panel = p(view, "")
    assert panel.get("layout_width") == 328.0 and panel.get("fill") == role(view, "surface_container_high") and panel.get("corner_radius") == 28.0
    assert panel.get("role") == "dialog" and panel.get("label") == "Select time"


def test_the_header_shows_the_time_in_twelve_hour_form_with_the_period(tmp_path):
    view, _ = opened(tmp_path)
    assert shown(view) == "02:35"
    assert p(view, "header.period.half[PM]").get("checked") is True
    assert p(view, "header.hour_button.hour_text").get("font_size") == 57.0
    assert (p(view, "header.hour_button").get("layout_width"), p(view, "header.hour_button").get("layout_height")) == (96.0, 80.0)


def test_midnight_shows_twelve(tmp_path):
    view, _ = opened(tmp_path, hour=0, minute=0)
    assert shown(view) == "12:00" and p(view, "header.period.half[AM]").get("checked") is True


def test_the_hour_is_the_part_the_dial_sets_to_begin_with_and_pressing_the_minute_changes_that(tmp_path):
    view, _ = opened(tmp_path)
    assert p(view, "header.hour_button").get("fill") == role(view, "primary_container") and p(view, "header.minute_button").get("fill") == role(view, "surface_container_highest")
    assert dial(view).mode.get() == "hour"
    view.window.simulate("click", node=p(view, "header.minute_button"))
    settle(view, 6)
    assert dial(view).mode.get() == "minute" and p(view, "header.minute_button").get("fill") == role(view, "primary_container")
    assert p(view, "header.hour_button.hour_text").get("fill") == role(view, "on_surface") and p(view, "header.minute_button.minute_text").get("fill") == role(view, "on_primary_container")


def test_the_dial_sets_the_header_and_choosing_an_hour_moves_on_to_the_minutes(tmp_path):
    view, _ = opened(tmp_path)
    assert dial(view).hour.get() == 14 and dial(view).minute.get() == 35
    press_key_on_dial(view, "arrow_up", 2)
    assert shown(view) == "04:35" and dial(view).hour.get() == 16
    dial(view).mode.set("minute")
    settle(view, 4)
    press_key_on_dial(view, "arrow_up")
    assert shown(view).endswith(":40")


def test_the_period_selector_moves_the_hour_by_twelve(tmp_path):
    view, _ = opened(tmp_path)
    view.window.simulate("click", node=p(view, "header.period.half[AM]"))
    settle(view, 6)
    assert shown(view) == "02:35" and dial(view).hour.get() == 2
    view.window.simulate("click", node=p(view, "header.period.half[PM]"))
    settle(view, 6)
    assert dial(view).hour.get() == 14


def test_the_time_is_not_changed_until_ok_is_pressed(tmp_path):
    view, vm = opened(tmp_path)
    press_key_on_dial(view, "arrow_up", 3)
    assert (vm.h.get(), vm.m.get()) == (14, 35)
    view.window.simulate("click", node=p(view, "footer.ok"))
    settle(view, 6)
    assert (vm.h.get(), vm.m.get()) == (17, 35) and vm.open.get() is False and not view._shown_layers


def test_ok_calls_on_ok_after_it_has_set_the_time(tmp_path):
    view, vm = opened(tmp_path, "on_ok: confirmed")
    press_key_on_dial(view, "arrow_up")
    view.window.simulate("click", node=p(view, "footer.ok"))
    settle(view, 6)
    assert vm.log == ["ok"] and vm.h.get() == 15


def test_cancel_escape_and_the_scrim_leave_the_time_alone(tmp_path):
    view, vm = opened(tmp_path)
    press_key_on_dial(view, "arrow_up", 3)
    view.window.simulate("click", node=p(view, "footer.cancel"))
    settle(view, 6)
    assert (vm.h.get(), vm.m.get()) == (14, 35) and vm.open.get() is False
    vm.open.set(True)
    settle(view, 8)
    press_key_on_dial(view, "arrow_up")
    view.window.simulate("key_down", key="escape")
    settle(view, 6)
    assert (vm.h.get(), vm.m.get()) == (14, 35) and vm.open.get() is False
    vm.open.set(True)
    settle(view, 8)
    view.window.simulate("pointer_down", x=5, y=5)
    settle(view, 6)
    assert vm.open.get() is False and (vm.h.get(), vm.m.get()) == (14, 35)


def test_opening_it_again_starts_from_the_time_as_it_now_is(tmp_path):
    view, vm = opened(tmp_path)
    press_key_on_dial(view, "arrow_up", 2)
    view.window.simulate("click", node=p(view, "footer.cancel"))
    settle(view, 6)
    vm.h.set(9)
    vm.m.set(10)
    vm.open.set(True)
    settle(view, 8)
    assert shown(view) == "09:10" and p(view, "header.period.half[AM]").get("checked") is True


def test_the_keyboard_button_swaps_the_dial_for_typed_fields_and_back(tmp_path):
    view, _ = opened(tmp_path)
    button = p(view, "footer.mode_button")
    assert button.get("label") == "Switch to typing"
    view.window.simulate("click", node=button)
    settle(view, 6)
    assert "root.tp.panel.dial" not in view._built.specs and "root.tp.panel.fields" in view._built.specs
    assert p(view, "footer.mode_button").get("label") == "Switch to the clock"
    view.window.simulate("click", node=p(view, "footer.mode_button"))
    settle(view, 6)
    assert "root.tp.panel.dial" in view._built.specs and "root.tp.panel.fields" not in view._built.specs


def test_typing_a_time_and_pressing_ok_sets_it(tmp_path):
    view, vm = opened(tmp_path)
    view.window.simulate("click", node=p(view, "footer.mode_button"))
    settle(view, 6)
    hour = view.node("root.tp.panel.fields.hour_field.box.body.input")
    hour.focus()
    settle(view, 2)
    hour.set(text="")
    view.window.simulate("input", text="9")
    settle(view, 6)
    minute = view.node("root.tp.panel.fields.minute_field.box.body.input")
    minute.focus()
    settle(view, 2)
    minute.set(text="")
    view.window.simulate("input", text="07")
    settle(view, 6)
    view.window.simulate("click", node=p(view, "footer.ok"))
    settle(view, 6)
    assert (vm.h.get(), vm.m.get()) == (21, 7)  # 9:07 PM: the period stayed


def test_a_time_changed_on_the_dial_is_what_the_typed_fields_start_from(tmp_path):
    view, _ = opened(tmp_path)
    press_key_on_dial(view, "arrow_up", 2)
    view.window.simulate("click", node=p(view, "footer.mode_button"))
    settle(view, 6)
    assert view.node("root.tp.panel.fields.hour_field.box.body.input").get("text") == "04"


def test_twenty_four_hour_time_opens_on_the_fields_with_no_dial_and_no_keyboard_button(tmp_path):
    view, vm = opened(tmp_path, "twelve: false")
    assert "root.tp.panel.dial" not in view._built.specs and "root.tp.panel.header" not in view._built.specs
    assert "root.tp.panel.footer.mode_button" not in view._built.specs
    hour = view.node("root.tp.panel.fields.hour_field.box.body.input")
    assert hour.get("text") == "14"
    hour.focus()
    settle(view, 2)
    hour.set(text="")
    view.window.simulate("input", text="22")
    settle(view, 6)
    view.window.simulate("click", node=p(view, "footer.ok"))
    settle(view, 6)
    assert vm.h.get() == 22


def test_letting_go_on_an_hour_moves_the_dial_and_the_header_on_to_the_minutes(tmp_path):
    view, _ = opened(tmp_path)
    node = dial(view).node
    cx, cy = node.get("layout_x") + 128, node.get("layout_y") + 128
    view.window.simulate("pointer_down", x=cx + 90, y=cy)  # the 3 o'clock position
    view.window.simulate("pointer_up", x=cx + 90, y=cy)
    settle(view, 6)
    assert shown(view).startswith("03") and dial(view).mode.get() == "minute"
    assert p(view, "header.minute_button").get("fill") == role(view, "primary_container")
