#!/usr/bin/env python3
"""Writes the YAML reference page, `docs/api/yaml.md` (0.3.4, #83).

One page for every key of every kind of file Tesserae reads: a view's node (and
its `style`, `text`, `handlers`, `a11y`), the kinds of node, component calls
and fragments, a shell file, a theme and a stylesheet. Each stub lists all of
its properties with the values they take and what they do. It is written from
the same schemas the editors use (`tools/generate_yaml_schema.py`), so the page,
the schemas and the code can't disagree; the only prose of its own is KINDS.

    python tools/generate_yaml_docs.py          # write docs/api/yaml.md
    python tools/generate_yaml_docs.py --check  # exit 1 if it is out of date
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "docs" / "api" / "yaml.md"

#: Every `kind:`, in the order the page lists them: (kind, what it is, the keys beyond the common ones that it uses).
KINDS = (
    ("Rect", "A box you paint: a fill, a border, rounded corners, a shadow. Holds children. Takes `interaction:` and click handlers.", ""),
    ("Container", "A box that lays out its children and paints nothing unless you style it. Takes `interaction:` and click handlers.", ""),
    ("ScrollView", "A box whose children scroll when they are bigger than it.", ""),
    ("Text", "Text in one style.", "`text:`"),
    ("Link", "Text that is clickable, with focus and a keyboard activation.", "`text:`, `handlers: {on_click}`"),
    ("TextField", "A single-line text input in a box.", "`text:`, `two_way:`, `handlers: {on_change}`"),
    ("Image", "A picture from a file.", "`image:`"),
    ("Icon", "A glyph from Tesserae's icon set, coloured by `style.foreground`.", "`icon:`"),
    ("Checkbox", "MD3's checkbox.", "`checked:`, `disabled:`, `handlers: {on_change}`"),
    ("RadioButton", "MD3's radio button; the ones with one `group:` exclude each other.", "`selected:`, `group:`, `disabled:`"),
    ("Switch", "MD3's switch.", "`selected:`, `disabled:`"),
    ("Slider", "MD3's slider.", "`value:`, `min:`, `max:`, `step:`"),
    ("SpinBox", "A number field between − and + buttons.", "`value:`, `min:`, `max:`, `step:`"),
    ("CircularProgress", "A circular progress indicator; no `value:` means indeterminate.", "`value:`"),
    ("LinearProgress", "A linear progress indicator; no `value:` means indeterminate.", "`value:`"),
    ("LoadingIndicator", "MD3's loading indicator, always indeterminate.", ""),
    ("TimePickerDial", "MD3's time picker dial.", "`hour:`, `minute:`"),
    ("NodeGraph", "A pannable canvas of `GraphNode`s joined by edges.", "`edges:`, children that are `GraphNode`s"),
    ("GraphNode", "A node in a `NodeGraph`: a titled box at a place.", "`label:`, `x:`, `y:`"),
    ("TitleBar", "The window's own title bar: an icon, a title, your content and the window's buttons. Needs `App(decorations=False)`.", "`title:`, `icon:`, `buttons:`"),
)


def _schemas() -> dict[str, dict[str, Any]]:
    spec = importlib.util.spec_from_file_location("generate_yaml_schema", ROOT / "tools" / "generate_yaml_schema.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.schemas()


class Reader:
    """Resolves `$ref`s and says in words what a schema accepts."""

    def __init__(self, schema: dict[str, Any]) -> None:
        self.defs = schema.get("definitions", {})

    def resolve(self, schema: dict[str, Any]) -> dict[str, Any]:
        while "$ref" in schema:
            schema = {**self.defs[schema["$ref"].rsplit("/", 1)[1]], **{k: v for k, v in schema.items() if k != "$ref"}}
        return schema

    def values(self, schema: dict[str, Any]) -> str:
        if "$ref" in schema:
            name = schema["$ref"].rsplit("/", 1)[1]
            if name in ("color", "style", "zone_style"):
                return {"color": "a color", "style": "a `style` mapping", "zone_style": "a `style` mapping"}[name]
        schema = self.resolve(schema)
        if "enum" in schema:
            if len(schema["enum"]) > 14:
                return f"one of {len(schema['enum'])} names"
            return " \\| ".join(f"`{v}`" for v in schema["enum"])
        if "const" in schema:
            return f"`{schema['const']}`"
        for key in ("anyOf", "oneOf"):
            if key in schema:
                parts = [self.values(s) for s in schema[key] if "$ref" not in s or "parameter" not in s["$ref"] and "conditional" not in s["$ref"]]
                out: list[str] = []
                for part in parts:
                    if part not in out:
                        out.append(part)
                return " or ".join(out)
        kind = schema.get("type")
        if kind == "string" and "pattern" in schema and "%" in schema["pattern"]:
            return "a percentage such as `50%`"
        return {"number": "a number", "integer": "an integer", "string": "text", "boolean": "`true` or `false`",
                "object": "a mapping", "array": "a list"}.get(kind, "any value")


#: A mapping with more properties than this, all of one kind (colour roles, type roles), is one row, not one each.
GROUP = 8
SIDES = {"top": "the top", "right": "the right", "bottom": "the bottom", "left": "the left"}


def _item_properties(reader: Reader, schema: dict[str, Any]) -> dict[str, Any]:
    """The properties of a list's entries, when they are a small mapping of their own (not a whole node)."""
    resolved = reader.resolve(schema)
    items = resolved.get("items", {})
    if resolved.get("type") != "array" or items.get("$ref", "").rsplit("/", 1)[-1] in ("node", "widget"):
        return {}
    return reader.resolve(items).get("properties", {})


