"""#146: the Material 3 snackbar -- a message that goes by itself, with an action and a close, announced politely."""

import pytest

from tesserae import App, Signal, ViewModel, tokens
from tesserae.shipped import shipped_views


class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.open = Signal(False)
        self.log = []

    def undone(self):
        self.log.append("undone")

    def closed(self):
        self.log.append("closed")


def opened(tmp_path, props="", show=True, message="Message deleted"):
    (tmp_path / "Views").mkdir(exist_ok=True)
    lines = "\n    ".join(props.split(", ")) if props else ""
    (tmp_path / "Views" / "Main_View.yaml").write_text(f"""name: main
widget: Container
style: {{width: 600, height: 400}}
children:
  - {{widget: Container, name: page, style: {{width: 600, height: 400, background: surface}}}}
  - widget: Snackbar
    name: sb
    open: "{{{{ open }}}}"
    message: '{message}'
    {lines}
""")
    app = App(root=tmp_path, width=600, height=400)
    app.bind(VM)
    view = app.open_view("Main")
    vm = app.bindings.viewmodel_for("main")
    app.show("main")
    settle(view, 4)
    if show:
        vm.open.set(True)
        settle(view, 6)
    return view, vm


def role(view, name):
    return (view._scheme or tokens.BASELINE)[name]


def settle(view, n=30):
    for _ in range(n):
        view.window.advance(16)


def sb(view, part=""):
    return view.node("root.sb" + (f".{part}" if part else ""))


def test_it_is_shipped():
    assert "Snackbar" in shipped_views()


def test_it_is_closed_until_open_and_then_sits_at_the_bottom_start_16_pixels_in(tmp_path):
    view, vm = opened(tmp_path, show=False)
    assert not view._shown_layers
    vm.open.set(True)
    settle(view, 6)
    assert view._shown_layers
    assert (sb(view).get("layout_x"), sb(view).get("layout_y")) == (16.0, 400 - 16 - 48.0)
    assert sb(view).get("layout_width") == 344.0


def test_it_is_inverse_surface_with_4_pixel_corners_at_level_three_and_the_message_is_inverse_on_surface(tmp_path):
    view, _ = opened(tmp_path)
    assert sb(view).get("fill") == role(view, "inverse_surface") and sb(view).get("corner_radius") == 4.0 and sb(view).get("shadows")
    msg = sb(view, "bar.message")
    assert msg.get("text") == "Message deleted" and msg.get("fill") == role(view, "inverse_on_surface") and msg.get("font_size") == 14.0
    assert msg.get("layout_x") == sb(view).get("layout_x") + 16


def test_a_long_message_wraps_to_two_lines_and_the_bar_grows_to_68(tmp_path):
    view, _ = opened(tmp_path, message="word " * 30)
    assert sb(view).get("layout_height") >= 68.0 and sb(view).get("layout_width") <= 560.0


def test_it_goes_by_itself_after_the_duration_and_calls_on_close(tmp_path):
    view, vm = opened(tmp_path, "duration: 1000, on_close: closed")
    settle(view, 40)  # 640 ms
    assert vm.open.get() is True
    settle(view, 40)
    assert vm.open.get() is False and not view._shown_layers and vm.log == ["closed"]


def test_it_lasts_four_seconds_by_default(tmp_path):
    view, vm = opened(tmp_path)
    settle(view, 200)  # 3.2 s
    assert vm.open.get() is True
    settle(view, 70)
    assert vm.open.get() is False


def test_a_duration_of_zero_keeps_it_until_it_is_closed(tmp_path):
    view, vm = opened(tmp_path, "duration: 0")
    settle(view, 600)
    assert vm.open.get() is True


def test_the_pointer_over_it_holds_off_the_close_and_leaving_restarts_the_time(tmp_path):
    view, vm = opened(tmp_path, "duration: 1000")
    x, y = sb(view).get("layout_x") + 10, sb(view).get("layout_y") + 10
    view.window.simulate("pointer_move", x=x, y=y)
    settle(view, 150)
    assert vm.open.get() is True
    view.window.simulate("pointer_move", x=300, y=100)
    settle(view, 40)
    assert vm.open.get() is True
    settle(view, 40)
    assert vm.open.get() is False


def test_the_action_runs_its_handler_and_closes_it(tmp_path):
    view, vm = opened(tmp_path, "action: Undo, on_action: undone, on_close: closed")
    act = sb(view, "bar.action")
    assert act.get("role") == "button" and act.get("label") == "Undo" and sb(view, "bar.action.action_text").get("fill") == role(view, "inverse_primary")
    view.window.simulate("click", node=act)
    settle(view, 4)
    assert vm.log == ["undone", "closed"] and vm.open.get() is False


