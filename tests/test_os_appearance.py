"""M53 Phase 3 (#17): `App(dark="system")` starts with the OS's
appearance, which `tre` 0.3.5.2 can report (`window.get("dark")`,
`tre` issue #18), instead of always starting dark. Where the OS can't say
before the window opens (macOS, Windows), `run()` asks again on the first
frame (Q2). `conftest.os_appearance` fixes what the OS says (Q3).
"""

import subprocess
import sys
import textwrap

import pytest

from tesserae import App, Theme
from tesserae.app import _os_dark
from tesserae.widgets import button

SEED = (0x67, 0x50, 0xA4, 0xFF)
VIEW = 'id: box\nkind: Rect\nstyle: {width: 10, height: 10, background: surface}\n'


def _app(tmp_path, **kwargs):
    app = App(width=300, height=200, theme_seed=SEED, **kwargs)
    (tmp_path / "Home_View.yaml").write_text(VIEW)
    view = app.build_view(tmp_path / "Home_View.yaml")
    return app, view


@pytest.mark.parametrize("os_dark, starts_dark", [(False, False), (True, True), (None, True)])
def test_system_starts_with_the_os_appearance_or_dark_when_it_cant_say(os_appearance, tmp_path, os_dark, starts_dark):
    os_appearance.dark = os_dark
    app, view = _app(tmp_path)
    assert app.dark is starts_dark and app.theme.dark is starts_dark
    assert view.root.get("fill") == Theme.resolve(theme_seed=SEED, dark=starts_dark).role("surface")


@pytest.mark.parametrize("fixed", [True, False])
def test_a_fixed_choice_ignores_the_os(os_appearance, tmp_path, fixed):
    os_appearance.dark = not fixed
    app, _ = _app(tmp_path, dark=fixed)
    assert app.dark is fixed
    app._adopt_os_appearance()  # the first frame changes nothing either
    assert app.dark is fixed


def test_the_first_frame_adopts_an_appearance_the_os_couldnt_give_before(os_appearance, tmp_path):
    """macOS and Windows answer only once the window is open: the app
    starts dark, then re-themes its views and widgets on the first frame."""
    app, view = _app(tmp_path)
    save = button(app.window, "Save", 120, 40, variant="filled")
    assert app.dark is True
    os_appearance.dark = False  # the window is open now, and the OS says light
    app._adopt_os_appearance()
    light = Theme.resolve(theme_seed=SEED, dark=False)
    assert app.dark is False and view.root.get("fill") == light.role("surface")
    assert save.node.get("fill") == light.role("primary")
    os_appearance.dark = None  # a later "can't say" leaves it
    app._adopt_os_appearance()
    assert app.dark is False


def test_the_first_frame_leaves_a_dark_start_when_the_os_still_cant_say(os_appearance, tmp_path):
    """Headless, or no settings portal: `None` open or not, so the app
    stays dark, as before M53."""
    app, _ = _app(tmp_path)
    app._adopt_os_appearance()
    assert app.dark is True


def test_os_dark_reads_the_window_and_tolerates_an_older_tre():
    class Window:
        def __init__(self, answer):
            self.answer = answer

        def get(self, key):
            assert key == "dark"
            if isinstance(self.answer, Exception):
                raise self.answer
            return self.answer

    assert _os_dark(Window(True)) is True and _os_dark(Window(False)) is False
    assert _os_dark(Window(None)) is None
    assert _os_dark(Window(1)) is True
    assert _os_dark(Window(ValueError("unknown property 'dark'"))) is None


def test_os_dark_asks_the_real_window():
    import tre

    assert _os_dark(tre.Window(width=10, height=10)) in (True, False, None)


RUN_SCRIPT = textwrap.dedent(
    '''
    import sys

    import tesserae.app
    from tesserae import App

    answers = iter([None])  # can't say at start (macOS, Windows), light once open
    tesserae.app._os_dark = lambda window: next(answers, False)
    app = App(width=200, height=80, title="os_appearance_live", theme_seed=(0x67, 0x50, 0xA4, 0xFF))
    app.register("Home", app.build_view(sys.argv[1]), None)
    app.show("Home")
    print("START", app.dark)
    frames = {"n": 0}
    handle = app.thread_handle()

    def count():
        frames["n"] += 1
        if frames["n"] < 5:
            handle.call_soon(count)

    handle.call_soon(count)
    app.run(max_frames=10)
    print("FRAMES", frames["n"], "AFTER", app.dark)
    '''
)


def test_run_asks_the_os_again_on_the_first_frame(tmp_path):
    """The real `App.run()` queues the second ask: in a fresh process
    (as the other live tests run), an app that couldn't learn the
    appearance at start adopts it once the loop runs."""
    view = tmp_path / "Home_View.yaml"
    view.write_text(VIEW)
    script = tmp_path / "run_app.py"
    script.write_text(RUN_SCRIPT)
    result = subprocess.run([sys.executable, str(script), str(view)], capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stderr
    words = result.stdout.split()
    assert words[:2] == ["START", "True"], result.stdout
    if words[3] == "0":
        pytest.skip("no display reachable -- App.run() rendered no frames")
    assert words[4:] == ["AFTER", "False"], result.stdout + result.stderr
