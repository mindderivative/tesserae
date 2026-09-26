"""MD3's overlays on `tre` 0.3.4's layers (M41): `Dialog`, `Menu` (and a
context menu), `Snackbar`, `Tooltip`, the modal `SideSheet` and the modal
`NavigationDrawer`, since `tre` 0.3.5 removes its `open_*`/`close_*`.

Each is built from its fragment (`tesserae.widgets._composed.Widget`) and
shown with `window.show_layer`: `open()` shows it, `close()` hides it (and
focus goes back to where it was), `on_close(fn)` hears it close. Each
closes itself on the dismissals `tre`'s legacy overlays allowed:

| Overlay | Placement | Outside press | Escape | Modal |
| --- | --- | --- | --- | --- |
| `Menu` | below its anchor (flipped to fit), or at a point | closes | closes | no |
| `Dialog` | centred, over a scrim | -- | closes | yes |
| `SideSheet`, `NavigationDrawer` | at the window's end / start, over a scrim | -- | closes | yes |
| `Snackbar` | 24 px in, 72 px from the bottom | no | no | no |
| `Tooltip` | below its anchor | closes | closes | no |
| `SearchView` | below its search bar | closes | closes | no |

A modal overlay's scrim fills the window (sized when it opens), so an
outside press lands on the scrim. MD3's timing, which `tre` never had: a
snackbar hides itself after 4 s (`duration=None` keeps it), and a tooltip
opens 500 ms after its anchor is hovered, or at once on keyboard focus.
"""

from __future__ import annotations

from typing import Any, Callable, Optional

from tesserae import a11y
from tesserae.theme import Theme
from tesserae.widgets._composed import Widget, fragment

__all__ = ["Dialog", "Menu", "NavigationDrawer", "Overlay", "SearchView", "SideSheet", "Snackbar", "Tooltip"]

#: MD3's scrim: black at 32%, as the fragments' own.
SCRIM = "#00000052"


class _Timer:
    """`fn()` after `ms`: `tre` has no timers, so an animation of a private
    box that's in no tree (animations run there too) stands in for one."""

    def __init__(self, window: Any) -> None:
        self._node = window.create("box", width=0.0, height=0.0)
        self._generation = 0

    def after(self, ms: int, fn: Callable[[], Any]) -> None:
        self.cancel()
        generation = self._generation
        self._node.stop_animation("stroke_width")
        self._node.set(stroke_width=0.0)
        self._node.animate("stroke_width", 1.0, int(ms),
                           on_complete=lambda: fn() if generation == self._generation else None)

    def cancel(self) -> None:
        self._generation += 1
        self._node.stop_animation("stroke_width")


class Overlay:
    """The shared part: a `Widget` shown as a layer. `modal` blocks input
    beneath it and traps focus; `dismissible` closes it on `dismiss`."""

    modal = False
    dismissible = True

    def __init__(self, window: Any, widget: Widget) -> None:
        self.window = window
        self.widget = widget
        self.node = widget.node
        self._open = False
        self._closes: list[Callable[[], Any]] = []
        self._undo = [widget.view._listen(self.node, "dismiss", lambda event: self.close())]

    @property
    def is_open(self) -> bool:
        return self._open

    def on_close(self, fn: Callable[[], Any]) -> Callable[[], None]:
        """Calls `fn()` each time it closes. Returns the function that stops it."""
        self._closes.append(fn)
        return lambda: self._closes.remove(fn) if fn in self._closes else None

    def open(self, anchor: Any = None, placement: str = "below") -> None:
        if self._open:
            return
        self._before_open()
        self.window.show_layer(self.node, anchor=anchor, placement=placement, modal=self.modal,
                               dismissible=self.dismissible)
        self._open = True
        self._after_open()

    def close(self) -> None:
        if not self._open:
            return
        self._before_close()
        self.window.hide_layer(self.node)
        self._open = False
        for fn in list(self._closes):
            fn()

    def set_theme(self, theme: Theme) -> None:
        self.widget.set_theme(theme)

    def _window_size(self) -> tuple[float, float]:
        root = self.window.root
        return root.get("layout_width") or 0.0, root.get("layout_height") or 0.0

    def _before_open(self) -> None:
        """Size or place it for the window as it is now."""

    def _after_open(self) -> None:
        pass

    def _before_close(self) -> None:
        pass


