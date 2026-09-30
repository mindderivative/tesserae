"""Tesserae's spec compiler (M37 Phase 2): builds an expanded view spec
(a `WidgetSpec`-shaped dict, from `tesserae.spec.expand`) into `tre`
0.3.4 nodes with `window.create`/`set`/`add_child`, the job `tre`'s
`engine-spec/src/build.rs` does today and 0.3.5 removes.

Each kind maps onto `tre`'s building blocks:

| `kind:` | nodes |
|---|---|
| `Rect`, `Container` | a `box` (a Rect needs `background`; a Container's is optional) |
| `Text` | a `text` (needs `foreground`) |
| `Link` | a `text` with `role="link"` and a pointer cursor (needs `foreground`) |
| `TextField` | a `box` (its `background`) holding a `text_input` |
| `Image` | an `image`, from pixels Tesserae decoded |
| `Icon` | a `path` from `tesserae.icons` (needs `foreground`) |
| `Checkbox`, `RadioButton`, `Switch`, `Slider`, `CircularProgress`, `LinearProgress`, `LoadingIndicator`, `TimePickerDial` | Tesserae's own MD3 controls (`tesserae.controls`, M40), whose `.node` goes in the tree; `Built.controls` keeps them |

Styles resolve through `tesserae.spec.cascade`; theme roles, shape
tokens, elevation levels and type roles through `tesserae.tokens`. Errors
use `tre`'s wording. Bindings, handlers and `two_way:` aren't wired here
(M37 Phase 4).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from tesserae import a11y, tokens
from tesserae.icons import ICON_VIEW_BOX, icon_path
from tesserae.spec.cascade import STYLE_FIELDS, Sheet, resolve_style

__all__ = [
    "A11Y_BINDABLE", "Built", "Layers", "SpecBuildError", "a11y_bindings", "build", "control_shape", "focus_ring_color",
    "interaction_tint", "is_binding", "natural_size", "patch",
    "prepare_layers",
    "shipped_default_theme",
]

RGBA = tuple[int, int, int, int]
_TRANSPARENT: RGBA = (0, 0, 0, 0)
#: The fixed colour `tre`'s TextField draws its text in (`engine-core`).
_TEXT_FIELD_GLYPH: RGBA = (0x1C, 0x1B, 0x1F, 0xFF)
#: MD3's baseline colours, for nodes with no theme.
_BASELINE = tokens.BASELINE
_CONTROL_KINDS = frozenset({
    "Checkbox", "RadioButton", "Switch", "Slider", "SpinBox", "CircularProgress", "LinearProgress",
    "LoadingIndicator", "TimePickerDial",
})
#: Kinds built with a `tesserae.widgets` widget (M60): a node graph and its nodes.
_WIDGET_KINDS = frozenset({"NodeGraph", "GraphNode"})
_KINDS = _CONTROL_KINDS | _WIDGET_KINDS | {"Rect", "Container", "Text", "Link", "TextField", "Image", "Icon",
                                           "ScrollView"}
_NODE_KEYS = frozenset({
    "id", "kind", "classes", "style", "text", "checked", "selected", "value", "hour", "minute",
    "image", "icon", "bindings", "handlers", "two_way", "interaction", "a11y", "group", "children",
    "component_of",  # the fragment a node is the root of (M57): its theme `components:` entry
    "min", "max", "step",  # a SpinBox's (M58)
    "disabled",  # any node's (M70): the View applies it, or a control's own

    "label", "x", "y", "edges",  # a GraphNode's title and place, a NodeGraph's edges (M60)
})


class SpecBuildError(ValueError):
    """A spec the compiler can't build. The message is `tre`'s."""


@dataclass
class Built:
    """A built tree. `nodes[id]` is the node a widget's `id` names (for a
    TextField, its `text_input`); `outer[id]` is the node that sits in the
    tree and carries its layout (for a TextField, the `box`)."""

    root: Any
    nodes: dict[str, Any] = field(default_factory=dict)
    outer: dict[str, Any] = field(default_factory=dict)
    specs: dict[str, dict[str, Any]] = field(default_factory=dict)
    #: The control (`tesserae.controls`) behind each control kind's id.
    controls: dict[str, Any] = field(default_factory=dict)
    #: RadioButtons' `group:` names, each one `tesserae.controls.RadioGroup`.
    radio_groups: dict[str, Any] = field(default_factory=dict)
    #: The M71 layout keys each node's style gave, for `patch`'s `before`.
    layout_keys: dict[str, frozenset[str]] = field(default_factory=dict)


@dataclass
class _Context:
    window: Any
    layers: tuple[Optional[Sheet], ...]
    scheme: Optional[dict[str, RGBA]]
    frames: dict[str, tuple[bytes, int, int]]
    #: The shared listener registrar controls use (a View's; otherwise their own).
    listen: Optional[Callable[..., Any]] = None
    #: The NodeGraph widget whose GraphNodes are being built (M60).
    graph: Any = None


def build(
    window: Any,
    spec: dict[str, Any],
    *,
    scheme: Optional[dict[str, RGBA]] = None,
    default_theme: Optional[dict[str, Any]] = None,
    custom_theme: Optional[dict[str, Any]] = None,
    stylesheet: Optional[dict[str, Any]] = None,
    frames: Optional[dict[str, tuple[bytes, int, int]]] = None,
) -> Built:
    """Builds `spec` into detached nodes of `window`. `scheme` is the
    resolved colour scheme (`tokens.resolve_scheme`), or `None` for no
    theme. `default_theme` defaults to `tre`'s shipped one. `frames` maps
    an Image's id to its decoded `(rgba, width, height)`."""
    if default_theme is None:
        default_theme = shipped_default_theme()
    ctx = _Context(window, prepare_layers(default_theme, custom_theme, stylesheet), scheme, frames or {})
    built = Built(root=None)
    built.root = _build(ctx, spec, built)
    return built


