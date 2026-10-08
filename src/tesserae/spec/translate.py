"""Old to new: translates a 0.4.x view or fragment into the 0.5.0 syntax (spec section 15; phase 3 of #209).

`Translator.translate(data)` takes the parsed YAML of one `*_View.yaml` or `*_Component.yaml` and returns the 0.5.0 mapping; everything it
could not translate exactly is a line in `.notes`, never a silent change. `to_yaml` writes it out. Phase 7 builds the `tesserae migrate-yaml`
command on this (files renamed, comments kept, a report); this module is the node-level rules, tested over every file in the repository.

What it does (the section 15 table): `kind:`/`component:`/`view:`/`include:` become `widget:`; `id:` becomes `name:` (the root's
`id: root` is dropped); `with:` becomes plain keys; `repeat:` becomes `for:` (a literal list becomes the sibling nodes the old expander
made); `when:` and `{if/then/else}` become `if:`; `bindings:` and `two_way:` become the property's expression (a model property given a
bare reference is two-way); `text:`, `icon:`, `image:` and `svg:` mappings are flattened into properties; `interaction: {color: X}`
becomes `interaction: X`.
"""

from __future__ import annotations

import re
from typing import Any, Callable, Optional

import yaml

from tesserae.spec.cascade import STYLE_FIELDS

__all__ = ["Translator", "to_yaml"]

_BRACES = re.compile(r"^\s*\{\{(.*)\}\}\s*$", re.S)
_GET = re.compile(r"^\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\.\s*get\s*\(\s*\)\s*\}\}$")
_VIEW_FILE = re.compile(r"^(.*?)(?:_View)?\.ya?ml$")
_DIRECTIVES = ("for", "key", "if")
#: A parameter spliced into text inside an expression: `'{{ screen }}'` in `{{ a == '{{ screen }}' }}` is just `screen`.
_NESTED = re.compile(r"""(['"])\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}\1""")
_NAVIGATE = re.compile(r"^navigate\.\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}$")
#: Old keys the translator consumes or drops; they are never copied as properties.
_CONSUMED = {"kind", "component", "view", "include", "id", "with", "repeat", "when", "bindings", "two_way", "component_of", "children"}
#: Old mapping-valued keys that are flattened into the widget's own properties, and the inner key that takes the outer name.
_FLATTEN = {"text": "content", "icon": "name", "image": None, "svg": None}


def _clean(value: Any) -> Any:
    """An expression string with its spliced-in parameters written as names."""
    if isinstance(value, str) and value.lstrip().startswith("{{") and "{{" in value[value.index("{{") + 2:]:
        return _NESTED.sub(lambda m: m.group(2), value)
    return value


def _unbrace(value: Any) -> Any:
    """`{{ x }}` as `x`, for the keys that take an expression without braces."""
    if isinstance(value, str):
        match = _BRACES.match(value)
        if match and "{{" not in match.group(1):
            return match.group(1).strip()
    return value