class Dialog(Overlay):
    """MD3's basic dialog (from its fragment): a `surface_container_high`
    panel with 28 px corners, a `headline_small` headline, `body_medium`
    supporting text, and text-button `actions` (`(label, fn)`, right-
    aligned, each closing it after calling `fn`), over a scrim. Modal:
    focus moves into it, and Escape closes it. `role="dialog"`."""

    modal = True

    def __init__(self, window: Any, headline: str, text: str, *, width: float = 312.0, height: float = 200.0,
                 actions: Optional[list[tuple[str, Optional[Callable[[], Any]]]]] = None,
                 theme: Optional[Theme] = None) -> None:
        self.actions = list(actions or [])
        name = "dialog"

        def edit(spec: dict[str, Any]) -> None:
            panel = spec["children"][0]
            if self.actions:
                buttons = [fragment("ButtonText", {"label": label, "width": 72, "height": 40, "corner_radius": 20},
                                    f"{name}.panel.action{i}") for i, (label, _) in enumerate(self.actions)]
                panel["children"].append({"id": f"{name}.panel.actions", "kind": "Container",
                                          "style": {"flex_direction": "horizontal", "justify_content": "flex_end",
                                                    "gap": 8}, "children": buttons})

        widget = Widget(window, "Dialog", {"headline": headline, "text": text, "width": width, "height": height,
                                           "scrim_width": 1, "scrim_height": 1},
                        theme=theme, edit=edit, name=name, attach=False,
                        interactive={f"panel.action{i}": None for i in range(len(self.actions))})
        super().__init__(window, widget)
        panel = widget.part("panel")
        a11y.describe(panel, role="dialog", label=headline)
        for i, (_, fn) in enumerate(self.actions):
            widget.on_click(lambda fn=fn: self._act(fn), part=f"panel.action{i}")

    def _act(self, fn: Optional[Callable[[], Any]]) -> None:
        if fn is not None:
            fn()
        self.close()

    def _before_open(self) -> None:
        width, height = self._window_size()
        self.node.set(width=width, height=height)


class Menu(Overlay):
    """MD3's menu: a `surface_container` panel, 4 px corners, elevation 2,
    8 px top and bottom, of 48 px `label_large` items (`(label, fn)`, or a
    ready `menu_item` widget). Clicking or Enter on an item calls it and
    closes the menu; the up and down arrows move between items; an outside
    press or Escape closes it. `open(anchor)` shows it below `anchor`,
    `open_at(x, y)` at a point, and `attach_context(node)` opens it at the
    pointer on a right-click. `role="menu"`, items `menuitem`."""

    def __init__(self, window: Any, items: list[Any], *, width: float = 200.0,
                 theme: Optional[Theme] = None) -> None:
        if not items:
            raise ValueError("a menu needs at least one item")
        name = "menu"
        labels = [item if isinstance(item, tuple) else None for item in items]
        children = []
        for i, entry in enumerate(labels):
            if entry is not None:
                spec = fragment("MenuItem", {"label": entry[0], "width": width}, f"{name}.item{i}")
                spec["style"].update(height=48, padding={"left": 12, "right": 12, "top": 0, "bottom": 0})
                children.append(spec)
            else:
                children.append({"id": f"{name}.item{i}", "kind": "Container", "style": {"width": width}})
        spec = {"id": name, "kind": "Container",
                "style": {"width": width, "flex_direction": "vertical", "background": "surface_container",
                          "corner_radius": "extra_small", "elevation": "level_2",
                          "padding": {"left": 0, "right": 0, "top": 8, "bottom": 8}},
                "children": children}
        widget = Widget(window, spec=spec, theme=theme, name=name, attach=False,
                        interactive={f"item{i}": "on_surface" for i, e in enumerate(labels) if e is not None})
        super().__init__(window, widget)
        a11y.describe(self.node, role="menu")
        self.items = []
        for i, item in enumerate(items):
            slot = widget.part(f"item{i}")
            listen = widget.view._listen
            if labels[i] is None:  # a ready widget (`menu_item(...)`) or node: it becomes the item
                node = getattr(item, "node", item)
                if node.parent() is not None:
                    node.remove()
                slot.add_child(node)
                slot = node
                fn = getattr(item, "_menu_action", None)
                if hasattr(item, "view"):  # its node already has listeners in its own view's dispatcher
                    listen = item.view._listen
            else:
                fn = labels[i][1]
            self.items.append(slot)
            widget._undo.append(listen(slot, "click", lambda e, fn=fn: self._choose(fn)))
            slot.set(focusable=True, role="menuitem", cursor="pointer")
            widget._undo.append(listen(slot, "key_down", lambda e, i=i: self._key(e, i)))

    def _choose(self, fn: Optional[Callable[[], Any]]) -> None:
        if fn is not None:
            fn()
        self.close()

    def _key(self, event: Any, i: int) -> None:
        step = {"arrow_down": 1, "arrow_up": -1}.get(event.key)
        if step is not None:
            self.items[(i + step) % len(self.items)].focus()

    def _after_open(self) -> None:
        self.items[0].focus()  # MD3: focus moves to the first item

    def open_at(self, x: float, y: float) -> None:
        """Opens it with its top-left corner at the window point `x`, `y`."""
        self.node.set(position="absolute", x=float(x), y=float(y))
        self.open()

    def attach_context(self, node: Any) -> Callable[[], None]:
        """Makes this `node`'s context menu: a right-click opens it at the pointer."""
        return self.widget.view._listen(node, "secondary_click",
                                        lambda e: self.open_at(e.window_x or 0.0, e.window_y or 0.0))


