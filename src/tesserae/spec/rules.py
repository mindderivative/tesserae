"""Stylesheet rules: the looks of widgets, by widget, variant, part and state (spec section 10; phase 6 of #209).

A stylesheet (`<Name>_Stylesheet.yaml`) is a list of rules:

```yaml
styles:
  - widget: Button          # a widget (a built-in, or a view called by its name)
    variant: tonal          # optional: variant, size, shape (properties the widget declares), classes, name
    part: label             # optional: a named node inside the widget's view (default: the widget's root)
    state: hovered          # optional: hovered, focused, pressed, disabled, selected, checked, expanded
    style: {foreground: on_secondary_container}
```

**Specificity**, high to low: `name`, then how many of `variant`/`size`/`shape`/`classes` the rule names, then `state`, then `widget` alone;
a later rule wins a tie. **Layers** are applied lowest first (a widget's own shipped looks, then the app's), so the app's stylesheet beats what
a widget ships. A node's inline `style:` beats every rule, for the fields it sets and no others.

A value in a rule may be an expression (`"{{ height / 2 }}"`), read in the widget's own names: its properties for a built-in, its params for a
view. `RuleSheet.of` checks every rule against the registry; `Rule.matches` and `ordered` find a node's rules in the order they apply.
"""

from __future__ import annotations

import difflib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Optional

from tesserae.expr import ExprError, Origin, compile_template
from tesserae.spec import widgets as registry
from tesserae.spec.nodes import LoadError, load_marked
from tesserae.spec.widgets import style_fields_of

__all__ = ["INTERACTION_STATES", "Identity", "Rule", "RuleSheet", "STATES", "is_rule_sheet", "load_rule_sheet", "ordered",
           "style_fields_of"]

#: The states a rule may select. The first three are interaction states; the rest read the node's own property of that name.
STATES = ("hovered", "focused", "focus_visible", "pressed", "disabled", "selected", "checked", "expanded", "error", "read_only")
INTERACTION_STATES = ("hovered", "focused", "focus_visible", "pressed")
#: Properties a rule may select on, besides `classes` and `name`.
SELECTOR_PROPERTIES = ("variant", "size", "shape")
_RULE_KEYS = ("widget", "variant", "size", "shape", "classes", "name", "part", "state", "style")


def is_rule_sheet(spec: Any) -> bool:
    """Whether a parsed stylesheet is in this shape: some rule names a `widget`, `part`, `state`, `variant`, `size`, `shape` or `name`
    (the 0.4.x shape has `kind`, `classes` and `id`)."""
    rules = spec.get("styles") if isinstance(spec, dict) else None
    return isinstance(rules, list) and any(isinstance(r, dict) and set(r) & {"widget", "part", "state", "variant", "size", "shape", "name"} for r in rules)


@dataclass
class Identity:
    """One way an instance can be named by a rule: it is the `widget` itself (`part` is `None`) or the node called `part` inside it.
    `get(name)` reads the widget's property of that name; `scope` is where a rule's expressions read."""

    widget: str
    part: Optional[str]
    get: Callable[[str], Any]
    scope: Any
    #: the interaction Signal (`hovered`, `focused`, ...) of the widget this names: for a part, the widget's, not the part's own
    interaction: Optional[Callable[[str], Any]] = None


@dataclass
class Rule:
    widget: Optional[str]
    style: dict[str, Any]
    selectors: dict[str, Any] = field(default_factory=dict)  # variant, size, shape
    classes: frozenset[str] = frozenset()
    name: Optional[str] = None
    part: Optional[str] = None
    state: Optional[str] = None
    order: int = 0
    at: tuple[int, int] = (1, 0)

    @property
    def specificity(self) -> tuple[int, int, int, int]:
        return (1 if self.name else 0, len(self.selectors) + (1 if self.classes else 0), 1 if self.state else 0, 1 if self.widget else 0)

    def matches(self, identity: Identity, classes: Iterable[str], name: Optional[str]) -> bool:
        """Whether this rule's widget, part and selectors fit `identity` (the state is tested by the caller, which knows the node)."""
        if self.widget is not None and (self.widget != identity.widget or self.part != identity.part):
            return False
        if self.name is not None and self.name != name:
            return False
        if self.classes and not self.classes <= set(classes):
            return False
        return all(identity.get(prop) == wanted for prop, wanted in self.selectors.items())


class RuleSheet:
    """A prepared stylesheet in the rule shape. The rules are indexed by widget name for a quick first test."""

    def __init__(self, rules: list[Rule], file: str = "<stylesheet>") -> None:
        self.rules, self.file = rules, file
        self.by_widget: dict[Optional[str], list[Rule]] = {}
        for rule in rules:
            self.by_widget.setdefault(rule.widget, []).append(rule)

    @classmethod
    def of(cls, spec: Any, file: str = "<stylesheet>", text: str = "") -> "RuleSheet":
        """Checks and prepares `{styles: [...]}`. Every problem is a `LoadError` naming the rule."""
        return _build(spec, file, text)

    def without(self, widgets: Iterable[str]) -> "RuleSheet":
        """The sheet less the rules that name any of `widgets` (the looks of components a project has replaced)."""
        gone = set(widgets)
        return RuleSheet([r for r in self.rules if r.widget not in gone], self.file)

    def candidates(self, widgets: Iterable[str]) -> list[Rule]:
        """The rules that could apply to a node known by these widget names (and the ones with no widget)."""
        out: list[Rule] = list(self.by_widget.get(None, ()))
        for name in widgets:
            out.extend(self.by_widget.get(name, ()))
        return out


