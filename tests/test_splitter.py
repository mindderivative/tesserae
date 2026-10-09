"""#203: `widget: Splitter` -- two panes and a handle you drag, move with the keys, and (optionally) double click to collapse."""

import pytest

from tesserae import App, Signal, ViewModel
from tesserae.spec.nodes import LoadError


class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.split = Signal(0.5)


def view_text(props="", orientation="horizontal"):
    return f"""name: main
widget: Container
style: {{width: 416, height: 200}}
children:
  - widget: Splitter
    name: sp
    orientation: {orientation}
    {props}
    style: {{width: 416, height: 200}}
    children:
      - {{widget: Container, name: left, style: {{background: primary, flex: fill}}}}
      - {{widget: Container, name: right, style: {{background: secondary, flex: fill}}}}
"""


def opened(tmp_path, props="", orientation="horizontal"):
    (tmp_path / "Views").mkdir(exist_ok=True)
    (tmp_path / "Views" / "Main_View.yaml").write_text(view_text(props, orientation))
    app = App(root=tmp_path, width=500, height=400)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    for _ in range(3):
        view.window.advance(16)
    return view, app.bindings.viewmodel_for("main")


def pane(view, part, key="layout_width"):
    return view._built.nodes[f"root.sp.{part}"].get(key)


def handle(view):
    return view._built.nodes["root.sp.handle"]


def drag(view, to_fraction, key="window_x", horizontal=True):
    """Press the handle, move the pointer so the handle's middle is `to_fraction` of the way along the panes' room, release."""
    h = handle(view)
    first = view._built.nodes["root.sp.first"]
    start = first.get("layout_x" if horizontal else "layout_y")
    room = 416.0 - 16.0 if horizontal else 200.0 - 16.0
    cx, cy = (h.get("layout_x") + 8, h.get("layout_y") + 20) if horizontal else (h.get("layout_x") + 20, h.get("layout_y") + 8)
    view.window.simulate("pointer_down", h, x=8 if horizontal else 20, y=20 if horizontal else 8)
    target = start + to_fraction * room + 8
    if horizontal:
        view.window.simulate("pointer_move", x=target, y=cy)
        view.window.simulate("pointer_up", x=target, y=cy)
    else:
        view.window.simulate("pointer_move", x=cx, y=target)
        view.window.simulate("pointer_up", x=cx, y=target)
    for _ in range(3):
        view.window.advance(16)


def test_two_panes_share_the_room_less_the_handle(tmp_path):
    view, _ = opened(tmp_path)
    assert pane(view, "first") == 200.0 and pane(view, "second") == 200.0 and handle(view).get("layout_width") == 16.0
    assert view.node("root.sp.left").get("layout_width") == 200.0


def test_the_position_sets_the_split(tmp_path):
    view, _ = opened(tmp_path, "position: 0.25")
    assert pane(view, "first") == 100.0 and pane(view, "second") == 300.0


def test_a_vertical_one_stacks_the_panes(tmp_path):
    view, _ = opened(tmp_path, "position: 0.5", "vertical")
    assert pane(view, "first", "layout_height") == 92.0 and pane(view, "second", "layout_height") == 92.0
    assert handle(view).get("layout_height") == 16.0 and handle(view).get("cursor") == "row_resize"


def test_the_handle_is_a_slider_with_a_cursor_and_a_tab_stop(tmp_path):
    view, _ = opened(tmp_path, "label: Resize the sidebar")
    h = handle(view)
    assert (h.get("role"), h.get("label")) == ("slider", "Resize the sidebar") and h.get("focusable") is True
    assert (h.get("value"), h.get("value_min"), h.get("value_max")) == (0.5, 0.0, 1.0) and h.get("cursor") == "col_resize"


def test_dragging_the_handle_moves_the_split(tmp_path):
    view, _ = opened(tmp_path)
    drag(view, 0.25)
    assert pane(view, "first") == pytest.approx(100.0, abs=1) and pane(view, "second") == pytest.approx(300.0, abs=1)
    assert handle(view).get("value") == pytest.approx(0.25, abs=0.01)


def test_dragging_writes_a_bound_signal_and_following_it_moves_the_panes(tmp_path):
    view, vm = opened(tmp_path, 'position: "{{ split }}"')
    drag(view, 0.75)
    assert vm.split.get() == pytest.approx(0.75, abs=0.01) and pane(view, "first") == pytest.approx(300.0, abs=1)
    vm.split.set(0.1)
    view.window.advance(16)
    assert pane(view, "first") == pytest.approx(40.0, abs=1)


def test_a_vertical_drag_uses_the_y(tmp_path):
    view, _ = opened(tmp_path, "", "vertical")
    drag(view, 0.25, horizontal=False)
    assert pane(view, "first", "layout_height") == pytest.approx(46.0, abs=1)


def test_the_pointer_must_have_gone_down_on_the_handle_to_drag(tmp_path):
    view, vm = opened(tmp_path, 'position: "{{ split }}"')
    view.window.simulate("pointer_move", x=300, y=100)
    view.window.advance(16)
    assert vm.split.get() == 0.5


def test_the_minimum_sizes_hold(tmp_path):
    view, vm = opened(tmp_path, 'position: "{{ split }}"\n    min_first: 80\n    min_second: 120')
    drag(view, 0.0)
    assert pane(view, "first") >= 79.5 and vm.split.get() == pytest.approx(0.2, abs=0.01)
    drag(view, 1.0)
    assert pane(view, "second") >= 119.5 and vm.split.get() == pytest.approx(0.7, abs=0.01)


