"""M29 Phase 4: themes and stylesheets as data. Tesserae reads theme and
stylesheet YAML files itself and hands `tre` plain dicts via tre M86's
`*_spec=` arguments -- `stylesheet_spec=`/`default_theme_spec=`/
`custom_theme_spec=` on `View(...)`, and the theme two on
`View.set_theme`/`Window.set_theme`. `tre` validates the dict exactly as
it would the file (same schema: `seed`, `dark`, `colors`, `styles`,
`components`, `typography`), so this module only reads, parses, and
checks fonts.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterator

import yaml

from tesserae.fonts import check_font_families
from tesserae.spec.expand import _normalize_scalars

__all__ = ["load_stylesheet", "load_theme"]


def _load_mapping(path: str | Path, what: str) -> dict[str, Any]:
    path = Path(path)
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ValueError(f"{path}: invalid YAML: {exc}") from exc
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"{path}: a {what} must be a mapping, got {type(data).__name__}")
    return _normalize_scalars(data)


def theme_font_families(theme: dict[str, Any]) -> Iterator[str]:
    """Every `font_family` a theme's `typography:` names."""
    typography = theme.get("typography")
    if isinstance(typography, dict):
        for role in typography.values():
            if isinstance(role, dict) and isinstance(role.get("font_family"), str):
                yield role["font_family"]


def view_font_families(spec: Any) -> Iterator[str]:
    """Every `text.font_family` in a view spec, children included."""
    if not isinstance(spec, dict):
        return
    text = spec.get("text")
    if isinstance(text, dict) and isinstance(text.get("font_family"), str):
        yield text["font_family"]
    for child in spec.get("children") or []:
        yield from view_font_families(child)


def load_theme(path: str | Path) -> dict[str, Any]:
    """Reads a theme YAML file into the dict `tre`'s
    `default_theme_spec=`/`custom_theme_spec=` take, for `load_view` or
    for switching themes later:

    ```python
    view.set_theme(custom_theme_spec=load_theme("themes/Dark.yaml"))
    ```

    Warns (`tesserae.fonts.FontFallbackWarning`) if its `typography:`
    names a font family that isn't available.
    """
    theme = _load_mapping(path, "theme")
    check_font_families(theme_font_families(theme), str(path))
    return theme


def load_stylesheet(path: str | Path) -> dict[str, Any]:
    """Reads a stylesheet YAML file into the dict `tre`'s
    `stylesheet_spec=` takes."""
    return _load_mapping(path, "stylesheet")
