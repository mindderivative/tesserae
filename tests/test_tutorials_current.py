"""The Tasks tutorial (flat and as a project) and Getting Started, in the current view language.

`examples/tutorial/step1..6` and `examples/tutorial_project/step1..6` are the Tasks app built up a step at a time; every step
builds, checks clean (`app.check() == []`) and does what its page says. `examples/getting_started/{declarative,imperative}/step1..4`
are the counter, the two ways. Each page must include every file a step adds or changes.
"""

import filecmp
import re
import runpy
import sys
from pathlib import Path

import pytest

import tesserae

ROOT = Path(__file__).resolve().parent.parent
EX = ROOT / "examples"
FLAVOURS = {"tutorial": "Tasks", "tutorial_project": "Main"}
PAGES = {"tutorial": "tutorial.md", "tutorial_project": "tutorial-project.md"}
CHECKED = (".py", ".yaml")


@pytest.fixture
def run_step(monkeypatch):
    def run(flavour, step, argv=()):
        folder = EX / flavour / f"step{step}"
        seen = {}
        monkeypatch.setattr(tesserae.App, "run", lambda self, *a, **k: seen.setdefault("app", self))
        monkeypatch.syspath_prepend(str(folder))
        monkeypatch.chdir(folder.parent)  # nothing depends on where the app is started from
        monkeypatch.setattr(sys, "argv", ["app.py", *argv])
        for name in [n for n in sys.modules if n.split("_")[0] in ("Tasks", "Main", "Settings", "Window")]:
            sys.modules.pop(name)  # another step's modules of the same names
        runpy.run_path(str(folder / "app.py"), run_name="__main__")
        app = seen["app"]
        app.window.advance(16)
        return app

    return run


def click(app, node):
    app.window.simulate("click", node=node)
    app.window.advance(16)


def parts(app, flavour, step):
    """The view that holds the nodes, the path to the Tasks screen's root in it, and the ViewModel."""
    screen = FLAVOURS[flavour]
    if step == 6:  # the screens are calls in the window view, served by its ViewModel
        view, vm = app.screen("Window")
        return view, "root.body.screens." + screen.lower(), vm
    view, vm = app.screen(screen)
    return view, "root", vm


def add_path(base, step):
    return f"{base}.buttons.add" if step == 5 else f"{base}.add"


@pytest.mark.parametrize("flavour", FLAVOURS)
@pytest.mark.parametrize("step", [1, 2, 3, 4, 5, 6])
def test_each_step_checks_clean_and_adds_tasks(flavour, step, run_step):
    app = run_step(flavour, step)
    assert app.check() == []
    view, base, vm = parts(app, flavour, step)
    for _ in range(2):
        click(app, view.node(add_path(base, step)))
    assert len(vm.tasks.get()) == 2


@pytest.mark.parametrize("flavour", FLAVOURS)
def test_step_2_rows_follow_the_list(flavour, run_step):
    app = run_step(flavour, 2)
    view, base, vm = parts(app, flavour, 2)
    for _ in range(3):
        click(app, view.node(f"{base}.add"))
    assert len(view.node(f"{base}.list").children()) == 3
    click(app, view.node(f"{base}.list.row[2].done"))
    assert [t["done"] for t in vm.tasks.get()] == [False, True, False]
    click(app, view.node(f"{base}.list.row[1].remove"))
    assert [t["id"] for t in vm.tasks.get()] == [2, 3] and len(view.node(f"{base}.list").children()) == 2


@pytest.mark.parametrize("flavour", FLAVOURS)
def test_step_3_the_look_comes_from_files(flavour, run_step):
    app = run_step(flavour, 3)
    view, base, vm = parts(app, flavour, 3)
    assert view.node(base).get("padding") == 24.0  # the stylesheet's `page` class
    add = view.node(f"{base}.add")
    assert add.get("fill") == app.theme.role("tertiary")  # the stylesheet's rule for the filled Button
    click(app, add)
    assert view.node(f"{base}.list.row[1]").get("gap") == 8.0  # the rule for TaskItem


@pytest.mark.parametrize("flavour", FLAVOURS)
@pytest.mark.parametrize("step", [4, 5, 6])
def test_step_4_a_view_of_its_own_with_bound_values(flavour, step, run_step):
    app = run_step(flavour, step)
    view, base, vm = parts(app, flavour, step)
    shown = lambda: (view.node(f"{base}.stats.open.value").get("text"), view.node(f"{base}.stats.finished.value").get("text"))  # noqa: E731
    assert shown() == ("0", "0")
    for _ in range(3):
        click(app, view.node(add_path(base, step)))
    assert shown() == ("3", "0")
    click(app, view.node(f"{base}.list.row[1].done"))
    assert shown() == ("2", "1")
    click(app, view.node(f"{base}.list.row[1].remove"))
    assert shown() == ("2", "0")


@pytest.mark.parametrize("flavour", FLAVOURS)
def test_step_5_two_screens_share_state_and_navigate(flavour, run_step):
    app = run_step(flavour, 5)
    tasks, settings = FLAVOURS[flavour], "Settings"
    tview, _ = app.screen(tasks)
    sview, _ = app.screen(settings)
    title = lambda: tview.node("root.title").get("text")  # noqa: E731
    assert title() == "Ada's tasks"
    click(app, tview.node("root.buttons.settings"))
    assert app.current == settings and app.can_go_back.get()
    field = sview.node("root.name.box.body.input")
    field.focus()
    app.window.advance(16)
    app.window.simulate("input", text="!")
    app.window.advance(16)
    assert app.state.user.get() == "Ada!" and title() == "Ada!'s tasks"
    dark = app.dark
    click(app, sview.node("root.buttons.theme"))
    assert app.dark is not dark
    click(app, sview.node("root.buttons.back"))
    assert app.current == tasks


