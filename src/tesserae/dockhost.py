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

A dragged panel can be dropped onto a half (0.5.0, #106; `tesserae.docking.Dock` finds the half and the band under the pointer):
on its middle it joins the half as another panel (`halves()`, `show_in_half`; the half's own content is its first), on an edge
it splits the half there, the panel taking the new half beside it with a handle of its own.

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
        self._halves: dict[str, Any] = {}  # a drop target's name -> its node: the view's leaf halves, and the ones a split made
        self._made_halves: set[str] = set()  # the names of those a drop's split made
        self._half_panels: dict[str, list[str]] = {}  # half -> the ids of the panels dropped into it, in order
        self._half_shown: dict[str, Optional[str]] = {}  # half -> the panel it shows (None: the half's own content)
        self._half_own: dict[str, list[Any]] = {}  # half -> its own content nodes, kept while a dropped panel is shown
        self._made_splits: list[_Handle] = []  # the handles of the splits a drop made
        self._made = 0
        self.panels: dict[str, dict[str, Any]] = {}  # a panel's id -> {title, zone, closable}
        self._closed: dict[str, dict[str, Any]] = {}  # the closable panels that are shut: id -> what they were (to open them again)
        self._close_listeners: list[Callable[[list[str]], Any]] = []
        self.dock = Dock(self.window, theme=self.theme)
        self.dock.on_close(self._shut)
        self.dock.accept_halves(lambda: list(self._halves.items()), self._drop_on_half)
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
            before_id = info["before"]
            handle = self._split_handle(node, info["axis"], f"Resize {before_id}", self.view.node(before_id), node.parent(), before_id)
            self._splits[node_id] = handle
            if before_id in self._split_sizes:
                handle.set(self._split_sizes[before_id])
        self._sync_halves()

    def _split_handle(self, node: Any, axis: str, label: str, before: Any, parent: Any, key: str) -> _Handle:
        """A handle on `node` that resizes `before`, the half in front of it, within `parent`; its size is kept under `key`."""
        extent = "layout_width" if axis == "x" else "layout_height"
        across = "width" if axis == "x" else "height"

        def get() -> float:
            return float(before.get(extent) or 0.0)

        def put(size: float) -> None:
            before.set(**{across: size, "flex_grow": 0.0, "flex_shrink": 0.0})
            self._split_sizes[key] = size

        def bounds() -> tuple[float, float]:
            room = float(parent.get(extent) or 0.0)
            return MIN_SPLIT, max(MIN_SPLIT, room - MIN_SPLIT - HANDLE_SPAN)

        handle = _Handle(self, node, axis, label, 1.0, get, put, bounds)
        handle.before = key  # type: ignore[attr-defined]
        return handle

    @staticmethod
    def _walk(spec: dict[str, Any]):
        yield spec
        for child in spec.get("children") or []:
            if isinstance(child, dict):
                yield from DockHost._walk(child)

    # -- halves: dropping a panel onto one ----------------------------------------------

    def _sync_halves(self) -> None:
        """The drop targets: the view's halves that hold content (not a half that is itself split), and the ones a drop made."""
        leaves = {n["id"] for n in self._walk(self.view.spec)
                  if (n.get("dock_panel") or {}).get("split")
                  and not any((c.get("dock_panel") or {}).get("split") for c in n.get("children") or [] if isinstance(c, dict))}
        self._halves = {**{i: self.view.node(i) for i in leaves}, **{i: n for i, n in self._halves.items() if i in self._made_halves}}

    def halves(self) -> dict[str, dict[str, Any]]:
        """Each drop target's panels (the ids of those dropped into it, in order) and the one it shows (`None`: its own content)."""
        return {name: {"panels": list(self._half_panels.get(name, [])), "shown": self._half_shown.get(name)} for name in self._halves}

    def half_of(self, panel_id: str) -> Optional[str]:
        """The half `panel_id` was dropped into, or `None` if it is in a zone."""
        return (self.panels.get(panel_id) or {}).get("half")

    def show_in_half(self, half: str, panel_id: Optional[str]) -> None:
        """Shows `panel_id` in `half` (`None`: the half's own content, if it has any); the rest of what it holds is hidden."""
        if half not in self._halves:
            raise ValueError(f"the dock has no half {half!r} (it has {', '.join(self._halves) or 'none'})")
        panels = self._half_panels.get(half, [])
        own = self._half_own.get(half, [])
        if panel_id is None and half in self._made_halves:
            raise ValueError(f"{half!r} has no content of its own; show one of its panels")
        if panel_id is not None and panel_id not in panels:
            raise ValueError(f"{panel_id!r} isn't in {half!r}")
        for node in own:
            node.set(visible=panel_id is None)
        for other in panels:
            self.view.node(other).set(visible=other == panel_id)
        self._half_shown[half] = panel_id

    def _drop_on_half(self, node: Any, half: str, band: str) -> None:
        """A dragged panel (already out of its zone) was dropped on `half`'s `band`: on the middle it joins the half, on an edge it
        splits it there."""
        panel_id = next((i for i in self.panels if self.view.node(i) == node), None)
        if panel_id is None or half not in self._halves:
            return
        if band == "middle":
            self._join(half, panel_id)
        else:
            self._split_half(half, band, panel_id)

    def _join(self, half: str, panel_id: str) -> None:
        target = self._halves[half]
        if half not in self._half_own:
            self._half_own[half] = list(target.children())  # the half's own content, before anything else is in it
        node = self.view.node(panel_id)
        target.add_child(node)
        self.panels[panel_id]["half"] = half
        self._half_panels.setdefault(half, []).append(panel_id)
        self.show_in_half(half, panel_id)

    def _split_half(self, half: str, band: str, panel_id: str) -> None:
        """Replaces `half` in its parent with a container holding it and a new half beside it (on `band`'s side) for the panel,
        with a handle between; they share the room the half had."""
        old = self._halves[half]
        parent, window = old.parent(), self.window
        horizontal = band in ("left", "right")
        index = [child == old for child in parent.children()].index(True)
        extent = old.get("layout_width" if horizontal else "layout_height") or 0.0
        sizing = {k: old.get(k) for k in ("width", "height", "flex_grow", "flex_shrink", "flex_basis")}
        both = window.create("box", flex_direction="horizontal" if horizontal else "vertical", clip_children=True, **sizing)
        old.remove()
        parent.insert_child(index, both)
        old.set(width="auto", height="auto", flex_grow=1.0, flex_shrink=1.0, flex_basis="auto")
        self._made += 1
        name = f"{half}.split{self._made}"
        new = window.create("box", flex_grow=1.0, flex_shrink=1.0, clip_children=True)
        new.add_child(self.view.node(panel_id))
        grip = window.create("box", flex_shrink=0.0, **{"width" if horizontal else "height": HANDLE_SPAN})
        first, second = (new, old) if band in ("left", "top") else (old, new)
        for child in (first, grip, second):
            both.add_child(child)
        self._halves[name] = new
        self._made_halves.add(name)
        self._half_panels[name], self._half_own[name], self._half_shown[name] = [panel_id], [], panel_id
        self.panels[panel_id]["half"] = name
        handle = self._split_handle(grip, "x" if horizontal else "y", f"Resize {name}", first, both, name)
        self._made_splits.append(handle)
        if extent:
            handle.set((float(extent) - HANDLE_SPAN) / 2)
        handle.paint()

    def _leave_half(self, panel_id: str) -> None:
        """Takes `panel_id` out of the half it was dropped into (the node is kept, off the tree); the half shows what is left."""
        half = (self.panels.get(panel_id) or {}).pop("half", None)
        if half is None:
            return
        node = self.view.node(panel_id)
        node.set(visible=True)
        if node.parent() is not None:
            node.remove()
        panels = self._half_panels.get(half, [])
        if panel_id in panels:
            panels.remove(panel_id)
        if self._half_shown.get(half) == panel_id and half in self._halves:
            if panels:
                self.show_in_half(half, panels[-1])
            elif half not in self._made_halves:
                self.show_in_half(half, None)

    # -- the host's panels, for a reload -----------------------------------------------

    def add_panel(self, panel_id: str, zone: str, title: str, closable: bool = False) -> None:
        """Docks the view's node `panel_id` in `zone`, titled `title`."""
        if zone not in self.dock._zones:
            raise ValueError(f"the dock has no {zone} zone")
        self._leave_half(panel_id)
        node = self.view.node(panel_id)
        if node.parent() is not None:
            node.remove()
        self.dock.add_panel(zone, node, title, closable)
        self.panels[panel_id] = {"title": title, "zone": zone, "closable": closable}

    def move(self, panel_id: str, zone: str) -> None:
        """Moves the panel `panel_id` to `zone`'s tabs, from another zone or from a half it was dropped into."""
        info = self.panels[panel_id]
        if info.get("half") is not None:
            self.add_panel(panel_id, zone, info["title"], bool(info.get("closable")))
        else:
            self.dock.move(self.view.node(panel_id), zone)
            info["zone"] = zone

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
        self._leave_half(panel_id)
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
        self._leave_half(panel_id)
        if self.dock.side_of(node) is not None:
            self.dock.remove_panel(node)
        self.panels.pop(panel_id, None)
        self._closed.pop(panel_id, None)

    def retitle(self, panel_id: str, title: str) -> None:
        if self.dock.side_of(self.view.node(panel_id)) is not None:
            self.dock.rename(self.view.node(panel_id), title)
        self.panels[panel_id]["title"] = title

    # -- colour --------------------------------------------------------------------------

    def _scheme(self) -> dict[str, Any]:
        return self.theme.roles if self.theme.roles is not None else tokens.baseline_scheme()

    def _color(self, role: str) -> tuple[int, int, int, int]:
        return self._scheme()[role]

    def paint(self) -> None:
        for handle in (*self._handles.values(), *self._splits.values(), *self._made_splits):
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
        for handle in (*self._handles.values(), *self._splits.values(), *self._made_splits):
            handle.interaction.detach()
        self._handles.clear()
        self._splits.clear()
        self._made_splits.clear()
