"""#269: a view opened with `app.open_view` is hot-reloaded: the file, the views it calls and its pictures are watched, and a change recomposes it
with the ViewModel, the nodes that keep their id and their `state:` left as they were. A mistake leaves the view as it was."""

import os
import time

import pytest

from tesserae import App, Signal, ViewModel
from tesserae.spec.watch import ComposedWatcher


class VM(ViewModel):
    views = "main"

    def __init__(self):
        super().__init__()
        self.count = Signal(0)
        self.clicks = 0

    def bump(self):
        self.count.update(lambda n: n + 1)
        self.clicks += 1


HEAD = "name: main\nwidget: Container\nstyle: {width: 300, height: 200, flex_direction: vertical}\nstate: {open: false}\nchildren:\n"
V1 = HEAD + "  - {widget: Text, name: label, text: \"Count {{ count }}\", typography_role: body_large, style: {foreground: on_surface}}\n  - {widget: Button, name: go, label: Go, handlers: {on_click: bump}}\n"
V2 = HEAD + "  - {widget: Text, name: label, text: \"Total {{ count }}\", typography_role: body_large, style: {foreground: on_surface}}\n  - {widget: Button, name: go, label: Go, handlers: {on_click: bump}}\n  - {widget: Text, name: extra, text: new, typography_role: body_large, style: {foreground: on_surface}}\n"


def bump_time(path):
    """A save the watcher sees: the stamp is (mtime, size), so move the mtime on."""
    stat = path.stat()
    os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 5_000_000_000))


def write(path, text):
    path.write_text(text)
    bump_time(path)


@pytest.fixture
def opened(tmp_path):
    (tmp_path / "Views").mkdir()
    path = tmp_path / "Views" / "Main_View.yaml"
    path.write_text(V1)
    app = App(root=tmp_path)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    view.window.advance(16)
    watcher = ComposedWatcher(view, view.source, app._composed_docs, lambda library: app._composed_rules(library)[0])
    return app, view, path, watcher, app.bindings.viewmodel_for("main")


def text_of(view, name):
    return view.node(f"root.{name}").get("text")


def test_a_view_opened_with_open_view_knows_its_file(opened):
    app, view, path, watcher, vm = opened
    assert view.source == path.resolve()
    assert path.resolve() in watcher.files


def test_nothing_changed_means_nothing_reloaded(opened):
    *_, watcher, _vm = opened
    assert watcher.poll() is False


def test_an_edit_changes_the_window(opened):
    app, view, path, watcher, vm = opened
    assert text_of(view, "label") == "Count 0"
    write(path, V2)
    assert watcher.poll() is True
    view.window.advance(16)
    assert text_of(view, "label") == "Total 0"
    assert text_of(view, "extra") == "new"


def test_the_viewmodel_and_its_signals_are_the_same_after_a_reload(opened):
    app, view, path, watcher, vm = opened
    vm.bump()
    write(path, V2)
    watcher.poll()
    view.window.advance(16)
    assert app.bindings.viewmodel_for("main") is vm and vm.count.get() == 1
    assert text_of(view, "label") == "Total 1"
    vm.bump()
    view.window.advance(16)
    assert text_of(view, "label") == "Total 2"  # still bound


def test_a_handler_still_works_after_a_reload(opened):
    app, view, path, watcher, vm = opened
    write(path, V2)
    watcher.poll()
    view.window.advance(16)
    view.window.simulate("click", view.node("root.go"))
    assert vm.clicks == 1


def test_state_of_a_node_that_keeps_its_id_survives(opened):
    app, view, path, watcher, vm = opened
    view.handle.state("open").set(True)
    write(path, V2)
    watcher.poll()
    assert view.handle.state("open").get() is True


def test_a_yaml_mistake_leaves_the_view_as_it_was(opened):
    app, view, path, watcher, vm = opened
    write(path, V1.replace("widget: Text", "widget: Textt"))
    with pytest.raises(Exception):
        watcher.poll()
    view.window.advance(16)
    assert text_of(view, "label") == "Count 0"
    vm.bump()
    view.window.advance(16)
    assert text_of(view, "label") == "Count 1"


def test_a_fixed_file_reloads_after_a_mistake(opened):
    app, view, path, watcher, vm = opened
    write(path, "widget: [")
    with pytest.raises(Exception):
        watcher.poll()
    write(path, V2)
    assert watcher.poll() is True
    view.window.advance(16)
    assert text_of(view, "label") == "Total 0"


def test_a_view_the_engine_rejects_leaves_the_view_as_it_was(opened):
    """The parse is fine and the build fails (a Text with no type role): the old composition is drawn again, bound and clickable."""
    app, view, path, watcher, vm = opened
    write(path, V2.replace("typography_role: body_large, ", "", 1))
    with pytest.raises(Exception):
        watcher.poll()
    view.window.advance(16)
    assert text_of(view, "label") == "Count 0"
    view.window.simulate("click", view.node("root.go"))
    view.window.advance(16)
    assert vm.clicks == 1 and text_of(view, "label") == "Count 1"
    assert view.handle.composition.find("root.extra") is None


