"""The app shell (M45): the frame around an app's screens -- a top app bar,
navigation, docked panels around the content, and a status bar -- what
`tre` 0.3.4's `build_shell` did, which 0.3.5 leaves to the framework.

    shell = AppShell(app.window, top_bar=bar, navigation=rail, status_bar=status,
                     zones={"left": 240, "right": 280, "bottom": 180})
    shell.dock.add_panel("left", files, "Files")
    app.use_shell(shell)  # screens now show in shell.content

The shell fills the window and follows it as it resizes: the side zones
keep their size and the content takes the rest. Each zone has a resize
handle between it and the content (MD3's drag handle, as M42's splitter
draws it): drag it, or focus it and use the arrow keys (16 px), Home and
End. `layout()` returns where every panel is and how big each zone is, as
plain data an app can save; `restore(layout)` puts it back (M45 Q4).

`center=True` makes the middle a dock zone too, as an IDE's editor area
is: `App.use_shell` then shows each screen as a tab there, titled by its
name -- `show(name)` docks it the first time and brings its tab forward
after -- so screens stay open side by side, and can be dragged out to an
edge zone like any panel. Without it, `content` shows one screen at a time.
"""

from __future__ import annotations

from typing import Any, Optional

from tesserae import a11y, tokens
from tesserae.docking import Dock
from tesserae.follow import initial_theme
from tesserae.interaction import Interaction
from tesserae.listeners import Listeners
from tesserae.theme import Theme

__all__ = ["HANDLE_SPAN", "MIN_ZONE", "STEP", "AppShell"]

#: The resize handle: a 16 px target holding MD3's 4x48 drag handle (M42's splitter's).
HANDLE_SPAN = 16.0
GRIP = (4.0, 48.0)
#: A zone's smallest size, and how far an arrow key moves its handle.
MIN_ZONE = 120.0
STEP = 16.0
#: A zone may take at most this share of the area it sits in.
MAX_SHARE = 0.7
_EDGE = ("left", "right", "top", "bottom")


class _Handle:
    """A resize handle for one zone: dragging it (with pointer capture), the
    arrow keys, Home and End set the zone's size, clamped."""

    def __init__(self, shell: "AppShell", side: str) -> None:
        self.shell, self.side = shell, side
        window = shell.window
        horizontal = side in ("left", "right")
        across = {"width": HANDLE_SPAN} if horizontal else {"height": HANDLE_SPAN}
        self.node = window.create("box", flex_shrink=0.0, align_items="center", justify_content="center",
                                  focusable=True, cursor="col_resize" if horizontal else "row_resize", **across)
        grip_w, grip_h = GRIP if horizontal else GRIP[::-1]
        self.grip = window.create("box", width=grip_w, height=grip_h, corner_radius=2.0, hit_testable=False,
                                  a11y_hidden=True)
        self.node.add_child(self.grip)
        a11y.describe(self.node, role="slider", label=f"Resize the {side} panels", value_step=STEP)
        self.interaction = Interaction(window, self.node, shell._color("on_surface"), shell._events.listen,
                                       shell._color("secondary"))
        self._drag: Optional[tuple[float, float]] = None
        listen = shell._events.listen
        for event, fn in (("pointer_down", self._down), ("pointer_move", self._move), ("pointer_up", self._up),
                          ("pointer_cancel", self._up), ("key_down", self._key)):  # cancel: the OS took the press
            listen(self.node, event, fn)

    def _axis(self, event: Any) -> Optional[float]:
        return event.window_x if self.side in ("left", "right") else event.window_y

    def _down(self, event: Any) -> None:
        at = self._axis(event)
        if at is None:
            return
        self._drag = (at, self.shell.size(self.side))
        self.node.capture_pointer()
        self.interaction.set_dragged(True)

    def _move(self, event: Any) -> None:
        at = self._axis(event)
        if self._drag is None or at is None:
            return
        start, size = self._drag
        grows = 1.0 if self.side in ("left", "top") else -1.0  # a right or bottom zone grows as its handle moves back
        self.shell.set_size(self.side, size + grows * (at - start))

    def _up(self, event: Any) -> None:
        if self._drag is not None:
            self._drag = None
            self.node.release_pointer()
            self.interaction.set_dragged(False)

    def _key(self, event: Any) -> None:
        size = self.shell.size(self.side)
        low, high = self.shell._bounds(self.side)
        grow, shrink = {"left": ("arrow_right", "arrow_left"), "right": ("arrow_left", "arrow_right"),
                        "top": ("arrow_down", "arrow_up"), "bottom": ("arrow_up", "arrow_down")}[self.side]
        moves = {grow: size + STEP, shrink: size - STEP, "home": low, "end": high}
        if event.key in moves:
            self.shell.set_size(self.side, moves[event.key])

    def paint(self) -> None:
        self.grip.set(fill=self.shell._color("outline"))
        self.interaction.retint(self.shell._color("on_surface"), self.shell._color("secondary"))