def ordered(rules: Iterable[Rule]) -> list[Rule]:
    """Rules in the order they apply: least specific first, a later rule after an earlier one of the same specificity."""
    return sorted(rules, key=lambda r: (r.specificity, r.order))


def _near(text: Any, options: Iterable[Any]) -> Optional[str]:
    close = difflib.get_close_matches(str(text), [str(o) for o in options], n=3)
    return ("did you mean " + " or ".join(f"'{c}'" for c in close)) if close else None


def _build(spec: Any, file: str, text: str) -> RuleSheet:
    def fail(at: tuple[int, int], message: str, hint: Optional[str] = None) -> LoadError:
        return LoadError(message, file=file, line=at[0], column=at[1], hint=hint, text=text)

    if spec is None:
        return RuleSheet([], file)
    top_at = getattr(spec, "at", (1, 0))
    if not isinstance(spec, dict):
        raise fail(top_at, f"a stylesheet is a mapping with 'styles:', got {type(spec).__name__}")
    for key in spec:
        if key != "styles":
            raise fail(getattr(spec, "key_at", {}).get(key, top_at), f"a stylesheet has only 'styles:', not '{key}'")
    items = spec.get("styles") or []
    if not isinstance(items, list):
        raise fail(getattr(spec, "val_at", {}).get("styles", top_at), "'styles:' is a list of rules")
    rules: list[Rule] = []
    for index, item in enumerate(items):
        at = getattr(items, "item_at", [top_at] * len(items))[index]
        if not isinstance(item, dict):
            raise fail(at, f"a rule is a mapping, got {type(item).__name__}")
        key_at = getattr(item, "key_at", {})
        val_at = getattr(item, "val_at", {})
        for key in item:
            if key not in _RULE_KEYS:
                raise fail(key_at.get(key, at), f"a rule has no '{key}'", _near(key, _RULE_KEYS))
        widget = item.get("widget")
        decl: Optional[registry.WidgetDecl] = None
        if widget is not None:
            if not isinstance(widget, str):
                raise fail(val_at.get("widget", at), f"'widget:' is a widget name, got {widget!r}")
            decl = registry.lookup(widget)  # a view is known only to the project: its rule is checked when the view is composed
        selectors: dict[str, Any] = {}
        for prop in SELECTOR_PROPERTIES:
            if prop in item:
                if widget is None:
                    raise fail(key_at.get(prop, at), f"'{prop}:' needs a 'widget:'")
                if decl is not None and prop not in decl.properties:
                    raise fail(key_at.get(prop, at), f"{widget} has no property '{prop}' to select on", _near(prop, decl.properties))
                declared = decl.properties.get(prop) if decl else None
                if declared is not None and declared.choices is not None and item[prop] not in declared.choices:
                    raise fail(val_at.get(prop, at), f"{widget}.{prop} is one of {', '.join(map(str, declared.choices))}, not {item[prop]!r}",
                               _near(item[prop], declared.choices))
                selectors[prop] = item[prop]
        classes = item.get("classes") or []
        if not isinstance(classes, list) or not all(isinstance(c, str) for c in classes):
            raise fail(val_at.get("classes", at), "'classes:' is a list of names")
        name = item.get("name")
        if name is not None and not isinstance(name, str):
            raise fail(val_at.get("name", at), "'name:' is a node's name")
        part = item.get("part")
        if part is not None:
            if widget is None:
                raise fail(key_at.get("part", at), "'part:' needs a 'widget:'")
            if decl is not None and decl.parts and part not in decl.parts:
                raise fail(val_at.get("part", at), f"{widget} has no part '{part}'", f"parts: {', '.join(decl.parts)}")
        state = item.get("state")
        if state is not None and state not in STATES:
            raise fail(val_at.get("state", at), f"'state:' is one of {', '.join(STATES)}, not {state!r}", _near(state, STATES))
        raw_style = item.get("style")
        if not isinstance(raw_style, dict) or not raw_style:
            raise fail(val_at.get("style", at), "a rule needs a 'style:' mapping")
        allowed = style_fields_of(decl) if decl is not None else style_fields_of(None) | {"foreground"}  # a view (not in the registry) is decided by its root
        style: dict[str, Any] = {}
        style_key_at, style_val_at = getattr(raw_style, "key_at", {}), getattr(raw_style, "val_at", {})
        for field_name, value in raw_style.items():
            if field_name not in allowed:
                message = f"{widget or 'a rule'}: style '{field_name}' is not valid here"
                if field_name == "foreground":
                    users = sorted(n for n in registry.names() if "foreground" in (registry.lookup(n).extras or ()))
                    raise fail(style_key_at.get(field_name, at), message, f"widgets that accept it: {', '.join(users)}")
                raise fail(style_key_at.get(field_name, at), message, _near(field_name, allowed))
            style[field_name] = _template(value, file, style_val_at.get(field_name, at), text)
        rules.append(Rule(widget, style, selectors, frozenset(classes), name, part, state, order=len(rules), at=at))
    return RuleSheet(rules, file)


def _template(value: Any, file: str, at: tuple[int, int], text: str) -> Any:
    if isinstance(value, str) and "{{" in value:
        try:
            return compile_template(value, origin=Origin(file, at[0], at[1]))
        except ExprError as exc:
            raise LoadError(exc.message, file=file, line=exc.line, column=exc.column, hint=exc.hint, text=text) from None
    return value


def load_rule_sheet(path: Any) -> RuleSheet:
    """Reads a stylesheet file in the rule shape."""
    file = Path(path)
    text = file.read_text(encoding="utf-8")
    return RuleSheet.of(load_marked(text, str(file)), str(file), text)