class Layers(tuple):
    """The cascade's three prepared layers (default theme, custom theme,
    stylesheet), plus the two themes' `typography:` overrides (M38),
    which display text resolves its `typography_role` through."""

    typography: dict[str, dict[str, Any]]
    #: The two themes' `components:` (M57), a custom theme's entry
    #: replacing the default's: shape and elevation for fragment roots.
    components: dict[str, Any]


def prepare_layers(
    default_theme: Optional[dict[str, Any]],
    custom_theme: Optional[dict[str, Any]],
    stylesheet: Optional[dict[str, Any]],
) -> Layers:
    """The cascade's three layers, prepared once (`default_theme` defaults
    to `tre`'s shipped one), with the themes' typography overrides: a
    custom theme's role entry replaces the default theme's."""
    from tesserae.theme import _component, _type_override

    if default_theme is None:
        default_theme = shipped_default_theme()
    layers = Layers((Sheet.of(default_theme), Sheet.of(custom_theme), Sheet.of(stylesheet)))
    layers.typography = {}
    layers.components = {}
    for theme in (default_theme, custom_theme):
        for role, raw in ((theme or {}).get("typography") or {}).items():
            layers.typography[role] = _type_override(role, raw)
        for key, raw in ((theme or {}).get("components") or {}).items():
            layers.components[key] = _component(key, raw)
    return layers


def build_with(
    window: Any,
    spec: dict[str, Any],
    *,
    scheme: Optional[dict[str, RGBA]],
    layers: tuple[Optional[Sheet], ...],
    frames: Optional[dict[str, tuple[bytes, int, int]]] = None,
    into: Optional[Built] = None,
    listen: Optional[Callable[..., Any]] = None,
    graph: Any = None,
) -> Any:
    """Builds `spec` with already-prepared layers, recording its nodes in
    `into` (a new `Built` if none); returns the subtree's outer root.
    `listen` is the listener registrar the controls share with the view;
    `graph`, the NodeGraph widget a GraphNode `spec` belongs to (M60)."""
    ctx = _Context(window, layers, scheme, frames or {}, listen, graph)
    built = into if into is not None else Built(root=None)
    return _build(ctx, spec, built)


_shipped: Optional[dict[str, Any]] = None


def shipped_default_theme() -> dict[str, Any]:
    """`tre`'s shipped default theme (Tesserae's copy)."""
    global _shipped
    if _shipped is None:
        from pathlib import Path

        import yaml

        _shipped = yaml.safe_load((Path(__file__).parent / "default_theme.yaml").read_text(encoding="utf-8"))
    return _shipped


def _build(ctx: _Context, node: dict[str, Any], built: Built) -> Any:
    node_id, kind = node.get("id"), node.get("kind")
    if not isinstance(node_id, str):
        raise SpecBuildError(f"every widget needs an `id:`, got {node!r}")
    if kind not in _KINDS:
        raise SpecBuildError(f"widget {_q(node_id)}: unknown kind {kind!r}")
    unknown = set(node) - _NODE_KEYS
    if unknown:
        raise SpecBuildError(f"widget {_q(node_id)}: unknown field(s) {sorted(unknown)}")
    style = resolve_style(node, ctx.layers)
    _check_interaction(node)
    _a11y_fields(node)
    unknown_style = set(style) - STYLE_FIELDS
    if unknown_style:
        raise SpecBuildError(f"widget {_q(node_id)}: unknown style field(s) {sorted(unknown_style)}")

    try:
        outer, inner = _create(ctx, node, style, built)
    except ValueError as exc:
        if isinstance(exc, SpecBuildError):
            raise
        raise SpecBuildError(f"widget {_q(node_id)}: {exc}") from None  # `tre`'s message, naming the widget (M71)
    built.layout_keys[node_id] = layout_keys(style)
    built.nodes[node_id] = inner
    built.outer[node_id] = outer
    built.specs[node_id] = node
    if kind == "NodeGraph":  # its GraphNodes place themselves in the graph's content (M60)
        graph, ctx.graph = ctx.graph, built.controls[node_id]
        try:
            for child in node.get("children") or []:
                if child.get("kind") != "GraphNode":
                    raise SpecBuildError(f"widget {_q(node_id)}: a NodeGraph's children are GraphNodes, "
                                         f"got {child.get('kind')!r} ({child.get('id')!r})")
                _build(ctx, child, built)
        finally:
            ctx.graph = graph
        connect_edges(built.controls[node_id], node, built)
        return outer
    # a GraphNode's content goes in its body, a ScrollView's in its content box (M71)
    parent = inner if kind in ("GraphNode", "ScrollView") else outer
    for child in node.get("children") or []:
        parent.add_child(_build(ctx, child, built))
    return outer


def _q(node_id: str) -> str:
    return f'"{node_id}"'


# -- shared style mapping ---------------------------------------------------------------


def _spacing(value: Any, prefix: str) -> dict[str, float]:
    if value is None:
        return {f"{prefix}_{side}": 0.0 for side in ("top", "right", "bottom", "left")}
    if isinstance(value, (int, float)):
        return {f"{prefix}_{side}": float(value) for side in ("top", "right", "bottom", "left")}
    return {f"{prefix}_{side}": float(value.get(side, 0.0)) for side in ("top", "right", "bottom", "left")}


