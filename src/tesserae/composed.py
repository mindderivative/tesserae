"""A composed view on screen: a `View` that is fed by a `ViewHandle` instead of a file (phase 5 of #209).

`ComposedView(handle)` lowers the handle's composition (`tesserae.spec.lower`) and builds it with the existing builder, then keeps it in step:

- an `Effect` lowers again whenever a value any property reads changes, and `View.reconcile` patches the live nodes (the same machinery hot
  reload uses: nodes are matched by id, so a node that is kept stays);
- when a `for:` or `if:` adds, removes or moves instances, the effect runs again so it follows the new instances;
- each instance's handlers are wired to its node (`Instance.fire` runs them in the scope they were written in), and a `model` property given a
  bare reference writes the user's edit back to that Signal or state;
- `ViewHandle.visible` shows and hides the view's root.

`open_composed` is the one call an app makes: it opens the view against its ViewModel and shows it.
"""

from __future__ import annotations

import time
import weakref
from pathlib import Path
from typing import Any, Callable, Optional

from tesserae import a11y as a11y_module, tokens, urls
from tesserae.follow import app_of
from tesserae.listeners import handled, listen_window
from tesserae.reactive import Effect, Signal, untrack
from tesserae.expr import compile_statements, is_action_name
from tesserae.spec.compose import Instance
from tesserae.timers import Timers
from tesserae.spec.images import extract_images
from tesserae.spec.lower import SPLIT_HANDLE, lower
from tesserae.spec.mask import Mask
from tesserae.spec.nodes import ViewDoc
from tesserae.view import _EVENTS, SURFACE_ACTIONS, WINDOW_ACTIONS, View

#: Events the renderer adds to the engine's: a key press, Enter in a field that is not multiline, and a pointer press (which, unlike a click,
#: does not make the node a button).
_KEY_EVENTS = {"on_input": "input_value", "on_key": "key_down", "on_submit": "key_down", "on_press": "pointer_down", "on_move": "pointer_move", "on_release": "pointer_up"}
#: The keys that move focus in a `focus_group`, by its mode, as (previous, next).
_GROUP_KEYS = {"horizontal": (("arrow_left",), ("arrow_right",)), "vertical": (("arrow_up",), ("arrow_down",)),
               "both": (("arrow_left", "arrow_up"), ("arrow_right", "arrow_down"))}
#: A pause this long (seconds) in typing starts a new type-ahead search.
#: The ScrollView properties the renderer writes (the caller binds a Signal or a state name to read them), and how near an edge counts as at it.
_MEASURED = ("measured_width", "measured_height")
_SCROLL_OUTPUTS = frozenset({"scroll_offset", "at_top", "at_end", "scroll_direction"})
SCROLL_EDGE = 0.5
TYPEAHEAD_RESET = 1.0
from tesserae.viewmodel import Bindings, ViewHandle, open_view

__all__ = ["ComposedView", "builtin_actions", "open_composed"]


def _is_text_input(node: Any) -> bool:
    try:
        return node.get("kind") == "text_input"
    except (AttributeError, ValueError):
        return False


def _is_submit(event: Any) -> bool:
    """Enter pressed in something that is not a multiline input."""
    if getattr(event, "key", None) != "Enter":
        return False
    try:
        return not event.target.get("multiline")
    except (AttributeError, ValueError):
        return True


def _clip(text: Any) -> str:
    """What `copy(...)` puts on the clipboard: text, or a number or a bool as text; anything else is a mistake."""
    if isinstance(text, str):
        return text
    if isinstance(text, (int, float)):
        return str(text)
    raise ValueError(f"copy() takes text, not {text!r}")


def scroll_direction(last: str, old: Any, new: Any, horizontal: bool = False) -> str:
    """`'down'` or `'up'` (`'right'` or `'left'` when horizontal) from a scroll event's offsets; the last direction when it did not move or the
    event has none."""
    if old is None or new is None or new == old:
        return last
    forward, back = ("right", "left") if horizontal else ("down", "up")
    return forward if new > old else back


def scroll_edges(offset: float, viewport: float, length: float) -> tuple[bool, bool]:
    """`(at_top, at_end)` for a scroll view `viewport` tall over content `length` tall. Before the first layout (a size of 0) nothing is known
    about the end, so it is not at it."""
    laid_out = viewport > 0 and length > 0
    return offset <= SCROLL_EDGE, laid_out and offset >= length - viewport - SCROLL_EDGE


def builtin_actions(view_ref: Callable[[], Any], window: Any = None) -> Callable[..., Optional[Callable[..., Any]]]:
    """The actions a handler may call without a ViewModel: `window.<action>`, `navigate.<screen>`, `navigate_to(screen[, params])`, `navigate_route(path)`, `open_window(view[, modal])`, `surface.dismiss` and
    `focus(name)`, `capture()`, `release()`, `cursor(name)`, `copy(text)`, `paste()`, `open_url(url)`, `after(ms, action[, name])`, `every(ms, action[, name])` and `cancel(name)`. `view_ref()` is the `ComposedView` they act for (it does not exist yet when composing starts); `window` is the one it will be on, which is how `app` is found then."""

    def resolve(path: str, scope: Any = None) -> Optional[Callable[..., Any]]:
        view = view_ref()
        if path == "focus":
            return lambda name: view.focus(scope, name)
        if path == "open_url":
            return lambda url: urls.open_url(url)
        if path == "copy":
            return lambda text: bool(view.window.write_clipboard(_clip(text)))
        if path == "paste":
            return lambda: view.window.read_clipboard() or ""
        if path in ("capture", "release"):
            return lambda: getattr(view.firing_node(path), "capture_pointer" if path == "capture" else "release_pointer")()
        if path == "cursor":
            return lambda name: view.firing_node("cursor").set(cursor=name)
        if path in ("after", "every"):
            start = view.timers.after if path == "after" else view.timers.every
            return lambda ms, action, name=None: start(ms, view.timer_action(scope, action), view.timer_name(scope, name))
        if path == "cancel":
            return lambda name: view.timers.cancel(view.timer_name(scope, name))
        head, _, rest = path.partition(".")
        if head == "window" and rest in WINDOW_ACTIONS:
            def window_action() -> None:
                app = app_of(view.window)
                if app is not None:  # a second window's title bar acts on that window, not the main one
                    getattr(app._appwindow_for(view.window) or app, rest)()
            return window_action
        if path == "open_window":  # a view in a window of its own (`open_window('Settings', True)`: the second argument blocks this window)
            def open_window(name: str, modal: bool = False) -> None:
                app = app_of(view.window)
                if app is not None:
                    app.open_window(name, parent=app._appwindow_for(view.window), modal=bool(modal))
            return open_window
        if head == "navigate" and rest:
            def navigate() -> None:
                app = app_of(view.window)
                if app is None:
                    return
                if rest == "back":
                    app.back()
                elif rest == "forward":
                    app.forward()
                else:
                    app.navigate(rest)
            return navigate
        if path == "navigate_to":  # a screen by name, with params for the screen to read as `app.params`
            return lambda screen, params=None: app_of(view.window).navigate(screen, **(params or {})) if app_of(view.window) is not None else None
        if path == "navigate_route":  # a route by its path (`'notes/' + str(id)`): the screen it names, with the params the path holds
            return lambda route: app_of(view.window).navigate_to(route) if app_of(view.window) is not None else None
        if head == "surface" and rest in SURFACE_ACTIONS:
            from tesserae.overlays import dismiss_surface

            return lambda: dismiss_surface(view.root)
        return None

    resolve.app = lambda: app_of(window if window is not None else getattr(view_ref(), "window", None))  # type: ignore[attr-defined]  # `app` in an expression
    resolve.wants_scope = True  # type: ignore[attr-defined]  # `focus` needs the widget the handler was written in
    return resolve