def test_a_close_button_closes_it(tmp_path):
    view, vm = opened(tmp_path, "closable: true, on_close: closed")
    close = sb(view, "bar.close")
    assert close.get("label") == "Close" and sb(view, "bar.close.close_icon").get("fill") == role(view, "inverse_on_surface")
    view.window.simulate("click", node=close)
    settle(view, 4)
    assert vm.log == ["closed"] and vm.open.get() is False


def test_it_is_not_modal_and_a_press_elsewhere_does_not_close_it(tmp_path):
    view, vm = opened(tmp_path, "duration: 0")
    view.window.simulate("pointer_down", x=300, y=100)
    view.window.simulate("key_down", key="escape")
    settle(view, 4)
    assert vm.open.get() is True and view.node("root.page").get("layout_width") == 600.0


def test_it_is_announced_politely_as_an_alert(tmp_path):
    view, _ = opened(tmp_path)
    bar = sb(view, "bar")
    assert bar.get("role") == "alert" and bar.get("live") == "polite" and bar.get("label") == "Message deleted"


def test_it_can_be_centred_and_follows_the_window(tmp_path):
    view, _ = opened(tmp_path, "centered: true")
    assert sb(view).get("layout_x") == (600 - 344) / 2


def test_opening_it_again_restarts_the_time(tmp_path):
    view, vm = opened(tmp_path, "duration: 1000")
    settle(view, 45)
    vm.open.set(False)
    settle(view, 4)
    vm.open.set(True)
    settle(view, 45)
    assert vm.open.get() is True
    settle(view, 40)
    assert vm.open.get() is False


# -- the host: one after another ----------------------------------------------------------------------------------------------


class HostVM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.queue = Signal([])
        self.chosen = Signal("")


def host(tmp_path, props=""):
    (tmp_path / "Views").mkdir(exist_ok=True)
    lines = "\n    ".join(props.split(", ")) if props else ""
    (tmp_path / "Views" / "Main_View.yaml").write_text(f"""name: main
widget: Container
style: {{width: 600, height: 400}}
children:
  - widget: SnackbarHost
    name: h
    messages: "{{{{ queue }}}}"
    chosen: "{{{{ chosen }}}}"
    {lines}
""")
    app = App(root=tmp_path, width=600, height=400)
    app.bind(HostVM)
    view = app.open_view("Main")
    app.show("main")
    settle(view, 4)
    return view, app.bindings.viewmodel_for("main")


def text_showing(view):
    return [view.node(k).get("text") for k in view._built.specs if k.endswith(".bar.message") and "current" in k]


def test_nothing_shows_while_the_list_is_empty(tmp_path):
    view, _ = host(tmp_path)
    assert not view._shown_layers


def test_messages_show_one_after_another_each_for_its_time(tmp_path):
    view, vm = host(tmp_path)
    vm.queue.set([{"message": "One", "duration": 500}, {"message": "Two", "duration": 500}])
    settle(view, 6)
    assert text_showing(view) == ["One"] and len(view._shown_layers) == 1
    settle(view, 40)
    assert text_showing(view) == ["Two"] and vm.queue.get() == [{"message": "Two", "duration": 500}]
    settle(view, 40)
    assert text_showing(view) == [] and vm.queue.get() == [] and not view._shown_layers


def test_a_message_added_while_one_shows_waits_its_turn(tmp_path):
    view, vm = host(tmp_path)
    vm.queue.set([{"message": "One", "duration": 500}])
    settle(view, 6)
    vm.queue.set(vm.queue.get() + [{"message": "Two", "duration": 500}])
    settle(view, 6)
    assert text_showing(view) == ["One"]
    settle(view, 40)
    assert text_showing(view) == ["Two"]


def test_pressing_an_action_reports_its_value_and_moves_on(tmp_path):
    view, vm = host(tmp_path)
    vm.queue.set([{"message": "Deleted", "action": "Undo", "value": "undo", "duration": 0}, {"message": "Next", "duration": 0}])
    settle(view, 6)
    action = next(view.node(k) for k in view._built.specs if k.endswith(".bar.action") and "current" in k)
    view.window.simulate("click", node=action)
    settle(view, 6)
    assert vm.chosen.get() == "undo" and text_showing(view) == ["Next"]


def test_a_close_button_skips_to_the_next(tmp_path):
    view, vm = host(tmp_path, "closable: true")
    vm.queue.set([{"message": "One", "duration": 0}, {"message": "Two", "duration": 0}])
    settle(view, 6)
    close = next(view.node(k) for k in view._built.specs if k.endswith(".bar.close") and "current" in k)
    view.window.simulate("click", node=close)
    settle(view, 6)
    assert text_showing(view) == ["Two"]
