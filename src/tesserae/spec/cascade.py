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

__all__ = ["STYLE_FIELDS", "Sheet", "resolve_style"]

#: Every field a `style:` can hold, as in `tre`'s `StyleSpec`.
STYLE_FIELDS = frozenset({
    "width", "height", "flex_direction", "padding", "margin", "gap", "flex_grow", "flex_shrink",
    "flex_basis", "align_items", "justify_content", "background", "foreground", "corner_radius",
    "opacity", "border_width", "border_color", "elevation",
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
        sheet = cls()
        for rule in spec.get("styles") or []:
            style = rule.get("style") or {}
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
    theme, stylesheet; `None`s skipped), then its inline `style:`."""
    resolved: dict[str, Any] = {}
    for sheet in layers:
        if sheet is not None:
            sheet.resolve(node, resolved)
    resolved.update(node.get("style") or {})
    return resolved
