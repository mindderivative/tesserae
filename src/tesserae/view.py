"""Tesserae's `View` (M37 Phase 4): a view spec built onto `tre` 0.3.4's
building blocks by Tesserae's compiler, kept up to date by Tesserae's
reconciler, with bindings, `handlers:` and `two_way:` wired by Tesserae --
the job `tre`'s `View` does today and 0.3.5 removes.

The surface is the one Tesserae used on `tre`'s `View`: `node(id)`,
`reconcile(spec=...)`, `set_theme(...)`, `set_stylesheet(...)`, and
`_attach(viewmodel)` (called by `ViewModel.__init__`), plus `root` and
`window`.

**Bindings** are evaluated with `tesserae.binding` inside a
`tesserae.reactive` recording frame, so their dependencies are tracked
by Tesserae; a change re-evaluates the expression (re-tracking what it
reads) and sets the property. A value that hasn't changed isn't set
again. On `tre` 0.3.4's building blocks a programmatic `set` fires no
`change` event, so a declared `on_change` runs only for the user's own
edits (`tre` issue #12 doesn't happen here). The eight MD3 control kinds
are Tesserae's controls (M40, `tesserae.controls`): their `checked`/
`selected`/`value`/`hour`/`minute` and `disabled` bindings set the
control's `Signal`s, and `on_change` and `two_way:` hear the control's
`on_change`, which fires for the user's changes only.

**Handlers** are `node.on(...)` listeners: `on_click` → `click`,
`on_hover_enter` → `pointer_enter`, `on_hover_exit` → `pointer_leave`,
`on_change` → `change`, `on_focus_enter` → `focus`, `on_focus_exit` →
`unfocus`. A handler taking one argument gets the event; one taking none
is called without it, as in `tre`. Other names are validated but not
wired, as in `tre`.

**`two_way:`** names one bound property whose user edits write back to
its `Signal`; the binding must be exactly `{{ name.get() }}`.

**Reconciling** matches children by `id`: an unchanged node is kept, a
changed one is patched in place (keeping its identity, focus and
animations), a changed kind is rebuilt, a missing one destroyed. Unlike
`tre`, children also follow the new spec's order. After any update --
reconcile, theme, stylesheet -- bindings and handlers are wired again, so
bound nodes show their live values.
"""

from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any, Callable, Optional

import tre

from tesserae import reactive, tokens
from tesserae.binding import BindingError, Handle, evaluate_value, parse_binding, value_debug
from tesserae.interaction import Interaction
from tesserae.listeners import Listeners
from tesserae.spec.build import (
    Built, _CONTROL_KINDS, build_with, control_shape, focus_ring_color, interaction_tint, natural_size, patch,
    prepare_layers,
)
from tesserae.spec.cascade import resolve_style
from tesserae.spec.cascade import check_stylesheet, check_theme

__all__ = ["Component", "View"]

#: The size of the window a `View` builds itself into when not given one.
DEFAULT_SIZE = (800, 600)

_EVENTS = {
    "on_click": "click", "on_hover_enter": "pointer_enter", "on_hover_exit": "pointer_leave",
    "on_change": "change", "on_focus_enter": "focus", "on_focus_exit": "unfocus",
}
_COLOR_PROPS = {"background": "fill", "foreground": "fill", "border_color": "stroke_color"}
_NUMBER_PROPS = {"width", "height", "padding", "gap", "opacity", "corner_radius", "border_width", "elevation"}


def _props_equal(a: dict[str, Any], b: dict[str, Any]) -> bool:
    """`tre`'s `node_props_equal`, plus the state fields Tesserae builds from."""
    # `handlers` and `a11y` too: they change focus, role and label (M39)
    keys = ("kind", "classes", "style", "text", "image", "icon", "checked", "selected", "value", "hour", "minute",
            "handlers", "a11y")
    return all(a.get(k) == b.get(k) for k in keys)


