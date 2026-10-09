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
_DISABLED = {"disabled": P("bool", doc="Dimmed, not focusable, and its handlers do not run.")}
declare("Rect", _DISABLED, container=True, doc="A filled box that can hold children.")
declare("Container", _DISABLED, container=True, doc="A box with an optional fill that lays out its children.")

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
declare("Text", {**_TEXT, "selectable": P("bool", doc="The text can be selected and copied."),
                 "heading": P("int", choices=(1, 2, 3, 4, 5, 6), doc="Makes it a heading of this level for a screen reader.")},
        extras=("foreground",), doc="A run of text.")
declare("Link", {**_TEXT, "text": P("str", default="", doc="The link's text, which names it for a screen reader."),
                 "href": P("str", doc="A web or mail link (http, https, mailto, tel) opened in the OS's browser or mail program when it is activated."),
                 "visited": P("bool", model=True, doc="Whether it has been followed; opening its href sets it, and a rule can show it with `state: visited`."),
                 "disabled": P("bool", doc="Dimmed, and not activated."),
                 "underline": P("enum", choices=("hover", "always", "never"), default="hover", doc="When the text is underlined: while the pointer is over it or it has the keyboard focus, always, or never.")},
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
declare("Svg", {"src": P("str", doc="A .svg or .svgz file, relative to the view."), "content": P("str", doc="The SVG text, instead of a file."),
                "alt": P("str", doc="What the picture shows, for a screen reader. Without it the picture is decorative and hidden from one.")},
        extras=("foreground",), one_of=[("src", "content")], doc="A vector picture.")
declare("ScrollView", {
    "orientation": P("enum", choices=("vertical", "horizontal"), default="vertical", doc="Which way it scrolls. Horizontal lays its children out in a row and `scroll_direction` is 'right' or 'left'."),
    "snap": P("enum", choices=("none", "start", "center", "end"), default="none", doc="When scrolling stops it settles on the nearest child that has a `snap_align` style, with that edge of the child at the same edge of the view."),
    "scroll_offset": P("float", default=0.0, model=True, doc="The scrolled distance; scrolling writes it back to a Signal it is bound to."),
    "at_top": P("bool", model=True, doc="Output: whether it is scrolled to the start. Bind a Signal or a state name to read it."),
    "at_end": P("bool", model=True, doc="Output: whether it is scrolled as far as it goes."),
    "scroll_direction": P("str", model=True, doc="Output: 'down' or 'up' (a horizontal one: 'right' or 'left') for the last scroll, 'none' before the first."),
}, container=True, doc="A scrolling viewport for its children.")

declare("VirtualList", {
    "item_height": P("float", required=True, doc="How tall every row is, in pixels."),
    "overscan": P("int", default=3, doc="Rows built beyond each edge of what is in view."),
    "scroll_offset": P("float", default=0.0, model=True, doc="The scrolled distance; scrolling writes it back to a Signal it is bound to."),
    "at_top": P("bool", model=True, doc="Output: whether it is scrolled to the start."),
    "at_end": P("bool", model=True, doc="Output: whether it is scrolled as far as it goes."),
    "scroll_direction": P("str", model=True, doc="Output: 'down' or 'up' for the last scroll, 'none' before the first."),
}, container=True, doc="A scrolling list of equal rows that builds only the rows in view: its one child is a `for:`.")
declare("Splitter", {
    "orientation": P("enum", choices=("horizontal", "vertical"), default="horizontal", doc="horizontal puts the panes side by side, vertical one above the other."),
    "position": P("float", default=0.5, model=True, doc="How much of the room the first pane has, from 0 to 1. Dragging the handle writes it back to a Signal it is bound to."),
    "min_first": P("float", default=0.0, doc="The least the first pane can be, in pixels."),
    "min_second": P("float", default=0.0, doc="The least the second pane can be, in pixels."),
    "collapsible": P("bool", doc="A double click on the handle closes the first pane, and opens it again."),
    "label": P("str", default="Resize panes", doc="What a screen reader calls the handle."),
}, container=True, doc="Two panes with a draggable, keyboard-operable handle between them.")
declare("Overlay", {
    "open": P("bool", default=False, model=True, doc="Whether it is showing. Closing it (Escape, a press outside) writes false back to a Signal it is bound to."),
    "anchor": P("str", doc="The name of a node in this view to sit against, or `parent` for the node it is written inside; without one it is centred in the window."),
    "placement": P("enum", choices=("below", "above", "start", "end"), default="below", doc="Which side of the anchor; it flips or shifts to fit."),
    "modal": P("bool", doc="Dims the window behind it, blocks input to it, and keeps focus inside."),
    "dismissible": P("bool", default=True, doc="Escape and a press outside close it."),
    "timeout": P("float", default=0.0, doc="Closes itself this many milliseconds after it opens, unless the pointer is over it; 0 never."),
}, container=True, doc="A layer over the window: a menu, a dialog, a popover. `on_dismiss` runs when it closes itself, or the user closes it.")
_CONTROL_LABEL = P("str", doc="Text beside it that is part of what you press, and what a screen reader calls it.")
declare("Checkbox", {"checked": P("bool", model=True, doc="true, false, or empty (null) for a box that is neither: a parent of some checked children."),
                     "disabled": P("bool"), "error": P("bool", doc="Drawn in the error colours."), "label": _CONTROL_LABEL},
        extras=("foreground",), doc="A box that is on or off.")
declare("RadioButton", {"selected": P("bool", model=True), "group": P("str", doc="Buttons with one group are exclusive."),
                        "disabled": P("bool"), "error": P("bool", doc="Drawn in the error colours."), "label": _CONTROL_LABEL},
        extras=("foreground",), doc="One choice of a group.")
declare("Switch", {"selected": P("bool", model=True), "disabled": P("bool"), "label": _CONTROL_LABEL,
                   "icons": P("bool", doc="A check on the handle when on and a cross when off.")}, extras=("foreground",), doc="A toggle.")
declare("Slider", {"value": P("float", default=0.0, model=True, doc="From `min` to `max`; a bound Signal follows the drag."),
                   "min": P("float", default=0.0), "max": P("float", default=1.0),
                   "step": P("float", doc="Snap to multiples of this from `min`; the keys move by it."),
                   "ticks": P("bool", doc="A mark at each step (needs `step`): a discrete slider."),
                   "value_indicator": P("bool", doc="A bubble with the value over the handle while it is dragged or has the keyboard."),
                   "label": P("str", doc="What a screen reader calls it."), "disabled": P("bool")},
        extras=("foreground",), doc="Picks a value between `min` and `max` by dragging.")
declare("SpinBox", {
    "value": P("float", default=0.0, model=True), "min": P("float"), "max": P("float"), "step": P("float", default=1.0),
    "disabled": P("bool"), "label": P("str", doc="What a screen reader calls it."),
    "decimals": P("int", doc="How many decimal places show (empty: only as many as the number needs)."),
    "prefix": P("str", default="", doc="Shown before the number, such as a currency sign."),
    "suffix": P("str", default="", doc="Shown after the number, such as a unit."),
    "wrap": P("bool", doc="A step past one bound lands on the other (needs min and max)."),
}, doc="A number with step buttons. Holding a button repeats the step; Page Up and Page Down step by ten.")
_TRACK = P("str", doc="The colour role of the track behind the indicator.")
declare("CircularProgress", {"value": P("float", doc="0 to 1; leave out, or give nothing, for a wait with no end."), "track": _TRACK,
                             "label": P("str", doc="What a screen reader calls it.")}, extras=("foreground",), doc="A progress ring.")
declare("LinearProgress", {"value": P("float", doc="0 to 1; leave out, or give nothing, for a wait with no end."), "track": _TRACK,
                           "buffer": P("float", doc="0 to 1: how much has loaded, drawn as a lighter bar behind the value."),
                           "stop_indicator": P("bool", doc="A dot at the end of the track (Material 3)."),
                           "label": P("str", doc="What a screen reader calls it.")}, extras=("foreground",), doc="A progress bar.")
declare("LoadingIndicator", {"label": P("str", doc="What a screen reader calls it.")}, extras=("foreground",), doc="An indeterminate wait indicator.")
declare("TimePickerDial", {"hour": P("float", default=0.0, model=True, doc="0 to 23; a press keeps the half of the day it is in."),
                           "minute": P("float", default=0.0, model=True, doc="0 to 59, in fives on the face."),
                           "mode": P("enum", choices=("hour", "minute"), default="hour", model=True,
                                     doc="Which hand the face shows and sets; letting go in hour mode moves on to minutes."),
                           "auto_advance": P("bool", default=True, doc="Letting go in hour mode moves on to the minutes."),
                           "label": P("str", doc="What a screen reader calls it.")},
        doc="The clock face of a time picker.")

declare("NodeGraph", {"edges": P("list", doc="The links: each {from: id, to: id}, the ids of the GraphNodes."),
                      "snap": P("float", default=0.0, doc="A node the user moves lands on a multiple of this many pixels; 0 is no grid."),
                      "arrows": P("bool", doc="Each edge ends in an arrowhead."),
                      "fit": P("bool", doc="Pan and zoom, when it opens, so every node shows (never beyond actual size).")},
        container=True, doc="A canvas of linked nodes you can pan, zoom and move.")
declare("GraphNode", {"label": P("str"), "x": P("float"), "y": P("float")}, container=True, doc="A node of a NodeGraph.")

declare("Window", {
    "title": P("str", required=True, doc="The OS window's title."), "borderless": P("bool", default=False),
    "fullscreen": P("bool", doc="The window fills its monitor, borderless (set when the view loads)."),
    "maximized": P("bool", doc="The window opens maximized."),
    "transparent": P("bool", doc="A see-through window that draws only what the view paints; the OS fixes it before the window opens."),
    "blur_behind": P("bool", doc="The desktop behind a transparent window is blurred (where the compositor does it)."),
    "click_through": P("bool", doc="Clicks go to the window beneath; the window takes none."),
    "min_width": P("float"), "min_height": P("float"), "title_bar": P("dict", doc="Title, icon and buttons of a custom title bar."),
}, container=True, doc="The root of an app window.")
declare("TitleBar", {"title": P("str"), "icon": P("icon"), "buttons": P("list")}, container=True, doc="A custom title bar.")
declare("Dock", {"closed": P("list", model=True, doc="The names of the closable panels that are shut; a close button adds its panel, and taking a name out opens the panel again.")},
        container=True, doc="Panels docked around a centre.")
declare("DockPanel", {"title": P("str", doc="The panel's tab, when its zone has several."),
                      "closable": P("bool", doc="Its tab has a close button.")}, container=True, doc="One panel of a Dock.")
