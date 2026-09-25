"""MD3 design tokens, owned by Tesserae (M37 Phase 1, from M38): the
colour scheme from a seed, the shape and elevation scales, MD3 elevation
as `shadows`, the type scale, and colour parsing.

`tre` resolves these today, in `engine-md3` and `engine-render`, and
removes them in 0.3.5 (its D7: `tre` keeps no theme). The values here are
`tre`'s at v0.3.4, and `tests/test_tokens.py` checks them against `tre`
while it still has them:

- **colour roles** come from `materialyoucolor`'s TonalSpot scheme with
  `spec_version="2021"`, which `tre`'s `material-colors` 0.4.2 follows,
  plus tone 10 for the four light-mode `on_*_container` roles, where
  newer `material-color-utilities` moved to tone 30 (M34's spike: 784 of
  784 role values identical);
- **shapes** and **elevation levels** are `tre`'s `engine-md3` scales;
- **elevation as shadows**: 0.3.4 nodes have no `elevation`, only
  `shadows`, so a level becomes `tre`'s own key and ambient shadow pair,
  with `engine-render`'s geometry, key first (it paints on top);
- **type styles** are `tre`'s 15 MD3 roles.
"""

from __future__ import annotations

import colorsys
import re
from dataclasses import dataclass
from typing import Any, Optional, Tuple

from materialyoucolor.dynamiccolor.material_dynamic_colors import MaterialDynamicColors
from materialyoucolor.hct import Hct
from materialyoucolor.scheme.scheme_tonal_spot import SchemeTonalSpot
from PIL import ImageColor

__all__ = [
    "ELEVATION_LEVELS", "ROLES", "SHAPES", "TYPE_SCALE", "TypeStyle", "color_scheme",
    "elevation", "elevation_shadows", "parse_color", "resolve_scheme", "shape", "type_style",
]

RGBA = Tuple[int, int, int, int]

# -- colour -------------------------------------------------------------------

#: Every role `tre`'s `ColorScheme.role` answers, in its order.
ROLES = (
    "primary", "on_primary", "primary_container", "on_primary_container", "inverse_primary",
    "primary_fixed", "primary_fixed_dim", "on_primary_fixed", "on_primary_fixed_variant",
    "secondary", "on_secondary", "secondary_container", "on_secondary_container",
    "secondary_fixed", "secondary_fixed_dim", "on_secondary_fixed", "on_secondary_fixed_variant",
    "tertiary", "on_tertiary", "tertiary_container", "on_tertiary_container",
    "tertiary_fixed", "tertiary_fixed_dim", "on_tertiary_fixed", "on_tertiary_fixed_variant",
    "error", "on_error", "error_container", "on_error_container",
    "surface_dim", "surface", "surface_tint", "surface_bright",
    "surface_container_lowest", "surface_container_low", "surface_container",
    "surface_container_high", "surface_container_highest",
    "on_surface", "on_surface_variant", "outline", "outline_variant",
    "inverse_surface", "inverse_on_surface", "surface_variant",
    "background", "on_background", "shadow", "scrim",
)

#: The four roles `tre` keeps at tone 10 in light mode.
_TONE_10_LIGHT = {
    "on_primary_container": "primary_palette",
    "on_secondary_container": "secondary_palette",
    "on_tertiary_container": "tertiary_palette",
    "on_error_container": "error_palette",
}


def _argb_to_rgba(argb: int) -> RGBA:
    return ((argb >> 16) & 0xFF, (argb >> 8) & 0xFF, argb & 0xFF, (argb >> 24) & 0xFF)


def _camel(role: str) -> str:
    head, *rest = role.split("_")
    return head + "".join(word.capitalize() for word in rest)


def color_scheme(seed: RGBA, dark: bool = False) -> dict[str, RGBA]:
    """Every MD3 role for `seed`, light or dark, as `tre` computes it."""
    r, g, b = seed[0], seed[1], seed[2]
    argb = 0xFF000000 | (r << 16) | (g << 8) | b
    scheme = SchemeTonalSpot(Hct.from_int(argb), dark, 0.0, spec_version="2021")
    roles: dict[str, RGBA] = {}
    for role in ROLES:
        if not dark and role in _TONE_10_LIGHT:
            roles[role] = _argb_to_rgba(getattr(scheme, _TONE_10_LIGHT[role]).tone(10))
            continue
        dynamic = getattr(MaterialDynamicColors, role, None) or getattr(MaterialDynamicColors, _camel(role))
        roles[role] = _argb_to_rgba(dynamic.get_argb(scheme))
    return roles


