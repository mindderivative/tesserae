"""A `kind: Dock` in a view (0.4.4): the zones around the middle, their resize handles, the splits of a panel, built on
`tesserae.docking.Dock` (the tabs and the drag between zones) once the view's nodes exist.

The view built the `Dock` as a container holding its `DockPanel`s as containers. `DockHost` lays the dock out in it:

    left zone | handle | top zone              | handle | right zone
                         handle
                         center zone (or room)
                         handle
                         bottom zone

and docks each panel in its zone, so panels sharing a zone are its tabs and a panel can be dragged to another zone. A zone's size
is what its panel's `style:` said (`width` for left and right, `height` for top and bottom); the handle between a zone and the
middle resizes it (drag it, or focus it and use the arrow keys, Home and End).

A panel's own splits (`DockPanel`s inside a `DockPanel`) have handle nodes between them, made by the spec (`split_handle:`); the
host gives them their behaviour: dragging one resizes the half before it.

Nothing here uses the app shell or the shell file.
"""

from __future__ import annotations

from typing import Any, Callable, Optional

from tesserae import a11y, tokens
from tesserae.docking import Dock
from tesserae.follow import initial_theme
from tesserae.interaction import Interaction
from tesserae.listeners import Listeners
from tesserae.theme import Theme

__all__ = ["DockHost", "MIN_SPLIT", "MIN_ZONE"]

#: A resize handle: a 16 px target holding a 4x48 grip (MD3's drag handle).
HANDLE_SPAN = 16.0
GRIP = (4.0, 48.0)
#: A zone's smallest size and the share of the room it may take; a split half's smallest size; an arrow key's step.
MIN_ZONE = 120.0
MAX_SHARE = 0.7
MIN_SPLIT = 48.0
STEP = 16.0
DEFAULT_SIZE = {"left": 240.0, "right": 240.0, "top": 180.0, "bottom": 180.0}
_EDGE = ("left", "right", "top", "bottom")


class _Handle:
    """A resize handle: pointer capture while dragging, the arrow keys, Home and End. `get`/`put` read and set the size it
    resizes, `bounds` says how far, `grows` is +1 when moving right or down makes it bigger."""

    def __init__(self, host: "DockHost", node: Any, axis: str, label: str, grows: float, get: Callable[[], float],
                 put: Callable[[float], None], bounds: Callable[[], tuple[float, float]]) -> None:
        self.host, self.node, self.axis, self.grows = host, node, axis, grows
        self.get, self.put, self.bounds = get, put, bounds
        horizontal = axis == "x"
        node.set(focusable=True, cursor="col_resize" if horizontal else "row_resize", align_items="center",
                 justify_content="center")
        grip_w, grip_h = GRIP if horizontal else GRIP[::-1]
        self.grip = host.window.create("box", width=grip_w, height=grip_h, corner_radius=2.0, hit_testable=False, a11y_hidden=True)
        node.add_child(self.grip)
        a11y.describe(node, role="slider", label=label, value_step=STEP)
        self.interaction = Interaction(host.window, node, host._color("on_surface"), host._events.listen, host._color("secondary"))
        self._drag: Optional[tuple[float, float]] = None
        for event, fn in (("pointer_down", self._down), ("pointer_move", self._move), ("pointer_up", self._up),
                          ("pointer_cancel", self._up), ("key_down", self._key)):
            host._events.listen(node, event, fn)

    def _at(self, event: Any) -> Optional[float]:
        return event.window_x if self.axis == "x" else event.window_y

    def _down(self, event: Any) -> None:
        at = self._at(event)
        if at is None:
            return
        self._drag = (at, self.get())
        self.node.capture_pointer()
        self.interaction.set_dragged(True)

    def _move(self, event: Any) -> None:
        at = self._at(event)
        if self._drag is None or at is None:
            return
        start, size = self._drag
        self.set(size + self.grows * (at - start))

    def _up(self, event: Any) -> None:
        if self._drag is not None:
            self._drag = None
            self.node.release_pointer()
            self.interaction.set_dragged(False)

    def _key(self, event: Any) -> None:
        size = self.get()
        low, high = self.bounds()
        grow, shrink = ("arrow_right", "arrow_left") if self.axis == "x" else ("arrow_down", "arrow_up")
        if self.grows < 0:
            grow, shrink = shrink, grow
        moves = {grow: size + STEP, shrink: size - STEP, "home": low, "end": high}
        if event.key in moves:
            self.set(moves[event.key])

    def set(self, size: float) -> float:
        low, high = self.bounds()
        size = min(max(float(size), low), high)
        self.put(size)
        self.node.set(value=size, value_min=low, value_max=high)
        return size

    def paint(self) -> None:
        self.grip.set(fill=self.host._color("outline"))
        self.interaction.retint(self.host._color("on_surface"), self.host._color("secondary"))