CALLED = "name: Chip\nwidget: Container\nparams: {title: {type: str, default: x}}\nchildren:\n  - {widget: Text, name: t, text: \"{{ title }}\", typography_role: body_large, style: {foreground: on_surface}}\n"
WITH_CALL = HEAD + "  - {widget: Chip, name: chip, title: Hello}\n"


@pytest.fixture
def calling(tmp_path):
    (tmp_path / "Views").mkdir()
    main, chip = tmp_path / "Views" / "Main_View.yaml", tmp_path / "Views" / "Chip_View.yaml"
    main.write_text(WITH_CALL)
    chip.write_text(CALLED)
    app = App(root=tmp_path)
    app.bind(VM)
    view = app.open_view("Main")
    app.show("main")
    view.window.advance(16)
    watcher = ComposedWatcher(view, view.source, app._composed_docs, lambda library: app._composed_rules(library)[0])
    return app, view, main, chip, watcher


def test_a_view_it_calls_is_watched_and_an_edit_to_it_reloads(calling):
    app, view, main, chip, watcher = calling
    assert chip.resolve() in watcher.files
    assert text_of(view, "chip.t") == "Hello"
    write(chip, CALLED.replace("{{ title }}", "{{ title }}!"))
    assert watcher.poll() is True
    view.window.advance(16)
    assert text_of(view, "chip.t") == "Hello!"


def test_the_shipped_views_are_not_watched(opened):
    app, view, path, watcher, vm = opened  # it calls Button, which Tesserae ships
    from tesserae.shipped import SHIPPED

    assert not [f for f in watcher.files if SHIPPED in f.parents]
    assert any(SHIPPED in f.parents for f in app._composed_docs(path)[1].read)  # it was read; it is just not watched


def test_a_view_called_by_a_view_it_calls_is_watched_too(tmp_path):
    (tmp_path / "Views").mkdir()
    main, chip, inner = (tmp_path / "Views" / f"{n}_View.yaml" for n in ("Main", "Chip", "Inner"))
    main.write_text(WITH_CALL)
    chip.write_text("name: Chip\nwidget: Container\nparams: {title: {type: str, default: x}}\nchildren:\n  - {widget: Inner, name: in, title: \"{{ title }}\"}\n")
    inner.write_text(CALLED.replace("name: Chip", "name: Inner"))
    app = App(root=tmp_path)
    app.bind(VM)
    view = app.open_view("Main")
    view.window.advance(16)
    watcher = ComposedWatcher(view, view.source, app._composed_docs, lambda library: app._composed_rules(library)[0])
    assert inner.resolve() in watcher.files
    write(inner, inner.read_text().replace("{{ title }}", "<{{ title }}>"))
    assert watcher.poll() is True
    view.window.advance(16)
    assert text_of(view, "chip.in.t") == "<Hello>"


def test_the_old_instances_are_let_go_and_a_list_still_follows_its_data_after_a_reload(tmp_path):
    (tmp_path / "Views").mkdir()
    rows = HEAD.replace("state: {open: false}", "state: {open: false}") + "  - for: n in rows\n    widget: Text\n    key: n\n    text: \"{{ n }}\"\n    typography_role: body_large\n    style: {foreground: on_surface}\n"
    path = tmp_path / "Views" / "Main_View.yaml"
    path.write_text(rows)

    class Rows(VM):
        def __init__(self):
            super().__init__()
            self.rows = Signal(["a"])

    app = App(root=tmp_path)
    app.bind(Rows)
    view = app.open_view("Main")
    view.window.advance(16)
    vm = app.bindings.viewmodel_for("main")
    before = list(view.handle.composition.walk())
    write(path, rows + "# edited\n")
    watcher = ComposedWatcher(view, view.source, app._composed_docs, lambda library: app._composed_rules(library)[0])
    write(path, rows + "# edited again\n")
    assert watcher.poll() is True
    assert all(inst.disposed for inst in before) and not any(inst.disposed for inst in view.handle.composition.walk())
    vm.rows.set(["a", "b"])
    view.window.advance(16)
    assert len([i for i in view.handle.composition.walk() if i.widget == "Text"]) == 2
    vm.rows.set(["a", "b", "c"])
    view.window.advance(16)
    assert len([i for i in view.handle.composition.walk() if i.widget == "Text"]) == 3


