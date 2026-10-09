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

from tesserae.follow import app_of
from tesserae.listeners import handled
from tesserae.reactive import Effect, untrack
from tesserae.expr import compile_statements, is_action_name
from tesserae.spec.compose import Instance
from tesserae.timers import Timers
from tesserae.spec.images import extract_images
from tesserae.spec.lower import lower
from tesserae.spec.nodes import ViewDoc
from tesserae.view import _EVENTS, SURFACE_ACTIONS, WINDOW_ACTIONS, View

#: Events the renderer adds to the engine's: a key press, Enter in a field that is not multiline, and a pointer press (which, unlike a click,
#: does not make the node a button).
_KEY_EVENTS = {"on_key": "key_down", "on_submit": "key_down", "on_press": "pointer_down", "on_move": "pointer_move", "on_release": "pointer_up"}
#: The keys that move focus in a `focus_group`, by its mode, as (previous, next).
_GROUP_KEYS = {"horizontal": (("arrow_left",), ("arrow_right",)), "vertical": (("arrow_up",), ("arrow_down",)),
               "both": (("arrow_left", "arrow_up"), ("arrow_right", "arrow_down"))}
#: A pause this long (seconds) in typing starts a new type-ahead search.
#: The ScrollView properties the renderer writes (the caller binds a Signal or a state name to read them), and how near an edge counts as at it.
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


def scroll_direction(last: str, old: Any, new: Any) -> str:
    """`'down'` or `'up'` from a scroll event's offsets; the last direction when it did not move or the event has none."""
    if old is None or new is None or new == old:
        return last
    return "down" if new > old else "up"


def scroll_edges(offset: float, viewport: float, length: float) -> tuple[bool, bool]:
    """`(at_top, at_end)` for a scroll view `viewport` tall over content `length` tall. Before the first layout (a size of 0) nothing is known
    about the end, so it is not at it."""
    laid_out = viewport > 0 and length > 0
    return offset <= SCROLL_EDGE, laid_out and offset >= length - viewport - SCROLL_EDGE


