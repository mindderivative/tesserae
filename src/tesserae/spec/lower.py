"""Instances down to the builder's spec (phase 5 of #209).

`lower(instance)` writes the tree of a composition as the node mappings `tesserae.spec.build` has always built from (`id`, `kind`, `style`,
`text: {content, ...}`, `icon: {name}`, `image: {src, fit}`, ...), using each property's *current* value. The renderer (`tesserae.composed`)
lowers again whenever something the tree reads changes and lets `View.reconcile` bring the live nodes in line, so the builder, the cascade and
the controls are the code that has been tested for years; only what feeds them is new.

Handlers, bindings and two-way edits are not part of the lowered spec: the renderer wires those from the instances.
"""

from __future__ import annotations

from typing import Any

from tesserae.spec.compose import Instance

__all__ = ["lower"]

_TEXT_KEYS = ("typography_role", "font_family", "font_size", "font_weight", "wrap", "overflow", "text_align", "max_lines", "letter_spacing", "selectable")
_FIELD_KEYS = ("typography_role", "font_family", "font_size", "font_weight", "placeholder", "multiline", "obscured")
#: The widget names that are not the builder's kind names.
_KIND = {"TextInput": "TextField", "VirtualList": "ScrollView"}
#: Properties the renderer acts on (it has no builder equivalent), so they are not part of the lowered spec.
_RENDERER_ONLY = {"TextInput": {"max_length", "read_only", "mask"}}
#: Properties the renderer does not draw yet: said by name, never dropped silently.
_PLACEHOLDER = "composed"
_NOT_RENDERED = {"frame": "a video frame"}


def lower(inst: Instance) -> dict[str, Any]:
    """The 0.4.x node mapping for `inst` and everything under it, at the values the instances hold now."""
    node: dict[str, Any] = {"id": inst.id, "kind": _KIND.get(inst.widget, inst.widget)}
    values = {name: inst.value(name) for name in inst.props}
    for name, what in _NOT_RENDERED.items():
        if name in values:
            raise ValueError(f"{inst.id}: {inst.widget}.{name} ({what}) is not drawn by the renderer yet")
    widget = inst.widget
    folded: set[str] = set()  # the properties a nested mapping took
    if widget in ("Text", "Link"):
        folded = {"text", "heading", *_TEXT_KEYS}
        node["text"] = {"content": values.get("text", ""), **{k: values[k] for k in _TEXT_KEYS if k in values}}
        if widget == "Link":
            folded |= {"href", "visited", "underline"}  # the renderer opens the href and underlines; the builder draws plain text
            if not {"typography_role", "font_family", "font_size"} & set(node["text"]):
                node["text"]["typography_role"] = "body_medium"
    elif widget == "TextInput":
        folded = {"text", *_FIELD_KEYS, *_RENDERER_ONLY["TextInput"]}
        node["text"] = {"content": values.get("text", ""), **{k: values[k] for k in _FIELD_KEYS if k in values}}
    elif widget == "Icon":
        folded = {"icon", "path", "view_box"}
        node["icon"] = {name: values[key] for name, key in (("name", "icon"), ("path", "path"), ("view_box", "view_box")) if values.get(key) is not None}
    elif widget == "Image":
        folded = {"src", "fit", "alt"}
        node["image"] = {k: values[k] for k in ("src", "fit") if k in values}
    elif widget == "Svg":
        folded = {"src", "content", "alt"}
        node["svg"] = {k: values[k] for k in ("src", "content") if k in values}
    elif widget in ("ScrollView", "VirtualList"):
        folded = {"scroll_offset", "at_top", "at_end", "scroll_direction", "item_height", "overscan"}  # the outputs are the renderer's to write
        if inst.virtual is not None:  # the whole list's height is its length; the rows built are placed in it
            node["virtual"] = {"count": inst.virtual.count, "extent": float(inst.virtual.extent())}
        if "scroll_offset" in values:
            node["scroll"] = {"offset": values["scroll_offset"]}
    elif widget == "Splitter":
        folded = {"orientation", "position", "min_first", "min_second", "collapsible", "label"}
        node["kind"] = "Container"
    elif widget == "Overlay":
        folded = {"open", "anchor", "placement", "modal", "dismissible"}  # the renderer shows the layer; the builder needs only to know it is modal
        node["overlay"] = {"modal": bool(values.get("modal"))}
    elif widget == "Canvas":
        folded = {"draw"}
        node["canvas"] = {"draw": values.get("draw")}
    node.update({k: v for k, v in values.items() if k not in folded})  # the rest stay flat: `disabled`, `checked`, `value`, ...
    style = inst.effective_style()
    if inst.virtual_index is not None and inst.parent is not None and inst.parent.virtual is not None:  # a row of a VirtualList sits at its place in it
        extent = float(inst.parent.virtual.extent())
        style = {"position": "absolute", "x": 0, "y": inst.virtual_index.get() * extent, "height": extent, "width": "100%", **style}
    if style:
        node["style"] = style
    if inst.classes:
        node["classes"] = list(inst.classes)
    a11y: dict[str, Any] = {}
    if widget == "Text" and values.get("heading"):
        a11y = {"role": "heading", "level": values["heading"]}
    if widget in ("Image", "Svg"):  # described by `alt`, else decorative -- unless it is pressed, when hiding it would hide a control
        a11y = {"role": "img", "label": values["alt"]} if values.get("alt") else {} if inst.handlers else {"hidden": True}
    if inst.a11y:  # what the node says itself beats what `alt` makes of it
        a11y.update({name: (held.get() if hasattr(held, "get") else held) for name, held in inst.a11y.items()})
        for relation in ("describedby", "controls"):  # names of nodes in this view, as the ids the builder knows them by
            if relation in a11y:
                a11y[relation] = _node_ids(inst, relation, a11y[relation])
    if a11y:
        node["a11y"] = a11y
    if inst.interaction is not None:
        node["interaction"] = {"color": inst.interaction} if isinstance(inst.interaction, str) else inst.interaction
    if inst.handlers:
        # The builder reads a node's handlers to make it clickable (role, cursor, state layer); the renderer wires the real ones from the
        # instance, so the spec carries a name the 0.4.x wiring does not act on.
        node["handlers"] = {event: _PLACEHOLDER for event in inst.handlers}
    if inst.window_region is not None:
        node["window_region"] = inst.window_region
    if widget == "Splitter":
        _split(inst, node, values)
    elif inst.children:
        node["children"] = [lower(child) for child in inst.children]
    return node