class Snackbar(Overlay):
    """MD3's snackbar (from its fragment): 48 px of `inverse_surface`,
    `body_medium` `inverse_on_surface` text, an optional `action` text
    button (`inverse_primary`, calling `on_action` and closing) and an
    optional close icon button. It opens 24 px in and 72 px up from the
    bottom, isn't modal, ignores outside presses and Escape, and hides
    itself after `duration` ms (4000; `None` keeps it). `role="alert"`,
    announced politely."""

    dismissible = False

    def __init__(self, window: Any, text: str, *, width: float = 344.0, action: Optional[str] = None,
                 on_action: Optional[Callable[[], Any]] = None, closable: bool = False,
                 duration: Optional[int] = 4000, theme: Optional[Theme] = None) -> None:
        self.duration = duration
        name = "snackbar"

        def edit(spec: dict[str, Any]) -> None:
            if action is not None:
                button = fragment("ButtonText", {"label": action, "width": 80, "height": 36, "corner_radius": 18},
                                  f"{name}.action")
                button["children"][0]["style"]["foreground"] = "inverse_primary"
                spec["children"].append(button)
            if closable:
                spec["children"].append({"id": f"{name}.close", "kind": "Rect",
                                         "style": {"width": 40, "height": 40, "corner_radius": 20,
                                                   "background": "transparent", "align_items": "center",
                                                   "justify_content": "center"},
                                         "children": [{"id": f"{name}.close.icon", "kind": "Icon",
                                                       "icon": {"name": "close"},
                                                       "style": {"width": 24, "height": 24,
                                                                 "foreground": "inverse_on_surface"}}]})

        parts = (["action"] if action is not None else []) + (["close"] if closable else [])
        widget = Widget(window, "Snackbar", {"text": text, "width": width}, theme=theme, edit=edit, name=name,
                        attach=False, interactive={p: None for p in parts})
        super().__init__(window, widget)
        a11y.describe(self.node, role="alert", live="polite")
        self._timer = _Timer(window)
        if action is not None:
            widget.on_click(lambda: (on_action() if on_action else None, self.close()), part="action")
        if closable:
            a11y.describe(widget.part("close"), label="Close")
            widget.on_click(self.close, part="close")

    def _before_open(self) -> None:
        _, height = self._window_size()
        self.node.set(position="absolute", x=24.0, y=max(0.0, height - 72.0))

    def _after_open(self) -> None:
        if self.duration is not None:
            self._timer.after(self.duration, self.close)

    def _before_close(self) -> None:
        self._timer.cancel()


class Tooltip(Overlay):
    """MD3's plain tooltip (from its fragment): 24 px of `inverse_surface`
    with `body_small` text, below its anchor. `attach(anchor)` shows it
    500 ms after the anchor is hovered, or at once when it gets keyboard
    focus, and hides it when the pointer or focus leaves; an outside press
    or Escape closes it too. It names the anchor for screen readers
    (`label`), since a tooltip itself isn't reachable."""

    DELAY_MS = 500

    def __init__(self, window: Any, text: str, *, width: Optional[float] = None,
                 theme: Optional[Theme] = None) -> None:
        self.text = text
        widget = Widget(window, "Tooltip", {"text": text, "width": width if width is not None else 1.0},
                        theme=theme, name="tooltip", attach=False)
        super().__init__(window, widget)
        if width is None:  # fit the text: 8 px either side
            widget.node.set(width=widget.part("text").get("width") + 16.0)
        a11y.describe(self.node, hidden=True)
        self._timer = _Timer(window)

    def attach(self, anchor: Any) -> Callable[[], None]:
        """Shows it for `anchor` on hover and keyboard focus. Returns the
        function that detaches it."""
        if not anchor.get("label"):
            a11y.describe(anchor, label=self.text)
        listen = self.widget.view._listen
        undo = [
            listen(anchor, "pointer_enter", lambda e: self._timer.after(self.DELAY_MS, lambda: self.open(anchor))),
            listen(anchor, "pointer_leave", lambda e: self._hide()),
            listen(anchor, "focus", lambda e: self.open(anchor) if e.focus_visible and e.target == anchor else None),
            listen(anchor, "unfocus", lambda e: self._hide()),
            listen(anchor, "pointer_down", lambda e: self._hide()),
        ]
        return lambda: [u() for u in undo]

    def _hide(self) -> None:
        self._timer.cancel()
        self.close()


