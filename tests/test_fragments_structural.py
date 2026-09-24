"""Real coverage for the Cards, Lists, Chips & Structural Rows
component fragments: `Card` (3 variants), `Chip` (5 variants),
`ListItem`, `Badge` (2 structural shapes), `Divider`,
`AccordionHeader`, `TreeNode` (2 structural shapes), `Link` (was
blocked until `tre`'s own M84 added declarative `NodeKindSpec` support
for it, this repo's own M27 -- see `BUILD_TRACKER.md`).
"""

import pytest
from tre import View, Window

from tesserae.spec import ComponentError, expand_components
from tesserae.widgets import accordion_header, badge, card, chip, divider, link, list_item, tree_node

THEME_SEED = (0x67, 0x50, 0xA4, 0xFF)

CARD_VARIANTS = [("CardElevated", "elevated"), ("CardFilled", "filled"), ("CardOutlined", "outlined")]

CHIP_CASES = [
    ("ChipAssist", "assist", False),
    ("ChipFilter", "filter", False),
    ("ChipFilterSelected", "filter", True),
    ("ChipInput", "input", False),
    ("ChipSuggestion", "suggestion", False),
]


def _themed_window(width=300, height=200):
    window = Window(width=width, height=height)
    window.set_theme(THEME_SEED)
    return window


def test_all_card_variants_match_the_imperative_catalog():
    for component_name, variant in CARD_VARIANTS:
        yaml_text = f"""
id: root
kind: Container
style: {{width: 300, height: 200}}
children:
  - id: c
    component: {component_name}
    with: {{width: 200, height: 100}}
"""
        expanded = expand_components(yaml_text)
        view = View("T.yaml", source=expanded, theme_seed=THEME_SEED)
        declarative = view.node("c")

        imperative = card(_themed_window(), 200, 100, variant=variant)

        assert declarative.get("corner_radius") == imperative.get("corner_radius"), component_name
        assert declarative.get("elevation") == imperative.get("elevation"), component_name
        assert declarative.get("border_width") == imperative.get("border_width"), component_name


def test_all_chip_cases_match_the_imperative_catalog():
    for component_name, variant, selected in CHIP_CASES:
        yaml_text = f"""
id: root
kind: Container
style: {{width: 300, height: 100}}
children:
  - id: c
    component: {component_name}
    with: {{label: Tag, width: 100}}
"""
        expanded = expand_components(yaml_text)
        view = View("T.yaml", source=expanded, theme_seed=THEME_SEED)
        declarative = view.node("c")

        imperative = chip(_themed_window(), "Tag", 100, variant=variant, selected=selected)

        assert declarative.get("corner_radius") == imperative.get("corner_radius"), component_name
        assert declarative.get("border_width") == imperative.get("border_width"), component_name


def test_list_item_constructs():
    yaml_text = """
id: root
kind: Container
style: {width: 300, height: 100}
children:
  - id: li
    component: ListItem
    with: {headline: Home, width: 260}
"""
    expanded = expand_components(yaml_text)
    view = View("T.yaml", source=expanded, theme_seed=THEME_SEED)
    assert view.node("li") is not None
    assert view.node("li.headline") is not None


def test_badge_dot_matches_the_imperative_catalog():
    yaml_text = """
id: root
kind: Container
style: {width: 300, height: 100}
children:
  - id: d
    component: BadgeDot
"""
    expanded = expand_components(yaml_text)
    view = View("T.yaml", source=expanded, theme_seed=THEME_SEED)
    declarative = view.node("d")
    imperative = badge(_themed_window())
    assert declarative.get("corner_radius") == imperative.get("corner_radius")


def test_badge_labeled_matches_the_imperative_catalog():
    yaml_text = """
id: root
kind: Container
style: {width: 300, height: 100}
children:
  - id: p
    component: BadgeLabeled
    with: {label: "3", width: 20}
"""
    expanded = expand_components(yaml_text)
    view = View("T.yaml", source=expanded, theme_seed=THEME_SEED)
    declarative = view.node("p")
    imperative = badge(_themed_window(), label="3", width=20)
    assert declarative.get("corner_radius") == imperative.get("corner_radius")


def test_divider_matches_the_imperative_catalog():
    yaml_text = """
id: root
kind: Container
style: {width: 300, height: 100}
children:
  - id: d
    component: Divider
    with: {width: 200, height: 1}
"""
    expanded = expand_components(yaml_text)
    view = View("T.yaml", source=expanded, theme_seed=THEME_SEED)
    declarative = view.node("d")
    imperative = divider(_themed_window(), 200)
    assert declarative.get("corner_radius") == imperative.get("corner_radius")


def test_accordion_header_constructs_with_a_real_chevron():
    yaml_text = """
id: root
kind: Container
style: {width: 300, height: 100}
children:
  - id: ah
    component: AccordionHeader
    with: {title: Section, width: 260}
"""
    expanded = expand_components(yaml_text)
    view = View("T.yaml", source=expanded, theme_seed=THEME_SEED)
    assert view.node("ah") is not None
    assert view.node("ah.chevron") is not None
    assert view.node("ah.title") is not None


def test_tree_node_leaf_has_no_chevron_structurally():
    yaml_text = """
id: root
kind: Container
style: {width: 300, height: 100}
children:
  - id: leaf
    component: TreeNodeLeaf
    with: {title: File, width: 260, left_padding: 40}
"""
    expanded = expand_components(yaml_text)
    view = View("T.yaml", source=expanded, theme_seed=THEME_SEED)
    assert view.node("leaf") is not None
    assert view.node("leaf.title") is not None
    with pytest.raises(ValueError):
        view.node("leaf.chevron")


def test_tree_node_branch_has_a_real_chevron():
    yaml_text = """
id: root
kind: Container
style: {width: 300, height: 100}
children:
  - id: branch
    component: TreeNodeBranch
    with: {title: Folder, width: 260, left_padding: 16}
"""
    expanded = expand_components(yaml_text)
    view = View("T.yaml", source=expanded, theme_seed=THEME_SEED)
    assert view.node("branch") is not None
    assert view.node("branch.chevron") is not None


def test_link_matches_the_imperative_catalog():
    yaml_text = """
id: root
kind: Container
style: {width: 200, height: 100}
children:
  - id: docs
    component: Link
    with: {text: "Docs", width: 60, height: 20}
"""
    expanded = expand_components(yaml_text)
    view = View("T.yaml", source=expanded, theme_seed=THEME_SEED)
    declarative = view.node("docs")

    window = Window(width=200, height=100)
    window.set_theme(THEME_SEED)
    imperative = link(window, "Docs", width=60)

    assert declarative.get_text() == imperative.get_text() == "Docs"


def test_link_text_is_a_required_param_not_silently_defaulted():
    yaml_text = """
id: root
kind: Container
children:
  - id: docs
    component: Link
    with: {width: 60, height: 20}
"""
    with pytest.raises(ComponentError, match=r"missing parameter"):
        expand_components(yaml_text)
