"""M48 Phase 2: `App.run(hot_reload=True)` watches every screen built from
a file -- `load()`ed, or `build_view()`ed and given to `register()` --
taking the file from the view itself (Q1); a screen built from a spec is
named in the log instead (Q2).

As in `test_theme_reload.py`, a `FakeHandle` stands in for `tre`'s loop:
the watcher queues each reload, and the test runs it on this thread.
"""

import importlib.util
import queue
import sys
from pathlib import Path

import pytest

import tesserae
from tesserae import App, Signal, ViewModel
from tesserae.spec import ViewWatcher

VIEW = ('id: root\nkind: Container\nchildren:\n'
        '  - id: title\n    kind: Text\n    text: {{content: "", font_family: Roboto, font_size: 14}}\n'
        '    style: {{foreground: "#000000", width: {width}, height: 20}}\n'
        '    bindings: {{text: "{{{{ title.get() }}}}"}}\n')


class FakeHandle:
    def __init__(self):
        self.queued: "queue.Queue" = queue.Queue()

    def call_soon(self, fn):
        self.queued.put(fn)


class HomeViewModel(ViewModel):
    """Needs the app, as `examples/multi_screen/`'s do -- the reason to
    `register()` rather than `load()`."""

    def __init__(self, view, app):
        self.app = app
        self.title = Signal("Home")
        super().__init__(view)


def _write(path: Path, width: int = 100) -> Path:
    path.write_text(VIEW.format(width=width))
    return path


def _edit_until_queued(handle: FakeHandle, path: Path, width: int, attempts: int = 40):
    for _ in range(attempts):
        _write(path, width)
        try:
            return handle.queued.get(timeout=0.25)
        except queue.Empty:
            continue
    raise AssertionError(f"the watcher never queued a reload for {path}")


@pytest.fixture
def watching():
    started = []

    def start(app: App):
        handle = FakeHandle()
        started.extend(app._start_watchers(handle))
        return handle

    yield start
    for watcher in started:
        watcher.stop()


def test_a_registered_screen_reloads_in_place_keeping_its_viewmodel(tmp_path, watching):
    app = App()
    path = _write(tmp_path / "Home_View.yaml")
    view = app.build_view(path)
    vm = HomeViewModel(view, app)
    app.register("Home", view, vm)
    app.show("Home")
    node = view.node("title")
    vm.title.set("Inbox")
    handle = watching(app)
    reload = _edit_until_queued(handle, path, width=240)
    assert node.get("width") == 100.0  # nothing applied until the loop runs it
    reload()
    assert view.node("title") == node and node.get("width") == 240.0
    assert node.get("text") == "Inbox"  # the binding kept its live value
    vm.title.set("Sent")
    assert node.get("text") == "Sent" and vm.app is app  # still wired, same ViewModel


def test_a_view_built_on_its_own_from_a_file_and_registered_is_watched_too(tmp_path):
    """`register()` rebuilds it in the app's window; it keeps its file."""
    app = App()
    path = _write(tmp_path / "Home_View.yaml")
    view = tesserae.View(path)
    app.register("Home", view, HomeViewModel(view, app))
    watchers = app._start_watchers(FakeHandle())
    try:
        assert [type(w) for w in watchers] == [ViewWatcher] and path in watchers[0].files
    finally:
        for w in watchers:
            w.stop()


def _loaded_viewmodel(tmp_path: Path):
    (tmp_path / "Loaded_ViewModel.py").write_text(
        "from tesserae import Signal, ViewModel\n\n\nclass LoadedViewModel(ViewModel):\n"
        "    def __init__(self, view):\n        self.title = Signal('x')\n        super().__init__(view)\n")
    spec = importlib.util.spec_from_file_location("Loaded_ViewModel", tmp_path / "Loaded_ViewModel.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.LoadedViewModel


def test_loaded_and_registered_screens_are_counted_and_a_spec_built_one_is_named(tmp_path, logs):
    app = App()
    app.load(_write(tmp_path / "Loaded_View.yaml"), _loaded_viewmodel(tmp_path))
    registered = app.build_view(_write(tmp_path / "Home_View.yaml"))
    app.register("Home", registered, HomeViewModel(registered, app))
    app.register("Scratch", tesserae.View({"id": "root", "kind": "Container"}), None)
    watchers = app._start_watchers(FakeHandle())
    try:
        watched = sorted(f.name for w in watchers for f in w.files if f.name.endswith("_View.yaml"))
        assert watched == ["Home_View.yaml", "Loaded_View.yaml"]
        info = logs.messages("INFO")
        assert "hot reload: screen 'Scratch' isn't watched -- it was built from a spec, not a file" in info
        assert "hot reload on: watching 2 screen(s) and 0 theme/stylesheet file(s)" in info
    finally:
        for w in watchers:
            w.stop()