class DockHost:
    """The dock a `kind: Dock` node is. `dock` is its `tesserae.docking.Dock`; `size(side)`, `set_size(side, size)`,
    `layout()` and `restore(layout)` read and set where the panels are and how big the zones are, as plain data."""

    def __init__(self, view: Any, node_id: str, spec: dict[str, Any]) -> None:
        self.view = view
        self.window = view.window
        self.node_id = node_id
        self.node = view.node(node_id)
        self.theme = initial_theme(self.window, None, self)  # the app's, followed (M50)
        self._events = Listeners()
        self.sizes: dict[str, float] = {}
        self._zones: dict[str, Any] = {}
        self._handles: dict[str, _Handle] = {}
        self._splits: dict[str, _Handle] = {}
        self._split_sizes: dict[str, float] = {}
        self.panels: dict[str, dict[str, Any]] = {}  # a panel's id -> {title, zone, closable}
        self._closed: dict[str, dict[str, Any]] = {}  # the closable panels that are shut: id -> what they were (to open them again)
        self._close_listeners: list[Callable[[list[str]], Any]] = []
        self.dock = Dock(self.window, theme=self.theme)
        self.dock.on_close(self._shut)
        self._build(spec)

    # -- laying out ------------------------------------------------------------------

    def _build(self, spec: dict[str, Any]) -> None:
        panels = spec["panels"]
        sides = [side for side in (*_EDGE, "center") if any(p["zone"] == side for p in panels)]
        create = self.window.create
        nodes = {p["id"]: self.view.node(p["id"]) for p in panels}
        for node in nodes.values():
            if node.parent() is not None:
                node.remove()  # the panels go into their zones
        self.node.set(flex_direction="vertical")
        self.middle = create("box", flex_grow=1.0, flex_direction="horizontal", align_items="stretch", width="100%", height="100%")
        self.centre = create("box", flex_grow=1.0, flex_direction="vertical", align_items="stretch")
        self.node.add_child(self.middle)
        for side in _EDGE:
            if side in sides:
                size = float((spec.get("sizes") or {}).get(side) or DEFAULT_SIZE[side])
                self.sizes[side] = size
                self._zones[side] = self.dock.add_zone(side, size)
                self._handles[side] = self._zone_handle(side)
        if "center" in sides:
            self._zones["center"] = self.dock.add_zone("center", 0.0)
        else:
            self._zones["center"] = create("box", flex_grow=1.0)  # the room the zones around it leave
        self._place("left", self.middle)
        self.middle.add_child(self.centre)
        self._place("right", self.middle)
        self._place("top", self.centre)
        self.centre.add_child(self._zones["center"])
        self._place("bottom", self.centre)
        for panel in panels:
            self.dock.add_panel(panel["zone"], nodes[panel["id"]], panel["title"], bool(panel.get("closable")))
            self.panels[panel["id"]] = {"title": panel["title"], "zone": panel["zone"], "closable": bool(panel.get("closable"))}
        for side in self.dock._zones:  # the first panel of each zone shows, as the file lists them
            first = next((p for p in panels if p["zone"] == side), None)
            if first is not None:
                self.dock.show(nodes[first["id"]])
        self.sync_splits()
        self.paint()

    def _place(self, side: str, parent: Any) -> None:
        if side not in self._handles:
            return
        zone, handle = self._zones[side], self._handles[side].node
        first, second = (zone, handle) if side in ("left", "top") else (handle, zone)
        parent.add_child(first)
        parent.add_child(second)

    def _zone_handle(self, side: str) -> _Handle:
        horizontal = side in ("left", "right")
        node = self.window.create("box", flex_shrink=0.0, **({"width": HANDLE_SPAN} if horizontal else {"height": HANDLE_SPAN}))
        return _Handle(self, node, "x" if horizontal else "y", f"Resize the {side} panels",
                       1.0 if side in ("left", "top") else -1.0, lambda: self.size(side), lambda v: self._put(side, v),
                       lambda: self._bounds(side))

    def _put(self, side: str, size: float) -> None:
        self.sizes[side] = size
        self.dock._zones[side].node.set(**{"width" if side in ("left", "right") else "height": size})

    def _bounds(self, side: str) -> tuple[float, float]:
        area = self.middle if side in ("left", "right") else self.centre
        extent = area.get("layout_width" if side in ("left", "right") else "layout_height") or 0.0
        return MIN_ZONE, max(MIN_ZONE, extent * MAX_SHARE)

    # -- sizes and layouts -----------------------------------------------------------

    def size(self, side: str) -> float:
        """`side`'s zone size in pixels (its width, or its height for top and bottom)."""
        if side not in self.sizes:
            raise ValueError(f"the dock has no {side} zone")
        return self.sizes[side]

    def set_size(self, side: str, size: float) -> float:
        """Sets `side`'s zone size, clamped between 120 px and 70% of the room; returns the size it got."""
        self.size(side)
        return self._handles[side].set(size)

    def layout(self) -> dict[str, Any]:
        """Where each panel is (by title), which one shows, and each zone's size (`None` for the center), as plain data."""
        sides = [*self._handles, *(["center"] if "center" in self.dock._zones else [])]
        return {"zones": {side: {"panels": self.dock.titles(side), "shown": self.dock.shown_title(side),
                                 "size": self.sizes.get(side)} for side in sides},
                "splits": dict(self._split_sizes)}

    def restore(self, layout: dict[str, Any]) -> None:
        """Puts back a `layout()`: moves each titled panel into its zone, shows the one that was shown, sizes the zones and
        the splits. Titles no panel has, and zones this dock hasn't, are skipped."""
        zones = (layout or {}).get("zones") or {}
        known = [*self._handles, *(["center"] if "center" in self.dock._zones else [])]
        for side, saved in zones.items():
            if side not in known:
                continue
            for title in saved.get("panels") or []:
                panel = self.dock.panel(title)
                if panel is not None and self.dock.side_of(panel) != side:
                    self.dock.move(panel, side)
        for side, saved in zones.items():
            if side not in known:
                continue
            shown = self.dock.panel(saved["shown"]) if saved.get("shown") is not None else None
            if shown is not None and self.dock.side_of(shown) == side:
                self.dock.show(shown)
            if saved.get("size") is not None and side in self.sizes:
                self.set_size(side, saved["size"])
        for node_id, size in ((layout or {}).get("splits") or {}).items():
            handle = next((h for h in self._splits.values() if h.before == node_id), None)
            if handle is not None:
                handle.set(size)

    # -- splits ------------------------------------------------------------------------

    def sync_splits(self) -> None:
        """Gives each split handle node of the view its behaviour (once), and takes it from the ones the view no longer has."""
        wanted = {n["id"]: n["split_handle"] for n in self._walk(self.view.spec) if isinstance(n.get("split_handle"), dict)}
        for node_id in [i for i in self._splits if i not in wanted]:
            del self._splits[node_id]
        for node_id, info in wanted.items():
            if node_id in self._splits:
                continue
            node = self.view.node(node_id)
            before = self.view.node(info["before"])
            axis, before_id = info["axis"], info["before"]
            extent = "layout_width" if axis == "x" else "layout_height"
            across = "width" if axis == "x" else "height"
            parent = node.parent()

            def get(before=before, extent=extent) -> float:
                return float(before.get(extent) or 0.0)

            def put(size: float, before=before, across=across, before_id=before_id) -> None:
                before.set(**{across: size, "flex_grow": 0.0, "flex_shrink": 0.0})
                self._split_sizes[before_id] = size

            def bounds(parent=parent, extent=extent) -> tuple[float, float]:
                room = float(parent.get(extent) or 0.0)
                return MIN_SPLIT, max(MIN_SPLIT, room - MIN_SPLIT - HANDLE_SPAN)

            handle = _Handle(self, node, axis, f"Resize {info['before']}", 1.0, get, put, bounds)
            handle.before = before_id  # type: ignore[attr-defined]
            self._splits[node_id] = handle
            if before_id in self._split_sizes:
                handle.set(self._split_sizes[before_id])

    @staticmethod
    def _walk(spec: dict[str, Any]):
        yield spec
        for child in spec.get("children") or []:
            if isinstance(child, dict):
                yield from DockHost._walk(child)

    # -- the host's panels, for a reload -----------------------------------------------

    def add_panel(self, panel_id: str, zone: str, title: str, closable: bool = False) -> None:
        """Docks the view's node `panel_id` in `zone`, titled `title`."""
        if zone not in self.dock._zones:
            raise ValueError(f"the dock has no {zone} zone")
        node = self.view.node(panel_id)
        if node.parent() is not None:
            node.remove()
        self.dock.add_panel(zone, node, title, closable)
        self.panels[panel_id] = {"title": title, "zone": zone, "closable": closable}

    # -- closing and opening a closable panel ------------------------------------------------------------

    def closed(self) -> list[str]:
        """The ids of the closable panels that are shut."""
        return list(self._closed)

    def on_closed(self, fn: Callable[[list[str]], Any]) -> Callable[[], None]:
        """Calls `fn(ids)`, the ids of the panels that are shut, when a close button shuts one. Returns the stopper."""
        self._close_listeners.append(fn)
        return lambda: self._close_listeners.remove(fn) if fn in self._close_listeners else None

    def _shut(self, node: Any) -> None:
        for panel_id, info in list(self.panels.items()):
            if self.view.node(panel_id) == node:
                self._closed[panel_id] = self.panels.pop(panel_id)
        for fn in list(self._close_listeners):
            fn(self.closed())

    def close(self, panel_id: str) -> None:
        """Shuts the closable panel `panel_id` (as its close button does), keeping its node to open it again."""
        if panel_id in self.panels and self.panels[panel_id].get("closable"):
            self._shut_by_id(panel_id)

    def _shut_by_id(self, panel_id: str) -> None:
        node = self.view.node(panel_id)
        if self.dock.side_of(node) is not None:
            self.dock.remove_panel(node)
        self._closed[panel_id] = self.panels.pop(panel_id)

    def reopen(self, panel_id: str) -> None:
        """Docks a shut panel back in the zone it was in, as the last tab."""
        info = self._closed.pop(panel_id, None)
        if info is not None:
            self.add_panel(panel_id, info["zone"], info["title"], info.get("closable", False))

    def sync_closed(self, ids: list[str]) -> None:
        """Shuts the panels in `ids` that are open and opens the shut ones that are not in it (what a bound `closed` list says)."""
        wanted = set(ids)
        for panel_id in list(self._closed):
            if panel_id not in wanted:
                self.reopen(panel_id)
        for panel_id in list(self.panels):
            if panel_id in wanted:
                self.close(panel_id)

    def remove_panel(self, panel_id: str) -> None:
        """Takes the panel out of the dock (its node is the caller's to destroy)."""
        node = self.view.node(panel_id)
        if self.dock.side_of(node) is not None:
            self.dock.remove_panel(node)
        self.panels.pop(panel_id, None)
        self._closed.pop(panel_id, None)

    def retitle(self, panel_id: str, title: str) -> None:
        self.dock.rename(self.view.node(panel_id), title)
        self.panels[panel_id]["title"] = title

    # -- colour --------------------------------------------------------------------------

    def _scheme(self) -> dict[str, Any]:
        return self.theme.roles if self.theme.roles is not None else tokens.baseline_scheme()

    def _color(self, role: str) -> tuple[int, int, int, int]:
        return self._scheme()[role]

    def paint(self) -> None:
        for handle in (*self._handles.values(), *self._splits.values()):
            handle.paint()

    def set_theme(self, theme: Theme) -> None:
        self.theme = theme
        self.dock.set_theme(theme)
        self.paint()

    def _follow_theme(self, theme: Theme, view_theme: dict[str, Any]) -> None:
        self.set_theme(theme)

    def dispose(self) -> None:
        """Stops the dock (the window's dock events, its tabs' and handles' listeners); the view destroys the nodes."""
        self.dock.dispose()
        for handle in (*self._handles.values(), *self._splits.values()):
            handle.interaction.detach()
        self._handles.clear()
        self._splits.clear()
