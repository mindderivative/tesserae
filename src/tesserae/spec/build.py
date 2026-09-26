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
    "Built", "Layers", "SpecBuildError", "build", "control_shape", "focus_ring_color", "interaction_tint", "patch",
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
    "Checkbox", "RadioButton", "Switch", "Slider", "CircularProgress", "LinearProgress",
    "LoadingIndicator", "TimePickerDial",
})
_KINDS = _CONTROL_KINDS | {"Rect", "Container", "Text", "Link", "TextField", "Image", "Icon"}
_NODE_KEYS = frozenset({
    "id", "kind", "classes", "style", "text", "checked", "selected", "value", "hour", "minute",
    "image", "icon", "bindings", "handlers", "two_way", "interaction", "a11y", "group", "children",
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


@dataclass
class _Context:
    window: Any
    layers: tuple[Optional[Sheet], ...]
    scheme: Optional[dict[str, RGBA]]
    frames: dict[str, tuple[bytes, int, int]]
    #: The shared listener registrar controls use (a View's; otherwise their own).
    listen: Optional[Callable[..., Any]] = None


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


def prepare_layers(
    default_theme: Optional[dict[str, Any]],
    custom_theme: Optional[dict[str, Any]],
    stylesheet: Optional[dict[str, Any]],
) -> Layers:
    """The cascade's three layers, prepared once (`default_theme` defaults
    to `tre`'s shipped one), with the themes' typography overrides: a
    custom theme's role entry replaces the default theme's."""
    from tesserae.theme import _type_override

    if default_theme is None:
        default_theme = shipped_default_theme()
    layers = Layers((Sheet.of(default_theme), Sheet.of(custom_theme), Sheet.of(stylesheet)))
    layers.typography = {}
    for theme in (default_theme, custom_theme):
        for role, raw in ((theme or {}).get("typography") or {}).items():
            layers.typography[role] = _type_override(role, raw)
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
) -> Any:
    """Builds `spec` with already-prepared layers, recording its nodes in
    `into` (a new `Built` if none); returns the subtree's outer root.
    `listen` is the listener registrar the controls share with the view."""
    ctx = _Context(window, layers, scheme, frames or {}, listen)
    built = into if into is not None else Built(root=None)
    return _build(ctx, spec, built)


_shipped: Optional[dict[str, Any]] = None


def shipped_default_theme() -> dict[str, Any]:
    """`tre`'s shipped default theme (Tesserae's copy)."""
    global _shipped
    if _shipped is None:
        from pathlib import Path

        import yaml

        _shipped = yaml.safe_load((Path(__file__).parent / "default_theme.yaml").read_text())
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

    outer, inner = _create(ctx, node, style, built)
    built.nodes[node_id] = inner
    built.outer[node_id] = outer
    built.specs[node_id] = node
    for child in node.get("children") or []:
        outer.add_child(_build(ctx, child, built))
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


def _text_props(ctx, node, style):
    fill = _required_foreground(ctx, node, style, node["kind"])
    props = {**_layout(style), **_paint(ctx, node["id"], style), **_text_style(ctx, node, node["kind"]), "fill": fill}
    if node["kind"] == "Link":
        props.update(role="link", cursor="pointer", focusable=True)
    return props, None


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
    "Link": ("text", _text_props), "TextField": ("box", _text_field_props), "Image": ("image", _image_props),
    "Icon": ("path", _icon_props),
}


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


def _a11y_fields(node: dict[str, Any]) -> dict[str, Any]:
    """The node's `a11y:` field, checked, as `tre` properties."""
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
    try:
        return a11y.check(value, where)
    except ValueError as exc:
        raise SpecBuildError(str(exc)) from None