class View:
    """A built view. `spec` is an expanded view spec (from
    `tesserae.spec.build_view_spec` or `expand_components_to_spec`);
    `frames` maps an Image's id to its decoded `(rgba, width, height)`.
    The theme and stylesheet arguments are `tre`'s `View`'s: the seed and
    dark flag, and the three `*_spec` dicts.

    `window` is the `tre.Window` to build into. Without one, the view
    makes its own and mounts its root there. It doesn't theme that window:
    everything a view builds takes the view's theme (M40)."""

    def __init__(
        self,
        source: Any,
        *,
        window: Any = None,
        frames: Optional[dict[str, tuple[bytes, int, int]]] = None,
        theme_seed: Optional[tuple[int, int, int, int]] = None,
        dark: bool = False,
        default_theme_spec: Optional[dict[str, Any]] = None,
        custom_theme_spec: Optional[dict[str, Any]] = None,
        stylesheet_spec: Optional[dict[str, Any]] = None,
    ) -> None:
        self.path: Optional[Path] = None
        if isinstance(source, (str, Path)):
            from tesserae.spec.load import build_view_spec

            self.path = Path(source)
            spec, file_frames, _ = build_view_spec(self.path)
            frames = {**{node_id: (rgba, w, h) for node_id, rgba, w, h in file_frames}, **(frames or {})}
        else:
            spec = source
        for arg, value, check in (("default_theme_spec", default_theme_spec, check_theme),
                                  ("custom_theme_spec", custom_theme_spec, check_theme),
                                  ("stylesheet_spec", stylesheet_spec, check_stylesheet)):
            try:
                check(value)
            except ValueError as exc:
                raise ValueError(f"{arg}=: {exc}") from None
        self._theme = dict(theme_seed=theme_seed, dark=dark, default_theme_spec=default_theme_spec,
                           custom_theme_spec=custom_theme_spec)
        self._stylesheet_spec = stylesheet_spec
        self._frames = dict(frames or {})
        self._components: list["Component"] = []
        self._scheme = tokens.resolve_scheme(theme_seed, dark, default_theme_spec, custom_theme_spec)
        self._layers = prepare_layers(default_theme_spec, custom_theme_spec, stylesheet_spec)
        self._owns_window = window is None
        if window is None:
            window = tre.Window(width=DEFAULT_SIZE[0], height=DEFAULT_SIZE[1])
            window.root.set(padding_top=0, padding_right=0, padding_bottom=0, padding_left=0, align_items="flex_start")
            # no `Window.set_theme` (removed in tre 0.3.5): since M40 nothing a view builds reads the window's theme
        self.window = window
        self._spec = spec
        self._built = Built(root=None)
        self._events = Listeners()
        try:
            self._built.root = build_with(window, spec, scheme=self._scheme, layers=self._layers,
                                          frames=self._frames, into=self._built, listen=self._events.listen)
        except ValueError as exc:
            if self.path is not None:
                raise ValueError(f"{self.path}: {exc}") from exc
            raise
        if self._owns_window:
            window.root.add_child(self._built.root)
        self._viewmodel: Any = None
        self._wiring: list[Callable[[], None]] = []  # undo steps
        self._interactions: dict[str, Interaction] = {}
        self._sync_interactions()

    # -- lookup ---------------------------------------------------------------

    @property
    def root(self) -> Any:
        """The root node of this view's tree."""
        return self._built.root

    @property
    def spec(self) -> dict[str, Any]:
        return self._spec

    @property
    def theme(self) -> "Theme":
        """This view's resolved theme (`tesserae.Theme`)."""
        from tesserae.theme import Theme

        return Theme.resolve(**self._theme)

    def node(self, widget_id: str) -> Any:
        """The node `widget_id` names (a TextField's `text_input`; a Link's
        box, which holds its text)."""
        try:
            if self._built.specs[widget_id].get("kind") == "Link":
                return self._built.outer[widget_id]
            return self._built.nodes[widget_id]
        except KeyError:
            raise ValueError(f"no widget with id {widget_id!r} in this view") from None

    def control(self, widget_id: str) -> Any:
        """The MD3 control (`tesserae.controls`) behind `widget_id`, one of
        the eight control kinds (M40); its `.node` is `node(widget_id)`."""
        self.node(widget_id)
        try:
            return self._built.controls[widget_id]
        except KeyError:
            raise ValueError(f"widget {widget_id!r} isn't a control kind") from None

    def interaction(self, widget_id: str) -> Optional[Interaction]:
        """The state layer and ripple on `widget_id`'s node (M39), or `None`
        when it has none."""
        self.node(widget_id)
        return self._interactions.get(widget_id)

    def click(self, node: Any) -> None:
        """A synthetic click on `node`, for tests: `window.simulate`."""
        self.window.simulate("click", node=node)

    # -- updates ----------------------------------------------------------------

    def reconcile(self, spec: dict[str, Any], frames: Optional[dict[str, tuple[bytes, int, int]]] = None) -> None:
        """Brings the live tree in line with `spec`, in place."""
        if frames is not None:
            self._frames = dict(frames)
        # All or nothing: build the new spec on the side first, so an error
        # (a bad kind, colour or token) leaves the live tree as it was.
        trial = Built(root=None)
        trial.root = build_with(self.window, spec, scheme=self._scheme, layers=self._layers, frames=self._frames,
                                into=trial, listen=Listeners().listen)
        for control in trial.controls.values():
            control.dispose()
        trial.root.destroy()
        old = self._spec
        if spec.get("id") != old.get("id") or not self._same_shape(old, spec):
            parent = self._built.root.parent()
            self._forget(old)
            self._built.root.destroy()
            self._built.root = build_with(self.window, spec, scheme=self._scheme, layers=self._layers,
                                          frames=self._frames, into=self._built, listen=self._events.listen)
            if parent is not None:
                parent.add_child(self._built.root)
        else:
            self._reconcile_node(old, spec)
        self._spec = spec
        self._sync_interactions()
        self._rewire()

    def set_theme(
        self,
        theme_seed: Optional[tuple[int, int, int, int]] = None,
        dark: bool = False,
        default_theme_spec: Optional[dict[str, Any]] = None,
        custom_theme_spec: Optional[dict[str, Any]] = None,
    ) -> None:
        """Re-themes every node in place. Each call is a complete
        selection, as in `tre`: an omitted argument means its default."""
        scheme = tokens.resolve_scheme(theme_seed, dark, default_theme_spec, custom_theme_spec)
        layers = prepare_layers(default_theme_spec, custom_theme_spec, self._stylesheet_spec)
        self._repatch(scheme, layers)
        self._scheme, self._layers = scheme, layers
        self._theme = dict(theme_seed=theme_seed, dark=dark, default_theme_spec=default_theme_spec,
                           custom_theme_spec=custom_theme_spec)
        self._rewire()
        for component in list(self._components):
            component._host_restyled(self)

    def set_stylesheet(self, stylesheet_spec: Optional[dict[str, Any]] = None) -> None:
        """Replaces the stylesheet and re-styles every node in place;
        `None` clears it. Embedded components follow."""
        layers = prepare_layers(self._theme["default_theme_spec"], self._theme["custom_theme_spec"], stylesheet_spec)
        self._repatch(self._scheme, layers)
        self._layers, self._stylesheet_spec = layers, stylesheet_spec
        self._rewire()
        for component in list(self._components):
            component._host_restyled(self)

    # -- components and windows -----------------------------------------------------

    def instantiate(self, path: Any, into: Any, spec: Optional[dict[str, Any]] = None,
                    frames: Optional[dict[str, tuple[bytes, int, int]]] = None) -> "Component":
        """Builds a component -- a view of its own, with its own ViewModel
        -- under `into`, a node of this view, in this view's window. It gets
        this view's theme and stylesheet, and follows them when they change.
        `spec` is the expanded spec; without it, `path` is read (the same
        call shape as `tre`'s `View.instantiate`)."""
        component = Component(self, spec if spec is not None else path, frames=frames)
        into.add_child(component.root)
        self._components.append(component)
        return component

    def move_to(self, window: Any) -> None:
        """Rebuilds this view in `window`, keeping its spec, theme and
        ViewModel: bindings and handlers are wired again on the new nodes.
        For a view built on its own being shown by an `App`. Nodes looked up
        before the move belong to the old tree."""
        if window is self.window:
            return
        self._unwire()
        self._drop_interactions()
        old_root, old_window = self._built.root, self.window
        self.window = window
        self._dispose_controls()
        self._built = Built(root=None)
        self._events = Listeners()
        self._built.root = build_with(window, self._spec, scheme=self._scheme, layers=self._layers,
                                      frames=self._frames, into=self._built, listen=self._events.listen)
        old_root.destroy()
        self._owns_window = False
        del old_window
        self._sync_interactions()
        if self._viewmodel is not None:
            self._wire(self._spec)

    def _use_scheme(self, scheme: Any) -> None:
        """Re-colours every node from `scheme` (a resolved `Theme`'s roles),
        for a composed widget given a `tesserae.Theme` (M41)."""
        self._repatch(scheme, self._layers)
        self._scheme = scheme

    def _repatch(self, scheme: Any, layers: Any) -> None:
        for node_id, node_spec in self._built.specs.items():
            patch(self.window, node_spec, self._built.outer[node_id], self._built.nodes[node_id],
                  scheme=scheme, layers=layers, frames=self._frames, state=False,
                  control=self._built.controls.get(node_id))
        self._sync_interactions(scheme)

    def _sync_interactions(self, scheme: Any = None) -> None:
        """Gives every node that should have a state layer and ripple one,
        in its current tint, and removes the rest (M39)."""
        scheme = self._scheme if scheme is None else scheme
        wanted: dict[str, Any] = {}
        for node_id, node_spec in self._built.specs.items():
            tint = interaction_tint(node_spec, scheme)
            if tint is not None:
                wanted[node_id] = tint
        for node_id, current in list(self._interactions.items()):
            if node_id not in wanted or current.node is not self._built.outer.get(node_id):
                current.detach()
                del self._interactions[node_id]
        ring = focus_ring_color(scheme)
        for node_id, tint in wanted.items():
            current = self._interactions.get(node_id)
            if current is None:
                self._interactions[node_id] = Interaction(self.window, self._built.outer[node_id], tint,
                                                          self._listen, ring)
                continue
            if (current.tint, current.ring_color) != (tint, ring):
                current.retint(tint, ring)
            current.refresh()

    def _drop_interactions(self) -> None:
        for current in self._interactions.values():
            current.detach()
        self._interactions = {}

    def _reconcile_node(self, old: dict[str, Any], new: dict[str, Any]) -> None:
        node_id = new["id"]
        outer = self._built.outer[node_id]
        if not _props_equal(old, new):
            patch(self.window, new, outer, self._built.nodes[node_id], scheme=self._scheme, layers=self._layers,
                  frames=self._frames, control=self._built.controls.get(node_id))
        self._built.specs[node_id] = new
        old_children = {c["id"]: c for c in old.get("children") or []}
        kept: set[str] = set()
        for index, child in enumerate(new.get("children") or []):
            previous = old_children.get(child["id"])
            if previous is not None and self._same_shape(previous, child):
                kept.add(child["id"])
                self._reconcile_node(previous, child)
                child_node = self._built.outer[child["id"]]
            else:
                if previous is not None:
                    kept.add(child["id"])
                    self._forget(previous)
                    self._built.outer.get(child["id"]) and self._built.outer[child["id"]].destroy()
                child_node = build_with(self.window, child, scheme=self._scheme, layers=self._layers,
                                        frames=self._frames, into=self._built, listen=self._events.listen)
            # a tre Node is a fresh handle on each call, so compare with ==, not `is`
            if child_node.parent() != outer or _child_index(outer, child_node) != index:
                outer.insert_child(index, child_node)
        for child_id, child in old_children.items():
            if child_id not in kept:
                node = self._built.outer.get(child_id)
                self._forget(child)
                if node is not None:
                    node.destroy()

    def _same_shape(self, old: dict[str, Any], new: dict[str, Any]) -> bool:
        """Whether `old`'s node can be patched into `new` rather than
        rebuilt: the same kind, and for a control, the same size."""
        if old.get("kind") != new.get("kind"):
            return False
        if new.get("kind") in _CONTROL_KINDS:
            return control_shape(old, self._layers) == control_shape(new, self._layers)
        return True

    def _dispose_controls(self) -> None:
        for control in self._built.controls.values():
            control.dispose()
        self._built.controls.clear()

    def _forget(self, spec: dict[str, Any]) -> None:
        control = self._built.controls.pop(spec["id"], None)
        if control is not None:
            control.dispose()
        for key in ("nodes", "outer", "specs"):
            getattr(self._built, key).pop(spec["id"], None)
        for child in spec.get("children") or []:
            self._forget(child)

    # -- the ViewModel ----------------------------------------------------------------

    def _attach(self, viewmodel: Any) -> None:
        """Wires every binding, handler and `two_way:` against `viewmodel`.
        Called by `ViewModel.__init__`."""
        self._unwire()
        self._viewmodel = viewmodel
        try:
            self._wire(self._spec)
        except Exception:
            self._unwire()
            raise

    def _rewire(self) -> None:
        if self._viewmodel is not None:
            self._unwire()
            self._wire(self._spec)

    def _unwire(self) -> None:
        steps, self._wiring = self._wiring, []
        for undo in reversed(steps):
            undo()

    def _wire(self, spec: dict[str, Any]) -> None:
        for node_spec in _walk(spec):
            for event, method_name in (node_spec.get("handlers") or {}).items():
                self._wire_handler(node_spec, event, method_name)
            bindings = node_spec.get("bindings") or {}
            for prop, raw in bindings.items():
                self._wire_binding(node_spec, prop, raw)
            two_way = node_spec.get("two_way")
            if two_way is not None:
                self._wire_two_way(node_spec, two_way, bindings.get(two_way))

    def _node_for(self, node_spec: dict[str, Any], prop: str) -> Any:
        node_id = node_spec["id"]
        if node_spec.get("kind") == "Link" and prop in ("width", "height", "padding", "gap", "opacity"):
            return self._built.outer[node_id]
        if node_spec.get("kind") == "TextField" and prop in ("width", "height", "padding", "gap", "background",
                                                              "corner_radius", "border_width", "border_color",
                                                              "opacity", "elevation"):
            return self._built.outer[node_id]
        return self._built.nodes[node_id]

    def _wire_handler(self, node_spec: dict[str, Any], event: str, method_name: str) -> None:
        node_id = node_spec["id"]
        try:
            method = getattr(self._viewmodel, method_name)
        except AttributeError:
            raise ValueError(f'widget "{node_id}": handler "{event}" names "{method_name}", which has no matching '
                             "attribute on the ViewModel") from None
        if not callable(method):
            raise ValueError(f'widget "{node_id}": handler "{event}" names "{method_name}", which is not callable')
        tre_event = _EVENTS.get(event)
        if tre_event is None:
            return  # validated, not wired -- as in tre
        call = _arity_adapter(method)
        # a Link's box takes the events (its text never gets any, M41)
        node = self._built.outer[node_id] if node_spec.get("kind") == "Link" else self._built.nodes[node_id]
        control = self._built.controls.get(node_id)
        if tre_event == "change" and control is not None:
            if hasattr(control, "on_change"):
                self._wiring.append(control.on_change(lambda value: call(None)))
            return
        self._add_listener(node, tre_event, call)

    def _add_listener(self, node: Any, event: str, fn: Callable[[Any], None]) -> None:
        """A ViewModel's listener: removed when the view is unwired."""
        self._wiring.append(self._listen(node, event, fn))

    def _listen(self, node: Any, event: str, fn: Callable[[Any], None]) -> Callable[[], None]:
        """`node.on` keeps one listener per event, so every callback for a
        node and event shares one dispatcher. Returns the undo."""
        return self._events.listen(node, event, fn)

    def _wire_binding(self, node_spec: dict[str, Any], prop: str, raw: str) -> None:
        node_id = node_spec["id"]
        where = f'widget "{node_id}" binding on "{prop}" ({_quoted(raw)})'
        try:
            expr = parse_binding(raw)
        except BindingError as exc:
            raise ValueError(f"{where}: {exc}") from None
        node = self._node_for(node_spec, prop)
        kind = node_spec.get("kind")
        control = self._built.controls.get(node_id)
        style = resolve_style(node_spec, self._layers)
        # a Text/Link without a size is sized to its content, so new text is measured again (M41)
        measured = prop == "text" and kind in ("Text", "Link") and (style.get("width") is None
                                                                    or style.get("height") is None)
        subscribed: list[Any] = []

        def run() -> None:
            for dependency in subscribed:
                dependency._unsubscribe(run)
            reactive._begin_recording()
            try:
                value = evaluate_value(expr, self._viewmodel)
            except BindingError as exc:
                raise ValueError(f"{where}: {exc}") from None
            finally:
                subscribed[:] = reactive._end_recording()
            for dependency in subscribed:
                dependency._subscribe(run)
            if control is not None and prop in _CONTROL_STATE:
                _apply_to_control(control, kind, prop, value)
            else:
                _apply(node, kind, prop, value)
                if measured:
                    _remeasure(self.window, node, style)
                if kind == "Link" and prop == "text":
                    self._built.outer[node_id].set(label=value)  # its name is its text

        run()

        def undo() -> None:
            for dependency in subscribed:
                dependency._unsubscribe(run)
            subscribed.clear()
        self._wiring.append(undo)

    def _wire_two_way(self, node_spec: dict[str, Any], prop: str, raw: Optional[str]) -> None:
        node_id = node_spec["id"]
        rule = (f'widget "{node_id}": two_way binding on "{prop}" ({_quoted(raw or "")}) must be a plain Signal\'s '
                'own .get() call (e.g. "{{ username.get() }}"), not a computed expression -- there\'s no way to '
                "reverse it back into a Signal")
        if raw is None:
            raise ValueError(rule)
        expr = parse_binding(raw)
        if not (expr.kind == "Call" and expr.value == "get" and expr.left.kind == "Ident"):
            raise ValueError(rule)
        name = expr.left.value
        signal = getattr(self._viewmodel, name, None)
        if signal is None:
            raise ValueError(f'widget "{node_id}": two_way binding names "{name}", which has no matching attribute '
                             "on the ViewModel")
        node = self._node_for(node_spec, prop)
        control = self._built.controls.get(node_id)
        if control is not None:
            state = getattr(control, prop, None)
            if not isinstance(state, reactive.Signal) or not hasattr(control, "on_change"):
                raise ValueError(f'widget "{node_id}": a {node_spec.get("kind")} has no user-editable "{prop}" '
                                 "for two_way")
            self._wiring.append(control.on_change(lambda value: signal.set(state.get())))
            return
        self._add_listener(node, "change", lambda event_obj: signal.set(node.get(prop)))


