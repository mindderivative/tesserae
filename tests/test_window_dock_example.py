"""0.4.4 (#102): `examples/window_dock` runs and checks itself, what it draws is read back from the window's snapshot, and
none of the 0.4.4 code leans on the shell file or `AppShell`, so those can be removed without touching it."""

import runpy
import sys
from pathlib import Path

import pytest

from tesserae import App

ROOT = Path(__file__).resolve().parent.parent
EXAMPLE = ROOT / "examples" / "window_dock"
#: The modules the window, dock, embedded and routed views are made of: none may use the shell file or the app shell.
NEW_MODULES = ["window_view.py", "dockhost.py", "spec/window.py", "spec/dock.py", "spec/embed.py", "spec/title_bar.py"]


def test_the_example_runs_and_its_own_checks_pass(monkeypatch):
    monkeypatch.syspath_prepend(str(EXAMPLE))
    for name in [n for n in sys.modules if n in ("Console_ViewModel", "Notes_ViewModel")]:
        sys.modules.pop(name)  # another test's modules of the same names
    runpy.run_path(str(EXAMPLE / "app.py"), run_name="__main__")


@pytest.fixture
def app(monkeypatch):
    monkeypatch.syspath_prepend(str(EXAMPLE))
    for name in [n for n in sys.modules if n in ("Console_ViewModel", "Notes_ViewModel")]:
        sys.modules.pop(name)
    app = App(title="Studio", theme_seed=(0x67, 0x50, 0xA4, 0xFF), dark=False)
    app.load(EXAMPLE / "Window_View.yaml")
    app.navigate_to("")
    for _ in range(3):
        app.window.advance(16)
    return app


def _pixel(app, x, y):
    rgba, width, _ = app.window.snapshot()
    i = (y * width + x) * 4
    return tuple(rgba[i:i + 4])


def _close(a, b, tolerance=3):
    return all(abs(p - q) <= tolerance for p, q in zip(a[:3], b[:3]))


def _role(app, name):
    return tuple(round(c) for c in app.theme.role(name))[:3]


def test_the_rail_fills_the_current_screens_destination(app):
    pill_home, pill_notes = (20, 68), (20, 136)
    assert _close(_pixel(app, *pill_home), _role(app, "secondary_container"))
    assert not _close(_pixel(app, *pill_notes), _role(app, "secondary_container"))
    app.navigate("Notes")
    app.window.advance(16)
    assert _close(_pixel(app, *pill_notes), _role(app, "secondary_container"))
    assert not _close(_pixel(app, *pill_home), _role(app, "secondary_container"))


def test_the_screens_swap_in_the_centre_zone(app):
    view = app._frame.view
    assert view.embedded("home").node("title").get("visible") and not view.node("notes").get("visible")
    app.navigate("Notes")
    app.window.advance(16)
    assert view.node("notes").get("visible") and not view.node("home").get("visible")


def test_the_frame_follows_dark_mode(app):
    light = _pixel(app, 560, 300)
    app.set_dark(True)
    for _ in range(3):
        app.window.advance(16)
    dark = _pixel(app, 560, 300)
    assert not _close(light, dark, 40) and sum(dark[:3]) < sum(light[:3])


def test_the_dock_zones_are_where_the_yaml_puts_them(app):
    dock = app._frame.view.dock_host("dock")
    assert dock.size("left") == 220 and dock.size("right") == 260 and dock.size("bottom") == 160


@pytest.mark.parametrize("module", NEW_MODULES)
def test_new_code_does_not_use_the_shell_file_or_the_app_shell(module):
    text = (ROOT / "src" / "tesserae" / module).read_text(encoding="utf-8")
    for needle in ("shell_file", "AppShell", "tesserae.shell", "from tesserae import shell", "load_shell"):
        assert needle not in text, f"{module} uses {needle!r}"
