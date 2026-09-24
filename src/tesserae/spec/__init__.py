"""Tesserae's own declarative macro-expansion layer -- `component: Name`
/ `with: {...}` in a `*_View.yaml`, expanding to a real `*_Component.yaml`
fragment's `WidgetSpec`-shaped subtree before `tre` ever parses the file.
See `expand.py`/`load.py` for the real design and its stated limits.
"""

from __future__ import annotations

from tesserae.spec.expand import ComponentError, expand_components
from tesserae.spec.load import load_view

__all__ = ["ComponentError", "expand_components", "load_view"]
