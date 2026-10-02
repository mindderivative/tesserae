"""0.3.4 (#83): the Python API reference page is written from the code.

`docs/api/python.md` comes from `tools/generate_api_docs.py`. It must be what
the generator writes now, every public name must have a description, and every
name the package exports must be on it.
"""

import importlib.util
import re
from pathlib import Path

import tesserae

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "docs" / "api" / "python.md"


def _generator():
    spec = importlib.util.spec_from_file_location("generate_api_docs", ROOT / "tools" / "generate_api_docs.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_page_is_what_the_generator_writes():
    text, _ = _generator().render()
    assert PAGE.read_text(encoding="utf-8") == text, "docs/api/python.md is out of date: run `python tools/generate_api_docs.py`"


def test_every_public_name_has_a_description():
    _, missing = _generator().render()
    assert not missing, "no docstring: " + ", ".join(missing)


def test_every_name_the_package_exports_is_on_the_page():
    page = PAGE.read_text(encoding="utf-8")
    headings = set(re.findall(r"^### `(\w+)`", page, re.MULTILINE))
    assert set(tesserae.__all__) <= headings | {"register_font", "configure_logging", "untrack", "batch", "instantiate"}
    for name in ("batch", "untrack", "instantiate", "register_font", "configure_logging"):
        assert f"### `{name}`" in page
