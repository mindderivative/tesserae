"""#91: the project Tutorial's programs.

`examples/tutorial_project/step1..6` are the Tasks app built as a project (what `tesserae new` makes), one step at
a time: files in `Views/`, `ViewModels/`, `Components/`, `Themes/` and `Styles/`, found by name. Each step runs
headless and does what the page says, and the page includes every file a step adds or changes.
"""

import filecmp
import re
import runpy
import sys
from pathlib import Path

import pytest

import tesserae

ROOT = Path(__file__).resolve().parent.parent
STEPS = ROOT / "examples" / "tutorial_project"
PAGE = ROOT / "docs" / "tutorial-project.md"
CHECKED = (".py", ".yaml")


@pytest.fixture
def run_step(monkeypatch):
    def run(step: int):
        folder = STEPS / f"step{step}"
        seen = {}
        monkeypatch.setattr(tesserae.App, "run", lambda self, *a, **k: seen.setdefault("app", self))
        monkeypatch.syspath_prepend(str(folder))
        monkeypatch.chdir(folder.parent)  # a project doesn't depend on where it is started from
        monkeypatch.setattr(sys, "argv", ["app.py"])  # steps 5 and 6 read a route from it
        for name in [n for n in sys.modules if n.split("_")[0] in ("Main", "TaskItem", "Settings")]:
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
    view, viewmodel = app.screen("Main")
    _click(app, view.node("add"))
    _click(app, view.node("add"))
    assert len(viewmodel.tasks.get()) == 2


def test_step_2_rows_are_components_with_their_own_view_model(run_step):
    app = run_step(2)
    view, viewmodel = app.screen("Main")
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
    view, viewmodel = app.screen("Main")
    assert view.node("root").get("padding") == 24.0  # from the stylesheet's `page` class
    assert view.node("add").get("fill") == app.theme.role("tertiary")  # ButtonFilled_Stylesheet.yaml, next to the views
    _click(app, view.node("add"))
    assert list(viewmodel.rows)[0][1].node("root").get("gap") == 8.0  # row_Style.yaml


def test_step_4_a_component_of_its_own_with_bound_values(run_step):
    app = run_step(4)
    view, viewmodel = app.screen("Main")
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
    tasks, _ = app.screen("Main")
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
    assert app.current == "Main"


def test_step_6_a_custom_window_with_a_shell(run_step):
    app = run_step(6)
    assert app.decorations is False
    assert app._shell is not None and app.current == "Main"
    app.show("Settings")
    assert app.current == "Settings"


def _files(step: int) -> dict[str, Path]:
    folder = STEPS / f"step{step}"
    return {p.relative_to(folder).as_posix(): p for p in folder.rglob("*") if p.suffix in CHECKED and "__pycache__" not in p.parts}


def test_the_page_includes_every_new_file_and_what_a_step_changes_about_finding_them():
    """The views change as they do in the flat Tutorial, which the page points to; what is the project's own is a new
    file, `app.py`, and the screen's ViewModel (where the rows are found by name)."""
    text = PAGE.read_text(encoding="utf-8")
    included = set(re.findall(r'--8<-- "(examples/tutorial_project/[^"]+)"', text))
    expected = set()
    previous: dict[str, Path] = {}
    for step in range(1, 7):
        current = _files(step)
        for name, path in current.items():
            changed = name not in previous or not filecmp.cmp(path, previous[name], shallow=False)
            if changed and (name not in previous or name in ("app.py", "ViewModels/Main_ViewModel.py")):
                expected.add(path.relative_to(ROOT).as_posix())
        previous = current
    assert included == expected, f"missing {sorted(expected - included)}, unknown {sorted(included - expected)}"


def test_a_project_needs_no_paths_or_imports_of_its_own_files(run_step):
    """What the flat steps spell out (`HERE / "X_View.yaml"`, the ViewModel's import) the project leaves to names."""
    for step in range(1, 7):
        text = (STEPS / f"step{step}" / "app.py").read_text()
        assert "HERE /" not in text and not re.search(r"^from \w+_ViewModel import", text, re.M)


def test_the_screen_and_the_rows_are_found_by_name(run_step):
    app = run_step(2)
    assert app.project.find("view", "TaskItem").name == "TaskItem_View.yaml"
