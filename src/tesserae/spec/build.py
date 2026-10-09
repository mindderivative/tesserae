"""Tesserae's spec compiler: builds an expanded view spec
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
.
"""

from __future__ import annotations

import difflib
import functools
import math
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from tesserae import a11y, tokens
from tesserae.icons import ICON_VIEW_BOX, icon_path, icon_view_box
from tesserae.spec.cascade import STYLE_FIELDS, Sheet, resolve_style
from tesserae.spec import effects, layout, richtext, transition
from tesserae.spec.canvas import painter as canvas_painter, plan as canvas_plan
from tesserae.spec.layout import LAYOUT_FIELDS, REPLACED, LayoutError, engine_style

__all__ = ["style_props", 
    "A11Y_BINDABLE", "Built", "Layers", "SpecBuildError", "a11y_bindings", "build", "control_shape", "focus_ring_color",
    "interaction_tint", "is_binding", "natural_size", "patch",
    "prepare_layers",
    "shipped_default_theme",
]

RGBA = tuple[int, int, int, int]
_TRANSPARENT: RGBA = (0, 0, 0, 0)
#: MD3's baseline colours, for nodes with no theme.
_BASELINE = tokens.BASELINE
_CONTROL_KINDS = frozenset({
    "Checkbox", "RadioButton", "Switch", "Slider", "SpinBox", "CircularProgress", "LinearProgress",
    "LoadingIndicator", "TimePickerDial",
})
#: Kinds built with a `tesserae.widgets` widget (M60): a node graph and its nodes.
_WIDGET_KINDS = frozenset({"NodeGraph", "GraphNode"})
_KINDS = _CONTROL_KINDS | _WIDGET_KINDS | {"Rect", "Container", "Text", "Link", "TextField", "Image", "Icon", "Svg",
                                           "ScrollView", "Canvas", "Overlay"}