def builtin_actions(view_ref: Callable[[], Any]) -> Callable[..., Optional[Callable[..., Any]]]:
    """The actions a handler may call without a ViewModel: `window.<action>`, `navigate.<screen>`, `navigate_to(screen)`, `surface.dismiss` and
    `focus(name)`, `capture()`, `release()`, `cursor(name)`, `after(ms, action[, name])`, `every(ms, action[, name])` and `cancel(name)`. `view_ref()` is the `ComposedView` they act for (it does not exist yet when composing starts)."""

    def resolve(path: str, scope: Any = None) -> Optional[Callable[..., Any]]:
        view = view_ref()
        if path == "focus":
            return lambda name: view.focus(scope, name)
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
            return lambda: getattr(app_of(view.window), rest)() if app_of(view.window) is not None else None
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
        if path == "navigate_to":
            return lambda screen: app_of(view.window).navigate(screen) if app_of(view.window) is not None else None
        if head == "surface" and rest in SURFACE_ACTIONS:
            from tesserae.overlays import dismiss_surface

            return lambda: dismiss_surface(view.root)
        return None

    resolve.wants_scope = True  # type: ignore[attr-defined]  # `focus` needs the widget the handler was written in
    return resolve


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
        if self._synced:
            untrack(lambda: self.reconcile(spec, frames))
        untrack(self._wire_instances)
        untrack(self._wire_scroll)
        untrack(self._wire_states)
        untrack(self._wire_focus_groups)
        untrack(lambda: self.root.get("visible") != visible and self.root.set(visible=visible))

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

                if tre_event == "change" and control is not None and hasattr(control, "on_change"):
                    self._handler_undos.append(control.on_change(lambda value, call=call: call(None)))
                elif tre_event == "click":
                    self._handler_undos.append(self._listen(node, tre_event, handled(call)))
                else:
                    self._handler_undos.append(self._listen(node, tre_event, call))
            for prop, (name, scope) in inst.models.items():
                if inst.widget == "ScrollView" and prop in _SCROLL_OUTPUTS:
                    continue  # `_wire_scroll`'s
                state = getattr(control, prop, None) if control is not None else None
                if state is not None and hasattr(control, "on_change"):
                    self._handler_undos.append(control.on_change(
                        lambda value, scope=scope, name=name, state=state: scope.assign(name, state.get())))
                else:
                    self._handler_undos.append(self._listen(
                        node, "change", lambda ev, scope=scope, name=name, node=node, prop=prop: scope.assign(name, node.get(prop))))

    def _wire_scroll(self) -> None:
        """A ScrollView's outputs: `scroll_offset`, `at_top`, `at_end` and `scroll_direction`, each written to the Signal or state name it was
        given, on every scroll and once the layout has settled."""
        for inst in self.handle.composition.walk():
            outputs = {prop: ref for prop, ref in inst.models.items() if prop in _SCROLL_OUTPUTS} if inst.widget == "ScrollView" else {}
            if inst.widget != "ScrollView" or not (outputs or "scroll_offset" in inst.props) or inst.id not in self._built.outer:
                continue
            outer, content = self._built.outer[inst.id], self._built.nodes[inst.id]
            last = self._scrolled.setdefault(inst.id, {"direction": "none"})  # kept across re-wiring: every write to a Signal re-syncs

            def report(event: Any = None, outputs: dict = outputs, outer: Any = outer, content: Any = content, last: dict = last) -> None:
                offset = float(outer.get("scroll_offset"))
                last["direction"] = scroll_direction(last["direction"], getattr(event, "old_value", None), getattr(event, "new_value", None))
                at_top, at_end = scroll_edges(offset, float(outer.get("layout_height")), float(content.get("layout_height")))
                values = {"scroll_offset": offset, "at_top": at_top, "at_end": at_end, "scroll_direction": last["direction"]}
                for prop, (name, scope) in outputs.items():
                    scope.assign(name, values[prop])

            if outputs:
                self._handler_undos.append(self._listen(outer, "scroll", report))

            def settle(inst: Instance = inst, outer: Any = outer, content: Any = content, report: Callable[..., None] = report) -> None:
                """On the first frame after a build: the offset that was asked for. tre clamps an offset to the content, which has no size until it
                has been laid out, and reading a layout property lays it out."""
                content.get("layout_height")
                if "scroll_offset" in inst.props:
                    outer.set(scroll_offset=float(inst.value("scroll_offset")))
                report()

            self.timers.after(0, settle, name=f"scroll:{inst.id}")

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
            active = ids.index(self._active[group.id]) if self._active.get(group.id) in ids else 0
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

        if inst.value("read_only") or inst.value("max_length"):
            self._handler_undos.append(self._listen(node, "change", enforce))

    def close(self) -> None:
        """Stops following the composition and releases it."""
        if self._effect is not None:
            self._effect.dispose()
        if self._timers is not None:
            self._timers.cancel_all()
        for undo in (*self._handler_undos, *self._state_undos, *self._group_undos):
            undo()
        self._handler_undos, self._state_undos, self._group_undos = [], [], []
        self.handle.close()


def open_composed(doc: ViewDoc, bindings: Bindings, views: Any = None, *, base_dir: Optional[Path] = None, window: Any = None,
                  rules: Any = (), **kwargs: Any) -> ComposedView:
    """Opens `doc` against the ViewModel that serves its name and builds it: `kwargs` are `View`'s (theme seed, dark, ...)."""
    holder: list[ComposedView] = []
    handle = open_view(doc, bindings, views, actions=builtin_actions(lambda: holder[0] if holder else None), rules=rules)
    view = ComposedView(handle, base_dir=base_dir, window=window, **kwargs)
    holder.append(view)
    return view
