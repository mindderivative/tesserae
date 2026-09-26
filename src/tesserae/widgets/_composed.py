"""The composed MD3 widgets of `tesserae.widgets` (M41): each is built
from its fragment in `spec/components/` by Tesserae's compiler, so a
`component: ButtonFilled` in a view and `button(window, ...)` in Python
are one definition.

A factory returns a `Widget`: `.node` (its root, attached to the window's
root), `.part(name)` for a named piece (`"label"`), `on_click(fn)` and
`set_theme(theme)`. The parts a factory makes interactive get MD3's state
layer, ripple and focus ring (M39) in their content's colour.
"""

from __future__ import annotations

from typing import Any, Callable, Optional

import yaml

from tesserae import a11y, tokens
from tesserae.spec.expand import expand_components_to_spec
from tesserae.theme import Theme

__all__ = ["Widget", "fragment"]


def fragment(name: str, params: dict[str, Any], node_id: str) -> dict[str, Any]:
    """The spec `name`'s fragment expands to with `params`, its root `node_id`
    (its parts `node_id.part`): for widgets built from several fragments."""
    return expand_components_to_spec(yaml.safe_dump({"id": node_id, "component": name, "with": params},
                                                    sort_keys=False))


def content_role(spec: dict[str, Any]) -> Optional[str]:
    """The colour role of a node's content (its first Text or Icon child's
    foreground): MD3 colours a part's state layer with it."""
    for child in spec.get("children") or []:
        if child.get("kind") in ("Text", "Icon", "Link"):
            return (child.get("style") or {}).get("foreground")
    return None


class Widget:
    """A composed MD3 widget: its fragment, expanded with `params` (or a
    `spec` a factory built from several), built into `window`.
    `interactive` maps a part (`None` for the root) to the colour role of
    its feedback, `None` meaning its content's colour. `edit(spec)`, when
    given, adjusts the spec before it's built (a factory's extra arguments)."""

    def __init__(self, window: Any, fragment_name: Optional[str] = None, params: Optional[dict[str, Any]] = None, *,
                 spec: Optional[dict[str, Any]] = None, theme: Optional[Theme] = None,
                 label: Optional[str] = None, x: Optional[float] = None, y: Optional[float] = None,
                 interactive: Optional[dict[Optional[str], Optional[str]]] = None,
                 edit: Optional[Callable[[dict[str, Any]], None]] = None, name: str = "widget") -> None:
        from tesserae.view import View

        self.window = window
        self.theme = theme if theme is not None else Theme.resolve()
        self.name = name
        if spec is None:
            spec = fragment(fragment_name, params or {}, name)
        if edit is not None:  # first, so the parts it adds can be interactive
            edit(spec)
        for part, role in (interactive or {}).items():
            node_spec = self._spec_of(spec, part)
            role = role or content_role(node_spec) or "on_surface"
            node_spec["interaction"] = {"color": role}
        self.spec = spec
        self.view = View(spec, window=window, theme_seed=tokens.BASELINE["primary"])
        self.view._use_scheme(self._scheme())
        self.node = self.view.root
        if label is not None:
            a11y.describe(self.node, label=label)
        window.root.add_child(self.node)
        if x is not None or y is not None:
            self.node.set(position="absolute", x=float(x or 0.0), y=float(y or 0.0))
        self._undo: list[Callable[[], None]] = []
        self._restyles: list[Callable[[], Any]] = []

    # -- parts ----------------------------------------------------------------

    def _id(self, part: Optional[str]) -> str:
        return self.name if part is None else f"{self.name}.{part}"

    def _spec_of(self, spec: dict[str, Any], part: Optional[str]) -> dict[str, Any]:
        wanted = self._id(part)
        stack = [spec]
        while stack:
            node = stack.pop()
            if node.get("id") == wanted:
                return node
            stack.extend(node.get("children") or [])
        raise ValueError(f"{self.name} has no part {part!r}")

    def part(self, name: Optional[str] = None) -> Any:
        """The node of the part `name` (the root for `None`)."""
        return self.view.node(self._id(name))

    def interaction(self, part: Optional[str] = None) -> Any:
        """A part's MD3 feedback (`tesserae.interaction.Interaction`), or `None`."""
        return self.view.interaction(self._id(part))

    # -- behaviour -------------------------------------------------------------

    def on_click(self, fn: Callable[[], Any], part: Optional[str] = None, role: str = "button") -> Callable[[], None]:
        """Calls `fn()` when the part (the root by default) is clicked, or
        activated with Enter or Space: it becomes focusable, with `role`,
        and gets MD3's feedback if it hasn't any. Returns the function that
        stops it."""
        self.interactive(part)
        node = self.part(part)
        node.set(focusable=True, role=role, cursor="pointer")
        undo = self.view._listen(node, "click", lambda event: fn())
        self._undo.append(undo)
        return undo

    def interactive(self, part: Optional[str] = None, role: Optional[str] = None) -> None:
        """Gives a part MD3's feedback (in its content's colour, or `role`'s)."""
        node_spec = self._spec_of(self.view.spec, part)
        if node_spec.get("interaction") is None:
            node_spec["interaction"] = {"color": role or content_role(node_spec) or "on_surface"}
            self.view._sync_interactions()

    def color(self, role: str) -> tuple[int, int, int, int]:
        """A colour role of this widget's theme (MD3's baseline without one)."""
        return self._scheme()[role]

    def after_theme(self, fn: Callable[[], Any]) -> None:
        """Calls `fn()` after each re-colouring: a widget whose state
        changes its colours reapplies them there."""
        self._restyles.append(fn)

    def set_theme(self, theme: Theme) -> None:
        """Re-colours the widget for `theme`, at once."""
        self.theme = theme
        self.view._use_scheme(self._scheme())
        for fn in list(self._restyles):
            fn()

    def _scheme(self) -> dict[str, Any]:
        return self.theme.roles if self.theme.roles is not None else tokens.baseline_scheme()

    def destroy(self) -> None:
        for undo in self._undo:
            undo()
        self._undo = []
        self.view._drop_interactions()
        self.view._dispose_controls()
        self.node.destroy()
