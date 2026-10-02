"""0.3.2 (#77, #78): a real window held idle, and what reaches it.

Before `tre` 0.5.1 its window, while it sat idle waiting for input, starved
the other Python threads: a worker's `thread_handle().call_soon(...)` never
ran, and nor did a hot-reload watcher's reload, so Tesserae 0.3.1 ticked the
window by default (`run(keepalive=)`). `tre` 0.5.1 lets threads run, and
Tesserae 0.3.2 requires it, so each of these holds a real window idle and
checks that the outside thread gets through: with no keepalive, which is the
default, and with `keepalive=True`; and that an edit reaches a window left
alone. (Every other live test queues a callback that re-queues itself each
frame, so its window is never idle; that is how the bug went unseen.)

Each test runs a real window in a subprocess (a second real `App.run()` in
one pytest process can break unrelated tests), with the outside thread an
editor's save would come from. A test is skipped where no window opens (no
display), and a window that stays starved is killed by the subprocess timeout.
"""

import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

PRELUDE = textwrap.dedent('''
    import sys, threading, time, traceback
    from pathlib import Path
    from tesserae import App

    folder = Path(sys.argv[1])
    mode = sys.argv[2]
    result = folder / "result.txt"

    def note(line):
        with open(result, "a") as f:
            f.write(line + "\\n")
''')

CODE_ONLY = PRELUDE + textwrap.dedent('''
    app = App(width=200, height=100, title="idle")
    app.window.root.add_child(app.window.create("text", text="idle", font_size=16, width=60, height=20,
                                                fill=(255, 255, 255, 255)))
    handle = app.thread_handle()

    def worker():  # a plain thread: what a hot-reload watcher, or an IDE's thread, is
        try:
            time.sleep(1.0)
            handle.call_soon(lambda: note("a thread's call_soon ran"))
            time.sleep(1.0)
            handle.call_soon(app.close)
        except BaseException:
            note("WORKER ERROR " + traceback.format_exc())

    threading.Thread(target=worker, daemon=True).start()
    app.run(**({"keepalive": True} if mode == "on" else {}))
''')

HOT_RELOAD = PRELUDE + textwrap.dedent('''
    path = folder / "Counter_View.yaml"
    app = App(width=360, height=160, title="idle hot reload")
    view = app.build_view(path)
    app.register("Counter", view, None)
    app.show("Counter")
    handle = app.thread_handle()

    def probe(tag):
        root = view.node("root")
        note(f"{tag}: width={root.get('width')} layout_width={root.get('layout_width')}")

    def editor():  # an outside thread, saving the file as an editor does, then looking at the window
        try:
            time.sleep(1.5)
            handle.call_soon(lambda: probe("before"))
            time.sleep(0.5)
            path.write_text(path.read_text().replace("width: auto", "width: 100%"))
            time.sleep(3.0)
            handle.call_soon(lambda: probe("after"))
            time.sleep(0.5)
            handle.call_soon(app.close)
        except BaseException:
            note("EDITOR ERROR " + traceback.format_exc())

    threading.Thread(target=editor, daemon=True).start()
    app.run(hot_reload=True)
''')

VIEW = """id: root
kind: Container
style: {flex_direction: vertical, width: auto, height: 100%, padding: 16, background: "#444444"}
children:
  - id: label
    kind: Text
    text: {content: "Count: 0", font_family: Roboto, font_size: 20}
    style: {foreground: "#FFFFFF"}
"""


def _run(tmp_path: Path, source: str, mode: str, timeout: float) -> tuple[subprocess.CompletedProcess | None, str]:
    script = tmp_path / "idle_window.py"
    script.write_text(source)
    (tmp_path / "Counter_View.yaml").write_text(VIEW)
    try:
        done = subprocess.run([sys.executable, str(script), str(tmp_path), mode], capture_output=True, text=True,
                              timeout=timeout)  # on a timeout, `run` kills the window
    except subprocess.TimeoutExpired:
        done = None
    result = tmp_path / "result.txt"
    return done, result.read_text() if result.exists() else ""


def test_a_thread_reaches_an_idle_window_by_default(tmp_path):
    """`tre` 0.5.1: no keepalive, and the outside thread's `call_soon` still runs."""
    done, result = _run(tmp_path, CODE_ONLY, "default", timeout=60)
    assert done is not None, "the window stayed starved: tre no longer lets threads run while it is idle"
    assert done.returncode == 0, done.stderr
    if not result:
        pytest.skip("no display reachable -- the window rendered nothing")
    assert result.strip() == "a thread's call_soon ran"


def test_a_thread_reaches_an_idle_window_with_the_keepalive_too(tmp_path):
    done, result = _run(tmp_path, CODE_ONLY, "on", timeout=60)
    assert done is not None, "the window stayed starved with keepalive=True"
    assert done.returncode == 0, done.stderr
    if not result:
        pytest.skip("no display reachable -- the window rendered nothing")
    assert result.strip() == "a thread's call_soon ran"


def test_hot_reload_applies_an_edit_to_an_idle_window(tmp_path):
    """The user's report: `width: auto` -> `100%` on a window left alone."""
    done, result = _run(tmp_path, HOT_RELOAD, "default", timeout=60)
    assert done is not None, "the window stayed starved: the reload never arrived (tre before 0.5.1?)"
    assert done.returncode == 0, done.stderr
    if not result:
        pytest.skip("no display reachable -- the window rendered nothing")
    before, after = result.strip().splitlines()
    assert before.startswith("before: width=auto") and float(before.split("layout_width=")[1]) < 360
    assert after == "after: width=100% layout_width=360.0"  # the edit showed, with nothing waking the window
