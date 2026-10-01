"""Real, repeatable coverage for `tesserae.App` -- registration,
name-collision handling, `show()`'s own real "first call opens, later
calls switch" behavior, and `load()`'s own real `*_View.yaml`/
`*_ViewModel.py` naming-convention enforcement -- mirroring `tre`'s own
established pytest conventions (`tmp_path` for a throwaway view file, no
`App.run()` in these tests -- `tre`'s own `test_tracing.py` documents
the real reason a second real render-loop call in the same process is
best avoided; the one live end-to-end proof lives in
`examples/counter/app.py`/`examples/multi_screen/app.py`).
"""

import importlib.util
import sys

import pytest

from tesserae import App, Signal, View, ViewModel


def write_view(tmp_path, yaml, name="view.yaml"):
    path = tmp_path / name
    path.write_text(yaml)
    return str(path)


def load_viewmodel_class(tmp_path, filename, class_name):
    """Writes a real, importable `*ViewModel.py`-shaped module to disk
    and imports it for real -- `App.load()`'s own naming check reads a
    class's *actual* defining file via `inspect.getfile`, so a class
    merely defined inline in this test module (whose own filename is
    `test_app.py`, not `*_ViewModel.py`) can't stand in for the real
    thing the way `SimpleVM` below does for the non-`load()` tests.
    """
    path = tmp_path / filename
    path.write_text(
        f"from tesserae import Signal, ViewModel\n\n\n"
        f"class {class_name}(ViewModel):\n"
        f"    def __init__(self, view):\n"
        f"        self.value = Signal(0)\n"
        f"        super().__init__(view)\n"
    )
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return getattr(module, class_name)


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


def test_run_with_nothing_to_show_raises_a_clear_runtime_error():
    app = App()
    with pytest.raises(RuntimeError, match=r"nothing to display: show\(\) a screen, or add nodes to app\.window\.root"):
        app.run()


def test_an_undecorated_apps_border_is_not_something_to_show():
    """The window border is a child of the window's root, but not content."""
    app = App(decorations=False)
    assert app._border is not None and len(app.window.root.children()) == 1
    with pytest.raises(RuntimeError, match="nothing to display"):
        app.run()


class _FakeTre:
    """tre's App, so `run()` can be called without a GPU or a display."""

    ran = []

    def add_window(self, window):
        pass

    def thread_handle(self):
        return type("Handle", (), {"call_soon": staticmethod(lambda fn: None)})()

    def run(self, max_frames=None):
        self.ran.append(max_frames)


def test_run_starts_for_a_window_with_nodes_added_by_calls(monkeypatch):
    """0.3.1: an app built in Python needs no screen: nodes on the window will do."""
    monkeypatch.setattr("tesserae.app._TreApp", _FakeTre)
    _FakeTre.ran.clear()
    app = App(width=200, height=100)
    app.window.root.add_child(app.window.create("text", text="Hi", font_size=16, width=40, height=20,
                                                fill=(255, 255, 255, 255)))
    app.run(max_frames=3)
    assert _FakeTre.ran == [3]


def test_run_starts_for_an_undecorated_app_with_nodes_added_by_calls(monkeypatch):
    monkeypatch.setattr("tesserae.app._TreApp", _FakeTre)
    _FakeTre.ran.clear()
    app = App(decorations=False)  # its border is a second child, not the reason it runs
    app.window.root.add_child(app.window.create("box", width=10, height=10, fill=(0, 0, 0, 255)))
    app.run(max_frames=1)
    assert _FakeTre.ran == [1]


def test_run_starts_for_a_shell_before_any_screen(monkeypatch):
    from tesserae.shell import AppShell
    from tesserae.widgets import top_app_bar

    monkeypatch.setattr("tesserae.app._TreApp", _FakeTre)
    _FakeTre.ran.clear()
    app = App(width=400, height=300)
    app.use_shell(AppShell(app.window, top_bar=top_app_bar(app.window, "Studio", width=400)))
    app.run(max_frames=1)  # nothing shown yet, but the shell is on the window
    assert _FakeTre.ran == [1]