_NODE_KEYS = frozenset({
    "id", "kind", "classes", "style", "text", "checked", "selected", "value", "hour", "minute",
    "image", "icon", "svg", "canvas", "scroll", "overlay", "virtual", "track", "stop_indicator", "buffer", "error", "icons", "ticks", "value_indicator", "bindings", "handlers", "two_way", "interaction", "a11y", "group", "children",
    "component_of",  # the fragment a node is the root of (M57): its theme `components:` entry
    "embed",  # a `view:` node, made a container (0.4.4): the view to build into it and its `with:`
    "window",  # a root `kind: Window`, made a container (0.4.4): the OS window's title, borderless, sizes
    "dock", "dock_panel", "split_handle",  # a Dock, a DockPanel and the handle between split panels, made containers (0.4.4)
    "min", "max", "step",  # a SpinBox's (M58)
    "spin",  # a SpinBox's decimals, prefix, suffix and wrap
    "dial",  # a TimePickerDial's mode and auto_advance
    "disabled",  # any node's (M70): the View applies it, or a control's own
    "window_region",  # any node's (0.3.0 M3): part of the window's title bar, or not
    "tooltip",  # any node's text on a rest of the pointer (a title bar's buttons): the view that has it shows it

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
    #: Each node's parent's id: its `flex_direction` and `display` say what the node's own `flex` means.
    parent_ids: dict[str, Optional[str]] = field(default_factory=dict)


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
    #: The `(flex_direction, display)` of the node whose children are being built.
    parent: tuple[str, str] = ("horizontal", "flex")


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
    """The cascade's prepared layers (Tesserae's own parts' looks -- a
    TitleBar's, 0.3.0 M3 -- then the default theme, the custom theme and
    the stylesheet), plus the two themes' `typography:` overrides,
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
    from tesserae.spec.title_bar import STYLES as title_bar_styles

    # First, under every theme: the look of Tesserae's own generated parts
    # (a TitleBar's, 0.3.0 M3), which any layer above can restyle.
    layers = Layers((Sheet.of(title_bar_styles), Sheet.of(default_theme), Sheet.of(custom_theme),
                     Sheet.of(stylesheet)))
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
    parent: Optional[str] = None,
) -> Any:
    """Builds `spec` with already-prepared layers, recording its nodes in
    `into` (a new `Built` if none); returns the subtree's outer root.
    `listen` is the listener registrar the controls share with the view;
    `graph`, the NodeGraph widget a GraphNode `spec` belongs to."""
    ctx = _Context(window, layers, scheme, frames or {}, listen, graph)
    built = into if into is not None else Built(root=None)
    if parent is not None and parent in built.specs:  # a subtree added under a node that is already built
        ctx.parent = layout_of(built.specs[parent], layers)
    return _build(ctx, spec, built, parent)


_shipped: Optional[dict[str, Any]] = None


def shipped_default_theme() -> dict[str, Any]:
    """`tre`'s shipped default theme (Tesserae's copy)."""
    global _shipped
    if _shipped is None:
        from pathlib import Path

        import yaml

        _shipped = yaml.safe_load((Path(__file__).parent / "default_theme.yaml").read_text(encoding="utf-8"))
    return _shipped


def _did_you_mean(unknown: Any, known: Any) -> str:
    """` -- did you mean 'foreground'?` for names that are a slip away from
    a known one (0.3.1), or nothing: a name that resembles none is left
    for the reader, not guessed at."""
    pairs = []
    for name in sorted(unknown, key=str):
        close = difflib.get_close_matches(str(name), sorted(known), n=1, cutoff=0.7)
        if close:
            pairs.append((name, close[0]))
    if not pairs:
        return ""
    if len(pairs) == 1:
        return f" -- did you mean {pairs[0][1]!r}?"
    return " -- did you mean " + ", ".join(f"{good!r} for {bad!r}" for bad, good in pairs) + "?"


def _engine(node_id: str, style: dict[str, Any], parent: tuple[str, str]) -> dict[str, Any]:
    """`style` with the layout fields turned into the engine's (`tesserae.spec.layout`)."""
    try:
        return engine_style(node_id, style, parent)
    except LayoutError as exc:
        raise SpecBuildError(str(exc)) from None


def layout_of(node: dict[str, Any], layers: tuple[Optional[Sheet], ...]) -> tuple[str, str]:
    """The `(flex_direction, display)` a node's style gives its children."""
    style = resolve_style(node, layers)
    return style.get("flex_direction", "horizontal"), style.get("display", "flex")


def _build(ctx: _Context, node: dict[str, Any], built: Built, parent_id: Optional[str] = None) -> Any:
    node_id, kind = node.get("id"), node.get("kind")
    if not isinstance(node_id, str):
        raise SpecBuildError(f"every widget needs an `id:`, got {node!r}")
    if kind not in _KINDS:
        raise SpecBuildError(f"widget {_q(node_id)}: unknown kind {kind!r}"
                             + _did_you_mean([kind] if isinstance(kind, str) else [], _KINDS))
    unknown = set(node) - _NODE_KEYS
    if unknown:
        raise SpecBuildError(f"widget {_q(node_id)}: unknown field(s) {sorted(unknown)}"
                             + _did_you_mean(unknown, _NODE_KEYS))
    style = resolve_style(node, ctx.layers)
    if "zone" in style and "dock_panel" not in node:
        raise SpecBuildError(f"widget {_q(node_id)}: style.zone is for a DockPanel in a Dock")
    _check_interaction(node)
    _a11y_fields(node)
    try:
        transition.plan(node_id, kind, style)
    except ValueError as exc:
        raise SpecBuildError(str(exc)) from None
    engine = _engine(node_id, style, ctx.parent)  # first: it says what replaces an engine name
    unknown_style = set(style) - STYLE_FIELDS - (set(REPLACED) | {"align_content", "align_self"} if layout.LEGACY_ENGINE_NAMES else set())
    if unknown_style:
        raise SpecBuildError(f"widget {_q(node_id)}: unknown style field(s) {sorted(unknown_style)}"
                             + _did_you_mean(unknown_style, STYLE_FIELDS))
    style = engine

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
    built.parent_ids[node_id] = parent_id
    if kind == "NodeGraph":  # its GraphNodes place themselves in the graph's content (M60)
        graph, ctx.graph = ctx.graph, built.controls[node_id]
        try:
            for child in node.get("children") or []:
                if child.get("kind") != "GraphNode":
                    raise SpecBuildError(f"widget {_q(node_id)}: a NodeGraph's children are GraphNodes, "
                                         f"got {child.get('kind')!r} ({child.get('id')!r})")
                _build(ctx, child, built, node_id)
        finally:
            ctx.graph = graph
        connect_edges(built.controls[node_id], node, built)
        return outer
    # a GraphNode's content goes in its body, a ScrollView's in its content box (M71)
    parent = inner if kind in ("GraphNode", "ScrollView", "Overlay") else outer
    above, ctx.parent = ctx.parent, (style.get("flex_direction", "horizontal"), style.get("display", "flex"))
    try:
        for child in node.get("children") or []:
            parent.add_child(_build(ctx, child, built, node_id))
    finally:
        ctx.parent = above
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
    # a transform (`style.scale` ...): drawn as the style says, and put back only if it was said before: Python code also turns a node (a chevron)
    "scale": 1.0, "translate_x": 0.0, "translate_y": 0.0, "rotation_deg": 0.0,
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


@functools.lru_cache(maxsize=1)
def _baseline_roles() -> dict[str, RGBA]:
    """MD3's baseline roles, for a view with no theme (0.3.3, #82): what an unthemed widget already uses."""
    return tokens.baseline_scheme()


def _color(ctx: _Context, node_id: str, field_name: str, raw: Any) -> RGBA:
    """A style colour: a theme role (the view's theme, or MD3's baseline when it has none), or a CSS colour."""
    roles = ctx.scheme if ctx.scheme is not None else _baseline_roles()
    if isinstance(raw, str) and raw in roles:
        return roles[raw]
    try:
        return tokens.resolve_color(str(raw), roles)
    except ValueError as exc:
        hint = _did_you_mean([raw], roles) if isinstance(raw, str) else ""
        raise SpecBuildError(f'widget {_q(node_id)}: invalid style.{field_name} "{raw}": {exc}{hint}') from None


def _fill(ctx: _Context, node_id: str, field_name: str, raw: Any) -> Any:
    """A style colour or a gradient (`tesserae.spec.effects`): RGBA, or a `tre.Gradient` whose stops are roles or colours."""
    if not effects.is_gradient(raw):
        return _color(ctx, node_id, field_name, raw)
    try:
        return effects.make_gradient(raw, lambda c: _color(ctx, node_id, field_name, c), f"widget {_q(node_id)}: style.{field_name}")
    except ValueError as exc:
        if isinstance(exc, SpecBuildError):
            raise
        raise SpecBuildError(str(exc)) from None


def _token(node_id: str, field_name: str, value: Any, lookup: Callable[[str], Optional[float]]) -> float:
    if isinstance(value, str):
        resolved = lookup(value)
        if resolved is None:
            raise SpecBuildError(f'widget {_q(node_id)}: unknown style.{field_name} token "{value}"')
        return resolved
    return float(value)


_CORNERS = ("top_left", "top_right", "bottom_right", "bottom_left")
#: An edge's two corners, for `corner_radius: {top: 12}`.
_EDGES = {"top": ("top_left", "top_right"), "right": ("top_right", "bottom_right"), "bottom": ("bottom_right", "bottom_left"),
          "left": ("bottom_left", "top_left")}


def _corner_radius(node_id: str, value: Any) -> Any:
    """A style's `corner_radius` as the node property: one radius (a number or a shape token) for every corner, or four, one per corner, as a list
    `[top_left, top_right, bottom_right, bottom_left]` or a mapping of corners and edges (`top`, `right`, `bottom`, `left`; a corner named
    beats its edge) with the corners it leaves out square. Four equal radii are one."""
    if isinstance(value, dict):
        unknown = [k for k in value if k not in _CORNERS and k not in _EDGES]
        if unknown:
            raise SpecBuildError(f'widget {_q(node_id)}: style.corner_radius has no "{unknown[0]}" (corners: {", ".join(_CORNERS)}; '
                                 f'edges: {", ".join(_EDGES)})')
        corners = dict.fromkeys(_CORNERS, 0.0)
        for key in [*(k for k in value if k in _EDGES), *(k for k in value if k in _CORNERS)]:  # edges first, then the corners that override them
            for corner in _EDGES.get(key, (key,)):
                corners[corner] = _radius(node_id, value[key])
        radii = list(corners.values())
    elif isinstance(value, (list, tuple)):
        if len(value) != 4:
            raise SpecBuildError(f'widget {_q(node_id)}: style.corner_radius takes four radii ({", ".join(_CORNERS)}), not {len(value)}')
        radii = [_radius(node_id, v) for v in value]
    else:
        return _radius(node_id, value)
    return radii[0] if len(set(radii)) == 1 else tuple(radii)


def _radius(node_id: str, value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise SpecBuildError(f'widget {_q(node_id)}: style.corner_radius is pixels or a shape token, not {value!r}')
    return _token(node_id, "corner_radius", value, tokens.shape)


#: The style fields that are a node property of the same name (0.3.3, #81).
_STYLE_PASSTHROUGH = frozenset({
    "width", "height", "min_width", "max_width", "min_height", "max_height", "flex_direction", "flex_wrap",
    "position", "display", "aspect_ratio", "x", "y", "z_index", "clip_children", "grid_template_columns",
    "grid_template_rows", "grid_auto_columns", "grid_auto_rows", "grid_auto_flow", "grid_column", "grid_row",
})
_STYLE_FLOATS = frozenset({"gap", "row_gap", "column_gap"})
#: What `tesserae.spec.layout` turns into, for a box that isn't a spec node.
_LAYOUT_PROPS = ("align_items", "justify_content", "align_content", "justify_items", "justify_self", "align_self")


def style_props(style: dict[str, Any], scheme: Optional[dict[str, RGBA]], where: str = "a style") -> dict[str, Any]:
    """The node properties a `style:` sets, only those it gives, for a box that isn't a spec node (a part
    of an app shell, 0.3.3 #81): `background` is the `fill`, a role resolved by `scheme` (MD3's baseline
    without one), `border_color` the `stroke_color`, `elevation` the `shadows`. `foreground` has nothing to
    colour in a box, so it is an error. Raises `SpecBuildError`, naming `where`."""
    ctx = _Context(window=None, layers=(), scheme=scheme, frames={})
    props: dict[str, Any] = {}
    laid = {k for k in style if k in LAYOUT_FIELDS or k in REPLACED}
    if laid:  # where its children go, how it takes room: the engine's names for them
        engine = _engine(where, style, ctx.parent)
        props.update({k: engine[k] for k in _LAYOUT_PROPS if k in engine})
        if "flex" in style:
            props.update(flex_grow=engine["flex_grow"], flex_shrink=engine["flex_shrink"])
    for key, value in style.items():
        if key in laid:
            continue
        if key in _STYLE_PASSTHROUGH:
            props[key] = value
        elif key in _STYLE_FLOATS:
            props[key] = float(value)
        elif key in ("padding", "margin"):
            props.update(_spacing(value, key))
        elif key == "background":
            props["fill"] = _fill(ctx, where, "background", value)
        elif key == "border_color":
            props["stroke_color"] = _fill(ctx, where, "border_color", value)
        elif key == "border_width":
            props["stroke_width"] = float(value)
        elif key == "corner_radius":
            props["corner_radius"] = _corner_radius(where, value)
        elif key == "opacity":
            props["opacity"] = float(value)
        elif key == "elevation":
            props["shadows"] = tokens.elevation_shadows(_token(where, "elevation", value, tokens.elevation))
        elif key in effects.EFFECT_FIELDS:
            props.update(_effects(where, {key: value}, only=key))
        elif key == "foreground":
            raise SpecBuildError(f"{where}: style.foreground has nothing to colour here (a box with no text); "
                                 "use style.background")
        else:
            raise SpecBuildError(f"{where}: unknown style field {key!r}" + _did_you_mean([key], STYLE_FIELDS))
    return props


def _paint(ctx: _Context, node_id: str, style: dict[str, Any], *, corner_radius: bool = True) -> dict[str, Any]:
    """The paint every kind shares: corner radius, opacity, border, and
    elevation as `shadows`."""
    paint: dict[str, Any] = {"opacity": float(style.get("opacity", 1.0))}
    if corner_radius:
        paint["corner_radius"] = _corner_radius(node_id, style.get("corner_radius", 0.0))
    paint["stroke_color"] = _fill(ctx, node_id, "border_color", style["border_color"]) if "border_color" in style else _TRANSPARENT
    paint["stroke_width"] = float(style.get("border_width", 0.0))
    level = _token(node_id, "elevation", style.get("elevation", 0.0), tokens.elevation)
    paint["shadows"] = tokens.elevation_shadows(level)
    paint.update(_effects(node_id, style))
    return paint


def _effects(node_id: str, style: dict[str, Any], only: str | None = None) -> dict[str, Any]:
    """`blur`, `backdrop_blur`, `blend_mode`, `filter`, `sticky` and `cursor` as node properties (`tesserae.spec.effects`)."""
    try:
        props = effects.effect_props(style, f"widget {_q(node_id)}: style")
    except ValueError as exc:
        raise SpecBuildError(str(exc)) from None
    if only is None:
        return props
    return {name: props[name] for name in {"filter": ("shader",), "cursor": ("cursor",)}.get(only, (only,))}


def _required_background(ctx: _Context, node: dict[str, Any], style: dict[str, Any], kind: str) -> RGBA:
    if "background" not in style:
        raise SpecBuildError(f'widget {_q(node["id"])}: {kind} requires style.background, none given')
    return _fill(ctx, node["id"], "background", style["background"])


def _required_foreground(ctx: _Context, node: dict[str, Any], style: dict[str, Any], kind: str) -> RGBA:
    if "background" in (node.get("style") or {}):
        raise SpecBuildError(
            f'widget {_q(node["id"])}: {kind} has no fill, so style.background doesn\'t apply -- its '
            "glyph/text color is style.foreground"
        )
    if "foreground" not in style:
        raise SpecBuildError(f'widget {_q(node["id"])}: {kind} requires style.foreground, none given')
    return _fill(ctx, node["id"], "foreground", style["foreground"])


#: What `text.text_align` can be: `tre`'s own values, where the text
#: sits in its node's width.
_TEXT_ALIGNS = ("start", "center", "end")
#: `text.wrap`: `word` breaks a line that is too long for its node; `none` never does.
_TEXT_WRAPS = ("word", "none")
#: `text.overflow`: what happens to a line that doesn't fit its node: `clip` cuts it off, `ellipsis` ends it with an ellipsis.
_TEXT_OVERFLOWS = ("clip", "ellipsis")

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
                                             for f in ("font_family", "font_weight", "font_size", "line_height", "tracking")})
    family = text.get("font_family") or (role_style.font_family if role_style else None)
    if family is None:
        raise SpecBuildError(f'widget {_q(node["id"])}: {kind} requires text.font_family (or text.typography_role), none given')
    size = text.get("font_size") if text.get("font_size") is not None else (role_style.font_size if role_style else None)
    if size is None:
        raise SpecBuildError(f'widget {_q(node["id"])}: {kind} requires text.font_size (or text.typography_role), none given')
    weight = text.get("font_weight") if text.get("font_weight") is not None else (role_style.font_weight if role_style else 400.0)
    line_height = text.get("line_height") if text.get("line_height") is not None else (role_style.line_height if role_style else None)
    align = text.get("text_align", "start")
    if align not in _TEXT_ALIGNS:
        raise SpecBuildError(
            f'widget {_q(node["id"])}: text.text_align must be one of {", ".join(_TEXT_ALIGNS)}, got {align!r}'
        )
    wrap = text.get("wrap", "word")
    if wrap not in _TEXT_WRAPS:
        raise SpecBuildError(f'widget {_q(node["id"])}: text.wrap must be one of {", ".join(_TEXT_WRAPS)}, got {wrap!r}')
    overflow = text.get("overflow", "clip")
    if overflow not in _TEXT_OVERFLOWS:
        raise SpecBuildError(
            f'widget {_q(node["id"])}: text.overflow must be one of {", ".join(_TEXT_OVERFLOWS)}, got {overflow!r}'
        )
    content = text.get("content", "")
    if not isinstance(content, str):
        raise SpecBuildError(
            f'widget {_q(node["id"])}: text.content must be a string, got {type(content).__name__} {content!r}'
        )
    props = {
        "text": content,
        "font_family": family,
        "font_size": float(size),
        "font_weight": float(weight),
        "line_height": line_height,
        "text_align": align,
        "wrap": wrap,
        "overflow": overflow,
        "spans": [],
        "selectable": False,
        "letter_spacing": role_style.tracking if role_style is not None else 0.0,
        "max_lines": None,
    }
    spacing = text.get("letter_spacing")
    if spacing is not None:
        if isinstance(spacing, bool) or not isinstance(spacing, (int, float)):
            raise SpecBuildError(f'widget {_q(node["id"])}: text.letter_spacing is a number of pixels, got {spacing!r}')
        props["letter_spacing"] = float(spacing)
    lines = text.get("max_lines")
    if lines is not None:
        if isinstance(lines, bool) or not isinstance(lines, int) or lines < 1:
            raise SpecBuildError(f'widget {_q(node["id"])}: text.max_lines is a whole number from 1, got {lines!r}')
        props["max_lines"] = lines
    if "selectable" in text:
        if not isinstance(text["selectable"], bool):
            raise SpecBuildError(f'widget {_q(node["id"])}: text.selectable must be true or false, got {text["selectable"]!r}')
        if text["selectable"] and kind != "Text":
            raise SpecBuildError(f'widget {_q(node["id"])}: only a Text can be selectable (a {kind} is pressed, not selected)')
        props["selectable"] = text["selectable"]
    if "runs" in text:
        if kind != "Text":
            raise SpecBuildError(f'widget {_q(node["id"])}: only a Text has text.runs (a {kind}\'s text is one piece)')
        if content:
            raise SpecBuildError(f'widget {_q(node["id"])}: text.runs is the text, so there is no text.content with it')
        try:
            props["text"], props["spans"], props["_pieces"] = richtext.build(
                text["runs"], f'widget {_q(node["id"])}', lambda c: _color(ctx, node["id"], "text.runs", c),
                _role(ctx, "primary"))
        except ValueError as exc:
            raise SpecBuildError(str(exc)) from None
    return props


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
        _fill(ctx, node["id"], "background", style["background"]) if "background" in style else _TRANSPARENT
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
    """A ScrollView is `tre`'s `scroll_view` holding one content box,
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
    virtual = node.get("virtual")
    if isinstance(virtual, dict):  # the content is as tall as the whole list; the rows that are built are placed in it
        content["height"] = float(virtual["count"]) * float(virtual["extent"])
    scroll = node.get("scroll")
    horizontal = isinstance(scroll, dict) and scroll.get("orientation") == "horizontal"
    outer["orientation"] = "horizontal" if horizontal else "vertical"
    if isinstance(scroll, dict) and scroll.get("offset") is not None:
        offset = scroll["offset"]
        if isinstance(offset, bool) or not isinstance(offset, (int, float)) or offset != offset or offset < 0:
            raise SpecBuildError(f'widget {_q(node["id"])}: scroll_offset is a distance in pixels, 0 or more, not {offset!r}')
        outer["scroll_offset"] = float(offset)
    # the content fills the cross axis and is as long as its children along the scrolling one
    fill = {"height": "100%"} if horizontal else {"width": "100%"}
    content.update(flex_direction=style.get("flex_direction", "horizontal" if horizontal else "vertical"), **fill,
                   **{k: style.get(k, _ALIGNMENT_DEFAULTS[k]) for k in _ALIGNMENT_DEFAULTS})
    return outer, content


def _overlay_props(ctx, node, style):
    """An Overlay is two nodes: a placeholder that takes no room where it is written, and the layer, which is the box its children are in and
    which `ComposedView` shows over the window while it is open. A modal layer is the scrim: it fills the window (the renderer sizes it) and
    centres its children unless the style places them."""
    modal = bool((node.get("overlay") or {}).get("modal"))
    if modal and "align_items" not in style and "justify_content" not in style:
        style = {**style, "align_items": "center", "justify_content": "center"}
    layer, _ = _box_props(ctx, node, style)
    if modal:
        layer["fill"] = _color(ctx, node["id"], "scrim", "scrim@32%") if "background" not in style else layer["fill"]
    placeholder = {"width": 0.0, "height": 0.0, "position": "absolute", "x": 0.0, "y": 0.0, "hit_testable": False, "a11y_hidden": True}
    return placeholder, layer


def natural_size(window: Any, props: dict[str, Any], style: dict[str, Any]) -> dict[str, float]:
    """A Text or Link's measured `width`/`height` for whichever its style
    leaves out: `tre` 0.3.4's text has no intrinsic size, so text
    without one was 0 px wide -- every fragment's label was invisible."""
    missing = [d for d in ("width", "height") if style.get(d) is None]
    if not missing:
        return {}
    if "_pieces" in props:  # rich text: each run in its own weight and size
        width, height = richtext.measure(window, props["_pieces"], props)
    else:
        fixed = style.get("width")  # a text with a width and no height is as tall as its lines wrap to (and `max_lines` allows)
        wrapped = {"max_width": float(fixed), "wrap": props.get("wrap", "word"), "overflow": props.get("overflow", "clip")} \
            if isinstance(fixed, (int, float)) and not isinstance(fixed, bool) else {}
        width, height = window.measure_text(props["text"], font_family=props["font_family"],
                                            font_size=props["font_size"], font_weight=props["font_weight"],
                                            line_height=props.get("line_height"), letter_spacing=props.get("letter_spacing", 0.0),
                                            max_lines=props.get("max_lines"), **wrapped)
    # Whole pixels, rounded up: the engine rounds an explicit width down, and text a fraction of a pixel
    # wider than its node wraps ("Add a / task").
    return {d: float(math.ceil(v)) for d, v in (("width", width), ("height", height)) if d in missing}


