"""The widget registry: what a node's `widget:` can name, and the properties it takes (spec section 3, phase 3 of #209).

A widget has a name, **properties** (`Property`: a type, a default, `choices`, `required`, `model`), the style `extras` it accepts and the
`parts` a stylesheet can address. Built-in widgets are declared with `@widget` (or `declare`); a view with `params:` becomes a declaration with
`decl_from_params`, so the loader, the schema generator and the editor treat both alike.

`Property.coerce` checks a literal against its type and returns the value to keep; a `{{ }}` expression is checked later, when it is
evaluated, and passes through here.
"""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Optional

__all__ = [
    "PROPERTY_TYPES", "RESERVED_KEYS", "Property", "PropertyError", "WidgetDecl", "declare", "decl_from_params", "is_expression", "json_schema", "lookup",
    "names", "register_widget", "style_fields_of", "unregister_widget", "widget",
]

PROPERTY_TYPES = ("str", "int", "float", "bool", "color", "length", "icon", "enum", "list", "dict", "node", "nodes", "handler", "any")

#: Keys every node has (spec section 2) and the header keys: a property may not use one of these names.
RESERVED_KEYS = frozenset({
    "widget", "name", "if", "for", "key", "slot", "state", "style", "classes", "handlers", "a11y", "interaction", "window_region",
    "route", "focus_group", "children", "params", "expects",
})

def _style_fields() -> frozenset[str]:
    from tesserae.spec.cascade import STYLE_FIELDS
    from tesserae.spec.layout import LAYOUT_FIELDS, REPLACED

    return (frozenset(STYLE_FIELDS) | frozenset(LAYOUT_FIELDS) | frozenset(REPLACED)) - {"foreground"}


_HEX_COLOR = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")
_ROLE_OR_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
_LENGTH = re.compile(r"^(?:auto|\d+(?:\.\d+)?%)$")
_ICON = re.compile(r"^[a-z][a-z0-9_]*$")


class PropertyError(ValueError):
    """A property value that does not fit its declaration."""

    def __init__(self, message: str, hint: Optional[str] = None) -> None:
        super().__init__(message)
        self.message = message
        self.hint = hint


def is_expression(value: Any) -> bool:
    return isinstance(value, str) and "{{" in value


def _near(text: str, options: Iterable[str]) -> Optional[str]:
    close = difflib.get_close_matches(text, list(options), n=3)
    return ("did you mean " + " or ".join(f"'{c}'" for c in close)) if close else None


@dataclass
class Property:
    """One property of a widget. `default` is the value when the property is not given; `required` makes omitting it an error."""

    type: str = "any"
    default: Any = None
    choices: Optional[tuple[Any, ...]] = None
    required: bool = False
    model: bool = False
    doc: str = ""
    name: str = field(default="", compare=False)

    def __post_init__(self) -> None:
        if isinstance(self.type, type):
            self.type = self.type.__name__
        if self.type not in PROPERTY_TYPES:
            raise ValueError(f"property type {self.type!r} is not one of {', '.join(PROPERTY_TYPES)}")
        if self.type == "enum" and not self.choices:
            raise ValueError("an enum property needs choices")
        if self.choices is not None:
            self.choices = tuple(self.choices)
        if self.type == "bool" and self.default is None and not self.required:
            self.default = False

    def __set_name__(self, owner: type, name: str) -> None:
        self.name = name

    def coerce(self, value: Any) -> Any:
        """The value to keep for `value`, or a `PropertyError`. An expression, `None` for an optional property and the structural
        types (`node`, `nodes`, checked by the loader) pass."""
        if is_expression(value) or self.type in ("node", "nodes"):
            return value
        if value is None:
            if self.required:
                raise PropertyError(f"'{self.name}' needs a value")
            return None
        result = _COERCE[self.type](self, value)
        if self.choices is not None and result not in self.choices:
            raise PropertyError(f"'{self.name}' is {value!r}, which is not one of: {', '.join(map(str, self.choices))}",
                                _near(str(result), [str(c) for c in self.choices]))
        return result


