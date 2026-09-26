"""`tesserae.Theme` (M38 Phase 1): one resolved MD3 theme, answering
everything `tre`'s `Window.theme` answers today -- colour roles, per-component
shape and elevation, typography -- plus MD3's motion tokens. `tre` 0.3.5
removes its theme (D7); Tesserae's widgets (M39–M42) read this one.

A theme is resolved from the same four inputs as a view: a seed, the
dark flag, and the default and custom theme dicts (`seed:`, `colors:`,
`styles:`, `components:`, `typography:`). The default theme defaults to
`tre`'s shipped one.

- **Roles:** `tokens.resolve_scheme`, `tre`'s `View` rules (the seed from
  `theme_seed`, else the custom theme's, else the default's; `colors:`
  overrides default then custom). `None` for every role with no seed.
- **`components:`:** per-component `corner_radius`/`elevation`, numbers or
  shape/elevation tokens. A custom theme's entry replaces the default
  theme's entry for the same key. `shape("card", "elevated")` looks up
  `card.elevated` first, then `card`, field by field -- `tre`'s lookup.
- **`typography:`:** per-role field overrides on the MD3 type scale; a
  custom theme's entry for a role replaces the default theme's.
- **Motion:** MD3's easing curves as the `(x1, y1, x2, y2)` tuples `tre`
  0.3.4's `animate(easing=...)` takes, and MD3's duration tokens in ms.
  `emphasized` is MD3's single-bézier form (0.2, 0, 0, 1): `tre`'s own
  Emphasized is two cubic segments, which one bézier can't express (M38
  Q4).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, Union

from tesserae import tokens

__all__ = ["DURATIONS", "EASINGS", "Theme"]

RGBA = tuple[int, int, int, int]
Easing = Union[str, tuple[float, float, float, float]]

#: MD3's easing tokens. `tre`'s curves, except `emphasized` (see above).
EASINGS: dict[str, Easing] = {
    "linear": "linear",
    "standard": (0.2, 0.0, 0.0, 1.0),
    "standard_decelerate": (0.0, 0.0, 0.0, 1.0),
    "standard_accelerate": (0.3, 0.0, 1.0, 1.0),
    "emphasized": (0.2, 0.0, 0.0, 1.0),
    "emphasized_decelerate": (0.05, 0.7, 0.1, 1.0),
    "emphasized_accelerate": (0.3, 0.0, 0.8, 0.15),
}

#: MD3's duration tokens, in milliseconds.
DURATIONS: dict[str, int] = {
    **{f"short{i}": 50 * i for i in range(1, 5)},
    **{f"medium{i}": 200 + 50 * i for i in range(1, 5)},
    **{f"long{i}": 400 + 50 * i for i in range(1, 5)},
    **{f"extra_long{i}": 600 + 100 * i for i in range(1, 5)},
}

_COMPONENT_FIELDS = ("corner_radius", "elevation")
_TYPE_FIELDS = ("font_family", "font_weight", "font_size", "line_height")


@dataclass(frozen=True)
class _Component:
    corner_radius: Optional[float] = None
    elevation: Optional[float] = None


@dataclass(frozen=True)
class Theme:
    """A resolved theme. Build one with `Theme.resolve(...)`."""

    seed: Optional[RGBA]
    dark: bool
    roles: Optional[dict[str, RGBA]]
    components: dict[str, _Component] = field(default_factory=dict)
    type_overrides: dict[str, dict[str, Any]] = field(default_factory=dict)

    @classmethod
    def resolve(
        cls,
        theme_seed: Optional[RGBA] = None,
        dark: bool = False,
        default_theme_spec: Optional[dict[str, Any]] = None,
        custom_theme_spec: Optional[dict[str, Any]] = None,
    ) -> "Theme":
        """Resolves a theme; raises `ValueError` for an unknown role, an
        unknown token in `components:` or an unknown `typography:` field."""
        from tesserae.spec.build import shipped_default_theme
        from tesserae.spec.cascade import check_theme

        default = default_theme_spec if default_theme_spec is not None else shipped_default_theme()
        for arg, spec in (("default_theme_spec", default), ("custom_theme_spec", custom_theme_spec)):
            try:
                check_theme(spec)
            except ValueError as exc:
                raise ValueError(f"{arg}=: {exc}") from None
        roles = tokens.resolve_scheme(theme_seed, dark, default, custom_theme_spec)
        components: dict[str, _Component] = {}
        type_overrides: dict[str, dict[str, Any]] = {}
        for spec in (default, custom_theme_spec):
            for key, raw in ((spec or {}).get("components") or {}).items():
                components[key] = _component(key, raw)
            for role, raw in ((spec or {}).get("typography") or {}).items():
                type_overrides[role] = _type_override(role, raw)
        seed = theme_seed or _seed(custom_theme_spec) or _seed(default)
        return cls(seed, dark, roles, components, type_overrides)

    # -- colour ----------------------------------------------------------------

    @property
    def is_set(self) -> bool:
        """Whether there's a colour scheme (a seed was given somewhere)."""
        return self.roles is not None

    def role(self, name: str) -> Optional[RGBA]:
        """An MD3 colour role, or `None` without a scheme or for an
        unknown name."""
        return (self.roles or {}).get(name)

    # -- shape and elevation --------------------------------------------------------

    def shape(self, component: str, variant: Optional[str] = None) -> Optional[float]:
        """A component's corner radius from `components:`, or `None` when
        the theme doesn't say (the widget uses its own MD3 default)."""
        return self._lookup(component, variant, "corner_radius")

    def elevation(self, component: str, variant: Optional[str] = None) -> Optional[float]:
        """A component's elevation level from `components:`, or `None`."""
        return self._lookup(component, variant, "elevation")

    def _lookup(self, component: str, variant: Optional[str], name: str) -> Optional[float]:
        if variant is not None:
            value = getattr(self.components.get(f"{component}.{variant}", _Component()), name)
            if value is not None:
                return value
        return getattr(self.components.get(component, _Component()), name)

    # -- typography -------------------------------------------------------------------

    def typography(self, role: str) -> Optional[tokens.TypeStyle]:
        """An MD3 type role with the theme's `typography:` overrides, or
        `None` for an unknown role."""
        base = tokens.type_style(role)
        if base is None:
            return None
        override = self.type_overrides.get(role, {})
        return tokens.TypeStyle(**{f: override.get(f, getattr(base, f)) for f in _TYPE_FIELDS})

    # -- motion ---------------------------------------------------------------------------

    @staticmethod
    def easing(name: str) -> Easing:
        """An MD3 easing token, as `animate(easing=...)` takes it."""
        try:
            return EASINGS[name]
        except KeyError:
            raise ValueError(f"unknown easing {name!r}; expected one of {sorted(EASINGS)}") from None

    @staticmethod
    def duration(name: str) -> int:
        """An MD3 duration token, in milliseconds."""
        try:
            return DURATIONS[name]
        except KeyError:
            raise ValueError(f"unknown duration {name!r}; expected one of {sorted(DURATIONS)}") from None


