"""How a style says where children go and how a node takes room.

The style fields are Tesserae's own vocabulary; the engine's (`align_items`, `justify_content`, `flex_grow`, ...)
are what they are turned into, in one place, here:

- `align_content` places a node's children: one of nine positions (`top_left` ... `bottom_right`). Which of
  the engine's two axes each half is on depends on the node's `flex_direction`.
- `spread` distributes the children along the main axis: `between`, `around` or `evenly`.
- `flex` is a node's own sizing in its parent: `none` (the default: as big as its content, never squeezed),
  `expand_horizontal`, `expand_vertical` or `fill`. Which axis is the parent's main one depends on the
  parent's `flex_direction`.
- `align_self` takes the same nine positions: a child's own place in its parent.
- `align_wrapped` (a wrapping node's lines), and `align_tracks` and `align_cells` (a grid's tracks, and where
  items sit in their cells) are for the nodes that have them.

The engine's names are refused, with the name that replaces each.
"""

from __future__ import annotations

from typing import Any, Optional

__all__ = [
    "ALIGN_TRACKS", "FLEXES", "LAYOUT_FIELDS", "LayoutError", "POSITIONS", "REPLACED", "SPREADS", "engine_style",
]

#: Each position as (horizontal, vertical).
POSITIONS: dict[str, tuple[str, str]] = {
    "top_left": ("left", "top"), "top": ("center", "top"), "top_right": ("right", "top"),
    "left": ("left", "center"), "center": ("center", "center"), "right": ("right", "center"),
    "bottom_left": ("left", "bottom"), "bottom": ("center", "bottom"), "bottom_right": ("right", "bottom"),
}
SPREADS = ("none", "between", "around", "evenly")
FLEXES = ("none", "expand_horizontal", "expand_vertical", "fill")
#: How the lines of a wrapping node, or the tracks of a grid, share the room left over.
ALIGN_TRACKS = ("start", "center", "end", "stretch", "between", "around", "evenly")

#: The fields this module owns.
LAYOUT_FIELDS = frozenset({"align_content", "spread", "flex", "align_self", "align_wrapped", "align_tracks", "align_cells"})

#: The engine's names, and what replaces each.
REPLACED: dict[str, str] = {
    "align_items": "align_content (a position such as `center` or `top_left`)",
    "justify_content": "align_content (a position), or `spread` (between, around, evenly)",
    "justify_self": "align_self (a position)",
    "justify_items": "align_cells (a position)",
    "flex_grow": "flex (expand_horizontal, expand_vertical, fill, none)",
    "flex_shrink": "flex (expand_horizontal, expand_vertical, fill, none)",
    "flex_basis": "flex (expand_horizontal, expand_vertical, fill, none), and width or height",
}

_END = {"left": "start", "top": "start", "center": "center", "right": "end", "bottom": "end"}
_TRACK = {"start": "start", "center": "center", "end": "end", "stretch": "stretch",
          "between": "space_between", "around": "space_around", "evenly": "space_evenly"}


#: The engine's own names are accepted, and passed through as they are, with its defaults. For tests that
#: compare Tesserae with answers recorded from the engine; nothing else turns it on.
LEGACY_ENGINE_NAMES = False


class LayoutError(ValueError):
    """A layout field that can't be used; the message names the field and what it takes."""


def _choose(node_id: str, field: str, value: Any, allowed: Any) -> Any:
    if value not in allowed:
        raise LayoutError(f'widget "{node_id}": style.{field} must be one of {", ".join(allowed)}, got {value!r}')
    return value


def _position(node_id: str, field: str, value: Any) -> tuple[str, str]:
    return POSITIONS[_choose(node_id, field, value, tuple(POSITIONS))]


def engine_style(node_id: str, style: dict[str, Any], parent: Optional[tuple[str, str]] = None) -> dict[str, Any]:
    """`style` with this module's fields replaced by the engine's, for a node whose parent has the layout
    `parent` = `(flex_direction, display)` (a row by default). Raises `LayoutError` for an engine name, a value
    that isn't one of the field's, or a field the node can't use."""
    if LEGACY_ENGINE_NAMES:
        return dict(style)
    for old, new in REPLACED.items():
        if old in style:
            raise LayoutError(f'widget "{node_id}": style.{old} is now {new}')
    out = {k: v for k, v in style.items() if k not in LAYOUT_FIELDS}
    direction = style.get("flex_direction", "horizontal")
    grid = style.get("display") == "grid"
    parent_direction, parent_display = parent or ("horizontal", "flex")

    # the node's own children
    if grid and ("align_content" in style or "spread" in style):
        raise LayoutError(f'widget "{node_id}": a grid places its items with style.align_cells and spreads its '
                          "tracks with style.align_tracks, not align_content or spread")
    if "align_content" in style:
        horizontal, vertical = _position(node_id, "align_content", style["align_content"])
        main, cross = (horizontal, vertical) if direction == "horizontal" else (vertical, horizontal)
        out["justify_content"], out["align_items"] = _END[main], _END[cross]
    if "spread" in style:
        spread = _choose(node_id, "spread", style["spread"], SPREADS)
        if spread != "none":
            out["justify_content"] = _TRACK[spread]
    if "align_wrapped" in style:
        if style.get("flex_wrap") != "wrap" or grid:
            raise LayoutError(f'widget "{node_id}": style.align_wrapped is for a node with flex_wrap: wrap')
        out["align_content"] = _TRACK[_choose(node_id, "align_wrapped", style["align_wrapped"], ALIGN_TRACKS)]
    if ("align_tracks" in style or "align_cells" in style) and not grid:
        raise LayoutError(f'widget "{node_id}": style.align_tracks and style.align_cells are for display: grid')
    if "align_tracks" in style:
        track = _TRACK[_choose(node_id, "align_tracks", style["align_tracks"], ALIGN_TRACKS)]
        out["justify_content"] = out["align_content"] = track
    if "align_cells" in style:
        horizontal, vertical = _position(node_id, "align_cells", style["align_cells"])
        out["justify_items"], out["align_items"] = _END[horizontal], _END[vertical]

    # the node in its parent
    if "align_self" in style:
        horizontal, vertical = _position(node_id, "align_self", style["align_self"])
        if parent_display == "grid":
            out["justify_self"], out["align_self"] = _END[horizontal], _END[vertical]
        else:  # a flex parent places a child itself only across its main axis
            out["align_self"] = _END[vertical if parent_direction == "horizontal" else horizontal]
    flex = _choose(node_id, "flex", style.get("flex", "none"), FLEXES)
    out["flex_grow"], out["flex_shrink"] = 0.0, 0.0
    axes = ("horizontal", "vertical") if flex == "fill" else (() if flex == "none" else (flex.removeprefix("expand_"),))
    for axis in axes:
        size = "width" if axis == "horizontal" else "height"
        if parent_display == "grid" or axis != parent_direction:  # across the parent's main axis: stretch
            out.pop(size, None)
            out["justify_self" if parent_display == "grid" and axis == "horizontal" else "align_self"] = "stretch"
            out["_fill_x" if axis == "horizontal" else "_fill_y"] = True
        else:  # along it: take the room left over, starting from its own size
            out["flex_grow"], out["flex_shrink"] = 1.0, 1.0
    return out
