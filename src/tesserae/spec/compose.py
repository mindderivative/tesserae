"""Composition: from parsed views to a live tree of instances (spec sections 6, 7 and 9.2; phase 4 of #209).

`Composer(views, viewmodel).compose(doc)` turns a parsed view (`nodes.parse_view`) into a `Composition`: a tree of `Instance`s, one per node that
will exist, in which

- a **view call** is replaced by the callee's root instance; the call's properties are the callee's params, and an expression written at the
  call site is evaluated in the **caller's** scope (and stays reactive inside the callee when it reads a reactive name);
- `widget: Slot` is replaced by the call's children for that slot, built in the **caller's** scope; a call with children to a view with no
  `Slot` (or to a slot the view does not have) is an error;
- `for:` expands a node once for each element (a static iterable is expanded once; a reactive one is **reconciled by `key:`** when it changes:
  elements whose key persists keep their instance, new keys are built, removed keys are disposed, order follows the list) and `if:` includes a
  node only while its expression is truthy (tested per element when both are given);
- `state:` is a per-instance `Signal` per name, visible to the node's subtree, written by handlers, and carried over when a view is composed
  again with `previous=` (hot reload) for the instances whose id is the same.

An `Instance` holds the node's widget, its id, its property values (a plain value, or a `Computed` when the expression is reactive), its style,
handlers (each with the scope it was written in) and its children, which change as the regions under it change; `Instance.on_children` tells a
builder what to add, remove or move. Building real nodes from instances is phase 5; this module never touches `tre`.

Ids: an instance id is its parent's id, a dot and the node's `name` or its place (`children[2]`), then `[key]` under a `for:`. A view call's id is
its own and the callee's root has it, so the callee's parts are `nav.label`. Slot content has the call's id as its parent, and its segment is
its `name` or `<slot>[i]` (`content[i]` for the default slot).
"""

from __future__ import annotations

from typing import Any, Callable, Iterable, Iterator, Mapping, Optional

from tesserae.expr import BUILTIN_FUNCTIONS, Expr, Template
from tesserae.reactive import Computed, Effect, Signal, untrack
from tesserae.spec.nodes import Handler, LoadError, Node, ViewDoc
from tesserae.spec.rules import INTERACTION_STATES, Identity, Rule, RuleSheet, ordered
from tesserae.spec.widgets import PropertyError, WidgetDecl

__all__ = ["Composer", "Composition", "Instance", "Scope"]

MAX_DEPTH = 64
#: Names a param, a loop variable or a state variable may not take (spec 8.7).
RESERVED = frozenset({"hovered", "focused", "pressed", "event", "app", "True", "False", "None"}) | frozenset(BUILTIN_FUNCTIONS)


class _StateValues(dict):
    """A frame that also answers `hovered`, `focused` and `pressed` with the interaction state of one instance, made when first read."""

    def __init__(self, values: Mapping[str, Any], inst: "Instance") -> None:
        super().__init__(values)
        self._inst = inst

    def __contains__(self, key: object) -> bool:
        return key in INTERACTION_STATES or dict.__contains__(self, key)

    def __getitem__(self, key: str) -> Any:
        if key in INTERACTION_STATES and not dict.__contains__(self, key):
            return self._inst.interaction_signal(key)
        return dict.__getitem__(self, key)


# -- scope -----------------------------------------------------------------------------------------------------------------


