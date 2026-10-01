"""0.3.1 (#77): a real window held idle, and the keepalive that lets threads run.

`tre`'s window, while it sits idle waiting for input, starves the other
Python threads: a worker's `thread_handle().call_soon(...)` never runs, and
nor does a hot-reload watcher's reload. Every other live test queues a
callback that re-queues itself each frame, so the window is never idle and
that went unseen until a user's edit to a view didn't show.

Each test runs a real window in a subprocess (a second real `App.run()` in
one pytest process can break unrelated tests), with the outside thread an
editor's save would come from. A test is skipped where no window opens (no
display), and a window left starved is killed by the subprocess timeout.
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
    scale = float(sys.argv[3])  # how long the outside thread waits, in the units below
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
            time.sleep(1.0 * scale)
            handle.call_soon(lambda: note("a thread's call_soon ran"))
            time.sleep(1.0 * scale)
            handle.call_soon(app.close)
        except BaseException:
            note("WORKER ERROR " + traceback.format_exc())

    threading.Thread(target=worker, daemon=True).start()
    app.run(**({"keepalive": False} if mode == "off" else {"keepalive": True} if mode == "on" else {}))
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
            time.sleep(1.5 * scale)
            handle.call_soon(lambda: probe("before"))
            time.sleep(0.5 * scale)
            path.write_text(path.read_text().replace("width: auto", "width: 100%"))
            time.sleep(3.0 * scale)
            handle.call_soon(lambda: probe("after"))
            time.sleep(0.5 * scale)
            handle.call_soon(app.close)
        except BaseException:
            note("EDITOR ERROR " + traceback.format_exc())

    threading.Thread(target=editor, daemon=True).start()
    app.run(hot_reload=True, **({"keepalive": False} if mode == "off" else {}))
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


def _run(tmp_path: Path, source: str, mode: str, timeout: float,
         scale: float = 1.0) -> tuple[subprocess.CompletedProcess | None, str]:
    tmp_path.mkdir(exist_ok=True)
    script = tmp_path / "idle_window.py"
    script.write_text(source)
    (tmp_path / "Counter_View.yaml").write_text(VIEW)
    try:
        done = subprocess.run([sys.executable, str(script), str(tmp_path), mode, str(scale)], capture_output=True,
                              text=True, timeout=timeout)  # on a timeout, `run` kills the window
    except subprocess.TimeoutExpired:
        done = None
    result = tmp_path / "result.txt"
    return done, result.read_text() if result.exists() else ""


def _starved(tmp_path: Path, source: str, timeout: float, scale: float, attempts: int = 3):
    """Runs a window with no keepalive until one attempt stays starved (the window outlives the
    timeout), and gives that attempt's `(done, result)`; the last attempt's if none did. A window
    still warming up on a busy machine lets the thread through, so one attempt that closes by
    itself proves nothing: only `attempts` in a row mean that threads now run while idle."""
    for attempt in range(attempts):
        done, result = _run(tmp_path / f"attempt{attempt}", source, "off", timeout, scale)
        if done is None or (done is not None and not result):  # starved, or no display at all
            break
    return done, result


def test_a_thread_reaches_an_idle_window_with_the_keepalive(tmp_path):
    done, result = _run(tmp_path, CODE_ONLY, "on", timeout=60)
    assert done is not None, "the window stayed starved: the keepalive didn't let the thread run"
    assert done.returncode == 0, done.stderr
    if not result:
        pytest.skip("no display reachable -- the window rendered nothing")
    assert result.strip() == "a thread's call_soon ran"


def test_hot_reload_applies_an_edit_to_an_idle_window(tmp_path):
    """The user's report: `width: auto` -> `100%` on a window left alone."""
    done, result = _run(tmp_path, HOT_RELOAD, "default", timeout=60)
    assert done is not None, "the window stayed starved: the reload never arrived"
    assert done.returncode == 0, done.stderr
    if not result:
        pytest.skip("no display reachable -- the window rendered nothing")
    before, after = result.strip().splitlines()
    assert before.startswith("before: width=auto") and float(before.split("layout_width=")[1]) < 360
    assert after == "after: width=100% layout_width=360.0"  # the edit showed, with nothing waking the window


def test_without_the_keepalive_an_idle_window_starves_its_threads(tmp_path):
    """`tre`'s limitation, kept as a test: once the window has settled, the outside thread's
    `app.close` never runs, so the window outlives the timeout and is killed. (Its first call,
    a second after start-up, can still get through while the window is warming up.) When `tre`
    fixes this the window closes by itself, three attempts in a row, and this fails: make
    `keepalive` default to off."""
    done, result = _starved(tmp_path, CODE_ONLY, timeout=9, scale=2.0)
    if done is not None:  # it returned: either no display, or tre no longer starves threads
        if not result:
            pytest.skip("no display reachable -- the window rendered nothing")
        pytest.fail("a thread reached an idle window with no keepalive: tre has fixed it, so make "
                    "`run(keepalive=)` default to off (app.py `_keepalive_interval`) and drop this test")
    assert done is None  # starved: the thread's `app.close` never ran


def test_a_hot_reload_without_the_keepalive_stays_starved(tmp_path):
    done, result = _starved(tmp_path, HOT_RELOAD, timeout=9, scale=1.3)
    if done is not None and not result:
        pytest.skip("no display reachable -- the window rendered nothing")
    assert done is None and "after" not in result  # the edit never reached the window