def test_a_view_the_file_starts_to_call_is_watched_from_then_on(tmp_path):
    (tmp_path / "Views").mkdir()
    main, chip = tmp_path / "Views" / "Main_View.yaml", tmp_path / "Views" / "Chip_View.yaml"
    main.write_text(V1)
    chip.write_text(CALLED)
    app = App(root=tmp_path)
    app.bind(VM)
    view = app.open_view("Main")
    watcher = ComposedWatcher(view, view.source, app._composed_docs, lambda library: app._composed_rules(library)[0])
    assert chip.resolve() not in watcher.files
    write(main, WITH_CALL)
    assert watcher.poll() is True
    assert chip.resolve() in watcher.files
    write(chip, CALLED.replace("body_large", "body_small"))
    assert watcher.poll() is True


def test_a_picture_it_draws_is_watched(tmp_path):
    from PIL import Image

    (tmp_path / "Views").mkdir()
    Image.new("RGBA", (4, 4), (255, 0, 0, 255)).save(tmp_path / "Views" / "dot.png")
    (tmp_path / "Views" / "Main_View.yaml").write_text(HEAD + "  - {widget: Image, name: pic, src: dot.png, style: {width: 8, height: 8}}\n")
    app = App(root=tmp_path)
    app.bind(VM)
    view = app.open_view("Main")
    watcher = ComposedWatcher(view, view.source, app._composed_docs, lambda library: app._composed_rules(library)[0])
    assert (tmp_path / "Views" / "dot.png").resolve() in watcher.files
    Image.new("RGBA", (4, 4), (0, 255, 0, 255)).save(tmp_path / "Views" / "dot.png")
    bump_time(tmp_path / "Views" / "dot.png")
    assert watcher.poll() is True


def test_a_closed_view_is_left_alone(opened):
    app, view, path, watcher, vm = opened
    view.handle.close()
    write(path, V2)
    assert watcher.poll() is True  # the file is read; nothing is built for a view that has gone
    assert view.handle.composition.find("root.extra") is None


class Loop:
    """Stands in for the event loop's handle: what the watcher thread queues, the test runs on its own thread."""

    def __init__(self):
        import queue

        self.calls = queue.Queue()

    def call_soon(self, fn):
        self.calls.put(fn)


def test_the_watcher_thread_queues_the_reload_for_the_loop(opened):
    app, view, path, watcher, vm = opened
    loop = Loop()
    watcher.start(loop)
    try:
        time.sleep(0.3)  # let the thread start watching
        write(path, V2)
        run = loop.calls.get(timeout=10)
        assert text_of(view, "label") == "Count 0"  # not yet: it is for the loop thread to do
        run()
        view.window.advance(16)
        assert text_of(view, "label") == "Total 0"
    finally:
        watcher.stop()


def test_a_mistake_found_on_the_watcher_thread_is_logged_and_nothing_is_queued(opened):
    from loguru import logger

    app, view, path, watcher, vm = opened
    messages = []
    sink = logger.add(lambda m: messages.append(str(m)), level="ERROR")
    loop = Loop()
    watcher.start(loop)
    try:
        time.sleep(0.3)
        write(path, "widget: [")
        deadline = time.time() + 10
        while not messages and time.time() < deadline:
            time.sleep(0.05)
        assert messages and "hot reload" in messages[0]
        assert loop.calls.empty()
    finally:
        watcher.stop()
        logger.remove(sink)


def test_app_run_with_hot_reload_watches_an_opened_view(tmp_path):
    from loguru import logger

    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Main_View.yaml").write_text(V1)
    app = App(root=tmp_path)
    app.bind(VM)
    app.open_view("Main")
    app.show("main")
    messages = []
    sink = logger.add(lambda m: messages.append(str(m)), level="INFO")
    try:
        app.run(max_frames=5, hot_reload=True)
    finally:
        logger.remove(sink)
    assert any("hot reload on: watching 1 screen(s)" in m for m in messages), messages
    assert not any("isn't watched" in m for m in messages)


def test_a_view_opened_while_hot_reload_runs_is_watched_too(tmp_path):
    (tmp_path / "Views").mkdir()
    (tmp_path / "Views" / "Main_View.yaml").write_text(V1)
    (tmp_path / "Views" / "Other_View.yaml").write_text(V1.replace("name: main", "name: other"))
    app = App(root=tmp_path)

    class Other(VM):
        views = "other"

    app.bind(VM)
    app.bind(Other)
    app._hot_handle = Loop()
    try:
        view = app.open_view("Other")
        assert [w for w in app._watchers if isinstance(w, ComposedWatcher) and view.source in w.files]
    finally:
        app._stop_watchers()


@pytest.mark.parametrize("broken", [
    V1.replace("Count {{ count }}", "Count {{ nope }}"),                       # a name nothing defines
    V1 + "  - {widget: Button, name: two, label: Go, colour: red}\n",           # a property the widget does not have
])
def test_a_wrong_name_or_property_in_an_edit_leaves_the_view_as_it_was(opened, broken):
    app, view, path, watcher, vm = opened
    write(path, broken)
    with pytest.raises(Exception):
        watcher.poll()
    view.window.advance(16)
    assert text_of(view, "label") == "Count 0"