def _text_props(ctx, node, style):
    fill = _required_foreground(ctx, node, style, node["kind"])
    props = {**_layout(style), **_paint(ctx, node["id"], style), **_text_style(ctx, node, node["kind"]), "fill": fill}
    props.update(natural_size(ctx.window, props, style))
    props.pop("_pieces", None)
    if node["kind"] == "Text" and style.get("width") is None and (props["text_align"] != "start" or style.get("_fill_x")):
        # The engine aligns text within the width it is laid out in, so a centred or right aligned Text with no
        # width fills its parent's, and keeps its own as the least (a parent with no width yet gives 100% nothing).
        props["min_width"] = max(props["width"], float(style.get("min_width") or 0.0))
        props["width"] = "100%"
    return props, None


_PLACED = ("scale", "translate_x", "translate_y", "rotation_deg", "margin_top", "margin_right", "margin_bottom", "margin_left", "flex_grow", "flex_shrink", "flex_basis",
           "align_self", "position", "x", "y", "z_index", "min_width", "max_width", "min_height", "max_height",
           "aspect_ratio", "grid_column", "grid_row", "justify_self")


def _link_props(ctx, node, style):
    """A Link is a box holding its text: `tre` 0.3.4's `text` never
    gets pointer events, so a Link that was a bare `text` could only be
    clicked from the keyboard. The box takes the events, focus, role and
    label (the text's content); the text is only drawn."""
    text, _ = _text_props(ctx, node, style)
    layout = _layout(style)
    outer = {k: v for k, v in layout.items() if k in _PLACED or k in ("width", "height")}
    cursor = text.pop("cursor", None)  # the hit-testable box shows it, not the text
    outer.update(role="link", cursor="pointer" if cursor is None else cursor, focusable=True, label=text["text"])
    inner = {k: v for k, v in text.items() if k not in _PLACED}
    inner.update(hit_testable=False, a11y_hidden=True)
    return outer, inner


