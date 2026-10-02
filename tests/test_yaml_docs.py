"""0.3.4 (#83): the YAML reference page is written from the schemas.

`docs/api/yaml.md` comes from `tools/generate_yaml_docs.py`. It must be what
the generator writes now, and no key on it may be left without a description.
"""

import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "docs" / "api" / "yaml.md"


def _generator():
    spec = importlib.util.spec_from_file_location("generate_yaml_docs", ROOT / "tools" / "generate_yaml_docs.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_page_is_what_the_generator_writes():
    assert PAGE.read_text(encoding="utf-8") == _generator().render(), \
        "docs/api/yaml.md is out of date: run `python tools/generate_yaml_docs.py`"


def test_every_key_has_a_description():
    empty = [line for line in PAGE.read_text(encoding="utf-8").splitlines() if re.match(r"^\| `.*\| +\|$", line)]
    assert not empty, "keys with no description:\n" + "\n".join(empty)


def test_every_kind_the_compiler_builds_is_described():
    from tesserae.spec import build

    page = PAGE.read_text(encoding="utf-8")
    for kind in sorted(build._KINDS | {"TitleBar"}):
        assert f"| `{kind}` |" in page, kind