class _SpecTip:
    """The tooltip of a node the language did not write (a title bar's buttons), in the shape `_wire_tooltips` reads."""

    def __init__(self, node_id: str, tooltip: dict[str, Any]) -> None:
        self.id, self.tooltip, self.a11y = node_id, tooltip, {}


class _Screen:
    """A routed call as the app keeps it: the node it is (the app shows and hides the node, and tells a screen by this object)."""

    def __init__(self, view: Any, record: Any) -> None:
        self.view, self.record = view, record

    @property
    def root(self) -> Any:
        inst = self.record.instance
        return self.view._built.outer.get(inst.id) if inst is not None else None


class ComposedView(View):
    """A `View` built and kept up to date from a `ViewHandle`. See the module docstring."""

    def __init__(self, handle: ViewHandle, *, base_dir: Optional[Path] = None, window: Any = None, **kwargs: Any) -> None:
        self.handle = handle
        self._base_dir = Path(base_dir) if base_dir is not None else Path.cwd()
        self._handler_undos: list[Callable[[], None]] = []
        self._state_undos: list[Callable[[], None]] = []
        self._group_undos: list[Callable[[], None]] = []
        self._active: dict[str, str] = {}  # a focus group's id -> the id of the item that holds its tab stop
        self._typed: tuple[str, float] = ("", 0.0)
        self._observed: set[int] = set()
        self._synced = False
        self._effect: Optional[Effect] = None
        self._timers: Optional[Timers] = None
        self._scrolled: dict[str, dict[str, str]] = {}
        self._firing: list[Instance] = []
        self._split_dragging: set[str] = set()
        self._tips: dict[str, tuple[Any, Callable[[], None]]] = {}  # tooltips showing: the node id -> its layer and the Escape listener's undo
        self._tip_undos: list[Callable[[], None]] = []
        self._link_hot: dict[str, set[str]] = {}  # a Link's reasons to be underlined now: 'pointer', 'focus'
        self._link_undos: list[Callable[[], None]] = []
        self._field_undos: list[Callable[[], None]] = []
        self._frame_effects: list[Effect] = []
        self._screens: dict[str, Any] = {}
        self._measure_undo: Optional[Callable[[], None]] = None
        self._split_last_up: dict[str, float] = {}
        self._split_kept: dict[str, float] = {}  # a collapsed splitter's position before it closed
        self._syncing = False
        self._layer_resize: dict[str, Callable[[], None]] = {}
        self._layer_timeouts: dict[str, Callable[[], None]] = {}
        self._shown_layers: dict[str, Any] = {}  # each Overlay showing: its id -> the layer node shown
        self._overlay_undos: list[Callable[[], None]] = []
        self._dismissed_open: set[str] = set()  # overlays closed by the user whose `open` is not a Signal: not reopened until `open` goes false
        self._timer_code: dict[str, Any] = {}
        self._timer_scopes: weakref.WeakKeyDictionary[Any, int] = weakref.WeakKeyDictionary()
        spec, frames = self._lowered()
        super().__init__(spec, window=window, frames=frames, **kwargs)
        handle.window = self.window  # the ViewModel finds its app through the view's window
        handle.view = self
        self._effect = Effect(self._sync)
        self._synced = True

    def firing_node(self, action: str) -> Any:
        """The node whose handler is running, for an action that acts on it. Only a handler has one: a timer's action does not."""
        if not self._firing:
            raise ValueError(f"{action}() acts on the widget whose handler is running; it cannot be called from a timer or anywhere else")
        inst = self._firing[-1]
        return self._built.outer[inst.id] if inst.widget == "Link" else self._built.nodes[inst.id]

    # timers (#217)

    @property
    def timers(self) -> Timers:
        """The view's timers; they stop when it closes."""
        if self._timers is None:
            self._timers = Timers(self.window)
        return self._timers

    def timer_name(self, scope: Any, name: Any) -> Optional[str]:
        """A timer's name as the scope that wrote it owns it, as a local name is: the same name in two items of a `for:` is two timers, and in
        two widgets of one view is one."""
        if name is None:
            return None
        if not isinstance(name, str) or not name:
            raise ValueError(f"a timer's name is text, not {name!r}")
        if scope is None:
            return name
        if scope not in self._timer_scopes:
            self._timer_scopes[scope] = len(self._timer_scopes) + 1
        return f"{self._timer_scopes[scope]}:{name}"

    def timer_action(self, scope: Any, action: Any) -> Callable[[], None]:
        """What `after`/`every` run: `action` (an action name or statements) in the scope it was written in, unless its widget has gone."""
        if not isinstance(action, str) or not action.strip():
            raise ValueError(f"after/every run an action name or statements, not {action!r}")
        if action not in self._timer_code:
            self._timer_code[action] = None if is_action_name(action) else compile_statements(action)
        code = self._timer_code[action]
        instance = scope.nearest_instance()

        def run() -> None:
            if instance is not None and instance.disposed:
                return
            if code is None:
                scope.call_action(action.strip(), [], {})
            else:
                code.run(scope)

        return run

    # lowering and syncing

    def _lowered(self) -> tuple[dict[str, Any], dict[str, tuple[bytes, int, int]]]:
        spec = lower(self.handle.composition.root)
        spec, frames = extract_images(spec, self._base_dir, dependencies=set())
        return spec, {node_id: (rgba, w, h) for node_id, rgba, w, h in frames}

    def _sync(self) -> None:
        spec, frames = self._lowered()  # read inside the effect: these are the values the view depends on
        visible = self.handle.visible.get()
        self._observe()
        self._syncing = True  # the engine can report a scroll while the nodes are patched; what that changes waits for the next frame
        try:
            if self._synced:
                untrack(lambda: self.reconcile(spec, frames))
            untrack(self._wire_instances)
            untrack(self._wire_scroll)
            untrack(self._fit_graphs)
            untrack(self._wire_overlays)
            untrack(self._wire_splitters)
            untrack(self._wire_tooltips)
            untrack(self._wire_links)
            untrack(self._wire_fields)
            untrack(self._wire_frames)
            untrack(self._wire_measures)
            untrack(self._wire_states)
            untrack(self._wire_focus_groups)
            untrack(lambda: self.root.get("visible") != visible and self.root.set(visible=visible))
        finally:
            self._syncing = False

    def _observe(self) -> None:
        """Asks each instance that is new to tell this view when its children change."""
        for inst in self.handle.composition.walk():
            if id(inst) not in self._observed:
                self._observed.add(id(inst))
                inst.on_children(self._children_changed)

    def _children_changed(self, inst: Instance, old: list[Instance], new: list[Instance]) -> None:
        if self._effect is not None and not self.handle.closed:
            self._effect._run()

    # handlers and edits

    def _wire_instances(self) -> None:
        for undo in self._handler_undos:
            undo()
        self._handler_undos = []
        for inst in self.handle.composition.walk():
            if inst.id not in self._built.nodes:
                continue
            node = self._built.outer[inst.id] if inst.widget == "Link" else self._built.nodes[inst.id]
            control = self._built.controls.get(inst.id)
            self._enforce_input(inst, node)
            # the bound Signal is written before a handler runs, so a handler reads what the user just did
            for prop, (name, scope) in inst.models.items():
                if inst.widget in ("ScrollView", "VirtualList") and prop in _SCROLL_OUTPUTS:
                    continue  # `_wire_scroll`'s
                if inst.widget == "Container" and prop in _MEASURED:
                    continue  # `_wire_measures`'s
                if inst.widget == "Dock" and prop == "closed":  # a closable panel's close button: the names of the panels that are shut
                    host = self._docks.get(inst.id)
                    if host is not None:
                        self._handler_undos.append(host.on_closed(
                            lambda ids, scope=scope, name=name: scope.assign(name, [i.rsplit(".", 1)[-1] for i in ids])))
                    continue
                state = getattr(control, prop, None) if control is not None else None
                if state is not None and prop == "mode" and hasattr(control, "on_mode"):  # the dial moving itself on to the minutes
                    self._handler_undos.append(control.on_mode(
                        lambda mode, scope=scope, name=name: scope.assign(name, mode)))
                elif state is not None and hasattr(control, "on_input"):  # a bound slider value follows the drag, not only its end
                    self._handler_undos.append(control.on_input(
                        lambda value, scope=scope, name=name, state=state: scope.assign(name, state.get())))
                    self._handler_undos.append(control.on_change(
                        lambda value, scope=scope, name=name, state=state: scope.assign(name, state.get())))
                elif state is not None and hasattr(control, "on_change"):
                    self._handler_undos.append(control.on_change(
                        lambda value, scope=scope, name=name, state=state: scope.assign(name, state.get())))
                else:
                    self._handler_undos.append(self._listen(
                        node, "change", lambda ev, scope=scope, name=name, node=node, prop=prop: scope.assign(name, node.get(prop))))
            for event in inst.handlers:
                tre_event = _EVENTS.get(event) or _KEY_EVENTS.get(event)
                if tre_event is None:
                    continue

                def call(event_obj: Any, inst: Instance = inst, event: str = event) -> Any:
                    if inst.id in self._disabled_on:  # a disabled node's handlers do not run
                        return
                    if event == "on_submit" and not _is_submit(event_obj):
                        return
                    self._firing.append(inst)  # what `capture()`, `release()` and `cursor()` act on
                    try:
                        inst.fire(event, event_obj)
                    finally:
                        self._firing.pop()

                if tre_event == "input_value":  # a slider's value changing while it is dragged, as against `on_change`, once it is let go
                    if control is None or not hasattr(control, "on_input"):
                        raise ValueError(f"{inst.id}: on_input is for a Slider, which says it while it is dragged")
                    self._handler_undos.append(control.on_input(lambda value, call=call: call(None)))
                elif tre_event == "change" and control is not None and hasattr(control, "on_change"):
                    self._handler_undos.append(control.on_change(lambda value, call=call: call(None)))
                elif tre_event == "click":
                    self._handler_undos.append(self._listen(node, tre_event, handled(call)))
                else:
                    self._handler_undos.append(self._listen(node, tre_event, call))

    def _fit_scroll(self, inst: Instance) -> None:
        """A ScrollView with a `max_height` (a `max_width` when horizontal) and no size of its own is as long as its content, up to that limit: the
        engine gives a scroll view no size from what is in it. Done once the content has been laid out."""
        horizontal = inst.value("orientation") == "horizontal"
        size, limit = ("width", "max_width") if horizontal else ("height", "max_height")
        cap = inst.style.get(limit)
        cap = cap.get() if hasattr(cap, "get") else cap
        own = inst.style.get(size)
        own = own.get() if hasattr(own, "get") else own
        if isinstance(cap, bool) or not isinstance(cap, (int, float)) or own not in (None, "auto"):
            return
        outer, content = self._built.outer[inst.id], self._built.nodes[inst.id]

        def fit(outer: Any = outer, content: Any = content, size: str = size, cap: float = float(cap)) -> None:
            outer.set(**{size: min(float(content.get(f"layout_{size}")), cap)})

        self.timers.after(0, fit, name=f"fit:{inst.id}")

    def _fit_graphs(self) -> None:
        """A NodeGraph with `fit` pans and zooms to show every node once it has been laid out."""
        for inst in self.handle.composition.walk():
            graph = self._built.controls.get(inst.id) if inst.widget == "NodeGraph" else None
            if graph is not None and getattr(graph, "fit_wanted", False):
                self.timers.after(0, graph.fit_to_view, name=f"fit-graph:{inst.id}")

    def _wire_scroll(self) -> None:
        """A ScrollView's outputs: `scroll_offset`, `at_top`, `at_end` and `scroll_direction`, each written to the Signal or state name it was
        given, on every scroll and once the layout has settled."""
        for inst in self.handle.composition.walk():
            scrolls = inst.widget in ("ScrollView", "VirtualList")
            outputs = {prop: ref for prop, ref in inst.models.items() if prop in _SCROLL_OUTPUTS} if scrolls else {}
            if inst.widget == "ScrollView" and inst.id in self._built.outer:
                self._fit_scroll(inst)
            if not scrolls or not (outputs or inst.virtual or "scroll_offset" in inst.props) or inst.id not in self._built.outer:
                continue
            outer, content = self._built.outer[inst.id], self._built.nodes[inst.id]
            last = self._scrolled.setdefault(inst.id, {"direction": "none"})  # kept across re-wiring: every write to a Signal re-syncs

            def report(event: Any = None, outputs: dict = outputs, outer: Any = outer, content: Any = content, last: dict = last,
                       inst: Instance = inst) -> None:
                offset = float(outer.get("scroll_offset"))
                across = outer.get("orientation") == "horizontal"
                side = "layout_width" if across else "layout_height"
                last["direction"] = scroll_direction(last["direction"], getattr(event, "old_value", None), getattr(event, "new_value", None), across)
                at_top, at_end = scroll_edges(offset, float(outer.get(side)), float(content.get(side)))
                values = {"scroll_offset": offset, "at_top": at_top, "at_end": at_end, "scroll_direction": last["direction"]}
                for prop, (name, scope) in outputs.items():
                    scope.assign(name, values[prop])
                if inst.virtual is not None:  # build the rows that are in view
                    window = inst.virtual.window_for(offset, float(outer.get("layout_height")))
                    if self._syncing:
                        self.timers.after(0, lambda: inst.virtual.set_window(*window), name=f"window:{inst.id}")
                    else:
                        inst.virtual.set_window(*window)

            if outputs or inst.virtual is not None:
                self._handler_undos.append(self._listen(outer, "scroll", report))

            def settle(inst: Instance = inst, outer: Any = outer, content: Any = content, report: Callable[..., None] = report) -> None:
                """On the first frame after a build: the offset that was asked for. tre clamps an offset to the content, which has no size until it
                has been laid out, and reading a layout property lays it out."""
                content.get("layout_height")
                if "scroll_offset" in inst.props:
                    outer.set(scroll_offset=float(inst.value("scroll_offset")))
                report()

            self.timers.after(0, settle, name=f"scroll:{inst.id}")

    # splitters (#228)

    SPLIT_STEP = 0.05
    #: two releases of the handle this close together are a double click
    DOUBLE_CLICK = 0.4

    def _wire_splitters(self) -> None:
        """The handle of each `Splitter`: a drag with the pointer captured, the arrow keys, Home and End, the screen reader's actions, and (when the
        splitter is `collapsible`) a double click that closes the first pane and opens it again."""
        for inst in self.handle.composition.walk():
            handle_id = f"{inst.id}.handle"
            if inst.widget != "Splitter" or handle_id not in self._built.nodes:
                continue
            handle, first = self._built.nodes[handle_id], self._built.nodes[f"{inst.id}.first"]
            horizontal = inst.value("orientation") == "horizontal"

            def room(inst: Instance = inst, horizontal: bool = horizontal) -> float:
                """The length the two panes share: the splitter less the handle."""
                key = "layout_width" if horizontal else "layout_height"
                return float(self._built.outer[inst.id].get(key) or 0.0) - float(self._built.nodes[f"{inst.id}.handle"].get(key) or 0.0)

            def user(share: float, inst: Instance = inst, room: Callable[[], float] = room) -> None:
                length = room()
                low = float(inst.value("min_first")) / length if length > 0 else 0.0
                high = 1.0 - float(inst.value("min_second")) / length if length > 0 else 1.0
                share = round(min(max(share, low, 0.0), max(low, min(high, 1.0))), 6)
                if share == float(inst.value("position")):
                    return
                bound = inst.models.get("position")
                if bound is not None:
                    bound[1].assign(bound[0], share)
                elif isinstance(inst.props.get("position"), Signal):
                    inst.props["position"].set(share)

            def down(event: Any, inst: Instance = inst, handle: Any = handle) -> None:
                self._split_dragging.add(inst.id)
                handle.capture_pointer()

            def move(event: Any, inst: Instance = inst, first: Any = first, horizontal: bool = horizontal, room: Callable[[], float] = room,
                     user: Callable[[float], None] = user) -> None:
                pointer = event.window_x if horizontal else event.window_y
                length = room()
                if inst.id not in self._split_dragging or pointer is None or length <= 0:
                    return
                start = float(first.get("layout_x" if horizontal else "layout_y"))
                user((pointer - start - SPLIT_HANDLE / 2) / length)  # the handle's middle under the pointer

            def up(event: Any, inst: Instance = inst, handle: Any = handle, user: Callable[[float], None] = user) -> None:
                if inst.id not in self._split_dragging:
                    return
                self._split_dragging.discard(inst.id)
                handle.release_pointer()
                now = time.monotonic()
                if inst.value("collapsible") and now - self._split_last_up.get(inst.id, -1e9) <= self.DOUBLE_CLICK:
                    share = float(inst.value("position"))
                    if share > 0:
                        self._split_kept[inst.id] = share
                        user(0.0)
                    else:
                        user(self._split_kept.get(inst.id, 0.5))
                    self._split_last_up.pop(inst.id, None)
                else:
                    self._split_last_up[inst.id] = now

            forward, back = ("arrow_right", "arrow_left") if horizontal else ("arrow_down", "arrow_up")

            def key(event: Any, inst: Instance = inst, forward: str = forward, back: str = back, user: Callable[[float], None] = user) -> None:
                share = float(inst.value("position"))
                moves = {forward: share + self.SPLIT_STEP, back: share - self.SPLIT_STEP, "home": 0.0, "end": 1.0}
                if event.key in moves:
                    user(moves[event.key])

            for event_name, fn in (("pointer_down", down), ("pointer_move", move), ("pointer_up", up), ("pointer_cancel", up), ("key_down", key)):
                self._handler_undos.append(self._listen(handle, event_name, fn))
            self._handler_undos.append(a11y_module.on_action(handle, {
                "increment": lambda e, inst=inst, user=user: user(float(inst.value("position")) + self.SPLIT_STEP),
                "decrement": lambda e, inst=inst, user=user: user(float(inst.value("position")) - self.SPLIT_STEP),
                "set_value": lambda e, user=user: user(float(e.value)),
            }, listen=self._listen))

    # labelled controls (#175)

    def screen_of(self, record: Any) -> Any:
        """The same stand-in each time for the routed call `record` (the app tells a rebuilt screen by it): it has the node's root, once there is one, and no ViewModel of its own."""
        screen = self._screens.get(id(record))
        if screen is None or screen.record is not record:
            screen = self._screens[id(record)] = _Screen(self, record)
        return screen

    def _wire_measures(self) -> None:
        """A Container with `measured_width` / `measured_height` bound is told how big it is laid out, once the layout has run and whenever the window resizes."""
        if self._measure_undo is not None:
            self._measure_undo()
            self._measure_undo = None
        measured = [(inst, prop, name, scope) for inst in self.handle.composition.walk() if inst.widget == "Container" and inst.id in self._built.nodes
                    for prop, (name, scope) in inst.models.items() if prop in _MEASURED]
        if not measured:
            return

        def report(event: Any = None) -> None:
            for inst, prop, name, scope in measured:
                if inst.disposed or inst.id not in self._built.nodes:
                    continue
                size = float(self._built.nodes[inst.id].get("layout_width" if prop == "measured_width" else "layout_height") or 0.0)
                held = scope.lookup(name)
                if (held.get() if isinstance(held, Signal) else held) != size:
                    scope.assign(name, size)

        self.timers.after(0, report, name="measure")
        self._measure_undo = listen_window(self.window, "resize", lambda event: self.timers.after(0, report, name="measure"))

    def _wire_frames(self) -> None:
        """An Image with a `frame` shows each new one as it is given (a video: the app pushes `(rgba, width, height)`); none yet leaves the last."""
        for effect in self._frame_effects:
            effect.dispose()
        self._frame_effects = []
        for inst in self.handle.composition.walk():
            if inst.widget != "Image" or "frame" not in inst.props or inst.id not in self._built.nodes:
                continue

            def show(inst: Instance = inst) -> None:
                frame = inst.value("frame")  # the Effect follows what this reads
                if frame is None:
                    return
                try:
                    untrack(lambda: self._show_frame(inst.id, self._built.nodes[inst.id], frame))
                except (TypeError, ValueError) as exc:
                    raise ValueError(f"{inst.id}: a frame is (rgba bytes, width, height): {exc}") from None
            self._frame_effects.append(Effect(show))

    def _wire_fields(self) -> None:
        """A Checkbox, RadioButton or Switch with a `label` is a row of the control and its text; a press on the text is a press on the control
        (it takes the focus and toggles, or selects), and a press on the control itself is its own."""
        for undo in self._field_undos:
            undo()
        self._field_undos = []
        for inst in self.handle.composition.walk():
            field_id = f"{inst.id}.field"
            if field_id not in self._built.nodes or inst.id not in self._built.controls:
                continue
            control = self._built.controls[inst.id]

            def press(event: Any, control: Any = control) -> None:
                if control.disabled.get():
                    return  # (the control's own press is handled, and does not reach this row)
                control.node.focus()
                control._activate()

            self._field_undos.append(self._listen(self._built.nodes[field_id], "click", handled(press)))

    # links (#174)

    def _wire_links(self) -> None:
        """A Link's `href` (opened in the OS's browser or mail program when it is activated, which also marks it `visited`) and its underline (under
        the pointer or the keyboard focus, always, or never)."""
        for undo in self._link_undos:
            undo()
        self._link_undos = []
        for inst in self.handle.composition.walk():
            if inst.widget != "Link" or inst.id not in self._built.outer:
                continue
            box, text = self._built.outer[inst.id], self._built.nodes[inst.id]
            mode = inst.value("underline")

            def underline(inst: Instance = inst, text: Any = text, mode: str = mode) -> None:
                on = mode == "always" or (mode == "hover" and bool(self._link_hot.get(inst.id)))
                size = len(str(text.get("text")).encode("utf-8"))
                text.set(spans=[(0, size, {"underline": True})] if on and size else [])

            def heat(reason: str, on: bool, inst: Instance = inst, underline: Callable[[], None] = underline) -> Callable[[Any], None]:
                def change(event: Any = None) -> None:
                    if reason == "focus" and on and not getattr(event, "focus_visible", True):
                        return  # focus a mouse click gave is not a reason to underline
                    hot = self._link_hot.setdefault(inst.id, set())
                    hot.add(reason) if on else hot.discard(reason)
                    underline()
                return change

            underline()  # a re-sync put the text back as the spec has it
            for event_name, reason, on in (("pointer_enter", "pointer", True), ("pointer_leave", "pointer", False),
                                           ("focus", "focus", True), ("unfocus", "focus", False)):
                self._link_undos.append(self._listen(box, event_name, heat(reason, on)))

            def follow(event: Any = None, inst: Instance = inst) -> None:
                href = inst.value("href")
                if not href or inst.value("disabled"):
                    return
                try:
                    opened = urls.open_url(href)
                except ValueError as exc:
                    from loguru import logger

                    logger.warning("Link {}: {}", inst.id, exc)
                    return
                bound = inst.models.get("visited")
                if opened and bound is not None:
                    bound[1].assign(bound[0], True)

            self._link_undos.append(self._listen(box, "click", follow))

    # tooltips (#238)

    #: how long the pointer rests on a node before its tooltip shows (Material 3: 500 ms), and the widest a plain one is
    TIP_DELAY = 500.0
    TIP_WIDTH = 200.0
    #: how long a rich tooltip waits for the pointer to move onto it, after it leaves the node
    TIP_GRACE = 150.0

    def _tip_rich(self, inst: Instance) -> bool:
        """A rich tooltip has a subhead or actions (Material 3): it is a card the pointer can enter."""
        return bool(self._tip_value(inst, "title") or inst.tooltip.get("actions"))

    def _run_handler(self, held: tuple[Any, Any]) -> None:
        handler, scope = held
        if handler.action is not None:
            scope.call_action(handler.action, [], {})
        else:
            handler.statements.run(scope, event=None)

    def _tip_value(self, inst: Instance, name: str, default: Any = None) -> Any:
        held = inst.tooltip.get(name, default)
        return held.get() if hasattr(held, "get") else held

    def _wire_tooltips(self) -> None:
        """A node's `tooltip:` shows in a layer next to it when the pointer rests on it for `delay` (500 ms) or at once when keyboard focus lands on
        it, and goes when the pointer leaves, it is pressed, focus leaves, or Escape is pressed. The text also goes to the node as its accessibility
        `description` where it has none."""
        for undo in self._tip_undos:
            undo()
        self._tip_undos = []
        live: set[str] = set()
        tipped = list(self.handle.composition.walk()) + [_SpecTip(node_id, spec["tooltip"]) for node_id, spec in self._built.specs.items()
                                                         if isinstance(spec.get("tooltip"), dict)]
        for inst in tipped:  # the instances that have a `tooltip:`, and the generated nodes (a title bar's buttons) whose spec says so
            if not inst.tooltip or inst.id not in self._built.outer:
                continue
            live.add(inst.id)
            node = self._built.outer[inst.id]
            if "description" not in inst.a11y and self._tip_value(inst, "text"):
                a11y_module.apply_extras(node, {"description": str(self._tip_value(inst, "text"))})

            def start(event: Any = None, inst: Instance = inst) -> None:
                self.timers.after(float(self._tip_value(inst, "delay", self.TIP_DELAY)), lambda: self._show_tip(inst), name=f"tip:{inst.id}")

            def now(event: Any = None, inst: Instance = inst) -> None:
                if getattr(event, "focus_visible", True):  # a mouse click that focuses it is not a reason to show it
                    self._show_tip(inst)

            def held(event: Any = None, inst: Instance = inst) -> None:
                self._show_tip(inst)

            def away(event: Any = None, inst: Instance = inst) -> None:
                self.timers.cancel(f"tip:{inst.id}")
                self._hide_tip(inst.id)

            def leave(event: Any = None, inst: Instance = inst) -> None:
                """A rich tooltip stays while the pointer moves onto it: it goes a moment after the pointer leaves the node, unless it has arrived."""
                if inst.id in self._tips and self._tip_rich(inst):
                    self.timers.cancel(f"tip:{inst.id}")
                    self.timers.after(self.TIP_GRACE, lambda: self._hide_tip(inst.id), name=f"tipclose:{inst.id}")
                else:
                    away(event)

            for event_name, fn in (("pointer_enter", start), ("pointer_leave", leave), ("pointer_down", away), ("focus", now), ("unfocus", away),
                                   ("long_press", held)):
                self._tip_undos.append(self._listen(node, event_name, fn))
        for gone in set(self._tips) - live:
            self._hide_tip(gone)

    def _show_tip(self, inst: Instance) -> None:
        text = self._tip_value(inst, "text")
        if inst.id in self._tips or not text or not str(text).strip() or inst.id not in self._built.outer:
            return
        scheme = self._scheme or tokens.BASELINE
        title = self._tip_value(inst, "title")
        actions = inst.tooltip.get("actions") or []
        rich = self._tip_rich(inst)
        ink = scheme["on_surface" if rich else "inverse_on_surface"]
        pad_x, pad_y = (16.0, 12.0) if rich else (8.0, 4.0)
        layer = self.window.create(
            "box", flex_direction="vertical", gap=4.0, fill=scheme["surface_container" if rich else "inverse_surface"],
            corner_radius=12.0 if rich else 4.0, max_width=self.TIP_WIDTH, padding_left=pad_x, padding_right=pad_x, padding_top=pad_y,
            padding_bottom=pad_y, hit_testable=rich, a11y_hidden=True,
            shadows=tokens.elevation_shadows(2) if rich else [])
        if title:
            layer.add_child(self.window.create("text", text=str(title), font_family="Roboto", font_size=14.0, font_weight=500.0, fill=ink))
        layer.add_child(self.window.create("text", text=str(text), font_family="Roboto", font_size=12.0, fill=ink, wrap="word"))
        undos = []
        if actions:
            row = self.window.create("box", flex_direction="horizontal", gap=8.0, margin_top=8.0, justify_content="end")
            for label, held in actions:
                button = self.window.create("box", padding_left=12.0, padding_right=12.0, padding_top=6.0, padding_bottom=6.0, corner_radius=16.0,
                                            focusable=True, role="button", label=str(label.get() if hasattr(label, "get") else label))
                button.add_child(self.window.create("text", text=str(label.get() if hasattr(label, "get") else label), font_family="Roboto",
                                                    font_size=14.0, font_weight=500.0, fill=scheme["primary"]))
                undos.append(self._listen(button, "click", lambda event, held=held, inst_id=inst.id: (self._run_handler(held), self._hide_tip(inst_id))))
                row.add_child(button)
            layer.add_child(row)
        if rich:  # the pointer on the card keeps it; leaving it closes it
            undos.append(self._listen(layer, "pointer_enter", lambda event, inst_id=inst.id: self.timers.cancel(f"tipclose:{inst_id}")))
            undos.append(self._listen(layer, "pointer_leave", lambda event, inst_id=inst.id: self.timers.after(
                self.TIP_GRACE, lambda: self._hide_tip(inst_id), name=f"tipclose:{inst_id}")))
        self.window.show_layer(layer, anchor=self._built.outer[inst.id], placement=self._tip_value(inst, "placement", "below"), modal=False,
                               dismissible=False)

        def escape(event: Any, inst_id: str = inst.id) -> None:
            if event.key == "escape":
                self._hide_tip(inst_id)

        undos.append(self._listen(self.window.root, "key_down", escape))
        self._tips[inst.id] = (layer, lambda: [undo() for undo in undos])

    def _hide_tip(self, inst_id: str) -> None:
        shown = self._tips.pop(inst_id, None)
        self.timers.cancel(f"tipclose:{inst_id}")
        if shown is not None:
            shown[1]()
            self.window.hide_layer(shown[0])

    # overlays (#227)

    def _wire_overlays(self) -> None:
        """Shows and hides the layer of each `Overlay` as its `open` says, and hears the layer asked to close (Escape, a press outside)."""
        for undo in self._overlay_undos:
            undo()
        self._overlay_undos = []
        live: set[str] = set()
        for inst in self.handle.composition.walk():
            if inst.widget != "Overlay" or inst.id not in self._built.outer:
                continue
            live.add(inst.id)
            layer = self._built.nodes[inst.id]
            wanted = bool(inst.value("open"))
            if not wanted:
                self._dismissed_open.discard(inst.id)
            elif inst.id in self._dismissed_open:
                wanted = False
            shown = self._shown_layers.get(inst.id)
            if wanted and shown is None:
                self._show_layer(inst, layer)
            elif not wanted and shown is not None:
                self._hide_layer(inst.id)
            elif wanted:
                self._fit_layer(inst, layer)  # a patch put the layer's own size back
            self._overlay_undos.append(self._listen(layer, "dismiss", lambda event, inst=inst: self._dismiss_layer(inst)))
            if inst.value("modal") and inst.value("dismissible") is not False:  # the scrim is the layer, so a press on it is not "outside"
                self._overlay_undos.append(self._listen(layer, "pointer_down", lambda event, inst=inst, layer=layer: (
                    self._dismiss_layer(inst) if getattr(event, "target", None) == layer else None)))
        for gone in set(self._shown_layers) - live:
            self._hide_layer(gone)

    def _anchor_node(self, inst: Instance) -> Optional[Any]:
        name = inst.value("anchor")
        if not name:
            return None
        if name == "parent":  # the node the overlay is written inside (a submenu opens beside the row that has it)
            if inst.parent is None or inst.parent.id not in self._built.outer:
                raise ValueError(f"Overlay {inst.id!r}: anchor 'parent' needs the overlay to be inside another node")
            return self._built.outer[inst.parent.id]
        here = inst
        while here is not None:  # the view the overlay is written in, then the one that called it, and so on out (a menu names its button in the caller's view)
            root = here.view_root or self.handle.composition.root
            for other in root.walk():
                if other.name == name and other.id in self._built.outer:
                    return self._built.outer[other.id]
            here = root.parent  # the node the view was called from, in the view that called it (None at the top)
        raise ValueError(f"Overlay {inst.id!r}: anchor {name!r} is no node by that name in this view")

    def _fit_layer(self, inst: Instance, layer: Any) -> None:
        if inst.value("modal"):  # the scrim fills the window
            root = self.window.root
            layer.set(width=float(root.get("layout_width") or 0.0), height=float(root.get("layout_height") or 0.0), position="absolute", x=0.0, y=0.0)

    def _show_layer(self, inst: Instance, layer: Any) -> None:
        self._fit_layer(inst, layer)
        anchor = None if inst.value("modal") else self._anchor_node(inst)
        self.window.show_layer(layer, anchor=anchor, placement=inst.value("placement") or "below", modal=bool(inst.value("modal")),
                               dismissible=inst.value("dismissible") is not False)
        self._shown_layers[inst.id] = layer
        if inst.value("focus_first") is True:
            self._focus_into(inst)
        self._start_layer_timeout(inst, layer)
        if inst.value("modal"):  # the scrim follows the window's size while it is up
            self._layer_resize[inst.id] = listen_window(self.window, "resize", lambda event, inst=inst, layer=layer: self._fit_layer(inst, layer))

    def _focus_into(self, inst: Instance) -> None:
        """Moves the focus to the first thing under `inst`: the first item of its first focus group, else the first focusable node."""
        groups = [g for g in inst.walk() if g.focus_group is not None]
        items = self._focus_items(groups[0]) if groups else []
        if not items:
            items = [(c, n) for c in inst.walk() if c is not inst and (n := self._focus_node(c)) is not None and n.get("focusable") and not n.get("disabled")]
        if items:
            items[0][1].focus()

    def _start_layer_timeout(self, inst: Instance, layer: Any) -> None:
        """An `Overlay` with a `timeout` closes itself that long after it opens; the pointer on it holds the time off until it leaves."""
        timeout = inst.value("timeout")
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or timeout <= 0:
            return
        name = f"overlay:{inst.id}"
        arm = lambda: self.timers.after(float(timeout), lambda: self._dismiss_layer(inst), name=name)  # noqa: E731
        arm()
        enter = self._listen(layer, "pointer_enter", lambda event: self.timers.cancel(name))
        leave = self._listen(layer, "pointer_leave", lambda event: arm())
        self._layer_timeouts[inst.id] = lambda: (enter(), leave(), self.timers.cancel(name))

    def _hide_layer(self, inst_id: str) -> None:
        stop = self._layer_timeouts.pop(inst_id, None)
        if stop is not None:
            stop()
        layer = self._shown_layers.pop(inst_id, None)
        undo = self._layer_resize.pop(inst_id, None)
        if undo is not None:
            undo()
        if layer is not None:
            self.window.hide_layer(layer)

    def _dismiss_layer(self, inst: Instance) -> None:
        """The user closed the layer: hide it, and write false to the Signal `open` is bound to (else keep it closed until `open` goes false)."""
        if inst.id not in self._shown_layers:
            return
        self._hide_layer(inst.id)
        bound = inst.models.get("open")
        if bound is not None:
            name, scope = bound
            scope.assign(name, False)
        else:
            self._dismissed_open.add(inst.id)
        if "on_dismiss" in inst.handlers and inst.id not in self._disabled_on:
            inst.fire("on_dismiss")

    def _wire_states(self) -> None:
        """Feeds the interaction Signals (`hovered`, `focused`, `pressed`) of the instances a rule or an expression asked about."""
        for undo in self._state_undos:
            undo()
        self._state_undos = []
        for inst in self.handle.composition.walk():
            if not inst._istates or inst.id not in self._built.outer:
                continue
            node = self._built.outer[inst.id]
            signals = inst._istates

            def setter(name: str, value: Any, signals: dict = signals) -> Callable[[Any], None]:
                return lambda event=None: signals[name].set(value(event) if callable(value) else value) if name in signals else None

            for event, name, value in (("pointer_enter", "hovered", True), ("pointer_leave", "hovered", False),
                                       ("pointer_down", "pressed", True), ("pointer_up", "pressed", False), ("pointer_cancel", "pressed", False),
                                       # focus events bubble: a widget is focused when something inside it is
                                       ("focus", "focused", True), ("unfocus", "focused", False),
                                       ("focus", "focus_visible", lambda e: bool(getattr(e, "focus_visible", False))), ("unfocus", "focus_visible", False)):
                if name in signals:
                    self._state_undos.append(self._listen(node, event, setter(name, value)))

    # focus

    def _focus_node(self, inst: Instance) -> Optional[Any]:
        """The node that takes focus for `inst` (a text field's input, a link's box), or `None` if it has none built."""
        if inst.id not in self._built.nodes:
            return None
        return self._built.outer[inst.id] if inst.widget == "Link" else self._built.nodes[inst.id]

    def focus(self, scope: Any, name: str) -> None:
        """`focus(name)` in a handler: gives the focus to the node called `name` in the view the handler was written in."""
        origin = scope.nearest_instance() if scope is not None else None
        root = (origin.view_root or self.handle.composition.root) if origin is not None else self.handle.composition.root
        for inst in root.walk():
            if inst.name == name:
                node = self._focus_node(inst)
                if node is None:
                    raise ValueError(f"focus({name!r}): that node is not on the screen")
                node.focus()
                return
        raise ValueError(f"focus({name!r}): no node by that name in this view")

    def _focus_items(self, group: Instance) -> list[tuple[Instance, Any]]:
        """The focus group's items: every focusable node under it, in order, not counting what a group inside it looks after."""
        items: list[tuple[Instance, Any]] = []

        def visit(inst: Instance) -> None:
            for child in inst.children:
                node = self._focus_node(child)
                if node is not None and child.focus_group is None and node.get("focusable") and child.id not in self._disabled_on \
                        and not node.get("disabled"):
                    items.append((child, node))
                if child.focus_group is None:
                    visit(child)

        visit(group)
        return items

    def _item_label(self, inst: Instance, node: Any) -> str:
        label = node.get("label")
        if label:
            return str(label)
        for sub in inst.walk():
            if sub.widget in ("Text", "Link") and "text" in sub.props:
                return str(sub.value("text"))
        return ""

    def _wire_focus_groups(self) -> None:
        """Roving tab stops and arrow keys for each `focus_group`: one item is in the Tab order, the arrow keys (by the group's mode), Home, End and
        typing the start of an item's name move the focus among them, and whichever item has the focus holds the tab stop."""
        for undo in self._group_undos:
            undo()
        self._group_undos = []
        for group in self.handle.composition.walk():
            if group.focus_group is None or group.id not in self._built.outer:
                continue
            items = self._focus_items(group)
            if not items:
                continue
            box = self._built.outer[group.id]
            ids = [inst.id for inst, _ in items]
            chosen = next((i for i, (_, node) in enumerate(items) if node.get("checked") is True or node.get("selected") is True or node.get("pressed") is True or node.get("current") not in (None, False)), 0)
            active = ids.index(self._active[group.id]) if self._active.get(group.id) in ids else chosen  # the first tab stop is the chosen item
            self._active[group.id] = ids[active]
            for index, (_, node) in enumerate(items):
                node.set(tab_index=0 if index == active else -1)

            def index_of(target: Any, items: list = items) -> Optional[int]:
                while target is not None:
                    for index, (_, node) in enumerate(items):
                        if target == node:
                            return index
                    target = target.parent()
                return None

            def hold(index: int, group: Instance = group, items: list = items) -> None:
                self._active[group.id] = items[index][0].id
                for other, (_, node) in enumerate(items):
                    node.set(tab_index=0 if other == index else -1)

            def on_focus(event: Any, hold: Callable = hold, index_of: Callable = index_of) -> None:
                index = index_of(event.target)
                if index is not None:
                    hold(index)

            def on_key(event: Any, group: Instance = group, items: list = items, hold: Callable = hold, index_of: Callable = index_of) -> None:
                key = getattr(event, "key", "")
                current = index_of(event.target)
                if current is None:
                    return
                before, after = _GROUP_KEYS[group.focus_group]  # type: ignore[index]
                if key in before:
                    target = (current - 1) % len(items)
                elif key in after:
                    target = (current + 1) % len(items)
                elif key == "Home":
                    target = 0
                elif key == "End":
                    target = len(items) - 1
                elif len(key) == 1 and key.isprintable() and not _is_text_input(event.target):
                    found = self._typeahead(key, current, items)
                    if found is None:
                        return
                    target = found
                else:
                    return
                hold(target)
                items[target][1].focus()

            self._group_undos.append(self._listen(box, "focus", on_focus))
            self._group_undos.append(self._listen(box, "key_down", on_key))

    def _typeahead(self, key: str, current: int, items: list[tuple[Instance, Any]]) -> Optional[int]:
        """The item whose name starts with what has been typed (a pause starts over), searching on from the current one. The same letter
        typed again and again goes on to the next item that starts with it."""
        typed, when = self._typed
        now = time.monotonic()
        text = (typed if now - when < TYPEAHEAD_RESET else "") + key.lower()
        self._typed = (text, now)
        labels = [self._item_label(inst, node).lower() for inst, node in items]
        repeated = len(text) > 1 and len(set(text)) == 1
        wanted = text[0] if repeated else text
        start = current + 1 if repeated else current
        for step in range(len(items)):
            index = (start + step) % len(items)
            if labels[index].startswith(wanted):
                return index
        return None

    def _enforce_input(self, inst: Instance, node: Any) -> None:
        """A `TextInput`'s `max_length` and `read_only`, which the engine's input does not have: an edit that breaks either is put right as it
        arrives, before any listener that writes the text back hears of it."""
        if inst.widget != "TextInput":
            return

        def enforce(event: Any = None) -> None:
            text = node.get("text")
            if inst.value("read_only") and text != inst.value("text"):
                node.set(text=inst.value("text"))
                return
            limit = inst.value("max_length")
            if limit and len(text) > limit:
                node.set(text=text[:limit])

        mask = Mask(inst.value("mask")) if inst.value("mask") else None

        def fit(event: Any = None) -> None:
            text = node.get("text")
            masked = mask.apply(text)
            if masked != text:
                node.set(text=masked)

        if inst.value("read_only") or inst.value("max_length"):
            self._handler_undos.append(self._listen(node, "change", enforce))
        if mask is not None:  # after the others: a read-only field is put back whole, a masked one fitted
            self._handler_undos.append(self._listen(node, "change", fit))

    def close(self) -> None:
        """Stops following the composition and releases it."""
        if self._effect is not None:
            self._effect.dispose()
        for effect in self._frame_effects:
            effect.dispose()
        if self._timers is not None:
            self._timers.cancel_all()
        for inst_id in list(self._tips):
            self._hide_tip(inst_id)
        for undo in (*self._tip_undos, *self._link_undos, *self._field_undos):
            undo()
        for inst_id in list(self._shown_layers):
            self._hide_layer(inst_id)
        for undo in self._overlay_undos:
            undo()
        for undo in (*self._handler_undos, *self._state_undos, *self._group_undos):
            undo()
        self._handler_undos, self._state_undos, self._group_undos = [], [], []
        self.handle.close()


def open_composed(doc: ViewDoc, bindings: Bindings, views: Any = None, *, base_dir: Optional[Path] = None, window: Any = None,
                  rules: Any = (), **kwargs: Any) -> ComposedView:
    """Opens `doc` against the ViewModel that serves its name and builds it: `kwargs` are `View`'s (theme seed, dark, ...)."""
    holder: list[ComposedView] = []
    handle = open_view(doc, bindings, views, actions=builtin_actions(lambda: holder[0] if holder else None, window), rules=rules)
    view = ComposedView(handle, base_dir=base_dir, window=window, **kwargs)
    holder.append(view)
    return view
