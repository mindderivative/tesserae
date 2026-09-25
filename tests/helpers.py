"""Small helpers shared by tests."""

from tesserae import tokens


def elevation(node) -> float:
    """A node's MD3 elevation level, read back from its `shadows` (0.3.4
    nodes have no `elevation`; Tesserae sets `tokens.elevation_shadows`)."""
    shadows = node.get("shadows")
    for level in range(6):
        if shadows == tokens.elevation_shadows(level):
            return float(level)
    raise AssertionError(f"shadows {shadows!r} aren't an MD3 elevation level")
