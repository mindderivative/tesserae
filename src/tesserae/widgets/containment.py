"""The carousel and the splitter: new by M42's Q1, since
`tre` had them (`add_carousel`, `add_splitter`) and Tesserae never
wrapped them. Built on `tre` 0.3.4's building blocks, following `tre`'s
`legacy-behavior.md` (0.3.5) for how they move.

`tre` animates no `width` and has no per-frame callback, so the carousel
drives its fractional position by animating a property of a private node
in no tree (`tre` applies the easing, and `get` reads the value mid-
animation), and re-lays its items out each frame from a chained one-frame
animation (`_Ticker`), the trick `tesserae.overlays._Timer` uses.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Optional

from tesserae import a11y
from tesserae.reactive import Effect, Signal
from tesserae.theme import Theme
from tesserae.widgets._composed import Widget
from tesserae import motion

if TYPE_CHECKING:
    from tre import Window

__all__ = ["carousel", "carousel_layout", "splitter"]

#: The carousel's geometry (`tre`'s, MD3's): items 16 px in, 8 apart, 8 above and below.
CAROUSEL_PADDING = 16.0
CAROUSEL_GAP = 8.0
CAROUSEL_INSET = 8.0
#: The snapping layouts' fixed slots, and each layout's pattern.
SMALL, MEDIUM = 56.0, 112.0
PATTERNS = {"hero": ("large", "small"), "multi_browse": ("large", "medium", "small")}
LAYOUTS = ("uncontained", *PATTERNS)
#: An uncontained item's width when it has none; px dragged per index when snapping.
UNCONTAINED_WIDTH = 200.0
DRAG_STEP = 60.0
#: Moving to an index takes 300 ms, standard easing (`tre`'s).
MOVE_MS = 300


class _Ticker:
    """`fn()` once per frame while `running()` says so: a one-frame
    animation of a private node in no tree, chained from `on_complete`."""

    def __init__(self, window: Any, fn: Callable[[], None], running: Callable[[], bool]) -> None:
        self._node = window.create("box", width=0.0, height=0.0)
        self._fn, self._running, self._on = fn, running, False

    def start(self) -> None:
        if not self._on:
            self._on = True
            self._tick_later()

    def _tick_later(self) -> None:
        self._node.stop_animation("stroke_width")
        self._node.set(stroke_width=0.0)
        self._node.animate("stroke_width", 1.0, 1, on_complete=self._tick)

    def _tick(self) -> None:
        self._fn()
        if self._running():
            self._tick_later()
        else:
            self._on = False


def carousel_layout(layout: str, width: float, count: int, position: float,
                    own_widths: list[float], scroll: float = 0.0) -> list[tuple[float, float]]:
    """Each item's `(x, width)` in a carousel `width` wide, by `tre`'s
    rules. The snapping layouts blend their layouts at the indices either
    side of a fractional `position`; `uncontained` places items at their
    own widths, `scroll` px along."""
    if layout == "uncontained":
        placed, x = [], CAROUSEL_PADDING - scroll
        for w in own_widths:
            placed.append((x, w))
            x += w + CAROUSEL_GAP
        return placed
    below = int(position)
    above = min(below + 1, max(count - 1, 0))
    t = position - below
    low, high = _snapped(layout, width, count, below), _snapped(layout, width, count, above)
    return [(xl + (xh - xl) * t, wl + (wh - wl) * t) for (xl, wl), (xh, wh) in zip(low, high)]


def _slot_widths(layout: str, width: float) -> list[float]:
    pattern = PATTERNS[layout]
    fixed = sum(SMALL if s == "small" else MEDIUM for s in pattern if s != "large")
    large = max(SMALL, width - 2 * CAROUSEL_PADDING - fixed - (len(pattern) - 1) * CAROUSEL_GAP)
    return [large if s == "large" else SMALL if s == "small" else MEDIUM for s in pattern]


def _snapped(layout: str, width: float, count: int, index: int) -> list[tuple[float, float]]:
    slots = _slot_widths(layout, width)
    widths = [SMALL if i < index else slots[min(i - index, len(slots) - 1)] for i in range(count)]
    placed, x = [], CAROUSEL_PADDING - sum(w + CAROUSEL_GAP for w in widths[:index])
    for w in widths:  # the current item starts at the left padding
        placed.append((x, w))
        x += w + CAROUSEL_GAP
    return placed


def carousel(
    window: "Window",
    width: float,
    height: float,
    layout: str = "multi_browse",
    items: Optional[list[Any]] = None,
    x: float | None = None,
    y: float | None = None,
    *,
    label: str = "Carousel",
    theme: "Theme | None" = None,
) -> Widget:
    """MD3's carousel: a clip holding items 16 px in, 8 apart and
    8 above and below, each masked to 28 px corners (`extra_large`) on
    `surface_container_highest`. `hero` and `multi_browse` snap through
    large/medium/small slots (`small` 56, `medium` 112, `large` what's
    left), items before the current one small; moving blends the widths.
    `.index` is a `Signal` of the item it's settling on; setting it (or a
    wheel notch, 60 px of drag, or the left/right arrows when focused)
    moves there over 300 ms, standard easing. `uncontained` keeps each
    item's own width (200 if unset) and scrolls by pixel: `.scroll` is a
    `Signal`, and the wheel (half its delta), drag (1:1) and the arrows
    move it, clamped. `.position()` is where it's drawn now. `.add(item)`
    adds a node or widget; `.on_change(fn)` hears the user's moves (an
    index, or the scroll)."""
    if layout not in LAYOUTS:
        raise ValueError(f"unknown carousel layout {layout!r}; expected one of {list(LAYOUTS)}")
    name = "carousel"
    width, height = float(width), float(height)
    spec = {"id": name, "kind": "Container", "style": {"width": width, "height": height}}
    widget = Widget(window, spec=spec, theme=theme, x=x, y=y, name=name)
    root = widget.node
    root.set(clip_children=True, focusable=True)
    a11y.describe(root, role="group", label=label)
    snapping = layout != "uncontained"
    widget.layout = layout
    widget.slots = []
    own: list[float] = []
    widget.index = Signal(0)
    widget.scroll = Signal(0.0)
    changes: list[Callable[[Any], Any]] = []
    widget.on_change = lambda fn: (changes.append(fn), lambda: changes.remove(fn) if fn in changes else None)[1]
    driver = window.create("box", width=0.0, height=0.0)  # its `stroke_width` is the animated position
    driver.set(stroke_width=0.0)
    target = [0.0]

    def position() -> float:
        return float(driver.get("stroke_width") or 0.0)

    widget.position = position

    def max_scroll() -> float:
        content = sum(own) + CAROUSEL_GAP * max(len(own) - 1, 0) + 2 * CAROUSEL_PADDING
        return max(0.0, content - width)

    def place() -> None:
        placed = carousel_layout(layout, width, len(widget.slots), position(), own, widget.scroll.get())
        for slot, (sx, sw) in zip(widget.slots, placed):
            slot.set(x=sx, width=sw)

    ticker = _Ticker(window, place, lambda: position() != target[0])

    def follow_index() -> None:
        index = widget.index.get()
        if snapping and float(index) != target[0]:
            target[0] = float(index)
            driver.animate("stroke_width", target[0], motion.duration(window, MOVE_MS), easing=Theme.easing("standard"))
            ticker.start()

    def follow_scroll() -> None:
        widget.scroll.get()
        place()

    widget._undo.append(Effect(follow_index).dispose)
    widget._undo.append(Effect(follow_scroll).dispose)

    def user_index(index: int) -> None:
        index = min(max(index, 0), max(len(widget.slots) - 1, 0))
        if index != widget.index.get():
            widget.index.set(index)
            for fn in list(changes):
                fn(index)

    def user_scroll(value: float) -> None:
        value = min(max(value, 0.0), max_scroll())
        if value != widget.scroll.get():
            widget.scroll.set(value)
            for fn in list(changes):
                fn(value)

    drag: dict[str, Any] = {}

    def down(event: Any) -> None:
        if event.window_x is None:
            return
        drag.update(start=event.window_x, index=widget.index.get(), scroll=widget.scroll.get())
        root.capture_pointer()

    def move(event: Any) -> None:
        if drag and event.window_x is not None:
            travelled = event.window_x - drag["start"]
            if snapping:  # dragging left moves on, one index per 60 px
                user_index(drag["index"] - int(travelled / DRAG_STEP))
            else:
                user_scroll(drag["scroll"] - travelled)

    def up(event: Any) -> None:
        if drag:
            drag.clear()
            root.release_pointer()

    def wheel(event: Any) -> None:
        delta = event.delta_y if event.delta_y else event.delta_x
        if not delta:
            return
        if snapping:  # a notch down (positive) moves on
            user_index(widget.index.get() + (1 if delta > 0 else -1))
        else:
            user_scroll(widget.scroll.get() + float(delta) / 2)

    def key(event: Any) -> None:
        step = {"arrow_right": 1, "arrow_left": -1}.get(event.key)
        if step is None or event.target != root:
            return
        if snapping:
            user_index(widget.index.get() + step)
        else:
            user_scroll(widget.scroll.get() + step * (SMALL + CAROUSEL_GAP))

    for event_name, fn in (("pointer_down", down), ("pointer_move", move), ("pointer_up", up),
                           ("pointer_cancel", up), ("wheel", wheel), ("key_down", key)):
        widget._undo.append(widget.view._listen(root, event_name, fn))

    def add(item: Any) -> Any:
        """Adds `item` (a node or a widget) in a new slot; returns the slot."""
        node = getattr(item, "node", item)
        if node.parent() is not None:
            node.remove()
        own_width = node.get("width") if not snapping else None  # an unsized node's is "auto"
        own.append(float(own_width) if isinstance(own_width, (int, float)) and own_width else UNCONTAINED_WIDTH)
        slot = window.create("box", position="absolute", y=CAROUSEL_INSET, height=height - 2 * CAROUSEL_INSET,
                             width=0.0, x=0.0, clip_children=True, corner_radius=_radius(widget),
                             fill=widget.color("surface_container_highest"))
        slot.add_child(node)
        root.add_child(slot)
        widget.slots.append(slot)
        place()
        return slot

    def recolour() -> None:
        for slot in widget.slots:
            slot.set(fill=widget.color("surface_container_highest"), corner_radius=_radius(widget))

    widget.add = add
    widget.after_theme(recolour)
    for item in items or []:
        add(item)
    return widget


def _radius(widget: Widget) -> float:
    """MD3's carousel item shape, `extra_large` (28), or the theme's."""
    return (widget.theme.shape("carousel", "item") if widget.theme.is_set else None) or 28.0


#: The splitter's handle: a 16 px target holding MD3's 4x48 drag handle.
HANDLE_SPAN = 16.0
HANDLE_SIZE = (4.0, 48.0)
#: How far an arrow key moves the split.
SPLIT_STEP = 0.05


def splitter(
    window: "Window",
    first: Any,
    second: Any,
    width: float,
    height: float,
    orientation: str = "horizontal",
    position: float = 0.5,
    x: float | None = None,
    y: float | None = None,
    *,
    label: str = "Resize panes",
    theme: "Theme | None" = None,
) -> Widget:
    """Two panes and the handle between them: `first` and `second`
    (nodes or widgets) share `width` (a `horizontal` splitter) or `height`
    (`vertical`) less the 16 px handle, `first` getting `.position` (a
    `Signal`, 0..1) of it. The handle holds MD3's 4x48 `outline` drag
    handle, shows a `col_resize` (or `row_resize`) cursor, and is a
    focusable `role="slider"`: dragging it (with pointer capture) puts
    the split under the pointer, clamped, at once; the arrow keys move it
    by 5%, Home and End to the ends. `.on_change(fn)` hears the user's
    moves. Parts `first`, `handle`, `second`."""
    if orientation not in ("horizontal", "vertical"):
        raise ValueError(f"a splitter's orientation is 'horizontal' or 'vertical', got {orientation!r}")
    if not 0.0 <= position <= 1.0:
        raise ValueError(f"position={position} is outside 0..1")
    horizontal = orientation == "horizontal"
    name = "splitter"
    width, height = float(width), float(height)
    extent, across = (width, height) if horizontal else (height, width)
    available = max(extent - HANDLE_SPAN, 0.0)
    main, cross = ("width", "height") if horizontal else ("height", "width")
    grip_w, grip_h = HANDLE_SIZE if horizontal else HANDLE_SIZE[::-1]

    def pane(part: str) -> dict[str, Any]:
        return {"id": f"{name}.{part}", "kind": "Container",
                "style": {main: available / 2, cross: across}}

    spec = {"id": name, "kind": "Container",
            "style": {"width": width, "height": height,
                      "flex_direction": "horizontal" if horizontal else "vertical"},
            "children": [
                pane("first"),
                {"id": f"{name}.handle", "kind": "Rect",
                 "style": {main: HANDLE_SPAN, cross: across, "background": "transparent", "align_content": "center"},
                 "children": [{"id": f"{name}.handle.grip", "kind": "Rect",
                               "style": {"width": grip_w, "height": grip_h, "corner_radius": 2,
                                         "background": "outline"}}]},
                pane("second")]}
    widget = Widget(window, spec=spec, theme=theme, x=x, y=y, interactive={"handle": "on_surface"}, name=name)
    for part, item in (("first", first), ("second", second)):
        node = getattr(item, "node", item)
        if node.parent() is not None:
            node.remove()
        widget.part(part).add_child(node)
    handle = widget.part("handle")
    handle.set(focusable=True, cursor="col_resize" if horizontal else "row_resize")
    a11y.describe(handle, role="slider", label=label, value_min=0.0, value_max=1.0, value_step=SPLIT_STEP)
    widget.orientation = orientation
    widget.position = Signal(float(position))
    changes: list[Callable[[float], Any]] = []
    widget.on_change = lambda fn: (changes.append(fn), lambda: changes.remove(fn) if fn in changes else None)[1]

    def apply() -> None:
        share = widget.position.get()
        widget.part("first").set(**{main: available * share})
        widget.part("second").set(**{main: available * (1.0 - share)})
        handle.set(value=share)

    widget._undo.append(Effect(apply).dispose)
    widget.after_theme(apply)

    def user(share: float) -> None:
        share = min(max(share, 0.0), 1.0)
        if share != widget.position.get():
            widget.position.set(share)
            for fn in list(changes):
                fn(share)

    dragging = [False]

    def down(event: Any) -> None:
        dragging[0] = True
        handle.capture_pointer()
        widget.interaction("handle").set_dragged(True)

    def move(event: Any) -> None:
        if not dragging[0] or event.window_x is None or not available:
            return
        pointer = event.window_x if horizontal else event.window_y
        start = widget.part("first").get("layout_x" if horizontal else "layout_y")
        user((pointer - start - HANDLE_SPAN / 2) / available)  # the handle's middle under the pointer

    def up(event: Any) -> None:
        if dragging[0]:
            dragging[0] = False
            handle.release_pointer()
            widget.interaction("handle").set_dragged(False)

    forward, back = ("arrow_right", "arrow_left") if horizontal else ("arrow_down", "arrow_up")

    def key(event: Any) -> None:
        share = widget.position.get()
        moves = {forward: share + SPLIT_STEP, back: share - SPLIT_STEP, "home": 0.0, "end": 1.0}
        if event.key in moves:
            user(round(moves[event.key], 6))

    for event_name, fn in (("pointer_down", down), ("pointer_move", move), ("pointer_up", up),
                           ("pointer_cancel", up), ("key_down", key)):
        widget._undo.append(widget.view._listen(handle, event_name, fn))
    widget._undo.append(a11y.on_action(handle, {
        "increment": lambda e: user(round(widget.position.get() + SPLIT_STEP, 6)),
        "decrement": lambda e: user(round(widget.position.get() - SPLIT_STEP, 6)),
        "set_value": lambda e: user(float(e.value)),
    }, listen=widget.view._listen))
    return widget
