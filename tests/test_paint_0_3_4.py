"""M33: Tesserae's own YAML is right for `tre` 0.3.4's paint model.

`tre` 0.3.4 (its M95) changed two things a static spec can get wrong,
and neither shows up anywhere but on screen:

- **A color's own alpha renders.** A Text glyph colored `"#FFFFFF00"`
  painted solid white on 0.3.3, where the node's opacity replaced the
  alpha; on 0.3.4 it's invisible.
- **`opacity` is group opacity:** it fades the node's whole subtree. A
  translucent scrim wrapping its panel has to take its translucency
  from its color, or the panel fades with it.

`tre` 0.3.4 can't read pixels back from Python, so this checks what
every view, fragment and docs snippet declares.
"""

import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
FENCE = re.compile(r"^```ya?ml\n(.*?)^```", re.MULTILINE | re.DOTALL)
HEX = re.compile(r"^#(?:[0-9A-Fa-f]{3}|[0-9A-Fa-f]{4}|[0-9A-Fa-f]{6}|[0-9A-Fa-f]{8})$")


def _documents():
    """`(label, parsed YAML)` for every view and fragment file, and every
    `yaml` block in the docs that parses."""
    for path in sorted([*ROOT.glob("examples/**/*.yaml"), *ROOT.glob("src/tesserae/**/*.yaml")]):
        yield str(path.relative_to(ROOT)), yaml.safe_load(path.read_text())
    for path in sorted([*ROOT.glob("docs/**/*.md"), ROOT / "README.md"]):
        for i, block in enumerate(FENCE.findall(path.read_text())):
            try:
                data = yaml.safe_load(block)
            except yaml.YAMLError:
                continue
            yield f"{path.relative_to(ROOT)} (yaml block {i + 1})", data


def _nodes(data):
    """Every mapping with a `kind:` or `component:` -- a widget node."""
    if isinstance(data, dict):
        if "kind" in data or "component" in data:
            yield data
        for value in data.values():
            yield from _nodes(value)
    elif isinstance(data, list):
        for item in data:
            yield from _nodes(item)


def _alpha(color: str) -> int:
    digits = color[1:]
    if len(digits) in (4, 8):
        return int(digits[-(len(digits) // 4):] * (2 if len(digits) == 4 else 1), 16)
    return 255


DOCS = list(_documents())


def test_the_scan_covers_views_fragments_and_docs():
    labels = [label for label, _ in DOCS]
    assert any(label.startswith("examples/") for label in labels)
    assert sum(label.startswith("src/tesserae/spec/components/") for label in labels) >= 60
    assert any("yaml block" in label for label in labels)


@pytest.mark.parametrize("label,data", DOCS, ids=[label for label, _ in DOCS])
def test_no_glyph_color_is_translucent(label, data):
    for node in _nodes(data):
        color = (node.get("style") or {}).get("foreground")
        if isinstance(color, str) and HEX.match(color):
            assert _alpha(color) == 255, f"{label}: {node.get('id')!r} has glyph color {color}, invisible on tre 0.3.4"


@pytest.mark.parametrize("label,data", DOCS, ids=[label for label, _ in DOCS])
def test_no_node_with_children_sets_opacity(label, data):
    for node in _nodes(data):
        style = node.get("style") or {}
        if "opacity" in style and node.get("children"):
            pytest.fail(f"{label}: {node.get('id')!r} sets opacity {style['opacity']} and has children, which fade too on tre 0.3.4")
