"""A view takes a `handler` parameter: the caller's action or statements, run in the caller's scope when the view calls the parameter by name."""

import pytest

from tesserae import App, Signal, ViewModel
from tesserae.spec.nodes import LoadError

CALLEE = """name: callee
params:
  on_done: {type: handler}
widget: Container
style: {width: 100, height: 40, background: primary}
handlers: {on_click: "on_done()"}
"""


class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.count = Signal(0)
        self.log = []

    def noted(self):
        self.log.append("noted")


def opened(tmp_path, call):
    (tmp_path / "Views").mkdir(exist_ok=True)
    (tmp_path / "Views" / "Callee_View.yaml").write_text(CALLEE)
    (tmp_path / "Views" / "Main_View.yaml").write_text(
        f"name: main\nwidget: Container\nstyle: {{width: 300, height: 100}}\nchildren:\n  - {call}\n")
    app = App(root=tmp_path)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    view.window.advance(16)
    return view, app.bindings.viewmodel_for("main")


def test_statements_run_in_the_callers_names(tmp_path):
    view, vm = opened(tmp_path, '{widget: Callee, name: c, on_done: "count = count + 1"}')
    view.window.simulate("click", node=view.node("root.c"))
    view.window.simulate("click", node=view.node("root.c"))
    assert vm.count.get() == 2


def test_an_action_name_runs_the_callers_action(tmp_path):
    view, vm = opened(tmp_path, "{widget: Callee, name: c, on_done: noted}")
    view.window.simulate("click", node=view.node("root.c"))
    assert vm.log == ["noted"]


def test_a_parameter_the_caller_left_out_does_nothing(tmp_path):
    view, vm = opened(tmp_path, "{widget: Callee, name: c}")
    view.window.simulate("click", node=view.node("root.c"))
    assert vm.count.get() == 0 and vm.log == []


def test_a_loop_variable_is_in_the_handler(tmp_path):
    view, vm = opened(tmp_path, '{widget: Callee, name: c, for: "n in [5, 7]", key: n, on_done: "count = count + n"}')
    view.window.simulate("click", node=view.node("root.c[7]"))
    assert vm.count.get() == 7


def test_a_mistake_in_the_statements_is_a_load_error_at_the_call(tmp_path):
    with pytest.raises(LoadError):
        opened(tmp_path, '{widget: Callee, name: c, on_done: "count = = 1"}')
