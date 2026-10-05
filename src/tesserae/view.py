"""Tesserae's `View`: a view spec built onto `tre` 0.3.4's
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
are Tesserae's controls: their `checked`/
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

from tesserae import a11y, reactive, tokens
from tesserae.binding import BindingError, Handle, evaluate_value, parse_binding, value_debug
from tesserae.follow import app_of
from tesserae.interaction import Interaction
from tesserae.listeners import Listeners, handled
from tesserae.scrolling import Scroller
from tesserae.spec.images import check_frame
from tesserae.spec.title_bar import expand_title_bars
from tesserae.spec.build import (
    A11Y_BINDABLE, Built, _CONTROL_KINDS, _WIDGET_KINDS, a11y_bindings, build_with, connect_edges, control_shape,
    focus_ring_color,
    interaction_tint, layout_of, natural_size, patch, prepare_layers, resting_focus,
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
#: The app's window actions a handler can name without a ViewModel method
#: (0.3.0 M3): `on_click: window.close`, for a title bar's buttons.
WINDOW_ACTIONS = ("minimize", "maximize", "restore", "toggle_maximized", "close")
#: How far a disabled node fades (M70): MD3's disabled content opacity.
DISABLED_OPACITY = 0.38
_NUMBER_PROPS = {"width", "height", "padding", "gap", "opacity", "corner_radius", "border_width", "elevation"}


def _props_equal(a: dict[str, Any], b: dict[str, Any]) -> bool:
    """`tre`'s `node_props_equal`, plus the state fields Tesserae builds from."""
    # `handlers` and `a11y` too: they change focus, role and label (M39)
    keys = ("kind", "classes", "style", "text", "image", "icon", "svg", "checked", "selected", "value", "hour", "minute",
            "handlers", "a11y", "component_of", "min", "max", "step", "label", "x", "y",  # M57, M58, M60
            "disabled",  # M70: a control's is its own
            "window_region")  # 0.3.0 M3
    return all(a.get(k) == b.get(k) for k in keys)


