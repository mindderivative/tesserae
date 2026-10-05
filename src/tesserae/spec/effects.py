"""Gradients and the visual effects of a style (tre 0.5.4): `blur`, `backdrop_blur`, `blend_mode`, `filter`,
`sticky` and `cursor`.

A gradient is given where a colour goes (`background`, `foreground`, `border_color`) as a CSS-like string or a
mapping:

    background: "linear-gradient(90deg, primary, tertiary)"
    background: "radial-gradient(at 30% 30%, primary_container, surface)"
    background: "conic-gradient(from 90deg, primary, secondary, primary)"
    background: {gradient: linear, angle: 90, stops: [primary, [0.6, secondary], tertiary]}

Stop colours are theme roles or CSS colours.
"""

from __future__ import annotations

import re
from typing import Any, Callable

__all__ = ["EFFECT_FIELDS", "cursor_value", "effect_props", "is_gradient", "make_gradient"]

RGBA = tuple[int, int, int, int]

#: The style keys `effect_props` reads.
EFFECT_FIELDS = frozenset({"blur", "backdrop_blur", "blend_mode", "filter", "sticky", "cursor"})

_FUNCTION = re.compile(r"^\s*(linear|radial|conic)-gradient\((.*)\)\s*$", re.DOTALL | re.IGNORECASE)
_KINDS = {"linear": "linear", "radial": "radial", "conic": "sweep", "sweep": "sweep"}
_SIDES = {"top": 0.0, "right": 90.0, "bottom": 180.0, "left": 270.0, "top right": 45.0, "right top": 45.0,
          "bottom right": 135.0, "right bottom": 135.0, "bottom left": 225.0, "left bottom": 225.0,
          "top left": 315.0, "left top": 315.0}
_FILTERS = ("saturate", "brightness", "contrast", "grayscale", "hue_rotate", "invert", "sepia")
_COLOUR_START = re.compile(r"^(#|rgb|hsl|hwb|lab|lch|oklab|oklch|color\()")


def is_gradient(raw: Any) -> bool:
    """Whether `raw` (a style colour) is a gradient rather than a colour."""
    if isinstance(raw, str):
        return _FUNCTION.match(raw) is not None
    return isinstance(raw, dict) and "gradient" in raw


def _split(text: str) -> list[str]:
    """`text` at its commas, except inside parentheses (`rgb(1, 2, 3)`)."""
    parts, depth, current = [], 0, []
    for char in text:
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        if char == "," and depth == 0:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    parts.append("".join(current).strip())
    return parts


def _number(text: str, unit: str, where: str) -> float:
    try:
        return float(text[: -len(unit)] if unit and text.endswith(unit) else text)
    except ValueError:
        raise ValueError(f"{where}: {text!r} is not a number") from None


def _position(text: str, where: str) -> float:
    """A stop's place or a centre coordinate: `50%` or `0.5`, as a fraction."""
    text = text.strip()
    return _number(text, "%", where) / 100.0 if text.endswith("%") else _number(text, "", where)


def _angle(text: str, where: str) -> float:
    for unit, scale in (("deg", 1.0), ("turn", 360.0), ("rad", 57.29577951308232)):
        if text.endswith(unit):
            return _number(text, unit, where) * scale
    return _number(text, "", where)


def _spread(stops: list[tuple[float | None, RGBA]]) -> list[tuple[float, RGBA]]:
    """Gives the stops with no place one, as CSS does: the first 0, the last 1, the rest evenly between."""
    if all(place is None for place, _ in stops):
        last = max(len(stops) - 1, 1)
        return [(i / last, color) for i, (_, color) in enumerate(stops)]
    places = [place for place, _ in stops]
    if places[0] is None:
        places[0] = 0.0
    if places[-1] is None:
        places[-1] = 1.0
    i = 0
    while i < len(places):
        if places[i] is None:
            j = i
            while places[j] is None:
                j += 1
            low, high = places[i - 1], places[j]
            for k in range(i, j):
                places[k] = low + (high - low) * (k - i + 1) / (j - i + 1)
            i = j
        i += 1
    running, out = 0.0, []
    for place, (_, color) in zip(places, stops):  # the places don't go back, as CSS fixes them
        running = max(running, place)
        out.append((running, color))
    return out


def _colour_stop(raw: Any, color: Callable[[Any], RGBA], where: str) -> tuple[float | None, RGBA]:
    if isinstance(raw, (list, tuple)) and len(raw) == 2 and not isinstance(raw[0], str):
        return float(raw[0]), color(raw[1])
    if isinstance(raw, dict):
        return (float(raw["offset"]) if "offset" in raw else None), color(raw.get("color"))
    if isinstance(raw, str):
        text = raw.strip()
        match = re.match(r"^(.*\S)\s+(-?[\d.]+%?)$", text)
        if match:
            try:
                return _position(match.group(2), where), color(match.group(1))
            except ValueError:
                pass
        return None, color(text)
    return None, color(raw)


def _centre(text: str, where: str) -> tuple[float, float]:
    parts = text.split()
    if len(parts) == 1:
        parts.append("50%")
    names = {"left": 0.0, "center": 0.5, "right": 1.0, "top": 0.0, "bottom": 1.0}
    values = [names[p] if p in names else _position(p, where) for p in parts[:2]]
    if parts[0] in ("top", "bottom") or parts[1] in ("left", "right"):
        values.reverse()
    return values[0], values[1]


