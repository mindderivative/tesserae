"""0.3.4 (#83): the Tutorial's programs.

`examples/tutorial/step1..6` are the Tasks app built up one step at a time:
a screen, a list of components, styling in files, a component of its own,
a second screen with shared state, and a custom window with a shell. Each step runs
headless and does what the page says; the page includes every file a step adds
or changes.
"""

import filecmp
import re
import runpy
import sys
from pathlib import Path

import pytest

import tesserae

ROOT = Path(__file__).resolve().parent.parent
STEPS = ROOT / "examples" / "tutorial"
PAGE = ROOT / "docs" / "tutorial.md"
CHECKED = (".py", ".yaml")


@pytest.fixture
def run_step(monkeypatch):
    def run(step: int):
        folder = STEPS / f"step{step}"
        seen = {}
        monkeypatch.setattr(tesserae.App, "run", lambda self, *a, **k: seen.setdefault("app", self))
        monkeypatch.syspath_prepend(str(folder))
        monkeypatch.setattr(sys, "argv", ["app.py"])  # steps 5 and 6 read a route from it
        for name in [n for n in sys.modules if n.split("_")[0] in ("Tasks", "TaskItem", "Settings")]:
            sys.modules.pop(name)  # another step's modules of the same names
        runpy.run_path(str(folder / "app.py"), run_name="__main__")
        app = seen["app"]
        app.window.advance(16)
        return app

    return run


def _click(app, node):
    app.window.simulate("click", node=node)
    app.window.advance(16)


@pytest.mark.parametrize("step", [1, 2, 3, 4, 5, 6])
def test_each_step_builds_and_adds_tasks(step, run_step):
    app = run_step(step)
    view, viewmodel = app.screen("Tasks")
    _click(app, view.node("add"))
    _click(app, view.node("add"))
    assert len(viewmodel.tasks.get()) == 2


def test_step_2_rows_are_components_with_their_own_view_model(run_step):
    app = run_step(2)
    view, viewmodel = app.screen("Tasks")
    for _ in range(3):
        _click(app, view.node("add"))
    rows = list(viewmodel.rows)
    assert len(rows) == 3
    _click(app, rows[0][1].node("done"))
    assert rows[0][2].done.get() is True and rows[1][2].done.get() is False
    _click(app, rows[1][1].node("remove"))
    assert viewmodel.tasks.get() == [1, 3]


def test_step_3_the_look_comes_from_files(run_step):
    app = run_step(3)
    view, viewmodel = app.screen("Tasks")
    assert view.node("root").get("padding") == 24.0  # from the stylesheet's `page` class
    assert view.node("add").get("fill") == app.theme.role("tertiary")  # ButtonFilled_Stylesheet.yaml, next to the views
    _click(app, view.node("add"))
    assert list(viewmodel.rows)[0][1].node("root").get("gap") == 8.0  # row_Style.yaml


def test_step_4_a_component_of_its_own_with_bound_values(run_step):
    app = run_step(4)
    view, viewmodel = app.screen("Tasks")
    shown = lambda: (view.node("open.value").get("text"), view.node("finished.value").get("text"))  # noqa: E731
    assert shown() == ("0", "0")
    for _ in range(3):
        _click(app, view.node("add"))
    assert shown() == ("3", "0")
    row = list(viewmodel.rows)[0][1]
    _click(app, row.node("done"))
    assert shown() == ("2", "1")
    _click(app, row.node("remove"))
    assert shown() == ("2", "0")


def test_step_5_two_screens_share_state_and_navigate(run_step):
    app = run_step(5)
    tasks, _ = app.screen("Tasks")
    settings, _ = app.screen("Settings")
    assert tasks.node("title").get("text") == "Ada's tasks"
    _click(app, tasks.node("settings"))
    assert app.current == "Settings" and app.can_go_back.get()
    app.state.user.set("Grace")
    app.window.advance(16)
    assert tasks.node("title").get("text") == "Grace's tasks" and settings.node("name").get("text") == "Grace"
    dark = app.dark
    _click(app, settings.node("theme"))
    assert app.dark is not dark
    _click(app, settings.node("back"))
    assert app.current == "Tasks"


def test_step_6_a_custom_window(run_step):
    app = run_step(6)
    assert app.borderless is True
    assert app._frame is not None and app.current == "Tasks"
    app.show("Settings")
    assert app.current == "Settings"


def _files(step: int) -> dict[str, Path]:
    return {p.name: p for p in (STEPS / f"step{step}").iterdir() if p.suffix in CHECKED}


def test_the_page_includes_every_file_a_step_adds_or_changes():
    text = PAGE.read_text(encoding="utf-8")
    included = set(re.findall(r'--8<-- "(examples/tutorial/[^"]+)"', text))
    expected = set()
    previous: dict[str, Path] = {}
    for step in range(1, 7):
        current = _files(step)
        for name, path in current.items():
            if name not in previous or not filecmp.cmp(path, previous[name], shallow=False):
                expected.add(path.relative_to(ROOT).as_posix())
        previous = current
    assert included == expected, f"missing {sorted(expected - included)}, unknown {sorted(included - expected)}"
