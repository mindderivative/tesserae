"""0.4.5 (#107): a removed name says what replaces it, and what it says is true.

The messages come first, so each phase that deletes a name only has to call `removed(...)` where the name was.
"""

import importlib
import re
import inspect
from pathlib import Path

import pytest

import tesserae
from tesserae import App, cli
from tesserae._removed import MIGRATION, REMOVED, RemovedError, removed

ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.parametrize("name", sorted(REMOVED))
def test_each_removed_name_says_what_replaces_it(name):
    error = removed(name)
    text = str(error)
    assert isinstance(error, RemovedError) and isinstance(error, ValueError) and error.name == name
    assert text.startswith(f"`{name}` was removed: ") and text.endswith(f"See {MIGRATION}.")
    assert "`" in REMOVED[name] and len(REMOVED[name]) > 30  # a replacement, not a shrug


def test_a_name_that_was_not_removed_is_an_error():
    with pytest.raises(KeyError, match="isn't a removed name"):
        removed("load")


def test_the_replacements_exist():
    """What the messages tell people to use is there to use."""
    assert "borderless" in inspect.signature(App).parameters and isinstance(App.borderless, property)
    assert importlib.import_module("tesserae.docking").Dock is not None
    assert cli._parser().parse_args(["new", "x", "--window"]).window is True
    shipped = Path(tesserae.__file__).parent / "spec" / "components"
    assert (shipped / "NavigationRailScreens_Component.yaml").is_file()
    assert (shipped / "StatusBar_Component.yaml").is_file()


def test_the_migration_link_is_where_the_docs_are():
    """The docs are published at the README's address, and `docs/migration.md` is a page of them."""
    assert MIGRATION == "https://mindderivative.github.io/tesserae/migration/"
    assert MIGRATION.removesuffix("migration/") in (ROOT / "README.md").read_text(encoding="utf-8")
    assert (ROOT / "docs" / "migration.md").is_file()


def test_load_shell_and_a_shell_file_say_what_replaced_them(tmp_path):
    """0.4.5 (#108): the shell file is gone."""
    app = App(width=300, height=200)
    with pytest.raises(RemovedError, match=r"`App.load_shell` was removed.*kind: Window") as raised:
        app.load_shell(tmp_path / "Studio_Shell.yaml")
    assert raised.value.name == "App.load_shell"
    with pytest.raises(RemovedError, match=r"`\*_Shell.yaml` was removed.*title_bar"):
        app.load(tmp_path / "Studio_Shell.yaml")
    for gone in ("shell_file", "tesserae-shell-schema.json", "Shell.yaml.tmpl"):
        assert not [p for p in (ROOT / "src").rglob(f"*{gone}*") if p.suffix != ".pyc"], gone


def test_use_shell_and_app_shell_say_what_replaced_them():
    """0.4.5 (#109): the Python app shell is gone; docking from Python is `Dock`."""
    app = App(width=300, height=200)
    with pytest.raises(RemovedError, match=r"`App.use_shell` was removed.*tesserae.docking.Dock") as raised:
        app.use_shell(object())
    assert raised.value.name == "App.use_shell"
    with pytest.raises(RemovedError, match=r"`AppShell` was removed.*kind: Window"):
        from tesserae.shell import AppShell  # noqa: F401
    with pytest.raises(AttributeError):
        importlib.import_module("tesserae.shell").Anything
    from tesserae.docking import Dock  # stays

    assert Dock is not None


def test_nothing_else_of_the_app_shell_is_left_in_src():
    leftovers = [p.name for p in (ROOT / "src" / "tesserae").rglob("*.py") if p.name not in ("_removed.py", "shell.py")
                 and ("AppShell" in p.read_text(encoding="utf-8") or "use_shell" in p.read_text(encoding="utf-8").replace(
                     'removed("App.use_shell")', "").replace("def use_shell", ""))]
    assert leftovers == []


#: The words of what was removed; in `src/` they may only be in the stubs that say so, and tre's own `decorations=` call.
GONE = re.compile(r"shell_file|AppShell|load_shell|use_shell|_Shell|tesserae\.shell|decorations")
STUB_FILES = {"_removed.py", "shell.py"}
#: In `app.py`: the lines of the stubs, `borderless`'s use of tre's `Window(decorations=)`, and nothing else.
APP_STUB_LINES = re.compile(
    r'"decorations" in removed_kwargs|removed\("decorations"\)|endswith\("_Shell\.yaml"\)|removed\("\*_Shell\.yaml"\)'
    r"|def use_shell|removed\(\"App\.use_shell\"\)|def load_shell|removed\(\"App\.load_shell\"\)"
    r"|def decorations|@decorations\.setter|removed\(\"app\.decorations\"\)"
    r"|Window\(width=width, height=height, title=title, decorations=not borderless\)"
    r"|self\._window\.set\(decorations=not bool\(value\)")


def test_nothing_of_the_old_shell_or_decorations_is_left_in_src():
    """0.4.5 (#112): the removed names appear only in what says they were removed."""
    left = []
    for path in sorted((ROOT / "src" / "tesserae").rglob("*")):
        if path.suffix not in (".py", ".yaml", ".tmpl", ".json") or "__pycache__" in path.parts or path.name in STUB_FILES:
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if GONE.search(line) and not (path.name == "app.py" and APP_STUB_LINES.search(line)):
                left.append(f"{path.relative_to(ROOT)}:{number}: {line.strip()[:80]}")
    assert left == []


def test_the_repository_has_no_shell_file_example_tool_or_workflow_left():
    for folder in ("examples", "tools", ".github"):
        for path in (ROOT / folder).rglob("*"):
            if path.is_file() and path.suffix in (".py", ".yaml", ".yml", ".tmpl") and "__pycache__" not in path.parts:
                text = path.read_text(encoding="utf-8")
                assert not re.search(r"load_shell|use_shell|AppShell|_Shell\.yaml|new \S+ --shell|app_shell", text), path
    assert not [p for d in (ROOT / "examples").glob("app_shell*") for p in d.rglob("*") if p.is_file() and p.suffix != ".pyc"]
