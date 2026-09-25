"""`ViewWatcher.start(handle)`: event-driven hot reload on a background
thread (`watchfiles`), handing each reload to the event loop through
`tre`'s thread-safe `LoopHandle.call_soon` (tre M87).

`FakeHandle` stands in for the `LoopHandle`: it records what the watcher
queues, and the test runs each callable on its own (main) thread -- the
thread that owns the view, as `tre`'s loop would. The watcher thread
must never touch the view itself; if it did, `tre` would raise a
`PanicException` there.

A background watcher can miss an edit made before it has started
listening, so `_edit_until_queued` re-applies the same final edit until
the watcher reports it. Retrying is harmless since every attempt writes
the same content.
"""

import queue
import threading
import time
from pathlib import Path

import pytest

from tesserae.spec import ViewWatcher, load_view


class FakeHandle:
    def __init__(self):
        self.queued: "queue.Queue" = queue.Queue()
        self.threads: list[str] = []

    def call_soon(self, fn):
        self.threads.append(threading.current_thread().name)
        self.queued.put(fn)


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def _text_view(content: str, extra: str = "") -> str:
    return (
        "id: root\nkind: Container\nchildren:\n"
        f"  - {{id: label, kind: Text, text: {{content: {content}, font_family: Roboto, font_size: 16}},"
        ' style: {width: 100, height: 20, foreground: "#000000"}}\n' + extra
    )


def _edit_until_queued(handle: FakeHandle, path: Path, text: str, attempts: int = 40):
    for _ in range(attempts):
        path.write_text(text)
        try:
            return handle.queued.get(timeout=0.25)
        except queue.Empty:
            continue
    raise AssertionError(f"the watcher never queued a reload for {path}")


@pytest.fixture
def started(tmp_path: Path):
    """A loaded view with a started watcher; stopped afterwards."""
    watchers = []

    def start(text: str):
        view_path = _write(tmp_path / "Home_View.yaml", text)
        view = load_view(view_path)
        watcher = ViewWatcher(view, view_path)
        handle = FakeHandle()
        watcher.start(handle)
        watchers.append(watcher)
        return view_path, view, watcher, handle

    yield start
    for watcher in watchers:
        watcher.stop()


def test_an_edit_is_queued_from_the_watcher_thread_and_applies_on_this_one(started):
    view_path, view, watcher, handle = started(_text_view("Hello"))
    assert watcher.running

    reload = _edit_until_queued(handle, view_path, _text_view("Goodbye"))
    assert view.node("label").get("text") == "Hello"  # nothing applied until the loop runs it
    reload()

    assert view.node("label").get("text") == "Goodbye"
    assert handle.threads and all(name.startswith("tesserae-watch:") for name in handle.threads)


def test_an_included_file_edit_is_picked_up(started, tmp_path: Path):
    part = _write(tmp_path / "parts" / "footer.yaml", _text_view("v1").replace("id: root", "id: footer", 1))
    _, view, _, handle = started("id: page\nkind: Container\nchildren:\n  - include: parts/footer.yaml\n")

    _edit_until_queued(handle, part, _text_view("v2").replace("id: root", "id: footer", 1))()

    assert view.node("label").get("text") == "v2"


def test_a_broken_edit_is_logged_and_the_watcher_carries_on(started, logs):
    view_path, view, watcher, handle = started(_text_view("Hello"))

    message = logs.edit_until(
        view_path,
        "id: root\nkind: Container\nchildren:\n  - {id: x, component: NoSuchThing}\n",
        "ERROR",
        "unknown component 'NoSuchThing'",
    )
    assert message.startswith(f"hot reload of {view_path} failed: ")
    logs.wait_for("DEBUG", "traceback")  # logged just after the ERROR, on the watcher thread
    assert handle.queued.empty()  # nothing for the loop to run
    assert watcher.running
    assert view.node("label").get("text") == "Hello"

    _edit_until_queued(handle, view_path, _text_view("Fixed"))()
    assert view.node("label").get("text") == "Fixed"
    assert f"reloaded {view_path}" in logs.messages("INFO")


def test_a_reload_tre_rejects_is_logged_on_the_loop(started, logs):
    view_path, view, _, handle = started(_text_view("Hello"))

    rejected = _edit_until_queued(handle, view_path, "id: root\nkind: NotARealKind\n")
    rejected()  # logs instead of raising, so tre's loop carries on

    message = logs.wait_for("ERROR", "NotARealKind")
    assert message.startswith(f"hot reload of {view_path} failed: {view_path}: ")
    assert view.node("label").get("text") == "Hello"


def test_a_new_dependency_in_a_new_directory_is_watched_after_reload(started, tmp_path: Path):
    rect = 'id: extra\nkind: Rect\nstyle: {{width: {n}, height: {n}, background: "#112233"}}\n'
    extra = _write(tmp_path / "more" / "extra.yaml", rect.format(n=5))
    view_path, view, watcher, handle = started(_text_view("Hello"))

    _edit_until_queued(handle, view_path, _text_view("Hello", "  - include: more/extra.yaml\n"))()
    assert extra.resolve() in watcher.files
    assert view.node("extra") is not None

    _edit_until_queued(handle, extra, rect.format(n=9))()


def test_unrelated_files_in_a_watched_directory_are_ignored(started, tmp_path: Path):
    _, _, _, handle = started(_text_view("Hello"))
    time.sleep(0.3)  # let the watcher start listening
    for i in range(3):
        (tmp_path / "notes.txt").write_text(f"not a dependency {i}")
    with pytest.raises(queue.Empty):
        handle.queued.get(timeout=0.5)


def test_stop_is_prompt_and_start_poll_are_guarded(started):
    _, _, watcher, handle = started(_text_view("Hello"))

    with pytest.raises(RuntimeError, match="called twice"):
        watcher.start(handle)
    with pytest.raises(RuntimeError, match="while start"):
        watcher.poll()

    began = time.monotonic()
    watcher.stop()
    assert time.monotonic() - began < 2.0
    assert not watcher.running
    assert watcher.poll() is False  # poll() is usable again once stopped