class AppShell:
    """An app's frame: `top_bar`, `navigation` and `status_bar` (widgets or
    nodes, placed as they are), a `Dock` (`dock=`, or a new one) whose
    zones -- `zones={side: size}`, from left, right, top and bottom --
    sit around `content`, where `App.use_shell` shows screens; with
    `center=True`, `content` is the dock's center zone and screens are its
    tabs. `size`, `set_size`, `layout`, `restore`, `set_theme`."""

    def __init__(self, window: Any, *, top_bar: Any = None, navigation: Any = None, status_bar: Any = None,
                 zones: Optional[dict[str, float]] = None, dock: Optional[Dock] = None, center: bool = False,
                 theme: Optional[Theme] = None) -> None:
        zones = dict(zones or {})
        unknown = sorted(set(zones) - set(_EDGE))
        if unknown:
            raise ValueError(f"an app shell's zones are left, right, top and bottom, got {unknown}")
        self.window = window
        self.theme = initial_theme(window, theme, self)  # the app's, followed, without one (M50)
        self._own_dock = dock is None
        self.dock = dock if dock is not None else Dock(window, theme=self.theme)
        self._events = Listeners()
        self._sizes: dict[str, float] = {}
        self._zone_nodes: dict[str, Any] = {}
        self._in_content: Any = None  # the screen `content` shows, without `center`
        self._handles: dict[str, _Handle] = {}
        create = window.create
        self.node = create("box", width="100%", height="100%", flex_direction="vertical")
        self.middle = create("box", flex_grow=1.0, flex_direction="horizontal", align_items="stretch")
        self.centre = create("box", flex_grow=1.0, flex_direction="vertical", align_items="stretch")
        self.center = center
        if center:  # the middle is a dock zone: screens and panels are its tabs
            self.content = self.dock.add_zone("center", 0.0)
        else:
            self.content = create("box", flex_grow=1.0, clip_children=True, align_items="flex_start")
        self.top_bar, self.navigation, self.status_bar = top_bar, navigation, status_bar
        if top_bar is not None:
            self.node.add_child(_take(top_bar))
        self.node.add_child(self.middle)
        if status_bar is not None:
            self.node.add_child(_take(status_bar))
        if navigation is not None:
            self.middle.add_child(_take(navigation))
        for side, size in zones.items():
            self._sizes[side] = float(size)
            self._zone_nodes[side] = self.dock.add_zone(side, float(size))
            self._handles[side] = _Handle(self, side)
        self._place("left", self.middle)
        self.middle.add_child(self.centre)
        self._place("right", self.middle)
        self._place("top", self.centre)
        self.centre.add_child(self.content)
        self._place("bottom", self.centre)
        window.root.add_child(self.node)
        self._paint()

    def _place(self, side: str, parent: Any) -> None:
        if side not in self._zone_nodes:
            return
        zone, handle = self._zone_nodes[side], self._handles[side].node
        first, second = (zone, handle) if side in ("left", "top") else (handle, zone)
        parent.add_child(first)
        parent.add_child(second)

    # -- sizes -----------------------------------------------------------------

    def size(self, side: str) -> float:
        """`side`'s zone size, px (its width, or height for top and bottom)."""
        if side not in self._sizes:
            raise ValueError(f"the shell has no {side} zone")
        return self._sizes[side]

    def set_size(self, side: str, size: float) -> float:
        """Sets `side`'s zone size, clamped between `MIN_ZONE` and 70% of the
        area it sits in; returns the size it got."""
        low, high = self._bounds(side)
        size = min(max(float(size), low), high)
        self._sizes[side] = size
        self._zone_nodes[side].set(**{"width" if side in ("left", "right") else "height": size})
        self._handles[side].node.set(value=size, value_min=low, value_max=high)
        return size

    def _bounds(self, side: str) -> tuple[float, float]:
        self.size(side)
        area = self.middle if side in ("left", "right") else self.centre
        extent = area.get("layout_width" if side in ("left", "right") else "layout_height") or 0.0
        return MIN_ZONE, max(MIN_ZONE, extent * MAX_SHARE)

    # -- layouts -------------------------------------------------------------

    def _sides(self) -> list[str]:
        return [*self._zone_nodes, *(["center"] if self.center else [])]

    def show_screen(self, root: Any, title: str, previous: Any = None) -> None:
        """Shows a screen's root (`App.show` calls this): in `content`,
        replacing the screen there; or, with `center=True`, as a center tab,
        docked the first time and brought forward after. A root already
        docked -- a panel registered as a screen (M52) -- has its tab
        brought forward where it is, and `content` is left alone."""
        if self.dock.side_of(root) is not None:
            self.dock.show(root)
            return
        if self.center:
            self.dock.add_panel("center", root, title)
            return
        shown = self._in_content
        if shown is not None and shown != root and shown.parent() == self.content:
            shown.remove()  # detached, kept alive with its state
        if root.parent() is None:
            self.content.add_child(root)
        self._in_content = root

    def layout(self) -> dict[str, Any]:
        """Where each panel is (by title), which is shown, and each zone's
        size (`None` for the center, which takes what's left), as plain data."""
        return {"zones": {side: {"panels": self.dock.titles(side), "shown": self.dock.shown_title(side),
                                 "size": self._sizes.get(side)} for side in self._sides()}}

    def restore(self, layout: dict[str, Any]) -> None:
        """Puts back a `layout()`: moves each titled panel into its zone,
        shows the one that was shown, and sizes the zones. Titles no panel
        has, and zones this shell hasn't, are skipped."""
        zones = (layout or {}).get("zones") or {}
        for side, saved in zones.items():
            if side not in self._sides():
                continue
            for title in saved.get("panels") or []:
                panel = self.dock.panel(title)
                if panel is not None and self.dock.side_of(panel) != side:
                    self.dock.move(panel, side)
        for side, saved in zones.items():  # shown and sized once every panel is in place
            if side not in self._sides():
                continue
            shown = self.dock.panel(saved.get("shown")) if saved.get("shown") is not None else None
            if shown is not None and self.dock.side_of(shown) == side:
                self.dock.show(shown)
            if saved.get("size") is not None and side in self._sizes:
                self.set_size(side, saved["size"])

    # -- theme ---------------------------------------------------------------

    def set_theme(self, theme: Theme) -> None:
        """Re-colours the shell, its dock and the widgets it was given."""
        self.theme = theme
        self.dock.set_theme(theme)
        for part in (self.top_bar, self.navigation, self.status_bar):
            if part is not None and hasattr(part, "set_theme"):
                part.set_theme(theme)
        self._paint()

    def _follow_theme(self, theme: Theme, view_theme: dict[str, Any]) -> None:
        """Following its app (M50): the shell and the dock it made. The
        widgets and dock it was given follow the app themselves, or keep
        the `theme=` they were pinned to."""
        self.theme = theme
        if self._own_dock:
            self.dock.set_theme(theme)
        self._paint()

    def _color(self, role: str) -> tuple[int, int, int, int]:
        scheme = self.theme.roles if self.theme.roles is not None else tokens.baseline_scheme()
        return scheme[role]

    def _paint(self) -> None:
        self.node.set(fill=self._color("surface"))
        for handle in self._handles.values():
            handle.paint()


def _take(part: Any) -> Any:
    """A widget's node (or the node), detached from wherever it was."""
    node = getattr(part, "node", part)
    if node.parent() is not None:
        node.remove()
    return node