class _EdgeSheet(Overlay):
    """A modal panel at a window edge over a scrim, sliding in: the side
    sheet (the end edge) and the navigation drawer (the start edge)."""

    modal = True
    SLIDE_MS = "medium4"

    def __init__(self, window: Any, widget: Widget, panel: Any, end: bool) -> None:
        super().__init__(window, widget)
        self.panel = panel
        self.end = end

    def _before_open(self) -> None:
        width, height = self._window_size()
        self.node.set(width=width, height=height)
        self.panel.set(height=height)
        travel = self.panel.get("width") or 0.0
        self.panel.stop_animation("translate_x")
        self.panel.set(translate_x=travel if self.end else -travel)

    def _after_open(self) -> None:
        self.panel.animate("translate_x", 0.0, Theme.duration(self.SLIDE_MS),
                           easing=Theme.easing("emphasized_decelerate"))
        if self.panel.get("focusable"):
            self.panel.focus()


class SideSheet(_EdgeSheet):
    """MD3's modal side sheet (from its fragment): a `surface_container_low`
    panel `width` wide at the window's end, with 16 px corners on its open
    side, over a scrim; it slides in, and Escape closes it. Put its content
    in `.panel`. `role="dialog"`. (A standard side sheet isn't an overlay:
    `tesserae.widgets.side_sheet(modal=False)`.)"""

    def __init__(self, window: Any, *, width: float = 360.0, label: Optional[str] = None,
                 theme: Optional[Theme] = None) -> None:
        widget = Widget(window, "SideSheetModal", {"width": width, "height": 1, "scrim_width": 1, "scrim_height": 1},
                        theme=theme, name="side_sheet", attach=False)
        panel = widget.part("panel")
        super().__init__(window, widget, panel, end=True)
        a11y.describe(panel, role="dialog", **({"label": label} if label else {}))
        panel.set(focusable=True, corner_radius=(16.0, 0.0, 0.0, 16.0))
        widget.after_theme(lambda: panel.set(corner_radius=(16.0, 0.0, 0.0, 16.0)))


class NavigationDrawer(_EdgeSheet):
    """MD3's modal navigation drawer: `tesserae.widgets.navigation_drawer`'s
    drawer, `modal=True`, over a scrim at the window's start; it slides in,
    and Escape closes it. Choosing an item closes it. `.drawer` is the
    drawer widget (`.drawer.selected`, `.drawer.on_change`)."""

    def __init__(self, window: Any, labels: list[str], icons: list[str], *, selected: Optional[int] = None,
                 width: float = 360.0, theme: Optional[Theme] = None) -> None:
        from tesserae.widgets.navigation import navigation_drawer

        scrim = Widget(window, spec={"id": "drawer_scrim", "kind": "Container",
                                     "style": {"width": 1, "height": 1, "background": SCRIM}},
                       theme=theme, name="drawer_scrim", attach=False)
        self.drawer = navigation_drawer(window, labels, icons, selected=selected, modal=True, width=width,
                                        theme=theme)
        self.drawer.node.remove()  # off the window's root, into the scrim
        scrim.node.add_child(self.drawer.node)
        super().__init__(window, scrim, self.drawer.node, end=False)
        a11y.describe(self.drawer.node, label="Navigation")
        self.drawer.on_change(lambda index: self.close())

    def _after_open(self) -> None:
        super()._after_open()
        chosen = self.drawer.selected.get()
        self.drawer.part(f"item{chosen if chosen is not None else 0}").focus()

    def set_theme(self, theme: Theme) -> None:
        super().set_theme(theme)
        self.drawer.set_theme(theme)