@pytest.mark.parametrize("flavour", FLAVOURS)
def test_step_5_opens_on_a_route(flavour, run_step):
    assert run_step(flavour, 5, argv=("settings",)).current == "Settings"


@pytest.mark.parametrize("flavour", FLAVOURS)
def test_step_6_a_custom_window(flavour, run_step):
    app = run_step(flavour, 6)
    assert app.borderless is True and app._frame is not None
    assert app.current == FLAVOURS[flavour]
    view, _, _ = parts(app, flavour, 6)
    app.show("Settings")
    assert app.current == "Settings"
    click(app, view.node("root.body.screens.settings.buttons.theme"))


@pytest.mark.parametrize("flavour", FLAVOURS)
def test_the_page_includes_every_file_a_step_adds_or_changes(flavour):
    text = (ROOT / "docs" / PAGES[flavour]).read_text(encoding="utf-8")
    included = set(re.findall(rf'--8<-- "(examples/{flavour}/[^"]+)"', text))
    expected, previous = set(), {}
    for step in range(1, 7):
        folder = EX / flavour / f"step{step}"
        current = {p.relative_to(folder).as_posix(): p for p in folder.rglob("*") if p.suffix in CHECKED and "__pycache__" not in p.parts}
        for name, path in current.items():
            if name not in previous or not filecmp.cmp(path, previous[name], shallow=False):
                expected.add(f"examples/{flavour}/step{step}/{name}")
        previous = current
    assert included == expected, f"missing {sorted(expected - included)}, unknown {sorted(included - expected)}"


# -- Getting Started ----------------------------------------------------------------------------------------------------


@pytest.fixture
def run_gs(monkeypatch):
    def run(kind, step):
        folder = EX / "getting_started" / kind / f"step{step}"
        seen = {}
        monkeypatch.setattr(tesserae.App, "run", lambda self, *a, **k: seen.setdefault("app", self))
        monkeypatch.syspath_prepend(str(folder))
        names = runpy.run_path(str(folder / "app.py"), run_name="__main__")
        sys.modules.pop("Counter_ViewModel", None)
        app = seen["app"]
        app.window.advance(16)
        return app, names

    return run


def gs_node(kind, app, names, name):
    return app.screen("Counter")[0].node("root." + name) if kind == "declarative" else names[name]


def box(node):
    return tuple(node.get(k) for k in ("layout_x", "layout_y", "layout_width", "layout_height"))


@pytest.mark.parametrize("kind", ["declarative", "imperative"])
def test_getting_started_each_step_builds_and_the_window_grows(kind, run_gs):
    for step in (1, 2, 3, 4):
        app, names = run_gs(kind, step)
        assert app.current == ("Counter" if kind == "declarative" else None)
        if step >= 2:
            assert gs_node(kind, app, names, "label").get("text") == "Count: 0"
        if step >= 3:
            assert box(gs_node(kind, app, names, "button"))[2:] == (96.0, 40.0)


@pytest.mark.parametrize("kind", ["declarative", "imperative"])
def test_getting_started_counts_clicks_and_keys(kind, run_gs):
    app, names = run_gs(kind, 4)
    label, button = gs_node(kind, app, names, "label"), gs_node(kind, app, names, "button")
    for expected in ("Count: 1", "Count: 2"):
        click(app, button)
        assert label.get("text") == expected
    app.window.simulate("key_down", key="tab")
    assert button.get("focused") is True
    app.window.simulate("key_down", key="enter")
    app.window.advance(16)
    assert label.get("text") == "Count: 3"


def test_getting_started_the_two_ways_are_the_same_app(run_gs):
    seen = {}
    for kind in ("declarative", "imperative"):
        app, names = run_gs(kind, 4)
        label, button = gs_node(kind, app, names, "label"), gs_node(kind, app, names, "button")
        seen[kind] = {
            "label": box(label), "button": box(button),
            "text": (label.get("text"), label.get("font_size"), label.get("fill")),
            "look": (button.get("fill"), button.get("corner_radius")),
            "role": (button.get("role"), button.get("focusable")),
        }
    assert seen["declarative"] == seen["imperative"]


def test_getting_started_the_two_ways_mix(run_gs):
    app, names = run_gs("declarative", 4)
    view = app.screen("Counter")[0]
    note = app.window.create("text", text="Made in Python", font_size=14, width=120, height=20, fill=(255, 255, 255, 255))
    view.root.add_child(note)
    app.window.advance(16)
    assert note.get("layout_y") > view.node("root.button").get("layout_y")


def test_getting_started_the_page_includes_every_step():
    text = (ROOT / "docs" / "getting-started.md").read_text(encoding="utf-8")
    included = set(re.findall(r'--8<-- "(examples/getting_started/[^"]+)"', text))
    expected = {p.relative_to(ROOT).as_posix() for p in (EX / "getting_started").rglob("*")
                if p.is_file() and p.suffix in CHECKED and "__pycache__" not in p.parts}
    assert included == expected, f"missing {sorted(expected - included)}, unknown {sorted(included - expected)}"
