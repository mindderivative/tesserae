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

__all__ = [
    "button",
    "button_group",
    "checkbox",
    "extended_fab",
    "fab",
    "icon_button",
    "radio_button",
    "slider",
    "spin_box",
    "split_button",
    "switch",
]
