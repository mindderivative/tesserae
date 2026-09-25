"""End to end: `App.run(hot_reload=True)` reloads a screen while the
app is running -- `watchfiles` notices the edit on the watcher thread,
and the reload reaches the live tree through `tre`'s `LoopHandle`.

Runs in a fresh subprocess: a second real `App.run()` in one pytest
process can break unrelated tests (found by `tre`'s own M87 testing).
Skips when no frame renders (no display), since `App.run()` then returns
at once and there is nothing to test.

Timing is deterministic rather than raced: idle frames take
microseconds, so a background edit could land after `max_frames` ran
out. Instead a callable queued before `run()` makes the edit on the
first frame and re-queues itself (20 ms per frame) until the new text
shows up, re-applying the same edit in case the watcher wasn't listening
yet.
"""

import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

SCRIPT = textwrap.dedent(
    '''
    import sys, time
    from pathlib import Path

    work = Path(sys.argv[1])
    sys.path.insert(0, str(work))
    from Home_ViewModel import HomeViewModel
    from tesserae import App

    def view_text(content):
        return (
            "id: root\\nkind: Container\\nchildren:\\n"
            "  - {id: label, kind: Text, text: {content: " + content + ", font_family: Roboto, font_size: 16},"
            ' style: {width: 100, height: 20, foreground: "#000000"}}\\n'
        )

    view_path = work / "Home_View.yaml"
    view_path.write_text(view_text("Hello"))

    app = App(width=200, height=80, title="hot_reload_live")
    view, _ = app.load(view_path, HomeViewModel)
    app.show("Home")
    handle = app.thread_handle()
    state = {"frames": 0, "seen": None}
    deadline = time.monotonic() + 10

    def check():
        state["frames"] += 1
        if view.node("label").get_text() == "Goodbye":
            state["seen"] = "Goodbye"
            return
        if time.monotonic() < deadline:
            view_path.write_text(view_text("Goodbye"))  # the "editor save"
            time.sleep(0.02)
            handle.call_soon(check)

    handle.call_soon(check)
    app.run(max_frames=2000, hot_reload=True)
    print("FRAMES", state["frames"], "SEEN", state["seen"])
    '''
)


def test_app_run_hot_reload_updates_the_live_view(tmp_path: Path):
    (tmp_path / "Home_ViewModel.py").write_text(
        "from tesserae import ViewModel\n\n\nclass HomeViewModel(ViewModel):\n    pass\n"
    )
    script = tmp_path / "run_app.py"
    script.write_text(SCRIPT)

    result = subprocess.run(
        [sys.executable, str(script), str(tmp_path)], capture_output=True, text=True, timeout=60
    )
    assert result.returncode == 0, result.stderr
    frames, seen = result.stdout.split()[1], result.stdout.split()[3]
    if frames == "0":
        pytest.skip("no display reachable -- App.run() rendered no frames")
    assert seen == "Goodbye", result.stdout + result.stderr


STYLE_SCRIPT = textwrap.dedent(
    '''
    import sys, time
    from pathlib import Path

    work = Path(sys.argv[1])
    sys.path.insert(0, str(work))
    from Home_ViewModel import HomeViewModel
    from tesserae import App

    def rule(prop, value):
        return "styles:\\n  - kind: Rect\\n    style: {" + prop + ": " + str(value) + "}\\n"

    theme = work / "brand.yaml"
    sheet = work / "default.yaml"
    theme.write_text(rule("elevation", 1))
    sheet.write_text(rule("corner_radius", 2))
    view_path = work / "Home_View.yaml"
    view_path.write_text('id: box\\nkind: Rect\\nstyle: {width: 10, height: 10, background: "#112233"}\\n')

    app = App(width=200, height=80, title="style_reload_live",
              theme_seed=(0x67, 0x50, 0xA4, 0xFF), custom_theme=theme, stylesheet=sheet)
    view, _ = app.load(view_path, HomeViewModel)
    window = app.show("Home")
    handle = app.thread_handle()
    state = {"frames": 0, "seen": None}
    deadline = time.monotonic() + 10
    new_theme = rule("elevation", 6) + 'colors: {primary: "#0000FF"}\\n'

    def check():
        state["frames"] += 1
        box = view.node("box")
        got = (box.get("elevation"), box.get("corner_radius"), window.theme.role("primary"))
        if got == (6.0, 9.0, (0, 0, 255, 255)):
            state["seen"] = "restyled"
            return
        if time.monotonic() < deadline:
            theme.write_text(new_theme)  # the "editor saves"
            sheet.write_text(rule("corner_radius", 9))
            time.sleep(0.02)
            handle.call_soon(check)
        else:
            state["seen"] = "stuck:" + repr(got).replace(" ", "")

    handle.call_soon(check)
    app.run(max_frames=2000, hot_reload=True)
    print("FRAMES", state["frames"], "SEEN", state["seen"])
    '''
)


def test_app_run_hot_reload_restyles_on_theme_and_stylesheet_edits(tmp_path: Path):
    """M31: editing the theme file and the default stylesheet file while
    the app runs re-styles the live screen and re-themes the window."""
    (tmp_path / "Home_ViewModel.py").write_text(
        "from tesserae import ViewModel\n\n\nclass HomeViewModel(ViewModel):\n    pass\n"
    )
    script = tmp_path / "run_app.py"
    script.write_text(STYLE_SCRIPT)

    result = subprocess.run(
        [sys.executable, str(script), str(tmp_path)], capture_output=True, text=True, timeout=60
    )
    assert result.returncode == 0, result.stderr
    frames, seen = result.stdout.split()[1], result.stdout.split()[3]
    if frames == "0":
        pytest.skip("no display reachable -- App.run() rendered no frames")
    assert seen == "restyled", result.stdout + result.stderr