class Scope:
    """The names an expression reads: one frame of values (state, loop variables or params) over its parent, and at the end the
    ViewModel's public attributes. A `Signal` or `Computed` in a frame makes the name reactive."""

    def __init__(self, parent: Optional["Scope"] = None, values: Optional[Mapping[str, Any]] = None, *, root: Any = None,
                 readonly: bool = False, writable: Iterable[str] = (), actions: Optional[Callable[[str], Optional[Callable[..., Any]]]] = None,
                 states: Optional["Instance"] = None) -> None:
        self.parent = parent
        #: with `states`, the names `hovered`, `focused` and `pressed` are that instance's interaction state (spec 8.7)
        self.values = _StateValues(values or {}, states) if states is not None else dict(values or {})
        self.readonly = readonly  # loop variables and params are read-only; state is not (a model param holds the caller's Signal)
        self.writable = set(writable)
        self.root = root if root is not None or parent is None else parent.root
        #: built-in actions (`window.close`, `navigate.back`, `navigate_to(...)`): a function from a dotted name to a callable or None
        self.actions = actions if actions is not None or parent is None else parent.actions
        #: the instance whose own names and handlers these are (set on the scope of each built-in widget)
        self.instance: Optional["Instance"] = None

    def _frame(self, name: str) -> Optional["Scope"]:
        scope: Optional[Scope] = self
        while scope is not None:
            if name in scope.values:
                return scope
            scope = scope.parent
        return None

    def lookup(self, name: str) -> Any:
        frame = self._frame(name)
        if frame is not None:
            return frame.values[name]
        if name.startswith("_"):
            raise KeyError(name)
        if self.root is not None:
            try:
                return getattr(self.root, name)
            except AttributeError:
                pass
        source = getattr(self.actions, "app", None) if name == "app" else None  # a ViewModel of the new kind has no `.app`: the renderer's is the window's
        app = source() if source is not None else None
        if app is not None:
            return app
        raise KeyError(name)

    def names(self) -> list[str]:
        out: list[str] = []
        scope: Optional[Scope] = self
        while scope is not None:
            out.extend(scope.values)
            scope = scope.parent
        if self.root is not None:
            out.extend(n for n in dir(self.root) if not n.startswith("_"))
        return out

    def is_reactive(self, name: str) -> bool:
        frame = self._frame(name)
        if frame is not None:
            return isinstance(frame.values[name], (Signal, Computed))
        # the ViewModel: a Signal, a Computed or a plain attribute that may be replaced; a built-in function is static
        return name == "app" or (self.root is not None and not name.startswith("_") and hasattr(self.root, name))

    def assign(self, name: str, value: Any) -> None:
        frame = self._frame(name)
        if frame is not None:
            if frame.readonly and name not in frame.writable:
                raise KeyError(name)
            target = frame.values[name]
        elif self.root is not None and not name.startswith("_") and hasattr(self.root, name):
            target = getattr(self.root, name)
        else:
            raise KeyError(name)
        if not isinstance(target, Signal):
            raise KeyError(name)  # a param, a loop variable or a plain attribute is read-only
        target.set(value)

    def _action(self, path: str) -> Optional[Callable[..., Any]]:
        if self.actions is not None:
            built_in = self.actions(path, self) if getattr(self.actions, "wants_scope", False) else self.actions(path)
            if built_in is not None:
                return built_in
        if self.root is None:
            return None
        target: Any = self.root
        for part in path.split("."):
            if part.startswith("_") or not hasattr(target, part):
                return None
            target = getattr(target, part)
        return target if callable(target) and not isinstance(target, (Signal, Computed)) else None

    def nearest_instance(self) -> Optional["Instance"]:
        """The instance of the closest widget this scope belongs to."""
        scope: Optional[Scope] = self
        while scope is not None:
            if scope.instance is not None:
                return scope.instance
            scope = scope.parent
        return None

    def is_writable(self, name: str) -> bool:
        frame = self._frame(name)
        if frame is not None:
            return not frame.readonly or name in frame.writable
        return self.root is not None and not name.startswith("_") and isinstance(getattr(self.root, name, None), Signal)

    def is_action(self, path: str) -> bool:
        return self._action(path) is not None

    def call_action(self, path: str, args: list[Any], kwargs: dict[str, Any]) -> Any:
        action = self._action(path)
        if action is None:
            raise KeyError(path)
        return action(*args, **kwargs)


# -- instances -------------------------------------------------------------------------------------------------------------


