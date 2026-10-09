"""#186 to #189: the Material 3 modal date picker -- the grid of days, the month, a typed date, Cancel and OK."""

import pytest

from tesserae import App, Signal, ViewModel, tokens
from tesserae.shipped import shipped_views


class VM(ViewModel):
    views = "main"
    start = "2026-10-09"

    def __init__(self):
        super().__init__()
        self.open = Signal(False)
        self.d = Signal(self.start)
        self.log = []

    def confirmed(self):
        self.log.append("ok")


def opened(tmp_path, props="", date="2026-10-09", show=True):
    (tmp_path / "Views").mkdir(exist_ok=True)
    lines = "\n    ".join(props.split(", ")) if props else ""
    (tmp_path / "Views" / "Main_View.yaml").write_text(f"""name: main
widget: Container
style: {{width: 600, height: 700}}
children:
  - widget: DatePicker
    name: dp
    open: "{{{{ open }}}}"
    date: "{{{{ d }}}}"
    {lines}
""")
    VM.start = date
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


def p(view, path=""):
    return view.node("root.dp.panel" + (("." + path) if path else ""))


def day(view, iso):
    return view.node(f"root.dp.panel.grid.day[{iso}]")


def test_it_is_shipped():
    assert {"DatePicker", "DatePickerDay"} <= set(shipped_views())


def test_it_is_a_scrim_with_a_dialog_of_surface_container_high_with_28_pixel_corners(tmp_path):
    view, vm = opened(tmp_path, show=False)
    assert not view._shown_layers
    vm.open.set(True)
    settle(view, 8)
    assert view._shown_layers and view._built.nodes["root.dp"].get("fill")[3] == round(0.32 * 255)
    panel = p(view)
    assert panel.get("fill") == role(view, "surface_container_high") and panel.get("corner_radius") == 28.0 and panel.get("role") == "dialog"


def test_the_header_shows_the_chosen_date_and_the_month_is_named(tmp_path):
    view, _ = opened(tmp_path)
    assert p(view, "header.chosen").get("text") == "Fri, Oct 9" and p(view, "header.chosen").get("font_size") == 32.0
    assert p(view, "month_bar.month").get("text") == "October 2026"


def test_the_grid_is_six_weeks_of_seven_days_starting_on_a_sunday_by_default(tmp_path):
    view, _ = opened(tmp_path)
    days = [k for k in view._built.specs if k.startswith("root.dp.panel.grid.day[") and k.count(".") == 4]
    assert len(days) == 42 and days[0].endswith("[2026-09-27]") and days[-1].endswith("[2026-11-07]")
    first, second = day(view, "2026-09-27"), day(view, "2026-09-28")
    assert second.get("layout_x") == first.get("layout_x") + 48 and day(view, "2026-10-04").get("layout_y") == first.get("layout_y") + 48


def test_weeks_can_start_on_a_monday(tmp_path):
    view, _ = opened(tmp_path, "week_starts: monday")
    days = [k for k in view._built.specs if k.startswith("root.dp.panel.grid.day[") and k.count(".") == 4]
    assert days[0].endswith("[2026-09-28]")
    assert [p(view, f"weekdays.weekday[{k}].initial").get("text") for k in range(7)] == list("MTWTFSS")


def test_the_weekday_initials_start_with_sunday_by_default(tmp_path):
    view, _ = opened(tmp_path)
    assert [p(view, f"weekdays.weekday[{k}].initial").get("text") for k in range(7)] == list("SMTWTFS")


def test_the_chosen_day_is_a_primary_circle_and_days_of_other_months_are_faint(tmp_path):
    view, _ = opened(tmp_path)
    assert day(view, "2026-10-09").get("selected") is True
    assert view.node("root.dp.panel.grid.day[2026-10-09].circle").get("fill") == role(view, "primary")
    assert view.node("root.dp.panel.grid.day[2026-09-27].circle.number").get("fill") == role(view, "on_surface_variant")
    assert view.node("root.dp.panel.grid.day[2026-10-10].circle.number").get("fill") == role(view, "on_surface")


def test_today_is_outlined(tmp_path, monkeypatch):
    from tesserae import expr

    monkeypatch.setitem(expr.BUILTIN_FUNCTIONS, "current_date", lambda: "2026-10-14")
    view, _ = opened(tmp_path)
    c = view.node("root.dp.panel.grid.day[2026-10-14].circle")
    assert c.get("stroke_width") == 1.0 and c.get("stroke_color") == role(view, "primary")


def test_pressing_a_day_chooses_it_in_the_header_but_not_in_the_date_until_ok(tmp_path):
    view, vm = opened(tmp_path)
    view.window.simulate("click", node=day(view, "2026-10-21"))
    settle(view, 6)
    assert p(view, "header.chosen").get("text") == "Wed, Oct 21" and day(view, "2026-10-21").get("selected") is True and day(view, "2026-10-09").get("selected") is False
    assert vm.d.get() == "2026-10-09"
    view.window.simulate("click", node=p(view, "footer.ok"))
    settle(view, 6)
    assert vm.d.get() == "2026-10-21" and vm.open.get() is False and not view._shown_layers