def _a11y_props(node: dict[str, Any], *, patching: bool) -> dict[str, Any]:
    """Accessibility properties for the node that carries them (a
    TextField's `text_input`, otherwise the node): the `a11y:` field, and
    a clickable node's focus and role (M39). On a patch, dropped fields
    reset."""
    fields = _a11y_fields(node)
    props = {**_A11Y_RESET, **{k: v for k, v in fields.items() if k != "role"}} if patching else {
        k: v for k, v in fields.items() if k != "role"}
    if node["kind"] not in _OWN_ROLE:
        if _clickable(node):
            props.update(focusable=True, role=fields.get("role", "button"))
        elif "role" in fields or patching:
            props["role"] = fields.get("role", "none")
            if patching:
                props["focusable"] = False
    return props


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
    if kind in _CONTROL_KINDS:
        control = _control(ctx, node, style, built)
        built.controls[node["id"]] = control
        return control.node, control.node
    tre_kind, props_of = _PRIMITIVE[kind]
    outer_props, inner_props = props_of(ctx, node, style)
    # M39: as `tre`'s `set_on_click` did, a clickable node is a focusable
    # Tab stop that Enter and Space activate -- and a button.
    (outer_props if inner_props is None else inner_props).update(_a11y_props(node, patching=False))
    outer = ctx.window.create(tre_kind, **outer_props)
    if inner_props is None:
        return outer, outer
    inner = ctx.window.create("text_input", **inner_props)
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
) -> None:
    """Sets `node`'s properties on its existing nodes, in place -- what
    `tre`'s `patch_node` does. The node keeps its identity, focus and
    running animations. Children aren't touched.

    For a control kind, `control` is its control: it's re-themed, and its
    state set from the spec unless `state=False` (a theme or stylesheet
    change, which leaves what the user did)."""
    ctx = _Context(window, layers, scheme, frames or {})
    style = resolve_style(node, layers)
    kind = node["kind"]
    if kind in _CONTROL_KINDS:
        if control is not None:
            _patch_control(ctx, node, style, control, state)
        return
    _, props_of = _PRIMITIVE[kind]
    outer_props, inner_props = props_of(ctx, node, style)
    (outer_props if inner_props is None else inner_props).update(_a11y_props(node, patching=True))
    outer.set(**_ALIGNMENT_DEFAULTS, **outer_props)
    if inner_props is not None:
        inner.set(**inner_props)


def _role(ctx, name):
    return (ctx.scheme or {}).get(name, _BASELINE[name])


#: Layout a control's node takes from its style: where it sits, not its
#: size (a control is built at its size) or its own content alignment.
_PLACEMENT = frozenset({
    "margin_top", "margin_right", "margin_bottom", "margin_left", "flex_grow", "flex_shrink", "flex_basis",
    "align_self", "position", "x", "y",
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
        else:  # TimePickerDial
            common.pop("color")
            control = controls.TimePickerDial(ctx.window, hour=int(node.get("hour") or 0),
                                              minute=int(node.get("minute") or 0), size=size.get("width", 256.0),
                                              **common)
    placement = {k: v for k, v in _layout(style).items() if k in _PLACEMENT}
    if placement:
        control.node.set(**placement)
    return control


def _patch_control(ctx: _Context, node: dict[str, Any], style: dict[str, Any], control: Any, state: bool) -> None:
    control.node.set(**{**_PLACEMENT_RESET, **{k: v for k, v in _layout(style).items() if k in _PLACEMENT}})
    control._color = _control_colour(ctx, node, style)
    control.set_theme(_theme(ctx))
    if not state:
        return
    kind = node["kind"]
    if kind == "Checkbox":
        control.checked.set(bool(node.get("checked") or False))
    elif kind in ("Switch", "RadioButton"):
        control.selected.set(bool(node.get("selected") or False))
    elif kind in ("Slider", "CircularProgress", "LinearProgress"):
        control.value.set(float(node.get("value") or 0.0))
    elif kind == "TimePickerDial":
        control.hour.set(int(node.get("hour") or 0) % 24)
        control.minute.set(int(node.get("minute") or 0) % 60)


def control_shape(node: dict[str, Any], layers: tuple[Optional[Sheet], ...]) -> tuple[Any, ...]:
    """What a control is built at (its kind and size): when it changes,
    the reconciler rebuilds the control rather than patching it."""
    style = resolve_style(node, layers)
    return node.get("kind"), style.get("width"), style.get("height"), node.get("group")
