"""A ScrollView with `orientation: horizontal` scrolls sideways (tre 0.5.6): a row of children, an offset along x, and `right`/`left` for the way it went."""

import pytest

from tesserae import App, Signal, ViewModel
from tesserae.spec.build import SpecBuildError


class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.x = Signal(0.0)
        self.start = Signal(True)
        self.end = Signal(False)
        self.way = Signal("none")


def opened(tmp_path, props="orientation: horizontal"):
    (tmp_path / "Views").mkdir(exist_ok=True)
    (tmp_path / "Views" / "Main_View.yaml").write_text(f"""name: main
widget: Container
style: {{flex_direction: vertical, align_content: top_left, width: 300, height: 200}}
children:
  - widget: ScrollView
    name: strip
    {props}
    scroll_offset: "{{{{ x }}}}"
    at_top: "{{{{ start }}}}"
    at_end: "{{{{ end }}}}"
    scroll_direction: "{{{{ way }}}}"
    style: {{width: 100, height: 60}}
    children:
      - {{widget: Container, name: a, style: {{width: 150, height: 40, background: primary}}}}
      - {{widget: Container, name: b, style: {{width: 150, height: 40, background: secondary}}}}
      - {{widget: Container, name: c, style: {{width: 150, height: 40, background: tertiary}}}}
""")
    app = App(root=tmp_path)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    for _ in range(3):
        view.window.advance(16)
    return view, app.bindings.viewmodel_for("main")


def test_the_children_are_a_row_and_the_view_scrolls_sideways(tmp_path):
    view, vm = opened(tmp_path)
    strip = view._built.outer["root.strip"]
    assert strip.get("orientation") == "horizontal"
    assert view.node("root.strip.b").get("layout_x") == view.node("root.strip.a").get("layout_x") + 150
    strip.set(scroll_offset=150.0)
    view.window.advance(16)
    assert strip.get("scroll_offset") == 150.0


def test_a_wheel_to_the_side_moves_it_and_the_outputs_follow(tmp_path):
    view, vm = opened(tmp_path)
    strip = view._built.outer["root.strip"]
    view.window.simulate("wheel", node=strip, delta_x=60.0, delta_y=0.0)
    view.window.advance(16)
    assert vm.x.get() == 60.0 and vm.way.get() == "right" and vm.start.get() is False and vm.end.get() is False
    view.window.simulate("wheel", node=strip, delta_x=-20.0, delta_y=0.0)
    view.window.advance(16)
    assert vm.way.get() == "left"
    strip.set(scroll_offset=350.0)
    view.window.advance(16)
    assert vm.end.get() is True


def test_a_bound_offset_moves_the_view(tmp_path):
    view, vm = opened(tmp_path)
    vm.x.set(90.0)
    view.window.advance(16)
    assert view._built.outer["root.strip"].get("scroll_offset") == 90.0


def test_vertical_is_still_the_default(tmp_path):
    view, vm = opened(tmp_path, props="")
    assert view._built.outer["root.strip"].get("orientation") == "vertical"


def test_another_orientation_is_refused(tmp_path):
    with pytest.raises((SpecBuildError, ValueError, Exception), match="vertical or horizontal|orientation"):
        opened(tmp_path, props="orientation: diagonal")
