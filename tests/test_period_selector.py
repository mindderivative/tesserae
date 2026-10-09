"""#191, #192: the AM / PM selector -- two halves in a frame, the chosen one tertiary_container."""

import pytest

from tesserae import App, Signal, ViewModel, tokens
from tesserae.shipped import shipped_views


class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.p = Signal("AM")


def opened(tmp_path, props=""):
    (tmp_path / "Views").mkdir(exist_ok=True)
    lines = "\n    ".join(props.split(", ")) if props else ""
    (tmp_path / "Views" / "Main_View.yaml").write_text(f"""name: main
widget: Container
style: {{width: 200, height: 200, align_content: top_left}}
children:
  - widget: PeriodSelector
    name: ps
    period: "{{{{ p }}}}"
    {lines}
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


def half(view, p):
    return view.node(f"root.ps.half[{p}]")


def settle(view, n=20):
    for _ in range(n):
        view.window.advance(16)


def test_it_is_shipped():
    assert "PeriodSelector" in shipped_views()


def test_it_is_52_by_80_with_two_40_pixel_halves_in_a_one_pixel_outline_with_8_pixel_corners(tmp_path):
    view, _ = opened(tmp_path)
    frame = view.node("root.ps")
    assert (frame.get("layout_width"), frame.get("layout_height")) == (52.0, 80.0) and frame.get("corner_radius") == 8.0
    assert frame.get("stroke_width") == 1.0 and frame.get("stroke_color") == role(view, "outline")
    assert (half(view, "AM").get("layout_height"), half(view, "PM").get("layout_height")) == (40.0, 40.0)
    assert half(view, "PM").get("layout_y") == half(view, "AM").get("layout_y") + 40


def test_the_chosen_half_is_tertiary_container_and_the_other_is_plain(tmp_path):
    view, vm = opened(tmp_path)
    assert half(view, "AM").get("fill") == role(view, "tertiary_container") and half(view, "PM").get("fill")[3] == 0
    assert view.node("root.ps.half[AM].label").get("fill") == role(view, "on_tertiary_container")
    assert view.node("root.ps.half[PM].label").get("fill") == role(view, "on_surface_variant")
    vm.p.set("PM")
    settle(view)
    assert half(view, "PM").get("fill") == role(view, "tertiary_container") and half(view, "AM").get("fill")[3] == 0


def test_pressing_a_half_chooses_it_and_each_is_a_radio_that_knows_if_it_is_checked(tmp_path):
    view, vm = opened(tmp_path)
    assert [half(view, p).get("role") for p in ("AM", "PM")] == ["radio", "radio"] and half(view, "AM").get("checked") is True
    view.window.simulate("click", node=half(view, "PM"))
    settle(view)
    assert vm.p.get() == "PM" and half(view, "PM").get("checked") is True and half(view, "AM").get("checked") is False


def test_one_tab_stop_and_the_arrows_choose(tmp_path):
    view, vm = opened(tmp_path)
    assert [half(view, p).get("tab_index") for p in ("AM", "PM")] == [0, -1]
    half(view, "AM").focus()
    view.window.simulate("key_down", key="arrow_down")
    settle(view, 6)
    assert vm.p.get() == "PM"
    view.window.simulate("key_down", key="arrow_up")
    settle(view, 6)
    assert vm.p.get() == "AM"


def test_a_disabled_selector_does_not_respond(tmp_path):
    view, vm = opened(tmp_path, "disabled: true")
    view.window.simulate("click", node=half(view, "PM"))
    settle(view, 6)
    assert vm.p.get() == "AM"


def test_it_works_with_no_binding_at_all(tmp_path):
    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Main_View.yaml").write_text("name: main\nwidget: Container\nstyle: {width: 100, height: 100}\nchildren:\n  - {widget: PeriodSelector, name: ps}\n")
    app = App(root=tmp_path)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    settle(view, 4)
    view.window.simulate("click", node=half(view, "PM"))
    settle(view, 6)
    assert half(view, "PM").get("fill") == role(view, "tertiary_container")