def _text_field_props(ctx, node, style):
    background = _required_background(ctx, node, style, "TextField")
    if "text_align" in node["text"]:
        raise SpecBuildError(f'widget {_q(node["id"])}: a TextField has no text.text_align (its text starts at the left)')
    for key in ("wrap", "overflow"):
        if key in node["text"]:
            raise SpecBuildError(f'widget {_q(node["id"])}: a TextField has no text.{key} (it is a single line that scrolls)')
    for key in ("max_lines", "letter_spacing"):
        if key in node["text"]:
            raise SpecBuildError(f'widget {_q(node["id"])}: a TextField has no text.{key} (the engine\'s input takes neither)')
    for key in ("runs", "selectable"):
        if key in node["text"]:
            raise SpecBuildError(f'widget {_q(node["id"])}: a TextField has no text.{key} (what is typed is one style)')
    text = _text_style(ctx, node, "TextField")
    text.pop("line_height")
    text.pop("text_align")
    text.pop("wrap")
    text.pop("overflow")
    text.pop("spans")
    text.pop("selectable")
    text.pop("letter_spacing")
    text.pop("max_lines")
    outer = {**_layout(style), **_paint(ctx, node["id"], style), "fill": background}
    # What is typed is the theme's `on_surface` (or the style's `foreground`), and the caret its `primary`, so a
    # dark scheme's field is light on dark: the engine's own default is the light scheme's dark ink.
    ink = _fill(ctx, node["id"], "foreground", style["foreground"]) if "foreground" in style else _role(ctx, "on_surface")
    inner = {**text, "fill": ink, "caret_color": _role(ctx, "primary"), "flex_grow": 1.0, "align_self": "stretch", "role": "textbox", "focusable": True}
    given = node["text"]
    for key in ("multiline", "obscured"):
        if key in given:
            if not isinstance(given[key], bool):
                raise SpecBuildError(f'widget {_q(node["id"])}: text.{key} is true or false, got {given[key]!r}')
            inner[key] = given[key]
    if given.get("placeholder"):
        if not isinstance(given["placeholder"], str):
            raise SpecBuildError(f'widget {_q(node["id"])}: text.placeholder is text, got {given["placeholder"]!r}')
        inner["placeholder"] = given["placeholder"]
        inner["placeholder_fill"] = _role(ctx, "on_surface_variant")
    if given.get("multiline"):  # a field of several lines grows from the top, not the middle
        inner["align_self"] = "stretch"
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