def _bad(prop: Property, value: Any, wanted: str) -> PropertyError:
    return PropertyError(f"'{prop.name}' takes {wanted}, got {value!r}")


def _str(prop: Property, value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    raise _bad(prop, value, "text")


def _int(prop: Property, value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or (isinstance(value, float) and not value.is_integer()):
        raise _bad(prop, value, "a whole number")
    return int(value)


def _float(prop: Property, value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise _bad(prop, value, "a number")
    return float(value)


def _bool(prop: Property, value: Any) -> bool:
    if not isinstance(value, bool):
        raise _bad(prop, value, "true or false")
    return value


def _color(prop: Property, value: Any) -> str:
    base = re.sub(r"\s*@\s*\d+(?:\.\d+)?\s*%$", "", value) if isinstance(value, str) else value  # `primary@12%`: a colour with its alpha scaled
    if isinstance(base, str) and (_HEX_COLOR.match(base) or _ROLE_OR_NAME.match(base) or "(" in base):
        return value
    raise _bad(prop, value, "a theme role, #RRGGBB[AA] or a CSS colour, optionally ending in @N%")


def _length(prop: Property, value: Any) -> Any:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value
    if isinstance(value, str) and _LENGTH.match(value):
        return value
    raise _bad(prop, value, "a number, 'auto' or a percentage like '50%'")


def _icon(prop: Property, value: Any) -> str:
    from tesserae.icons import ICONS

    if not isinstance(value, str) or not _ICON.match(value):
        raise _bad(prop, value, "an icon name")
    if value not in ICONS:
        raise PropertyError(f"'{prop.name}' names no built-in icon: {value!r}", _near(value, ICONS))
    return value


def _list(prop: Property, value: Any) -> list:
    if not isinstance(value, list):
        raise _bad(prop, value, "a list")
    return value


def _dict(prop: Property, value: Any) -> dict:
    if not isinstance(value, dict):
        raise _bad(prop, value, "a mapping")
    return value


def _handler(prop: Property, value: Any) -> str:
    if not isinstance(value, str):
        raise _bad(prop, value, "an action name or statements")
    return value


_COERCE: dict[str, Callable[[Property, Any], Any]] = {
    "str": _str, "int": _int, "float": _float, "bool": _bool, "color": _color, "length": _length, "icon": _icon,
    "enum": lambda prop, value: value, "list": _list, "dict": _dict, "handler": _handler, "any": lambda prop, value: value,
}


@dataclass
class WidgetDecl:
    """A widget's declaration. `container` is whether it takes `children`; `view` is whether it came from a view file's `params:`."""

    name: str
    properties: dict[str, Property] = field(default_factory=dict)
    extras: tuple[str, ...] = ()
    parts: tuple[str, ...] = ()
    container: bool = False
    view: bool = False
    doc: str = ""
    #: groups of properties of which exactly one must be given (an Icon's `icon` or `path`)
    one_of: tuple[tuple[str, ...], ...] = ()

    def check_properties(self, given: Iterable[str]) -> list[tuple[str, Optional[str]]]:
        """Problems with a set of property names: `(message, hint)`, unknown first, then required but missing."""
        problems: list[tuple[str, Optional[str]]] = []
        given = list(given)
        for key in given:
            if key not in self.properties:
                listing = "properties: " + (", ".join(self.properties) or "none")
                near = _near(key, self.properties)
                problems.append((f"{self.name}: no property '{key}'", f"{near}; {listing}" if near else listing))
        for name, prop in self.properties.items():
            if prop.required and name not in given:
                problems.append((f"{self.name}: '{name}' is required", None))
        for group in self.one_of:
            chosen = [name for name in group if name in given]
            if not chosen:
                problems.append((f"{self.name}: give one of {', '.join(repr(n) for n in group)}", None))
            elif len(chosen) > 1:
                problems.append((f"{self.name}: {' and '.join(repr(n) for n in chosen)} cannot both be given", None))
        return problems


_REGISTRY: dict[str, WidgetDecl] = {}
_BUILTIN_LOADED = False


def _load_builtins() -> None:
    global _BUILTIN_LOADED
    if not _BUILTIN_LOADED:
        _BUILTIN_LOADED = True
        from tesserae.spec import builtin_widgets  # noqa: F401  (declares on import)


def declare(name: str, properties: Optional[dict[str, Property]] = None, *, extras: Iterable[str] = (), parts: Iterable[str] = (),
            container: bool = False, doc: str = "", one_of: Iterable[Iterable[str]] = ()) -> WidgetDecl:
    """Declares a built-in widget. A duplicate name is an error: replace one on purpose with `register_widget(..., replace=True)`."""
    props = dict(properties or {})
    for prop_name, prop in props.items():
        prop.name = prop_name
    _check_reserved(name, props)
    decl = WidgetDecl(name, props, tuple(extras), tuple(parts), container, False, doc, tuple(tuple(g) for g in one_of))
    if name in _REGISTRY:
        raise ValueError(f"widget {name!r} is already declared")
    _REGISTRY[name] = decl
    return decl


def _check_reserved(name: str, props: dict[str, Property]) -> None:
    clash = sorted(set(props) & RESERVED_KEYS)
    if clash:
        raise ValueError(f"{name}: {', '.join(repr(c) for c in clash)} cannot be a property: the name is a key every node has")


def register_widget(decl: WidgetDecl, *, replace: bool = False) -> WidgetDecl:
    """Registers an app's own widget (`app.register_widget`)."""
    _load_builtins()
    _check_reserved(decl.name, decl.properties)
    if decl.name in _REGISTRY and not replace:
        raise ValueError(f"widget {decl.name!r} is already registered")
    _REGISTRY[decl.name] = decl
    return decl


def unregister_widget(name: str) -> None:
    _REGISTRY.pop(name, None)


def widget(name: str, *, container: bool = False, doc: str = "") -> Callable[[type], type]:
    """Declares a widget from a class whose `Property` attributes are its properties, `extras` and `parts` its tuples."""

    def wrap(cls: type) -> type:
        props = {k: v for k, v in vars(cls).items() if isinstance(v, Property)}
        decl = declare(name, props, extras=getattr(cls, "extras", ()), parts=getattr(cls, "parts", ()), container=container,
                       doc=doc or (cls.__doc__ or "").strip().split("\n")[0])
        cls.decl = decl  # type: ignore[attr-defined]
        return cls

    return wrap


def lookup(name: str) -> Optional[WidgetDecl]:
    _load_builtins()
    return _REGISTRY.get(name)


def names() -> list[str]:
    _load_builtins()
    return sorted(_REGISTRY)


def style_fields_of(decl: Optional[WidgetDecl]) -> frozenset[str]:
    """The style fields `decl`'s nodes may have (spec section 10): the universal ones and the widget's own `extras`
    (`foreground` is one for the widgets that draw text or glyphs). A view accepts `foreground` too: its root decides."""
    base = _style_fields()
    if decl is not None and decl.view:
        return base | {"foreground"}
    return base | frozenset(decl.extras if decl else ())


def decl_from_params(name: str, params: Any) -> WidgetDecl:
    """A view's declaration from its `params:` (spec section 3): a list of names (all `any`, required unless written `{name: default}`)
    or a mapping of name to a type, or to `{type, default, choices, required, model, doc}`."""
    props: dict[str, Property] = {}
    if params is None:
        pass
    elif isinstance(params, list):
        for item in params:
            if isinstance(item, str):
                props[item] = Property("any", required=True)
            elif isinstance(item, dict) and len(item) == 1:
                (key, default), = item.items()
                props[key] = Property("any", default=default)
            else:
                raise ValueError(f"{name}: a params entry is a name or {{name: default}}, got {item!r}")
    elif isinstance(params, dict):
        allowed = {"type", "default", "choices", "required", "model", "doc"}
        for key, spec in params.items():
            if isinstance(spec, str):
                props[key] = Property(spec)
            elif isinstance(spec, dict):
                extra = set(spec) - allowed
                if extra:
                    raise ValueError(f"{name}: param '{key}' has unknown field(s) {sorted(extra)} (allowed: {', '.join(sorted(allowed))})")
                props[key] = Property(**{**spec, "type": spec.get("type", "any")})
            else:
                raise ValueError(f"{name}: param '{key}' is a type or a mapping, got {spec!r}")
    else:
        raise ValueError(f"{name}: params is a list or a mapping, got {params!r}")
    for key, prop in props.items():
        prop.name = key
    _check_reserved(name, props)
    return WidgetDecl(name, props, container=True, view=True)


# -- JSON schema -----------------------------------------------------------------------------------------------------

_UNIVERSAL: dict[str, dict[str, Any]] = {
    "widget": {"type": "string"},
    "name": {"type": "string", "pattern": "^[A-Za-z_][A-Za-z0-9_]*$"},
    "if": {"type": "string"}, "for": {"type": "string"}, "key": {"type": "string"}, "slot": {"type": "string"},
    "state": {"type": "object"}, "style": {"type": "object"}, "classes": {"type": "array", "items": {"type": "string"}},
    "handlers": {"type": "object", "additionalProperties": {"type": "string"}}, "a11y": {"type": "object"},
    "interaction": {"type": ["boolean", "string"]}, "window_region": {"enum": ["drag", "none"]},
    "route": {"type": "string"}, "focus_group": {"enum": ["horizontal", "vertical", "both"]},
    # the header of a view file, valid on its root
    "params": {"type": ["array", "object"]}, "expects": {"type": "object"},
}
_EXPRESSION = {"type": "string", "pattern": r"\{\{"}
_JSON_TYPE = {
    "str": {"type": "string"}, "icon": {"type": "string"}, "handler": {"type": "string"}, "color": {"type": "string"},
    "int": {"type": "integer"}, "float": {"type": "number"}, "bool": {"type": "boolean"}, "length": {"type": ["number", "string"]},
    "list": {"type": "array"}, "dict": {"type": "object"},
}


def _schema_of(prop: Property) -> dict[str, Any]:
    if prop.type == "node":
        out: dict[str, Any] = {"$ref": "#"}
    elif prop.type == "nodes":
        out = {"type": "array", "items": {"$ref": "#"}}
    elif prop.type == "enum":
        out = {"anyOf": [{"enum": list(prop.choices or ())}, _EXPRESSION]}
    elif prop.type == "any":
        out = {}
    else:
        out = {"anyOf": [_JSON_TYPE[prop.type], _EXPRESSION]}
    return {**out, "description": prop.doc} if prop.doc else out


def json_schema() -> dict[str, Any]:
    """A JSON schema of every registered widget's node (an `if`/`then` per `widget:` value), for editors."""
    _load_builtins()
    branches = []
    for name in sorted(_REGISTRY):
        decl = _REGISTRY[name]
        props = {k: _schema_of(p) for k, p in decl.properties.items()}
        extra = {"children": {"type": "array", "items": {"$ref": "#"}}} if decl.container else {}
        branches.append({
            "if": {"properties": {"widget": {"const": name}}, "required": ["widget"]},
            "then": {
                "properties": {**_UNIVERSAL, **extra, **props},
                "required": ["widget"] + [k for k, p in decl.properties.items() if p.required],
                "propertyNames": {"enum": [*_UNIVERSAL, *extra, *props]},
            },
        })
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Tesserae view node (0.5.0)",
        "type": "object",
        "required": ["widget"],
        "properties": {**_UNIVERSAL, "widget": {"enum": sorted(_REGISTRY)}},
        "allOf": branches,
    }
