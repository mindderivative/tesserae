"""`kind: Dock` and `kind: DockPanel` (0.4.4): panels docked around the content, in a view.

    - id: dock
      kind: Dock
      children:
        - id: files
          kind: DockPanel
          title: Files                      # the panel's tab, when its zone has several
          style: {zone: left, width: 220}   # where it docks; a left or right zone's width, a top or bottom one's height
          children: [...]                   # anything: a Tabs, a list, a form
        - id: editor
          kind: DockPanel
          title: Editor
          style: {zone: center}
          children: [...]

A `Dock` holds the zones (left, right, top, bottom and center); a `DockPanel` says which zone it is in with `zone:`, a style
field that is an error anywhere else. Panels in one zone are its tabs, which the user can drag between zones; one alone has no
tab strip. A `DockPanel` inside a `DockPanel` is a split of it, side by side (the parent's `flex_direction: horizontal`, the
default) or top and bottom (`vertical`), with a handle between them to resize; the halves hold what a panel holds, and can be
split again. A panel has either splits or content, not both.

Before the view is built, each `Dock` becomes a plain `Container` carrying `dock:` (its panels), each panel one carrying
`dock_panel:`, and a handle node (`split_handle:`) goes between split panels; `tesserae.dockhost.DockHost` makes them a dock
once they are built.
"""

from __future__ import annotations

import copy
from typing import Any

__all__ = ["DOCK_SIDES", "DockError", "expand_docks"]

DOCK_SIDES = ("left", "right", "top", "bottom", "center")
_DOCK_KEYS = frozenset({"id", "kind", "style", "classes", "a11y", "children"})
_PANEL_KEYS = frozenset({"id", "kind", "title", "style", "classes", "a11y", "children"})
#: How wide a split's handle is across the split.
SPLIT_SPAN = 16


class DockError(ValueError):
    """A `Dock` or `DockPanel` written wrongly, said on one line naming its id."""


def expand_docks(spec: Any) -> Any:
    """`spec` with each `Dock`, its `DockPanel`s and their splits turned into containers (a copy; `spec` itself is left as
    it is). A `zone:` anywhere but on a `DockPanel` of a `Dock`, a `DockPanel` outside a `Dock`, and a second `Dock` are errors."""
    if not isinstance(spec, dict):
        return spec
    spec = copy.deepcopy(spec)
    docks: list[str] = []
    out = _walk(spec, docks, in_dock=False)
    if len(docks) > 1:
        raise DockError(f"widget {docks[1]!r}: a window has one Dock (and {docks[0]!r} is it)")
    return out


def _walk(node: dict[str, Any], docks: list[str], *, in_dock: bool) -> dict[str, Any]:
    kind = node.get("kind")
    if kind == "Dock":
        docks.append(str(node.get("id")))
        return _dock(node, docks)
    if kind == "DockPanel":
        raise DockError(f"widget {node.get('id')!r}: a DockPanel is in a Dock (or in another DockPanel, as a split)")
    style = node.get("style")
    if isinstance(style, dict) and "zone" in style:
        raise DockError(f"widget {node.get('id')!r}: style.zone is for a DockPanel in a Dock, not a {kind}")
    if isinstance(node.get("children"), list):
        node["children"] = [_walk(c, docks, in_dock=in_dock) if isinstance(c, dict) else c for c in node["children"]]
    return node


def _check(node: dict[str, Any], allowed: frozenset[str], what: str) -> None:
    node_id = node.get("id")
    if not isinstance(node_id, str):
        raise DockError(f"a `{what}` needs an `id:`")
    unknown = sorted(set(node) - allowed)
    if unknown:
        raise DockError(f"widget {node_id!r}: a {what} takes {', '.join(sorted(allowed - {'id', 'kind'}))}; not {', '.join(unknown)}")
    if not isinstance(node.get("style") or {}, dict):
        raise DockError(f"widget {node_id!r}: a {what}'s style is a mapping of style fields, got {node.get('style')!r}")