def _svg_props(ctx, node, style):
    svg = node.get("svg")
    if not isinstance(svg, dict) or "content" not in svg:
        raise SpecBuildError(f'widget {_q(node["id"])}: Svg requires svg: {{src: file.svg}} (or content:), none given')
    props = {**_layout(style), **_paint(ctx, node["id"], style), "svg": svg["content"],
             "svg_images": dict(svg.get("images") or {}),
             "fill": _color(ctx, node["id"], "background", style["background"]) if "background" in style else _TRANSPARENT}
    if "foreground" in style:  # what `currentColor` is: a monochrome icon follows the theme
        props["svg_color"] = _color(ctx, node["id"], "foreground", style["foreground"])
    return props, None


def _canvas_props(ctx, node, style):
    canvas = node.get("canvas")
    draw = canvas.get("draw") if isinstance(canvas, dict) else None
    commands = canvas_plan(draw, lambda raw: _color(ctx, node["id"], "color", raw))
    return {**_layout(style), **_paint(ctx, node["id"], style), "draw": canvas_painter(commands)}, None


def _icon_props(ctx, node, style):
    icon = node.get("icon")
    if not isinstance(icon, dict) or ("name" in icon) == ("path" in icon):
        raise SpecBuildError(f'widget {_q(node["id"])}: Icon takes icon (a name) or path (SVG path data), one of them')
    if "path" in icon:
        data, view_box = icon["path"], _view_box(node["id"], icon.get("view_box"))
        if not isinstance(data, str) or not data.strip():
            raise SpecBuildError(f'widget {_q(node["id"])}: icon path is SVG path data, not {data!r}')
    else:
        data, view_box = icon_path(str(icon["name"])), icon_view_box(str(icon["name"]))
        if data is None:
            raise SpecBuildError(f'widget {_q(node["id"])}: unknown icon "{icon["name"]}"')
        if icon.get("view_box") is not None:
            view_box = _view_box(node["id"], icon["view_box"])
    tint = _required_foreground(ctx, node, style, "Icon")
    return {**_layout(style), **_paint(ctx, node["id"], style, corner_radius=False),
            "data": data, "view_box": view_box, "fill": tint}, None


