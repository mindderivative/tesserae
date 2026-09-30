"""#39: a watcher doesn't read a file in the middle of a save. A save
empties a file, then writes it, and macOS can report both as one event
while the file is still empty; the watchers read at once, so a reload
read an empty file ("'NoneType' object has no attribute 'get'") and
missed the edit (CI, macOS). Both watchers now let a change settle
(`_settled`) before reading. Here the one event is made on any platform:
`watchfiles` is faked to report the save while the file is empty, and the
content lands just after.
"""

import queue
import threading
import time
from pathlib import Path

import yaml

from tesserae.spec import watch
from tesserae.spec.load import load_view
from tesserae.spec.watch import FileWatcher, ViewWatcher, _settled, _stamp


class FakeHandle:
    def __init__(self):
        self.queued = queue.Queue()

    def call_soon(self, fn):
        self.queued.put(fn)


def _one_event_mid_save(monkeypatch, path: Path, content: str, delay: float = 0.12) -> None:
    """`watchfiles.watch`, faked: it empties `path`, reports that once,
    and the content lands `delay` later with no event of its own."""
    def fake_watch(*dirs, watch_filter, stop_event, recursive):
        path.write_text("", encoding="utf-8")
        threading.Timer(delay, lambda: path.write_text(content, encoding="utf-8")).start()
        yield {(watch.watchfiles.Change.modified, str(path))}
        stop_event.wait()

    monkeypatch.setattr(watch.watchfiles, "watch", fake_watch)


def test_a_view_reload_waits_for_the_save_to_finish(tmp_path, monkeypatch, logs):
    view_file = tmp_path / "Home_View.yaml"
    rect = lambda width: yaml.safe_dump(  # noqa: E731
        {"id": "root", "kind": "Rect", "style": {"width": width, "height": 10, "background": "#000000"}})
    view_file.write_text(rect(10), encoding="utf-8")
    view = load_view(view_file)
    _one_event_mid_save(monkeypatch, view_file, rect(42))
    watcher, handle = ViewWatcher(view, view_file), FakeHandle()
    watcher.start(handle)
    try:
        handle.queued.get(timeout=5)()
        assert view.node("root").get("width") == 42.0
        assert logs.messages("ERROR") == []  # no reload of the empty file
    finally:
        watcher.stop()


def test_a_file_reload_waits_for_the_save_to_finish(tmp_path, monkeypatch, logs):
    theme = tmp_path / "Brand_Theme.yaml"
    theme.write_text("styles: []\n", encoding="utf-8")
    _one_event_mid_save(monkeypatch, theme, "styles: [{kind: Rect}]\n")
    read = []
    watcher = FileWatcher([theme], lambda: read.append(theme.read_text(encoding="utf-8")), lambda _: None)
    handle = FakeHandle()
    watcher.start(handle)
    try:
        handle.queued.get(timeout=5)
        assert read == ["styles: [{kind: Rect}]\n"]
    finally:
        watcher.stop()


def test_settling(tmp_path):
    steady = tmp_path / "steady.yaml"
    steady.write_text("a: 1\n", encoding="utf-8")
    started = time.monotonic()
    assert _settled([steady]) == {steady: _stamp(steady)}
    assert time.monotonic() - started < 0.5  # a finished save costs one check

    growing = tmp_path / "growing.yaml"
    growing.write_text("", encoding="utf-8")
    threading.Timer(0.15, lambda: growing.write_text("b: 2\n", encoding="utf-8")).start()
    assert _settled([growing])[growing][1] == len("b: 2\n")  # waited out the empty file

    empty = tmp_path / "empty.yaml"
    empty.write_text("", encoding="utf-8")
    gone = tmp_path / "gone.yaml"
    started = time.monotonic()
    assert _settled([empty, gone], limit=0.2) == {empty: _stamp(empty), gone: None}
    assert 0.2 <= time.monotonic() - started < 1.0  # really empty: read as it is, after the limit