_FUNC = re.compile(r"^(rgba?|hsla?)\((.*)\)$", re.IGNORECASE)
_UNSUPPORTED = re.compile(r"^(color|lab|lch|oklab|oklch|hwb)\(", re.IGNORECASE)


def _alpha(text: str) -> int:
    value = float(text[:-1]) / 100 if text.endswith("%") else float(text)
    return int(_clamp(value, 0.0, 1.0) * 255 + 0.5)


def _functional(name: str, body: str) -> RGBA:
    """`rgb()`/`rgba()`/`hsl()`/`hsla()`, in CSS Color 4's comma or
    space syntax, with an optional alpha (`, a` or `/ a`)."""
    if "/" in body:
        main, alpha_text = body.split("/", 1)
        parts = main.split()
    else:
        main, alpha_text = body, None
        parts = [p.strip() for p in main.split(",")] if "," in main else main.split()
        if len(parts) == 4:
            parts, alpha_text = parts[:3], parts[3]
    if len(parts) != 3:
        raise ValueError
    alpha = _alpha(alpha_text.strip()) if alpha_text is not None else 255
    if name.lower().startswith("rgb"):
        channels = [
            int(_clamp(float(p[:-1]) / 100 * 255 if p.endswith("%") else float(p), 0, 255) + 0.5) for p in parts
        ]
        return (channels[0], channels[1], channels[2], alpha)
    hue = float(parts[0][:-3] if parts[0].endswith("deg") else parts[0]) % 360
    sat, light = (_clamp(float(p.rstrip("%")) / 100, 0, 1) for p in parts[1:])
    r, g, b = colorsys.hls_to_rgb(hue / 360, light, sat)
    return (int(r * 255 + 0.5), int(g * 255 + 0.5), int(b * 255 + 0.5), alpha)


def parse_color(raw: str) -> RGBA:
    """A colour string as `tre` parses it: hex (`#RGB`, `#RGBA`,
    `#RRGGBB`, `#RRGGBBAA`), a CSS colour name, `transparent`, or
    `rgb()`/`rgba()`/`hsl()`/`hsla()` in CSS Color 4's comma or space
    syntax with an optional alpha. `tre` also accepts CSS's wide-gamut
    functions (`color()`, `lab()`, `lch()`, `oklab()`, `oklch()`, `hwb()`);
    Tesserae doesn't yet and says so. Raises `ValueError`."""
    text = raw.strip()
    if text.lower() == "transparent":
        return (0, 0, 0, 0)
    if _UNSUPPORTED.match(text):
        raise ValueError(f"color {raw!r}: {text.split('(')[0]}() colours aren't supported by Tesserae yet")
    match = _FUNC.match(text)
    if match:
        try:
            return _functional(match.group(1), match.group(2))
        except ValueError:
            raise ValueError(f"invalid color {raw!r}") from None
    if text.startswith("#") and len(text) == 5:  # #RGBA, which Pillow reads differently
        text = "#" + "".join(c * 2 for c in text[1:])
    try:
        value = ImageColor.getrgb(text)
    except ValueError as exc:
        raise ValueError(f"invalid color {raw!r}") from exc
    return tuple(value) if len(value) == 4 else (*value, 255)


def _seed_of(theme: Optional[dict[str, Any]]) -> Optional[RGBA]:
    raw = (theme or {}).get("seed")
    return parse_color(raw) if isinstance(raw, str) else None