def _dock(node: dict[str, Any], docks: list[str]) -> dict[str, Any]:
    _check(node, _DOCK_KEYS, "Dock")
    node_id = node["id"]
    panels: list[dict[str, Any]] = []
    children: list[dict[str, Any]] = []
    sizes: dict[str, float] = {}
    for child in node.get("children") or []:
        if not isinstance(child, dict) or child.get("kind") != "DockPanel":
            raise DockError(f"widget {node_id!r}: a Dock holds DockPanels, got {child.get('kind') if isinstance(child, dict) else child!r}")
        _check(child, _PANEL_KEYS, "DockPanel")
        style = dict(child.get("style") or {})
        zone = style.pop("zone", None)
        if zone not in DOCK_SIDES:
            raise DockError(f"widget {child['id']!r}: a DockPanel in a Dock says which zone it is in: `style: {{zone: ...}}`, "
                            f"one of {', '.join(DOCK_SIDES)}; got {zone!r}")
        across = "width" if zone in ("left", "right") else "height"
        size = style.pop(across, None)
        style.pop("height" if across == "width" else "width", None)  # the zone fills the other way
        if size is not None and (isinstance(size, bool) or not isinstance(size, (int, float)) or size <= 0):
            raise DockError(f"widget {child['id']!r}: a {zone} zone's {across} is a number of pixels, got {size!r}")
        if size is not None:
            sizes.setdefault(zone, float(size))
        title = child.get("title", child["id"])
        if not isinstance(title, str):
            raise DockError(f"widget {child['id']!r}: a DockPanel's title is text, got {title!r}")
        panel = _panel(child, style, docks)
        panel["dock_panel"] = {"title": title, "zone": zone}
        panels.append({"id": child["id"], "title": title, "zone": zone})
        children.append(panel)
    style = {"flex": "fill", **(node.get("style") or {})}
    out: dict[str, Any] = {"id": node_id, "kind": "Container", "classes": ["dock", *(node.get("classes") or [])],
                           "style": style, "dock": {"panels": panels, "sizes": sizes}, "children": children}
    if "a11y" in node:
        out["a11y"] = node["a11y"]
    return out


def _panel(node: dict[str, Any], style: dict[str, Any], docks: list[str], *, split: bool = False) -> dict[str, Any]:
    """A panel as a container; its `DockPanel` children (a split) with a handle between each pair."""
    node_id = node["id"]
    kids = node.get("children") or []
    nested = [c for c in kids if isinstance(c, dict) and c.get("kind") == "DockPanel"]
    if nested and len(nested) != len(kids):
        raise DockError(f"widget {node_id!r}: a DockPanel has splits (DockPanels) or content, not both")
    children: list[dict[str, Any]] = []
    if nested:
        horizontal = style.get("flex_direction", "horizontal") != "vertical"
        previous = None
        for child in nested:
            _check(child, _PANEL_KEYS, "DockPanel")
            child_style = dict(child.get("style") or {})
            if "zone" in child_style:
                raise DockError(f"widget {child['id']!r}: a DockPanel inside a DockPanel is a split of it and has no zone")
            if previous is not None:
                children.append({"id": f"{node_id}.split.{len(children) // 2}", "kind": "Container", "classes": ["dock_split"],
                                 "split_handle": {"axis": "x" if horizontal else "y", "before": previous["id"], "after": child["id"]},
                                 "style": {"width" if horizontal else "height": SPLIT_SPAN, "flex": "none"}})
            sized = "width" if horizontal else "height"
            # a half with a size of its own keeps it (the others take what is left); one without shares the room
            half = _panel(child, {"flex": "none" if sized in child_style else "fill", **child_style}, docks, split=True)
            half["dock_panel"] = {"title": child.get("title", child["id"]), "split": True}
            children.append(half)
            previous = child
    else:
        children = [_walk(c, docks, in_dock=True) if isinstance(c, dict) else c for c in kids]
    fills = {} if split else {"width": "100%", "height": "100%"}  # a split's size is its share of its parent's
    out = {"id": node_id, "kind": "Container", "classes": ["dock_panel", *(node.get("classes") or [])],
           "style": {**fills, "clip_children": True, **style}, "children": children}
    if "a11y" in node:
        out["a11y"] = node["a11y"]
    return out