#: M71's layout keys, each with the default `tre` takes back. A style sets
#: one only when it gives it, and a patch resets one only when the style
#: gave it before (`patch`'s `before`): Python code also places and clips
#: nodes a spec built (a widget's `x`/`y`, an overlay's `position`, a
#: viewport's `clip_children`), and a re-theme mustn't undo that.
_OPTIONAL_LAYOUT: dict[str, Any] = {
    "flex_wrap": "no_wrap", "align_self": None, "min_width": "auto", "max_width": "auto", "min_height": "auto",
    "max_height": "auto", "aspect_ratio": None, "position": "relative", "x": "auto", "y": "auto", "z_index": 0,
    "clip_children": False,
    # M74: CSS Grid. `justify_items`/`align_content` can't be set back to unset;
    # "stretch" lays out the same. A dropped `row_gap`/`column_gap` goes back
    # to the style's `gap` (`_resets`), which `_layout` sets before them.
    "display": "flex", "grid_template_columns": "", "grid_template_rows": "", "grid_auto_columns": "",
    "grid_auto_rows": "", "grid_auto_flow": "row", "grid_column": "auto", "grid_row": "auto", "row_gap": 0.0,
    "column_gap": 0.0, "justify_items": "stretch", "justify_self": None, "align_content": "stretch",
}


def _resets(style: dict[str, Any], dropped: frozenset[str]) -> dict[str, Any]:
    """What each dropped M71/M74 key goes back to: `tre`'s default, but a
    row or column gap to the style's `gap`, which sets both."""
    gap = float(style.get("gap", 0.0))
    return {k: gap if k in ("row_gap", "column_gap") else _OPTIONAL_LAYOUT[k] for k in dropped}


def layout_keys(style: dict[str, Any]) -> frozenset[str]:
    """Which of M71's layout keys `style` gives."""
    return frozenset(k for k in _OPTIONAL_LAYOUT if k in style)


def _layout(style: dict[str, Any]) -> dict[str, Any]:
    """Every layout property, defaults included, as `tre`'s
    `layout_style` sets it -- so a patch can also reset one."""
    return {
        "width": style.get("width", "auto"),
        "height": style.get("height", "auto"),
        "flex_direction": style.get("flex_direction", "horizontal"),
        **_spacing(style.get("padding"), "padding"),
        **_spacing(style.get("margin"), "margin"),
        "gap": float(style.get("gap", 0.0)),
        "flex_grow": float(style.get("flex_grow", 0.0)),
        "flex_shrink": float(style.get("flex_shrink", 1.0)),
        "flex_basis": style.get("flex_basis", "auto"),
        **{k: style[k] for k in _OPTIONAL_LAYOUT if k in style},  # M71: only those a style gives
        # `tre` leaves these unset unless given, and `create` won't take None.
        **({"align_items": style["align_items"]} if style.get("align_items") is not None else {}),
        **({"justify_content": style["justify_content"]} if style.get("justify_content") is not None else {}),
    }


def _color(ctx: _Context, node_id: str, field_name: str, raw: Any) -> RGBA:
    if ctx.scheme is not None and isinstance(raw, str) and raw in ctx.scheme:
        return ctx.scheme[raw]
    try:
        return tokens.parse_color(str(raw))
    except ValueError as exc:
        raise SpecBuildError(f'widget {_q(node_id)}: invalid style.{field_name} "{raw}": {exc}') from None


def _token(node_id: str, field_name: str, value: Any, lookup: Callable[[str], Optional[float]]) -> float:
    if isinstance(value, str):
        resolved = lookup(value)
        if resolved is None:
            raise SpecBuildError(f'widget {_q(node_id)}: unknown style.{field_name} token "{value}"')
        return resolved
    return float(value)


def _paint(ctx: _Context, node_id: str, style: dict[str, Any], *, corner_radius: bool = True) -> dict[str, Any]:
    """The paint every kind shares: corner radius, opacity, border, and
    elevation as `shadows`."""
    paint: dict[str, Any] = {"opacity": float(style.get("opacity", 1.0))}
    if corner_radius:
        paint["corner_radius"] = _token(node_id, "corner_radius", style.get("corner_radius", 0.0), tokens.shape)
    paint["stroke_color"] = _color(ctx, node_id, "border_color", style["border_color"]) if "border_color" in style else _TRANSPARENT
    paint["stroke_width"] = float(style.get("border_width", 0.0))
    level = _token(node_id, "elevation", style.get("elevation", 0.0), tokens.elevation)
    paint["shadows"] = tokens.elevation_shadows(level)
    return paint


def _required_background(ctx: _Context, node: dict[str, Any], style: dict[str, Any], kind: str) -> RGBA:
    if "background" not in style:
        raise SpecBuildError(f'widget {_q(node["id"])}: {kind} requires style.background, none given')
    return _color(ctx, node["id"], "background", style["background"])


def _required_foreground(ctx: _Context, node: dict[str, Any], style: dict[str, Any], kind: str) -> RGBA:
    if "background" in (node.get("style") or {}):
        raise SpecBuildError(
            f'widget {_q(node["id"])}: {kind} has no fill, so style.background doesn\'t apply -- its '
            "glyph/text color is style.foreground"
        )
    if "foreground" not in style:
        raise SpecBuildError(f'widget {_q(node["id"])}: {kind} requires style.foreground, none given')
    return _color(ctx, node["id"], "foreground", style["foreground"])


#: The kinds whose `typography_role` follows the theme's `typography:`:
#: display text. Text inputs keep their own font (M38 Q1).
_THEMED_TEXT = frozenset({"Text", "Link"})


