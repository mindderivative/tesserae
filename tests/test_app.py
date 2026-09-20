"""Real, repeatable coverage for `tesserae.App` -- registration,
name-collision handling, and `show()`'s own real "first call opens,
later calls switch" behavior, mirroring `tre`'s own established pytest
conventions (`tmp_path` for a throwaway view file, no `App.run()` in
these tests -- `tre`'s own `test_tracing.py` documents the real reason a
second real render-loop call in the same process is best avoided; the
one live end-to-end proof lives in `examples/counter/app.py`).
"""

import pytest

from tesserae import App, Signal, View, ViewModel


def write_view(tmp_path, yaml, name="view.yaml"):
    path = tmp_path / name
    path.write_text(yaml)
    return str(path)


SIMPLE_VIEW = """
id: root
kind: Rect
style: {width: 40, height: 20, background: "#112233"}
"""


class SimpleVM(ViewModel):
    def __init__(self, view):
        self.value = Signal(0)
        super().__init__(view)


def test_register_then_show_opens_a_real_window(tmp_path):
    path = write_view(tmp_path, SIMPLE_VIEW)
    view = View(path)
    vm = SimpleVM(view)

    app = App(width=200, height=100, title="Test App")
    app.register("main", view, vm)
    window = app.show("main")

    assert window is not None
    assert app.current == "main"


def test_registering_the_same_name_twice_raises(tmp_path):
    path = write_view(tmp_path, SIMPLE_VIEW)
    view = View(path)
    vm = SimpleVM(view)

    app = App()
    app.register("main", view, vm)
    with pytest.raises(ValueError):
        app.register("main", view, vm)


def test_show_before_register_raises_a_clear_key_error():
    app = App()
    with pytest.raises(KeyError):
        app.show("nope")


def test_show_switches_the_same_live_window_on_the_second_call(tmp_path):
    """The real, decisive proof: a second `show()` call must return the
    *same* `Window` object as the first (proving it called `Window.
    show_view`, not a second `Window.from_view` -- which would open a
    second, independent window instead of switching the existing one).
    """
    path_a = write_view(tmp_path, SIMPLE_VIEW, name="a.yaml")
    path_b = write_view(
        tmp_path,
        'id: root\nkind: Rect\nstyle: {width: 60, height: 30, background: "#332211"}\n',
        name="b.yaml",
    )
    view_a = View(path_a)
    view_b = View(path_b)
    vm_a = SimpleVM(view_a)
    vm_b = SimpleVM(view_b)

    app = App()
    app.register("a", view_a, vm_a)
    app.register("b", view_b, vm_b)

    window_first = app.show("a")
    window_second = app.show("b")

    assert window_first is window_second
    assert app.current == "b"


def test_run_before_show_raises_a_clear_runtime_error():
    app = App()
    with pytest.raises(RuntimeError):
        app.run()