class Component(View):
    """An embedded view with its own ViewModel, built by
    `View.instantiate`/`Component.instantiate` (or `tesserae.instantiate`)
    in its host's window, with its host's theme and stylesheet. It follows
    them when the host is re-themed or re-styled. `remove()` unwires it
    and frees its nodes."""

    def __init__(self, host: View, source: Any, frames: Optional[dict[str, tuple[bytes, int, int]]] = None) -> None:
        self._host = host
        super().__init__(
            source, window=host.window, frames=frames, stylesheet_spec=host._stylesheet_spec, **host._theme,
        )
        self._scheme, self._layers = host._scheme, host._layers

    def _host_restyled(self, host: View) -> None:
        self._theme = dict(host._theme)
        self._stylesheet_spec = host._stylesheet_spec
        self._repatch(host._scheme, host._layers)
        self._scheme, self._layers = host._scheme, host._layers
        self._rewire()
        for component in list(self._components):
            component._host_restyled(self)

    def remove(self) -> None:
        """Unwires this component (its `Signal`s stop reaching it) and frees
        its nodes, and any components inside it."""
        for component in list(self._components):
            component.remove()
        self._unwire()
        self._drop_interactions()
        self._dispose_controls()
        self._viewmodel = None
        if self in self._host._components:
            self._host._components.remove(self)
        self._built.root.destroy()