def _view_box(node_id, raw):
    """An icon's `view_box`: four numbers, the width and height above 0. Material Symbols' own when not given."""
    if raw is None:
        return ICON_VIEW_BOX
    if (not isinstance(raw, (list, tuple)) or len(raw) != 4
            or any(isinstance(n, bool) or not isinstance(n, (int, float)) for n in raw) or raw[2] <= 0 or raw[3] <= 0):
        raise SpecBuildError(f"widget {_q(node_id)}: icon view_box is [min_x, min_y, width, height] with a width and height above 0, not {raw!r}")
    return tuple(float(n) for n in raw)


_PRIMITIVE = {
    "Rect": ("box", _box_props), "Container": ("box", _box_props), "Text": ("text", _text_props),
    "Link": ("box", _link_props), "TextField": ("box", _text_field_props), "Image": ("image", _image_props),
    "Svg": ("svg", _svg_props), "Overlay": ("box", _overlay_props), "Canvas": ("canvas", _canvas_props), "Icon": ("path", _icon_props), "ScrollView": ("scroll_view", _scroll_props),
}


def _a11y_for(node: dict[str, Any], kind: str, *, patching: bool) -> dict[str, Any]:
    props = _a11y_props(node, patching=patching)
    if kind == "Link" and props.get("label") is None:
        props.pop("label", None)  # a Link without a fixed `a11y:` label is named by its text (or its binding)
    return props


#: The node inside a two-node kind's box: what it's drawn with.
_INNER = {"TextField": "text_input", "Link": "text", "ScrollView": "box", "Overlay": "box"}


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
_A11Y_YAML = ("label", "role", "hidden", "live", "level", "expanded", "selected", "checked", "value", "value_min", "value_max", "value_step",
              *a11y.EXTRAS, *a11y.RELATIONS)
#: The states `a11y:` may set on a node that is not a control; a control kind sets its own (a Checkbox is checked or not by its state).
_A11Y_STATES = frozenset({"expanded", "selected", "checked", "value", "value_min", "value_max", "value_step"})
#: What each `a11y:` field resets to when a patch drops it.
_A11Y_RESET = {"label": None, "a11y_hidden": False, "live": None, "level": None, "expanded": None, "selected": None, "checked": None,
               "value": None, "value_min": None, "value_max": None, "value_step": None}
#: The `a11y:` fields a `{{ }}` binding may set (M47 Q2), and the
#: property each is; `role` and `live` stay fixed.
A11Y_BINDABLE = {"label": "label", "hidden": "a11y_hidden", "level": "level", "expanded": "expanded", "selected": "selected", "checked": "checked",
                 "value": "value", "value_min": "value_min", "value_max": "value_max", "value_step": "value_step", **{k: k for k in a11y.EXTRAS}}


def is_binding(value: Any) -> bool:
    """Whether an `a11y:` value is a `{{ }}` binding (M47 Q1)."""
    return isinstance(value, str) and "{{" in value


def a11y_bindings(node: dict[str, Any]) -> dict[str, str]:
    """The node's bound `a11y:` fields, `{field: "{{ expr }}"}` (the view wires them)."""
    value = node.get("a11y")
    return {k: v for k, v in value.items() if is_binding(v)} if isinstance(value, dict) else {}


def _a11y_fields(node: dict[str, Any]) -> dict[str, Any]:
    """The node's fixed `a11y:` fields, checked, as `tre` properties. A
    bound one is left to the view, and only its field is checked."""
    value = node.get("a11y")
    if value is None:
        return {}
    where = f"widget {_q(node['id'])}"
    if not isinstance(value, dict):
        raise SpecBuildError(f"{where}: `a11y:` takes a mapping of {', '.join(_A11Y_YAML)}, got {value!r}")
    unknown = set(value) - set(_A11Y_YAML)
    if unknown:
        raise SpecBuildError(f"{where}: unknown a11y field(s) {sorted(unknown)} (known: {', '.join(_A11Y_YAML)})"
                             + _did_you_mean(unknown, _A11Y_YAML))
    if "role" in value and node["kind"] in _OWN_ROLE:
        raise SpecBuildError(f"{where}: a {node['kind']} has its own role; `a11y:` can't set `role`")
    own = sorted(_A11Y_STATES & set(value)) if node["kind"] in _CONTROL_KINDS else []
    if own:
        raise SpecBuildError(f"{where}: a {node['kind']} sets its own {own[0]}; `a11y:` can't")
    bound = [k for k, v in value.items() if is_binding(v)]
    fixed_only = [k for k in bound if k not in A11Y_BINDABLE]
    if fixed_only:
        raise SpecBuildError(f"{where}: a11y {fixed_only[0]} can't be bound -- only "
                             f"{', '.join(A11Y_BINDABLE)} can follow a binding")
    try:
        checked = a11y.check({k: v for k, v in value.items() if k not in bound}, where)
    except ValueError as exc:
        raise SpecBuildError(str(exc)) from None
    # what tre may not have yet (and relations) are applied by the view, one at a time, not set with the rest
    return {k: v for k, v in checked.items() if k not in a11y.EXTRAS and k not in a11y.RELATIONS}


