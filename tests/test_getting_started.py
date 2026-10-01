"""Docs Phase 2 (#70): the Getting Started walk-through's programs.

`examples/getting_started/{declarative,imperative}/step1..4` are the
programs the page builds up, one folder per step: a window, a label, a
button, and a click that counts. The page includes those files as they
are, so what a reader types is what runs here. Each step runs headless
(`App.run` is replaced by a note of the app); the two finished apps must
be the same app -- the same layout, colours and role, and the same
answer to a click or to Tab and Enter -- and the page must include every
step's files.
"""

import os
import re
import runpy
import shutil
import sys
from pathlib import Path

import pytest

import tesserae
from tesserae.spec.watch import ViewWatcher

ROOT = Path(__file__).resolve().parent.parent
STEPS = ROOT / "examples" / "getting_started"
PAGE = ROOT / "docs" / "getting-started.md"


@pytest.fixture
def run_step(monkeypatch):
    """Run `kind/stepN/app.py` as a script up to `app.run()`, and give
    back the app and the script's names."""

    def run(kind: str, step: int):
        folder = STEPS / kind / f"step{step}"
        seen = {}
        monkeypatch.setattr(tesserae.App, "run", lambda self, *a, **k: seen.setdefault("app", self))
        monkeypatch.syspath_prepend(str(folder))  # `from Counter_ViewModel import ...`, as run from there
        names = runpy.run_path(str(folder / "app.py"), run_name="__main__")
        sys.modules.pop("Counter_ViewModel", None)  # not left for another step's import
        app = seen["app"]
        app.window.advance(16)
        return app, names

    return run


def _node(kind, app, names, name):
    """The node called `name` ("label" or "button") of a step's app, either way."""
    return app.screen("Counter")[0].node(name) if kind == "declarative" else names[name]


def _box(node):
    return tuple(node.get(k) for k in ("layout_x", "layout_y", "layout_width", "layout_height"))


@pytest.mark.parametrize("kind", ["declarative", "imperative"])
def test_each_step_builds_and_the_window_grows(kind, run_step):
    for step in (1, 2, 3, 4):
        app, names = run_step(kind, step)
        assert app.current == ("Counter" if kind == "declarative" else None)  # in code, no screen
        if step >= 2:
            assert _node(kind, app, names, "label").get("text") == "Count: 0"
        if step >= 3:
            assert _box(_node(kind, app, names, "button"))[2:] == (96.0, 40.0)


@pytest.mark.parametrize("kind", ["declarative", "imperative"])
def test_the_finished_app_counts_clicks(kind, run_step):
    app, names = run_step(kind, 4)
    label, button = _node(kind, app, names, "label"), _node(kind, app, names, "button")
    for expected in ("Count: 1", "Count: 2"):
        app.window.simulate("click", node=button)
        assert label.get("text") == expected


@pytest.mark.parametrize("kind", ["declarative", "imperative"])
def test_the_button_works_from_the_keyboard(kind, run_step):
    app, names = run_step(kind, 4)
    label, button = _node(kind, app, names, "label"), _node(kind, app, names, "button")
    app.window.simulate("key_down", key="tab")
    assert button.get("focused") is True
    app.window.simulate("key_down", key="enter")
    assert label.get("text") == "Count: 1"
    app.window.simulate("key_down", key="space")
    app.window.simulate("key_up", key="space")
    assert label.get("text") == "Count: 2"


def test_the_two_ways_are_the_same_app(run_step):
    seen = {}
    for kind in ("declarative", "imperative"):
        app, names = run_step(kind, 4)
        label, button = _node(kind, app, names, "label"), _node(kind, app, names, "button")
        seen[kind] = {
            "label": _box(label), "button": _box(button),
            "text": (label.get("text"), label.get("font_size"), label.get("fill")),
            "look": (button.get("fill"), button.get("corner_radius")),
            "role": (button.get("role"), button.get("focusable")),
        }
    assert seen["declarative"] == seen["imperative"]
    assert seen["declarative"]["label"] == (16.0, 16.0, 160.0, 28.0)  # padding 16
    assert seen["declarative"]["button"] == (16.0, 56.0, 96.0, 40.0)  # 12 below the label (gap)