def _grouped(reader: Reader, schema: dict[str, Any]) -> bool:
    props = list(reader.resolve(schema).get("properties", {}).values())
    return len(props) > GROUP and len({reader.values(p) + str(sorted(reader.resolve(p).get("properties", {}))) for p in props}) == 1


def _rows(reader: Reader, schema: dict[str, Any], prefix: str = "", depth: int = 3) -> list[tuple[str, str, str, bool]]:
    """(dotted key, values, what it does, required) for each property, nested ones after their parent."""
    schema = reader.resolve(schema)
    required = set(schema.get("required", []))
    rows = []
    if _grouped(reader, schema):
        first = next(iter(schema["properties"].values()))
        names = ", ".join(f"`{n}`" for n in list(schema["properties"])[:4])
        text = f"One for each of {len(schema['properties'])} names, such as {names}."
        rows.append((f"{prefix}<name>", reader.values(first), text, False))
        inner = reader.resolve(first)
        if depth > 1 and inner.get("properties"):
            rows += _rows(reader, inner, f"{prefix}<name>.", depth - 1)
        return rows
    for name, sub in schema.get("properties", {}).items():
        resolved = reader.resolve(sub)
        if "anyOf" in resolved and not resolved.get("description"):
            described = next((s for s in resolved["anyOf"] if reader.resolve(s).get("description")), None)
            if described:
                resolved = {**resolved, "description": reader.resolve(described)["description"]}
        text = " ".join(resolved.get("description", "").split())
        if not text and name == "kind" and "const" in resolved:
            text = f"Always `{resolved['const']}`."
        if not text and name in SIDES:
            text = f"Space on {SIDES[name]} side."
        if sub.get("$ref", "").endswith("/color") and "description" not in sub:
            text = "A color."
        values = reader.values(sub)
        if name == "kind" and resolved.get("enum"):
            values = "a [kind](#the-kinds)"
        rows.append((prefix + name, values, text, name in required))
        if _item_properties(reader, sub) and depth > 1:
            rows += _rows(reader, resolved["items"], f"{prefix}{name}[].", depth - 1)
        if depth > 1 and sub.get("$ref", "").rsplit("/", 1)[-1] not in ("style", "zone_style", "text", "handlers", "a11y"):
            inner = resolved
            if "anyOf" in inner:  # a number or a `{size, style}`: show the mapping's keys
                inner = next((reader.resolve(s) for s in inner["anyOf"] if reader.resolve(s).get("properties")), inner)
            if inner.get("properties"):
                rows += _rows(reader, inner, f"{prefix}{name}.", depth - 1)
    return rows


