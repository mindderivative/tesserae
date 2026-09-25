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
| `Checkbox`, `RadioButton`, `Switch`, `Slider`, `CircularProgress`, `LinearProgress`, `LoadingIndicator`, `TimePickerDial` | **for now**, `tre`'s legacy window factories (`add_checkbox`, ...), moved into the tree. Tesserae's own controls replace them in M40; they're the one use of `tre`'s old API here, and `TRE_FORBID_REMOVED` (M43) catches any left |

Styles resolve through `tesserae.spec.cascade`; theme roles, shape
tokens, elevation levels and type roles through `tesserae.tokens`. Errors
use `tre`'s wording. Bindings, handlers and `two_way:` aren't wired here
(M37 Phase 4).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from tesserae import tokens
from tesserae.icons import ICON_VIEW_BOX, icon_path
from tesserae.spec.cascade import STYLE_FIELDS, Sheet, resolve_style

__all__ = ["Built", "SpecBuildError", "build"]

RGBA = tuple[int, int, int, int]
_TRANSPARENT: RGBA = (0, 0, 0, 0)
#: `tre`'s MD3 baseline tints for the legacy kinds when there's no theme.
_BASELINE = {
    "primary": (0x67, 0x50, 0xA4, 0xFF), "on_primary": (0xFF, 0xFF, 0xFF, 0xFF),
    "outline": (0x79, 0x74, 0x7E, 0xFF), "surface_container_highest": (0xE6, 0xE0, 0xE9, 0xFF),
}
_LEGACY_KINDS = frozenset({
    "Checkbox", "RadioButton", "Switch", "Slider", "CircularProgress", "LinearProgress",
    "LoadingIndicator", "TimePickerDial",
})
_KINDS = _LEGACY_KINDS | {"Rect", "Container", "Text", "Link", "TextField", "Image", "Icon"}
_NODE_KEYS = frozenset({
    "id", "kind", "classes", "style", "text", "checked", "selected", "value", "hour", "minute",
    "image", "icon", "bindings", "handlers", "two_way", "children",
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


@dataclass
class _Context:
    window: Any
    layers: tuple[Optional[Sheet], ...]
    scheme: Optional[dict[str, RGBA]]
    frames: dict[str, tuple[bytes, int, int]]


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
    ctx = _Context(
        window,
        (Sheet.of(default_theme), Sheet.of(custom_theme), Sheet.of(stylesheet)),
        scheme,
        frames or {},
    )
    built = Built(root=None)
    built.root = _build(ctx, spec, built)
    return built


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
    unknown_style = set(style) - STYLE_FIELDS
    if unknown_style:
        raise SpecBuildError(f"widget {_q(node_id)}: unknown style field(s) {sorted(unknown_style)}")

    outer, inner = _KIND_BUILDERS[kind](ctx, node, style)
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


def _text_style(node: dict[str, Any], kind: str) -> dict[str, Any]:
    text = node.get("text")
    if not isinstance(text, dict):
        raise SpecBuildError(f'widget {_q(node["id"])}: {kind} requires text, none given')
    role = text.get("typography_role")
    role_style = None
    if role is not None:
        role_style = tokens.type_style(role)
        if role_style is None:
            raise SpecBuildError(f'widget {_q(node["id"])}: unknown text.typography_role "{role}"')
    family = text.get("font_family") or (role_style.font_family if role_style else None)
    if family is None:
        raise SpecBuildError(f'widget {_q(node["id"])}: {kind} requires text.font_family (or text.typography_role), none given')
    size = text.get("font_size") if text.get("font_size") is not None else (role_style.font_size if role_style else None)
    if size is None:
        raise SpecBuildError(f'widget {_q(node["id"])}: {kind} requires text.font_size (or text.typography_role), none given')
    weight = text.get("font_weight") if text.get("font_weight") is not None else (role_style.font_weight if role_style else 400.0)
    line_height = text.get("line_height") if text.get("line_height") is not None else (role_style.line_height if role_style else None)
    return {
        "text": str(text.get("content", "")),
        "font_family": family,
        "font_size": float(size),
        "font_weight": float(weight),
        "line_height": line_height,
    }


def _check_state(node: dict[str, Any], kind: str, expected: str, given: str) -> None:
    if node.get(given) is not None:
        raise SpecBuildError(f'widget {_q(node["id"])}: {kind} takes `{expected}:`, not `{given}:`')


# -- kinds ----------------------------------------------------------------------------------


def _box(ctx, node, style):
    kind = node["kind"]
    fill = _required_background(ctx, node, style, "Rect") if kind == "Rect" else (
        _color(ctx, node["id"], "background", style["background"]) if "background" in style else _TRANSPARENT
    )
    n = ctx.window.create("box", **_layout(style), **_paint(ctx, node["id"], style), fill=fill)
    return n, n


def _text(ctx, node, style):
    fill = _required_foreground(ctx, node, style, node["kind"])
    props = {**_layout(style), **_paint(ctx, node["id"], style), **_text_style(node, node["kind"]), "fill": fill}
    if node["kind"] == "Link":
        props.update(role="link", cursor="pointer", focusable=True)
    n = ctx.window.create("text", **props)
    return n, n


def _text_field(ctx, node, style):
    background = _required_background(ctx, node, style, "TextField")
    text = _text_style(node, "TextField")
    text.pop("line_height")
    outer = ctx.window.create("box", **_layout(style), **_paint(ctx, node["id"], style), fill=background)
    inner = ctx.window.create("text_input", **text, flex_grow=1.0, align_self="stretch", role="textbox", focusable=True)
    outer.add_child(inner)
    return outer, inner


def _image(ctx, node, style):
    image = node.get("image")
    if not isinstance(image, dict):
        raise SpecBuildError(f'widget {_q(node["id"])}: Image requires image, none given')
    rgba, width, height = ctx.frames.get(node["id"], (bytes(4), 1, 1))
    n = ctx.window.create(
        "image", **_layout(style), **_paint(ctx, node["id"], style),
        rgba=rgba, pixel_width=width, pixel_height=height, fit=str(image.get("fit", "cover")).lower(),
    )
    return n, n


def _icon(ctx, node, style):
    icon = node.get("icon")
    if not isinstance(icon, dict):
        raise SpecBuildError(f'widget {_q(node["id"])}: Icon requires icon, none given')
    data = icon_path(str(icon.get("name")))
    if data is None:
        raise SpecBuildError(f'widget {_q(node["id"])}: unknown icon "{icon.get("name")}"')
    tint = _required_foreground(ctx, node, style, "Icon")
    n = ctx.window.create(
        "path", **_layout(style), **_paint(ctx, node["id"], style, corner_radius=False),
        data=data, view_box=ICON_VIEW_BOX, fill=tint,
    )
    return n, n


def _role(ctx, name):
    return (ctx.scheme or {}).get(name, _BASELINE[name])


def _legacy(ctx, node, style):
    """The eight MD3 kinds `tre` still draws itself, until M40: built with
    its legacy factories, then given the node's layout."""
    w, kind, node_id = ctx.window, node["kind"], node["id"]
    width, height = style.get("width"), style.get("height")
    if kind == "Checkbox":
        _check_state(node, "Checkbox", "checked", "selected")
        n = w.add_checkbox(_required_background(ctx, node, style, "Checkbox"), width or 18.0, height or 18.0,
                           checked=bool(node.get("checked") or False))
    elif kind == "Slider":
        n = w.add_slider(_required_background(ctx, node, style, "Slider"), width or 200.0, height or 40.0,
                         value=float(node.get("value") or 0.0))
    elif kind == "RadioButton":
        _check_state(node, "RadioButton", "selected", "checked")
        n = w.add_radio_button(size=width or 20.0, selected=bool(node.get("selected") or False))
    elif kind == "Switch":
        _check_state(node, "Switch", "selected", "checked")
        n = w.add_switch(width=width or 52.0, height=height or 32.0, selected=bool(node.get("selected") or False))
    elif kind == "CircularProgress":
        n = w.add_circular_progress(size=width or 48.0, value=float(node.get("value") or 0.0))
    elif kind == "LinearProgress":
        n = w.add_linear_progress(width or 200.0, height=height or 4.0, value=float(node.get("value") or 0.0))
    elif kind == "LoadingIndicator":
        if width is None or height is None:
            missing = "style.width" if width is None else "style.height"
            raise SpecBuildError(f'widget {_q(node_id)}: LoadingIndicator requires {missing}, none given')
        n = w.add_loading_indicator(size=width, foreground=_required_foreground(ctx, node, style, "LoadingIndicator"))
    else:  # TimePickerDial
        n = w.add_time_picker_dial(hour=int(node.get("hour") or 0), minute=int(node.get("minute") or 0), size=width or 256.0)
    n.remove()  # the factories attach to the window's root; the caller places it
    n.set(**_layout(style), opacity=float(style.get("opacity", 1.0)))
    return n, n


_KIND_BUILDERS: dict[str, Callable[..., tuple[Any, Any]]] = {
    "Rect": _box, "Container": _box, "Text": _text, "Link": _text, "TextField": _text_field,
    "Image": _image, "Icon": _icon, **{kind: _legacy for kind in _LEGACY_KINDS},
}