def _parse(raw: str, color: Callable[[Any], RGBA], where: str) -> tuple[str, dict[str, Any], list[Any]]:
    match = _FUNCTION.match(raw)
    if match is None:
        raise ValueError(f"{where}: {raw!r} is not a linear-gradient(), radial-gradient() or conic-gradient()")
    kind, arguments = _KINDS[match.group(1).lower()], _split(match.group(2))
    spec: dict[str, Any] = {"angle": 180.0, "center": None, "radius": 1.0, "start": 0.0}
    head = arguments[0].lower()
    leading = not _COLOUR_START.match(head) and (
        head.startswith(("to ", "at ", "from ", "circle", "ellipse", "closest", "farthest"))
        or re.match(r"^-?[\d.]+(deg|turn|rad)?$", head) is not None)
    if leading:
        arguments = arguments[1:]
        if kind == "linear":
            if head.startswith("to "):
                side = " ".join(head[3:].split())
                if side not in _SIDES:
                    raise ValueError(f"{where}: unknown direction {head!r}")
                spec["angle"] = _SIDES[side]
            else:
                spec["angle"] = _angle(head, where)
        else:
            at = re.search(r"\bat\s+(.+)$", head)
            if at:
                spec["center"] = _centre(at.group(1), where)
                head = head[: at.start()].strip()
            if kind == "sweep" and head.startswith("from "):
                spec["start"] = _angle(head[5:].strip(), where)
    return kind, spec, arguments


def make_gradient(raw: Any, color: Callable[[Any], RGBA], where: str = "a gradient") -> Any:
    """`tre.Gradient` for the CSS-like string or mapping `raw`; `color` turns a stop's colour (a role or a CSS
    colour) into RGBA. Raises `ValueError`, naming `where`."""
    import tre

    if isinstance(raw, str):
        kind, spec, items = _parse(raw, color, where)
    elif isinstance(raw, dict):
        kind = _KINDS.get(str(raw.get("gradient")).lower(), "")
        if not kind:
            raise ValueError(f"{where}: gradient must be linear, radial or sweep, got {raw.get('gradient')!r}")
        unknown = set(raw) - {"gradient", "stops", "angle", "center", "radius", "start"}
        if unknown:
            raise ValueError(f"{where}: unknown gradient field(s) {sorted(unknown)}")
        items = raw.get("stops")
        if not isinstance(items, list):
            raise ValueError(f"{where}: a gradient needs stops: [...]")
        spec = {"angle": float(raw.get("angle", 180.0)), "radius": float(raw.get("radius", 1.0)),
                "start": float(raw.get("start", 0.0)),
                "center": tuple(float(v) for v in raw["center"]) if raw.get("center") is not None else None}
    else:
        raise ValueError(f"{where}: a gradient is a string or a mapping, got {type(raw).__name__}")
    if len(items) < 2:
        raise ValueError(f"{where}: a gradient needs at least two colours")
    stops = _spread([_colour_stop(item, color, where) for item in items])
    if kind == "linear":
        return tre.Gradient.linear(stops, spec["angle"])
    if kind == "radial":
        return tre.Gradient.radial(stops, spec["center"], spec["radius"])
    return tre.Gradient.sweep(stops, spec["center"], spec["start"])


def cursor_value(value: Any, where: str) -> Any:
    """A `cursor:` as the node property: a name (tre checks it), or a decoded picture (`{rgba, width, height,
    hotspot}`, made from `{src, hotspot}` where the view is read) as a `tre.CursorImage`."""
    import tre

    if isinstance(value, str):
        return value
    if isinstance(value, dict) and "rgba" in value:
        try:
            return tre.CursorImage(value["rgba"], int(value["width"]), int(value["height"]),
                                   hotspot=tuple(int(v) for v in value.get("hotspot", (0, 0))))
        except ValueError as exc:
            raise ValueError(f"{where}: cursor: {exc}") from None
    if isinstance(value, dict) and "src" in value:
        raise ValueError(f"{where}: cursor.src is read with the view, so only a node's own style: can give it")
    raise ValueError(f"{where}: cursor is a name or {{src: file.png, hotspot: [x, y]}}, got {value!r}")


def _filter(value: Any, where: str) -> Any:
    import tre

    if value is None or value is False:
        return None
    if not isinstance(value, dict) or not value:
        raise ValueError(f"{where}: filter is a mapping of {', '.join(_FILTERS)}, got {value!r}")
    for key in value:
        if key not in _FILTERS:
            raise ValueError(f"{where}: unknown filter {key!r}, expected one of {', '.join(_FILTERS)}")
    try:
        return tre.Shader.filter(**{k: float(v) for k, v in value.items()})
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{where}: filter: {exc}") from None


def _non_negative(value: Any, name: str, where: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{where}: {name} must be a number of pixels, got {value!r}") from None
    if number < 0:
        raise ValueError(f"{where}: {name} must be 0 or more, got {value!r}")
    return number


def effect_props(style: dict[str, Any], where: str, *, cursor: bool = True) -> dict[str, Any]:
    """The node properties for the effects `style` gives, and the resting value for each it doesn't (so a patch
    clears what the style no longer asks for). `cursor=False` leaves `cursor` out (a kind that sets its own)."""
    props: dict[str, Any] = {
        "blur": _non_negative(style.get("blur", 0.0), "blur", where),
        "backdrop_blur": _non_negative(style.get("backdrop_blur", 0.0), "backdrop_blur", where),
        "blend_mode": str(style.get("blend_mode", "normal")),
        "shader": _filter(style.get("filter"), where),
        "sticky": None if style.get("sticky") is None else float(style["sticky"]),
    }
    if cursor:
        props["cursor"] = cursor_value(style["cursor"], where) if style.get("cursor") is not None else None
    return props