def _text_style(ctx: _Context, node: dict[str, Any], kind: str) -> dict[str, Any]:
    text = node.get("text")
    if not isinstance(text, dict):
        raise SpecBuildError(f'widget {_q(node["id"])}: {kind} requires text, none given')
    role = text.get("typography_role")
    role_style = None
    if role is not None:
        role_style = tokens.type_style(role)
        if role_style is None:
            raise SpecBuildError(f'widget {_q(node["id"])}: unknown text.typography_role "{role}"')
        override = getattr(ctx.layers, "typography", {}).get(role) if kind in _THEMED_TEXT else None
        if override:
            role_style = tokens.TypeStyle(**{f: override.get(f, getattr(role_style, f))
                                             for f in ("font_family", "font_weight", "font_size", "line_height")})
    family = text.get("font_family") or (role_style.font_family if role_style else None)
    if family is None:
        raise SpecBuildError(f'widget {_q(node["id"])}: {kind} requires text.font_family (or text.typography_role), none given')
    size = text.get("font_size") if text.get("font_size") is not None else (role_style.font_size if role_style else None)
    if size is None:
        raise SpecBuildError(f'widget {_q(node["id"])}: {kind} requires text.font_size (or text.typography_role), none given')
    weight = text.get("font_weight") if text.get("font_weight") is not None else (role_style.font_weight if role_style else 400.0)
    line_height = text.get("line_height") if text.get("line_height") is not None else (role_style.line_height if role_style else None)
    content = text.get("content", "")
    if not isinstance(content, str):
        raise SpecBuildError(
            f'widget {_q(node["id"])}: text.content must be a string, got {type(content).__name__} {content!r}'
        )
    return {
        "text": content,
        "font_family": family,
        "font_size": float(size),
        "font_weight": float(weight),
        "line_height": line_height,
    }


def _check_state(node: dict[str, Any], kind: str, expected: str, given: str) -> None:
    if node.get(given) is not None:
        raise SpecBuildError(f'widget {_q(node["id"])}: {kind} takes `{expected}:`, not `{given}:`')


# -- kinds ----------------------------------------------------------------------------------
#
# Each kind has a props function giving `(outer_props, inner_props)` -- what
# to create a node with, and what `patch` sets on an existing one -- so a
# rebuild and a patch can't drift apart.


def _box_props(ctx, node, style):
    fill = _required_background(ctx, node, style, "Rect") if node["kind"] == "Rect" else (
        _color(ctx, node["id"], "background", style["background"]) if "background" in style else _TRANSPARENT
    )
    return {**_layout(style), **_paint(ctx, node["id"], style), "fill": fill}, None


#: What a ScrollView's content box takes from its style (M71): how its
#: children are laid out. Its size, placement and paint are the scroll view's.
_CONTENT = frozenset({"flex_direction", "gap", "padding_top", "padding_right", "padding_bottom", "padding_left",
                      "align_items", "justify_content", "flex_wrap",
                      # M74: a scrolling grid's container keys
                      "display", "grid_template_columns", "grid_template_rows", "grid_auto_columns",
                      "grid_auto_rows", "grid_auto_flow", "row_gap", "column_gap", "justify_items", "align_content"})


def _scroll_props(ctx, node, style):
    """A ScrollView (M71) is `tre`'s `scroll_view` holding one content box,
    which is where its children go: several children straight in a
    `scroll_view` shrink to fit it, and nothing scrolls (it lays its one
    child out unshrunk, and ignores its own padding). The content is
    vertical unless the style says otherwise, and the full width. The
    scroll view is a Tab stop (its keys are `tre`'s since 0.4.2), and its
    scrollbar is the theme's `outline`."""
    outer, _ = _box_props(ctx, node, style)
    content = {k: v for k, v in outer.items() if k in _CONTENT}
    outer = {k: v for k, v in outer.items() if k not in _CONTENT}
    outer.update(scrollbar_fill=_role(ctx, "outline"), focusable=True)
    content.update(flex_direction=style.get("flex_direction", "vertical"), width="100%",
                   **{k: style.get(k, _ALIGNMENT_DEFAULTS[k]) for k in _ALIGNMENT_DEFAULTS})
    return outer, content


def natural_size(window: Any, props: dict[str, Any], style: dict[str, Any]) -> dict[str, float]:
    """A Text or Link's measured `width`/`height` for whichever its style
    leaves out (M41): `tre` 0.3.4's text has no intrinsic size, so text
    without one was 0 px wide -- every fragment's label was invisible."""
    missing = [d for d in ("width", "height") if style.get(d) is None]
    if not missing:
        return {}
    width, height = window.measure_text(props["text"], font_family=props["font_family"],
                                        font_size=props["font_size"], font_weight=props["font_weight"],
                                        line_height=props.get("line_height"))
    return {d: float(v) for d, v in (("width", width), ("height", height)) if d in missing}


def _text_props(ctx, node, style):
    fill = _required_foreground(ctx, node, style, node["kind"])
    props = {**_layout(style), **_paint(ctx, node["id"], style), **_text_style(ctx, node, node["kind"]), "fill": fill}
    props.update(natural_size(ctx.window, props, style))
    return props, None


_PLACED = ("margin_top", "margin_right", "margin_bottom", "margin_left", "flex_grow", "flex_shrink", "flex_basis",
           "align_self", "position", "x", "y", "z_index", "min_width", "max_width", "min_height", "max_height",
           "aspect_ratio", "grid_column", "grid_row", "justify_self")


