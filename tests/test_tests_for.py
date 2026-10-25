"""`tools/tests_for.py` picks the tests that cover a change; here, a changed example and the core-module option CI uses."""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("tests_for", ROOT / "tools" / "tests_for.py")
tests_for = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tests_for)

TESTS = tests_for.load_tests()


def picked(*files, **kw):
    return set(tests_for.pick(list(files), TESTS, **kw)[0])


@pytest.mark.parametrize("example, expected", [
    ("counter", {"tests/test_examples_run.py"}),
    ("multi_screen", {"tests/test_examples_run.py"}),
    ("todo_list", {"tests/test_examples_run.py"}),
    ("custom_title_bar", {"tests/test_examples_run.py", "tests/test_title_bar.py"}),
    ("window_dock", {"tests/test_examples_run.py", "tests/test_window_dock_example.py"}),
    ("typing_effects", {"tests/test_examples_run.py", "tests/test_typing_effects.py"}),
    ("tutorial", {"tests/test_tutorials_current.py"}),
    ("tutorial_project", {"tests/test_tutorials_current.py"}),
    ("getting_started", {"tests/test_tutorials_current.py"}),
])
def test_a_changed_file_of_an_example_picks_the_tests_that_run_or_check_it(example, expected):
    assert expected <= picked(f"examples/{example}/anything.py")


def test_every_example_folder_has_a_test_that_names_it():
    for folder in sorted(p.name for p in (ROOT / "examples").iterdir() if p.is_dir() and not p.name.startswith("__")):
        assert picked(f"examples/{folder}/app.py"), f"no test names examples/{folder}"


def test_an_example_no_test_names_says_so():
    ghost = "gho" + "st_example"  # built here so that this file does not name it
    picks, notes = tests_for.pick([f"examples/{ghost}/app.py"], TESTS)
    assert not picks and any(f"no test names the example {ghost}" in n for n in notes)


def test_a_core_module_picks_its_importers_only_when_asked():
    assert len(picked("src/tesserae/__init__.py")) < 10
    assert len(picked("src/tesserae/__init__.py", include_core=True)) > 100