#: The handle between a Splitter's panes: its width along the split, and the grip drawn in it (MD3's 4 x 48 drag handle).
SPLIT_HANDLE = 16.0
SPLIT_GRIP = (4.0, 48.0)


def _node_ids(inst: Instance, field: str, names: Any) -> list[str]:
    """The ids of the nodes of `inst`'s view called `names` (one name or a list)."""
    wanted = [names] if isinstance(names, str) else list(names)
    root = inst.view_root
    if root is None:  # the view that is open itself has no owner: its root is the top of the tree
        root = inst
        while root.parent is not None:
            root = root.parent
    found = {other.name: other.id for other in root.walk() if other.name} if root is not None else {}
    missing = [n for n in wanted if n not in found]
    if missing:
        raise ValueError(f"{inst.id}: a11y {field} names {missing[0]!r}, which is no node by that name in this view")
    return [found[n] for n in wanted]


def _split(inst: Instance, node: dict[str, Any], values: dict[str, Any]) -> None:
    """A Splitter is a row (or column) of the first pane, the handle and the second pane; the renderer wires the handle."""
    horizontal = values.get("orientation", "horizontal") == "horizontal"
    share = min(max(float(values.get("position", 0.5)), 0.0), 1.0)
    main, least = ("width", "min_width") if horizontal else ("height", "min_height")
    tracks = f"{share:g}fr {SPLIT_HANDLE:g} {1.0 - share:g}fr"  # the panes share what the handle leaves, in proportion
    node["style"] = {**node.get("style", {}), "display": "grid", "grid_template_columns" if horizontal else "grid_template_rows": tracks}
    mins = (float(values.get("min_first", 0.0)), float(values.get("min_second", 0.0)))

    def pane(part: str, child: Instance, minimum: float) -> dict[str, Any]:
        return {"id": f"{inst.id}.{part}", "kind": "Container", "children": [lower(child)],
                "style": {"clip_children": True, least: minimum}}

    grip = SPLIT_GRIP if horizontal else SPLIT_GRIP[::-1]
    handle = {"id": f"{inst.id}.handle", "kind": "Container",
              "style": {main: SPLIT_HANDLE, "background": "transparent", "align_content": "center",
                        "cursor": "col_resize" if horizontal else "row_resize"},
              "handlers": {"on_click": _PLACEHOLDER},  # what makes the builder give it a Tab stop; the renderer wires its real events
              "a11y": {"role": "slider", "label": values.get("label", "Resize panes"), "value": share, "value_min": 0.0, "value_max": 1.0, "value_step": 0.05},
              "children": [{"id": f"{inst.id}.handle.grip", "kind": "Rect",
                            "style": {"width": grip[0], "height": grip[1], "corner_radius": 2, "background": "outline"}}]}
    node["children"] = [pane("first", inst.children[0], mins[0]), handle, pane("second", inst.children[1], mins[1])]