def _seed(spec: Optional[dict[str, Any]]) -> Optional[RGBA]:
    raw = (spec or {}).get("seed")
    return tokens.parse_color(raw) if isinstance(raw, str) else None


def _component(key: str, raw: Any) -> _Component:
    if not isinstance(raw, dict):
        raise ValueError(f"components: {key!r} must be a mapping, got {type(raw).__name__}")
    unknown = set(raw) - set(_COMPONENT_FIELDS)
    if unknown:
        raise ValueError(f"components: {key!r} has unknown field(s) {sorted(unknown)}")
    values = {}
    for name, lookup in (("corner_radius", tokens.shape), ("elevation", tokens.elevation)):
        value = raw.get(name)
        if isinstance(value, str):
            resolved = lookup(value)
            if resolved is None:
                raise ValueError(f"components: {key!r} has an unknown {name} token: {value!r}")  # tre's wording
            value = resolved
        values[name] = float(value) if value is not None else None
    return _Component(**values)


def _type_override(role: str, raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError(f"typography: {role!r} must be a mapping, got {type(raw).__name__}")
    unknown = set(raw) - set(_TYPE_FIELDS)
    if unknown:
        raise ValueError(f"typography: {role!r} has unknown field(s) {sorted(unknown)}")
    return {k: (float(v) if k != "font_family" else v) for k, v in raw.items() if v is not None}
