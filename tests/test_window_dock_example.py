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
    for name in [n for n in sys.modules if n in ("Window_ViewModel",)]:
        sys.modules.pop(name)  # another test's modules of the same names
    runpy.run_path(str(EXAMPLE / "app.py"), run_name="__main__")


def test_interactive_runs_until_the_window_is_closed_and_the_default_for_20_frames(monkeypatch):
    monkeypatch.syspath_prepend(str(EXAMPLE))
    for name in [n for n in sys.modules if n in ("Window_ViewModel",)]:
        sys.modules.pop(name)
    calls = []
    monkeypatch.setattr(App, "run", lambda self, *args, **kwargs: calls.append(kwargs))
    runpy.run_path(str(EXAMPLE / "app.py"), run_name="__main__")
    monkeypatch.setattr(sys, "argv", ["app.py", "--interactive"])
    runpy.run_path(str(EXAMPLE / "app.py"), run_name="__main__")
    assert calls == [{"max_frames": 20, "hot_reload": True}, {"hot_reload": True}]  # no frame limit when asked for


@pytest.fixture
def app(monkeypatch):
    monkeypatch.syspath_prepend(str(EXAMPLE))
    for name in [n for n in sys.modules if n in ("Window_ViewModel",)]:
        sys.modules.pop(name)
    from Window_ViewModel import WindowViewModel

    app = App(title="Studio", theme_seed=(0x67, 0x50, 0xA4, 0xFF), dark=False, root=EXAMPLE, search=["."])
    app.bind(WindowViewModel)
    app.open_view("Window")
    app.navigate_to("")
    app.window.advance(400)  # the rail's pill eases in
    return app


def _pixel(app, x, y):
    rgba, width, _ = app.window.snapshot()
    i = (y * width + x) * 4
    return tuple(rgba[i:i + 4])


def _close(a, b, tolerance=3):
    return all(abs(p - q) <= tolerance for p, q in zip(a[:3], b[:3]))


def _role(app, name):
    return tuple(round(c) for c in app.theme.role(name))[:3]


def _pill_centre(app, name):
    """A point on the rail's pill for `name`, in window coordinates."""
    pill = app._opened["Window"].node(f"root.body.nav.item[{name}].pill")
    x, y, w, h = (pill.get(k) for k in ("layout_x", "layout_y", "layout_width", "layout_height"))
    return int(x + 6), int(y + h / 2)  # the layout position is the window's already; beside the icon, on the pill


def test_the_rail_fills_the_current_screens_destination(app):
    home, notes = _pill_centre(app, "Home"), _pill_centre(app, "Notes")
    assert _close(_pixel(app, *home), _role(app, "secondary_container"))
    assert not _close(_pixel(app, *notes), _role(app, "secondary_container"))
    app.navigate("Notes")
    app.window.advance(300)
    assert _close(_pixel(app, *notes), _role(app, "secondary_container"))
    assert not _close(_pixel(app, *home), _role(app, "secondary_container"))


def test_the_screens_swap_in_the_centre_zone(app):
    view = app._opened["Window"]
    assert view.node("root.body.dock.screens.home.title").get("visible") and not view.node("root.body.dock.screens.notes").get("visible")
    app.navigate("Notes")
    app.window.advance(16)
    assert view.node("root.body.dock.screens.notes").get("visible") and not view.node("root.body.dock.screens.home").get("visible")


def test_the_frame_follows_dark_mode(app):
    light = _pixel(app, 560, 300)
    app.set_dark(True)
    for _ in range(3):
        app.window.advance(16)
    dark = _pixel(app, 560, 300)
    assert not _close(light, dark, 40) and sum(dark[:3]) < sum(light[:3])


def test_the_dock_zones_are_where_the_yaml_puts_them(app):
    dock = app._opened["Window"].dock_host("root.body.dock")
    assert dock.size("left") == 220 and dock.size("right") == 260 and dock.size("bottom") == 160


@pytest.mark.parametrize("module", NEW_MODULES)
def test_new_code_does_not_use_the_shell_file_or_the_app_shell(module):
    text = (ROOT / "src" / "tesserae" / module).read_text(encoding="utf-8")
    for needle in ("shell_file", "AppShell", "tesserae.shell", "from tesserae import shell", "load_shell"):
        assert needle not in text, f"{module} uses {needle!r}"
