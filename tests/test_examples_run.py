"""#276: the vertical-slice examples are written in the current view language and run: each checks itself with real dispatched clicks and renders frames
headless. Each runs in its own process (their ViewModels share file names, like `Home_ViewModel.py`)."""

import re
import subprocess
import sys
from pathlib import Path

import pytest

from tesserae import cli

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"
SELF_CHECKING = ["counter", "multi_screen", "todo_list", "custom_title_bar", "window_dock", "typing_effects"]


@pytest.mark.parametrize("name", SELF_CHECKING)
def test_the_example_runs_and_its_own_checks_pass(name):
    result = subprocess.run([sys.executable, "app.py"], cwd=EXAMPLES / name, capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stderr[-1500:]


def test_a_deep_link_opens_the_multi_screen_example_on_settings():
    result = subprocess.run([sys.executable, "app.py", "settings"], cwd=EXAMPLES / "multi_screen", capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stderr[-1500:]


@pytest.mark.parametrize("name", ["counter", "multi_screen", "todo_list", "custom_title_bar", "window_dock"])
def test_the_example_is_in_the_current_language(name, capsys):
    folder = EXAMPLES / name
    for path in folder.glob("*.yaml"):
        text = path.read_text(encoding="utf-8")
        assert not re.search(r"^\s*-?\s*(kind|component|include|view|id):", text, re.M), f"{path.name} is in the older syntax"
    for path in folder.glob("*.py"):
        assert "app.load(" not in path.read_text(encoding="utf-8"), path.name
    assert cli.main(["migrate-yaml", str(folder)]) == 0
    out = capsys.readouterr().out
    assert "migrated" not in out and "nothing written" in out  # the tool has nothing to translate: every file is current
