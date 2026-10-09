"""Binding ViewModels to views (spec section 11; phase 5 of #209).

A ViewModel serves **named** views: its class lists their names in `views`, and a view is named by its root `name:` (the bind key). One
ViewModel instance serves every view whose name it lists, wherever they are, so a pie chart and a list of the same rows are two views of one
`Signal`. A view without a name is not bound (a static visual).

- `Bindings` is what `app.bind` fills: `bind(DataViewModel)` makes the instance once, lazily, when the first view it serves is opened;
  `bind(instance)` uses one you made; `bind(factory=DataViewModel)` makes one per view instance.
- `open_view(doc, bindings, ...)` composes a parsed view against its ViewModel and returns a `ViewHandle`, which the ViewModel finds in
  `self.views[name]` (`.node(name)`, `.state(name)`, `.show()`, `.hide()`).
- `check_view(doc, viewmodel)` is the contract checker: every name and action a view uses, and every `expects:` entry, against a ViewModel,
  as one-line problems with file, line and column, without a window.

The ViewModel base class (`tesserae.ViewModel`) keeps its 0.4.x form, `ViewModel(view)`, for the compatibility release.
"""

from __future__ import annotations

import ast
from typing import Any, Callable, Iterable, Iterator, Optional

from tesserae.expr import BUILTIN_FUNCTIONS, Expr, Statements, Template
from tesserae.reactive import Computed, Signal, untrack
from tesserae.spec.compose import Composer, Composition, Instance
from tesserae.spec.nodes import Node, ViewDoc

__all__ = ["Bindings", "BindingError", "ViewHandle", "ViewHandles", "check_view", "declared_views", "open_view"]

#: Names an expression may read that no ViewModel provides.
_RESERVED_READS = frozenset({"app", "event", "hovered", "focused", "pressed", "True", "False", "None"})
#: Built-in action families: `window.close`, `surface.dismiss`, `navigate.back`, `navigate_to(...)`.
_ACTION_FAMILIES = ("window", "surface", "navigate", "navigate_to", "focus", "after", "every", "cancel")
_TYPES: dict[str, Callable[[Any], bool]] = {
    "int": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "float": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "str": lambda v: isinstance(v, str),
    "bool": lambda v: isinstance(v, bool),
    "list": lambda v: isinstance(v, (list, tuple)),
    "dict": lambda v: isinstance(v, dict),
    "any": lambda v: True,
}


class BindingError(ValueError):
    """A ViewModel that cannot be bound: two serve one name, or one cannot be made."""


def declared_views(target: Any) -> list[str]:
    """The view names a ViewModel class (or instance) serves: its `views`, where a string means one."""
    names = getattr(target if isinstance(target, type) else type(target), "views", ())
    if isinstance(names, str):
        return [names]
    return [n for n in (names or ()) if isinstance(n, str)]


# -- handles ---------------------------------------------------------------------------------------------------------------


class ViewHandle:
    """What a ViewModel holds of one of its views: the composed instances, whether it is shown, and a way back to named nodes."""

    def __init__(self, name: Optional[str], composition: Composition, viewmodel: Any, bindings: Optional["Bindings"] = None,
                 doc: Optional[ViewDoc] = None) -> None:
        self.name = name
        self.composition = composition
        self.viewmodel = viewmodel
        self.doc = doc
        self.visible = Signal(True)
        self._bindings = bindings
        self.closed = False

    def node(self, name: str) -> Instance:
        """The instance of the node called `name` (names are unique in a view)."""
        for inst in self.composition.walk():
            if inst.name == name:
                return inst
        raise KeyError(f"view {self.name!r} has no node named {name!r}")

    def state(self, var: str, node: Optional[str] = None) -> Signal:
        """The local state `var` of the named node (the root when no node is named)."""
        inst = self.node(node) if node is not None else self.composition.root
        try:
            return inst.state[var]
        except KeyError:
            raise KeyError(f"{'node ' + repr(node) if node else 'the root'} of view {self.name!r} has no state {var!r}") from None

    def show(self) -> None:
        self.visible.set(True)

    def hide(self) -> None:
        self.visible.set(False)

    def close(self) -> None:
        """Disposes the composition and tells the ViewModel the view has gone."""
        if self.closed:
            return
        self.closed = True
        self.composition.dispose()
        if self._bindings is not None:
            self._bindings._detach(self)

    def __repr__(self) -> str:
        return f"<ViewHandle {self.name!r}>"


