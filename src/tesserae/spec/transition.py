"""`transition:` in a style: a property that changes eases to its new value instead of jumping (#214).

```yaml
style:
  background: primary
  transition:
    background: 150                                  # milliseconds, with the standard easing
    opacity: {duration: 200, easing: emphasized_decelerate}
    scale: {duration: 300, easing: spring, bounce: 0.3}
    all: 100                                         # whatever else can ease
```

Only a *change* eases: the first time a node is built it is where it says. The properties are the ones tre can animate (`background`,
`foreground` for text and glyphs, `border_color`, `border_width`, `corner_radius`, `elevation`, `opacity`, `blur`, `backdrop_blur`, `scale`,
`translate_x`, `translate_y`, `rotation_deg`, and `icon` on an `Icon`: one glyph morphing into the next); layout properties (`width`, `height`, `x`, `y`, `gap`, `padding`, `margin`) ease too, in pixels (a change to or from `auto` or a percentage is made at once). An app that asked for reduced
motion gets the new value at once.

`plan(...)` turns the style's `transition:` into `{node property: (milliseconds, easing)}`; the builder's `patch` animates those.
"""

from __future__ import annotations

from typing import Any, Optional, Union

__all__ = ["EASINGS", "LAYOUT_TRANSITIONABLE", "TRANSITIONABLE", "plan"]

Easing = Union[str, tuple[float, float, float, float], tuple[str, float]]

#: Material 3's easing curves as cubic beziers (Material Web's values), plus `linear`; `spring` takes a `bounce`.
EASINGS: dict[str, Easing] = {
    "linear": "linear",
    "standard": (0.2, 0.0, 0.0, 1.0),
    "standard_accelerate": (0.3, 0.0, 1.0, 1.0),
    "standard_decelerate": (0.0, 0.0, 0.0, 1.0),
    "emphasized": (0.3, 0.0, 0.0, 1.0),
    "emphasized_accelerate": (0.3, 0.0, 0.8, 0.15),
    "emphasized_decelerate": (0.05, 0.7, 0.1, 1.0),
}
DEFAULT_EASING = "standard"
#: The style fields that can ease, and the node property each is. `background` and `foreground` are both `fill`, of different nodes.
TRANSITIONABLE: dict[str, str] = {
    "background": "fill", "foreground": "fill", "border_color": "stroke_color", "border_width": "stroke_width", "corner_radius": "corner_radius",
    "elevation": "shadows", "opacity": "opacity", "blur": "blur", "backdrop_blur": "backdrop_blur", "scale": "scale", "translate_x": "translate_x",
    "translate_y": "translate_y", "rotation_deg": "rotation_deg",
    "icon": "data",  # an Icon's glyph morphs into the next one's (two closed shapes, or two open lines, in one view box); `all` does not include it
}
#: The layout fields that ease too, each the node properties it is. The engine animates them in pixels (tre 0.5.6); `all` leaves them out, since a layout that changes is not always meant to glide.
LAYOUT_TRANSITIONABLE: dict[str, tuple[str, ...]] = {
    "width": ("width",), "height": ("height",), "x": ("x",), "y": ("y",), "gap": ("gap",),
    "padding": ("padding_top", "padding_right", "padding_bottom", "padding_left"),
    "margin": ("margin_top", "margin_right", "margin_bottom", "margin_left"),
}
#: The kinds whose `fill` is the text or glyph colour (`foreground`); on every other kind `fill` is the `background`.
_FOREGROUND_FILL = frozenset({"Text", "Link", "Icon", "Svg"})


def _easing(where: str, name: Any, bounce: Any) -> Easing:
    if name == "spring":
        if bounce is None:
            return "spring"
        if isinstance(bounce, bool) or not isinstance(bounce, (int, float)) or not -1 < bounce < 1:
            raise ValueError(f"{where}: bounce is a number between -1 and 1, not {bounce!r}")
        return ("spring", float(bounce))
    if bounce is not None:
        raise ValueError(f"{where}: bounce goes with easing: spring")
    if isinstance(name, str):
        if name not in EASINGS:
            raise ValueError(f"{where}: easing is one of {', '.join([*EASINGS, 'spring'])} or four numbers, not {name!r}")
        return EASINGS[name]
    if isinstance(name, (list, tuple)) and len(name) == 4 and all(isinstance(n, (int, float)) and not isinstance(n, bool) for n in name):
        return (float(name[0]), float(name[1]), float(name[2]), float(name[3]))
    raise ValueError(f"{where}: easing is one of {', '.join([*EASINGS, 'spring'])} or four numbers, not {name!r}")


def _entry(where: str, value: Any) -> tuple[float, Easing]:
    if isinstance(value, bool):
        raise ValueError(f"{where}: a duration in milliseconds or {{duration, easing}}, not {value!r}")
    if isinstance(value, (int, float)):
        duration, easing, bounce = value, DEFAULT_EASING, None
    elif isinstance(value, dict):
        unknown = set(value) - {"duration", "easing", "bounce"}
        if unknown:
            raise ValueError(f"{where}: unknown key(s) {sorted(unknown)} (duration, easing, bounce)")
        duration, easing, bounce = value.get("duration"), value.get("easing", DEFAULT_EASING), value.get("bounce")
    else:
        raise ValueError(f"{where}: a duration in milliseconds or {{duration, easing}}, not {value!r}")
    if isinstance(duration, bool) or not isinstance(duration, (int, float)) or duration < 0:
        raise ValueError(f"{where}: duration is milliseconds, 0 or more, not {duration!r}")
    return float(duration), _easing(where, easing, bounce)


def plan(node_id: str, kind: str, style: dict[str, Any]) -> dict[str, tuple[float, Easing]]:
    """The style's `transition:` as `{node property: (milliseconds, easing)}` for a node of `kind`. Raises `ValueError` naming the widget."""
    raw: Optional[Any] = style.get("transition")
    if raw is None:
        return {}
    where = f'widget "{node_id}": style.transition'
    if not isinstance(raw, dict):
        raise ValueError(f"{where} is a mapping of style fields to durations, not {raw!r}")
    unknown = [k for k in raw if k != "all" and k not in TRANSITIONABLE and k not in LAYOUT_TRANSITIONABLE]
    if unknown:
        raise ValueError(f"{where}: '{unknown[0]}' cannot ease (it can: {', '.join([*TRANSITIONABLE, *LAYOUT_TRANSITIONABLE])}; or 'all')")
    out: dict[str, tuple[float, Easing]] = {}
    fill_field = "foreground" if kind in _FOREGROUND_FILL else "background"
    if "all" in raw:
        every = _entry(f"{where}.all", raw["all"])
        out.update({prop: every for field, prop in TRANSITIONABLE.items() if field not in ("background", "foreground", "icon")})
        out["fill"] = every
    for field, value in raw.items():
        if field == "all":
            continue
        if field in LAYOUT_TRANSITIONABLE:
            entry = _entry(f"{where}.{field}", value)
            out.update({prop: entry for prop in LAYOUT_TRANSITIONABLE[field]})
            continue
        prop = TRANSITIONABLE[field]
        if prop == "data" and kind != "Icon":
            continue  # only an Icon has a glyph to morph
        if prop == "fill" and field != fill_field:
            continue  # a Text's `fill` is its foreground and a box's its background; the other is not this node's to ease
        out[prop] = _entry(f"{where}.{field}", value)
    return out
