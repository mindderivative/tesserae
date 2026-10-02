#!/usr/bin/env python3
"""Writes Tesserae's YAML schemas (0.3.2, #79) for Red Hat's YAML language server.

Four JSON Schema draft-07 files, each for one kind of file Tesserae reads:

- `tesserae-yaml-schema.json`       a view, `*_View.yaml`
- `tesserae-shell-schema.json`      an app shell, `*_Shell.yaml`
- `tesserae-theme-schema.json`      a theme or a stylesheet
- `tesserae-component-schema.json`  a component fragment, `*_Component.yaml`

They are built from Tesserae's own code, so a new kind, style field or
token can't be left out by accident: the kinds, node keys, style fields, the
colour, type and shape tokens, the icons, the accessibility roles, the
handlers, and every built-in fragment's name and parameters. The layout
enums (`flex_direction`, `align_items`, ...) are asked of `tre`, whose error
for a bad value lists the good ones. `tests/test_yaml_schema.py` checks every
YAML file in the repository against them and that the committed files match
what this writes.

    python tools/generate_yaml_schema.py          # write src/tesserae/schema and docs/schema
    python tools/generate_yaml_schema.py --check  # exit 1 if they are out of date
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIRS = (ROOT / "src" / "tesserae" / "schema", ROOT / "docs" / "schema")
SITE = "https://mindderivative.github.io/tesserae/schema/"
DRAFT = "http://json-schema.org/draft-07/schema#"

#: The style fields whose valid values `tre` lists in its errors.
TRE_ENUMS = ("flex_direction", "align_items", "justify_content", "align_self", "justify_items", "justify_self",
             "align_content", "flex_wrap", "position", "display", "grid_auto_flow")


# -- what Tesserae and tre say ---------------------------------------------------------------

def _tre_values(prop: str) -> list[str]:
    """The values `tre` accepts for a node property, from the error it gives for a bad one."""
    from tesserae import App

    window = App(width=10, height=10).window
    try:
        window.create("box", **{prop: "__no_such_value__"})
    except Exception as exc:  # noqa: BLE001 -- the message is what we want
        found = re.search(r"must be one of: (.+)$", str(exc))
        if found:
            return [value.strip() for value in found.group(1).split(",")]
    raise SystemExit(f"tre did not list the values of `{prop}`: has its error message changed?")


def _fragments() -> dict[str, dict[str, Any]]:
    """Every built-in fragment's name and its parameters, each with its default if it has one: an entry
    of `params:` is a name (required) or a one-key `{name: default}` (optional)."""
    from tesserae.spec import expand

    folder = Path(expand.__file__).parent / "components"
    out: dict[str, dict[str, Any]] = {}
    for path in sorted(folder.glob("*_Component.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        params: dict[str, Any] = {}
        for entry in data.get("params") or []:
            if isinstance(entry, str):
                params[entry] = {}
            else:
                name, default = next(iter(entry.items()))
                params[name] = {} if default is None else {"default": default}
        out[path.name.removesuffix("_Component.yaml")] = params
    return out


# -- the building blocks ---------------------------------------------------------------------

def _definitions(fragment: bool) -> dict[str, Any]:
    """The shared definitions. A fragment's numbers and names can be `{{ parameter }}`s, filled in
    when the fragment is used, so there they may also be that."""
    from tesserae import a11y, icons, tokens
    from tesserae import view as view_module
    from tesserae.spec import build, cascade, expand, title_bar

    roles = sorted(tokens.color_scheme((0x67, 0x50, 0xA4, 0xFF)))
    param = {"type": "string", "pattern": r"^\s*\{\{.*\}\}\s*$",
             "description": "A fragment parameter: filled in where the fragment is used."}

    conditional = {"type": "object", "required": ["if", "then"], "additionalProperties": False,
                   "properties": {"if": {}, "then": {}, "else": {}},
                   "description": "A value chosen by a parameter: `{if: \"{{ flag }}\", then: a, else: b}`."}

    def loose(schema: dict[str, Any]) -> dict[str, Any]:
        """In a fragment a value may also be a `{{ parameter }}`, or chosen by one."""
        if not fragment:
            return schema
        return {"anyOf": [schema, {"$ref": "#/definitions/parameter"}, {"$ref": "#/definitions/conditional"}]}

    number = {"type": "number"}
    dimension = {"anyOf": [number, {"enum": ["auto"]}, {"type": "string", "pattern": r"^-?\d+(\.\d+)?%$"}]}
    sides = ("top", "right", "bottom", "left")
    spacing = {"anyOf": [loose(number), {"type": "object", "properties": {side: loose(number) for side in sides},
                                         "additionalProperties": False}]}
    enums = {name: {"enum": _tre_values(name)} for name in TRE_ENUMS}
    size_text = "Pixels, `auto` (its content's size, or stretched), or a percentage of the parent such as `50%`."
    style_fields: dict[str, tuple[dict[str, Any], str]] = {
        "width": (dimension, size_text), "height": (dimension, size_text),
        "min_width": (dimension, "The least width it can take."), "max_width": (dimension, "The most width it can take."),
        "min_height": (dimension, "The least height it can take."), "max_height": (dimension, "The most height it can take."),
        "flex_basis": (dimension, "Its size along the main axis before it grows or shrinks."),
        "flex_direction": (enums["flex_direction"], "How its children are laid out: `horizontal` (the default) or `vertical`."),
        "padding": (spacing, "Space inside it: one number, or `{left, right, top, bottom}`."),
        "margin": (spacing, "Space outside it: one number, or `{left, right, top, bottom}`."),
        "gap": ({"type": "number", "minimum": 0}, "Space between its children."),
        "row_gap": ({"type": "number", "minimum": 0}, "Space between rows (defaults to `gap`)."),
        "column_gap": ({"type": "number", "minimum": 0}, "Space between columns (defaults to `gap`)."),
        "flex_grow": ({"type": "number", "minimum": 0}, "How much of the spare room it takes, relative to its siblings."),
        "flex_shrink": ({"type": "number", "minimum": 0}, "How much it gives up when there is too little room."),
        "align_items": (enums["align_items"], "Where its children sit across the layout axis."),
        "justify_content": (enums["justify_content"], "Where its children sit along the layout axis."),
        "align_self": (enums["align_self"], "Overrides its parent's `align_items` for this node."),
        "justify_items": (enums["justify_items"], "Where grid children sit across their cell's width."),
        "justify_self": (enums["justify_self"], "Where this node sits across its grid cell's width."),
        "align_content": (enums["align_content"], "How wrapped rows, or grid tracks, are spaced."),
        "flex_wrap": (enums["flex_wrap"], "`wrap` lets children flow onto more lines; `no_wrap` keeps one."),
        "position": (enums["position"], "`absolute` takes it out of the flow and places it at `x` and `y`."),
        "display": (enums["display"], "`flex` (the default) or `grid`."),
        "grid_auto_flow": (enums["grid_auto_flow"], "How grid children fill the cells."),
        "background": ({"$ref": "#/definitions/color"}, "Its fill: a theme role such as `surface`, `#RRGGBB`, or any CSS colour."),
        "foreground": ({"$ref": "#/definitions/color"}, "Its text or glyph colour: a theme role, `#RRGGBB`, or any CSS colour."),
        "border_color": ({"$ref": "#/definitions/color"}, "The colour of its border."),
        "border_width": ({"type": "number", "minimum": 0}, "The width of its border, in pixels."),
        "corner_radius": ({"anyOf": [number, {"enum": sorted(tokens.SHAPES)}]}, "Pixels, or a shape token (`none` to `extra_large`)."),
        "opacity": ({"type": "number", "minimum": 0, "maximum": 1}, "From 0 (clear) to 1 (opaque)."),
        "elevation": ({"anyOf": [number, {"enum": sorted(tokens.ELEVATION_LEVELS)}]}, "A shadow level, 0 to 5."),
        "aspect_ratio": ({"type": "number", "exclusiveMinimum": 0}, "Width over height: gives the missing side from the one set."),
        "x": ({"anyOf": [number, {"enum": ["auto"]}]}, "Where an `absolute` node sits from the left."),
        "y": ({"anyOf": [number, {"enum": ["auto"]}]}, "Where an `absolute` node sits from the top."),
        "z_index": ({"type": "integer"}, "Stacking order: higher is in front."),
        "clip_children": ({"type": "boolean"}, "Whether children are cut off at its edge."),
        "grid_template_columns": ({"type": "string"}, "The grid's columns, as in CSS: `1fr 2fr 100px`."),
        "grid_template_rows": ({"type": "string"}, "The grid's rows, as in CSS."),
        "grid_auto_columns": ({"type": "string"}, "The size of columns the template doesn't name."),
        "grid_auto_rows": ({"type": "string"}, "The size of rows the template doesn't name."),
        "grid_column": ({"anyOf": [{"type": "string"}, {"type": "integer"}]}, "Which grid column it takes: `2`, or `1 / 3`."),
        "grid_row": ({"anyOf": [{"type": "string"}, {"type": "integer"}]}, "Which grid row it takes: `2`, or `1 / 3`."),
    }
    missing = cascade.STYLE_FIELDS - set(style_fields)
    extra = set(style_fields) - cascade.STYLE_FIELDS
    if missing or extra:
        raise SystemExit(f"the style fields changed: add {sorted(missing)}, drop {sorted(extra)} in {__file__}")
    style = {"type": "object", "description": "How a node looks and lays out its children.",
             "properties": {name: {**loose(schema), "description": text}
                            for name, (schema, text) in sorted(style_fields.items())},
             "additionalProperties": False}

    text = {"type": "object", "description": "What a Text, Link or TextField says, and in what type.",
            "properties": {
                "content": {"type": "string", "description": "The text."},
                "typography_role": loose({"enum": sorted(tokens.TYPE_SCALE),
                                          "description": "A Material 3 type style: it sets the font, size, weight and line height."}),
                "font_family": {"type": "string", "description": "A font family, such as `Roboto`."},
                "font_size": loose({"type": "number", "exclusiveMinimum": 0, "description": "Pixels."}),
                "font_weight": loose({"type": "number", "minimum": 1, "maximum": 1000,
                                      "description": "1 to 1000; 400 is regular, 700 bold."}),
                "line_height": loose({"type": "number", "exclusiveMinimum": 0, "description": "A multiple of the size."}),
                "text_align": loose({"enum": ["start", "center", "end"],
                                     "description": "Where the text sits in its node's width (0.3.1). Not for a TextField."}),
            },
            "additionalProperties": False}
    window_actions = ", ".join("`window." + action + "`" for action in view_module.WINDOW_ACTIONS)
    handlers = {"type": "object", "description": "What a user's action calls: the name of a ViewModel method, or `window.<action>`.",
                "properties": {name: {"type": "string",
                                      "description": f"Runs on `{event}`: a ViewModel method name, or one of {window_actions}."}
                               for name, event in view_module._EVENTS.items()},
                "additionalProperties": False}
    a11y_schema = {"type": "object", "description": "What assistive technology is told about this node.",
                   "properties": {"label": {"type": "string", "description": "The name a screen reader says."},
                                  "role": {"enum": sorted(a11y.ROLES), "description": "What kind of thing it is."},
                                  "hidden": {"type": "boolean", "description": "Hide it from assistive technology."},
                                  "live": {"enum": sorted(a11y.LIVE), "description": "How changes to it are announced."},
                                  "level": {"type": "integer", "minimum": 1, "description": "A heading's level."}},
                   "additionalProperties": False}
    maybe_bool = {"anyOf": [{"type": "boolean"}, {"type": "string"}]}
    maybe_number = {"anyOf": [number, {"type": "string"}]}
    node_props: dict[str, dict[str, Any]] = {
        "id": {"type": "string", "description": "A name for this node, unique in the view. Handlers, bindings and `view.node(id)` use it."},
        "kind": {"enum": sorted(build._KINDS), "description": "What this node is."},
        "classes": {"type": "array", "items": {"type": "string"}, "description": "Style classes a theme or stylesheet rule can match."},
        "style": {"$ref": "#/definitions/style"},
        "text": {"$ref": "#/definitions/text"},
        "checked": {**maybe_bool, "description": "A Checkbox's state."},
        "selected": {**maybe_bool, "description": "A Switch's or RadioButton's state."},
        "value": {**maybe_number, "description": "A Slider's or SpinBox's value."},
        "hour": {**maybe_number, "description": "A TimePickerDial's hour."},
        "minute": {**maybe_number, "description": "A TimePickerDial's minute."},
        "min": {**maybe_number, "description": "The least a Slider or SpinBox takes."},
        "max": {**maybe_number, "description": "The most a Slider or SpinBox takes."},
        "step": {**maybe_number, "description": "How far a Slider or SpinBox moves."},
        "image": {"type": "object", "description": "An Image's source and fit.",
                  "properties": {"src": {"type": "string", "description": "An image file, relative to this one."},
                                 "fit": {"type": "string", "description": "How it fills its box: `cover` (the default), `contain`, ..."}},
                  "additionalProperties": True},
        "icon": {"type": "object", "description": "An Icon's glyph.",
                 "properties": {"name": {**loose({"enum": sorted(icons.ICONS)}), "description": "An icon in Tesserae's set."}},
                 "required": ["name"], "additionalProperties": False},
        "bindings": {"type": "object", "description": "Properties kept live from the ViewModel: `{{ expression }}`.",
                     "additionalProperties": {"type": "string"}},
        "handlers": {"$ref": "#/definitions/handlers"},
        "two_way": {"type": "string", "description": "The one bound property whose user edits write back to the ViewModel."},
        "interaction": {"anyOf": [{"type": "boolean"},
                                  {"type": "object", "properties": {"color": {"$ref": "#/definitions/color"}},
                                   "additionalProperties": False}],
                        "description": "A Rect or Container's hover, press and focus feedback: `true`, `false`, or `{color: ...}`."},
        "a11y": {"$ref": "#/definitions/a11y"},
        "group": {"type": "string", "description": "A RadioButton's group: the ones with one name exclude each other."},
        "component_of": {"type": "string", "description": "The fragment this node is the root of."},
        "disabled": {**maybe_bool, "description": "Whether the node ignores input and fades."},
        "window_region": {"enum": ["drag", "none"],
                          "description": "`drag`: a press here moves the window (a title bar); `none`: it does not."},
        "label": {"type": "string", "description": "A GraphNode's title."},
        "x": {**maybe_number, "description": "A GraphNode's place."},
        "y": {**maybe_number, "description": "A GraphNode's place."},
        "edges": {"type": "array", "description": "A NodeGraph's edges."},
    }
    if fragment:
        for key in ("style", "text", "bindings", "handlers", "a11y", "interaction"):
            node_props[key] = {"anyOf": [node_props[key], {"$ref": "#/definitions/conditional"}]}
    uncovered = build._NODE_KEYS - set(node_props) - {"children"}
    if uncovered:
        raise SystemExit(f"the node keys changed: add {sorted(uncovered)} in {__file__}")
    node_props["children"] = {"type": "array", "items": {"$ref": "#/definitions/node"},
                              "description": "The nodes inside this one."}
    widget_props = dict(node_props)
    if fragment:
        widget_props["params"] = {
            "type": "array", "description": "The parameters this fragment takes: each `{{ name }}` is filled from `with:`. "
                                            "A name is required; `{name: default}` is optional.",
            "items": {"anyOf": [{"type": "string"}, {"type": "object", "minProperties": 1, "maxProperties": 1}]}}
        widget_props["when"] = {"description": "Keeps this child only when the value is true."}
    widget = {"type": "object", "required": ["id", "kind"], "properties": widget_props, "additionalProperties": False}

    title_bar_node = {
        "type": "object", "required": ["id", "kind"],
        "properties": {
            "id": node_props["id"], "kind": {"const": "TitleBar"},
            "title": {"type": "string", "description": "The window's title."},
            "icon": {"enum": sorted(icons.ICONS), "description": "An icon name, shown before the title."},
            "buttons": {"type": "array", "uniqueItems": True, "items": {"enum": list(title_bar.BUTTONS)},
                        "description": "Which window buttons, in order: minimize, maximize, close (all by default)."},
            "children": node_props["children"], "style": node_props["style"], "classes": node_props["classes"],
            "a11y": node_props["a11y"],
        },
        "additionalProperties": False,
        "description": "A window title bar: an icon, a title, your own content and the window's buttons. "
                       "Needs `App(decorations=False)`.",
    }
    if set(title_bar_node["properties"]) != set(title_bar._KEYS):
        raise SystemExit(f"a TitleBar's keys changed: they are now {sorted(title_bar._KEYS)}; update {__file__}")

    components = _fragments()
    call_props = {key: node_props[key] for key in expand._CALL_KEYS}
    call_props.update({
        "id": node_props["id"],
        "component": {"anyOf": [{"enum": sorted(components)}, {"type": "string"}],
                      "description": "A fragment: one of Tesserae's, or one of your own `<Name>_Component.yaml`."},
        "with": {"type": "object", "description": "The fragment's parameters."},
        "repeat": {"type": "array", "items": {"type": "object"}, "description": "One call per entry, each merged over `with:`."}})
    if fragment:
        call_props["when"] = widget_props["when"]
        call_props["repeat"] = {"anyOf": [call_props["repeat"], {"$ref": "#/definitions/parameter"}],
                                "description": call_props["repeat"]["description"]}
    per_component = []
    for name, params in sorted(components.items()):
        props = dict(params)
        per_component.append({
            "if": {"properties": {"component": {"const": name}}, "required": ["component"]},
            "then": {"properties": {
                "with": {"type": "object", "properties": props, "additionalProperties": False},
                "repeat": loose({"type": "array", "items": {"type": "object", "properties": props,
                                                              "additionalProperties": False}})}},
        })
    component_call = {"type": "object", "required": ["component"], "properties": call_props, "additionalProperties": False,
                      "description": "A fragment used in place: `component: Name` and its `with:` parameters.",
                      "allOf": per_component}
    include_node = {"type": "object", "required": ["include"], "description": "A file's contents, put in place.",
                    "properties": {"include": {"type": "string", "description": "A YAML file, relative to this one."}},
                    "additionalProperties": True}
    # Declared here as well as in the branches below, so an editor can suggest them before `kind:`
    # (or `component:`, or `include:`) is typed: the branches only apply once it is.
    suggestible = {**widget_props, **call_props, "include": include_node["properties"]["include"],
                   "title": title_bar_node["properties"]["title"], "buttons": title_bar_node["properties"]["buttons"]}
    suggestible["kind"] = {"enum": sorted([*build._KINDS, "TitleBar"]), "description": "What this node is."}
    # `icon` means an object on an Icon node and a plain name on a TitleBar.
    suggestible["icon"] = {"anyOf": [widget_props["icon"], title_bar_node["properties"]["icon"]],
                           "description": "An Icon's glyph (`{name: ...}`), or a TitleBar's icon name."}
    node = {"type": "object",
            "description": "A node: a widget (`kind:`), a fragment used in place (`component:`), or a file put in place (`include:`).",
            "properties": dict(sorted(suggestible.items())),
            "anyOf": [{"required": ["kind"]}, {"required": ["component"]}, {"required": ["include"]}],
            "allOf": [
                {"if": {"required": ["component"]}, "then": {"$ref": "#/definitions/component_call"}},
                {"if": {"required": ["include"]}, "then": {"$ref": "#/definitions/include"}},
                {"if": {"required": ["kind"], "properties": {"kind": {"const": "TitleBar"}}},
                 "then": {"$ref": "#/definitions/title_bar"}},
                {"if": {"required": ["kind"], "properties": {"kind": {"not": {"const": "TitleBar"}}}},
                 "then": {"$ref": "#/definitions/widget"}},
            ]}
    color = {"anyOf": [{"enum": roles}, {"type": "string"}],
             "description": "A theme role (such as `surface` or `on_primary`), `#RGB`, `#RRGGBB`, `#RRGGBBAA`, `transparent`, "
                            "a CSS colour name, or a CSS function such as `rgb(...)` or `oklch(...)`."}
    extra = {"parameter": param, "conditional": conditional} if fragment else {}
    return {**extra, "color": color, "style": style, "text": text, "handlers": handlers, "a11y": a11y_schema,
            "widget": widget, "title_bar": title_bar_node, "component_call": component_call, "include": include_node,
            "node": node}


def _only(definitions: dict[str, Any], *names: str) -> dict[str, Any]:
    """The named definitions and everything they refer to."""
    wanted: set[str] = set()
    pending = list(names)
    while pending:
        name = pending.pop()
        if name in wanted:
            continue
        wanted.add(name)
        pending += re.findall(r"#/definitions/(\w+)", json.dumps(definitions[name]))
    return {name: definitions[name] for name in definitions if name in wanted}


def _root(filename: str, title: str, description: str, definitions: dict[str, Any], body: dict[str, Any]) -> dict[str, Any]:
    return {"$schema": DRAFT, "$id": SITE + filename, "title": title, "description": description,
            "definitions": definitions, **body}


# -- the four files --------------------------------------------------------------------------

def _view() -> dict[str, Any]:
    defs = _only(_definitions(fragment=False), "node")
    return _root("tesserae-yaml-schema.json", "Tesserae view",
                 "A Tesserae view: `*_View.yaml`. One node, with its children inside it.",
                 defs, {"type": "object", "allOf": [{"$ref": "#/definitions/node"}]})


def _component() -> dict[str, Any]:
    defs = _only(_definitions(fragment=True), "node")
    return _root("tesserae-component-schema.json", "Tesserae component fragment",
                 "A Tesserae component fragment: `*_Component.yaml`. One node, with `params:` naming the `{{ }}` it fills in.",
                 defs, {"type": "object", "allOf": [{"$ref": "#/definitions/node"}]})


def _theme() -> dict[str, Any]:
    from tesserae import tokens
    from tesserae.spec import build

    defs = _only(_definitions(fragment=False), "style", "color")
    defs["rule"] = {
        "type": "object",
        "description": "Styles for the nodes it matches: by `kind`, by `classes`, or by `id`. With none of the three, for every node.",
        "properties": {"kind": {"enum": sorted(build._KINDS), "description": "Every node of this kind."},
                       "classes": {"type": "array", "items": {"type": "string"}, "description": "Nodes with all of these classes."},
                       "id": {"type": "string", "description": "The node with this id."},
                       "style": {"$ref": "#/definitions/style"}},
        "additionalProperties": False}
    typography = {
        "type": "object", "description": "Changes to Material 3's type styles, by role.",
        "properties": {role: {"type": "object",
                              "properties": {"font_family": {"type": "string", "description": "A font family."},
                                             "font_size": {"type": "number", "description": "Pixels."},
                                             "font_weight": {"type": "number", "description": "1 to 1000."},
                                             "line_height": {"type": "number", "description": "A multiple of the size."}},
                              "additionalProperties": False}
                       for role in sorted(tokens.TYPE_SCALE)},
        "additionalProperties": False}
    colors = {"type": "object", "description": "Colour roles to replace: a role name and a colour.",
              "properties": {role: {"$ref": "#/definitions/color", "description": f"The `{role}` colour."}
                             for role in sorted(tokens.color_scheme((0x67, 0x50, 0xA4, 0xFF)))},
              "additionalProperties": False}
    return _root("tesserae-theme-schema.json", "Tesserae theme or stylesheet",
                 "A theme or stylesheet file: `styles:` rules, and for a theme also a `seed`, `dark`, `colors`, `typography` and `components`.",
                 defs, {"type": "object", "additionalProperties": False, "properties": {
                     "seed": {"$ref": "#/definitions/color", "description": "The colour the theme's palette is made from."},
                     "dark": {"type": "boolean", "description": "Whether it is the dark scheme."},
                     "colors": colors, "typography": typography,
                     "components": {"type": "object", "description": "Per-component shape and elevation."},
                     "styles": {"type": "array", "items": {"$ref": "#/definitions/rule"}, "description": "Style rules, in order."}}})


def _shell() -> dict[str, Any]:
    from tesserae import icons, shell_file

    edges = list(shell_file._EDGES)
    icon = {"enum": sorted(icons.ICONS), "description": "An icon name."}
    # A shell part's style (0.3.3): a node's, but a box with no text to colour has no `foreground`, and a
    # zone's size is its `size`, so its style has no width or height.
    defs = _only(_definitions(fragment=False), "style", "color")
    full = defs["style"]
    part_style = {**full, "properties": {k: v for k, v in full["properties"].items() if k != "foreground"}}
    zone_style = {**part_style, "properties": {k: v for k, v in part_style["properties"].items() if k not in ("width", "height")}}
    definitions = {"color": defs["color"], "style": part_style, "zone_style": zone_style}
    style_ref = {"$ref": "#/definitions/style", "description": "A node's `style:`: `height`, `background`, `padding`, ..."}
    size = {"type": "number", "exclusiveMinimum": 0, "description": "The zone's size in pixels."}
    body = {"type": "object", "additionalProperties": False, "properties": {
        "style": {**style_ref, "description": "The whole shell's style."},
        "top_bar": {"type": "object", "required": ["title"], "additionalProperties": False, "description": "The bar across the top.",
                    "properties": {"title": {"type": "string", "description": "The title shown in the bar."},
                                   "leading_icon": {**icon, "description": "An icon before the title, such as a menu."},
                                   "trailing_icons": {"type": "array", "items": icon, "description": "Icons after the title, as icon buttons."},
                                   "style": style_ref}},
        "navigation": {"type": "object", "required": ["items"], "additionalProperties": False,
                       "description": "A navigation rail of screens.",
                       "properties": {"items": {"type": "array", "minItems": 1, "description": "The screens, in order.", "items": {
                           "type": "object", "required": ["screen", "icon"], "additionalProperties": False,
                           "properties": {"screen": {"type": "string", "description": "A registered screen's name."}, "icon": icon}}},
                                      "on_navigate": {"type": "string",
                                                      "description": "A ViewModel method to call instead of showing the screen."},
                                      "style": style_ref}},
        "status_bar": {"type": "object", "required": ["text"], "additionalProperties": False,
                       "description": "The bar across the bottom.",
                       "properties": {"text": {"type": "string", "description": "The text shown in the bar."}, "style": style_ref}},
        "content": {"type": "object", "additionalProperties": False, "description": "Where the screens show.",
                    "properties": {"style": style_ref}},
        "zones": {"type": "object", "description": "Docked areas around the content: a size in pixels, or `{size, style}`.",
                  "properties": {edge: {"anyOf": [size, {"type": "object", "required": ["size"], "additionalProperties": False,
                                                          "properties": {"size": size, "style": {"$ref": "#/definitions/zone_style"}}}],
                                        "description": f"The {edge} zone: its size in pixels, or `{{size, style}}`."}
                                 for edge in edges},
                  "additionalProperties": False},
        "center": {"type": "boolean", "description": "Whether the middle is a dock zone too, with the screens as its tabs."},
        "panels": {"type": "object", "description": "Which panels (screens) sit in which zone.",
                   "properties": {edge: {"type": "array", "items": {"type": "string"},
                                         "description": f"The panels docked {'in the middle' if edge == 'center' else 'on the ' + edge}, in tab order."}
                                  for edge in [*edges, "center"]},
                   "additionalProperties": False}}}
    return _root("tesserae-shell-schema.json", "Tesserae app shell",
                 "An app shell: `*_Shell.yaml`. A top bar, a navigation rail, a status bar and docked zones around the screens.",
                 definitions, body)


def schemas() -> dict[str, dict[str, Any]]:
    return {"tesserae-yaml-schema.json": _view(), "tesserae-shell-schema.json": _shell(),
            "tesserae-theme-schema.json": _theme(), "tesserae-component-schema.json": _component()}


def render(schema: dict[str, Any]) -> str:
    return json.dumps(schema, indent=2, ensure_ascii=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    parser.add_argument("--check", action="store_true", help="exit 1 if the committed files are out of date")
    args = parser.parse_args(argv)
    stale = []
    for name, schema in schemas().items():
        text = render(schema)
        for folder in OUTPUT_DIRS:
            path = folder / name
            if args.check:
                if not path.exists() or path.read_text(encoding="utf-8") != text:
                    stale.append(path.relative_to(ROOT).as_posix())
            else:
                folder.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
    if args.check and stale:
        print("out of date: " + ", ".join(stale) + " -- run tools/generate_yaml_schema.py", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