def _link_props(ctx, node, style):
    """A Link is a box holding its text (M41): `tre` 0.3.4's `text` never
    gets pointer events, so a Link that was a bare `text` could only be
    clicked from the keyboard. The box takes the events, focus, role and
    label (the text's content); the text is only drawn."""
    text, _ = _text_props(ctx, node, style)
    layout = _layout(style)
    outer = {k: v for k, v in layout.items() if k in _PLACED or k in ("width", "height")}
    outer.update(role="link", cursor="pointer", focusable=True, label=text["text"])
    inner = {k: v for k, v in text.items() if k not in _PLACED}
    inner.update(hit_testable=False, a11y_hidden=True)
    return outer, inner


def _text_field_props(ctx, node, style):
    background = _required_background(ctx, node, style, "TextField")
    text = _text_style(ctx, node, "TextField")
    text.pop("line_height")
    outer = {**_layout(style), **_paint(ctx, node["id"], style), "fill": background}
    # `tre`'s TextField draws its text in MD3's baseline on_surface, not a theme role.
    inner = {**text, "fill": _TEXT_FIELD_GLYPH, "flex_grow": 1.0, "align_self": "stretch", "role": "textbox", "focusable": True}
    return outer, inner


def _image_props(ctx, node, style):
    image = node.get("image")
    if not isinstance(image, dict):
        raise SpecBuildError(f'widget {_q(node["id"])}: Image requires image, none given')
    rgba, width, height = ctx.frames.get(node["id"], (bytes(4), 1, 1))
    return {
        **_layout(style), **_paint(ctx, node["id"], style),
        "rgba": rgba, "pixel_width": width, "pixel_height": height, "fit": str(image.get("fit", "cover")).lower(),
    }, None


def _icon_props(ctx, node, style):
    icon = node.get("icon")
    if not isinstance(icon, dict):
        raise SpecBuildError(f'widget {_q(node["id"])}: Icon requires icon, none given')
    data = icon_path(str(icon.get("name")))
    if data is None:
        raise SpecBuildError(f'widget {_q(node["id"])}: unknown icon "{icon.get("name")}"')
    tint = _required_foreground(ctx, node, style, "Icon")
    return {**_layout(style), **_paint(ctx, node["id"], style, corner_radius=False),
            "data": data, "view_box": ICON_VIEW_BOX, "fill": tint}, None


_PRIMITIVE = {
    "Rect": ("box", _box_props), "Container": ("box", _box_props), "Text": ("text", _text_props),
    "Link": ("box", _link_props), "TextField": ("box", _text_field_props), "Image": ("image", _image_props),
    "Icon": ("path", _icon_props), "ScrollView": ("scroll_view", _scroll_props),
}


def _a11y_for(node: dict[str, Any], kind: str, *, patching: bool) -> dict[str, Any]:
    props = _a11y_props(node, patching=patching)
    if kind == "Link" and props.get("label") is None:
        props.pop("label", None)  # a Link without a fixed `a11y:` label is named by its text (or its binding)
    return props


#: The node inside a two-node kind's box: what it's drawn with.
_INNER = {"TextField": "text_input", "Link": "text", "ScrollView": "box"}


#: Kinds with their own role and focus (a Link, a TextField's input, and
#: the MD3 controls); `on_click` doesn't change them.
_OWN_ROLE = frozenset({"Link", "TextField"}) | _CONTROL_KINDS


def _clickable(node: dict[str, Any]) -> bool:
    return "on_click" in (node.get("handlers") or {}) and node["kind"] not in _OWN_ROLE


#: Kinds whose node can hold the state layer and ripple (a `box`).
_INTERACTIVE_KINDS = frozenset({"Rect", "Container"})


def _check_interaction(node: dict[str, Any]) -> None:
    value = node.get("interaction")
    if value is None or isinstance(value, bool):
        return
    if not isinstance(value, dict) or set(value) - {"color"}:
        raise SpecBuildError(f"widget {_q(node['id'])}: `interaction:` takes true, false or {{color: ...}}, "
                             f"got {value!r}")
    if node["kind"] not in _INTERACTIVE_KINDS:
        raise SpecBuildError(f"widget {_q(node['id'])}: `interaction:` needs a Rect or Container, "
                             f"not a {node['kind']}")


def focus_ring_color(scheme: Optional[dict[str, RGBA]]) -> RGBA:
    """MD3's focus indicator colour: the theme's `secondary`."""
    return _role(_Context(None, (), scheme, {}), "secondary")


#: The `a11y:` fields a YAML node may set; widget states (`checked`, ...)
#: belong to Tesserae's widgets (M40).
_A11Y_YAML = ("label", "role", "hidden", "live", "level")
#: What each `a11y:` field resets to when a patch drops it.
_A11Y_RESET = {"label": None, "a11y_hidden": False, "live": None, "level": None}
#: The `a11y:` fields a `{{ }}` binding may set (M47 Q2), and the
#: property each is; `role` and `live` stay fixed.
A11Y_BINDABLE = {"label": "label", "hidden": "a11y_hidden", "level": "level"}


def is_binding(value: Any) -> bool:
    """Whether an `a11y:` value is a `{{ }}` binding (M47 Q1)."""
    return isinstance(value, str) and "{{" in value


def a11y_bindings(node: dict[str, Any]) -> dict[str, str]:
    """The node's bound `a11y:` fields, `{field: "{{ expr }}"}` (the view wires them)."""
    value = node.get("a11y")
    return {k: v for k, v in value.items() if is_binding(v)} if isinstance(value, dict) else {}


