"""The sizes and insets a style may give, checked as tre takes them (tre 0.5.7), so a mistake is found where it is written.

- `width`, `height`: a number, `auto`, `fit-content`, a percentage, or a sum such as `calc(100% - 16)` or `100% - 16`;
- `min_width`, `max_width`, `min_height`, `max_height`, `flex_basis`: a number, `auto` or a percentage;
- `left`, `top`, `right`, `bottom`, `inset` (and `x`, `y`): a number, a percentage or `auto`.

A sum has terms (a number, a percentage, or pixels written `16px`) joined by ` + ` or ` - `, with a space each side; written without `calc( )` it has
at least two terms (`16px` alone is not a size). tre takes no negative size (an inset may be a negative number), no other unit (`vw`, `em`), no `*` or `/`,
and no `min()`. `tests/test_sizes.py` runs this against tre, so it fails if tre's own grammar moves. (tre also takes `50 %`, with a space, in some fields;
that is not copied.)
"""

from __future__ import annotations

import re
from typing import Any, Optional

__all__ = ["INSET_FIELDS", "SIZE_FIELDS", "size_problem"]

#: Sizes that also take `fit-content` and a sum.
SIZE_FIELDS = ("width", "height")
#: Sizes that take only a number, `auto` or a percentage.
LIMIT_FIELDS = ("min_width", "max_width", "min_height", "max_height", "flex_basis")
#: Where an absolute node sits, from each edge.
INSET_FIELDS = ("left", "top", "right", "bottom", "inset", "x", "y")

_PERCENT = re.compile(r"^\d+(?:\.\d+)?%$")
_TERM = r"\d+(?:\.\d+)?(?:%|px)?"
_SUM = re.compile(rf"^{_TERM}(?: [+-] {_TERM})*$")


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _sum(text: str) -> bool:
    """`calc(100% - 16)` (even one term), or `100% - 16` (two terms or more)."""
    if text.startswith("calc(") and text.endswith(")"):
        return bool(_SUM.match(text[5:-1].strip()))
    return bool(_SUM.match(text)) and " " in text


def size_problem(field: str, value: Any) -> Optional[str]:
    """Why `value` is not one that tre takes for style `field`, or `None` when it is (or when `field` is not a size or an inset)."""
    if field in SIZE_FIELDS:
        if (_is_number(value) and value >= 0) or value in ("auto", "fit-content"):
            return None
        if isinstance(value, str) and (_PERCENT.match(value) or _sum(value)):
            return None
        return _explain(field, value, "a number from 0, `auto`, `fit-content`, a percentage (`50%`), or a sum (`calc(100% - 16)` or `100% - 16`, a space each side of `+` and `-`)")
    if field in LIMIT_FIELDS or field in INSET_FIELDS:
        if (_is_number(value) and (value >= 0 or field in INSET_FIELDS)) or value == "auto" or (isinstance(value, str) and _PERCENT.match(value)):
            return None
        return _explain(field, value, "a number, `auto` or a percentage (`50%`)" if field in INSET_FIELDS else "a number from 0, `auto` or a percentage (`50%`)")
    return None


def _explain(field: str, value: Any, takes: str) -> str:
    hint = ""
    if isinstance(value, str):
        unit = re.search(r"\d(px|em|rem|vw|vh|pt)\b", value)
        if unit and "calc" not in value and value.endswith(unit.group(1)) and unit.group(1) != "px":
            hint = f" (`{unit.group(1)}` is not a unit here; sizes are pixels, so write the number)"
        elif re.match(r"^\d+(?:\.\d+)?px$", value):
            hint = f" (sizes are pixels already: write {value[:-2]})"
        elif value in ("stretch", "min-content", "max-content"):
            hint = " (to fill the room, use `flex: fill` or `flex: expand_horizontal`)"
        elif re.search(r"[*/]", value) or value.startswith("min(") or value.startswith("max("):
            hint = " (a sum has only `+` and `-`)"
        elif re.search(r"\S[+-]\S", value):
            hint = " (write a space each side of `+` and `-`)"
    return f"style.{field} must be {takes}, got {value!r}{hint}"
