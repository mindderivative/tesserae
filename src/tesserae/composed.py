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

from pathlib import Path
from typing import Any, Callable, Optional

from tesserae.follow import app_of
from tesserae.listeners import handled
from tesserae.reactive import Effect, untrack
from tesserae.spec.compose import Instance
from tesserae.spec.images import extract_images
from tesserae.spec.lower import lower
from tesserae.spec.nodes import ViewDoc
from tesserae.view import _EVENTS, SURFACE_ACTIONS, WINDOW_ACTIONS, View
from tesserae.viewmodel import Bindings, ViewHandle, open_view

__all__ = ["ComposedView", "builtin_actions", "open_composed"]


def builtin_actions(view_ref: Callable[[], Any]) -> Callable[[str], Optional[Callable[..., Any]]]:
    """The actions a handler may call without a ViewModel: `window.<action>`, `navigate.<screen>`, `navigate_to(screen)` and
    `surface.dismiss`. `view_ref()` is the `ComposedView` they act for (it does not exist yet when composing starts)."""

    def resolve(path: str) -> Optional[Callable[..., Any]]:
        view = view_ref()
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

    return resolve


class ComposedView(View):
    """A `View` built and kept up to date from a `ViewHandle`. See the module docstring."""

    def __init__(self, handle: ViewHandle, *, base_dir: Optional[Path] = None, window: Any = None, **kwargs: Any) -> None:
        self.handle = handle
        self._base_dir = Path(base_dir) if base_dir is not None else Path.cwd()
        self._handler_undos: list[Callable[[], None]] = []
        self._state_undos: list[Callable[[], None]] = []
        self._observed: set[int] = set()
        self._synced = False
        self._effect: Optional[Effect] = None
        spec, frames = self._lowered()
        super().__init__(spec, window=window, frames=frames, **kwargs)
        handle.window = self.window  # the ViewModel finds its app through the view's window
        handle.view = self
        self._effect = Effect(self._sync)
        self._synced = True

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
        untrack(self._wire_states)
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
            for event in inst.handlers:
                tre_event = _EVENTS.get(event)
                if tre_event is None:
                    continue  # `on_key` is checked when the file loads and drawn when the renderer has it

                def call(event_obj: Any, inst: Instance = inst, event: str = event) -> Any:
                    if inst.id not in self._disabled_on:  # a disabled node's handlers do not run
                        inst.fire(event, event_obj)

                if tre_event == "change" and control is not None and hasattr(control, "on_change"):
                    self._handler_undos.append(control.on_change(lambda value, call=call: call(None)))
                elif tre_event == "click":
                    self._handler_undos.append(self._listen(node, tre_event, handled(call)))
                else:
                    self._handler_undos.append(self._listen(node, tre_event, call))
            for prop, (name, scope) in inst.models.items():
                state = getattr(control, prop, None) if control is not None else None
                if state is not None and hasattr(control, "on_change"):
                    self._handler_undos.append(control.on_change(
                        lambda value, scope=scope, name=name, state=state: scope.assign(name, state.get())))
                else:
                    self._handler_undos.append(self._listen(
                        node, "change", lambda ev, scope=scope, name=name, node=node, prop=prop: scope.assign(name, node.get(prop))))

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
                                       ("focus", "focused", lambda e: bool(getattr(e, "focus_visible", False))), ("unfocus", "focused", False)):
                if name in signals:
                    self._state_undos.append(self._listen(node, event, setter(name, value)))

    def close(self) -> None:
        """Stops following the composition and releases it."""
        if self._effect is not None:
            self._effect.dispose()
        for undo in (*self._handler_undos, *self._state_undos):
            undo()
        self._handler_undos, self._state_undos = [], []
        self.handle.close()


def open_composed(doc: ViewDoc, bindings: Bindings, views: Any = None, *, base_dir: Optional[Path] = None, window: Any = None,
                  rules: Any = (), **kwargs: Any) -> ComposedView:
    """Opens `doc` against the ViewModel that serves its name and builds it: `kwargs` are `View`'s (theme seed, dark, ...)."""
    holder: list[ComposedView] = []
    handle = open_view(doc, bindings, views, actions=builtin_actions(lambda: holder[0] if holder else None), rules=rules)
    view = ComposedView(handle, base_dir=base_dir, window=window, **kwargs)
    holder.append(view)
    return view