def _walk(spec: dict[str, Any]):
    yield spec
    for child in spec.get("children") or []:
        yield from _walk(child)


def _child_index(parent: Any, child: Any) -> int:
    for index, node in enumerate(parent.children()):
        if node == child:
            return index
    return -1


def _quoted(raw: str) -> str:
    return '"' + raw.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _arity_adapter(method: Callable[..., Any]) -> Callable[[Any], Any]:
    """Calls `method` with the event if it takes an argument, else
    without -- `tre`'s handler convention."""
    try:
        params = [p for p in inspect.signature(method).parameters.values()
                  if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD, p.VAR_POSITIONAL)]
    except (TypeError, ValueError):
        params = []
    if params:
        return lambda event_obj: method(event_obj)
    return lambda event_obj: method()


def _remeasure(window: Any, node: Any, style: dict[str, Any]) -> None:
    props = {name: node.get(name) for name in ("text", "font_family", "font_size", "font_weight", "line_height")}
    size = natural_size(window, props, style)
    if size:
        node.set(**size)


#: A control's state a binding sets on the control (M40), and the type each takes.
_CONTROL_STATE = {"checked": bool, "selected": bool, "disabled": bool, "value": float, "hour": int, "minute": int}


def _apply_to_control(control: Any, kind: Optional[str], prop: str, value: Any) -> None:
    """Sets a bound value on a control's `Signal`, with `tre`'s type rules
    and messages."""
    expected = _CONTROL_STATE[prop]
    if expected is bool:
        if not isinstance(value, bool):
            raise ValueError(f'widget property "{prop}" expects a boolean binding, got {value_debug(value)}')
    elif isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f'widget property "{prop}" expects a numeric binding, got {value_debug(value)}')
    state = getattr(control, prop, None)
    if not isinstance(state, reactive.Signal):
        raise ValueError(f'a {kind} has no "{prop}" to bind')
    state.set(expected(value))


