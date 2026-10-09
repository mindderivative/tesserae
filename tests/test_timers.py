"""#217: `after`, `every` and `cancel` -- timers on the frame loop, for Python and for a view's handlers."""

import pytest

from tesserae import App, Signal, ViewModel
from tesserae.spec.nodes import LoadError, parse_view
from tesserae.timers import Timers


def window():
    import tre

    return tre.Window(width=100, height=100)


def run(win, ms, step=10):
    for _ in range(ms // step):
        win.advance(step)


def test_after_runs_once_when_its_time_is_up():
    win, log = window(), []
    Timers(win).after(100, lambda: log.append("a"))
    run(win, 60)
    assert log == []
    run(win, 100)
    run(win, 200)
    assert log == ["a"]


def test_every_repeats_until_cancelled():
    win, log = window(), []
    timers = Timers(win)
    timers.every(50, lambda: log.append(1), name="tick")
    run(win, 260)
    count = len(log)
    assert 3 <= count <= 5 and timers.running("tick")
    assert timers.cancel("tick") and not timers.running("tick")
    run(win, 300)
    assert len(log) == count and not timers.cancel("tick")


def test_a_timer_of_the_same_name_replaces_the_first():
    win, log = window(), []
    timers = Timers(win)
    timers.after(100, lambda: log.append("first"), name="n")
    run(win, 60)
    timers.after(100, lambda: log.append("second"), name="n")  # restarted: a debounce
    run(win, 60)
    assert log == []
    run(win, 100)
    assert log == ["second"]


def test_after_forgets_its_name_once_it_has_run():
    win = window()
    timers = Timers(win)
    name = timers.after(20, lambda: None)
    assert timers.running(name)
    run(win, 100)
    assert not timers.running(name)


def test_cancel_all_stops_every_timer():
    win, log = window(), []
    timers = Timers(win)
    timers.after(50, lambda: log.append("a"))
    timers.every(50, lambda: log.append("e"))
    timers.cancel_all()
    run(win, 300)
    assert log == []


def test_a_timer_can_cancel_itself_from_inside():
    win, log = window(), []
    timers = Timers(win)

    def tick():
        log.append(1)
        timers.cancel("t")

    timers.every(20, tick, name="t")
    run(win, 200)
    assert log == [1]


@pytest.mark.parametrize("ms", [-1, "100", None, True, float("nan"), float("inf")])
def test_a_bad_time_is_refused(ms):
    with pytest.raises(ValueError, match="the time is milliseconds, 0 or more"):
        Timers(window()).after(ms, lambda: None)


def test_something_to_run_and_a_name_are_checked():
    with pytest.raises(ValueError, match="needs something to run"):
        Timers(window()).every(10, "no")
    with pytest.raises(ValueError, match="a timer's name is text"):
        Timers(window()).after(10, lambda: None, name=3)
    with pytest.raises(ValueError, match="a timer's name is text"):
        Timers(window()).after(10, lambda: None, name="")


def test_zero_milliseconds_fires_on_a_frame_not_at_once():
    win, log = window(), []
    Timers(win).after(0, lambda: log.append(1))
    assert log == []
    run(win, 50)
    assert log == [1]


# -- in a view's handlers ---------------------------------------------------------------------------------------------------


class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.shown = Signal(False)
        self.count = Signal(0)
        self.log = []

    def bump(self):
        self.count.set(self.count.get() + 1)
        self.log.append("bump")


def opened(tmp_path, body):
    (tmp_path / "Views").mkdir(exist_ok=True)
    (tmp_path / "Views" / "Main_View.yaml").write_text(
        "name: main\nwidget: Container\nstyle: {flex_direction: vertical, width: 200, height: 100}\nchildren:\n" + body)
    app = App(root=tmp_path)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    return view, app.bindings.viewmodel_for("main")


def click(view, name):
    node = next(i for i in view.handle.composition.walk() if i.id == name)
    node.fire("on_click")


def test_a_handler_can_start_a_timer_that_sets_a_signal(tmp_path):
    view, vm = opened(tmp_path, "  - {widget: Container, name: b, handlers: {on_click: \"shown = True; after(100, 'shown = False')\"}}\n")
    click(view, "root.b")
    assert vm.shown.get() is True
    run(view.window, 60)
    assert vm.shown.get() is True
    run(view.window, 100)
    assert vm.shown.get() is False


def test_every_calls_a_viewmodel_method_and_cancel_stops_it(tmp_path):
    view, vm = opened(tmp_path, "  - {widget: Container, name: go, handlers: {on_click: \"every(40, 'bump', 'ticker')\"}}\n"
                                "  - {widget: Container, name: stop, handlers: {on_click: \"cancel('ticker')\"}}\n")
    click(view, "root.go")
    run(view.window, 200)
    seen = vm.count.get()
    assert seen >= 3
    click(view, "root.stop")
    run(view.window, 200)
    assert vm.count.get() == seen


def test_a_name_is_the_scopes_as_a_local_name_is(tmp_path):
    view, vm = opened(tmp_path, "  - {widget: Container, name: a, handlers: {on_click: \"after(100, 'bump', 't')\"}}\n"
                                "  - {widget: Container, name: b, handlers: {on_click: \"after(100, 'bump', 't')\"}}\n"
                                "  - widget: Container\n    for: n in [1, 2]\n    key: n\n    name: item\n"
                                "    handlers: {on_click: \"after(100, 'bump', 't')\"}\n")
    click(view, "root.a")
    click(view, "root.b")  # the same view, the same name: one timer, restarted
    run(view.window, 200)
    assert vm.log == ["bump"]
    vm.log.clear()
    items = [i for i in view.handle.composition.walk() if i.id.startswith("root.item")]
    assert len(items) == 2
    for item in items:  # two iterations, two scopes, two timers
        item.fire("on_click")
    run(view.window, 200)
    assert vm.log == ["bump", "bump"]


def test_timers_stop_when_the_view_closes(tmp_path):
    view, vm = opened(tmp_path, "  - {widget: Container, name: go, handlers: {on_click: \"every(40, 'bump')\"}}\n")
    click(view, "root.go")
    run(view.window, 100)
    view.close()
    seen = len(vm.log)
    run(view.window, 200)
    assert len(vm.log) == seen


def test_a_timer_does_not_run_for_a_widget_that_has_gone(tmp_path):
    view, vm = opened(tmp_path, "  - {widget: Container, name: go, if: count < 1, handlers: {on_click: \"after(100, 'bump'); count += 1\"}}\n")
    click(view, "root.go")
    view.window.advance(16)
    run(view.window, 300)
    assert vm.log == []  # the widget that started it left when count changed


def test_a_mistake_in_a_literal_action_is_found_when_the_view_loads():
    with pytest.raises(LoadError, match="not available in a handler"):
        parse_view("widget: Rect\nhandlers:\n  on_click: \"after(100, 'if x: pass')\"\n", "T_View.yaml")
    parse_view("widget: Rect\nhandlers:\n  on_click: \"after(100, 'a = 1')\"\n", "T_View.yaml")


def test_closing_the_view_cancels_timers_started_from_python(tmp_path):
    view, _ = opened(tmp_path, "  - {widget: Container, name: c}\n")
    log = []
    view.timers.every(20, lambda: log.append(1))
    run(view.window, 100)
    assert log
    view.close()
    seen = len(log)
    run(view.window, 200)
    assert len(log) == seen


@pytest.mark.parametrize("call", ["after(100)", "after(100, 'a = 1', 'n')", "every(100, 'a = 1')", "cancel('n')"])
def test_calls_the_loader_can_read_are_accepted(call):
    parse_view(f"widget: Rect\nhandlers:\n  on_click: \"{call}\"\n", "T_View.yaml")


def test_a_mistake_in_every_is_found_at_load_too():
    with pytest.raises(LoadError, match="not available in a handler"):
        parse_view("widget: Rect\nhandlers:\n  on_click: \"every(100, 'if x: pass')\"\n", "T_View.yaml")