class View:
    """A built view. `spec` is an expanded view spec (from
    `tesserae.spec.build_view_spec` or `expand_components_to_spec`);
    `frames` maps an Image's id to its decoded `(rgba, width, height)`.
    The theme and stylesheet arguments are `tre`'s `View`'s: the seed and
    dark flag, and the three `*_spec` dicts.

    `window` is the `tre.Window` to build into. Without one, the view
    makes its own and mounts its root there. It doesn't theme that window:
    everything a view builds takes the view's theme. Built on an
    `App`'s window with no theme argument at all, it takes the app's theme
    and follows it; any theme argument pins it."""

    def __init__(
        self,
        source: Any,
        *,
        window: Any = None,
        frames: Optional[dict[str, tuple[bytes, int, int]]] = None,
        theme_seed: Optional[tuple[int, int, int, int]] = None,
        dark: Optional[bool] = None,
        default_theme_spec: Optional[dict[str, Any]] = None,
        custom_theme_spec: Optional[dict[str, Any]] = None,
        stylesheet_spec: Optional[dict[str, Any]] = None,
        project: Any = None,
    ) -> None:
        self.path: Optional[Path] = None
        app = None
        if window is not None and all(arg is None for arg in (theme_seed, dark, default_theme_spec, custom_theme_spec)):
            app = app_of(window)  # no theme given: the app's, followed (M50)
            if app is not None:
                given = app._view_theme()
                theme_seed, dark = given.get("theme_seed"), given["dark"]
                default_theme_spec, custom_theme_spec = given.get("default_theme_spec"), given.get("custom_theme_spec")
        dark = bool(dark)
        if isinstance(source, (str, Path)):
            from tesserae.spec.load import build_view_spec

            self.path = Path(source)
            if project is None and window is not None and (found := app_of(window)) is not None:
                project = found.project  # the app's files, found by name
            spec, file_frames, _ = build_view_spec(self.path, project=project)
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
        spec = expand_title_bars(spec)  # 0.3.0 M3: `kind: TitleBar` into its nodes
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
        self._scrollers: dict[str, Scroller] = {}  # each ScrollView's write-back (M71; `tre` scrolls, M73)
        #: M70: the nodes shown disabled now, by their `disabled:` key or binding.
        self._disabled_on: set[str] = set()
        self._sync_interactions()
        if app is not None:
            app._followers[self] = None

    def _follow_theme(self, theme: Any, view_theme: dict[str, Any]) -> None:
        """Following its app: re-themed with the app's arguments."""
        self.set_theme(**view_theme)

    def _follow_alive(self) -> bool:
        try:
            self.root.get("visible")
        except ValueError:
            return False
        return True

    # -- lookup ---------------------------------------------------------------

    @property
    def root(self) -> Any:
        """The root node of this view's tree."""
        return self._built.root

    @property
    def spec(self) -> dict[str, Any]:
        """The expanded spec the view was built from: every `component:` and `include:` resolved."""
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
        the eight control kinds; its `.node` is `node(widget_id)`."""
        self.node(widget_id)
        try:
            return self._built.controls[widget_id]
        except KeyError:
            raise ValueError(f"widget {widget_id!r} isn't a control kind") from None

    def interaction(self, widget_id: str) -> Optional[Interaction]:
        """The state layer and ripple on `widget_id`'s node, or `None`
        when it has none."""
        self.node(widget_id)
        return self._interactions.get(widget_id)

    def click(self, node: Any) -> None:
        """A synthetic click on `node`, for tests: `window.simulate`."""
        self.window.simulate("click", node=node)

    # -- updates ----------------------------------------------------------------

    def reconcile(self, spec: dict[str, Any], frames: Optional[dict[str, tuple[bytes, int, int]]] = None) -> None:
        """Brings the live tree in line with `spec`, in place."""
        spec = expand_title_bars(spec)  # 0.3.0 M3, as in `__init__`
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
            # where it was, so a rebuilt component stays in place among its siblings (M51)
            index = parent.children().index(self._built.root) if parent is not None else None
            self._forget(old)
            self._built.root.destroy()
            self._built.root = build_with(self.window, spec, scheme=self._scheme, layers=self._layers,
                                          frames=self._frames, into=self._built, listen=self._events.listen)
            if parent is not None:
                parent.insert_child(index, self._built.root)
        else:
            self._reconcile_node(old, spec)
        self._spec = spec
        self._sync_interactions()
        self._rewire()
        self._prune_components()

    def _prune_components(self) -> None:
        """Forgets the components whose nodes a reload destroyed (their
        `into` node, say): unwired, so their bindings stop."""
        for component in list(self._components):
            if not component._follow_alive():
                component._forget_dead()
                self._components.remove(component)
            else:
                component._prune_components()

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
        if spec is not None and path:
            component.path = Path(path)  # the file it came from, for hot reload (M51)
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
        for a composed widget given a `tesserae.Theme`."""
        self._repatch(scheme, self._layers)
        self._scheme = scheme

    def _repatch(self, scheme: Any, layers: Any) -> None:
        for node_id, node_spec in self._built.specs.items():
            self._built.layout_keys[node_id] = patch(
                self.window, node_spec, self._built.outer[node_id], self._built.nodes[node_id],
                scheme=scheme, layers=layers, frames=self._frames, state=False,
                control=self._built.controls.get(node_id), before=self._built.layout_keys.get(node_id, frozenset()),
                parent=self._parent_layout(node_id, layers))
        self._sync_interactions(scheme)

    def _parent_layout(self, node_id: str, layers: Any) -> tuple[str, str]:
        """The `(flex_direction, display)` of a node's parent: what the node's own `flex` and `align_self` mean."""
        parent = self._built.specs.get(self._built.parent_ids.get(node_id) or "")
        return layout_of(parent, layers) if parent is not None else ("horizontal", "flex")

    def _sync_interactions(self, scheme: Any = None) -> None:
        """Gives every node that should have a state layer and ripple one,
        in its current tint, and removes the rest."""
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
        self._sync_scrolls()
        self._sync_disabled()

    def _sync_disabled(self) -> None:
        """Shows every node disabled that its `disabled:` key says is,
        and enabled again those that no longer are -- after each build and
        patch, which would otherwise make them focusable and opaque again.
        A `disabled` binding is applied again right after, as every binding
        is. A control keeps its own `disabled`."""
        for node_id, spec in self._built.specs.items():
            if node_id in self._built.controls:
                continue
            off = bool(spec.get("disabled") or False)
            if off or node_id in self._disabled_on:
                self._show_disabled(node_id, off)

    def _show_disabled(self, node_id: str, off: bool) -> None:
        spec = self._built.specs[node_id]
        outer = self._built.outer[node_id]
        target = self._built.nodes[node_id] if spec.get("kind") == "TextField" else outer
        target.set(disabled=off, focusable=False if off else resting_focus(spec))
        opacity = float(resolve_style(spec, self._layers).get("opacity", 1.0))
        outer.set(opacity=opacity * DISABLED_OPACITY if off else opacity)
        interaction = self._interactions.get(node_id)
        if interaction is not None:
            interaction.enabled = not off
        if off:
            self._disabled_on.add(node_id)
        else:
            self._disabled_on.discard(node_id)

    def _sync_scrolls(self) -> None:
        """Gives every ScrollView its `Scroller`, and stops those whose
        node is gone or was rebuilt."""
        for node_id, current in list(self._scrollers.items()):
            spec = self._built.specs.get(node_id) or {}
            if spec.get("kind") != "ScrollView" or current.node != self._built.outer.get(node_id):
                current.detach()
                del self._scrollers[node_id]
        for node_id, spec in self._built.specs.items():
            if spec.get("kind") == "ScrollView" and node_id not in self._scrollers:
                self._scrollers[node_id] = Scroller(self._built.outer[node_id], self._listen)

    def _drop_interactions(self) -> None:
        for current in self._interactions.values():
            current.detach()
        self._interactions = {}
        for scroller in self._scrollers.values():
            scroller.detach()
        self._scrollers = {}

    def _reconcile_node(self, old: dict[str, Any], new: dict[str, Any]) -> None:
        node_id = new["id"]
        outer = self._built.outer[node_id]
        if not _props_equal(old, new):
            self._built.layout_keys[node_id] = patch(
                self.window, new, outer, self._built.nodes[node_id], scheme=self._scheme, layers=self._layers,
                frames=self._frames, control=self._built.controls.get(node_id),
                before=self._built.layout_keys.get(node_id, frozenset()), parent=self._parent_layout(node_id, self._layers))
        self._built.specs[node_id] = new
        if new.get("kind") == "NodeGraph":
            self._reconcile_graph(old, new)
            return
        if new.get("kind") in ("GraphNode", "ScrollView"):
            outer = self._built.nodes[node_id]  # its children live in its body, or its content box (M71)
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
                                        frames=self._frames, into=self._built, listen=self._events.listen,
                                        parent=node_id)
            # a tre Node is a fresh handle on each call, so compare with ==, not `is`
            if child_node.parent() != outer or _child_index(outer, child_node) != index:
                outer.insert_child(index, child_node)
        for child_id, child in old_children.items():
            if child_id not in kept:
                node = self._built.outer.get(child_id)
                self._forget(child)
                if node is not None:
                    node.destroy()

    def _reconcile_graph(self, old: dict[str, Any], new: dict[str, Any]) -> None:
        """A NodeGraph's GraphNodes, matched by id: a kept one is
        patched in place (so a place the user dragged it to stays, unless
        the file moves it), a new one is built into the graph, a gone one
        is removed; then the edges are drawn again."""
        graph = self._built.controls[new["id"]]
        old_children = {c["id"]: c for c in old.get("children") or []}
        kept: set[str] = set()
        for child in new.get("children") or []:
            previous = old_children.get(child["id"])
            if previous is not None and self._same_shape(previous, child):
                kept.add(child["id"])
                self._reconcile_node(previous, child)
                continue
            if previous is not None:
                kept.add(child["id"])
                self._forget_graph_node(graph, previous)
            if child.get("kind") != "GraphNode":
                raise ValueError(f'widget "{new["id"]}": a NodeGraph\'s children are GraphNodes, '
                                 f"got {child.get('kind')!r} ({child.get('id')!r})")
            build_with(self.window, child, scheme=self._scheme, layers=self._layers, frames=self._frames,
                       into=self._built, listen=self._events.listen, graph=graph)
        for child_id, child in old_children.items():
            if child_id not in kept:
                self._forget_graph_node(graph, child)
        connect_edges(graph, new, self._built)

    def _forget_graph_node(self, graph: Any, spec: dict[str, Any]) -> None:
        widget = self._built.controls.get(spec["id"])
        self._forget(spec)
        if widget is not None:
            if widget in graph.graph_nodes:
                graph.graph_nodes.remove(widget)
            widget.node.destroy()

    def _same_shape(self, old: dict[str, Any], new: dict[str, Any]) -> bool:
        """Whether `old`'s node can be patched into `new` rather than
        rebuilt: the same kind, and for a control or a graph's widget, the
        same size."""
        if old.get("kind") != new.get("kind"):
            return False
        if new.get("kind") in _CONTROL_KINDS or new.get("kind") in _WIDGET_KINDS:
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
            for field_name, raw in a11y_bindings(node_spec).items():
                self._wire_a11y(node_spec, field_name, raw)
            two_way = node_spec.get("two_way")
            if two_way is not None:
                self._wire_two_way(node_spec, two_way, bindings.get(two_way))

    def _node_for(self, node_spec: dict[str, Any], prop: str) -> Any:
        node_id = node_spec["id"]
        if node_spec.get("kind") == "ScrollView":  # its content box takes how its children lay out (M71)
            return self._built.nodes[node_id] if prop in ("padding", "gap") else self._built.outer[node_id]
        if node_spec.get("kind") == "Link" and prop in ("width", "height", "padding", "gap", "opacity"):
            return self._built.outer[node_id]
        if node_spec.get("kind") == "TextField" and prop in ("width", "height", "padding", "gap", "background",
                                                              "corner_radius", "border_width", "border_color",
                                                              "opacity", "elevation"):
            return self._built.outer[node_id]
        return self._built.nodes[node_id]

    def _wire_handler(self, node_spec: dict[str, Any], event: str, method_name: str) -> None:
        node_id = node_spec["id"]
        if method_name.startswith("window."):
            method = self._window_action(node_id, event, method_name)
        else:
            try:
                method = getattr(self._viewmodel, method_name)
            except AttributeError:
                raise ValueError(f'widget "{node_id}": handler "{event}" names "{method_name}", which has no '
                                 "matching attribute on the ViewModel") from None
        if not callable(method):
            raise ValueError(f'widget "{node_id}": handler "{event}" names "{method_name}", which is not callable')
        tre_event = _EVENTS.get(event)
        if tre_event is None:
            return  # validated, not wired -- as in tre
        adapted = _arity_adapter(method)

        def call(event_obj: Any) -> Any:
            if node_id not in self._disabled_on:  # a disabled node's handlers don't run (M70)
                return adapted(event_obj)
            return None

        # a Link's box takes the events (its text never gets any, M41)
        node = self._built.outer[node_id] if node_spec.get("kind") == "Link" else self._built.nodes[node_id]
        control = self._built.controls.get(node_id)
        if tre_event == "change" and control is not None:
            if hasattr(control, "on_change"):
                self._wiring.append(control.on_change(lambda value: call(None)))
            return
        if tre_event == "click":  # the innermost clickable takes the click (tre bubbles it, M49)
            self._add_listener(node, tre_event, handled(call))
            return
        self._add_listener(node, tre_event, call)

    def _window_action(self, node_id: str, event: str, name: str) -> Callable[[], None]:
        """`window.<action>`: the app's window action (0.3.0 M3), checked
        now and looked up when it runs."""
        action = name[len("window."):]
        where = f'widget "{node_id}": handler "{event}" names "{name}"'
        if action not in WINDOW_ACTIONS:
            raise ValueError(f"{where}, which isn't a window action "
                             f"({', '.join('window.' + a for a in WINDOW_ACTIONS)})")
        if app_of(self.window) is None:
            raise ValueError(f"{where}, but this view isn't on an App's window, which the action needs")

        def run() -> None:
            app = app_of(self.window)
            if app is not None:
                getattr(app, action)()
        return run

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
            elif prop == "disabled":  # any other node's (M70): the View holds it
                if not isinstance(value, bool):
                    raise ValueError(f'widget property "disabled" expects a boolean binding, got {value_debug(value)}')
                self._show_disabled(node_id, value)
            elif prop == "frame":  # M59: a video's frames, from the ViewModel
                if kind != "Image":
                    raise ValueError(f"{where}: only an Image takes a frame")
                frame = value.obj if isinstance(value, Handle) else value
                if frame is not None:
                    try:
                        self._show_frame(node_id, node, frame)
                    except (TypeError, ValueError) as exc:
                        raise ValueError(f"{where}: a frame is (rgba bytes, width, height): {exc}") from None
            else:
                _apply(node, kind, prop, value)
                if measured:
                    _remeasure(self.window, node, style, kind)
                if kind == "Link" and prop == "text" and "label" not in (node_spec.get("a11y") or {}):
                    self._built.outer[node_id].set(label=value)  # its name is its text, unless `a11y:` names it

        run()

        def undo() -> None:
            for dependency in subscribed:
                dependency._unsubscribe(run)
            subscribed.clear()
        self._wiring.append(undo)

    def _show_frame(self, node_id: str, node: Any, frame: Any) -> None:
        """Shows `frame`, `(rgba, width, height)`, on an Image node, and
        keeps it as the node's frame so a re-theme or reconcile shows the
        latest (M59; the `video` widget uses it too)."""
        rgba, width, height = frame
        data, width, height = check_frame(rgba, width, height)
        node.set(rgba=data, pixel_width=width, pixel_height=height)
        self._frames[node_id] = (data, width, height)

    def _wire_a11y(self, node_spec: dict[str, Any], field_name: str, raw: str) -> None:
        """A bound `a11y:` field: `label`, `hidden` or `level`, set on
        the node that carries the widget's accessibility (a Link's box, a
        TextField's input, a control's target) and kept up to date."""
        node_id = node_spec["id"]
        where = f'widget "{node_id}" a11y binding on "{field_name}" ({_quoted(raw)})'
        try:
            expr = parse_binding(raw)
        except BindingError as exc:
            raise ValueError(f"{where}: {exc}") from None
        node = self._built.outer[node_id] if node_spec.get("kind") == "Link" else self._built.nodes[node_id]
        prop = A11Y_BINDABLE[field_name]
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
            value = _a11y_value(field_name, value, where)
            if node.get(prop) != value:
                node.set(**{prop: value})

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
        if node_spec.get("kind") == "ScrollView":  # its Scroller follows `tre`'s `scroll` event (M71, M73)
            if prop != "scroll_offset":
                raise ValueError(f'widget "{node_id}": a ScrollView\'s only user-editable property is "scroll_offset"')
            self._wiring.append(self._scrollers[node_id].on_scroll(signal.set))
            return
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

    def _forget_dead(self) -> None:
        """Unwires a component whose nodes are already gone, and the
        components inside it; its `Signal`s stop reaching it. (`tre`'s
        `off` on a destroyed node is harmless, so unwiring is safe.)"""
        for component in list(self._components):
            component._forget_dead()
        self._components = []
        self._unwire()
        self._viewmodel = None

    def remove(self) -> None:
        """Unwires this component (its `Signal`s stop reaching it) and frees
        its nodes, and any components inside it. A component a host's
        reload already destroyed is simply forgotten."""
        if not self._follow_alive():
            self._forget_dead()
            if self in self._host._components:
                self._host._components.remove(self)
            return
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


