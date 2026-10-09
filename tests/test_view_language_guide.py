"""#209 phase 7: the YAML in the view-language guide is real -- every view block loads and every stylesheet block is a valid set of rules."""

import re
from pathlib import Path

import pytest

from tesserae.spec.nodes import load_marked, parse_view
from tesserae.spec.rules import RuleSheet
from tesserae.spec.widgets import WidgetDecl

PAGE = Path(__file__).resolve().parent.parent / "docs" / "guide" / "view-language.md"
BLOCKS = re.findall(r"```yaml\n(.*?)```", PAGE.read_text(encoding="utf-8"), re.S)


def test_the_guide_has_its_examples():
    assert len(BLOCKS) >= 6


@pytest.mark.parametrize("block", BLOCKS, ids=[b.splitlines()[0][:30] for b in BLOCKS])
def test_every_yaml_block_in_the_guide_loads(block):
    if block.startswith("styles:"):
        RuleSheet.of(load_marked(block, "guide"), "guide", block)
    else:
        parse_view(block, "guide_View.yaml", resolver=lambda name: WidgetDecl(name, view=True, container=True))
