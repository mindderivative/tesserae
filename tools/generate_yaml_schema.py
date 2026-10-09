#!/usr/bin/env python3
"""Writes Tesserae's YAML schemas (0.3.2, #79) for Red Hat's YAML language server.

Four JSON Schema draft-07 files, each for one kind of file Tesserae reads:

- `tesserae-yaml-schema.json`       a view, `*_View.yaml`
- `tesserae-theme-schema.json`      a theme or a stylesheet
- `tesserae-component-schema.json`  a component fragment, `*_Component.yaml`
- `tesserae-style-schema.json`      one node's style, `*_Style.yaml`

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
TRE_ENUMS = ("flex_direction", "flex_wrap", "position", "display", "grid_auto_flow")


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
    from tesserae.spec import build, cascade, expand, layout, title_bar

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
    radius = {"anyOf": [number, {"enum": [*sorted(tokens.SHAPES), "full"]}]}
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
        "flex_direction": (enums["flex_direction"], "How its children are laid out: `horizontal` (the default) or `vertical`."),
        "padding": (spacing, "Space inside it: one number, or `{left, right, top, bottom}`."),
        "margin": (spacing, "Space outside it: one number, or `{left, right, top, bottom}`."),
        "gap": ({"type": "number", "minimum": 0}, "Space between its children."),
        "row_gap": ({"type": "number", "minimum": 0}, "Space between rows (defaults to `gap`)."),
        "column_gap": ({"type": "number", "minimum": 0}, "Space between columns (defaults to `gap`)."),
        "align_content": ({"enum": list(layout.POSITIONS)},
                          "Where its children sit: `top_left`, `top`, `top_right`, `left`, `center`, `right`, `bottom_left`, "
                          "`bottom` or `bottom_right`. Not set, they fill the space across the layout."),
        "spread": ({"enum": list(layout.SPREADS)},
                   "Spreads its children along the layout: `between` (the space goes between them), `around` or `evenly`."),
        "flex": ({"enum": list(layout.FLEXES)},
                 "How it takes room in its parent: `none` (the default) is as big as its content and never squeezed, "
                 "`expand_horizontal` and `expand_vertical` take the room left over in that direction, `fill` both."),
        "align_self": ({"enum": list(layout.POSITIONS)}, "Its own place in its parent, over the parent's `align_content`."),
        "align_wrapped": ({"enum": list(layout.ALIGN_TRACKS)},
                          "With `flex_wrap: wrap`: how the lines share the room left over."),
        "align_tracks": ({"enum": list(layout.ALIGN_TRACKS)}, "In a grid: how the tracks share the room left over."),
        "align_cells": ({"enum": list(layout.POSITIONS)}, "In a grid: where each item sits in its cell."),
        "flex_wrap": (enums["flex_wrap"], "`wrap` lets children flow onto more lines; `no_wrap` keeps one."),
        "position": (enums["position"], "`absolute` takes it out of the flow and places it at `x` and `y`."),
        "display": (enums["display"], "`flex` (the default) or `grid`."),
        "grid_auto_flow": (enums["grid_auto_flow"], "How grid children fill the cells."),
        "background": ({"$ref": "#/definitions/fill"},
                       "Its fill: a theme role such as `surface`, `#RRGGBB`, any CSS colour, or a gradient such as "
                       "`linear-gradient(90deg, primary, tertiary)`."),
        "foreground": ({"$ref": "#/definitions/fill"},
                       "Its text or glyph colour: a theme role, `#RRGGBB`, any CSS colour, or a gradient."),
        "border_color": ({"$ref": "#/definitions/fill"}, "The colour of its border: a colour or a gradient."),
        "blur": ({"type": "number", "minimum": 0}, "Blurs the node and what it draws, by this many pixels."),
        "backdrop_blur": ({"type": "number", "minimum": 0},
                          "Blurs what is behind it, by this many pixels: with a translucent `background`, a frosted surface."),
        "blend_mode": ({"enum": ["normal", "multiply", "screen", "overlay", "darken", "lighten", "color_dodge", "color_burn",
                                 "hard_light", "soft_light", "difference", "exclusion", "hue", "saturation", "color",
                                 "luminosity"]},
                       "How it is drawn over what is behind it, as CSS `mix-blend-mode`."),
        "filter": ({"type": "object", "additionalProperties": False,
                    "properties": {name: {"type": "number", "description": text} for name, text in (
                        ("saturate", "1 is unchanged, 0 grey, above 1 more vivid."),
                        ("brightness", "1 is unchanged, 0 black, above 1 brighter."),
                        ("contrast", "1 is unchanged, 0 flat grey, above 1 harder."),
                        ("grayscale", "0 is unchanged, 1 fully grey."),
                        ("hue_rotate", "Turns the hues, in degrees."),
                        ("invert", "0 is unchanged, 1 inverted."),
                        ("sepia", "0 is unchanged, 1 fully sepia."))}},
                   "Colour filters over it and its children, as in CSS: `{grayscale: 1}`, `{saturate: 0.4, brightness: 0.9}` "
                   "(`hue_rotate` is in degrees)."),
        "sticky": ({"type": "number"}, "In a scroll view, it sticks this many pixels from the top edge as its siblings scroll past."),
        "scale": ({"type": "number", "minimum": 0}, "Draws the node and what is in it at this multiple of its size (1 is unchanged), about its centre."),
        "translate_x": ({"type": "number"}, "Draws the node this many pixels to the right of where it is laid out."),
        "translate_y": ({"type": "number"}, "Draws the node this many pixels lower than where it is laid out."),
        "rotation_deg": ({"type": "number"}, "Turns the node by this many degrees, clockwise, about its centre."),
        "transition": ({"type": "object",
                        "description": "Which changes ease instead of jumping.",
                        "properties": {name: {"anyOf": [{"type": "number", "minimum": 0},
                                                         {"type": "object", "additionalProperties": False,
                                                          "properties": {"duration": {"type": "number", "minimum": 0},
                                                                         "easing": {"anyOf": [{"enum": ["linear", "standard", "standard_accelerate", "standard_decelerate",
                                                                                                        "emphasized", "emphasized_accelerate", "emphasized_decelerate", "spring"]},
                                                                                              {"type": "array", "items": {"type": "number"}, "minItems": 4, "maxItems": 4}]},
                                                                         "bounce": {"type": "number", "exclusiveMinimum": -1, "exclusiveMaximum": 1}}}]}
                                       for name in ("all", "background", "foreground", "border_color", "border_width", "corner_radius", "elevation",
                                                    "opacity", "blur", "backdrop_blur", "scale", "translate_x", "translate_y", "rotation_deg")},
                        "additionalProperties": False},
                       "Which style changes ease to their new value: a duration in milliseconds, or `{duration, easing, bounce}`. "
                       "`all` covers every one that can. A node is where it says when first drawn; only a change eases."),
        "zone": ({"enum": ["left", "right", "top", "bottom", "center"]},
                 "A DockPanel's zone in its Dock: where it docks. Only a DockPanel directly in a Dock has one; anywhere else it is an error."),
        "cursor": ({"anyOf": [{"enum": ["default", "pointer", "text", "grab", "grabbing", "move", "not_allowed", "wait",
                                        "progress", "crosshair", "help", "col_resize", "row_resize", "ew_resize", "ns_resize",
                                        "nesw_resize", "nwse_resize", "copy", "cell", "context_menu", "zoom_in", "zoom_out",
                                        "all_scroll"]},
                              {"type": "object", "additionalProperties": False, "required": ["src"],
                               "properties": {"src": {"type": "string", "description": "A PNG (or any picture Pillow reads) next to the view."},
                                              "hotspot": {"type": "array", "items": {"type": "integer"},
                                                          "description": "`[x, y]`: the pixel that is the pointer's place."}}}]},
                   "The pointer over it: a name, or `{src: cursor.png, hotspot: [x, y]}` (a picture next to the view, at most "
                   "256 pixels a side; only in a node's own `style:`)."),
        "border_width": ({"type": "number", "minimum": 0}, "The width of its border, in pixels."),
        "corner_radius": ({"anyOf": [radius, {"type": "array", "items": radius, "minItems": 4, "maxItems": 4},
                                     {"type": "object", "additionalProperties": False,
                                      "properties": {key: {**radius, "description": f"The radius of {what}."} for key, what in (
                                          ("top_left", "the top left corner"), ("top_right", "the top right corner"),
                                          ("bottom_right", "the bottom right corner"), ("bottom_left", "the bottom left corner"),
                                          ("top", "both top corners"), ("right", "both right corners"),
                                          ("bottom", "both bottom corners"), ("left", "both left corners"))}}]},
                          "Pixels, or a shape token (`none` to `extra_large`, or `full` for a pill or circle). Per corner: a list `[top_left, top_right, bottom_right, "
                          "bottom_left]`, or a mapping of corners and edges (`top`, `right`, `bottom`, `left`) with the rest square."),
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
             "properties": {name: {**loose(schema), "description": f"{text} ({cascade.STYLE_GROUP_OF[name]}.)",
                                  "x-group": cascade.STYLE_GROUP_OF[name]}
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
                                     "description": "Where the text sits in its node's width; a `center` or `end` Text with no width fills its parent's. Not for a TextField."}),
                "wrap": loose({"enum": ["word", "none"],
                               "description": "`word` (the default) breaks a line that is too long for its node onto the next; "
                                              "`none` keeps one line. Not for a TextField."}),
                "selectable": loose({"type": "boolean",
                                     "description": "A Text only: the user can select it with the pointer and copy it (Ctrl+C)."}),
                "runs": {"type": "array", "minItems": 1,
                         "description": "A Text only: the text as styled pieces, instead of `content`. A piece is a string, or "
                                        "`{text, color, weight, italic, underline, strikethrough, font_size, font_family, link}`. "
                                        "A piece with a `link` is `primary` and underlined, and a click on it calls `on_link` "
                                        "with `event.href`.",
                         "items": {"anyOf": [{"type": "string"}, {"type": "object", "required": ["text"], "additionalProperties": False,
                                  "properties": {
                                      "text": {"type": "string", "description": "This piece's words."},
                                      "color": {"$ref": "#/definitions/color", "description": "Its colour: a theme role or a CSS colour."},
                                      "weight": {"type": "number", "minimum": 1, "maximum": 1000, "description": "Its font weight."},
                                      "italic": {"type": "boolean", "description": "Italic."},
                                      "underline": {"type": "boolean", "description": "Underlined."},
                                      "strikethrough": {"type": "boolean", "description": "Struck through."},
                                      "font_size": {"type": "number", "exclusiveMinimum": 0, "description": "Its size in pixels."},
                                      "font_family": {"type": "string", "description": "Its font family."},
                                      "link": {"type": "string", "description": "Makes it a link: what `on_link` hears as `event.href`."}}}]}},
                "overflow": loose({"enum": ["clip", "ellipsis"],
                                   "description": "What happens to a line that doesn't fit its node: `clip` (the default) cuts it off, "
                                                  "`ellipsis` ends it with an ellipsis. Not for a TextField."}),
                "max_lines": loose({"type": "integer", "minimum": 1,
                                    "description": "The most lines shown; a longer text is cut there (with `overflow: ellipsis`, the last line ends with "
                                                   "an ellipsis). A Text with a width and no height is as tall as these lines. Not for a TextField."}),
                "letter_spacing": loose({"type": "number",
                                         "description": "Extra space between letters, in pixels (tracking); negative tightens. Not for a TextField."}),
            },
            "additionalProperties": False}
    window_actions = ", ".join("`window." + action + "`" for action in view_module.WINDOW_ACTIONS)
    window_actions += ", " + ", ".join("`surface." + action + "`" for action in view_module.SURFACE_ACTIONS)
    window_actions += ", `navigate.<Screen>`, " + ", ".join("`navigate." + t + "`" for t in view_module.NAVIGATE_TARGETS)
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
                                  "level": {"type": "integer", "minimum": 1, "description": "A heading's level."},
                                  "expanded": {"anyOf": [{"type": "boolean"}, {"type": "null"}, {"type": "string"}],
                                               "description": "Open or closed, on something that opens and closes."},
                                  "selected": {"anyOf": [{"type": "boolean"}, {"type": "null"}, {"type": "string"}], "description": "One of a set, chosen."},
                                  "checked": {"anyOf": [{"type": "boolean"}, {"type": "null"}, {"type": "string"}], "description": "On or off."},
                                  "value": {"anyOf": [{"type": "number"}, {"type": "null"}, {"type": "string"}], "description": "A number the node holds."},
                                  "value_min": {"anyOf": [{"type": "number"}, {"type": "null"}, {"type": "string"}], "description": "Its least."},
                                  "value_max": {"anyOf": [{"type": "number"}, {"type": "null"}, {"type": "string"}], "description": "Its most."},
                                  "value_step": {"anyOf": [{"type": "number"}, {"type": "null"}, {"type": "string"}], "description": "One step."},
                                  "pressed": {"anyOf": [{"type": "boolean"}, {"const": "mixed"}, {"type": "null"}, {"type": "string"}],
                                              "description": "A toggle button's state: true, false or `mixed`."},
                                  "invalid": {"anyOf": [{"type": "boolean"}, {"type": "null"}, {"type": "string"}], "description": "The value is not acceptable."},
                                  "description": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "A longer description than the label."},
                                  "describedby": {"anyOf": [{"type": "string"}, {"type": "array", "items": {"type": "string"}}],
                                                  "description": "The `name:` of a node in this view that describes this one, or a list."},
                                  "controls": {"anyOf": [{"type": "string"}, {"type": "array", "items": {"type": "string"}}],
                                               "description": "The `name:` of a node in this view that this one controls, or a list."},
                                  "current": {"anyOf": [{"type": "boolean"}, {"enum": sorted(a11y.CURRENT)}, {"type": "null"}, {"type": "string"}],
                                              "description": "The current item of a set: `page`, `step`, `location`, `date`, `time` or true."},
                                  "value_now": {"anyOf": [{"type": "number"}, {"type": "null"}, {"type": "string"}], "description": "The value of a range."},
                                  "value_text": {"anyOf": [{"type": "string"}, {"type": "null"}], "description": "How a range's value is said."},
                                  "busy": {"anyOf": [{"type": "boolean"}, {"type": "null"}, {"type": "string"}], "description": "The node is updating."}},
                   "additionalProperties": False}
    style_file = {"type": "string", "pattern": r"_Style\.yaml$", "description": "A `*_Style.yaml` file next to this one."}
    maybe_bool = {"anyOf": [{"type": "boolean"}, {"type": "string"}]}
    maybe_number = {"anyOf": [number, {"type": "string"}]}
    node_props: dict[str, dict[str, Any]] = {
        "id": {"type": "string", "description": "A name for this node, unique in the view. Handlers, bindings and `view.node(id)` use it."},
        "kind": {"enum": sorted(build._KINDS), "description": "What this node is."},
        "classes": {"type": "array", "items": {"type": "string"}, "description": "Style classes a theme or stylesheet rule can match."},
        "style": {"$ref": "#/definitions/style"} if fragment else {"anyOf": [{"$ref": "#/definitions/style"}, style_file],
                                                                   "description": "How a node looks: a mapping, or the name of a `*_Style.yaml` file."},
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
        "svg": {"type": "object", "description": "An Svg's document: a file, or its text.",
                "properties": {"src": {"type": "string", "description": "An SVG file (`.svg` or `.svgz`), relative to this view. "
                                                                          "The pictures it refers to are decoded and found next to it."},
                               "content": {"type": "string", "description": "The SVG document itself, as text."}},
                "additionalProperties": False},
        "canvas": {"type": "object", "description": "A Canvas's drawing commands.",
                   "properties": {"draw": {"type": "array", "description": "Commands painted in order: `rect: [x, y, w, h]`, `circle: [cx, cy, r]` "
                                                                              "or `path: [points]` (with `width`), each with a `color`."}},
                   "additionalProperties": False},
        "scroll": {"type": "object", "description": "A ScrollView's position.",
                   "properties": {"offset": {"type": "number", "minimum": 0, "description": "How far it is scrolled, in pixels."}},
                   "additionalProperties": False},
        "virtual": {"type": "object", "description": "A VirtualList's length: how many rows there are, and how tall each is.",
                    "properties": {"count": {"type": "integer", "minimum": 0, "description": "How many rows the list has."},
                                   "extent": {"type": "number", "exclusiveMinimum": 0, "description": "How tall each row is, in pixels."}},
                    "additionalProperties": False},
        "overlay": {"type": "object", "description": "An Overlay's shape.",
                    "properties": {"modal": {"type": "boolean", "description": "Whether the layer is a scrim over the whole window."}},
                    "additionalProperties": False},
        "icon": {"type": "object", "description": "An Icon's glyph.",
                 "properties": {"name": {**loose({"enum": sorted(icons.ICONS)}), "description": "An icon in Tesserae's set."},
                                "path": {"type": "string", "description": "SVG path data, instead of a name."},
                                "view_box": {"type": "array", "items": {"type": "number"}, "minItems": 4, "maxItems": 4,
                                             "description": "[min_x, min_y, width, height] the path is drawn in (default 0 -960 960 960)."}},
                 "additionalProperties": False},
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
    uncovered = build._NODE_KEYS - set(node_props) - {"children", "embed", "window", "dock", "dock_panel", "split_handle"}  # what `view:`, `Window`, `Dock` and `DockPanel` become, not keys a file has
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
            "buttons": {"type": "array", "uniqueItems": True, "items": {"enum": [*title_bar.BUTTONS, *title_bar.SURFACE_BUTTONS]},
                        "description": "Which window buttons, in order: minimize, maximize, close (all by default); or just "
                                       "`dismiss`, a button that closes the dialog or sheet the bar is in."},
            "children": node_props["children"], "style": node_props["style"], "classes": node_props["classes"],
            "a11y": node_props["a11y"],
        },
        "additionalProperties": False,
        "description": "A window title bar: an icon, a title, your own content and the window's buttons. "
                       "Needs `App(borderless=True)`, or `borderless: true` on a Window.",
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
    view_node = {"type": "object", "required": ["view"], "additionalProperties": False,
                 "description": "Another view shown here: `view: Left_View.yaml` (or a name found in the project). It is a view of its own, "
                                "with its own ids and its own ViewModel if it has one (`Left_ViewModel.py`); one with none is static.",
                 "properties": {
                     "id": node_props["id"],
                     "view": {"type": "string", "description": "The view to show: a `*_View.yaml` next to this file, or a name found in the project."},
                     "with": {"type": "object", "description": "What the embedded view's ViewModel is given, as keyword arguments to its constructor."},
                     "route": {"type": "string", "description": "In the window view, makes the view a screen of the app: its route, "
                                                                "such as `\"\"`, `settings` or `notes/{id}`. A view can be routed once."},
                     "style": node_props["style"], "classes": node_props["classes"], "a11y": node_props["a11y"],
                     "group": node_props["group"], "window_region": node_props["window_region"]}}
    bar_props = {k: v for k, v in title_bar_node["properties"].items() if k != "kind"}
    window_node = {
        "type": "object", "required": ["kind"], "additionalProperties": False,
        "description": "The OS window: the root of a view (there is one per app). Its `title_bar:` is the window's title bar, "
                       "its `children` are the window's content, and `style:`'s `width` and `height` are the window's size.",
        "properties": {
            "id": node_props["id"], "kind": {"const": "Window"},
            "title": {"type": "string", "description": "The window's title."},
            "borderless": {"type": "boolean", "description": "The OS window has no title bar or borders of its own: the "
                                                             "`title_bar:` is the window's."},
            "min_width": {"type": "number", "minimum": 0, "description": "The narrowest the user can resize the window to."},
            "min_height": {"type": "number", "minimum": 0, "description": "The shortest the user can resize the window to."},
            "title_bar": {"anyOf": [{"type": "boolean"}, {"type": "object", "additionalProperties": False, "properties": bar_props}],
                          "description": "The window's title bar, a `TitleBar`'s keys: its `title` is the window's by default, and "
                                         "it has the window buttons when the window is `borderless`."},
            "style": node_props["style"], "classes": node_props["classes"], "a11y": node_props["a11y"],
            "children": node_props["children"]}}
    dock_node = {
        "type": "object", "required": ["kind"], "additionalProperties": False,
        "description": "Panels docked in zones around the middle: its children are `DockPanel`s, each in the zone its `style: {zone: ...}` "
                       "names. There is one Dock per window.",
        "properties": {"id": node_props["id"], "kind": {"const": "Dock"}, "style": node_props["style"], "classes": node_props["classes"],
                       "a11y": node_props["a11y"], "children": node_props["children"]}}
    dock_panel_node = {
        "type": "object", "required": ["kind"], "additionalProperties": False,
        "description": "A panel in a Dock, in the zone its `style: {zone: ...}` says (left, right, top, bottom or center); panels in "
                       "one zone are its tabs. Inside another DockPanel it is a split of it. It holds content or splits, not both.",
        "properties": {"id": node_props["id"], "kind": {"const": "DockPanel"},
                       "title": {"type": "string", "description": "The panel's tab (its id by default)."},
                       "style": node_props["style"], "classes": node_props["classes"], "a11y": node_props["a11y"],
                       "children": node_props["children"]}}
    # Declared here as well as in the branches below, so an editor can suggest them before `kind:`
    # (or `component:`, or `include:`) is typed: the branches only apply once it is.
    suggestible = {**widget_props, **call_props, "include": include_node["properties"]["include"],
                   "view": view_node["properties"]["view"], "title_bar": window_node["properties"]["title_bar"],
                   "borderless": window_node["properties"]["borderless"], "min_width": window_node["properties"]["min_width"],
                   "min_height": window_node["properties"]["min_height"],
                   "title": title_bar_node["properties"]["title"], "buttons": title_bar_node["properties"]["buttons"]}
    suggestible["kind"] = {"enum": sorted([*build._KINDS, "TitleBar", "Window", "Dock", "DockPanel"]), "description": "What this node is."}
    suggestible["title"] = {"type": "string", "description": "A TitleBar's title, or a Window's."}
    # `icon` means an object on an Icon node and a plain name on a TitleBar.
    suggestible["icon"] = {"anyOf": [widget_props["icon"], title_bar_node["properties"]["icon"]],
                           "description": "An Icon's glyph (`{name: ...}`), or a TitleBar's icon name."}
    node = {"type": "object",
            "description": "A node: a widget (`kind:`), a fragment used in place (`component:`), a file put in place (`include:`), or another view (`view:`).",
            "properties": dict(sorted(suggestible.items())),
            "anyOf": [{"required": ["kind"]}, {"required": ["component"]}, {"required": ["include"]}, {"required": ["view"]}],
            "allOf": [
                {"if": {"required": ["component"]}, "then": {"$ref": "#/definitions/component_call"}},
                {"if": {"required": ["include"]}, "then": {"$ref": "#/definitions/include"}},
                {"if": {"required": ["view"]}, "then": {"$ref": "#/definitions/view_node"}},
                {"if": {"required": ["kind"], "properties": {"kind": {"const": "TitleBar"}}},
                 "then": {"$ref": "#/definitions/title_bar"}},
                {"if": {"required": ["kind"], "properties": {"kind": {"const": "Window"}}},
                 "then": {"$ref": "#/definitions/window_node"}},
                {"if": {"required": ["kind"], "properties": {"kind": {"const": "Dock"}}},
                 "then": {"$ref": "#/definitions/dock_node"}},
                {"if": {"required": ["kind"], "properties": {"kind": {"const": "DockPanel"}}},
                 "then": {"$ref": "#/definitions/dock_panel_node"}},
                {"if": {"required": ["kind"], "properties": {"kind": {"not": {"enum": ["TitleBar", "Window", "Dock", "DockPanel"]}}}},
                 "then": {"$ref": "#/definitions/widget"}},
            ]}
    color = {"anyOf": [{"enum": roles}, {"type": "string"}],
             "description": "A theme role (such as `surface` or `on_primary`), `#RGB`, `#RRGGBB`, `#RRGGBBAA`, `transparent`, "
                            "a CSS colour name, or a CSS function such as `rgb(...)` or `oklch(...)`. End any of them with `@N%` to scale its alpha: "
                            "`primary@12%`."}
    gradient = {"anyOf": [{"type": "string", "pattern": r"^\s*(linear|radial|conic)-gradient\("},
                          {"type": "object", "required": ["gradient", "stops"], "additionalProperties": False,
                           "properties": {"gradient": {"enum": ["linear", "radial", "sweep"]},
                                          "stops": {"type": "array", "minItems": 2,
                                                    "description": "Colours, or `[place, colour]` pairs with places from 0 to 1."},
                                          "angle": {"type": "number", "description": "Degrees: 0 up, 90 right, 180 down."},
                                          "center": {"type": "array", "items": {"type": "number"},
                                                     "description": "`[x, y]`, as fractions of the box."},
                                          "radius": {"type": "number"}, "start": {"type": "number"}}}],
                "description": "A CSS-like `linear-gradient(...)`, `radial-gradient(...)` or `conic-gradient(...)` whose stops are "
                               "theme roles or colours, or a mapping with `gradient: linear|radial|sweep` and `stops`."}
    fill = {"anyOf": [{"$ref": "#/definitions/color"}, gradient],
            "description": "A colour (a theme role, a hex or a CSS colour) or a gradient."}
    extra = {"parameter": param, "conditional": conditional} if fragment else {}
    return {**extra, "color": color, "fill": fill, "style": style, "text": text, "handlers": handlers, "a11y": a11y_schema,
            "widget": widget, "title_bar": title_bar_node, "component_call": component_call, "include": include_node,
            "view_node": view_node, "window_node": window_node, "dock_node": dock_node, "dock_panel_node": dock_panel_node,
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

    # A component's stylesheet (`<Name>_Stylesheet.yaml`, 0.3.4) is a stylesheet whose values may be the
    # component's `{{ parameters }}`, so a stylesheet's styles are as loose as a fragment's.
    defs = _only(_definitions(fragment=True), "style", "color", "fill")
    defs["rule"] = {
        "type": "object",
        "description": "Styles for the nodes it matches: by `kind`, by `classes`, or by `id`. With none of the three, for every node.",
        "properties": {"kind": {"enum": sorted(build._KINDS), "description": "Every node of this kind."},
                       "classes": {"type": "array", "items": {"type": "string"}, "description": "Nodes with all of these classes."},
                       "id": {"type": "string", "description": "The node with this id."},
                       "style": {"anyOf": [{"$ref": "#/definitions/style"},
                                           {"type": "string", "pattern": r"_Style\.yaml$", "description": "A `*_Style.yaml` file next to this one."}],
                                 "description": "How the matching nodes look: a mapping, or the name of a `*_Style.yaml` file."}},
        "additionalProperties": False}
    typography = {
        "type": "object", "description": "Changes to Material 3's type styles, by role.",
        "properties": {role: {"type": "object",
                              "properties": {"font_family": {"type": "string", "description": "A font family."},
                                             "font_size": {"type": "number", "description": "Pixels."},
                                             "font_weight": {"type": "number", "description": "1 to 1000."},
                                             "line_height": {"type": "number", "description": "A multiple of the size."},
                                             "tracking": {"type": "number", "description": "Extra space between letters, in pixels (Material 3's tracking: `tokens.MD3_TRACKING`)."}},
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


def _style_file() -> dict[str, Any]:
    defs = _only(_definitions(fragment=False), "style", "color", "fill")
    return _root("tesserae-style-schema.json", "Tesserae style file",
                 "A style file, `*_Style.yaml`: one node's style, shared by the views and rules that name it "
                 "(`style: row_Style.yaml`).",
                 defs, {"type": "object", "required": ["style"], "additionalProperties": False, "properties": {
                     "id": {"type": "string", "description": "A name for the style, such as `row_style`. It is for the reader."},
                     "style": {"$ref": "#/definitions/style", "description": "The style fields, as in a node's `style:`."}}})


def schemas() -> dict[str, dict[str, Any]]:
    return {"tesserae-yaml-schema.json": _view(),
            "tesserae-theme-schema.json": _theme(), "tesserae-component-schema.json": _component(),
            "tesserae-style-schema.json": _style_file()}


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