class Translator:
    """Translates nodes. `params_of(name)` returns a fragment's `params:` (so a `repeat:` over a parameter knows the per-item keys);
    `addressed`, when given, is the set of ids something addresses: the others lose their `id:`."""

    def __init__(self, params_of: Optional[Callable[[str], Any]] = None, addressed: Optional[set[str]] = None) -> None:
        self.params_of = params_of
        self.addressed = addressed
        self.notes: list[str] = []

    # documents

    def translate(self, data: Any) -> Any:
        """The 0.5.0 mapping for the root node `data` (header keys `params` and `expects` carried over)."""
        if not isinstance(data, dict):
            self.notes.append(f"the file is not a mapping ({type(data).__name__}); left as it was")
            return data
        header = {k: data[k] for k in ("params", "expects") if k in data}
        node = self.node({k: v for k, v in data.items() if k not in header}, root=True)
        return {**header, **node}

    # nodes

    def node(self, old: dict[str, Any], *, root: bool = False, extra: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        extra = extra or {}
        out: dict[str, Any] = {}
        where = old.get("id", "<node>")
        widget = self._widget(old, where)
        if widget is not None:
            out["widget"] = widget
        node_id = old.get("id")
        if isinstance(node_id, str) and not (root and node_id == "root"):
            if self.addressed is None or node_id in self.addressed:
                out["name"] = node_id
        for key in _DIRECTIVES:
            if key in extra:
                out[key] = extra[key]
        if "when" in old:
            out["if"] = _unbrace(old["when"])

        props: dict[str, Any] = {}
        for key, value in old.items():
            if key in _CONSUMED:
                continue
            if key in _FLATTEN and isinstance(value, dict):
                inner = _FLATTEN[key]
                for sub, item in value.items():
                    props[key if sub == inner else sub] = item
            elif key == "interaction" and isinstance(value, dict):
                out["interaction"] = value.get("color", True)
                if set(value) - {"color"}:
                    self.notes.append(f"{where}: interaction keys other than color were dropped: {sorted(set(value) - {'color'})}")
            elif key == "handlers" and isinstance(value, dict):
                out["handlers"] = {event: self._handler(action, where) for event, action in value.items()}
            else:
                props[key] = _clean(value)
        for key, value in (old.get("with") or {}).items():
            if key in props:
                self.notes.append(f"{where}: 'with: {key}' overrides the node's own '{key}'")
            props[key] = _clean(value)
        bindings = old.get("bindings") or {}
        if "if" in bindings and isinstance(bindings.get("then"), dict):
            self.notes.append(f"{where}: bindings: {{if, then}} became the then-bindings alone; the expression decides when it has a value")
            bindings = bindings["then"]
        for key, expression in bindings.items():
            if key in STYLE_FIELDS and key not in ("x", "y"):  # a bound paint or size is a style value
                style = props.get("style")
                if isinstance(style, str):
                    self.notes.append(f"{where}: bindings: {key} could not join the style file {style!r}")
                    props[key] = _clean(expression)
                else:
                    props["style"] = {**(style or {}), key: _clean(expression)}
            else:
                props[key] = _clean(expression)
        two_way = old.get("two_way")
        if isinstance(two_way, str) and two_way in props:
            bare = _GET.match(props[two_way]) if isinstance(props[two_way], str) else None
            if bare:
                props[two_way] = "{{ " + bare.group(1) + " }}"
            else:
                self.notes.append(f"{where}: two_way: {two_way} needs a bare reference but its binding is {props[two_way]!r}")
        elif two_way is not None:
            self.notes.append(f"{where}: two_way: {two_way!r} names no property the node gives")
        if "component_of" in old:
            self.notes.append(f"{where}: component_of: {old['component_of']} was dropped (name the node and address it as a part)")
        self._check_call(old, props, where)
        out.update(props)
        if "children" in old:
            out["children"] = self.children(old["children"], where)
        return out

    def _check_call(self, old: dict[str, Any], props: dict[str, Any], where: Any) -> None:
        """A call that gives a property its fragment does not declare (0.4.x let a call bind or handle the fragment's root)."""
        component = old.get("component")
        params = self.params_of(component) if (self.params_of and isinstance(component, str) and "{{" not in component) else None
        if params is None:
            return
        declared = {p if isinstance(p, str) else next(iter(p)) for p in params} if isinstance(params, list) else set(params)
        universal = {"style", "handlers", "a11y", "interaction", "classes", "window_region", "route", "slot", "state"}
        for key in props:
            if key not in declared and key not in universal:
                self.notes.append(f"{where}: {component} declares no parameter '{key}'; the component pass adds the property")

    def _handler(self, action: Any, where: Any) -> Any:
        match = _NAVIGATE.match(action) if isinstance(action, str) else None
        if match:
            self.notes.append(f"{where}: '{action}' became navigate_to({match.group(1)}): the dynamic form of navigate.<Screen>")
            return f"navigate_to({match.group(1)})"
        return action

    def _widget(self, old: dict[str, Any], where: Any) -> Optional[str]:
        if "kind" in old:
            return old["kind"]
        if "component" in old:
            if "{{" in str(old["component"]):
                self.notes.append(f"{where}: the widget name {old['component']!r} is a parameter; 0.5.0 has no dynamic widget names "
                                  "(a variant property replaces it)")
            return old["component"]
        for key in ("view", "include"):
            if key in old:
                match = _VIEW_FILE.match(str(old[key]))
                name = match.group(1) if match else str(old[key])
                if key == "include":
                    self.notes.append(f"{where}: include: {old[key]} became a call of the view '{name}'")
                return name
        self.notes.append(f"{where}: a node with no kind, component, view or include")
        return None

    # children, conditionals and repeats

    def children(self, items: Any, where: Any) -> list[Any]:
        out: list[Any] = []
        for item in items or []:
            if not isinstance(item, dict):
                out.append(item)
            elif "then" in item or "else" in item:
                out.extend(self._conditional(item))
            elif "repeat" in item:
                out.extend(self._repeat(item, where))
            else:
                out.append(self.node(item))
        return out

    def _conditional(self, item: dict[str, Any]) -> list[Any]:
        condition = _unbrace(item.get("if"))
        out = []
        if isinstance(item.get("then"), dict):
            out.append(self.node(item["then"], extra={"if": condition}))
        if isinstance(item.get("else"), dict):
            out.append(self.node(item["else"], extra={"if": f"not ({condition})"}))
        return out

    def _repeat(self, item: dict[str, Any], where: Any) -> list[Any]:
        repeat = item["repeat"]
        base = {k: v for k, v in item.items() if k != "repeat"}
        node_id = item.get("id", "item")
        if isinstance(repeat, list):  # literal per-item overrides: the sibling nodes the old expander made
            return [self.node({**base, "id": f"{node_id}_{index}", "with": {**(base.get("with") or {}), **(overrides or {})}})
                    for index, overrides in enumerate(repeat)]
        inner = _unbrace(repeat)
        given = set(item.get("with") or {})
        params = self.params_of(item["component"]) if (self.params_of and item.get("component")) else None
        per_item: dict[str, Any] = {}
        if params is None:
            self.notes.append(f"{where}: repeat: over {inner}: the per-item keys are not known; write the properties as '{{{{ item.x }}}}'")
        else:
            required = [p for p in (params if isinstance(params, list) else list(params))
                        if isinstance(p, str) and p not in given]
            per_item = {name: "{{ item." + name + " }}" for name in required}
        self.notes.append(f"{where}: repeat: became 'for: item in {inner}'; 'key: item' is a stand-in, write the identity (item.id)")
        merged = {**base, "with": {**(base.get("with") or {}), **per_item}}
        return [self.node(merged, extra={"for": f"item in {inner}", "key": "item"})]


def to_yaml(data: Any) -> str:
    """The mapping as YAML text, in order, with short mappings and lists on one line."""
    return yaml.safe_dump(data, sort_keys=False, default_flow_style=None, width=140, allow_unicode=True)