class Instance:
    """One node that exists. `props` maps a property to its value, or to a `Computed` while its expression is reactive; read through
    `value()`. `handlers` pairs each event's `Handler` with the scope it was written in; `fire` runs one."""

    def __init__(self, node: Node, widget: str, id: str, decl: Optional[WidgetDecl] = None) -> None:
        self.node, self.widget, self.id, self.decl = node, widget, id, decl
        self.name: Optional[str] = node.name
        self.props: dict[str, Any] = {}
        self.parts: dict[str, list["Instance"]] = {}
        self.style: dict[str, Any] = {}
        self.classes: list[str] = list(node.classes)
        self.handlers: dict[str, tuple[Handler, Scope]] = {}
        self.a11y: dict[str, Any] = {}
        self.interaction: Any = node.interaction
        self.window_region: Optional[str] = node.window_region
        self.route: Optional[str] = node.route
        self.focus_group: Optional[str] = node.focus_group
        #: `text`, `title` and `delay` of the tooltip, each a value or a `Computed`; empty when the node has none
        self.tooltip: dict[str, Any] = {}
        #: the root of the view this node was written in (names are unique within it): where `focus(name)` looks
        self.view_root: Optional["Instance"] = None
        self.state: dict[str, Signal] = {}
        #: model properties given a bare writable reference: property -> (name, scope); what the user's edit is written back to
        self.models: dict[str, tuple[str, Scope]] = {}
        #: the ways a stylesheet rule can name this instance, and the interaction states some rule or expression has asked for
        self.identities: list[Identity] = []
        self._istates: dict[str, Signal] = {}
        self._rules: Optional[Computed] = None
        self._release_rules: list[Callable[[], None]] = []
        self.parent: Optional["Instance"] = None
        self.children: list["Instance"] = []
        self.disposed = False
        self._regions: list[_Region] = []
        #: a VirtualList's window, and the position in its list of an item of one
        self.virtual: Optional[Virtual] = None
        self.virtual_index: Optional[Signal] = None
        self._observers: list[Callable[["Instance", list["Instance"], list["Instance"]], None]] = []
        self._release: list[Callable[[], None]] = []

    def value(self, name: str) -> Any:
        """The current value of a property: what was given, else the declaration's default."""
        if name in self.props:
            held = self.props[name]
            return held.get() if isinstance(held, (Signal, Computed)) else held
        prop = self.decl.properties.get(name) if self.decl else None
        if prop is None:
            raise KeyError(name)
        return prop.default

    def style_value(self, name: str) -> Any:
        """The inline value of a style field (what the node or the call gave)."""
        held = self.style[name]
        return held.get() if isinstance(held, (Signal, Computed)) else held

    def effective_style(self) -> dict[str, Any]:
        """The style at the values things hold now: the stylesheet rules that match, then the inline fields over them."""
        resolved = dict(self._rules.get()) if self._rules is not None else {}
        for name in self.style:
            resolved[name] = self.style_value(name)
        return resolved

    def interaction_signal(self, name: str) -> Signal:
        """The Signal for `hovered`, `focused` or `pressed`, made on first use; a renderer that sees one here wires the events to it."""
        signal = self._istates.get(name)
        if signal is None:
            signal = self._istates[name] = Signal(False)
        return signal

    def on_children(self, callback: Callable[["Instance", list["Instance"], list["Instance"]], None]) -> Callable[[], None]:
        """Calls `callback(instance, old_children, new_children)` when the children change; returns the undo."""
        self._observers.append(callback)
        return lambda: self._observers.remove(callback) if callback in self._observers else None

    def fire(self, event: str, payload: Any = None) -> None:
        """Runs the handler for `event` in the scope it was written in."""
        handler, scope = self.handlers[event]
        if handler.action is not None:
            scope.call_action(handler.action, [], {})
        else:
            assert handler.statements is not None
            handler.statements.run(scope, event=payload)

    def walk(self) -> Iterator["Instance"]:
        yield self
        for sub in self.parts.values():
            for inst in sub:
                yield from inst.walk()
        for child in self.children:
            yield from child.walk()

    def _refresh(self) -> None:
        new = [inst for region in self._regions for inst in region.instances]
        if len(new) == len(self.children) and all(a is b for a, b in zip(new, self.children)):
            return
        old, self.children = self.children, new
        for child in new:
            child.parent = self
        for callback in list(self._observers):
            callback(self, old, new)

    def dispose(self) -> None:
        if self.disposed:
            return
        self.disposed = True
        for release in self._release_rules:
            release()
        self._release_rules = []
        for region in self._regions:
            region.dispose()
        for sub in self.parts.values():
            for inst in sub:
                inst.dispose()
        for release in self._release:
            release()
        self._release.clear()

    def __repr__(self) -> str:
        return f"<Instance {self.widget} {self.id}>"


def _read(inst: Instance, name: str) -> Any:
    """A property of a built-in instance, or `None` when it has none by that name."""
    try:
        return inst.value(name)
    except KeyError:
        return None


def _state_holds(rule: Rule, inst: Instance, ident: Identity) -> bool:
    if rule.state is None:
        return True
    if rule.state in INTERACTION_STATES:  # the state of the widget the rule names, which for a part is the whole widget
        return bool((ident.interaction or inst.interaction_signal)(rule.state).get())
    return bool(ident.get(rule.state))


def _release_computed(computed: Computed) -> Callable[[], None]:
    def release() -> None:
        for dependency in computed._dependencies:
            dependency._unsubscribe(computed._recompute)
        computed._dependencies = []

    return release


# -- regions: what produces the instances under a parent --------------------------------------------------------------------


class _Region:
    """Something under a parent that yields zero or more instances and says when they change."""

    def __init__(self, notify: Callable[[], None]) -> None:
        self.instances: list[Instance] = []
        self.notify = notify

    def dispose(self) -> None:
        for inst in self.instances:
            inst.dispose()
        self.instances = []

    def _set(self, new: list[Instance]) -> None:
        if len(new) == len(self.instances) and all(a is b for a, b in zip(new, self.instances)):
            return
        self.instances = new
        self.notify()


class _Single(_Region):
    def __init__(self, notify: Callable[[], None], inst: Instance) -> None:
        super().__init__(notify)
        self.instances = [inst]


class _Group(_Region):
    """Several regions in a row (a slot's content)."""

    def __init__(self, notify: Callable[[], None]) -> None:
        super().__init__(notify)
        self.subs: list[_Region] = []

    def add(self, make: Callable[[Callable[[], None]], _Region]) -> None:
        self.subs.append(make(self._refresh))
        self._refresh()

    def _refresh(self) -> None:
        self._set([inst for sub in self.subs for inst in sub.instances])

    def dispose(self) -> None:
        for sub in self.subs:
            sub.dispose()
        self.subs, self.instances = [], []


