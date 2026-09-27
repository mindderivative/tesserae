"""M51 Phase 3: hot reload for components added at run time (M51 Q1-Q3).

One `ComponentWatcher` per component file, shared by its live instances
(a `Repeater`'s rows, say): an edit rebuilds the spec once and each row
reconciles in place, keeping its node, its ViewModel and its bound
values (Q1). A component added while hot reload runs is watched too
(Q2). A bad edit leaves every row as it was and fails once (Q3).

As in `test_register_reload.py`, a `FakeHandle` stands in for `tre`'s
loop for the threaded tests; the rest use `poll()`.
"""

import importlib.util
import queue
import sys

import pytest

from tesserae import App, View, instantiate
from tesserae.spec.watch import ComponentWatcher

HOST = """
id: root
kind: Container
style: {flex_direction: vertical, width: 300, height: 400}
children:
  - id: rows
    kind: Container
    style: {flex_direction: vertical, width: 280, height: 380}
"""

ROW = """
id: row
kind: Container
style: {{width: {width}, height: 32}}
children:
  - id: label
    kind: Text
    text: {{content: "", font_family: Roboto, font_size: 14}}
    style: {{foreground: "#000000", width: {width}, height: 20}}
    bindings: {{text: "{{{{ label.get() }}}}"}}
"""

ROW_VM = '''
from tesserae import Signal, ViewModel


class {name}ViewModel(ViewModel):
    def __init__(self, view, label="row"):
        self.label = Signal(label)
        super().__init__(view)
'''


class FakeHandle:
    def __init__(self):
        self.queued: "queue.Queue" = queue.Queue()

    def call_soon(self, fn):
        self.queued.put(fn)


def _component(tmp_path, name="Row", width=200):
    view = tmp_path / f"{name}_View.yaml"
    view.write_text(ROW.format(width=width))
    vm_file = tmp_path / f"{name}_ViewModel.py"
    vm_file.write_text(ROW_VM.format(name=name))
    spec = importlib.util.spec_from_file_location(f"{name}_ViewModel_{id(tmp_path)}", vm_file)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # the naming check finds the class's file through it
    spec.loader.exec_module(module)
    return view, getattr(module, f"{name}ViewModel")


def _host_file(tmp_path):
    (tmp_path / "Host_View.yaml").write_text(HOST)
    return tmp_path / "Host_View.yaml"


def _rows(host, path, vm_cls, n):
    return [instantiate(host, path, vm_cls, host.node("rows"), label=f"row {i}") for i in range(n)]


def _widths(rows):
    return [component.node("label").get("width") for component, _ in rows]


def test_an_edit_reloads_every_row_in_place_keeping_viewmodels_values_and_order(tmp_path):
    path, vm_cls = _component(tmp_path)
    host = View(_host_file(tmp_path))
    rows = _rows(host, path, vm_cls, 3)
    rows[1][1].label.set("edited")
    labels = [component.node("label") for component, _ in rows]
    watcher = ComponentWatcher(path, lambda: [component for component, _ in rows])
    path.write_text(ROW.format(width=240))
    assert watcher.poll() is True
    assert _widths(rows) == [240.0, 240.0, 240.0]
    assert [component.node("label") for component, _ in rows] == labels  # the same nodes
    assert [label.get("text") for label in labels] == ["row 0", "edited", "row 2"]  # live values kept
    assert host.node("rows").children() == [component.root for component, _ in rows]  # order kept
    rows[0][1].label.set("still wired")
    assert labels[0].get("text") == "still wired"


def test_each_row_gets_its_own_copy_of_the_spec(tmp_path):
    path, vm_cls = _component(tmp_path)
    host = View(_host_file(tmp_path))
    rows = _rows(host, path, vm_cls, 2)
    watcher = ComponentWatcher(path, lambda: [component for component, _ in rows])
    path.write_text(ROW.format(width=240))
    watcher.poll()
    assert rows[0][0].spec is not rows[1][0].spec


def test_a_bad_edit_leaves_every_row_as_it_was_and_fails_once(tmp_path):
    path, vm_cls = _component(tmp_path)
    host = View(_host_file(tmp_path))
    rows = _rows(host, path, vm_cls, 3)
    reconciled = []
    live = [component for component, _ in rows]
    for component in live:
        original = component.reconcile
        component.reconcile = lambda spec, frames=None, original=original, c=component: (
            reconciled.append(c), original(spec, frames=frames))
    watcher = ComponentWatcher(path, lambda: live)
    path.write_text(ROW.format(width=240).replace("kind: Text", "kind: NoSuchKind"))
    with pytest.raises(ValueError, match="Row_View.yaml"):
        watcher.poll()
    assert _widths(rows) == [200.0, 200.0, 200.0] and reconciled == [live[0]]  # the first failed; no more tried
    assert watcher.poll() is False  # once per edit


def test_a_file_the_row_includes_is_watched(tmp_path):
    path, vm_cls = _component(tmp_path)
    (tmp_path / "Part.yaml").write_text('id: part\nkind: Rect\nstyle: {width: 10, height: 4, background: "#FF0000"}\n')
    path.write_text(ROW.format(width=200) + "  - include: Part.yaml\n")
    host = View(_host_file(tmp_path))
    rows = _rows(host, path, vm_cls, 2)
    watcher = ComponentWatcher(path, lambda: [component for component, _ in rows])
    assert (tmp_path / "Part.yaml").resolve() in watcher.files
    (tmp_path / "Part.yaml").write_text('id: part\nkind: Rect\nstyle: {width: 50, height: 4, background: "#FF0000"}\n')
    assert watcher.poll() is True
    assert [component.node("part").get("width") for component, _ in rows] == [50.0, 50.0]