def test_a_code_only_app_draws_frames_in_a_real_window(tmp_path):
    """The real thing, in a subprocess (a second real `App.run()` in one pytest
    process can break unrelated tests); skipped where no frame renders."""
    import subprocess
    import textwrap

    script = tmp_path / "code_only.py"
    script.write_text(textwrap.dedent("""
        from tesserae import App

        app = App(width=200, height=100, title="code only")
        app.window.root.add_child(app.window.create("text", text="Hi", font_size=16, width=40, height=20,
                                                    fill=(255, 255, 255, 255)))
        app.run()
    """))
    report = tmp_path / "frames.txt"
    env = {**__import__("os").environ, "TESSERAE_MAX_FRAMES": "5", "TESSERAE_FRAMES_REPORT": str(report)}
    result = subprocess.run([sys.executable, str(script)], env=env, capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stderr
    if report.read_text() == "0":
        pytest.skip("no display reachable -- App.run() rendered no frames")
    assert int(report.read_text()) >= 5


def test_load_registers_a_valid_pair_under_the_inferred_prefix(tmp_path):
    view_path = write_view(tmp_path, SIMPLE_VIEW, name="Counter_View.yaml")
    vm_cls = load_viewmodel_class(tmp_path, "Counter_ViewModel.py", "CounterViewModel")

    app = App()
    app.load(view_path, vm_cls)
    window = app.show("Counter")

    assert window is not None
    assert app.current == "Counter"


def test_load_accepts_an_explicit_name_override(tmp_path):
    view_path = write_view(tmp_path, SIMPLE_VIEW, name="Counter_View.yaml")
    vm_cls = load_viewmodel_class(tmp_path, "Counter_ViewModel.py", "CounterViewModel")

    app = App()
    app.load(view_path, vm_cls, name="main_counter")
    window = app.show("main_counter")

    assert window is not None


def test_load_rejects_a_view_file_missing_the_required_suffix(tmp_path):
    view_path = write_view(tmp_path, SIMPLE_VIEW, name="Counter.yaml")
    vm_cls = load_viewmodel_class(tmp_path, "Counter_ViewModel.py", "CounterViewModel")

    app = App()
    with pytest.raises(ValueError, match="_View.yaml"):
        app.load(view_path, vm_cls)


def test_load_rejects_a_viewmodel_file_missing_the_required_suffix(tmp_path):
    view_path = write_view(tmp_path, SIMPLE_VIEW, name="Counter_View.yaml")
    vm_cls = load_viewmodel_class(tmp_path, "counter_vm.py", "CounterViewModel")

    app = App()
    with pytest.raises(ValueError, match="_ViewModel.py"):
        app.load(view_path, vm_cls)


def test_load_rejects_mismatched_view_and_viewmodel_prefixes(tmp_path):
    view_path = write_view(tmp_path, SIMPLE_VIEW, name="Counter_View.yaml")
    vm_cls = load_viewmodel_class(tmp_path, "Settings_ViewModel.py", "SettingsViewModel")

    app = App()
    with pytest.raises(ValueError, match="prefix"):
        app.load(view_path, vm_cls)


def test_load_with_no_component_usage_still_works_unchanged(tmp_path):
    """Real regression proof: `App.load()` now constructs via `tesserae.
    spec.load_view` instead of `tre.View` directly -- a view with zero
    `component:` usage must still load exactly as it always did
    (`load_view`'s own real "true no-op" design)."""
    view_path = write_view(tmp_path, SIMPLE_VIEW, name="Counter_View.yaml")
    vm_cls = load_viewmodel_class(tmp_path, "Counter_ViewModel.py", "CounterViewModel")

    app = App()
    view, vm = app.load(view_path, vm_cls)

    assert view.node("root") is not None


COMPONENT_USING_VIEW = """
id: root
kind: Container
style: {width: 300, height: 200}
children:
  - id: save_button
    component: ButtonFilled
    with: {label: Save, width: 120, height: 40, corner_radius: 20}
"""


def test_load_genuinely_expands_component_usage(tmp_path):
    """Real, distinguishing proof that `App.load()` now applies
    `component:` macro-expansion, not just that it doesn't crash on a
    plain view: before this change, a `component:`-using view would
    fail with `tre`'s own schema error (`component` is not a real
    `WidgetSpec` field, `#[serde(deny_unknown_fields)]`) -- confirming
    `tre` saw the raw, unexpanded YAML. After this change, the same
    view instead fails later, at MD3 color resolution (`Button_
    Component.yaml`'s own `background: primary`, with no `theme_seed`
    given -- `App` has no theme-related API of its own yet, a real,
    separate, pre-existing gap unrelated to this change) -- proving
    `component:`/`with:` were genuinely replaced with real `WidgetSpec`
    content before `tre` ever parsed it.
    """
    view_path = write_view(tmp_path, COMPONENT_USING_VIEW, name="Save_View.yaml")
    vm_cls = load_viewmodel_class(tmp_path, "Save_ViewModel.py", "SaveViewModel")

    app = App()
    with pytest.raises(ValueError, match="unknown color identifier"):
        app.load(view_path, vm_cls)
