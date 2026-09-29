"""The style cascade, owned by Tesserae (M37 Phase 2): a port of `tre`'s
`engine-spec/src/cascade.rs` at v0.3.4, which `tre` removes in 0.3.5.

Precedence, lowest first:

- **layers:** the default theme's `styles:`, then the custom theme's, then
  the view's stylesheet, then the node's own inline `style:`;
- **within a layer:** a rule with no selector (the baseline), then rules
  whose `kind:` matches, then rules whose `classes:` are all on the node
  (fewer classes before more), then a rule whose `id:` matches. Rules of
  one tier apply in the order written.

Styles merge field by field: a later value replaces an earlier one, and a
field a rule doesn't mention is left alone.

Rules are indexed by kind and id when a sheet is prepared, so resolving
a node doesn't scan every rule (M34's spike: the scan was half the build).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Optional

__all__ = ["STYLE_FIELDS", "Sheet", "check_stylesheet", "check_theme", "component_key", "resolve_style"]

_THEME_FIELDS = ("seed", "dark", "colors", "styles", "components", "typography")


def _check_fields(spec: Any, allowed: tuple[str, ...]) -> None:
    if spec is None:
        return
    if not isinstance(spec, dict):
        raise ValueError(f"must be a mapping, got {type(spec).__name__}")
    for key in spec:
        if key not in allowed:
            expected = ", ".join(f"`{name}`" for name in allowed)
            raise ValueError(f"unknown field `{key}`, expected one of {expected}")  # tre's wording
    Sheet.of(spec)


def check_theme(spec: Any) -> None:
    """Raises `ValueError` if `spec` isn't a valid theme dict."""
    _check_fields(spec, _THEME_FIELDS)


def check_stylesheet(spec: Any) -> None:
    """Raises `ValueError` if `spec` isn't a valid stylesheet dict."""
    _check_fields(spec, ("styles",))

#: Every field a `style:` can hold, as in `tre`'s `StyleSpec`.
STYLE_FIELDS = frozenset({
    "width", "height", "flex_direction", "padding", "margin", "gap", "flex_grow", "flex_shrink",
    "flex_basis", "align_items", "justify_content", "background", "foreground", "corner_radius",
    "opacity", "border_width", "border_color", "elevation",
    # M71: the rest of `tre`'s flexbox
    "flex_wrap", "align_self", "min_width", "max_width", "min_height", "max_height", "aspect_ratio",
    "position", "x", "y", "z_index", "clip_children",
})


@dataclass
class Sheet:
    """A prepared stylesheet or theme `styles:` list."""

    baseline: list[dict[str, Any]] = field(default_factory=list)
    by_kind: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    #: `(classes, style)`, stably sorted by how many classes.
    by_classes: list[tuple[frozenset[str], dict[str, Any]]] = field(default_factory=list)
    by_id: dict[str, list[dict[str, Any]]] = field(default_factory=dict)

    @classmethod
    def of(cls, spec: Optional[dict[str, Any]]) -> Optional["Sheet"]:
        """Prepares `{styles: [...]}` (a stylesheet or a theme), or returns
        `None` for `None`."""
        if spec is None:
            return None
        if not isinstance(spec, dict):
            raise ValueError(f"a stylesheet or theme must be a mapping, got {type(spec).__name__}")
        rules = spec.get("styles") or []
        if not isinstance(rules, list):
            raise ValueError(f"styles: must be a list of rules, got {type(rules).__name__} {rules!r}")
        sheet = cls()
        for index, rule in enumerate(rules):
            if not isinstance(rule, dict):
                raise ValueError(f"styles[{index}]: a rule must be a mapping, got {type(rule).__name__}")
            unknown = set(rule) - {"kind", "classes", "id", "style"}
            if unknown:
                raise ValueError(f"styles[{index}]: unknown field(s) {sorted(unknown)} (a rule has kind, classes, id, style)")
            style = rule.get("style") or {}
            if not isinstance(style, dict):
                raise ValueError(f"styles[{index}].style: must be a mapping, got {type(style).__name__}")
            bad = set(style) - STYLE_FIELDS
            if bad:
                raise ValueError(f"styles[{index}].style: unknown field(s) {sorted(bad)}")
            kind, classes, node_id = rule.get("kind"), rule.get("classes") or [], rule.get("id")
            if kind is None and not classes and node_id is None:
                sheet.baseline.append(style)
            if kind is not None:
                sheet.by_kind.setdefault(kind, []).append(style)
            if classes:
                sheet.by_classes.append((frozenset(classes), style))
            if node_id is not None:
                sheet.by_id.setdefault(node_id, []).append(style)
        sheet.by_classes.sort(key=lambda item: len(item[0]))
        return sheet

    def resolve(self, node: dict[str, Any], into: dict[str, Any]) -> None:
        """Merges this sheet's rules for `node` into `into`, in `tre`'s
        tier order."""
        for style in self.baseline:
            into.update(style)
        for style in self.by_kind.get(node.get("kind"), ()):
            into.update(style)
        if self.by_classes:
            classes = set(node.get("classes") or ())
            for wanted, style in self.by_classes:
                if wanted <= classes:
                    into.update(style)
        for style in self.by_id.get(node.get("id"), ()):
            into.update(style)


