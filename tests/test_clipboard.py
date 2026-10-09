"""#223: `copy(text)` and `paste()` in a handler -- the OS clipboard through tre."""

import pytest

from tesserae import App, Signal, ViewModel


class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.name = Signal("Ada")
        self.pasted = Signal("")
        self.ok = Signal(None)


VIEW = """name: main
widget: Container
style: {flex_direction: vertical, width: 200, height: 100}
children:
  - {widget: Container, name: copy, handlers: {on_click: "ok = copy(name)"}}
  - {widget: Container, name: paste, handlers: {on_click: "pasted = paste()"}}
  - {widget: Container, name: both, handlers: {on_click: "copy('x' + name); pasted = paste()"}}
  - {widget: Container, name: number, handlers: {on_click: "copy(42)"}}
  - {widget: Container, name: bad, handlers: {on_click: "copy([1])"}}
"""


def opened(tmp_path, text=VIEW):
    (tmp_path / "Views").mkdir(exist_ok=True)
    (tmp_path / "Views" / "Main_View.yaml").write_text(text)
    app = App(root=tmp_path)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    return view, app.bindings.viewmodel_for("main")


def fire(view, name):
    next(i for i in view.handle.composition.walk() if i.id == f"root.{name}").fire("on_click")


def test_copy_puts_text_on_the_clipboard_and_says_whether_it_could(tmp_path):
    view, vm = opened(tmp_path)
    fire(view, "copy")
    assert view.window.read_clipboard() == "Ada" and vm.ok.get() is True


def test_paste_reads_it_back(tmp_path):
    view, vm = opened(tmp_path)
    view.window.write_clipboard("from elsewhere")
    fire(view, "paste")
    assert vm.pasted.get() == "from elsewhere"


def test_an_empty_clipboard_pastes_as_empty_text(tmp_path):
    view, vm = opened(tmp_path)
    view.window.write_clipboard("")
    vm.pasted.set("old")
    fire(view, "paste")
    assert vm.pasted.get() == ""


def test_copy_then_paste_in_one_handler(tmp_path):
    view, vm = opened(tmp_path)
    fire(view, "both")
    assert vm.pasted.get() == "xAda"


def test_a_number_is_copied_as_text(tmp_path):
    view, _ = opened(tmp_path)
    fire(view, "number")
    assert view.window.read_clipboard() == "42"


def test_something_that_is_not_text_is_a_mistake_naming_the_call(tmp_path):
    view, _ = opened(tmp_path)
    with pytest.raises(Exception, match=r"copy\(\) failed: ValueError: copy\(\) takes text"):
        fire(view, "bad")


def test_the_view_accepts_the_actions_when_it_is_checked(tmp_path):
    app = App(root=tmp_path)
    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Main_View.yaml").write_text(VIEW)
    app.bind(VM)
    app.open_view("Main")
    assert app.check() == []


def test_a_clipboard_with_no_text_or_that_cannot_be_reached_pastes_as_empty_text():
    from tesserae.composed import builtin_actions

    class W:
        def read_clipboard(self):
            return None

    resolve = builtin_actions(lambda: type("V", (), {"window": W()})())
    assert resolve("paste")() == ""


def test_a_clipboard_that_cannot_be_written_says_false(tmp_path):
    from tesserae.composed import builtin_actions

    class W:
        def write_clipboard(self, text):
            return False

    resolve = builtin_actions(lambda: type("V", (), {"window": W()})())
    assert resolve("copy")("x") is False
