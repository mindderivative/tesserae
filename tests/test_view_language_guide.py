"""#209 phase 7: the YAML in the view-language guide is real -- every view block loads and every stylesheet block is a valid set of rules."""

import re
from pathlib import Path

import pytest

from tesserae.shipped import ViewLibrary
from tesserae.spec.nodes import load_marked, parse_view
from tesserae.spec.rules import RuleSheet
from tesserae.spec.widgets import WidgetDecl

DOCS = Path(__file__).resolve().parent.parent / "docs"
PAGES = [DOCS / "guide" / "view-language.md", DOCS / "components" / "text-fields.md"]
BLOCKS = [b for page in PAGES for b in re.findall(r"```yaml\n(.*?)```", page.read_text(encoding="utf-8"), re.S)]


def test_the_guide_has_its_examples():
    assert len(BLOCKS) >= 8


@pytest.mark.parametrize("block", BLOCKS, ids=[b.splitlines()[0][:30] for b in BLOCKS])
def test_every_yaml_block_in_the_guide_loads(block):
    if block.startswith("styles:"):
        RuleSheet.of(load_marked(block, "guide"), "guide", block)
    else:
        library = ViewLibrary()  # the shipped views, so `widget: TextField` is checked against its real parameters
        parse_view(block, "guide_View.yaml", resolver=lambda name: library.decl(name) or WidgetDecl(name, view=True, container=True))