class ViewHandles(dict):
    """`ViewModel.views` at run time: bind key to `ViewHandle`. A name the ViewModel serves whose view is not open says so."""

    def __init__(self, declared: Iterable[str] = ()) -> None:
        super().__init__()
        self._declared = list(declared)

    def __missing__(self, key: str) -> ViewHandle:
        if key in self._declared:
            raise KeyError(f"the view {key!r} is not open")
        raise KeyError(f"this ViewModel does not serve a view named {key!r}"
                       + (f" (it serves: {', '.join(self._declared)})" if self._declared else ""))


# -- bindings --------------------------------------------------------------------------------------------------------------


class _Entry:
    def __init__(self, names: list[str], instance: Any = None, cls: Optional[Callable[[], Any]] = None, factory: bool = False) -> None:
        self.names, self.instance, self.cls, self.factory = names, instance, cls, factory

    def label(self) -> str:
        target = self.instance if self.instance is not None else self.cls
        return getattr(target, "__name__", None) or type(target).__name__


class Bindings:
    """The ViewModels an app serves its views with."""

    def __init__(self) -> None:
        self._entries: list[_Entry] = []
        self._by_name: dict[str, _Entry] = {}

    def bind(self, target: Any = None, *, factory: Optional[Callable[[], Any]] = None, views: Optional[Iterable[str]] = None) -> None:
        """Serves views with a ViewModel: a class (one instance, made when its first view opens), an instance, or `factory=` (one per
        view instance). `views=` names the views when the target does not (a factory that is a function)."""
        if (target is None) == (factory is None):
            raise BindingError("bind(...) takes a ViewModel class or instance, or factory=...: exactly one")
        source = target if target is not None else factory
        if isinstance(source, str):
            raise BindingError(f"bind(...) takes a ViewModel, not the name {source!r}; the ViewModel's `views` names the views")
        names = list(views) if views is not None else declared_views(source)
        if not names:
            raise BindingError(f"{getattr(source, '__name__', type(source).__name__)} serves no views: give it `views = [...]`")
        if target is not None and not isinstance(target, type):
            entry = _Entry(names, instance=target)
        else:
            entry = _Entry(names, cls=source, factory=factory is not None)
        for name in names:
            if name in self._by_name:
                raise BindingError(f"the view {name!r} is already served by {self._by_name[name].label()}")
        for name in names:
            self._by_name[name] = entry
        self._entries.append(entry)

    def serves(self, view_name: str) -> bool:
        return view_name in self._by_name

    def viewmodel_for(self, view_name: Optional[str]) -> Any:
        """The ViewModel for a view with this bind key: the one instance (made on first use), a new one from a factory, or `None`
        for a view that is unnamed or that no ViewModel serves."""
        if view_name is None:
            return None
        entry = self._by_name.get(view_name)
        if entry is None:
            return None
        if entry.instance is None or entry.factory:
            try:
                made = entry.cls()  # type: ignore[misc]
            except TypeError as exc:
                raise BindingError(f"{entry.label()} could not be made without arguments ({exc}); a ViewModel that serves named views "
                                   "takes none (the 0.4.x form, ViewModel(view), is bound by app.load)") from None
            if entry.factory:
                return made
            entry.instance = made
        return entry.instance

    def _attach(self, handle: ViewHandle) -> None:
        vm = handle.viewmodel
        if vm is None or handle.name is None:
            return
        _handles_of(vm)[handle.name] = handle
        if getattr(vm, "_view", None) is None:
            vm._view = handle  # the first bound view, as `self.view` was
        hook = getattr(vm, "on_attached", None)
        if callable(hook):
            hook(handle)

    def _detach(self, handle: ViewHandle) -> None:
        vm = handle.viewmodel
        if vm is None or handle.name is None:
            return
        handles = _handles_of(vm)
        if handles.get(handle.name) is handle:
            del handles[handle.name]
        hook = getattr(vm, "on_detached", None)
        if callable(hook):
            hook(handle)

    def unserved(self, open_names: Iterable[str]) -> list[str]:
        """Warnings for ViewModels that serve a name none of `open_names` has."""
        have = set(open_names)
        return [f"{entry.label()} serves the view {name!r}, but no view has that name"
                for entry in self._entries for name in entry.names if name not in have]


def _handles_of(vm: Any) -> ViewHandles:
    handles = vm.__dict__.get("views")
    if not isinstance(handles, ViewHandles):
        handles = ViewHandles(declared_views(vm))
        vm.views = handles
    return handles


def open_view(doc: ViewDoc, bindings: Bindings, views: Any = None, *, actions: Optional[Callable[[str], Any]] = None,
              previous: Optional[ViewHandle] = None, rules: Iterable[Any] = ()) -> ViewHandle:
    """Composes `doc` against the ViewModel that serves its name and attaches it. `views` resolves the views `doc` calls."""
    vm = bindings.viewmodel_for(doc.name)
    composer = Composer(views, vm, previous=previous.composition if previous else None, actions=actions, rules=rules)
    handle = ViewHandle(doc.name, composer.compose(doc), vm, bindings, doc)
    bindings._attach(handle)
    return handle


