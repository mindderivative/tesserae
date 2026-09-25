"""Tesserae's own declarative macro-expansion layer -- `component: Name`
/ `with: {...}` in a `*_View.yaml`, expanding to a real `*_Component.yaml`
fragment's `WidgetSpec`-shaped subtree before `tre` ever parses the file.
See `expand.py`/`load.py` for the real design and its stated limits.
"""

from __future__ import annotations

from tesserae.spec.expand import ComponentError, expand_components, expand_components_to_spec
from tesserae.spec.load import load_view
from tesserae.spec.themes import load_stylesheet, load_theme
from tesserae.spec.watch import ViewWatcher

__all__ = ["ComponentError", "ViewWatcher", "expand_components", "expand_components_to_spec", "load_stylesheet", "load_theme", "load_view"]
