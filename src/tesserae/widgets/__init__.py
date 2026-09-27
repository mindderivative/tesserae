"""Tesserae's MD3 widget catalog -- one Python function per widget,
imperatively callable, each taking the window first. Since M40-M42 every
one is built by Tesserae from `tre`'s building blocks (most from the
same fragments a `component:` in a view uses) and returns a Tesserae
object -- a control, a `Widget` (`.node`, `.part(name)`) or an overlay --
never a bare `tre` node; none delegates to `tre`'s `Window.add_*`.
"""

from __future__ import annotations

from tesserae.widgets.buttons import (
    button,
    button_group,
    extended_fab,
    fab,
    icon_button,
    segmented_button,
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
    pagination,
    status_bar,
    tabs,
    toolbar,
    top_app_bar,
)
from tesserae.widgets.overlays import (
    dialog,
    menu,
    menu_item,
    popover,
    side_sheet,
    snackbar,
    tooltip,
)
from tesserae.widgets.search import search_bar, search_view
from tesserae.widgets.progress import circular_progress, linear_progress, loading_indicator
from tesserae.widgets.media import graph_node, icon, image, node_graph, video
from tesserae.widgets.containment import carousel, splitter
from tesserae.widgets.date_time import date_picker_day, period_selector, time_input_field, time_picker_dial

__all__ = [
    "accordion_header",
    "badge",
    "button",
    "button_group",
    "card",
    "carousel",
    "checkbox",
    "chip",
    "circular_progress",
    "date_picker_day",
    "dialog",
    "divider",
    "extended_fab",
    "fab",
    "graph_node",
    "icon",
    "icon_button",
    "image",
    "linear_progress",
    "link",
    "list_",
    "list_item",
    "loading_indicator",
    "menu",
    "menu_item",
    "navigation_drawer",
    "navigation_rail",
    "node_graph",
    "pagination",
    "period_selector",
    "popover",
    "radio_button",
    "search_bar",
    "search_view",
    "segmented_button",
    "side_sheet",
    "slider",
    "snackbar",
    "spin_box",
    "splitter",
    "split_button",
    "status_bar",
    "switch",
    "tabs",
    "time_input_field",
    "time_picker_dial",
    "toolbar",
    "tooltip",
    "top_app_bar",
    "tree_node",
    "video",
]
