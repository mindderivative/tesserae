"""Real coverage for `tesserae.widgets`'s Cards, Lists, Chips & Structural
Rows category. Same thin-delegate parity strategy as the other widget
test modules: construct the same widget two ways and assert real,
gettable state matches; add a kwarg-forwarding check where a variant
resolves to a visibly different, gettable value.
"""

import pytest
from tre import Window

from tesserae.widgets import (
    accordion_header,
    badge,
    card,
    chip,
    divider,
    link,
    list_,
    list_item,
    tree_node,
)


def test_card_matches_native_add_card():
    window = Window(width=400, height=300)
    a = card(window, 200, 100, variant="elevated")
    b = window.add_card(200, 100, variant="elevated")
    assert a.get("elevation") == b.get("elevation")
    assert a.get("corner_radius") == b.get("corner_radius")


def test_card_variant_kwarg_really_flows_through():
    window = Window(width=400, height=300)
    elevated = card(window, 200, 100, variant="elevated")
    outlined = card(window, 200, 100, variant="outlined")
    assert elevated.get("elevation") != outlined.get("elevation")
    assert elevated.get("border_width") != outlined.get("border_width")


def test_list_item_matches_native_add_list_item():
    window = Window(width=400, height=300)
    a = list_item(window, "Item", supporting_text="Details")
    b = window.add_list_item("Item", supporting_text="Details")
    assert a.get("corner_radius") == b.get("corner_radius")


def test_list_lays_out_list_items():
    window = Window(width=400, height=300)
    items = [list_item(window, "One"), list_item(window, "Two")]
    container = list_(window, items)
    assert container is not None


def test_list_rejects_empty_items_matching_native():
    window = Window(width=400, height=300)
    with pytest.raises(ValueError, match="at least 1 item"):
        list_(window, [])


def test_chip_matches_native_add_chip():
    window = Window(width=400, height=300)
    a = chip(window, "Filter", 100, variant="filter", selected=True)
    b = window.add_chip("Filter", 100, variant="filter", selected=True)
    assert a.get("corner_radius") == b.get("corner_radius")


def test_badge_matches_native_add_badge():
    window = Window(width=400, height=300)
    a = badge(window, label="3", width=24)
    b = window.add_badge(label="3", width=24)
    assert a.get("corner_radius") == b.get("corner_radius")


def test_divider_matches_native_add_divider():
    window = Window(width=400, height=300)
    a = divider(window, 200, orientation="horizontal")
    b = window.add_divider(200, orientation="horizontal")
    assert a.get("border_width") == b.get("border_width")


def test_link_matches_native_add_link():
    window = Window(width=400, height=300)
    a = link(window, "Learn more", 120)
    b = window.add_link("Learn more", 120)
    assert a.get("corner_radius") == b.get("corner_radius")


def test_accordion_header_matches_native_add_accordion_header():
    window = Window(width=400, height=300)
    a_header, a_chevron = accordion_header(window, "Section", expanded=True)
    b_header, b_chevron = window.add_accordion_header("Section", expanded=True)
    assert a_header.get("corner_radius") == b_header.get("corner_radius")


def test_tree_node_matches_native_add_tree_node():
    window = Window(width=400, height=300)
    a_node, a_chevron = tree_node(window, "Branch", depth=1, leaf=False)
    b_node, b_chevron = window.add_tree_node("Branch", depth=1, leaf=False)
    assert a_node.get("corner_radius") == b_node.get("corner_radius")
    assert a_chevron is not None and b_chevron is not None


def test_tree_node_leaf_kwarg_really_flows_through():
    window = Window(width=400, height=300)
    node, chevron = tree_node(window, "Leaf", leaf=True)
    assert chevron is None