# -- the contract ----------------------------------------------------------------------------------------------------------


def _called_names(statements: Statements) -> Iterator[str]:
    for statement in statements.body:
        for call in ast.walk(statement):
            if isinstance(call, ast.Call):
                parts = []
                func = call.func
                while isinstance(func, ast.Attribute):
                    parts.append(func.attr)
                    func = func.value
                if isinstance(func, ast.Name):
                    parts.append(func.id)
                    yield ".".join(reversed(parts))


def _expressions(node: Node) -> Iterator[tuple[Any, tuple[int, int]]]:
    """Every compiled expression, template and handler in a node, with a position to blame."""
    for value in (*node.props.values(), *node.style.values(), *node.a11y.values(), *node.state.values()):
        if isinstance(value, (Template, Expr)):
            yield value, node.at
    if node.when is not None:
        yield node.when, node.at
    if node.loop is not None:
        yield node.loop.iterable, node.at
    if node.key is not None:
        yield node.key, node.at
    for handler in node.handlers.values():
        yield handler, node.at


def _locals(doc: ViewDoc) -> set[str]:
    """Names the view defines for itself, anywhere in it: its params, its state variables and its loop variables."""
    names: set[str] = set(doc.decl.properties) if doc.decl else set()
    for node in doc.root.walk():
        names.update(node.state)
        if node.loop is not None:
            names.update(node.loop.targets)
    return names


def _check_type(vm: Any, name: str, type_name: str) -> Optional[str]:
    value = getattr(vm, name)
    if type_name == "handler":
        return None if callable(value) and not isinstance(value, (Signal, Computed)) else f"'{name}' should be a method"
    check = _TYPES.get(type_name)
    if check is None:
        return f"'{name}': unknown type {type_name!r}"
    if isinstance(value, (Signal, Computed)):
        value = untrack(value.get)
    return None if check(value) else f"'{name}' should be {type_name}, it is {type(value).__name__}"


def check_view(doc: ViewDoc, viewmodel: Any) -> list[str]:
    """Problems between a view and a ViewModel, as `file:line:column: message`. With no ViewModel, a view that needs one says so."""
    problems: list[str] = []
    local = _locals(doc)
    label = type(viewmodel).__name__ if viewmodel is not None else None

    def blame(at: tuple[int, int], message: str) -> None:
        problems.append(f"{doc.file}:{at[0]}:{at[1] + 1}: {message}")

    seen: set[tuple[str, str]] = set()
    for node in doc.root.walk():
        for item, at in _expressions(node):
            reads: set[str] = set()
            calls: list[str] = []
            if isinstance(item, (Template, Expr)):
                reads = set(item.names)
            elif item.action is not None:
                calls = [item.action]
            else:
                assert item.statements is not None
                reads = set(item.statements.names)
                calls = list(_called_names(item.statements))
            for name in sorted(reads):
                if name in local or name in _RESERVED_READS or name in BUILTIN_FUNCTIONS or name in _ACTION_FAMILIES or ("read", name) in seen:
                    continue
                seen.add(("read", name))
                if viewmodel is None:
                    blame(at, f"'{name}' is not defined: this view has no ViewModel")
                elif not hasattr(viewmodel, name) or name.startswith("_"):
                    blame(at, f"'{name}' is not defined by {label}")
            for path in calls:
                if path.split(".")[0] in _ACTION_FAMILIES or path.split(".")[0] in local or path in BUILTIN_FUNCTIONS or ("call", path) in seen:
                    continue
                seen.add(("call", path))
                target = viewmodel
                for part in path.split("."):
                    target = getattr(target, part, None) if target is not None and not part.startswith("_") else None
                if viewmodel is None:
                    blame(at, f"'{path}' is not an action: this view has no ViewModel")
                elif not callable(target) or isinstance(target, (Signal, Computed)):
                    blame(at, f"'{path}' is not a method of {label}")
    expects = doc.expects if isinstance(doc.expects, dict) else {}
    for name, type_name in expects.items():
        if viewmodel is None:
            blame(doc.root.at, f"expects '{name}': this view has no ViewModel")
        elif not hasattr(viewmodel, name):
            blame(doc.root.at, f"expects '{name}', which {label} does not define")
        else:
            problem = _check_type(viewmodel, name, str(type_name))
            if problem:
                blame(doc.root.at, f"expects: {problem}")
    return problems
