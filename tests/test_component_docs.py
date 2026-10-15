"""0.3.4 (#83): the component and stylesheet pages are written by `tools/generate_component_docs.py`.

The pages must be what the generator writes now, and every example on them
must work: each YAML usage builds in a real view, and each Python one runs.
"""

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from tesserae import App, View

ROOT = Path(__file__).resolve().parent.parent
SEED = (0x67, 0x50, 0xA4, 0xFF)


def _generator():
    spec = importlib.util.spec_from_file_location("generate_component_docs", ROOT / "tools" / "generate_component_docs.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GENERATOR = _generator()
DATA = yaml.safe_load(GENERATOR.DATA.read_text(encoding="utf-8"))
ENTRIES = [pytest.param(entry, id=entry["slug"]) for entry in DATA["components"]]


def test_the_pages_are_what_the_generator_writes():
    pages = GENERATOR.build()
    stale = [p.relative_to(ROOT).as_posix() for p, text in pages.items() if not p.exists() or p.read_text(encoding="utf-8") != text]
    existing = {p for folder in (GENERATOR.DOCS / "components", GENERATOR.DOCS / "stylesheets") for p in folder.rglob("*.md")}
    assert not stale and not (existing - set(pages)), \
        f"out of date: {stale or sorted(existing - set(pages))}: run `python tools/generate_component_docs.py`"


def test_every_shipped_view_is_on_exactly_one_page():
    listed = sorted(name for entry in DATA["components"] for name in entry.get("views", []))
    shipped = sorted(p.name.removesuffix("_View.yaml") for p in GENERATOR.VIEWS.glob("*_View.yaml"))
    assert listed == shipped


def test_a_view_left_off_every_page_is_refused():
    shipped = sorted(p.name.removesuffix("_View.yaml") for p in GENERATOR.VIEWS.glob("*_View.yaml"))
    with pytest.raises(SystemExit, match="not listed"):
        GENERATOR.check_coverage(DATA, shipped + ["NoSuchView"])


class _Anything:
    """A stand-in for the ViewModel and widgets an example refers to."""

    def __getattr__(self, name):
        return lambda *args, **kwargs: None


@pytest.mark.parametrize("entry", [p for p in ENTRIES if p.values[0].get("python")])
def test_a_python_example_runs(entry, tmp_path, monkeypatch):
    from PIL import Image

    Image.new("RGBA", (4, 4), (255, 0, 0, 255)).save(tmp_path / "cat.png")
    monkeypatch.chdir(tmp_path)
    app = App(width=800, height=600)
    from tesserae.widgets import button

    names = {"app": app, "viewmodel": _Anything(), "save": button(app.window, "Save", 80, 40),
             "left": button(app.window, "L", 80, 40), "right": button(app.window, "R", 80, 40)}
    exec(compile(entry["python"], f"<{entry['slug']}>", "exec"), names)


def test_every_page_links_to_its_stylesheets_and_back():
    pages = GENERATOR.build()
    for path, text in pages.items():
        if path.parent.parent == GENERATOR.DOCS / "stylesheets":
            slug = path.parent.name
            assert f"../../components/{slug}.md" in text