def test_the_two_ways_mix(run_step):
    """A declarative screen takes nodes made by calls too (the page says so)."""
    app, names = run_step("declarative", 4)
    view = app.screen("Counter")[0]
    note = app.window.create("text", text="Made in Python", font_size=14, width=120, height=20,
                             fill=(255, 255, 255, 255))
    view.root.add_child(note)
    app.window.advance(16)
    assert note.get("layout_y") > view.node("button").get("layout_y")  # laid out after the button


def test_the_page_includes_every_step():
    text = PAGE.read_text(encoding="utf-8")
    included = set(re.findall(r'--8<-- "(examples/getting_started/[^"]+)"', text))
    expected = {p.relative_to(ROOT).as_posix() for p in STEPS.rglob("*")
                if p.is_file() and p.suffix in (".py", ".yaml") and "__pycache__" not in p.parts}
    assert included == expected, f"missing {sorted(expected - included)}, unknown {sorted(included - expected)}"


def test_a_hot_reload_edit_keeps_the_count(tmp_path, run_step, monkeypatch):
    """The page says to edit the view while the app runs and the count stays."""
    folder = tmp_path / "counter"
    shutil.copytree(STEPS / "declarative" / "step4", folder)
    monkeypatch.setattr(tesserae.App, "run", lambda self, *a, **k: seen.setdefault("app", self))
    seen = {}
    monkeypatch.syspath_prepend(str(folder))
    runpy.run_path(str(folder / "app.py"), run_name="__main__")
    sys.modules.pop("Counter_ViewModel", None)
    app = seen["app"]
    view = app.screen("Counter")[0]
    app.window.advance(16)
    for _ in range(2):
        app.window.simulate("click", node=view.node("button"))
    assert view.node("label").get("text") == "Count: 2"

    path = folder / "Counter_View.yaml"
    watcher = ViewWatcher(view, path)  # what `run(hot_reload=True)` does on a thread
    path.write_text(path.read_text(encoding="utf-8").replace("#6750A4", "#146C2E"), encoding="utf-8")
    later = path.stat().st_mtime_ns + 10**9
    os.utime(path, ns=(later, later))  # a change the watcher sees, however fast the test
    assert watcher.poll() is True
    app.window.advance(16)
    assert view.node("button").get("fill") == (0x14, 0x6C, 0x2E, 255)  # the edit shows
    assert view.node("label").get("text") == "Count: 2"  # and the count stays


def test_a_typo_in_the_view_is_named_and_hot_reload_keeps_the_last_good_version(tmp_path, monkeypatch):
    """The page's error note: the last line names the widget, the misspelt key and what
    was meant; with hot reload on, the window keeps what it had, and fixing the file
    brings the edit in."""
    folder = tmp_path / "counter"
    shutil.copytree(STEPS / "declarative" / "step4", folder)
    seen = {}
    monkeypatch.setattr(tesserae.App, "run", lambda self, *a, **k: seen.setdefault("app", self))
    monkeypatch.syspath_prepend(str(folder))
    runpy.run_path(str(folder / "app.py"), run_name="__main__")
    sys.modules.pop("Counter_ViewModel", None)
    view = seen["app"].screen("Counter")[0]
    seen["app"].window.advance(16)
    seen["app"].window.simulate("click", node=view.node("button"))
    path = folder / "Counter_View.yaml"
    good = path.read_text(encoding="utf-8")
    watcher = ViewWatcher(view, path)

    def save(text, bump):
        path.write_text(text, encoding="utf-8")
        later = path.stat().st_mtime_ns + bump * 10**9
        os.utime(path, ns=(later, later))

    save(good.replace("foreground", "foregorund", 1).replace("#6750A4", "#146C2E"), 1)
    with pytest.raises(ValueError, match=r"widget \"label\": unknown style field\(s\) \['foregorund'\] -- did you mean 'foreground'\?"):
        watcher.poll()
    assert view.node("button").get("fill") == (0x67, 0x50, 0xA4, 255)  # nothing half-applied
    assert view.node("label").get("text") == "Count: 1"

    save(good.replace("#6750A4", "#146C2E"), 2)  # fixed: the edit comes in
    assert watcher.poll() is True
    seen["app"].window.advance(16)
    assert view.node("button").get("fill") == (0x14, 0x6C, 0x2E, 255)
    assert view.node("label").get("text") == "Count: 1"