def _table(rows: list[tuple[str, str, str, bool]], first: str = "Key") -> list[str]:
    out = [f"| {first} | Values | What it does |", "| --- | --- | --- |"]
    for key, values, text, required in rows:
        mark = " *(required)*" if required else ""
        out.append(f"| `{key}`{mark} | {values} | {text.replace('|', chr(92) + '|')} |")
    return out + [""]


def _stub(reader: Reader, schema: dict[str, Any], indent: int = 0, depth: int = 2) -> list[str]:
    schema = reader.resolve(schema)
    lines = []
    pad = "  " * indent
    if _grouped(reader, schema):
        first = next(iter(schema["properties"].values()))
        inner = reader.resolve(first)
        if inner.get("properties") and depth > 1:
            return [f"{pad}<name>:"] + _stub(reader, inner, indent + 1, depth - 1)
        return [f"{pad}<name>: <{reader.values(first).replace('`', '')}>"]
    for name, sub in schema.get("properties", {}).items():
        if _item_properties(reader, sub) and depth > 1:
            lines.append(f"{pad}{name}:")
            lines.append(f"{pad}  - " + ", ".join(f"{k}: ..." for k in _item_properties(reader, sub)))
            continue
        resolved = reader.resolve(sub)
        inner = resolved
        if "anyOf" in inner:
            inner = next((reader.resolve(s) for s in inner["anyOf"] if reader.resolve(s).get("properties")), inner)
        nested = inner.get("properties") if depth > 1 and sub.get("$ref", "").rsplit("/", 1)[-1] not in ("style", "zone_style", "text", "handlers", "a11y") else None
        if nested:
            lines.append(f"{pad}{name}:")
            lines += _stub(reader, inner, indent + 1, depth - 1)
        else:
            hint = reader.values(sub).replace(" \\| ", " | ").replace("`", "")
            if len(hint) > 60:
                hint = hint[:57] + "..."
            lines.append(f"{pad}{name}: <{hint}>")
    return lines


def _block(reader: Reader, schema: dict[str, Any], what: str, first: str = "Key") -> list[str]:
    return ["```yaml", *_stub(reader, schema), "```", "", *_table(_rows(reader, schema), first)]


