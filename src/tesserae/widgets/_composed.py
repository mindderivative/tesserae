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

__all__ = ["Widget"]


class Widget:
    """A composed MD3 widget: its fragment, expanded with `params` and
    built into `window`. `interactive` maps a part (`None` for the root)
    to the colour role of its feedback. `edit(spec)`, when given, adjusts
    the expanded spec before it's built (a factory's extra arguments)."""

    def __init__(self, window: Any, fragment: str, params: dict[str, Any], *, theme: Optional[Theme] = None,
                 label: Optional[str] = None, x: Optional[float] = None, y: Optional[float] = None,
                 interactive: Optional[dict[Optional[str], str]] = None,
                 edit: Optional[Callable[[dict[str, Any]], None]] = None, name: str = "widget") -> None:
        from tesserae.view import View

        self.window = window
        self.theme = theme if theme is not None else Theme.resolve()
        self.name = name
        spec = expand_components_to_spec(yaml.safe_dump({"id": name, "component": fragment, "with": params},
                                                        sort_keys=False))
        for part, role in (interactive or {}).items():
            self._spec_of(spec, part)["interaction"] = {"color": role}
        if edit is not None:
            edit(spec)
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

    def on_click(self, fn: Callable[[], Any], part: Optional[str] = None) -> Callable[[], None]:
        """Calls `fn()` when the part (the root by default) is clicked, or
        activated with Enter or Space: it becomes a focusable button.
        Returns the function that stops it."""
        node = self.part(part)
        node.set(focusable=True, role="button", cursor="pointer")
        undo = self.view._listen(node, "click", lambda event: fn())
        self._undo.append(undo)
        return undo

    def set_theme(self, theme: Theme) -> None:
        """Re-colours the widget for `theme`, at once."""
        self.theme = theme
        self.view._use_scheme(self._scheme())

    def _scheme(self) -> dict[str, Any]:
        return self.theme.roles if self.theme.roles is not None else tokens.baseline_scheme()

    def destroy(self) -> None:
        for undo in self._undo:
            undo()
        self._undo = []
        self.view._drop_interactions()
        self.view._dispose_controls()
        self.node.destroy()
