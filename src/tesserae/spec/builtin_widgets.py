"""The built-in widgets, declared (spec section 16, the part that exists in 0.4.x; phase 3 of #209).

These are the 0.4.x `kind:` values with their properties in the new, flat form: `text: Hello` and `typography_role: title_large` instead of
`text: {content: Hello, typography_role: title_large}`, `icon: home` instead of `icon: {name: home}`. State is a property (`checked`,
`selected`, `value`), never style. The component pass (#118 to #208) adds and merges widgets; each change is a declaration here.

`widgets._load_builtins` imports this module the first time the registry is read.
"""

from __future__ import annotations

from tesserae.spec.widgets import Property as P, declare

_TEXT_ALIGNS = ("start", "center", "end")
_TEXT_WRAPS = ("word", "none")
_TEXT_OVERFLOWS = ("clip", "ellipsis")

declare("Slot", doc="Where a caller's children go in a view (a default slot, or a named one).")
declare("Rect", container=True, doc="A filled box that can hold children.")
declare("Container", container=True, doc="A box with an optional fill that lays out its children.")

_TEXT = {
    "text": P("str", default="", doc="The text shown."),
    "typography_role": P("str", doc="A type role of the theme, such as body_large or title_large."),
    "font_family": P("str"),
    "font_size": P("float"),
    "font_weight": P("any"),
    "wrap": P("enum", choices=_TEXT_WRAPS, default="word", doc="'word' breaks a long line; 'none' never does."),
    "overflow": P("enum", choices=_TEXT_OVERFLOWS, default="clip"),
    "text_align": P("enum", choices=_TEXT_ALIGNS, default="start"),
    "max_lines": P("int", doc="The most lines shown, from 1; a longer text is cut (with `overflow: ellipsis`, an ellipsis ends the last line)."),
    "letter_spacing": P("float", default=0.0, doc="Extra space between letters, in pixels (tracking)."),
}
declare("Text", {**_TEXT, "selectable": P("bool", doc="The text can be selected and copied.")}, extras=("foreground",), doc="A run of text.")
declare("Link", {**_TEXT, "text": P("str", default="", doc="The link's text, which names it for a screen reader.")},
        extras=("foreground",), doc="Text that can be activated.")
declare("TextInput", {
    "text": P("str", default="", model=True, doc="What the user has typed."),
    "placeholder": P("str", default="", doc="Shown, dimmed, while the field is empty."),
    "multiline": P("bool", doc="Several lines; Enter makes a new one."),
    "obscured": P("bool", doc="Shows dots instead of the text, and blocks copy and cut (a password)."),
    "max_length": P("int", default=0, doc="The most characters it takes; 0 is no limit."),
    "read_only": P("bool", doc="The text can be selected and copied but not changed."),
    "mask": P("mask", doc="A pattern the typed text is put in: # a digit, A a letter, * either, \\ a literal; other characters come by themselves."),
    "typography_role": P("str"), "font_family": P("str"), "font_size": P("float"), "font_weight": P("any"), "disabled": P("bool"),
}, extras=("foreground",), doc="A bare text input (the part of a TextField that takes the typing).")
declare("Image", {
    "src": P("str", doc="A path relative to the file."),
    "fit": P("enum", default="cover", choices=("cover", "contain", "fill"), doc="How the picture fills its box."),
    "alt": P("str", doc="What the picture shows, for a screen reader. Without it the picture is decorative and hidden from one."),
    "frame": P("any", doc="A video frame, (rgba, width, height), pushed from a ViewModel."),
}, doc="A picture.")
declare("Icon", {"icon": P("icon", doc="A built-in icon name."),
                 "path": P("str", doc="SVG path data to draw instead of a named icon."),
                 "view_box": P("list", doc="[min_x, min_y, width, height] the path is drawn in; Material Symbols' 0 -960 960 960 when not given.")},
        extras=("foreground",), one_of=[("icon", "path")], doc="A glyph from the built-in set, or from SVG path data.")
declare("Canvas", {"draw": P("list", doc="Drawing commands in order: rect, circle or path, each with a color.")}, doc="A drawing surface: rects, circles and paths from data.")
declare("Svg", {"src": P("str"), "content": P("str", doc="The SVG text, instead of a file.")}, extras=("foreground",), doc="A vector picture.")
declare("ScrollView", {
    "scroll_offset": P("float", default=0.0, model=True, doc="The scrolled distance; scrolling writes it back to a Signal it is bound to."),
    "at_top": P("bool", model=True, doc="Output: whether it is scrolled to the start. Bind a Signal or a state name to read it."),
    "at_end": P("bool", model=True, doc="Output: whether it is scrolled as far as it goes."),
    "scroll_direction": P("str", model=True, doc="Output: 'down' or 'up' for the last scroll, 'none' before the first."),
}, container=True, doc="A scrolling viewport for its children.")

declare("Checkbox", {"checked": P("bool", model=True), "disabled": P("bool")}, doc="A box that is on or off.")
declare("RadioButton", {"selected": P("bool", model=True), "group": P("str", doc="Buttons with one group are exclusive."),
                        "disabled": P("bool")}, doc="One choice of a group.")
declare("Switch", {"selected": P("bool", model=True), "disabled": P("bool")}, doc="A toggle.")
declare("Slider", {"value": P("float", default=0.0, model=True), "disabled": P("bool")}, doc="Picks a value from 0 to 1 by dragging.")
declare("SpinBox", {
    "value": P("float", default=0.0, model=True), "min": P("float"), "max": P("float"), "step": P("float", default=1.0),
    "disabled": P("bool"),
}, doc="A number with step buttons.")
declare("CircularProgress", {"value": P("float", default=0.0, doc="0 to 1; leave out for indeterminate.")}, doc="A progress ring.")
declare("LinearProgress", {"value": P("float", default=0.0, doc="0 to 1; leave out for indeterminate.")}, doc="A progress bar.")
declare("LoadingIndicator", extras=("foreground",), doc="An indeterminate wait indicator.")
declare("TimePickerDial", {"hour": P("float", default=0.0, model=True), "minute": P("float", default=0.0, model=True)},
        doc="The clock face of a time picker.")

declare("NodeGraph", {"edges": P("list", doc="Pairs of node and port names to connect.")}, container=True, doc="A canvas of linked nodes.")
declare("GraphNode", {"label": P("str"), "x": P("float"), "y": P("float")}, container=True, doc="A node of a NodeGraph.")

declare("Window", {
    "title": P("str", required=True, doc="The OS window's title."), "borderless": P("bool", default=False),
    "min_width": P("float"), "min_height": P("float"), "title_bar": P("dict", doc="Title, icon and buttons of a custom title bar."),
}, container=True, doc="The root of an app window.")
declare("TitleBar", {"title": P("str"), "icon": P("icon"), "buttons": P("list")}, container=True, doc="A custom title bar.")
declare("Dock", container=True, doc="Panels docked around a centre.")
declare("DockPanel", {"title": P("str", doc="The panel's tab, when its zone has several.")}, container=True, doc="One panel of a Dock.")