def _a11y_fields(node: dict[str, Any]) -> dict[str, Any]:
    """The node's fixed `a11y:` fields, checked, as `tre` properties. A
    bound one (M47) is left to the view, and only its field is checked."""
    value = node.get("a11y")
    if value is None:
        return {}
    where = f"widget {_q(node['id'])}"
    if not isinstance(value, dict):
        raise SpecBuildError(f"{where}: `a11y:` takes a mapping of {', '.join(_A11Y_YAML)}, got {value!r}")
    unknown = set(value) - set(_A11Y_YAML)
    if unknown:
        raise SpecBuildError(f"{where}: unknown a11y field(s) {sorted(unknown)} (known: {', '.join(_A11Y_YAML)})")
    if "role" in value and node["kind"] in _OWN_ROLE:
        raise SpecBuildError(f"{where}: a {node['kind']} has its own role; `a11y:` can't set `role`")
    bound = [k for k, v in value.items() if is_binding(v)]
    fixed_only = [k for k in bound if k not in A11Y_BINDABLE]
    if fixed_only:
        raise SpecBuildError(f"{where}: a11y {fixed_only[0]} can't be bound -- only "
                             f"{', '.join(A11Y_BINDABLE)} can follow a binding")
    try:
        return a11y.check({k: v for k, v in value.items() if k not in bound}, where)
    except ValueError as exc:
        raise SpecBuildError(str(exc)) from None


def _a11y_props(node: dict[str, Any], *, patching: bool) -> dict[str, Any]:
    """Accessibility properties for the node that carries them (a
    TextField's `text_input`, otherwise the node): the `a11y:` field, and
    a clickable node's focus and role (M39). On a patch, dropped fields
    reset."""
    fields = _a11y_fields(node)
    bound = {A11Y_BINDABLE[k] for k in a11y_bindings(node)}  # the view sets these; a patch leaves them
    reset = {k: v for k, v in _A11Y_RESET.items() if k not in bound}
    props = {**reset, **{k: v for k, v in fields.items() if k != "role"}} if patching else {
        k: v for k, v in fields.items() if k != "role"}
    if node["kind"] not in _OWN_ROLE:
        if _clickable(node):
            props.update(focusable=True, role=fields.get("role", "button"))
        elif "role" in fields or patching:
            props["role"] = fields.get("role", "none")
            if patching:
                props["focusable"] = False
    return props


def resting_focus(node: dict[str, Any]) -> bool:
    """Whether `node` is focusable when it isn't disabled (M70): a Link and
    a TextField are, a clickable node is (a Tab stop, M39), and otherwise
    it's what its `a11y:` says."""
    if node["kind"] in ("Link", "TextField"):
        return True
    return bool(_a11y_props(node, patching=True).get("focusable", False))


def interaction_tint(node: dict[str, Any], scheme: Optional[dict[str, RGBA]]) -> Optional[RGBA]:
    """The state layer and ripple's tint for `node` (M39), or `None` for no
    interaction feedback. A clickable Rect or Container gets it in the
    theme's `on_surface` unless it says `interaction: false`;
    `interaction: {color: ...}` picks the colour (a theme role or a hex),
    and `interaction: true` turns it on without `on_click`."""
    value = node.get("interaction")
    if node["kind"] not in _INTERACTIVE_KINDS or value is False or (value is None and not _clickable(node)):
        return None
    ctx = _Context(None, (), scheme, {})
    if isinstance(value, dict) and "color" in value:
        return _color(ctx, node["id"], "interaction.color", value["color"])
    return _role(ctx, "on_surface")


def _create(ctx, node, style, built):
    kind = node["kind"]
    if kind in _WIDGET_KINDS:  # M60
        widget = _graph_widget(ctx, node, style)
        built.controls[node["id"]] = widget
        a11y_props = _a11y_props(node, patching=False)
        if a11y_props:
            widget.node.set(**a11y_props)
        return widget.node, (widget.part("body") if kind == "GraphNode" else widget.node)
    if kind in _CONTROL_KINDS:
        control = _control(ctx, node, style, built)
        built.controls[node["id"]] = control
        a11y_props = _a11y_props(node, patching=False)  # its label, hidden, live, level (M47: they were dropped)
        if a11y_props:
            _a11y_target(control).set(**a11y_props)
        return control.node, control.node
    tre_kind, props_of = _PRIMITIVE[kind]
    outer_props, inner_props = props_of(ctx, node, style)
    # M39: as `tre`'s `set_on_click` did, a clickable node is a focusable
    # Tab stop that Enter and Space activate -- and a button.
    (inner_props if kind == "TextField" else outer_props).update(_a11y_for(node, kind, patching=False))
    outer = ctx.window.create(tre_kind, **outer_props)
    if inner_props is None:
        return outer, outer
    inner = ctx.window.create(_INNER[kind], **inner_props)
    outer.add_child(inner)
    return outer, inner


#: What an unset alignment resets to on a patch: flexbox's defaults,
#: since `set` won't take `None`.
_ALIGNMENT_DEFAULTS = {"align_items": "stretch", "justify_content": "flex_start"}


