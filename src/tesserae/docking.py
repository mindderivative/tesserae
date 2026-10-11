"""Docking: panels in zones around an app's content -- a file tree
on the left, an inspector on the right -- that the user moves between
zones, on `tre` 0.3.5's bare docking mechanism.

`tre` registers zones (`add_dock_zone`), docks panels (`dock_panel`),
shows one panel per zone (`set_active_panel`) and runs a pointer drag
(`start_panel_drag`), reporting the zone under the pointer (`dock_target`)
and the drop (`dock_drop`). What a drag looks like is the framework's
(`tre` D10), so `Dock` draws it, in MD3's terms (M45 Q2):

- each zone is a column: a strip of MD3 secondary tabs, one per panel,
  over the `tre` zone that shows the selected panel;
- a click or Enter on a tab shows its panel; the left and right arrows
  move along the strip; the strip is one Tab stop, the shown tab;
- dragging a tab (past a few pixels) drags its panel, with MD3's dragged
  state on the tab and a `primary` highlight over the zone under the
  pointer; releasing over no zone leaves the panel where it was;
- `tre`'s drag is pointer-only, so each tab's context menu (a right
  click, the Menu key or Shift+F10) offers "Move to <side>" (`move`).

A `Dock` owns its window's `dock_target`/`dock_drop` events (`window.on`
keeps one listener per event), so a window has one `Dock`.

Split halves (0.5.0, #106): `tre` knows only the five zones, so the `Dock` keeps the
halves of a split as zones of its own (`add_half`): a column of the same tab strip over
the half, which shows one panel at a time (the half's own content is its first tab).
A panel is dropped onto a half, and dragged between halves and zones, like this:

- while a tab is dragged the window root's `pointer_move`s keep arriving with window
  coordinates (a real window checked, KDE Wayland), so the `Dock` finds the half under the
  pointer itself: the outer quarter of a side is that edge (the drop splits the half there,
  which the host does: `on_half_drop`), the rest is the middle (the drop adds the panel
  to the half as a tab). The highlight shows which;
- a tab in a half is not `tre`'s to drag (`tre` knows no such panel), so the `Dock` drags it
  with the pointer captured on the tab, and finds the zone or half under it the same way;
- a half whose last panel leaves, and has no content of its own, is empty (`on_half_empty`):
  the host collapses it into its neighbour.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from tesserae import a11y, tokens
from tesserae.follow import initial_theme
from tesserae.icons import icon_path, icon_view_box
from tesserae.interaction import Interaction
from tesserae.listeners import Listeners, handled
from tesserae.theme import Theme

__all__ = ["DRAG_THRESHOLD", "HALF", "HALF_EDGE", "SIDES", "TAB_HEIGHT", "Dock"]

SIDES = ("left", "right", "top", "bottom", "center")
#: What a half's name is prefixed with to make its zone's key (`HALF + "preview"`), wherever a zone's `side` is taken.
HALF = "half:"
#: MD3's secondary tabs: 48 px, 16 px either side of a `title_small`
#: label, a 2 px indicator the tab's width, a 1 px divider under the strip.
TAB_HEIGHT = 48.0
TAB_PADDING = 16.0
INDICATOR = 2.0
#: A closable tab's close button: 18 px, with 8 px before it.
CLOSE_SIZE = 18.0
CLOSE_ROOM = CLOSE_SIZE + 8.0
#: How far a press must move before it drags the panel, so a click selects.
DRAG_THRESHOLD = 4.0
#: The drop highlight: `primary` at 12% (MD3's pressed/dragged overlay) with a 2 px outline.
HIGHLIGHT_ALPHA = 0x1F
HIGHLIGHT_OUTLINE = 2.0
#: The share of a half, from each side, that is that edge (a drop there splits the half); the rest is its middle.
HALF_EDGE = 0.25


@dataclass
class _Panel:
    node: Any
    title: str
    side: str
    closable: bool = False
    own: Optional[list[Any]] = None  # a half's own content (its nodes; `node` is the half): a tab that cannot be moved or closed


@dataclass
class _Tab:
    node: Any
    label: Any
    indicator: Any
    interaction: Interaction
    undo: list[Callable[[], None]] = field(default_factory=list)


@dataclass
class _Zone:
    side: str
    node: Any  # the column: strip, divider, body
    strip: Any
    divider: Any
    body: Any  # `tre`'s dock zone
    panels: list[_Panel] = field(default_factory=list)
    tabs: list[_Tab] = field(default_factory=list)
    half: bool = False  # a half of a split, not one of `tre`'s zones: it shows its `active` panel itself
    active: Optional[_Panel] = None


class Dock:
    """The docking of one window (see the module doc). `add_zone(side,
    size)` returns the zone's node to place in the layout (the caller
    places them); `add_panel(side, node, title)` docks a panel; `show`,
    `move`, `side_of`, `panels`, `shown`, `titles`, `shown_title`,
    `panel(title)`; `on_move(fn)` hears a panel
    moving, `fn(node, side)`; `set_theme(theme)` re-colours it."""

    def __init__(self, window: Any, *, theme: Optional[Theme] = None) -> None:
        self.window = window
        self.theme = initial_theme(window, theme, self)  # the app's, followed, without one (M50)
        self._events = Listeners()
        self._zones: dict[str, _Zone] = {}
        self._moves: list[Callable[[Any, str], Any]] = []
        self._closes: list[Callable[[Any], Any]] = []
        self._press: Optional[dict[str, Any]] = None
        self._dragging: Optional[_Panel] = None
        self._menu: Any = None
        self._half_drop: Optional[Callable[[Any, str, str], Any]] = None
        self._half_empty: Optional[Callable[[str], Any]] = None
        self._own_drag = False  # a tab of a half is being dragged with the pointer captured (`tre` is not dragging it)
        self._tracking: list[Callable[[], None]] = []  # the root's pointer listeners, while a tab is dragged
        self._pointer: Optional[tuple[float, float]] = None
        self._zone_target: Optional[str] = None
        self._half_target: Optional[tuple[str, str]] = None  # (half, band) under the pointer, or None
        self.highlight = window.create("box", position="absolute", x=0.0, y=0.0, width="100%", height="100%",
                                       stroke_width=HIGHLIGHT_OUTLINE, hit_testable=False, a11y_hidden=True)
        window.on("dock_target", self._on_target)
        window.on("dock_drop", self._on_drop)
        self._paint_highlight()

    # -- zones and panels ----------------------------------------------------

    def add_zone(self, side: str, size: float) -> Any:
        """Creates `side`'s zone -- a tab strip over the area that shows
        its selected panel -- `size` px wide (left, right) or tall (top,
        bottom), or filling what's left (center). Returns its node."""
        if side not in SIDES:
            raise ValueError(f"a dock zone's side is one of {', '.join(SIDES)}, got {side!r}")
        if side in self._zones:
            raise ValueError(f"the dock already has a {side} zone")
        across = {"left": "width", "right": "width", "top": "height", "bottom": "height"}.get(side)
        outer: dict[str, Any] = {"flex_direction": "vertical", "clip_children": True}
        if across is None:
            outer["flex_grow"] = 1.0
        else:
            outer.update({across: float(size), "flex_shrink": 0.0})
        node = self.window.create("box", **outer)
        strip = self.window.create("box", height=TAB_HEIGHT, flex_direction="horizontal", flex_shrink=0.0,
                                   role="tablist", label=f"{side.capitalize()} panels")
        divider = self.window.create("box", height=1.0, flex_shrink=0.0, a11y_hidden=True)
        body = self.window.create("box", flex_grow=1.0, clip_children=True)
        for child in (strip, divider, body):
            node.add_child(child)
        self.window.add_dock_zone(side, body, size=float(size))
        zone = _Zone(side, node, strip, divider, body)
        self._zones[side] = zone
        self._paint_zone(zone)
        return node

    def add_panel(self, side: str, panel: Any, title: str, closable: bool = False) -> Any:
        """Docks `panel` (a node, or a widget's `.node`) in `side`'s zone (or a half: `HALF + name`),
        titled `title` on its tab, and shows it. A `closable` panel's tab has a close button (`on_close`). Returns the node."""
        zone = self._zone(side)
        node = getattr(panel, "node", panel)
        if self._find(node) is not None:
            raise ValueError(f"{title!r} is already docked; use move() to move it")
        if zone.half:
            zone.body.add_child(node)
        else:
            self.window.dock_panel(side, node)
        entry = _Panel(node, title, side, closable)
        zone.panels.append(entry)
        if node.get("role") is None:
            a11y.describe(node, role="tabpanel", label=title)
        self._rebuild(zone)
        if zone.half:
            self._activate(zone, entry)
        return node

    def panels(self, side: str) -> list[Any]:
        """`side`'s panels, in their tabs' order (not a half's own content)."""
        return [p.node for p in self._zone(side).panels if p.own is None]

    def shown(self, side: str) -> Optional[Any]:
        """The panel `side`'s zone is showing, or `None` if it has none."""
        zone = self._zone(side)
        if zone.half:
            return zone.active.node if zone.active is not None else None
        return next((p.node for p in zone.panels if p.node.parent() == zone.body), None)

    def titles(self, side: str) -> list[str]:
        """`side`'s panel titles, in their tabs' order."""
        return [p.title for p in self._zone(side).panels]

    def shown_title(self, side: str) -> Optional[str]:
        """The title of the panel showing in the `side` zone, or `None` if none is."""
        shown = self.shown(side)
        entry = self._find(shown) if shown is not None else None
        return entry.title if entry else None

    def panel(self, title: str) -> Optional[Any]:
        """The docked panel titled `title`, or `None` (for putting a saved layout back)."""
        return next((p.node for z in self._zones.values() for p in z.panels if p.title == title and p.own is None), None)

    def side_of(self, panel: Any) -> Optional[str]:
        """The side `panel` is docked on, or `None` if it isn't docked."""
        entry = self._find(getattr(panel, "node", panel))
        return entry.side if entry else None

    def show(self, panel: Any) -> None:
        """Shows `panel` in its zone."""
        entry = self._find(getattr(panel, "node", panel))
        if entry is None:
            raise ValueError("that panel isn't docked here")
        zone = self._zones[entry.side]
        if zone.half:
            self._activate(zone, entry)
            return
        self.window.set_active_panel(entry.side, zone.panels.index(entry))
        self._paint_tabs(zone)

    def move(self, panel: Any, side: str) -> None:
        """Moves `panel` to `side`'s zone and shows it there, as a drag
        would, moving it between zones."""
        entry = self._require(panel)
        target = self._zone(side)
        if entry.side == side:
            self.show(panel)
            return
        if self._zones[entry.side].half or target.half:
            self._carry(entry, target)
        else:
            self.window.dock_panel(side, entry.node)
        self._moved(entry, side)

    def remove_panel(self, panel: Any) -> Any:
        """Undocks `panel`: its tab goes, and if it was shown the zone
        shows the next panel, else the previous. The node is kept, off the tree, so
        `add_panel` can dock it again. A drag of it is cancelled. Returns
        the node."""
        entry = self._require(panel)
        zone = self._zones[entry.side]
        if zone.half:
            entry.node.set(visible=True)
            entry.node.remove()
        else:
            self.window.undock_panel(entry.node)
        if (self._dragging is entry) or (self._press is not None and self._press["entry"] is entry):
            self._end_drag()
            self._press, self._dragging = None, None
        zone.panels.remove(entry)
        self._rebuild(zone)
        if zone.half:
            self._after_leave(zone, entry)
        return entry.node

    def close(self, panel: Any) -> Any:
        """Closes `panel` as its tab's close button does: it is undocked (see `remove_panel`) and `on_close` is told. Returns the node."""
        node = self.remove_panel(panel)
        for fn in list(self._closes):
            fn(node)
        return node

    def on_close(self, fn: Callable[[Any], Any]) -> Callable[[], None]:
        """Calls `fn(node)` when a panel's close button closes it. Returns the stopper."""
        self._closes.append(fn)
        return lambda: self._closes.remove(fn) if fn in self._closes else None

    def rename(self, panel: Any, title: str) -> None:
        """Gives `panel` a new title, on its tab."""
        entry = self._require(panel)
        entry.title = title
        a11y.describe(entry.node, label=title)
        self._rebuild(self._zones[entry.side])

    def dispose(self) -> None:
        """Stops the dock: its window events, its tabs' listeners. The zones' nodes are the caller's to destroy."""
        self.window.off("dock_target")
        self.window.off("dock_drop")
        for zone in self._zones.values():
            for tab in zone.tabs:
                for undo in tab.undo:
                    undo()
                tab.interaction.detach()
        self._end_drag()
        self._press, self._dragging = None, None

    def on_move(self, fn: Callable[[Any, str], Any]) -> Callable[[], None]:
        """Calls `fn(node, side)` when a panel moves zone. Returns the stopper."""
        self._moves.append(fn)
        return lambda: self._moves.remove(fn) if fn in self._moves else None

    # -- halves ----------------------------------------------------------------------

    def add_half(self, name: str, body: Any, title: Optional[str] = None) -> Any:
        """Makes `body`, a half of a split, a zone of the dock (key `HALF + name`): a column of a tab strip over `body`, put in
        `body`'s place in its parent with `body`'s size (`body` then fills the column). With a `title`, `body`'s content is the
        half's first tab; without one the half has only what is docked in it (`add_panel(HALF + name, ...)`). Returns the column."""
        key = HALF + name
        if key in self._zones:
            raise ValueError(f"the dock already has a half named {name!r}")
        parent = body.parent()
        index = [child == body for child in parent.children()].index(True)
        sizing = {k: body.get(k) for k in ("width", "height", "flex_grow", "flex_shrink", "flex_basis")}
        node = self.window.create("box", flex_direction="vertical", clip_children=True, **sizing)
        strip = self.window.create("box", height=TAB_HEIGHT, flex_direction="horizontal", flex_shrink=0.0,
                                   role="tablist", label=f"{title or name} panels")
        divider = self.window.create("box", height=1.0, flex_shrink=0.0, a11y_hidden=True)
        body.remove()
        parent.insert_child(index, node)
        for child in (strip, divider, body):
            node.add_child(child)
        body.set(width="auto", height="auto", flex_grow=1.0, flex_shrink=1.0, flex_basis="auto", clip_children=True)
        zone = _Zone(key, node, strip, divider, body, half=True)
        self._zones[key] = zone
        if title is not None:
            entry = _Panel(body, title, key, own=list(body.children()))
            zone.panels.append(entry)
            zone.active = entry
        self._rebuild(zone)
        self._paint_zone(zone)
        return node

    def remove_half(self, name: str) -> None:
        """Stops the half being a zone: its tabs and strip go (the column and the body are the caller's; a panel docked in it is not moved)."""
        zone = self._zones.pop(HALF + name, None)
        if zone is None:
            return
        for tab in zone.tabs:
            for undo in tab.undo:
                undo()
            tab.interaction.detach()
            tab.node.destroy()
        zone.tabs = []
        zone.strip.set(visible=False)  # the column stays where it is, round whatever the half has become
        zone.divider.set(visible=False)
        if self._dragging is not None and self._dragging.side == zone.side:
            self._end_drag()
            self._press, self._dragging = None, None

    def half_slot(self, name: str) -> Any:
        """The column `add_half` made for the half `name`: what stands in the half's place in its parent."""
        return self._zone(HALF + name).node

    def half_state(self, name: str) -> tuple[list[Any], Optional[Any]]:
        """`(panels, shown)` of the half `name`: the panels docked in it, in tab order, and the one showing (`None`: its own content)."""
        zone = self._zone(HALF + name)
        shown = zone.active.node if zone.active is not None and zone.active.own is None else None
        return [p.node for p in zone.panels if p.own is None], shown

    def on_half_drop(self, fn: Optional[Callable[[Any, str, str], Any]]) -> None:
        """Lets a dragged panel be dropped onto a half: `fn(panel_node, name, band)` is called with the panel already out of its
        zone or half, `band` being `left`, `right`, `top`, `bottom` (an edge: split the half there) or `middle` (the host docks it
        in the half, as a tab). Without it a half takes no drops. `on_half_drop(None)` stops it."""
        self._half_drop = fn

    def on_half_empty(self, fn: Optional[Callable[[str], Any]]) -> None:
        """Calls `fn(name)` when a half with no content of its own has lost its last panel: the host collapses it."""
        self._half_empty = fn

    def set_theme(self, theme: Theme) -> None:
        """Re-colours the zones, tabs and highlight for `theme`, at once."""
        self.theme = theme
        self._paint_highlight()
        for zone in self._zones.values():
            self._paint_zone(zone)
            for tab in zone.tabs:
                tab.interaction.retint(self._color("on_surface"), self._color("secondary"))

    # -- the tab strip -------------------------------------------------------

    def _rebuild(self, zone: _Zone) -> None:
        for tab in zone.tabs:
            for undo in tab.undo:
                undo()
            tab.interaction.detach()
            tab.node.destroy()
        zone.tabs = [self._tab(zone, entry) for entry in zone.panels]
        self._paint_tabs(zone)

    def _tab(self, zone: _Zone, entry: _Panel) -> _Tab:
        style = tokens.type_style("title_small")
        text_width, text_height = self.window.measure_text(
            entry.title, font_family=style.font_family, font_size=style.font_size,
            font_weight=style.font_weight, line_height=style.line_height)
        text_width, text_height = math.ceil(text_width), math.ceil(text_height)  # the engine rounds a width down
        room = CLOSE_ROOM if entry.closable else 0.0
        node = self.window.create("box", height=TAB_HEIGHT, width=text_width + 2 * TAB_PADDING + room, flex_shrink=0.0,
                                  flex_direction="horizontal", align_items="center", justify_content="center", focusable=True, role="tab",
                                  label=entry.title, cursor="pointer")
        label = self.window.create("text", text=entry.title, font_family=style.font_family,
                                   font_size=style.font_size, font_weight=style.font_weight,
                                   line_height=style.line_height, width=text_width, height=text_height,
                                   hit_testable=False, a11y_hidden=True)
        indicator = self.window.create("box", position="absolute", x=0.0, y=TAB_HEIGHT - INDICATOR, width="100%",
                                       height=INDICATOR, hit_testable=False, a11y_hidden=True)
        node.add_child(label)
        close = None
        if entry.closable:
            close = self.window.create("box", width=CLOSE_SIZE, height=CLOSE_SIZE, corner_radius=CLOSE_SIZE / 2, margin_left=8.0, flex_shrink=0.0,
                                       align_items="center", justify_content="center", focusable=True, role="button",
                                       label=f"Close {entry.title}", cursor="pointer")
            glyph = self.window.create("path", data=icon_path("close"), view_box=icon_view_box("close"), width=14.0, height=14.0,
                                       fill=self._color("on_surface_variant"), hit_testable=False, a11y_hidden=True)
            close.add_child(glyph)
            node.add_child(close)
        node.add_child(indicator)
        zone.strip.add_child(node)
        interaction = Interaction(self.window, node, self._color("on_surface"), self._events.listen,
                                  self._color("secondary"))
        tab = _Tab(node, label, indicator, interaction)
        listen = self._events.listen
        tab.undo = [
            listen(node, "click", handled(lambda e: self.show(entry.node))),
            listen(node, "key_down", lambda e: self._key(e, zone, entry)),
            listen(node, "pointer_down", lambda e: self._down(e, entry, tab)),
            listen(node, "pointer_move", lambda e: self._tab_move(e)),
            listen(node, "pointer_up", lambda e: self._tab_up(True)),
            listen(node, "pointer_cancel", lambda e: self._tab_up(False)),  # the OS took the press (0.3.0 M2)
            listen(node, "secondary_click", handled(lambda e: self._open_menu(entry, at=(e.window_x, e.window_y)))),
        ]
        if close is not None:
            tab.undo.append(listen(close, "click", handled(lambda e: self.close(entry.node))))
        return tab

    def _paint_tabs(self, zone: _Zone) -> None:
        shown = self.shown(zone.side)
        stop = shown if shown is not None else (zone.panels[0].node if zone.panels else None)
        for entry, tab in zip(zone.panels, zone.tabs):
            on = entry.node == shown
            tab.node.set(selected=on, focusable=entry.node == stop)
            tab.label.set(fill=self._color("on_surface" if on else "on_surface_variant"))
            tab.indicator.set(fill=self._color("primary"), visible=on)

    def _key(self, event: Any, zone: _Zone, entry: _Panel) -> None:
        if event.key == "context_menu" or (event.key == "f10" and event.shift):
            self._open_menu(entry)
            return
        step = {"arrow_right": 1, "arrow_left": -1}.get(event.key)
        if step is None or len(zone.panels) < 2:
            return
        target = zone.panels[(zone.panels.index(entry) + step) % len(zone.panels)]
        self.show(target.node)
        zone.tabs[zone.panels.index(target)].node.focus()

    # -- dragging ------------------------------------------------------------

    def _down(self, event: Any, entry: _Panel, tab: _Tab) -> None:
        if event.window_x is not None:
            self._press = {"entry": entry, "tab": tab, "at": (event.window_x, event.window_y)}

    def _tab_move(self, event: Any) -> None:
        if self._own_drag:
            self._own_move(event)
        else:
            self._drag_past_threshold(event)

    def _tab_up(self, released: bool) -> None:
        if self._own_drag:
            self._own_drop(apply=released)
        else:
            self._up()

    def _drag_past_threshold(self, event: Any) -> None:
        press = self._press
        if press is None or self._dragging is not None or event.window_x is None:
            return
        x0, y0 = press["at"]
        if abs(event.window_x - x0) < DRAG_THRESHOLD and abs(event.window_y - y0) < DRAG_THRESHOLD:
            return
        entry = press["entry"]
        if entry.own is not None:  # a half's own content is not a panel that moves
            return
        self._dragging = entry
        press["tab"].interaction.set_dragged(True)
        self._pointer, self._zone_target, self._half_target = (event.window_x, event.window_y), None, None
        if self._zones[entry.side].half:  # `tre` does not know this panel: the tab holds the pointer and Tesserae finds the target
            self._own_drag = True
            press["tab"].node.capture_pointer()
            return
        if self._half_drop is not None and not self._tracking:
            root = self.window.root
            self._tracking = [self._events.listen(root, name, self._track) for name in ("pointer_move", "pointer_up", "pointer_cancel")]
        self.window.start_panel_drag(entry.node)

    def _up(self) -> None:
        if self._dragging is None:  # a click; a drag ends in `dock_drop`
            self._press = None

    def _on_target(self, event: Any) -> None:
        self._zone_target = event.side
        self._show_highlight()

    def _on_drop(self, event: Any) -> None:
        half = self._half_target
        self._end_drag()
        press, self._press, self._dragging = self._press, None, None
        if press is not None:
            press["tab"].interaction.set_dragged(False)
        entry = self._find(event.panel) if event.panel is not None else None
        if half is not None and entry is not None and self._half_drop is not None:
            # `tre` may have moved the panel to the zone it reported; take it out of whichever zone it is in
            self._half_drop(self.remove_panel(entry.node), *half)
            return
        if entry is None or event.side is None or event.side == entry.side or event.side not in self._zones:
            return
        self._moved(entry, event.side)

    # -- dragging a tab of a half --------------------------------------------

    def _own_move(self, event: Any) -> None:
        """The captured tab of a half moved: the half or the zone under the pointer is the target."""
        if event.window_x is None:
            return
        self._pointer = (event.window_x, event.window_y)
        half = self._half_hit(*self._pointer)
        # over a half that takes nothing from this tab (its own, with nothing else in it) is over nothing, not over the zone round it
        zone = None if half is not None or self._over_a_half(*self._pointer) else self._zone_hit(*self._pointer)
        if (half, zone) != (self._half_target, self._zone_target):
            self._half_target, self._zone_target = half, zone
            self._show_highlight()

    def _own_drop(self, *, apply: bool = True) -> None:
        """The captured tab was released (or the OS took the press: `apply` False): the panel goes to the target, or stays."""
        entry, press = self._dragging, self._press
        half, zone = self._half_target, self._zone_target
        if press is not None:
            press["tab"].node.release_pointer()  # before the tab is rebuilt
            press["tab"].interaction.set_dragged(False)
        self._end_drag()
        self._press, self._dragging = None, None
        if entry is None or not apply:
            return
        if half is not None and self._half_drop is not None:
            self._half_drop(self.remove_panel(entry.node), *half)
        elif zone is not None:
            self.move(entry.node, zone)

    def _over_a_half(self, x: float, y: float) -> bool:
        """Whether the point is in any half (strip and all)."""
        for zone in self._zones.values():
            rect = _rect(zone.node) if zone.half else None
            if rect is not None and rect[0] <= x < rect[0] + rect[2] and rect[1] <= y < rect[1] + rect[3]:
                return True
        return False

    def _zone_hit(self, x: float, y: float) -> Optional[str]:
        """The side of the `tre` zone (tab strip and all) the point is in, or `None`."""
        for zone in self._zones.values():
            rect = _rect(zone.node)
            if not zone.half and rect is not None and rect[0] <= x < rect[0] + rect[2] and rect[1] <= y < rect[1] + rect[3]:
                return zone.side
        return None

    # -- the halves under the pointer ----------------------------------------

    def _track(self, event: Any) -> None:
        """A root `pointer_move`/`pointer_up` during a drag: the half under the pointer, and the highlight that says so."""
        if self._dragging is None or event.window_x is None:
            return
        self._pointer = (event.window_x, event.window_y)
        hit = self._half_hit(*self._pointer)
        if hit != self._half_target:
            self._half_target = hit
            self._show_highlight()

    def _half_hit(self, x: float, y: float) -> Optional[tuple[str, str]]:
        """`(half, band)` for the half the point is in (strip and all), or `None`: not a half inside the dragged panel, and not
        the dragged panel's own half unless an edge would still leave something in each of the two. The halves are leaves, so they
        do not overlap."""
        dragged = self._dragging
        if self._half_drop is None or dragged is None:
            return None
        for zone in self._zones.values():
            rect = _rect(zone.node) if zone.half else None
            if rect is None or not zone.node.get("visible") or _inside(zone.node, dragged.node):
                continue
            if rect[0] <= x < rect[0] + rect[2] and rect[1] <= y < rect[1] + rect[3]:
                band = _band(rect, x, y)
                if zone.side == dragged.side and (band == "middle" or len(zone.panels) < 2):
                    return None
                return zone.side[len(HALF):], band
        return None

    def _show_highlight(self) -> None:
        """The highlight over the half band under the pointer, else over the zone being aimed at, else nowhere."""
        if self.highlight.parent() is not None:
            self.highlight.remove()
        if self._half_target is not None:
            name, band = self._half_target
            half = self._zones.get(HALF + name)
            rect = _rect(half.node) if half is not None else None
            if rect is not None:
                self.highlight.set(**_band_box(rect[2], rect[3], band))
                half.node.add_child(self.highlight)
                return
        zone = self._zones.get(self._zone_target) if self._zone_target is not None else None
        if zone is not None:
            self.highlight.set(x=0.0, y=0.0, width="100%", height="100%")
            zone.body.add_child(self.highlight)

    def _end_drag(self) -> None:
        """The drag is over (a drop, or the panel gone): no highlight, no pointer listeners, no target."""
        for undo in self._tracking:
            undo()
        self._tracking = []
        self._own_drag = False
        self._zone_target, self._half_target, self._pointer = None, None, None
        if self.highlight.parent() is not None:
            self.highlight.remove()

    def _activate(self, zone: _Zone, entry: _Panel) -> None:
        """A half shows `entry` -- a panel, or its own content -- and hides the rest."""
        zone.active = entry
        for other in zone.panels:
            for node in other.own if other.own is not None else [other.node]:
                node.set(visible=other is entry)
        self._paint_tabs(zone)

    def _carry(self, entry: _Panel, target: _Zone) -> None:
        """Moves `entry`'s node out of the zone or half it is in and into `target` (a half, or a `tre` zone), as `tre` does for a drop."""
        if self._zones[entry.side].half:
            entry.node.set(visible=True)
            entry.node.remove()
        else:
            self.window.undock_panel(entry.node)
        if target.half:
            target.body.add_child(entry.node)
        else:
            self.window.dock_panel(target.side, entry.node)

    def _after_leave(self, zone: _Zone, left: _Panel) -> None:
        """A panel has left the half `zone`: it shows what is left, and a half with nothing left is the host's to collapse."""
        if zone.active is left or zone.active not in zone.panels:
            zone.active = None
            if zone.panels:
                self._activate(zone, zone.panels[-1])
        if not zone.panels and self._half_empty is not None:
            self._half_empty(zone.side[len(HALF):])

    def _moved(self, entry: _Panel, side: str) -> None:
        """`entry`'s node is now in `side` (a drop `tre` made, or `move`): follow it."""
        old, new = self._zones[entry.side], self._zones[side]
        old.panels.remove(entry)
        entry.side = side
        new.panels.append(entry)
        self._rebuild(old)
        self._rebuild(new)
        if new.half:
            self._activate(new, entry)
        new.tabs[new.panels.index(entry)].node.focus()
        for fn in list(self._moves):
            fn(entry.node, side)
        if old.half:
            self._after_leave(old, entry)

    # -- the "Move to" menu --------------------------------------------------

    def _open_menu(self, entry: _Panel, at: Optional[tuple[Any, Any]] = None) -> None:
        from tesserae.overlays import Menu

        if self._menu is not None:
            self._menu.close()
        if entry.own is not None:
            return
        items = [(f"Move to {self._label(zone)}", lambda side=side: self.move(entry.node, side))
                 for side, zone in self._zones.items() if side != entry.side and not _inside(zone.node, entry.node)]
        if not items:
            return
        self._menu = Menu(self.window, items, theme=self.theme)
        zone = self._zones[entry.side]
        tab = zone.tabs[zone.panels.index(entry)].node
        if at is not None and at[0] is not None:
            self._menu.open_at(at[0], at[1])
        else:
            self._menu.open(tab)

    @staticmethod
    def _label(zone: _Zone) -> str:
        """What "Move to ..." calls a zone: its side, or for a half the titles of what it holds."""
        return " / ".join(p.title for p in zone.panels) if zone.half else zone.side

    # -- painting ------------------------------------------------------------

    def _color(self, role: str) -> tuple[int, int, int, int]:
        scheme = self.theme.roles if self.theme.roles is not None else tokens.baseline_scheme()
        return scheme[role]

    def _paint_zone(self, zone: _Zone) -> None:
        background = self._color("surface" if zone.side == "center" or zone.half else "surface_container_low")
        zone.node.set(fill=background)
        zone.strip.set(fill=background)
        zone.divider.set(fill=self._color("surface_variant"))
        self._paint_tabs(zone)

    def _paint_highlight(self) -> None:
        r, g, b, _ = self._color("primary")
        self.highlight.set(fill=(r, g, b, HIGHLIGHT_ALPHA), stroke_color=(r, g, b, 0xFF))

    # -- lookups -------------------------------------------------------------

    def _zone(self, side: str) -> _Zone:
        if side not in self._zones:
            raise ValueError(f"the dock has no {side} zone (it has {', '.join(self._zones) or 'none'})")
        return self._zones[side]

    def _find(self, node: Any) -> Optional[_Panel]:
        for zone in self._zones.values():
            for entry in zone.panels:
                if entry.node == node:
                    return entry
        return None

    def _require(self, panel: Any) -> _Panel:
        entry = self._find(getattr(panel, "node", panel))
        if entry is None:
            raise ValueError("that panel isn't docked here")
        if entry.own is not None:
            raise ValueError("a half's own content isn't a panel that can be moved, renamed or removed")
        return entry


