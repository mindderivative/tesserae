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

_TEXT_KEYS = ("typography_role", "font_family", "font_size", "font_weight", "wrap", "overflow", "text_align")
_FIELD_KEYS = ("typography_role", "font_family", "font_size", "font_weight", "placeholder", "multiline", "obscured")
#: The widget names that are not the builder's kind names.
_KIND = {"TextInput": "TextField"}
#: Properties the renderer acts on (it has no builder equivalent), so they are not part of the lowered spec.
_RENDERER_ONLY = {"TextInput": {"max_length", "read_only"}}
#: Properties the renderer does not draw yet: said by name, never dropped silently.
_PLACEHOLDER = "composed"
_NOT_RENDERED = {"frame": "a video frame", "scroll_offset": "a scroll position"}


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
        folded = {"text", *_TEXT_KEYS}
        node["text"] = {"content": values.get("text", ""), **{k: values[k] for k in _TEXT_KEYS if k in values}}
    elif widget == "TextInput":
        folded = {"text", *_FIELD_KEYS, *_RENDERER_ONLY["TextInput"]}
        node["text"] = {"content": values.get("text", ""), **{k: values[k] for k in _FIELD_KEYS if k in values}}
    elif widget == "Icon":
        folded = {"icon"}
        node["icon"] = {"name": values.get("icon")}
    elif widget == "Image":
        folded = {"src", "fit"}
        node["image"] = {k: values[k] for k in ("src", "fit") if k in values}
    elif widget == "Svg":
        folded = {"src", "content"}
        node["svg"] = {k: values[k] for k in ("src", "content") if k in values}
    node.update({k: v for k, v in values.items() if k not in folded})  # the rest stay flat: `disabled`, `checked`, `value`, ...
    style = inst.effective_style()
    if style:
        node["style"] = style
    if inst.classes:
        node["classes"] = list(inst.classes)
    if inst.a11y:
        node["a11y"] = {name: (held.get() if hasattr(held, "get") else held) for name, held in inst.a11y.items()}
    if inst.interaction is not None:
        node["interaction"] = {"color": inst.interaction} if isinstance(inst.interaction, str) else inst.interaction
    if inst.handlers:
        # The builder reads a node's handlers to make it clickable (role, cursor, state layer); the renderer wires the real ones from the
        # instance, so the spec carries a name the 0.4.x wiring does not act on.
        node["handlers"] = {event: _PLACEHOLDER for event in inst.handlers}
    if inst.window_region is not None:
        node["window_region"] = inst.window_region
    if inst.children:
        node["children"] = [lower(child) for child in inst.children]
    return node
