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
from tesserae.widgets.navigation import (
    navigation_drawer,
    navigation_rail,
    status_bar,
    tabs,
    toolbar,
    top_app_bar,
)
from tesserae.widgets.overlays import (
    dialog,
    menu,
    menu_item,
    side_sheet,
    snackbar,
    tooltip,
)

__all__ = [
    "accordion_header",
    "badge",
    "button",
    "button_group",
    "card",
    "checkbox",
    "chip",
    "dialog",
    "divider",
    "extended_fab",
    "fab",
    "icon_button",
    "link",
    "list_",
    "list_item",
    "menu",
    "menu_item",
    "navigation_drawer",
    "navigation_rail",
    "radio_button",
    "side_sheet",
    "slider",
    "snackbar",
    "spin_box",
    "split_button",
    "status_bar",
    "switch",
    "tabs",
    "toolbar",
    "tooltip",
    "top_app_bar",
    "tree_node",
]