def _a11y_value(field_name: str, value: Any, where: str) -> Any:
    """A bound `a11y:` value, checked by `tesserae.a11y`'s rules: a label is
    a string (or `None`, no label), `hidden` true or false, `level` a
    positive whole number (or `None`)."""
    if isinstance(value, Handle):
        if value.obj is not None:  # the evaluator hands `None` back as a handle: it clears the field
            raise ValueError(f"{where}: a11y {field_name} can't be {value_debug(value)}")
        value = None
    try:
        return a11y.check({field_name: value})[A11Y_BINDABLE[field_name]]
    except ValueError as exc:
        raise ValueError(f"{where}: {exc}") from None


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


def _remeasure(window: Any, node: Any, style: dict[str, Any], kind: str) -> None:
    props = {name: node.get(name) for name in ("text", "font_family", "font_size", "font_weight", "line_height")}
    size = natural_size(window, props, style)
    if size and "width" in size and kind == "Text" and node.get("width") == "100%":
        size["min_width"] = size.pop("width")  # a centred or right aligned Text fills its parent: this is its least
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
    fit = getattr(control, "_fit", None) if prop == "value" else None  # a SpinBox keeps to its bounds (M58)
    state.set(fit(expected(value)) if fit is not None else expected(value))


def _apply(node: Any, kind: Optional[str], prop: str, value: Any) -> None:
    """Sets one bound value, with `tre`'s type rules and messages; an
    unchanged value isn't set again."""
    if prop in ("checked", "selected", "visible"):  # visible: out of layout and hit-testing (0.3.0 M3)
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