def test_ok_calls_on_ok(tmp_path):
    view, vm = opened(tmp_path, "on_ok: confirmed")
    view.window.simulate("click", node=p(view, "footer.ok"))
    settle(view, 6)
    assert vm.log == ["ok"]


def test_cancel_escape_and_the_scrim_leave_the_date_alone(tmp_path):
    view, vm = opened(tmp_path)
    view.window.simulate("click", node=day(view, "2026-10-21"))
    view.window.simulate("click", node=p(view, "footer.cancel"))
    settle(view, 6)
    assert vm.d.get() == "2026-10-09" and vm.open.get() is False
    vm.open.set(True)
    settle(view, 8)
    assert p(view, "header.chosen").get("text") == "Fri, Oct 9"  # reopened from the date as it is
    view.window.simulate("key_down", key="escape")
    settle(view, 6)
    assert vm.open.get() is False and vm.d.get() == "2026-10-09"


def test_the_month_arrows_move_between_months_and_over_a_year(tmp_path):
    view, _ = opened(tmp_path, date="2026-12-15")
    assert p(view, "month_bar.month").get("text") == "December 2026"
    view.window.simulate("click", node=p(view, "month_bar.next"))
    settle(view, 6)
    assert p(view, "month_bar.month").get("text") == "January 2027" and day(view, "2027-01-01") is not None
    view.window.simulate("click", node=p(view, "month_bar.previous"))
    view.window.simulate("click", node=p(view, "month_bar.previous"))
    settle(view, 6)
    assert p(view, "month_bar.month").get("text") == "November 2026"


def test_choosing_a_day_of_the_next_month_moves_to_that_month(tmp_path):
    view, _ = opened(tmp_path)
    view.window.simulate("click", node=day(view, "2026-11-03"))
    settle(view, 6)
    assert p(view, "month_bar.month").get("text") == "November 2026" and day(view, "2026-11-03").get("selected") is True


def test_days_outside_the_limits_are_disabled_and_do_not_respond(tmp_path):
    view, _ = opened(tmp_path, "earliest: '2026-10-05', latest: '2026-10-20'")
    assert day(view, "2026-10-04").get("disabled") is True and day(view, "2026-10-21").get("disabled") is True and day(view, "2026-10-10").get("disabled") is False
    view.window.simulate("click", node=day(view, "2026-10-04"))
    settle(view, 6)
    assert p(view, "header.chosen").get("text") == "Fri, Oct 9"


def test_no_date_shows_none_and_starts_on_the_month_of_today(tmp_path, monkeypatch):
    from tesserae import expr

    monkeypatch.setitem(expr.BUILTIN_FUNCTIONS, "current_date", lambda: "2027-02-03")
    view, _ = opened(tmp_path, date="")
    assert p(view, "header.chosen").get("text") == "No date" and p(view, "month_bar.month").get("text") == "February 2027"


def test_the_arrows_move_the_focus_around_the_grid(tmp_path):
    view, _ = opened(tmp_path)
    day(view, "2026-10-09").focus()
    settle(view, 2)
    view.window.simulate("key_down", key="arrow_right")
    settle(view, 4)
    assert day(view, "2026-10-10").get("focused") is True


def test_the_keyboard_button_swaps_the_grid_for_a_typed_date(tmp_path):
    view, vm = opened(tmp_path)
    view.window.simulate("click", node=p(view, "header.mode_button"))
    settle(view, 6)
    assert "root.dp.panel.grid" not in view._built.specs and "root.dp.panel.entry" in view._built.specs
    box = view.node("root.dp.panel.entry.box.body.input")
    assert box.get("text") == "2026-10-09"
    box.focus()
    settle(view, 2)
    box.set(text="")
    view.window.simulate("input", text="20271225")
    settle(view, 8)
    assert box.get("text") == "2027-12-25" and p(view, "header.chosen").get("text") == "Sat, Dec 25"
    view.window.simulate("click", node=p(view, "footer.ok"))
    settle(view, 6)
    assert vm.d.get() == "2027-12-25"


def test_a_typed_date_that_does_not_exist_is_left_out(tmp_path):
    view, _ = opened(tmp_path)
    view.window.simulate("click", node=p(view, "header.mode_button"))
    settle(view, 6)
    box = view.node("root.dp.panel.entry.box.body.input")
    box.focus()
    settle(view, 2)
    box.set(text="")
    view.window.simulate("input", text="20261340")
    settle(view, 8)
    assert p(view, "header.chosen").get("text") == "Fri, Oct 9"