def _rect(node: Any) -> Optional[tuple[float, float, float, float]]:
    """`node`'s laid-out rectangle in window coordinates (`layout_x`/`layout_y` are window coordinates), or `None` before layout or when it is empty."""
    x, y, w, h = (node.get(k) for k in ("layout_x", "layout_y", "layout_width", "layout_height"))
    if None in (x, y, w, h) or not w or not h:
        return None
    return float(x), float(y), float(w), float(h)


def _inside(node: Any, ancestor: Any) -> bool:
    """Whether `node` is `ancestor` or below it."""
    while node is not None:
        if node == ancestor:
            return True
        node = node.parent()
    return False


def _band(rect: tuple[float, float, float, float], x: float, y: float) -> str:
    """Which part of `rect` the point is in: the nearest side if it is within `HALF_EDGE` of it, else `middle`."""
    rx, ry, rw, rh = rect
    fx, fy = (x - rx) / rw, (y - ry) / rh
    near = {"left": fx, "right": 1.0 - fx, "top": fy, "bottom": 1.0 - fy}
    side = min(near, key=near.__getitem__)
    return side if near[side] < HALF_EDGE else "middle"


def _band_box(width: float, height: float, band: str) -> dict[str, float]:
    """The highlight's box inside a half `width` x `height`: the edge's outer `HALF_EDGE` strip, or the whole half."""
    box = {"x": 0.0, "y": 0.0, "width": width, "height": height}
    if band in ("left", "right"):
        box["width"] = width * HALF_EDGE
        box["x"] = 0.0 if band == "left" else width - box["width"]
    elif band in ("top", "bottom"):
        box["height"] = height * HALF_EDGE
        box["y"] = 0.0 if band == "top" else height - box["height"]
    return box
