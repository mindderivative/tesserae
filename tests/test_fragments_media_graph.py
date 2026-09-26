from helpers import elevation, view_from
"""Real coverage for `NodeGraph_Component.yaml` -- the one Media &
Graphics fragment shipped after re-scoping the "next boundary" work.
`video`/`graph_node` are NOT here: `video` has no faithful declarative
port available today (tracked as `tre` issue #2, `ImageSpec.src` would
need to become optional); `graph_node` is structurally un-fragmentable
(needs a live node reference as its own attachment parent, which no
`{{ }}`-substitution macro can express -- see
`NodeGraph_Component.yaml`'s own header).
"""

from tre import Window

from tesserae.spec import expand_components
from tesserae.widgets import node_graph

THEME_SEED = (0x67, 0x50, 0xA4, 0xFF)


def _themed_window(width=400, height=300):
    window = Window(width=width, height=height)
    window.set_theme(THEME_SEED)
    return window


def test_node_graph_matches_the_imperative_catalog():
    yaml_text = """
id: root
kind: Container
style: {width: 400, height: 300}
children:
  - id: ng
    component: NodeGraph
    with: {width: 360, height: 200}
"""
    expanded = expand_components(yaml_text)
    view = view_from(expanded, theme_seed=THEME_SEED)
    declarative = view.node("ng")

    imperative = node_graph(_themed_window(), 360, 200).node  # a Widget since M42

    assert declarative.get("corner_radius") == imperative.get("corner_radius")
    assert elevation(declarative) == elevation(imperative)
