"""M65 (#13): an app-level state store. `App(state=...)` holds any object
(a class of `Signal`s, say); a ViewModel on the app's window reaches it
as `self.state` and the app as `self.app`, found through its view's
window, with no constructor change; a binding reads it as
`{{ state.<name>.get() }}`. An attribute a ViewModel sets itself wins.
"""

import importlib.util
import sys

import pytest
import tre

from tesserae import App, Signal, View, ViewModel, instantiate


class AppState:
    def __init__(self):
        self.user = Signal("Ada")
        self.visits = Signal(0)


def _label_view(binding="{{ state.user.get() }}"):
    return {"id": "root", "kind": "Container", "style": {"width": 200, "height": 60},
            "children": [{"id": "label", "kind": "Text", "text": {"content": "", "font_family": "Roboto", "font_size": 14},
                          "style": {"foreground": "#000000", "width": 180, "height": 20},
                          "bindings": {"text": binding}}]}


class Plain(ViewModel):
    pass


class Visitor(ViewModel):
    def visit(self):
        self.state.visits.update(lambda n: n + 1)
        self.state.user.set(f"visited {self.state.visits.get()}")
        return self.app


def test_screens_share_the_apps_state_through_bindings():
    app = App(state=AppState())
    home = View(_label_view(), window=app.window)
    Plain(home)
    settings = View(_label_view(), window=app.window)
    Plain(settings)
    assert home.node("label").get("text") == settings.node("label").get("text") == "Ada"
    app.state.user.set("Grace")  # one write, every screen
    assert home.node("label").get("text") == settings.node("label").get("text") == "Grace"


def test_a_viewmodel_reaches_the_app_and_its_state():
    app = App(state=AppState())
    vm = Visitor(View(_label_view(), window=app.window))
    assert vm.app is app and vm.state is app.state
    assert vm.visit() is app and app.state.visits.get() == 1
    assert vm._view.node("label").get("text") == "visited 1"


def test_state_can_be_set_later_and_app_of_finds_the_app():
    app = App()
    view = View(_label_view("{{ 'none' }}"), window=app.window)
    assert App.of(view) is app and App.of(app.window) is app and App.of(tre.Window(width=10, height=10)) is None
    vm = Plain(view)
    with pytest.raises(AttributeError, match=r"Plain.state: the app has no state -- give App\(state=...\)"):
        vm.state
    app.state = AppState()
    assert vm.state.user.get() == "Ada"


def test_a_viewmodels_own_app_or_state_wins():
    app = App(state=AppState())

    class Own(ViewModel):
        def __init__(self, view, app):
            self.app = app  # as the shell examples do
            self.state = Signal("mine")
            super().__init__(view)

    mine = object()
    vm = Own(View(_label_view("{{ state.get() }}"), window=app.window), mine)
    assert vm.app is mine and vm._view.node("label").get("text") == "mine"


def test_the_constructor_can_reach_the_app_before_super_init():
    app = App(state=AppState())

    class Greeting(ViewModel):
        def __init__(self, view):
            with pytest.raises(AttributeError, match=r"Greeting.state: call super\(\).__init__\(view\) first"):
                self.state
            self.greeting = Signal("Hello, " + App.of(view).state.user.get())
            super().__init__(view)

    vm = Greeting(View(_label_view("{{ greeting.get() }}"), window=app.window))
    assert vm._view.node("label").get("text") == "Hello, Ada"


def test_on_the_class_they_are_the_descriptors():  # for help() and inspect
    assert type(ViewModel.app).__name__ == type(Plain.state).__name__ == "_FromApp"


def test_off_an_apps_window_there_is_no_app():
    vm = Plain(View(_label_view("{{ 'x' }}")))  # its own window, no App
    with pytest.raises(AttributeError, match=r"Plain.app: its view isn't on an App's window"):
        vm.app
    with pytest.raises(AttributeError, match=r"Plain.state: its view isn't on an App's window"):
        vm.state
    assert not hasattr(vm, "state")


def test_each_app_has_its_own_state():
    one, two = App(state=AppState()), App(state=AppState())
    a, b = Plain(View(_label_view(), window=one.window)), Plain(View(_label_view(), window=two.window))
    one.state.user.set("One")
    assert a._view.node("label").get("text") == "One" and b._view.node("label").get("text") == "Ada"


def test_a_component_reaches_it_too(tmp_path):
    (tmp_path / "Badge_View.yaml").write_text(
        "id: badge\nkind: Text\ntext: {content: '', font_family: Roboto, font_size: 14}\n"
        "style: {foreground: '#000000', width: 100, height: 20}\nbindings: {text: '{{ state.user.get() }}'}\n")
    vm_file = tmp_path / "Badge_ViewModel.py"
    vm_file.write_text("from tesserae import ViewModel\nclass BadgeViewModel(ViewModel):\n    pass\n")
    spec = importlib.util.spec_from_file_location(f"Badge_ViewModel_{id(tmp_path)}", vm_file)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    app = App(state=AppState())
    host = View({"id": "root", "kind": "Container", "style": {"width": 200, "height": 60}}, window=app.window)
    component, vm = instantiate(host, tmp_path / "Badge_View.yaml", module.BadgeViewModel, host.root)
    assert vm.state is app.state and component.node("badge").get("text") == "Ada"
    app.state.user.set("Lin")
    assert component.node("badge").get("text") == "Lin"
