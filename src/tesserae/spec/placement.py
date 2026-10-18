"""Where a node or a layer sits against another node (tre 0.5.7): the placements, and the offset that moves it.

A side placement puts a layer beside its anchor and may flip or shift to fit the window; a corner or centre placement puts the layer's centre on that point of the
anchor and is never moved. `offset` is a pair of pixels, `[dx, dy]`, added to the attachment point.
"""

from __future__ import annotations

from typing import Any

__all__ = ["ANCHOR_FIELDS", "CORNERS", "PLACEMENTS", "SIDES", "offset_pair", "style_problem"]

SIDES = ("below", "above", "start", "end")
CORNERS = ("top_start", "top_end", "bottom_start", "bottom_end", "center")
PLACEMENTS = (*SIDES, *CORNERS)


def offset_pair(value: Any, where: str) -> tuple[float, float]:
    """`[dx, dy]` (or a tuple) as the pair of floats tre takes; raises `ValueError` naming `where`."""
    if isinstance(value, (list, tuple)) and len(value) == 2 and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in value):
        return float(value[0]), float(value[1])
    raise ValueError(f"{where}: offset is a pair of pixels, [dx, dy], got {value!r}")


#: The style fields that place a node against another node in the tree.
ANCHOR_FIELDS = ("anchor", "placement", "offset")


def style_problem(field: str, value: Any) -> "str | None":
    """Why `value` is not one for the style field `field` of ANCHOR_FIELDS, or `None` (also for a field that is not one of them)."""
    if field == "anchor":
        if isinstance(value, str) and value.strip():
            return None
        return f"style.anchor is the name of the node to sit against (or `parent`), got {value!r}"
    if field == "placement":
        if value in PLACEMENTS:
            return None
        return f"style.placement is one of {', '.join(PLACEMENTS)}, got {value!r}"
    if field == "offset":
        try:
            offset_pair(value, "style")
        except ValueError:
            return f"style.offset is a pair of pixels, [dx, dy], got {value!r}"
    return None