def test_the_arrow_keys_home_and_end(tmp_path):
    view, vm = opened(tmp_path, 'position: "{{ split }}"')
    handle(view).focus()
    view.window.simulate("key_down", key="arrow_right")
    assert vm.split.get() == pytest.approx(0.55)
    view.window.simulate("key_down", key="arrow_left")
    view.window.simulate("key_down", key="arrow_left")
    assert vm.split.get() == pytest.approx(0.45)
    view.window.simulate("key_down", key="end")
    assert vm.split.get() == 1.0
    view.window.simulate("key_down", key="home")
    assert vm.split.get() == 0.0
    view.window.simulate("key_down", key="a")
    assert vm.split.get() == 0.0


def test_a_vertical_one_uses_up_and_down(tmp_path):
    view, vm = opened(tmp_path, 'position: "{{ split }}"', "vertical")
    handle(view).focus()
    view.window.simulate("key_down", key="arrow_down")
    assert vm.split.get() == pytest.approx(0.55)
    view.window.simulate("key_down", key="arrow_right")
    assert vm.split.get() == pytest.approx(0.55)  # not this axis


def test_a_screen_reader_can_increment_decrement_and_set(tmp_path):
    view, vm = opened(tmp_path, 'position: "{{ split }}"')
    h = handle(view)
    view.window.simulate("a11y_action", h, action="increment")
    assert vm.split.get() == pytest.approx(0.55)
    view.window.simulate("a11y_action", h, action="decrement")
    view.window.simulate("a11y_action", h, action="decrement")
    assert vm.split.get() == pytest.approx(0.45)
    view.window.simulate("a11y_action", h, action="set_value", value=0.9)
    assert vm.split.get() == pytest.approx(0.9)


def test_an_unbound_position_still_moves(tmp_path):
    view, _ = opened(tmp_path)
    handle(view).focus()
    view.window.simulate("key_down", key="end")
    view.window.advance(16)
    assert pane(view, "first") == 400.0 and pane(view, "second") == 0.0


def test_a_double_click_closes_and_reopens_a_collapsible_one(tmp_path):
    view, vm = opened(tmp_path, 'position: "{{ split }}"\n    collapsible: true')
    vm.split.set(0.3)
    view.window.advance(16)
    h = handle(view)
    for _ in range(2):
        view.window.simulate("pointer_down", h, x=8, y=20)
        view.window.simulate("pointer_up", x=h.get("layout_x") + 8, y=h.get("layout_y") + 20)
    view.window.advance(16)
    assert vm.split.get() == 0.0 and pane(view, "first") == 0.0
    for _ in range(2):
        view.window.simulate("pointer_down", h, x=8, y=20)
        view.window.simulate("pointer_up", x=h.get("layout_x") + 8, y=h.get("layout_y") + 20)
    view.window.advance(16)
    assert vm.split.get() == pytest.approx(0.3) and pane(view, "first") == pytest.approx(120.0, abs=1)  # where it was before it closed


def test_a_double_click_does_nothing_unless_collapsible(tmp_path):
    view, vm = opened(tmp_path, 'position: "{{ split }}"')
    h = handle(view)
    for _ in range(2):
        view.window.simulate("pointer_down", h, x=8, y=20)
        view.window.simulate("pointer_up", x=h.get("layout_x") + 8, y=h.get("layout_y") + 20)
    assert vm.split.get() == 0.5


def test_two_clicks_far_apart_in_time_are_not_a_double_click(tmp_path, monkeypatch):
    import tesserae.composed as composed

    now = [100.0]
    monkeypatch.setattr(composed.time, "monotonic", lambda: now[0])
    view, vm = opened(tmp_path, 'position: "{{ split }}"\n    collapsible: true')
    h = handle(view)
    for at in (100.0, 101.0):  # a second apart
        now[0] = at
        view.window.simulate("pointer_down", h, x=8, y=20)
        view.window.simulate("pointer_up", x=h.get("layout_x") + 8, y=h.get("layout_y") + 20)
    assert vm.split.get() == 0.5
    now[0] = 101.2  # and a third, soon after the second
    view.window.simulate("pointer_down", h, x=8, y=20)
    view.window.simulate("pointer_up", x=h.get("layout_x") + 8, y=h.get("layout_y") + 20)
    assert vm.split.get() == 0.0


@pytest.mark.parametrize("children", [
    "      - {widget: Container, name: a}\n", "      - {widget: Container, name: a}\n      - {widget: Container, name: b}\n      - {widget: Container, name: c}\n",
])
def test_a_splitter_needs_exactly_two_panes(tmp_path, children):
    text = view_text()
    text = text[:text.index("    children:")] + "    children:\n" + children
    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Main_View.yaml").write_text(text)
    app = App(root=tmp_path)
    app.bind(VM)
    with pytest.raises(LoadError, match="two panes"):
        app.open_view("Main")


def test_a_bad_orientation_is_a_load_error(tmp_path):
    with pytest.raises(LoadError, match="orientation"):
        opened(tmp_path, "", "diagonal")


def test_a_splitter_with_no_room_for_its_panes_cannot_be_dragged(tmp_path):
    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Main_View.yaml").write_text(view_text('position: "{{ split }}"').replace("style: {width: 416, height: 200}\n    children", "style: {width: 16, height: 200}\n    children"))
    app = App(root=tmp_path, width=500, height=400)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    view.window.advance(16)
    h = handle(view)
    view.window.simulate("pointer_down", h, x=8, y=20)
    view.window.simulate("pointer_move", x=h.get("layout_x") + 30, y=h.get("layout_y") + 20)
    view.window.simulate("pointer_up", x=h.get("layout_x") + 30, y=h.get("layout_y") + 20)
    assert app.bindings.viewmodel_for("main").split.get() == 0.5