def resolve_style(node: dict[str, Any], layers: Iterable[Optional[Sheet]]) -> dict[str, Any]:
    """`node`'s resolved style: each layer in turn (default theme, custom
    theme, stylesheet; `None`s skipped), then its inline `style:`. A
    fragment's root (`component_of`, M57) then takes its corner radius and
    elevation from the themes' `components:`, where they say."""
    resolved: dict[str, Any] = {}
    for sheet in layers:
        if sheet is not None:
            sheet.resolve(node, resolved)
    resolved.update(node.get("style") or {})
    fragment = node.get("component_of")
    components = getattr(layers, "components", None)
    if fragment and components:
        component, variant = component_key(fragment)
        for name in ("corner_radius", "elevation"):
            value = _component_value(components, component, variant, name)
            if value is not None:
                resolved[name] = value
    return resolved


#: Fragment families whose `components:` variant is the rest of the name
#: (`CardElevated` -> `card.elevated`), longest prefix first (M57).
_VARIANT_FAMILIES = (("IconButton", "icon_button"), ("SplitButton", "split_button"), ("Button", "button"),
                     ("Card", "card"), ("Chip", "chip"), ("Badge", "badge"), ("SideSheet", "side_sheet"),
                     ("Toolbar", "toolbar"))
#: Fragments whose key isn't their name's: a selected filter chip is a
#: filter chip, and a standard side sheet is the plain entry. (A FAB's
#: variant is its size: its fragments name `fab.{{ fab_size }}` themselves.)
_EXACT_KEYS: dict[str, tuple[str, Optional[str]]] = {
    "ButtonGroup": ("button_group", None), "ChipFilterSelected": ("chip", "filter"),
    "SideSheetStandard": ("side_sheet", None),
    **{f"ExtendedFab{c}": ("extended_fab", None) for c in ("Primary", "Secondary", "Tertiary", "Surface")},
    **{f"PeriodSelector{p}": ("period_selector", None) for p in ("AM", "PM")},
    **{f"DatePickerDay{s}": ("date_picker_day", None) for s in ("", "Selected", "Today", "OutsideMonth")},
    **{f"TreeNode{s}": ("tree_node", None) for s in ("Branch", "Leaf")},
}


def _snake(name: str) -> str:
    out = []
    for i, ch in enumerate(name):
        if ch.isupper() and i and (not name[i - 1].isupper() or (i + 1 < len(name) and name[i + 1].islower())):
            out.append("_")
        out.append(ch.lower())
    return "".join(out)


def component_key(fragment: str) -> tuple[str, Optional[str]]:
    """The `components:` entry a fragment's root reads (M57): its
    component and variant, as a theme names them (`FabPrimary` ->
    `fab.default`, `CardElevated` -> `card.elevated`, `Dialog` ->
    `dialog`)."""
    if "." in fragment:  # a key the fragment named itself (`fab.small`)
        component, variant = fragment.split(".", 1)
        return component, variant
    if fragment in _EXACT_KEYS:
        return _EXACT_KEYS[fragment]
    for prefix, component in _VARIANT_FAMILIES:
        if fragment.startswith(prefix) and len(fragment) > len(prefix):
            return component, _snake(fragment[len(prefix):])
    return _snake(fragment), None


def _component_value(components: dict[str, Any], component: str, variant: Optional[str], name: str) -> Any:
    """`Theme._lookup`'s rule: the variant's entry, then the component's."""
    if variant is not None:
        value = getattr(components.get(f"{component}.{variant}"), name, None)
        if value is not None:
            return value
    return getattr(components.get(component), name, None)
