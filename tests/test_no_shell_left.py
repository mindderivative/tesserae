"""0.4.6 (#113): the shell file, `AppShell` and `decorations` are gone, and stay gone.

0.4.5 removed them and left stubs that said what replaced each; the stubs are removed too, so an old name now fails as any unknown
name does. These tests keep the names from creeping back into the code, the examples, the tools or the workflows.
"""

import re
import subprocess
import sys
from pathlib import Path

import pytest

from tesserae import App, cli

ROOT = Path(__file__).resolve().parent.parent
GONE = re.compile(r"shell_file|AppShell|load_shell|use_shell|_Shell|tesserae\.shell|decorations|_removed|RemovedError")
#: `decorations` is also `tre`'s own window option: the two lines where `borderless` is passed to it.
TRE_LINES = re.compile(r"Window\(width=width, height=height, title=title, decorations=not borderless\)"
                       r"|self\._window\.set\(decorations=not bool\(value\)")


def test_nothing_of_the_old_shell_or_decorations_is_left_in_src():
    left = []
    for path in sorted((ROOT / "src" / "tesserae").rglob("*")):
        if path.suffix not in (".py", ".yaml", ".tmpl", ".json") or "__pycache__" in path.parts:
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if GONE.search(line) and not (path.name == "app.py" and TRE_LINES.search(line)):
                left.append(f"{path.relative_to(ROOT)}:{number}: {line.strip()[:80]}")
    assert left == []
    assert not (ROOT / "src" / "tesserae" / "shell.py").exists()
    assert not (ROOT / "src" / "tesserae" / "_removed.py").exists()


def test_the_repository_has_no_shell_file_example_tool_or_workflow_left():
    for folder in ("examples", "tools", ".github"):
        for path in (ROOT / folder).rglob("*"):
            if path.is_file() and path.suffix in (".py", ".yaml", ".yml", ".tmpl") and "__pycache__" not in path.parts:
                text = path.read_text(encoding="utf-8")
                assert not re.search(r"load_shell|use_shell|AppShell|_Shell\.yaml|new \S+ --shell|app_shell", text), path
    assert not [p for d in (ROOT / "examples").glob("app_shell*") for p in d.rglob("*") if p.is_file() and p.suffix != ".pyc"]


def test_an_old_name_fails_as_any_unknown_name_does(tmp_path):
    app = App(width=300, height=200)
    with pytest.raises(TypeError, match="unexpected keyword argument 'decorations'"):
        App(decorations=False)
    for name in ("load_shell", "use_shell", "decorations"):
        with pytest.raises(AttributeError):
            getattr(app, name)
    with pytest.raises(ModuleNotFoundError):
        __import__("tesserae.shell")
    with pytest.raises(SystemExit) as stopped:
        cli._parser().parse_args(["new", "x", "--shell"])
    assert stopped.value.code == 2
    result = subprocess.run([sys.executable, "-m", "tesserae", "new", "x", "--shell", "--no-venv", "--dir", str(tmp_path)],
                            capture_output=True, text=True)
    assert result.returncode == 2 and "unrecognized arguments: --shell" in result.stderr and not (tmp_path / "x").exists()


def test_loading_a_shell_file_is_an_ordinary_load_error(tmp_path):
    path = tmp_path / "Studio_Shell.yaml"
    path.write_text("top_bar: {title: Studio}\n", encoding="utf-8")
    with pytest.raises(Exception) as raised:
        App(width=300, height=200).load(path)
    assert "removed" not in str(raised.value).lower()
