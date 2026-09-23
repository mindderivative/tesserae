"""Tesserae's own namespace for `tre`'s MD3 widget catalog -- one Python
function per widget, imperatively callable, delegating directly to the
matching `Window.add_*` factory in `tre`. See `buttons.py` for why these
are thin delegates rather than from-scratch Python ports.
"""

from __future__ import annotations

from tesserae.widgets.buttons import (
    button,
    button_group,
    extended_fab,
    fab,
    icon_button,
    split_button,
)
from tesserae.widgets.selection import (
    checkbox,
    radio_button,
    slider,
    spin_box,
    switch,
)
from tesserae.widgets.structural import (
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

__all__ = [
    "accordion_header",
    "badge",
    "button",
    "button_group",
    "card",
    "checkbox",
    "chip",
    "divider",
    "extended_fab",
    "fab",
    "icon_button",
    "link",
    "list_",
    "list_item",
    "radio_button",
    "slider",
    "spin_box",
    "split_button",
    "switch",
    "tree_node",
]
