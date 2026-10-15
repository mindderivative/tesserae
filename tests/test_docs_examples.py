"""Every view and stylesheet example on a docs page is real: the YAML loads against the shipped views.

A block that shows the *old* form on purpose (a migration page) says so with `<!-- old-syntax: ... -->` on the line before its fence.
The generated API and schema pages and the changelog are left out: they quote what was, not what to write now.
"""

import re
from pathlib import Path

import pytest
import yaml

from tesserae.shipped import ViewLibrary
from tesserae.spec.nodes import load_marked, parse_view
from tesserae.spec.rules import RuleSheet
from tesserae.spec.widgets import WidgetDecl

DOCS = Path(__file__).resolve().parent.parent / "docs"
FENCE = re.compile(r"^(<!-- old-syntax[^\n]*-->\n)?```ya?ml\n(.*?)^```", re.M | re.S)
LEFT_OUT = ("api/", "schema/", "changelog.md")
VIEW_KEYS = ("widget", "kind", "component", "children")


def _blocks():
    for page in sorted(DOCS.rglob("*.md")):
        rel = page.relative_to(DOCS).as_posix()
        if rel.startswith(LEFT_OUT):
            continue
        for number, (marker, block) in enumerate(FENCE.findall(page.read_text(encoding="utf-8")), 1):
            try:
                data = yaml.safe_load(block)
            except yaml.YAMLError:
                continue  # not a whole document (a fragment of one); the page's prose says so
            if isinstance(data, dict) and (not marker) and ("styles" in data or any(k in data for k in VIEW_KEYS)):
                yield pytest.param(rel, block, id=f"{rel}#{number}")


BLOCKS = list(_blocks())
LIBRARY = ViewLibrary()


def test_the_pages_have_their_examples():
    assert len(BLOCKS) > 100


@pytest.mark.parametrize("rel, block", BLOCKS)
def test_a_yaml_example_loads(rel, block):
    if "styles" in yaml.safe_load(block):
        RuleSheet.of(load_marked(block, rel), rel, block)
    else:
        parse_view(block, "doc_View.yaml", resolver=lambda name: LIBRARY.decl(name) or WidgetDecl(name, view=True, container=True))


def test_a_marked_old_syntax_block_is_one_the_loader_refuses():
    """The marker must not hide a block that has become valid or was never old."""
    for page in sorted(DOCS.rglob("*.md")):
        for marker, block in FENCE.findall(page.read_text(encoding="utf-8")):
            if marker:
                with pytest.raises(Exception):
                    parse_view(block, "doc_View.yaml", resolver=lambda name: LIBRARY.decl(name) or WidgetDecl(name, view=True, container=True))