def render() -> str:
    schemas = _schemas()
    view, component = Reader(schemas["tesserae-yaml-schema.json"]), Reader(schemas["tesserae-component-schema.json"])
    shell, theme = Reader(schemas["tesserae-shell-schema.json"]), Reader(schemas["tesserae-theme-schema.json"])
    out = ["# YAML Reference", "",
           "Every key Tesserae's YAML files take, with the values it accepts and what it does. "
           "This page is written from the same schemas your editor uses (`tesserae schema`), "
           "so it can't fall behind the code. For how the pieces fit, see the [guide](../guide/layout.md).", "",
           "## The files", "",
           "| File | What it is | Reference |", "| --- | --- | --- |",
           "| `<Name>_View.yaml` | A screen: one node with its children. | [The node](#the-node) |",
           "| `<Name>_Component.yaml` | A reusable fragment with `params:`. | [Components](#components) |",
           "| `<Name>_Shell.yaml` | The frame around the screens: bars, navigation, zones. | [Shell file](#shell-file) |",
           "| `<Name>_Theme.yaml` | A theme: colours, type, shapes and style rules. | [Theme and stylesheet](#theme-and-stylesheet) |",
           "| `<Name>_Stylesheet.yaml` | Style rules for a view. | [Theme and stylesheet](#theme-and-stylesheet) |",
           "| `<Name>_Style.yaml` | One node's `style:`, shared. | [The style](#the-style) |", ""]

    node = view.resolve(view.defs["node"])
    widget = view.resolve(view.defs["widget"])
    out += ["## The node", "",
            "A view is one node, with its children inside it. A node is a widget (`kind:`), a fragment used in place "
            "(`component:`), or a file put in place (`include:`).", ""]
    out += _block(view, widget, "node")
    out += ["## The kinds", "", "`kind:` says what a node is. Beyond the keys every node has, each kind uses a few.", "",
            "| Kind | What it is | It also uses |", "| --- | --- | --- |"]
    out += [f"| `{kind}` | {text} | {uses or 'Only the common keys.'} |" for kind, text, uses in KINDS]
    out += [""]
    out += ["## The style", "", "A node's `style:` is a mapping of these fields, or the name of a `*_Style.yaml` file. "
            "The same fields go in a stylesheet's or theme's rules, and in a shell file's parts.", ""]
    out += _table(_rows(view, view.defs["style"]), "Field")
    out += ["## Colors", "", "Any field that takes a color takes " + view.defs["color"]["description"][0].lower()
            + view.defs["color"]["description"][1:].replace("A theme role (", "a theme role (", 1) + "", ""]
    out += ["## The text", "", "`text:` on a Text, Link or TextField.", ""]
    out += _block(view, view.defs["text"], "text", "Key")
    from tesserae import view as view_module

    actions = ", ".join(f"`window.{action}`" for action in view_module.WINDOW_ACTIONS)
    out += ["## Handlers", "", f"`handlers:` names what an event calls: a ViewModel method, or one of {actions}.", ""]
    handler_rows = [(key, "a method name", text.split(":")[0] + ".", req) for key, _, text, req in _rows(view, view.defs["handlers"])]
    out += _table(handler_rows, "Event")
    out += ["## Accessibility", "", "`a11y:` on any node.", ""]
    out += _table(_rows(view, view.defs["a11y"]), "Key")
    out += ["## The title bar", "", "`kind: TitleBar`, for an app that draws its own window frame.", ""]
    out += _block(view, view.defs["title_bar"], "title bar")
    out += ["## Components", "",
            "`component: Name` puts a fragment in place, filling its `{{ parameters }}` from `with:`. "
            "[Every built-in one](../components/index.md) has a page.", ""]
    call = view.resolve(view.defs["component_call"])
    out += ["**Using one**", ""] + _block(view, {**call, "properties": {k: v for k, v in call["properties"].items()}}, "call")
    frag = component.resolve(component.defs["widget"])
    extra = {k: frag["properties"][k] for k in ("params", "when") if k in frag["properties"]}
    out += ["**Writing one**: a `*_Component.yaml` is a node, plus", ""]
    out += _table(_rows(component, {"properties": extra}), "Key")
    out += ["Inside a fragment, any value can also be a `{{ parameter }}`, or chosen by one with "
            "`{if: \"{{ flag }}\", then: a, else: b}`.", ""]
    out += ["## Shell file", "", "`*_Shell.yaml`: [App Shell & Docking](../guide/app-shell.md).", ""]
    out += _block(shell, schemas["tesserae-shell-schema.json"], "shell")
    out += ["## Theme and stylesheet", "",
            "A stylesheet has only `styles:`; a theme has everything. See [Themes](../themes/index.md).", ""]
    out += _block(theme, schemas["tesserae-theme-schema.json"], "theme")
    rule = theme.defs["rule"]
    out += ["**A rule in `styles:`**", ""] + _table(_rows(theme, rule), "Key")
    return "\n".join(out).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--check", action="store_true", help="exit 1 if the page is out of date")
    args = parser.parse_args()
    text = render()
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != text:
            print(f"{OUTPUT.relative_to(ROOT)} is out of date: run `python tools/generate_yaml_docs.py`")
            return 1
        return 0
    OUTPUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUTPUT.relative_to(ROOT)}: {len(text.splitlines())} lines")
    return 0


if __name__ == "__main__":
    sys.exit(main())
