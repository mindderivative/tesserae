"""M76: a watcher reloads only when a file really changed. On macOS,
FSEvents can report writes made just before a watch began, so a watcher
got an event for content it had already loaded and queued a needless
reload (three hot-reload tests failed there, on CI). Both watchers now
compare each file's stamp (mtime and size) with what they last read and
skip an event that changed nothing. Here the stale event is made on any
platform: the same content rewritten with its old mtime put back.
"""

import os
import queue
import time
from pathlib import Path

import yaml

from tesserae.spec.load import load_view
from tesserae.spec.watch import FileWatcher, ViewWatcher


class FakeHandle:
    def __init__(self):
        self.queued = queue.Queue()

    def call_soon(self, fn):
        self.queued.put(fn)


def _stale_event(path: Path) -> None:
    """An event for a file whose content and stamp didn't change."""
    stat = path.stat()
    path.write_bytes(path.read_bytes())
    os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))


def _settle(seconds=0.6):
    time.sleep(seconds)


def _real_edit_until_queued(handle, path, text, attempts=40):
    for _ in range(attempts):
        path.write_text(text, encoding="utf-8")
        try:
            return handle.queued.get(timeout=0.25)
        except queue.Empty:
            continue
    raise AssertionError(f"no reload queued for {path}")


def test_a_file_watcher_skips_an_event_that_changed_nothing(tmp_path):
    theme = tmp_path / "Brand_Theme.yaml"
    theme.write_text("styles: []\n", encoding="utf-8")
    rebuilt, handle = [], FakeHandle()
    watcher = FileWatcher([theme], lambda: rebuilt.append(theme.read_text(encoding="utf-8")), lambda _: None)
    watcher.start(handle)
    try:
        _settle()
        for _ in range(3):
            _stale_event(theme)
            _settle(0.3)
        assert rebuilt == [] and handle.queued.empty()
        _real_edit_until_queued(handle, theme, "styles: [{kind: Rect, style: {opacity: 0.5}}]\n")
        assert rebuilt[-1].startswith("styles: [{kind: Rect")
        _settle()
        while not handle.queued.empty():  # a real edit can make more than one event
            handle.queued.get()
        seen = len(rebuilt)
        for _ in range(3):  # and after it, what it read is the new baseline
            _stale_event(theme)
            _settle(0.3)
        assert len(rebuilt) == seen and handle.queued.empty()
    finally:
        watcher.stop()


def test_a_view_watcher_skips_an_event_that_changed_nothing(tmp_path):
    view_file = tmp_path / "Home_View.yaml"
    view_file.write_text(yaml.safe_dump({"id": "root", "kind": "Rect", "style": {"width": 10, "height": 10,
                                                                                "background": "#000000"}}),
                         encoding="utf-8")
    view = load_view(view_file)
    watcher, handle = ViewWatcher(view, view_file), FakeHandle()
    watcher.start(handle)
    try:
        _settle()
        for _ in range(3):
            _stale_event(view_file)
            _settle(0.3)
        assert handle.queued.empty()
        apply = _real_edit_until_queued(handle, view_file, yaml.safe_dump(
            {"id": "root", "kind": "Rect", "style": {"width": 42, "height": 10, "background": "#000000"}}))
        apply()
        assert view.node("root").get("width") == 42.0
    finally:
        watcher.stop()