# -- in the app (Q2) --------------------------------------------------------------


def _edit_until_queued(handle, path, text, attempts=40):
    for _ in range(attempts):
        path.write_text(text)
        try:
            return handle.queued.get(timeout=0.25)
        except queue.Empty:
            continue
    raise AssertionError(f"the watcher never queued a reload for {path}")


@pytest.fixture
def app_with_rows(tmp_path):
    app = App()
    path, vm_cls = _component(tmp_path)
    host = app.build_view(_host_file(tmp_path))
    app.register("Host", host, None)
    app.show("Host")
    rows = _rows(host, path, vm_cls, 2)
    yield app, host, path, vm_cls, rows
    for watcher in app._watchers:
        watcher.stop()


def test_hot_reload_watches_each_component_file_once_and_reloads_rows_added_since(app_with_rows):
    app, host, path, vm_cls, rows = app_with_rows
    handle = FakeHandle()
    app._start_watchers(handle)
    assert list(app._component_watchers) == [path.resolve()]  # one watcher for both rows
    rows.append(instantiate(host, path, vm_cls, host.node("rows"), label="added"))  # added while it runs
    assert list(app._component_watchers) == [path.resolve()]  # still one
    reload = _edit_until_queued(handle, path, ROW.format(width=260))
    reload()
    assert _widths(rows) == [260.0, 260.0, 260.0]
    assert rows[2][0].node("label").get("text") == "added"


def test_a_component_file_first_used_while_running_gets_its_own_watcher(app_with_rows, tmp_path):
    app, host, path, vm_cls, rows = app_with_rows
    handle = FakeHandle()
    app._start_watchers(handle)
    other, other_vm = _component(tmp_path, "Badge", width=40)
    badge, _ = instantiate(host, other, other_vm, host.node("rows"))
    assert set(app._component_watchers) == {path.resolve(), other.resolve()}
    reload = _edit_until_queued(handle, other, ROW.format(width=48))
    reload()
    assert badge.node("label").get("width") == 48.0 and _widths(rows) == [200.0, 200.0]


def test_a_removed_row_is_left_alone(app_with_rows):
    app, host, path, vm_cls, rows = app_with_rows
    handle = FakeHandle()
    app._start_watchers(handle)
    removed, _ = rows.pop(0)
    removed.remove()
    assert app._live_components(path.resolve()) == [rows[0][0]]
    reload = _edit_until_queued(handle, path, ROW.format(width=260))
    reload()
    assert _widths(rows) == [260.0]


def test_outside_hot_reload_nothing_is_watched(tmp_path):
    app = App()
    path, vm_cls = _component(tmp_path)
    host = app.build_view(_host_file(tmp_path))
    app.register("Host", host, None)
    instantiate(host, path, vm_cls, host.node("rows"))
    assert app._component_watchers == {} and app._watchers == []


def test_hot_reload_logs_each_component_file(app_with_rows):
    from loguru import logger

    app, host, path, vm_cls, rows = app_with_rows
    messages = []
    sink = logger.add(lambda m: messages.append(m.record["message"]), level="INFO")
    try:
        app._start_watchers(FakeHandle())
    finally:
        logger.remove(sink)
    assert "hot reload: watching component Row_View.yaml (2 instance(s))" in messages


def test_a_row_added_while_running_shares_the_files_one_watcher(app_with_rows):
    app, host, path, vm_cls, rows = app_with_rows
    app._start_watchers(FakeHandle())
    first, count = app._component_watchers[path.resolve()], len(app._watchers)
    instantiate(host, path, vm_cls, host.node("rows"))
    assert app._component_watchers[path.resolve()] is first and len(app._watchers) == count


def test_a_watcher_started_while_running_is_stopped_with_the_rest(app_with_rows, tmp_path):
    app, host, path, vm_cls, rows = app_with_rows
    app._start_watchers(FakeHandle())
    other, other_vm = _component(tmp_path, "Badge", width=40)
    instantiate(host, other, other_vm, host.node("rows"))
    started = list(app._watchers)
    assert app._component_watchers[other.resolve()] in started
    app._stop_watchers()
    assert not any(w.running for w in started)
    assert app._watchers == [] and app._component_watchers == {} and app._hot_handle is None
    instantiate(host, other, other_vm, host.node("rows"))  # after the run: nothing is watched
    assert app._component_watchers == {}


def test_nested_components_are_found_and_ones_a_reload_destroyed_are_not(app_with_rows, tmp_path):
    app, host, path, vm_cls, rows = app_with_rows
    badge_path, badge_vm = _component(tmp_path, "Badge", width=40)
    outer = rows[0][0]
    badge, _ = instantiate(outer, badge_path, badge_vm, outer.root)  # a component inside a row
    assert app._live_components(badge_path.resolve()) == [badge]
    rows[1][0].root.destroy()  # app code destroying a row's node directly: found gone at the next look
    assert app._live_components(path.resolve()) == [outer]
    host.reconcile(host.spec | {"children": [host.spec["children"][0] | {"id": "rows2"}]})  # `rows` destroyed
    assert app._live_components(path.resolve()) == [] and app._live_components(badge_path.resolve()) == []