class _If(_Region):
    def __init__(self, notify: Callable[[], None], condition: Expr, scope: Scope, make: Callable[[], Instance]) -> None:
        super().__init__(notify)
        self._condition, self._scope, self._make = condition, scope, make
        self._effect: Optional[Effect] = None
        if condition.is_reactive(scope):
            self._effect = Effect(self._run)
        else:
            self._run()

    def _run(self) -> None:
        truthy = bool(self._condition.evaluate(self._scope))  # read inside the effect: these are the dependencies
        if truthy and not self.instances:
            self._set([untrack(self._make)])
        elif not truthy and self.instances:
            old = self.instances
            self._set([])
            for inst in old:
                inst.dispose()

    def dispose(self) -> None:
        if self._effect is not None:
            self._effect.dispose()
        super().dispose()


class _Element:
    def __init__(self, signals: dict[str, Signal], region: _Region) -> None:
        self.signals, self.region = signals, region


class Virtual:
    """The window of a `VirtualList`: how many items there are, how tall each is, and which of them have instances. The renderer, which knows
    the scroll position and the height of the viewport, sets the window; the list's `for:` realizes only the items in it (#228)."""

    #: items realized before the renderer has said what is in view
    INITIAL = 24

    def __init__(self, extent: Callable[[], float], overscan: Callable[[], int]) -> None:
        self.extent, self.overscan = extent, overscan
        self.count = 0
        self.first, self.last = 0, self.INITIAL - 1
        self._reconcile: Optional[Callable[[], None]] = None

    def window_for(self, offset: float, viewport: float) -> tuple[int, int]:
        """The first and last item to realize for a viewport `viewport` tall scrolled `offset`, with the overscan on each side."""
        height, margin = float(self.extent()), int(self.overscan())
        first = max(0, int(offset // height) - margin)
        last = min(self.count - 1, int((offset + viewport) // height) + margin)
        return first, last

    def set_window(self, first: int, last: int) -> None:
        """Realize items `first` to `last`; does nothing if that is the window already."""
        if (first, last) == (self.first, self.last):
            return
        self.first, self.last = first, last
        if self._reconcile is not None:
            self._reconcile()


class _For(_Region):
    """A `for:`: one element per item, reconciled by key when the iterable is reactive."""

    def __init__(self, node: Node, scope: Scope, notify: Callable[[], None],
                 make_element: Callable[[Scope, str, Callable[[], None]], _Region], fail: Callable[[str, Optional[str]], LoadError],
                 virtual: Optional[Virtual] = None) -> None:
        super().__init__(notify)
        assert node.loop is not None
        self.virtual = virtual
        self._items_now: list[Any] = []
        self.node, self.loop, self.scope = node, node.loop, scope
        self._make, self._fail = make_element, fail
        self.elements: dict[Any, _Element] = {}
        self._order: list[Any] = []
        self.reactive = self.loop.iterable.is_reactive(scope)
        if self.reactive and node.key is None:
            raise fail("a reactive 'for:' needs a 'key:'", f"'{self.loop.source}' reads a name that can change; write key: item.id")
        for name in self.loop.targets:
            if name in RESERVED:
                raise fail(f"'{name}' is a reserved name and cannot be a loop variable", None)
        self._effect: Optional[Effect] = None
        if virtual is not None:
            virtual._reconcile = lambda: untrack(lambda: self._reconcile(self._items_now))
        if self.reactive:
            self._effect = Effect(self._run)
        else:
            self._run()

    def _items(self, raw: Any) -> list[Any]:
        if isinstance(raw, (list, tuple, range, str, Mapping)):
            return list(raw)
        raise self._fail(f"'for:' needs a list, tuple, dict, range or text, got {type(raw).__name__}", None)

    def _run(self) -> None:
        raw = self.loop.iterable.evaluate(self.scope)  # inside the effect: this is what the loop depends on
        untrack(lambda: self._reconcile(self._items(raw)))

    def _values(self, item: Any) -> dict[str, Any]:
        targets = self.loop.targets
        if len(targets) == 1:
            return {targets[0]: item}
        if not isinstance(item, (tuple, list)) or len(item) != len(targets):
            raise self._fail(f"'for: {self.loop.source}' unpacks {len(targets)} names from {item!r}", None)
        return dict(zip(targets, item))

    def _key(self, index: int, values: dict[str, Any]) -> Any:
        if self.node.key is None:
            return index
        key = self.node.key.evaluate(Scope(self.scope, values, readonly=True))
        try:
            hash(key)
        except TypeError:
            raise self._fail(f"'key:' must be text, a number or another plain value, got {type(key).__name__}", None) from None
        return key

    def _reconcile(self, items: list[Any]) -> None:
        order: list[Any] = []
        fresh: dict[Any, _Element] = {}
        self._items_now = items
        window = range(len(items)) if self.virtual is None else range(self.virtual.first, min(self.virtual.last, len(items) - 1) + 1)
        if self.virtual is not None:
            self.virtual.count = len(items)
        for index in window:
            item = items[index]
            values = self._values(item)
            key = self._key(index, values)
            if key in fresh:
                raise self._fail(f"two elements have the key {key!r}", "a 'key:' is unique among the elements")
            element = self.elements.get(key)
            if element is None:
                signals = {n: Signal(v) for n, v in values.items()} if self.reactive else {}
                region = self._make(Scope(self.scope, signals if self.reactive else values, readonly=True), f"[{key}]", self._changed)
                element = _Element(signals, region)
            else:
                for name, value in values.items():
                    if name in element.signals:
                        element.signals[name].set(value)
            if self.virtual is not None:  # where in the list it is, for the renderer to place it
                for inst in element.region.instances:
                    if inst.virtual_index is None:
                        inst.virtual_index = Signal(index)
                    elif inst.virtual_index.get() != index:
                        inst.virtual_index.set(index)
            fresh[key] = element
            order.append(key)
        removed = [e for k, e in self.elements.items() if k not in fresh]
        self.elements, self._order = fresh, order
        self._changed()
        for element in removed:
            element.region.dispose()

    def _changed(self) -> None:
        self._set([inst for key in self._order for inst in self.elements[key].region.instances])

    def dispose(self) -> None:
        if self._effect is not None:
            self._effect.dispose()
        for element in self.elements.values():
            element.region.dispose()
        self.elements, self.instances = {}, []


# -- the composer ----------------------------------------------------------------------------------------------------------


class _Owner:
    """The view call a node is inside, as a stylesheet names it: the widget, how it reads that widget's properties, and where its rules read."""

    def __init__(self, widget: str, get: Callable[[str], Any], scope: Scope) -> None:
        self.widget, self.get, self.scope = widget, get, scope
        self.root: Optional[Instance] = None  # the view's root instance, whose interaction state a part's rules read


class _Ctx:
    """Where a node is being composed: its view, how deep, the slot content a view call passed, and the call it is inside."""

    def __init__(self, doc: ViewDoc, depth: int, chain: tuple[str, ...], slots: Optional[dict[str, list[tuple[int, Node]]]] = None,
                 slot_scope: Optional[Scope] = None, slot_ctx: Optional["_Ctx"] = None, call_id: str = "",
                 owner: Optional[_Owner] = None) -> None:
        self.doc, self.depth, self.chain = doc, depth, chain
        self.owner = owner
        self.slots, self.slot_scope, self.slot_ctx, self.call_id = slots or {}, slot_scope, slot_ctx, call_id


class Composition:
    """The result: `root`, and every live instance by id."""

    def __init__(self, root: Instance, composer: "Composer") -> None:
        self.root = root
        self._composer = composer

    def find(self, id: str) -> Optional[Instance]:
        found = self._composer.by_id.get(id)
        return found if found is not None and not found.disposed else None

    def walk(self) -> Iterator[Instance]:
        return self.root.walk()

    def ids(self) -> list[str]:
        return [i.id for i in self.walk()]

    def outline(self) -> Any:
        """`(widget, id, [children])` for the current tree: a plain value to compare in tests."""
        def go(inst: Instance) -> Any:
            return (inst.widget, inst.id, [go(c) for c in inst.children])
        return go(self.root)

    def dispose(self) -> None:
        self.root.dispose()


class Composer:
    """Composes views. `views` maps a view name to its parsed `ViewDoc` (or is a function that does); `viewmodel` is the object the views'
    names resolve against; `previous` is an earlier `Composition` whose state is carried over."""

    def __init__(self, views: Any = None, viewmodel: Any = None, *, previous: Optional[Composition] = None,
                 actions: Optional[Callable[[str], Optional[Callable[..., Any]]]] = None, rules: Iterable[RuleSheet] = ()) -> None:
        self._views = views if views is not None else {}
        self.viewmodel = viewmodel
        self.actions = actions
        #: stylesheet layers, lowest first (a widget's shipped looks, then the app's)
        self.rules = [sheet for sheet in rules if sheet.rules]
        self.by_id: dict[str, Instance] = {}
        self.states: dict[tuple[str, str, str], Signal] = {}
        self._previous = previous._composer.states if previous is not None else {}

    # public

    def compose(self, doc: ViewDoc) -> Composition:
        ctx = _Ctx(doc, 0, (doc.name or doc.file,))
        self._check_root(doc.root, ctx)
        scope = Scope(None, {}, root=self.viewmodel, actions=self.actions)
        return Composition(self._instance(doc.root, "root", scope, ctx, forced_id="root"), self)

    # errors and lookup

    def _fail(self, ctx: _Ctx, at: tuple[int, int], message: str, hint: Optional[str] = None) -> LoadError:
        return LoadError(message, file=ctx.doc.file, line=at[0], column=at[1], hint=hint, text=ctx.doc.text)

    def _check_root(self, root: Node, ctx: _Ctx) -> None:
        for directive, label in ((root.loop, "for"), (root.when, "if"), (root.slot, "slot")):
            if directive is not None:
                raise self._fail(ctx, root.at, f"the root of a view takes no '{label}:'")

    def _view(self, name: str) -> Optional[ViewDoc]:
        return self._views(name) if callable(self._views) else self._views.get(name)

    # regions

    def _region(self, node: Node, seg: str, parent_id: str, scope: Scope, ctx: _Ctx, notify: Callable[[], None], *,
                suffix: str = "", looped: bool = False, virtual: Optional[Virtual] = None) -> _Region:
        if node.widget == "Slot":
            return self._slot(node, ctx, notify)
        if node.loop is not None and not looped:
            def element(el_scope: Scope, key_suffix: str, changed: Callable[[], None]) -> _Region:
                return self._region(node, seg, parent_id, el_scope, ctx, changed, suffix=key_suffix, looped=True)

            return _For(node, scope, notify, element, lambda message, hint: self._fail(ctx, node.at, message, hint), virtual)

        def make() -> Instance:
            return self._instance(node, seg, scope, ctx, parent_id=parent_id, suffix=suffix)

        if node.when is not None:
            return _If(notify, node.when, scope, make)
        return _Single(notify, make())

    def _slot(self, node: Node, ctx: _Ctx, notify: Callable[[], None]) -> _Region:
        for directive, label in ((node.loop, "for"), (node.when, "if")):
            if directive is not None:
                raise self._fail(ctx, node.at, f"a Slot takes no '{label}:'")
        slot = node.name or "default"
        group = _Group(notify)
        outer, scope = ctx.slot_ctx, ctx.slot_scope
        for index, child in ctx.slots.get(slot, []):
            seg = f"{node.name or 'content'}[{index}]"
            assert outer is not None and scope is not None
            group.add(lambda changed, child=child, seg=seg: self._region(child, seg, ctx.call_id, scope, outer, changed))
        return group

    # instances

    def _instance(self, node: Node, seg: str, scope: Scope, ctx: _Ctx, *, parent_id: str = "", suffix: str = "",
                  forced_id: Optional[str] = None) -> Instance:
        iid = forced_id or f"{parent_id}.{node.name or seg}{suffix}"
        if node.decl.view:
            doc = self._view(node.widget)
            if doc is None:
                raise self._fail(ctx, node.at, f"no view named '{node.widget}'")
            return self._call(node, doc, iid, scope, ctx)
        return self._builtin(node, iid, scope, ctx, forced=forced_id is not None)

    def _register(self, inst: Instance, ctx: _Ctx) -> None:
        existing = self.by_id.get(inst.id)
        if existing is not None and not existing.disposed:
            raise self._fail(ctx, inst.node.at, f"two nodes have the id '{inst.id}'", "give one of them a different name")
        self.by_id[inst.id] = inst
        inst._release.append(lambda: self.by_id.pop(inst.id, None) if self.by_id.get(inst.id) is inst else None)

    def _with_state(self, node: Node, scope: Scope, inst_id: str, level: str, ctx: _Ctx, holder: Instance) -> Scope:
        if not node.state:
            return scope
        values: dict[str, Signal] = {}
        for name, initial in node.state.items():
            if name in RESERVED:
                raise self._fail(ctx, node.at, f"'{name}' is a reserved name and cannot be a state variable")
            if hasattr(initial, "is_reactive") and initial.is_reactive(scope):
                raise self._fail(ctx, node.at, f"the starting value of state '{name}' must be static")
            value = initial.evaluate(scope) if hasattr(initial, "evaluate") else initial
            key = (inst_id, name, level)
            previous = self._previous.get(key)
            signal = Signal(previous._value if previous is not None else value)
            self.states[key] = signal
            values[name] = signal
            holder.state[name] = signal
        return Scope(scope, values)

    # evaluation helpers

    def _bind(self, value: Any, scope: Scope, inst: Instance, coerce: Optional[Callable[[Any], Any]] = None) -> Any:
        """A property's value: a template evaluated now, or a `Computed` that follows the names it reads."""
        if not hasattr(value, "evaluate"):
            return value
        convert = coerce or (lambda v: v)
        if value.is_reactive(scope):
            computed = Computed(lambda: convert(value.evaluate(scope)))
            inst._release.append(_release_computed(computed))
            return computed
        return convert(value.evaluate(scope))

    def _coercer(self, ctx: _Ctx, node: Node, decl: Optional[WidgetDecl], name: str) -> Optional[Callable[[Any], Any]]:
        prop = decl.properties.get(name) if decl else None
        if prop is None or prop.type in ("node", "nodes"):
            return None

        def convert(value: Any) -> Any:
            try:
                return prop.coerce(value)
            except PropertyError as exc:
                raise self._fail(ctx, node.prop_at.get(name, node.at), f"{node.widget}: {exc.message}", exc.hint) from None

        return convert

    # built-in widgets

    def _builtin(self, node: Node, iid: str, scope: Scope, ctx: _Ctx, forced: bool = False) -> Instance:
        inst = Instance(node, node.widget, iid, node.decl)
        self._register(inst, ctx)
        if forced and ctx.owner is not None:
            ctx.owner.root = inst
        inst.view_root = ctx.owner.root if ctx.owner is not None else None
        inner = self._with_state(node, scope, iid, "node", ctx, inst)
        if node.interaction or forced:  # `hovered`, `focused` and `pressed` are the nearest interactive widget's (a call may make a root so)
            inner = Scope(inner, states=inst, readonly=True)
        inner.instance = inst
        inst.identities.append(Identity(node.widget, None, lambda name, inst=inst: _read(inst, name), inner, inst.interaction_signal))
        if ctx.owner is not None and node.name and not forced:
            owner = ctx.owner
            inst.identities.append(Identity(owner.widget, node.name, owner.get, owner.scope,
                                            lambda state, owner=owner: owner.root.interaction_signal(state) if owner.root else Signal(False)))
        for name, value in node.style.items():
            inst.style[name] = self._bind(value, inner, inst)
        for name, value in node.a11y.items():
            inst.a11y[name] = self._bind(value, inner, inst)
        for name, value in node.tooltip.items():
            inst.tooltip[name] = self._bind(value, inner, inst)
        for event, handler in node.handlers.items():
            inst.handlers[event] = (handler, inner)
        for name, value in node.props.items():
            nodes = [value] if isinstance(value, Node) else value if isinstance(value, list) and value and all(isinstance(v, Node) for v in value) else None
            if nodes is None:
                inst.props[name] = self._bind(value, inner, inst, self._coercer(ctx, node, node.decl, name))
                bare = self._model_ref(node.decl, name, value, inner)
                if bare is not None:
                    inst.models[name] = (bare, inner)
                continue
            inst.parts[name] = [self._instance(sub, name if isinstance(value, Node) else f"{name}[{i}]", inner, ctx, parent_id=iid)
                                for i, sub in enumerate(nodes)]
            for sub in inst.parts[name]:
                sub.parent = inst
        if node.widget == "Splitter":
            if len(node.children) != 2 or any(c.loop is not None or c.when is not None for c in node.children):
                raise self._fail(ctx, node.at, "a Splitter has two panes: exactly two children, with no 'for:' or 'if:'")
            held = inst.props.get("position", 0.5)  # a number is where it starts; the handle moves it, so it is held in a Signal
            if not isinstance(held, (Signal, Computed)):
                inst.props["position"] = Signal(float(held))
        virtual: Optional[Virtual] = None
        if node.widget == "VirtualList":
            if len(node.children) != 1 or node.children[0].loop is None:
                raise self._fail(ctx, node.at, "a VirtualList has one child, and it has a 'for:'",
                                 "write the row once: children: [{for: row in rows, key: row.id, widget: ...}]")
            virtual = inst.virtual = Virtual(lambda: float(inst.value("item_height")), lambda: int(inst.value("overscan")))
        for index, child in enumerate(node.children):
            inst._regions.append(self._region(child, f"children[{index}]", iid, inner, ctx, inst._refresh, virtual=virtual))
        inst._refresh()
        self._install_rules(inst)
        return inst

    # stylesheet rules

    def _install_rules(self, inst: Instance) -> None:
        """Makes the `Computed` that resolves which rules apply to `inst` (again, when it gained a name from a view call)."""
        if inst._rules is not None:
            for release in inst._release_rules:
                release()
            inst._release_rules = []
            inst._rules = None
        if not self.rules:
            return
        widgets = {ident.widget for ident in inst.identities}
        layers = [(sheet, sheet.candidates(widgets)) for sheet in self.rules]
        if not any(candidates for _, candidates in layers):
            return

        def resolve() -> dict[str, Any]:
            style: dict[str, Any] = {}
            for _, candidates in layers:
                matched: list[tuple[Rule, Identity]] = []
                for rule in candidates:
                    for ident in inst.identities:
                        if rule.matches(ident, inst.classes, inst.name) and _state_holds(rule, inst, ident):
                            matched.append((rule, ident))
                            break
                for rule, ident in sorted(matched, key=lambda pair: (pair[0].specificity, pair[0].order)):
                    for field_name, value in rule.style.items():
                        style[field_name] = value.evaluate(ident.scope) if hasattr(value, "evaluate") else value
            return style

        inst._rules = Computed(resolve)
        inst._release_rules.append(_release_computed(inst._rules))

    def _model_ref(self, decl: Optional[WidgetDecl], name: str, value: Any, scope: Scope) -> Optional[str]:
        """The name a `model` property is two-way with: it is given one bare reference to a writable Signal (spec 9.3)."""
        prop = decl.properties.get(name) if decl else None
        if prop is None or not prop.model or not isinstance(value, Template) or not value.single:
            return None
        bare = value.parts[0].bare_name()
        if bare is None:
            return None
        try:
            return bare if isinstance(scope.lookup(bare), Signal) and scope.is_writable(bare) else None
        except KeyError:
            return None

    # view calls

    def _slots_of(self, doc: ViewDoc) -> list[str]:
        return [n.name or "default" for n in doc.root.walk() if n.widget == "Slot"]

    def _call(self, node: Node, doc: ViewDoc, iid: str, caller_scope: Scope, ctx: _Ctx) -> Instance:
        if ctx.depth + 1 > MAX_DEPTH:
            raise self._fail(ctx, node.at, f"views are nested more than {MAX_DEPTH} deep", " -> ".join(ctx.chain[-6:]))
        holder = Instance(node, node.widget, iid)  # carries the call's own state
        call_scope = self._with_state(node, caller_scope, iid, "call", ctx, holder)

        decl = doc.decl or WidgetDecl(node.widget, view=True, container=True)
        unknown = [k for k in node.props if k not in decl.properties]
        if unknown:
            raise self._fail(ctx, node.prop_at.get(unknown[0], node.at), f"{node.widget}: no parameter '{unknown[0]}'",
                             f"parameters: {', '.join(decl.properties) or 'none'}")
        values: dict[str, Any] = {}
        models: set[str] = set()
        for pname, prop in decl.properties.items():
            if pname in RESERVED:
                raise self._fail(ctx, node.at, f"'{pname}' is a reserved name and cannot be a parameter of {node.widget}")
            if pname in node.props:
                shared = self._model_ref(decl, pname, node.props[pname], call_scope)
                if shared is not None:  # a model param given a bare Signal: the callee gets the Signal, so its edits write back
                    values[pname] = call_scope.lookup(shared)
                    models.add(pname)
                    continue
                values[pname] = self._bind(node.props[pname], call_scope, holder, self._coercer(ctx, node, decl, pname))
            elif prop.required:
                raise self._fail(ctx, node.at, f"{node.widget}: '{pname}' is required")
            else:
                values[pname] = prop.default

        available = self._slots_of(doc)
        content: dict[str, list[tuple[int, Node]]] = {}
        for index, child in enumerate(node.children):
            slot = child.slot or "default"
            if not available:
                raise self._fail(ctx, child.at, f"{node.widget} takes no children", "its view has no Slot")
            if slot not in available:
                raise self._fail(ctx, child.at, f"{node.widget} has no slot '{slot}'", f"slots: {', '.join(available)}")
            content.setdefault(slot, []).append((index, child))

        callee_scope = Scope(None, values, root=self.viewmodel, readonly=True, writable=models, actions=self.actions)

        def param(name: str) -> Any:
            held = values.get(name)
            return held.get() if isinstance(held, (Signal, Computed)) else held

        sub = _Ctx(doc, ctx.depth + 1, (*ctx.chain, node.widget), content, call_scope, ctx, iid, owner=_Owner(node.widget, param, callee_scope))
        self._check_root(doc.root, sub)
        inst = self._instance(doc.root, "root", callee_scope, sub, forced_id=iid)
        # the call's own keys lie over the callee's root; a handler written at the call runs in the caller's scope
        for name, value in node.style.items():
            inst.style[name] = self._bind(value, call_scope, inst)
        for name, value in node.a11y.items():
            inst.a11y[name] = self._bind(value, call_scope, inst)
        for name, value in node.tooltip.items():
            inst.tooltip[name] = self._bind(value, call_scope, inst)
        for event, handler in node.handlers.items():
            inst.handlers[event] = (handler, call_scope)
        inst.classes = [*inst.classes, *node.classes]
        if node.interaction is not None:
            inst.interaction = node.interaction
        if node.window_region is not None:
            inst.window_region = node.window_region
        if node.route is not None:
            inst.route = node.route
        if node.focus_group is not None:
            inst.focus_group = node.focus_group
        if node.name is not None:
            inst.name = node.name
        inst.state = {**inst.state, **holder.state}
        inst._release.extend(holder._release)
        inst.identities.append(Identity(node.widget, None, param, callee_scope, inst.interaction_signal))
        self._install_rules(inst)
        return inst
