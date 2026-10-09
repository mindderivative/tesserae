#!/usr/bin/env python3
"""Writes the YAML reference page, `docs/api/yaml.md` (0.3.4, #83).

One page for every key of every kind of file Tesserae reads: a view's node (and
its `style`, `text`, `handlers`, `a11y`), the kinds of node, component calls
and fragments, a theme and a stylesheet. Each stub lists all of
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

from tesserae.spec import cascade

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
    ("Svg", "An SVG document, drawn by the engine: shapes, gradients, text, clips and masks. `style.foreground` is what `currentColor` means, so an icon follows the theme.", "`svg:`"),
    ("Canvas", "A drawing surface: rectangles, circles and paths from a `draw:` list, repainted when the Signals it reads change.", "`canvas:`"),
    ("Icon", "A glyph from Tesserae's icon set, or from SVG path data, coloured by `style.foreground`.", "`icon:` (`name:`, or `path:` and `view_box:`)"),
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
    ("TitleBar", "A title bar: an icon, a title, your content and the window's buttons (`App(borderless=True)`), or a close button for a dialog or a sheet (`buttons: [dismiss]`).", "`title:`, `icon:`, `buttons:`"),
    ("Window", "The root of a view that is the whole OS window: its title, `borderless`, a `title_bar:`, and the content under it.", "`title:`, `borderless:`, `min_width:`, `min_height:`, `title_bar:`"),
    ("Dock", "Panels docked in zones (left, right, top, bottom, center) around the middle, with handles to resize them. One per window.", "`DockPanel` children"),
    ("DockPanel", "A panel in a Dock, in the zone its `style: {zone: ...}` names; panels in one zone are its tabs. Inside another DockPanel it is a split of it.", "`title:`, `style: {zone}`"),
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
            if name in ("color", "fill", "style", "zone_style"):
                return {"color": "a color", "fill": "a color or a gradient", "style": "a `style` mapping",
                        "zone_style": "a `style` mapping"}[name]
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


LEAF_REFS = ("style", "zone_style", "text", "handlers", "a11y")


def _is_leaf(sub: dict[str, Any]) -> bool:
    """A property whose mapping has a section of its own (the style, the text, ...): not spelled out inline."""
    refs = [sub.get("$ref", ""), *(member.get("$ref", "") for member in sub.get("anyOf", []))]
    return any(ref.rsplit("/", 1)[-1] in LEAF_REFS for ref in refs if ref)


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
        if depth > 1 and not _is_leaf(sub):
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
        nested = inner.get("properties") if depth > 1 and not _is_leaf(sub) else None
        if nested:
            lines.append(f"{pad}{name}:")
            lines += _stub(reader, inner, indent + 1, depth - 1)
        else:
            hint = reader.values(sub).replace(" \\| ", " | ").replace("`", "")
            if len(hint) > 60:
                hint = hint[:57] + "..."
            lines.append(f"{pad}{name}: <{hint}>")
    return lines


def _style_tables(reader: Reader) -> list[str]:
    """The style fields in the sections `tesserae.spec.cascade.STYLE_GROUPS` makes, each its own table."""
    style = reader.defs["style"]
    rows = _rows(reader, style)
    by_group: dict[str, list[tuple[str, str, str, bool]]] = {}
    for row in rows:
        top = row[0].split(".")[0]  # a field's own keys (`filter.sepia`) go with it
        group = style["properties"][top]["x-group"]
        by_group.setdefault(group, []).append((row[0], row[1], row[2].removesuffix(f" ({group}.)"), row[3]))
    out: list[str] = []
    for group in cascade.STYLE_GROUPS:
        out += [f"### {group}", ""] + _table(by_group.pop(group), "Field")
    if by_group:
        raise SystemExit(f"style fields in no known group: {sorted(by_group)}")
    return out


def _block(reader: Reader, schema: dict[str, Any], what: str, first: str = "Key") -> list[str]:
    return ["```yaml", *_stub(reader, schema), "```", "", *_table(_rows(reader, schema), first)]


def render() -> str:
    schemas = _schemas()
    view, component = Reader(schemas["tesserae-yaml-schema.json"]), Reader(schemas["tesserae-component-schema.json"])
    theme = Reader(schemas["tesserae-theme-schema.json"])
    out = ["# YAML Reference", "",
           "Every key Tesserae's YAML files take, with the values it accepts and what it does. "
           "This page is written from the same schemas your editor uses (`tesserae schema`), "
           "so it can't fall behind the code. For how the pieces fit, see the [guide](../guide/layout.md).", "",
           "## The files", "",
           "| File | What it is | Reference |", "| --- | --- | --- |",
           "| `<Name>_View.yaml` | A screen: one node with its children. | [The node](#the-node) |",
           "| `<Name>_Component.yaml` | A reusable fragment with `params:`. | [Components](#components) |",
           "| `<Name>_Theme.yaml` | A theme: colours, type, shapes and style rules. | [Theme and stylesheet](#theme-and-stylesheet) |",
           "| `<Name>_Stylesheet.yaml` | Style rules for a view. | [Theme and stylesheet](#theme-and-stylesheet) |",
           "| `<Name>_Style.yaml` | One node's `style:`, shared. | [The style](#the-style) |", ""]

    node = view.resolve(view.defs["node"])
    widget = view.resolve(view.defs["widget"])
    out += ["## The node", "",
            "A view is one node, with its children inside it. A node is a widget (`kind:`), a fragment used in place "
            "(`component:`), a file put in place (`include:`), or another view shown there (`view:`, below).", ""]
    out += _block(view, widget, "node")
    out += ["## The kinds", "", "`kind:` says what a node is. Beyond the keys every node has, each kind uses a few.", "",
            "| Kind | What it is | It also uses |", "| --- | --- | --- |"]
    out += [f"| `{kind}` | {text} | {uses or 'Only the common keys.'} |" for kind, text, uses in KINDS]
    out += [""]
    out += ["## The style", "", "A node's `style:` is a mapping of these fields, or the name of a `*_Style.yaml` file, which holds them under a "
            "`style:` key (and an optional `id:` naming it): `{id: row_style, style: {gap: 8}}`. "
            "The same fields go in a stylesheet's or theme's rules.", ""]
    out += _style_tables(view)
    out += ["## Colors", "", "Any field that takes a color takes " + view.defs["color"]["description"][0].lower()
            + view.defs["color"]["description"][1:].replace("A theme role (", "a theme role (", 1) + "", ""]
    out += ["## Gradients", "",
            "`background`, `foreground` and `border_color` take a gradient where they take a color: a CSS-like string "
            "(`linear-gradient(90deg, primary, tertiary)`, `radial-gradient(at 30% 30%, primary_container, surface)`, "
            "`conic-gradient(from 90deg, primary, secondary, primary)`; `to right` and the like name a direction; a stop "
            "may have a place, `primary 40%`) or a mapping "
            "(`{gradient: linear, angle: 90, stops: [primary, [0.6, secondary], tertiary]}`). Stops are theme roles or colors. "
            "A control's color (a `Switch`, a `Slider`) takes a plain color only.", ""]
    out += ["## The text", "", "`text:` on a Text, Link or TextField.", ""]
    out += _block(view, view.defs["text"], "text", "Key")
    from tesserae import view as view_module

    actions = ", ".join([*(f"`window.{action}`" for action in view_module.WINDOW_ACTIONS),
                         *(f"`surface.{action}`" for action in view_module.SURFACE_ACTIONS),
                         "`navigate.<Screen>`", *(f"`navigate.{t}`" for t in view_module.NAVIGATE_TARGETS)])
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
    out += ["## The window", "",
            "`kind: Window` is the root of a view that is the whole OS window (there is one per app, and it is not embedded or nested). "
            "Load it with `app.load(\"Window\")` (or `App(window_view=\"Window\")`). Its `title_bar:` takes a `TitleBar`'s keys and is the "
            "window's title bar when the window is `borderless`; its `children` are the content under it; `style:`'s `width` and "
            "`height` are the window's size and its `background` the window's.", ""]
    out += _block(view, view.resolve(view.defs["window_node"]), "window")
    out += ["## The dock", "",
            "`kind: Dock` holds `kind: DockPanel`s; each says which zone it is in with `style: {zone: left|right|top|bottom|center}`. "
            "Panels in one zone are its tabs (titled by `title:`), which the user can drag to another zone; the size of a left or "
            "right zone is its panel's `width`, a top or bottom one's its `height`, and a handle between a zone and the middle "
            "resizes it. A `DockPanel` inside a `DockPanel` is a split of it, side by side (`flex_direction: horizontal`, the "
            "default) or top and bottom (`vertical`), with a handle between them. A panel has splits or content, not both. "
            "From Python, `view.dock_host(\"dock\")` has `layout()`, `restore(layout)`, `size(side)` and `set_size(side, size)`.", ""]
    out += _block(view, view.resolve(view.defs["dock_node"]), "dock")
    out += _block(view, view.resolve(view.defs["dock_panel_node"]), "dock panel")
    out += ["## Embedded views", "",
            "`view: Left_View.yaml` shows another view in place (or a name found in the project: `view: Left`). It is a view of its own, "
            "so its ids don't clash with this one's, and it has its own ViewModel when `Left_ViewModel.py` is beside it or in the project; "
            "a view with none is static (no bindings, handlers or `two_way:`). `with:` is given to the ViewModel's constructor as keyword "
            "arguments. From the host, `view.embedded(\"left\")` is the embedded view and its `.viewmodel` the ViewModel. "
            "A relative file is relative to the file that names it.", ""]
    out += _block(view, view.resolve(view.defs["view_node"]), "view node")
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