def _apply(node: Any, kind: Optional[str], prop: str, value: Any) -> None:
    """Sets one bound value, with `tre`'s type rules and messages; an
    unchanged value isn't set again."""
    if prop in ("checked", "selected"):
        if not isinstance(value, bool):
            raise ValueError(f'widget property "{prop}" expects a boolean binding, got {value_debug(value)}')
        if node.get(prop) != value:
            node.set(**{prop: value})
        return
    if prop == "text":
        if not isinstance(value, str) or isinstance(value, Handle):
            raise ValueError(f'widget property "text" expects a string binding, got {value_debug(value)}')
        if node.get("text") != value:
            node.set(text=value)
        return
    if prop in ("width", "height", "padding", "gap"):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f'widget property "{prop}" expects a numeric binding, got {value_debug(value)}')
        props = ({f"padding_{s}": float(value) for s in ("top", "right", "bottom", "left")} if prop == "padding"
                 else {prop: float(value)})
        node.set(**props)
        return
    target = _COLOR_PROPS.get(prop, "shadows" if prop == "elevation" else
                              "stroke_width" if prop == "border_width" else prop)
    if isinstance(value, str) and not isinstance(value, Handle) and prop in _COLOR_PROPS:
        try:
            rgba = tokens.parse_color(value)
        except ValueError as exc:
            raise ValueError(f'binding for property "{prop}" resolved to {exc}') from None
        if node.get(target) != rgba:
            node.set(**{target: rgba})
        return
    if isinstance(value, Handle):
        raw = value.obj
        node.set(**{target: tokens.elevation_shadows(raw) if prop == "elevation" else raw})
        return
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        new = tokens.elevation_shadows(float(value)) if prop == "elevation" else float(value)
        if node.get(target) != new:
            node.set(**{target: new})
        return
    raise ValueError(
        f'binding for property "{prop}" resolved to {value_debug(value)} -- only numeric, boolean (checked), '
        "string (text), and background-color bindings are supported today"
    )
