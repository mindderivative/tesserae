"""Small helpers shared by tests."""

import yaml

from tesserae import tokens


def elevation(node) -> float:
    """A node's MD3 elevation level. A Tesserae-built node carries it as
    `shadows` (0.3.4 nodes have no `elevation`); a node from one of
    `tre`'s legacy factories still has its own `elevation`."""
    shadows = node.get("shadows")
    if not shadows:
        return node.get("elevation")
    for level in range(6):
        if shadows == tokens.elevation_shadows(level):
            return float(level)
    raise AssertionError(f"shadows {shadows!r} aren't an MD3 elevation level")


def view_from(expanded_yaml: str, **kwargs):
    """A Tesserae `View` built from `expand_components`' YAML text -- what
    `tre.View("T.yaml", source=...)` did before M37."""
    from tesserae import View

    return View(yaml.safe_load(expanded_yaml), **kwargs)