def patch(
    window: Any,
    node: dict[str, Any],
    outer: Any,
    inner: Any,
    *,
    scheme: Optional[dict[str, RGBA]] = None,
    layers: tuple[Optional[Sheet], ...] = (),
    frames: Optional[dict[str, tuple[bytes, int, int]]] = None,
    state: bool = True,
    control: Any = None,
    before: frozenset[str] = frozenset(),
) -> frozenset[str]:
    """Sets `node`'s properties on its existing nodes, in place -- what
    `tre`'s `patch_node` does. The node keeps its identity, focus and
    running animations. Children aren't touched.

    For a control kind, `control` is its control: it's re-themed, and its
    state set from the spec unless `state=False` (a theme or stylesheet
    change, which leaves what the user did).

    `before` is the M71 layout keys the node's style gave when it was last
    built or patched (`Built.layout_keys`): one it no longer gives is reset.
    Returns the keys it gives now."""
    ctx = _Context(window, layers, scheme, frames or {})
    style = resolve_style(node, layers)
    kind = node["kind"]
    given = layout_keys(style)
    resets = _resets(style, before - given)
    try:
        if kind in _WIDGET_KINDS:
            if control is not None:
                _patch_graph_widget(ctx, node, control, state)
            return given
        if kind in _CONTROL_KINDS:
            if control is not None:
                _patch_control(ctx, node, style, control, state, resets)
                _a11y_target(control).set(**_a11y_props(node, patching=True))
            return given
        _, props_of = _PRIMITIVE[kind]
        outer_props, inner_props = props_of(ctx, node, style)
        (inner_props if kind == "TextField" else outer_props).update(_a11y_for(node, kind, patching=True))
        for key, value in resets.items():  # where `_layout` would have put it (a Link's text, a ScrollView's content)
            on_inner = (kind == "Link" and key not in _PLACED) or (kind == "ScrollView" and key in _CONTENT)
            (inner_props if on_inner else outer_props)[key] = value
        outer.set(**{**_ALIGNMENT_DEFAULTS, **outer_props})  # the node's own alignment wins
        if inner_props is not None:
            inner.set(**inner_props)
    except ValueError as exc:
        if isinstance(exc, SpecBuildError):
            raise
        raise SpecBuildError(f"widget {_q(node['id'])}: {exc}") from None
    return given


def _role(ctx, name):
    return (ctx.scheme or {}).get(name, _BASELINE[name])


#: Layout a control's node takes from its style: where it sits, not its
#: size (a control is built at its size) or its own content alignment.
_PLACEMENT = frozenset({
    "margin_top", "margin_right", "margin_bottom", "margin_left", "flex_grow", "flex_shrink", "flex_basis",
    "align_self", "position", "x", "y", "z_index", "grid_column", "grid_row", "justify_self",
})
_PLACEMENT_RESET = {"margin_top": 0.0, "margin_right": 0.0, "margin_bottom": 0.0, "margin_left": 0.0,
                    "flex_grow": 0.0, "flex_shrink": 1.0}


def _theme(ctx: _Context) -> Any:
    from tesserae.theme import Theme

    return Theme(None, False, ctx.scheme, {}, {})


def _control_colour(ctx: _Context, node: dict[str, Any], style: dict[str, Any]) -> Optional[RGBA]:
    """The selected/active colour a control's style gives: `background`
    (the fragments' param) or, for the indicators, `foreground`."""
    field = "foreground" if node["kind"] in _INDICATOR_KINDS else "background"
    raw = style.get(field)
    return None if raw is None else _color(ctx, node["id"], field, raw)


_INDICATOR_KINDS = frozenset({"CircularProgress", "LinearProgress", "LoadingIndicator"})


def _control(ctx: _Context, node: dict[str, Any], style: dict[str, Any], built: Built) -> Any:
    """The MD3 control for one of the eight control kinds (M40)."""
    from tesserae import controls

    kind, width, height = node["kind"], style.get("width"), style.get("height")
    if kind == "Checkbox":
        _check_state(node, "Checkbox", "checked", "selected")
    elif kind in ("Switch", "RadioButton"):
        _check_state(node, kind, "selected", "checked")
    group = node.get("group")
    if group is not None and (kind != "RadioButton" or not isinstance(group, str)):
        raise SpecBuildError(f"widget {_q(node['id'])}: `group:` is a RadioButton's, and a name "
                             f"(radio buttons with the same one exclude each other), got {group!r} on a {kind}")
    common = dict(theme=_theme(ctx), color=_control_colour(ctx, node, style))
    size = {k: float(v) for k, v in (("width", width), ("height", height)) if v is not None}
    if kind in _INDICATOR_KINDS:
        value = node.get("value")
        if kind == "LinearProgress":
            control = controls.LinearProgress(ctx.window, value=float(value or 0.0), width=size.get("width", 240.0),
                                              **common)
            if "height" in size:
                control.node.set(height=size["height"])
                control.bar.set(height=size["height"])
        elif kind == "CircularProgress":
            control = controls.CircularProgress(ctx.window, value=float(value or 0.0), size=size.get("width", 48.0),
                                                **common)
        else:
            control = controls.LoadingIndicator(ctx.window, size=size.get("width", 48.0), **common)
    else:
        common["listen"] = ctx.listen
        if kind == "Checkbox":
            control = controls.Checkbox(ctx.window, checked=bool(node.get("checked") or False), **size, **common)
        elif kind == "RadioButton":
            radio_group = None
            if group is not None:
                radio_group = built.radio_groups.setdefault(group, controls.RadioGroup())
            control = controls.RadioButton(ctx.window, selected=bool(node.get("selected") or False),
                                           group=radio_group, **size, **common)
        elif kind == "Switch":
            control = controls.Switch(ctx.window, selected=bool(node.get("selected") or False), **size, **common)
        elif kind == "Slider":
            control = controls.Slider(ctx.window, value=float(node.get("value") or 0.0), **size, **common)
        elif kind == "SpinBox":  # M58: two buttons and a field, sized by MD3, not `width`/`height`
            common.pop("color")
            control = controls.SpinBox(ctx.window, value=_spin_number(node.get("value") or 0, node.get("step") or 1),
                                       min=node.get("min"), max=node.get("max"), step=node.get("step") or 1,
                                       **common)
        else:  # TimePickerDial
            common.pop("color")
            control = controls.TimePickerDial(ctx.window, hour=int(node.get("hour") or 0),
                                              minute=int(node.get("minute") or 0), size=size.get("width", 256.0),
                                              **common)
    if node.get("disabled") is not None:  # M70: a control's static `disabled:` is its own
        control.disabled.set(bool(node["disabled"]))
    placement = {k: v for k, v in _layout(style).items() if k in _PLACEMENT}
    if placement:
        control.node.set(**placement)
    return control


