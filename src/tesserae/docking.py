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
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from tesserae import a11y, tokens
from tesserae.follow import initial_theme
from tesserae.interaction import Interaction
from tesserae.listeners import Listeners, handled
from tesserae.theme import Theme

__all__ = ["DRAG_THRESHOLD", "SIDES", "TAB_HEIGHT", "Dock"]

SIDES = ("left", "right", "top", "bottom", "center")
#: MD3's secondary tabs: 48 px, 16 px either side of a `title_small`
#: label, a 2 px indicator the tab's width, a 1 px divider under the strip.
TAB_HEIGHT = 48.0
TAB_PADDING = 16.0
INDICATOR = 2.0
#: How far a press must move before it drags the panel, so a click selects.
DRAG_THRESHOLD = 4.0
#: The drop highlight: `primary` at 12% (MD3's pressed/dragged overlay) with a 2 px outline.
HIGHLIGHT_ALPHA = 0x1F
HIGHLIGHT_OUTLINE = 2.0


@dataclass
class _Panel:
    node: Any
    title: str
    side: str


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


class Dock:
    """The docking of one window (see the module doc). `add_zone(side,
    size)` returns the zone's node to place in the layout (an `AppShell`
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
        self._press: Optional[dict[str, Any]] = None
        self._dragging: Optional[_Panel] = None
        self._menu: Any = None
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

    def add_panel(self, side: str, panel: Any, title: str) -> Any:
        """Docks `panel` (a node, or a widget's `.node`) in `side`'s zone,
        titled `title` on its tab, and shows it. Returns the node."""
        zone = self._zone(side)
        node = getattr(panel, "node", panel)
        if self._find(node) is not None:
            raise ValueError(f"{title!r} is already docked; use move() to move it")
        self.window.dock_panel(side, node)
        zone.panels.append(_Panel(node, title, side))
        if node.get("role") is None:
            a11y.describe(node, role="tabpanel", label=title)
        self._rebuild(zone)
        return node

    def panels(self, side: str) -> list[Any]:
        """`side`'s panels, in their tabs' order."""
        return [p.node for p in self._zone(side).panels]

    def shown(self, side: str) -> Optional[Any]:
        """The panel `side`'s zone is showing, or `None` if it has none."""
        zone = self._zone(side)
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
        """The docked panel titled `title`, or `None` (for `AppShell.restore`)."""
        return next((p.node for z in self._zones.values() for p in z.panels if p.title == title), None)

    def side_of(self, panel: Any) -> Optional[str]:
        """The side `panel` is docked on, or `None` if it isn't docked."""
        entry = self._find(getattr(panel, "node", panel))
        return entry.side if entry else None

    def show(self, panel: Any) -> None:
        """Shows `panel` in its zone."""
        entry = self._require(panel)
        zone = self._zones[entry.side]
        self.window.set_active_panel(entry.side, zone.panels.index(entry))
        self._paint_tabs(zone)

    def move(self, panel: Any, side: str) -> None:
        """Moves `panel` to `side`'s zone and shows it there, as a drag
        would, moving it between zones."""
        entry = self._require(panel)
        self._zone(side)
        if entry.side == side:
            self.show(panel)
            return
        self.window.dock_panel(side, entry.node)
        self._moved(entry, side)

    def remove_panel(self, panel: Any) -> Any:
        """Undocks `panel`: its tab goes, and if it was shown the zone
        shows the next panel, else the previous. The node is kept, off the tree, so
        `add_panel` can dock it again. A drag of it is cancelled. Returns
        the node."""
        entry = self._require(panel)
        zone = self._zones[entry.side]
        self.window.undock_panel(entry.node)
        if (self._dragging is entry) or (self._press is not None and self._press["entry"] is entry):
            if self.highlight.parent() is not None:
                self.highlight.remove()
            self._press, self._dragging = None, None
        zone.panels.remove(entry)
        self._rebuild(zone)
        return entry.node

    def on_move(self, fn: Callable[[Any, str], Any]) -> Callable[[], None]:
        """Calls `fn(node, side)` when a panel moves zone. Returns the stopper."""
        self._moves.append(fn)
        return lambda: self._moves.remove(fn) if fn in self._moves else None

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
        node = self.window.create("box", height=TAB_HEIGHT, width=text_width + 2 * TAB_PADDING, flex_shrink=0.0,
                                  align_items="center", justify_content="center", focusable=True, role="tab",
                                  label=entry.title, cursor="pointer")
        label = self.window.create("text", text=entry.title, font_family=style.font_family,
                                   font_size=style.font_size, font_weight=style.font_weight,
                                   line_height=style.line_height, width=text_width, height=text_height,
                                   hit_testable=False, a11y_hidden=True)
        indicator = self.window.create("box", position="absolute", x=0.0, y=TAB_HEIGHT - INDICATOR, width="100%",
                                       height=INDICATOR, hit_testable=False, a11y_hidden=True)
        node.add_child(label)
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
            listen(node, "pointer_move", lambda e: self._drag_past_threshold(e)),
            listen(node, "pointer_up", lambda e: self._up()),
            listen(node, "pointer_cancel", lambda e: self._up()),  # the OS took the press (0.3.0 M2)
            listen(node, "secondary_click", handled(lambda e: self._open_menu(entry, at=(e.window_x, e.window_y)))),
        ]
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

    def _drag_past_threshold(self, event: Any) -> None:
        press = self._press
        if press is None or self._dragging is not None or event.window_x is None:
            return
        x0, y0 = press["at"]
        if abs(event.window_x - x0) < DRAG_THRESHOLD and abs(event.window_y - y0) < DRAG_THRESHOLD:
            return
        self._dragging = press["entry"]
        press["tab"].interaction.set_dragged(True)
        self.window.start_panel_drag(press["entry"].node)

    def _up(self) -> None:
        if self._dragging is None:  # a click; a drag ends in `dock_drop`
            self._press = None

    def _on_target(self, event: Any) -> None:
        if self.highlight.parent() is not None:
            self.highlight.remove()
        zone = self._zones.get(event.side) if event.side is not None else None
        if zone is not None:
            zone.body.add_child(self.highlight)

    def _on_drop(self, event: Any) -> None:
        if self.highlight.parent() is not None:
            self.highlight.remove()
        press, self._press, self._dragging = self._press, None, None
        if press is not None:
            press["tab"].interaction.set_dragged(False)
        entry = self._find(event.panel) if event.panel is not None else None
        if entry is None or event.side is None or event.side == entry.side or event.side not in self._zones:
            return
        self._moved(entry, event.side)

    def _moved(self, entry: _Panel, side: str) -> None:
        """`tre` has moved `entry` to `side` (a drop, or `move`): follow it."""
        old, new = self._zones[entry.side], self._zones[side]
        old.panels.remove(entry)
        entry.side = side
        new.panels.append(entry)
        self._rebuild(old)
        self._rebuild(new)
        new.tabs[new.panels.index(entry)].node.focus()
        for fn in list(self._moves):
            fn(entry.node, side)

    # -- the "Move to" menu --------------------------------------------------

    def _open_menu(self, entry: _Panel, at: Optional[tuple[Any, Any]] = None) -> None:
        from tesserae.overlays import Menu

        if self._menu is not None:
            self._menu.close()
        items = [(f"Move to {side}", lambda side=side: self.move(entry.node, side))
                 for side in self._zones if side != entry.side]
        if not items:
            return
        self._menu = Menu(self.window, items, theme=self.theme)
        zone = self._zones[entry.side]
        tab = zone.tabs[zone.panels.index(entry)].node
        if at is not None and at[0] is not None:
            self._menu.open_at(at[0], at[1])
        else:
            self._menu.open(tab)

    # -- painting ------------------------------------------------------------

    def _color(self, role: str) -> tuple[int, int, int, int]:
        scheme = self.theme.roles if self.theme.roles is not None else tokens.baseline_scheme()
        return scheme[role]

    def _paint_zone(self, zone: _Zone) -> None:
        background = self._color("surface" if zone.side == "center" else "surface_container_low")
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
        return entry
