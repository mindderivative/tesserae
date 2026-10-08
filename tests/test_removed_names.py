"""0.4.5 (#107): a removed name says what replaces it, and what it says is true.

The messages come first, so each phase that deletes a name only has to call `removed(...)` where the name was.
"""

import importlib
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