class SearchView(Overlay):
    """MD3's docked search view (M42): the results under a search bar, a
    `surface_container_high` panel with 28 px corners and elevation, of
    56 px `body_large` rows (`role="menuitem"`), at most `max_height` tall.

    With a `bar` (`tesserae.widgets.search_bar`), it opens below it when
    the field has focus or is typed in, as long as there are results;
    the down arrow in the field moves into the rows, the arrows move
    between them (up from the first goes back to the field), and a click
    or Enter calls a row's `fn` and closes it. An outside press or Escape
    closes it. `set_results([(text, fn)])` replaces the rows (at most
    `max_results`); `on_query(fn)` hears the bar's typing."""

    ROW = 56.0

    def __init__(self, window: Any, *, bar: Optional[Widget] = None, width: float = 360.0,
                 max_height: float = 336.0, results: Optional[list[tuple[str, Optional[Callable[[], Any]]]]] = None,
                 max_results: int = 8, theme: Optional[Theme] = None) -> None:
        name = "search_view"
        self.bar = bar
        rows = [{"id": f"{name}.row{i}", "kind": "Container",
                 "style": {"width": width, "height": self.ROW, "align_items": "center",
                           "padding": {"left": 16, "right": 16, "top": 0, "bottom": 0}},
                 "children": [{"id": f"{name}.row{i}.label", "kind": "Text",
                               "text": {"content": " ", "typography_role": "body_large"},
                               "style": {"foreground": "on_surface", "width": width - 32, "height": 24}}]}
                for i in range(max_results)]
        spec = {"id": name, "kind": "Container",
                "style": {"width": width, "flex_direction": "vertical", "background": "surface_container_high",
                          "corner_radius": "extra_large", "elevation": "level_3",
                          "padding": {"left": 0, "right": 0, "top": 8, "bottom": 8}},
                "children": rows}
        widget = Widget(window, spec=spec, theme=theme, name=name, attach=False,
                        interactive={f"row{i}": "on_surface" for i in range(max_results)})
        super().__init__(window, widget)
        self.node.set(clip_children=True, max_height=float(max_height))
        a11y.describe(self.node, role="menu", label="Results")
        self.rows = [widget.part(f"row{i}") for i in range(max_results)]
        self._actions: list[Optional[Callable[[], Any]]] = [None] * max_results
        self._count = 0
        for i, row in enumerate(self.rows):
            row.set(focusable=True, role="menuitem", cursor="pointer")
            widget._undo.append(widget.view._listen(row, "click", lambda e, i=i: self._choose(i)))
            widget._undo.append(widget.view._listen(row, "key_down", lambda e, i=i: self._key(e, i)))
            row.remove()
        self.set_results(results or [])
        if bar is not None:
            field = bar.part("field")
            listen = bar.view._listen
            self._undo += [
                listen(field, "focus", lambda e: self._show()),
                listen(field, "change", lambda e: self._show()),
                listen(field, "key_down", self._field_key),
            ]

    # -- for app code ------------------------------------------------------------

    def set_results(self, results: list[tuple[str, Optional[Callable[[], Any]]]]) -> None:
        """Replaces the rows with `results`, `(text, fn)` each."""
        results = list(results)[: len(self.rows)]
        for i, row in enumerate(self.rows):
            if i < len(results):
                text, fn = results[i]
                self.widget.part(f"row{i}.label").set(text=text)
                row.set(label=text)
                self._actions[i] = fn
                if row.parent() is None:
                    self.node.add_child(row)
            elif row.parent() is not None:
                row.remove()
        self._count = len(results)
        if self._count == 0:
            self.close()

    def on_query(self, fn: Callable[[str], Any]) -> Callable[[], None]:
        """Hears the bar's typing (`fn(text)`)."""
        if self.bar is None:
            raise ValueError("a search view hears a query through its bar")
        return self.bar.on_query(fn)

    # -- internals -------------------------------------------------------------------

    def _show(self) -> None:
        if self._count and self.bar is not None:
            self.open(self.bar.node)

    def _choose(self, i: int) -> None:
        fn = self._actions[i]
        self.close()
        if fn is not None:
            fn()

    def _field_key(self, event: Any) -> None:
        if event.key == "arrow_down" and self._count:
            self._show()
            self.rows[0].focus()

    def _key(self, event: Any, i: int) -> None:
        if event.key == "arrow_down":
            self.rows[(i + 1) % self._count].focus()
        elif event.key == "arrow_up":
            if i == 0 and self.bar is not None:
                self.bar.part("field").focus()
            else:
                self.rows[(i - 1) % self._count].focus()