def _spin_number(value: Any, step: Any) -> Any:
    """A SpinBox's `value:` as `spin_box()` reads it: a number, or its text;
    whole with a whole step stays an `int`."""
    number = float(value) if isinstance(value, str) else value
    if isinstance(number, float) and number.is_integer() and isinstance(step, int):
        number = int(number)
    return number


def _graph_widget(ctx: _Context, node: dict[str, Any], style: dict[str, Any]) -> Any:
    """A NodeGraph's `node_graph` widget, or a GraphNode's `graph_node` in
    the NodeGraph being built (M60). Both take their size from `style`."""
    from tesserae.widgets.media import graph_node, node_graph

    node_id, kind = node["id"], node["kind"]
    size = [style.get("width"), style.get("height")]
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) for v in size):
        raise SpecBuildError(f"widget {_q(node_id)}: a {kind} needs a numeric style width and height, got {size}")
    width, height = float(size[0]), float(size[1])
    if kind == "NodeGraph":
        return node_graph(ctx.window, width, height, theme=_theme(ctx))  # `add_child` moves it into the view
    if ctx.graph is None:
        raise SpecBuildError(f"widget {_q(node_id)}: a GraphNode belongs inside a NodeGraph")
    x, y = float(node.get("x") or 0.0), float(node.get("y") or 0.0)
    widget = graph_node(ctx.window, ctx.graph, str(node.get("label") or ""), x, y, width, height, theme=_theme(ctx))
    widget.declared = (x, y)  # where the file puts it: a reload moves it only if this changes
    widget.on_change = widget.on_move  # `on_change` hears the user's moves
    return widget


def connect_edges(graph: Any, node: dict[str, Any], built: Built) -> None:
    """(Re)draws a NodeGraph's `edges:` (`[{from: id, to: id}, ...]`, its
    GraphNodes' ids), replacing any it had (M60)."""
    for _, _, path in graph.edges:
        path.destroy()
    graph.edges.clear()
    ids = {child["id"] for child in node.get("children") or []}
    for index, edge in enumerate(node.get("edges") or []):
        if not isinstance(edge, dict) or set(edge) != {"from", "to"}:
            raise SpecBuildError(f"widget {_q(node['id'])}: edges[{index}] is {{from: id, to: id}}, got {edge!r}")
        missing = [end for end in (edge["from"], edge["to"]) if end not in ids]
        if missing:
            raise SpecBuildError(f"widget {_q(node['id'])}: edges[{index}] names no GraphNode {missing[0]!r} here")
        graph.edge(built.controls[edge["from"]], built.controls[edge["to"]])


def _patch_graph_widget(ctx: _Context, node: dict[str, Any], widget: Any, state: bool) -> None:
    widget.set_theme(_theme(ctx))
    if node["kind"] != "GraphNode":
        return
    label = str(node.get("label") or "")
    widget.part("label").set(text=label)
    widget.node.set(label=label)
    declared = (float(node.get("x") or 0.0), float(node.get("y") or 0.0))
    if state and declared != widget.declared:  # the file moved it; otherwise the user's place stays
        widget.declared = declared
        widget.position.set(declared)


def _a11y_target(control: Any) -> Any:
    """Where a control's `a11y:` goes: its focus target -- a SpinBox's
    text input, else the control's node (M58)."""
    return getattr(control, "input", None) or control.node


def _patch_control(ctx: _Context, node: dict[str, Any], style: dict[str, Any], control: Any, state: bool,
                   resets: Optional[dict[str, Any]] = None) -> None:
    placement = {k: v for k, v in {**(resets or {}), **_layout(style)}.items() if k in _PLACEMENT}
    control.node.set(**{**_PLACEMENT_RESET, **placement})
    control._color = _control_colour(ctx, node, style)
    control.set_theme(_theme(ctx))
    if not state:
        return
    kind = node["kind"]
    control.disabled.set(bool(node.get("disabled") or False))  # M70
    if kind == "Checkbox":
        control.checked.set(bool(node.get("checked") or False))
    elif kind in ("Switch", "RadioButton"):
        control.selected.set(bool(node.get("selected") or False))
    elif kind in ("Slider", "CircularProgress", "LinearProgress"):
        control.value.set(float(node.get("value") or 0.0))
    elif kind == "SpinBox":
        control.value.set(control._fit(_spin_number(node.get("value") or 0, control.step)))
    elif kind == "TimePickerDial":
        control.hour.set(int(node.get("hour") or 0) % 24)
        control.minute.set(int(node.get("minute") or 0) % 60)


def control_shape(node: dict[str, Any], layers: tuple[Optional[Sheet], ...]) -> tuple[Any, ...]:
    """What a control is built at (its kind and size): when it changes,
    the reconciler rebuilds the control rather than patching it."""
    style = resolve_style(node, layers)
    return (node.get("kind"), style.get("width"), style.get("height"), node.get("group"),
            node.get("min"), node.get("max"), node.get("step"))  # a SpinBox's bounds are built in (M58)