def _a11y_props(node: dict[str, Any], *, patching: bool) -> dict[str, Any]:
    """Accessibility properties for the node that carries them (a
    TextField's `text_input`, otherwise the node): the `a11y:` field, and
    a clickable node's focus and role. On a patch, dropped fields
    reset."""
    fields = _a11y_fields(node)
    bound = {A11Y_BINDABLE[k] for k in a11y_bindings(node)}  # the view sets these; a patch leaves them
    reset = {k: v for k, v in _A11Y_RESET.items() if k not in bound}
    if node["kind"] in _CONTROL_KINDS:  # a control keeps its own states (checked, selected, value): resetting them would undo what it just drew
        reset = {k: v for k, v in reset.items() if k not in _A11Y_STATES}
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
    """Whether `node` is focusable when it isn't disabled: a Link and
    a TextField are, a clickable node is (a Tab stop, M39), and otherwise
    it's what its `a11y:` says."""
    if node["kind"] in ("Link", "TextField"):
        return True
    return bool(_a11y_props(node, patching=True).get("focusable", False))


def interaction_tint(node: dict[str, Any], scheme: Optional[dict[str, RGBA]]) -> Optional[RGBA]:
    """The state layer and ripple's tint for `node`, or `None` for no
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


#: `window_region:` (0.3.0 M3): `drag` makes a node part of the window's
#: title bar -- a press on it (or on anything in it that isn't
#: interactive) moves the window -- and `none` keeps a node out of one.
WINDOW_REGIONS = ("drag", "none")


def _window_region(node: dict[str, Any], *, patching: bool) -> dict[str, Any]:
    """The node's `window_region` for `tre`; on a patch, a dropped one
    resets (`tre`'s default, `None`)."""
    value = node.get("window_region")
    if value is None:
        return {"window_region": None} if patching else {}
    if value not in WINDOW_REGIONS:
        raise SpecBuildError(f'widget {_q(node["id"])}: window_region is "drag" or "none", got {value!r}')
    return {"window_region": value}


def _create(ctx, node, style, built):
    kind = node["kind"]
    if kind in _WIDGET_KINDS:  # M60
        widget = _graph_widget(ctx, node, style)
        built.controls[node["id"]] = widget
        a11y_props = _a11y_props(node, patching=False)
        if a11y_props:
            widget.node.set(**a11y_props)
        if node.get("window_region") is not None:
            widget.node.set(**_window_region(node, patching=False))
        return widget.node, (widget.part("body") if kind == "GraphNode" else widget.node)
    if kind in _CONTROL_KINDS:
        control = _control(ctx, node, style, built)
        built.controls[node["id"]] = control
        a11y_props = _a11y_props(node, patching=False)  # its label, hidden, live, level (M47: they were dropped)
        if a11y_props:
            _a11y_target(control).set(**a11y_props)
        if node.get("window_region") is not None:
            control.node.set(**_window_region(node, patching=False))
        return control.node, control.node
    tre_kind, props_of = _PRIMITIVE[kind]
    outer_props, inner_props = props_of(ctx, node, style)
    # M39: as `tre`'s `set_on_click` did, a clickable node is a focusable
    # Tab stop that Enter and Space activate -- and a button.
    (inner_props if kind in ("TextField", "Overlay") else outer_props).update(_a11y_for(node, kind, patching=False))
    outer_props.update(_window_region(node, patching=False))
    outer = ctx.window.create(tre_kind, **outer_props)
    if inner_props is None:
        return outer, outer
    inner = ctx.window.create(_INNER[kind], **inner_props)
    if kind != "Overlay":  # an overlay's layer is shown over the window, not placed in the tree
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
    parent: tuple[str, str] = ("horizontal", "flex"),
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
    style = _engine(node["id"], resolve_style(node, layers), parent)
    kind = node["kind"]
    given = layout_keys(style)
    resets = _resets(style, before - given)
    try:
        if kind in _WIDGET_KINDS:
            if control is not None:
                _patch_graph_widget(ctx, node, control, state)
                control.node.set(**_window_region(node, patching=True))
            return given
        if kind in _CONTROL_KINDS:
            if control is not None:
                _patch_control(ctx, node, style, control, state, resets)
                _a11y_target(control).set(**_a11y_props(node, patching=True))
                control.node.set(**_window_region(node, patching=True))
            return given
        _, props_of = _PRIMITIVE[kind]
        outer_props, inner_props = props_of(ctx, node, style)
        (inner_props if kind in ("TextField", "Overlay") else outer_props).update(_a11y_for(node, kind, patching=True))
        outer_props.update(_window_region(node, patching=True))
        for key, value in resets.items():  # where `_layout` would have put it (a Link's text, a ScrollView's content)
            on_inner = (kind == "Link" and key not in _PLACED) or (kind == "ScrollView" and key in _CONTENT) or kind == "Overlay"
            (inner_props if on_inner else outer_props)[key] = value
        eased = _eased(window, transition.plan(node["id"], kind, style), ((outer, outer_props), (inner, inner_props)))
        outer.set(**{**_ALIGNMENT_DEFAULTS, **outer_props})  # the node's own alignment wins
        if kind == "Canvas":
            outer.redraw()  # the new commands replace what it shows
        if inner_props is not None:
            inner.set(**inner_props)
        for target, prop, value, ms, easing in eased:
            try:
                target.animate(prop, value, ms, easing)
            except ValueError as exc:
                if "animates to a number of pixels" not in str(exc):
                    raise
                target.set(**{prop: value})  # `auto` and a percentage cannot be eased to: the change is made at once
    except ValueError as exc:
        if isinstance(exc, SpecBuildError):
            raise
        raise SpecBuildError(f"widget {_q(node['id'])}: {exc}") from None
    return given


def _eased(window: Any, planned: dict[str, Any], targets: tuple[tuple[Any, Optional[dict[str, Any]]], ...]) -> list[tuple[Any, str, Any, int, Any]]:
    """The changes a patch should ease (`style.transition`): each property in `planned` that is about to change on a node leaves that node's
    props and comes back as `(node, property, value, milliseconds, easing)`, to be started once the rest is set. A change that would last
    no time, because the app is to reduce motion, is left in the props to be set."""
    if not planned:
        return []
    from tesserae import motion

    eased = []
    for target, props in targets:
        if props is None:
            continue
        for prop in [p for p in props if p in planned]:
            try:
                changing = target.get(prop) != props[prop]
            except ValueError:
                continue
            ms = motion.duration(window, planned[prop][0])
            if changing and ms > 0:
                eased.append((target, prop, props.pop(prop), ms, planned[prop][1]))
    return eased


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
    """The selected/active colour a control's style gives: `foreground` (the view language's) or, for the 0.4.x controls, `background` (the
    fragments' param); an indicator takes `foreground` only."""
    field = "foreground" if node["kind"] in _INDICATOR_KINDS or style.get("foreground") is not None else "background"
    raw = style.get(field)
    return None if raw is None else _color(ctx, node["id"], field, raw)


_INDICATOR_KINDS = frozenset({"CircularProgress", "LinearProgress", "LoadingIndicator"})


def _checked(node: dict[str, Any]) -> Optional[bool]:
    """A checkbox's state: on, off, or `None` (neither) when the node says `checked` and it is empty. A node that does not mention it is off."""
    if "checked" in node and node["checked"] is None:
        return None
    return bool(node.get("checked") or False)


def _progress_value(node: dict[str, Any]) -> Optional[float]:
    """A progress indicator's value: a number from 0 to 1, or `None` (indeterminate) when the node says `value` and it is empty. A node that does not
    mention `value` (the 0.4.x syntax) is a bar at 0."""
    if "value" in node and node["value"] is None:
        return None
    value = node.get("value")
    if isinstance(value, bool) or (value is not None and not isinstance(value, (int, float))):
        raise SpecBuildError(f'widget {_q(node["id"])}: value is a number from 0 to 1, or empty for a wait with no end, got {value!r}')
    return float(value or 0.0)


def _control(ctx: _Context, node: dict[str, Any], style: dict[str, Any], built: Built) -> Any:
    """The MD3 control for one of the eight control kinds."""
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
        value = _progress_value(node)
        common["track"] = node.get("track")
        if kind == "LinearProgress":
            control = controls.LinearProgress(ctx.window, value=value, width=size.get("width", 240.0),
                                              stop_indicator=bool(node.get("stop_indicator")), buffer=node.get("buffer"), **common)
            if "height" in size:
                control.node.set(height=size["height"])
                control.bar.set(height=size["height"])
        elif kind == "CircularProgress":
            control = controls.CircularProgress(ctx.window, value=value, size=size.get("width", 48.0), **common)
        else:
            control = controls.LoadingIndicator(ctx.window, size=size.get("width", 48.0), **common)
    else:
        common["listen"] = ctx.listen
        if kind == "Checkbox":
            control = controls.Checkbox(ctx.window, checked=_checked(node), error=bool(node.get("error")), **size, **common)
        elif kind == "RadioButton":
            radio_group = None
            if group is not None:
                radio_group = built.radio_groups.setdefault(group, controls.RadioGroup())
            control = controls.RadioButton(ctx.window, selected=bool(node.get("selected") or False),
                                           group=radio_group, error=bool(node.get("error")), **size, **common)
        elif kind == "Switch":
            control = controls.Switch(ctx.window, selected=bool(node.get("selected") or False), icons=bool(node.get("icons")), **size, **common)
        elif kind == "Slider":
            control = controls.Slider(ctx.window, value=float(node.get("value") or 0.0), min=float(node.get("min") or 0.0),
                                      max=1.0 if node.get("max") is None else float(node["max"]), step=node.get("step"),
                                      ticks=bool(node.get("ticks")), value_indicator=bool(node.get("value_indicator")), **size, **common)
        elif kind == "SpinBox":  # M58: two buttons and a field, sized by MD3, not `width`/`height`
            common.pop("color")
            control = controls.SpinBox(ctx.window, value=_spin_number(node.get("value") or 0, node.get("step") or 1),
                                       min=node.get("min"), max=node.get("max"), step=node.get("step") or 1,
                                       **(node.get("spin") or {}), **common)
        else:  # TimePickerDial
            common.pop("color")
            control = controls.TimePickerDial(ctx.window, hour=int(node.get("hour") or 0),
                                              minute=int(node.get("minute") or 0), size=size.get("width", 256.0),
                                              mode=(node.get("dial") or {}).get("mode") or "hour", auto_advance=(node.get("dial") or {}).get("auto_advance") is not False,
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
    the NodeGraph being built. Both take their size from `style`."""
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
    GraphNodes' ids), replacing any it had."""
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
    text input, else the control's node."""
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
    if hasattr(control, "disabled"):  # a progress indicator is never disabled
        control.disabled.set(bool(node.get("disabled") or False))  # M70
    if kind == "Checkbox":
        control.checked.set(_checked(node))
        control.error.set(bool(node.get("error")))
    elif kind in ("Switch", "RadioButton"):
        control.selected.set(bool(node.get("selected") or False))
        if kind == "RadioButton":
            control.error.set(bool(node.get("error")))
    elif kind in ("CircularProgress", "LinearProgress"):
        control.value.set(_progress_value(node))
        if kind == "LinearProgress":
            control.buffer.set(node.get("buffer"))
    elif kind == "Slider":
        control.value.set(float(node.get("value") or 0.0))
    elif kind == "SpinBox":
        control.value.set(control._fit(_spin_number(node.get("value") or 0, control.step)))
    elif kind == "TimePickerDial":
        control.hour.set(int(node.get("hour") or 0) % 24)
        control.minute.set(int(node.get("minute") or 0) % 60)
        if (node.get("dial") or {}).get("mode") in ("hour", "minute"):
            control.mode.set(node["dial"]["mode"])


def control_shape(node: dict[str, Any], layers: tuple[Optional[Sheet], ...]) -> tuple[Any, ...]:
    """What a control is built at (its kind and size): when it changes,
    the reconciler rebuilds the control rather than patching it."""
    style = resolve_style(node, layers)
    return (node.get("kind"), style.get("width"), style.get("height"), node.get("group"),
            node.get("min"), node.get("max"), node.get("step"), repr(node.get("spin")), node.get("track"), node.get("stop_indicator"), node.get("icons"), node.get("ticks"), node.get("value_indicator"))  # a SpinBox's bounds are built in (M58)
