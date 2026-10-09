"""#186 to #189: one day of a date picker -- ordinary, today, selected and outside the month, in one view."""

import pytest

from tesserae import App, Signal, ViewModel, tokens
from tesserae.shipped import shipped_views


class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.on = Signal(False)
        self.clicks = Signal(0)

    def bump(self):
        self.clicks.set(self.clicks.get() + 1)


def opened(tmp_path, props=""):
    (tmp_path / "Views").mkdir(exist_ok=True)
    lines = "\n    ".join(props.split(", ")) if props else ""
    (tmp_path / "Views" / "Main_View.yaml").write_text(f"""name: main
widget: Container
style: {{width: 200, height: 100, align_content: top_left}}
children:
  - widget: DatePickerDay
    name: d
    day: '9'
    {lines}
    handlers: {{on_click: bump}}
""")
    app = App(root=tmp_path)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    for _ in range(6):
        view.window.advance(16)
    return view, app.bindings.viewmodel_for("main")


def role(view, name):
    return (view._scheme or tokens.BASELINE)[name]


def d(view, part=""):
    return view.node("root.d" + (f".{part}" if part else ""))


def test_it_is_shipped():
    assert "DatePickerDay" in shipped_views()


def test_a_day_is_a_48_pixel_target_with_a_40_pixel_circle_and_the_number_in_body_large(tmp_path):
    view, _ = opened(tmp_path)
    assert (d(view).get("layout_width"), d(view).get("layout_height")) == (48.0, 48.0)
    circle, number = d(view, "circle"), d(view, "circle.number")
    assert (circle.get("layout_width"), circle.get("layout_height")) == (40.0, 40.0) and circle.get("layout_x") == d(view).get("layout_x") + 4
    assert number.get("text") == "9" and number.get("font_size") == 16.0 and number.get("fill") == role(view, "on_surface") and circle.get("fill")[3] == 0


def test_today_is_outlined_in_primary_with_primary_text(tmp_path):
    view, _ = opened(tmp_path, "today: true")
    circle = d(view, "circle")
    assert circle.get("stroke_width") == 1.0 and circle.get("stroke_color") == role(view, "primary") and d(view, "circle.number").get("fill") == role(view, "primary")
    assert d(view).get("current") == "date"


def test_the_selected_day_is_a_primary_circle_with_on_primary_text_and_hides_the_today_outline(tmp_path):
    view, _ = opened(tmp_path, "selected: true, today: true")
    circle = d(view, "circle")
    assert circle.get("fill") == role(view, "primary") and circle.get("stroke_width") == 0.0 and d(view, "circle.number").get("fill") == role(view, "on_primary")
    assert d(view).get("selected") is True


def test_a_day_outside_the_month_is_on_surface_variant(tmp_path):
    view, _ = opened(tmp_path, "outside: true")
    assert d(view, "circle.number").get("fill") == role(view, "on_surface_variant")


def test_a_press_runs_the_handler_and_a_disabled_day_does_not_respond(tmp_path):
    view, vm = opened(tmp_path)
    view.window.simulate("click", node=d(view))
    assert vm.clicks.get() == 1 and d(view).get("role") == "button" and d(view).get("label") == "9"
    (tmp_path / "x").mkdir()
    off, vm2 = opened(tmp_path / "x", "disabled: true")
    off.window.simulate("click", node=d(off))
    assert vm2.clicks.get() == 0 and d(off).get("opacity") < 0.5


def test_one_view_goes_from_one_state_to_another(tmp_path):
    (tmp_path / "Views").mkdir(exist_ok=True)
    (tmp_path / "Views" / "Main_View.yaml").write_text("""name: main
widget: Container
style: {width: 200, height: 100, align_content: top_left}
children:
  - {widget: DatePickerDay, name: d, day: '9', selected: "{{ on }}"}
""")
    app = App(root=tmp_path)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    for _ in range(6):
        view.window.advance(16)
    vm = app.bindings.viewmodel_for("main")
    assert d(view, "circle").get("fill")[3] == 0
    vm.on.set(True)
    for _ in range(20):
        view.window.advance(16)
    assert d(view, "circle").get("fill") == role(view, "primary")
