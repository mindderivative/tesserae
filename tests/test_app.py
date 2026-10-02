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


def test_run_with_screens_registered_but_none_shown_raises_a_clear_runtime_error(tmp_path):
    app = App()
    app.register("a", View(write_view(tmp_path, SIMPLE_VIEW)), None)
    with pytest.raises(RuntimeError, match=r"called before show\(\): screens are registered but none is showing"):
        app.run()


@pytest.mark.skipif(sys.platform == "darwin", reason="no drawn border on macOS: the OS draws the frame")
def test_an_undecorated_apps_border_is_not_something_to_show(tmp_path):
    """The window border is a child of the window's root, but not content."""
    app = App(decorations=False)
    app.register("a", View(write_view(tmp_path, SIMPLE_VIEW)), None)
    assert app._border is not None and len(app.window.root.children()) == 1
    with pytest.raises(RuntimeError, match="none is showing"):
        app.run()


class _FakeTre:
    """tre's App, so `run()` can be called without a GPU or a display."""

    ran = []
    queued = []  # what `thread_handle().call_soon` was given, in order
    on_run = None  # called while the loop "runs", as the loop would run what was queued

    def add_window(self, window):
        pass

    def thread_handle(self):
        return type("Handle", (), {"call_soon": staticmethod(lambda fn: _FakeTre.queued.append(fn))})()

    def run(self, max_frames=None):
        self.ran.append(max_frames)
        if _FakeTre.on_run is not None:
            _FakeTre.on_run()


@pytest.fixture
def fake_tre(monkeypatch):
    monkeypatch.setattr("tesserae.app._TreApp", _FakeTre)
    _FakeTre.ran.clear()
    _FakeTre.queued.clear()
    _FakeTre.on_run = None
    return _FakeTre


def test_an_empty_window_runs(fake_tre):
    """0.3.1: an app built in Python starts empty, so a window with no screens is allowed."""
    App(width=200, height=100).run(max_frames=2)
    App(decorations=False).run(max_frames=3)  # and its border alone is no reason to refuse
    assert fake_tre.ran == [2, 3]


def test_run_starts_for_a_window_with_nodes_added_by_calls(fake_tre):
    app = App(width=200, height=100)
    app.window.root.add_child(app.window.create("text", text="Hi", font_size=16, width=40, height=20,
                                                fill=(255, 255, 255, 255)))
    app.run(max_frames=3)
    assert fake_tre.ran == [3]


def test_nodes_added_by_calls_are_content_even_with_a_screen_registered(fake_tre, tmp_path):
    app = App(decorations=False)  # its border is a second child, not the reason it runs
    app.register("a", View(write_view(tmp_path, SIMPLE_VIEW)), None)
    app.window.root.add_child(app.window.create("box", width=10, height=10, fill=(0, 0, 0, 255)))
    app.run(max_frames=1)
    assert fake_tre.ran == [1]


def test_run_starts_for_a_shell_before_any_screen(fake_tre):
    from tesserae.shell import AppShell
    from tesserae.widgets import top_app_bar

    app = App(width=400, height=300)
    app.use_shell(AppShell(app.window, top_bar=top_app_bar(app.window, "Studio", width=400)))
    app.run(max_frames=1)
    assert fake_tre.ran == [1]


@pytest.mark.parametrize("with_a_node", [True, False])
def test_a_code_only_app_draws_frames_in_a_real_window(tmp_path, with_a_node):
    """The real thing, in a subprocess (a second real `App.run()` in one pytest
    process can break unrelated tests); skipped where no frame renders. Empty
    is the walk-through's first step, so it is run for real too."""
    import os
    import subprocess
    import textwrap

    script = tmp_path / "code_only.py"
    script.write_text(textwrap.dedent("""
        import sys
        from tesserae import App

        app = App(width=200, height=100, title="code only")
        if sys.argv[1] == "node":
            app.window.root.add_child(app.window.create("text", text="Hi", font_size=16, width=40, height=20,
                                                        fill=(255, 255, 255, 255)))
        app.run()
    """))
    report = tmp_path / "frames.txt"
    env = {**os.environ, "TESSERAE_MAX_FRAMES": "5", "TESSERAE_FRAMES_REPORT": str(report)}
    result = subprocess.run([sys.executable, str(script), "node" if with_a_node else "empty"], env=env,
                            capture_output=True, text=True, timeout=60)
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


def _ticks(fake_tre):
    return [fn for fn in fake_tre.queued if getattr(fn, "__name__", "") == "tick"]


def test_the_keepalive_is_off_by_default(fake_tre):
    """0.3.2: tre 0.5.1 lets threads run in an idle window, so a hot-reload watcher needs no tick."""
    App().run()
    App().run(hot_reload=True)
    App().run(max_frames=5, hot_reload=True)
    assert _ticks(fake_tre) == []


@pytest.mark.parametrize("kwargs, ticks", [
    ({"keepalive": True}, 1),                      # on its own, for anything that wants the loop woken
    ({"keepalive": True, "hot_reload": True}, 1),
    ({"keepalive": 0.5}, 1),
    ({"keepalive": False, "hot_reload": True}, 0),
    ({"keepalive": None}, 0),                      # 0.3.1's "follow hot_reload" spelling: now just off
])
def test_the_keepalive_can_be_chosen(fake_tre, kwargs, ticks):
    App().run(**kwargs)
    assert len(_ticks(fake_tre)) == ticks


@pytest.mark.parametrize("bad", [0, -1, 0.0, "yes", [1]])
def test_a_wrong_keepalive_is_a_one_line_error(fake_tre, bad):
    with pytest.raises(ValueError, match=r"keepalive must be True, False or a positive number of seconds"):
        App().run(keepalive=bad)


def test_a_tick_sleeps_queues_the_next_and_stops_when_the_run_ends(fake_tre, monkeypatch):
    slept = []
    monkeypatch.setattr("tesserae.app.time.sleep", slept.append)
    fake_tre.on_run = lambda: _ticks(fake_tre)[0]()  # the loop runs the first tick
    App().run(keepalive=0.25)
    assert slept == [0.25]  # it slept (letting other threads run) ...
    assert len(_ticks(fake_tre)) == 2  # ... and queued the next
    after_the_run = _ticks(fake_tre)[1]
    slept.clear()
    fake_tre.queued.clear()
    after_the_run()  # a tick that reaches a loop that is over does nothing
    assert slept == [] and fake_tre.queued == []


def test_the_interval_rules():
    from tesserae.app import KEEPALIVE_INTERVAL, _keepalive_interval

    assert KEEPALIVE_INTERVAL == 0.02
    assert _keepalive_interval(None) is None and _keepalive_interval(False) is None
    assert _keepalive_interval(True) == 0.02
    assert _keepalive_interval(0.25) == 0.25 and _keepalive_interval(2) == 2.0