def resolve_scheme(
    theme_seed: Optional[RGBA],
    dark: bool,
    default_theme: Optional[dict[str, Any]],
    custom_theme: Optional[dict[str, Any]],
) -> Optional[dict[str, RGBA]]:
    """The scheme a view resolves roles against, by `tre`'s `View` rules:
    the seed is `theme_seed`, else the custom theme's `seed:`, else the
    default theme's; `colors:` overrides apply default theme first, then
    custom. `None` when there's no seed at all: roles then don't resolve,
    as in `tre`."""
    seed = theme_seed or _seed_of(custom_theme) or _seed_of(default_theme)
    if seed is None:
        return None
    roles = color_scheme(seed, dark)
    for theme in (default_theme, custom_theme):
        for role, raw in ((theme or {}).get("colors") or {}).items():
            if role not in roles:
                raise ValueError(f"unknown color role {role!r} in theme colors")
            roles[role] = parse_color(raw)
    return roles


# -- shape and elevation ---------------------------------------------------------

#: `tre`'s shape scale, in pixels.
SHAPES = {"none": 0.0, "extra_small": 4.0, "small": 8.0, "medium": 12.0, "large": 16.0, "extra_large": 28.0}
#: `tre`'s elevation levels.
ELEVATION_LEVELS = {f"level_{n}": float(n) for n in range(6)}


def shape(name: str) -> Optional[float]:
    return SHAPES.get(name)


def elevation(name: str) -> Optional[float]:
    return ELEVATION_LEVELS.get(name)


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


Shadow = Tuple[RGBA, float, float, float, float]


def elevation_shadows(level: float) -> list[Shadow]:
    """MD3 elevation `level` (0–5, fractional allowed) as a `shadows` list,
    `(color, offset_x, offset_y, blur, spread)`: `tre`'s key shadow (30%
    black) first, so it paints on top, then its ambient shadow (15%).
    Level 0 is no shadow.

    One difference from `tre`'s legacy `elevation`: its ambient shadow
    keeps the node's corner radius, while a `shadows` entry grows it by
    the spread, as CSS does."""
    if level <= 0:
        return []
    key_y = _clamp(level, 0, 1) + _clamp(level - 3, 0, 1) + 2 * _clamp(level - 4, 0, 1)
    key_blur = 2 * _clamp(level, 0, 1) + _clamp(level - 2, 0, 1) + _clamp(level - 4, 0, 1)
    ambient_y = _clamp(level, 0, 1) + _clamp(level - 1, 0, 1) + 2 * _clamp(level - 2, 0, 3)
    ambient_blur = 3 * _clamp(level, 0, 2) + 2 * _clamp(level - 2, 0, 3)
    ambient_spread = _clamp(level, 0, 4) + 2 * _clamp(level - 4, 0, 1)
    return [
        ((0, 0, 0, int(0.30 * 255 + 0.5)), 0.0, float(key_y), float(key_blur), 0.0),
        ((0, 0, 0, int(0.15 * 255 + 0.5)), 0.0, float(ambient_y), float(ambient_blur), float(ambient_spread)),
    ]


# -- type scale --------------------------------------------------------------------


@dataclass(frozen=True)
class TypeStyle:
    font_family: str
    font_weight: float
    font_size: float
    #: A multiple of `font_size`.
    line_height: float


def _roboto(weight: float, size: float, line_height: float) -> TypeStyle:
    return TypeStyle("Roboto", weight, size, line_height)


#: `tre`'s 15 MD3 type roles.
TYPE_SCALE = {
    "display_large": _roboto(400, 57, 1.12), "display_medium": _roboto(400, 45, 1.16),
    "display_small": _roboto(400, 36, 1.22), "headline_large": _roboto(400, 32, 1.25),
    "headline_medium": _roboto(400, 28, 1.29), "headline_small": _roboto(400, 24, 1.33),
    "title_large": _roboto(400, 22, 1.27), "title_medium": _roboto(500, 16, 1.50),
    "title_small": _roboto(500, 14, 1.43), "body_large": _roboto(400, 16, 1.50),
    "body_medium": _roboto(400, 14, 1.43), "body_small": _roboto(400, 12, 1.33),
    "label_large": _roboto(500, 14, 1.43), "label_medium": _roboto(500, 12, 1.33),
    "label_small": _roboto(500, 11, 1.45),
}


def type_style(role: str) -> Optional[TypeStyle]:
    return TYPE_SCALE.get(role)
