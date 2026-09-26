"""Accessibility on `tre` 0.3.4's nodes (M39): what a node tells assistive
technology, checked here so a mistake names the field, and requests
coming back from it (`a11y_action`).

`tre` exposes each node through AccessKit from its accessibility
properties: `role`, `label`, `value`, `value_min`/`value_max`/`value_step`,
`checked`, `selected`, `expanded`, `disabled`, `level`, `live` and
`a11y_hidden`. The requests a screen reader can make of a node arrive as
an `a11y_action` event, one of `ACTIONS`; activating (clicking) isn't
one of them in 0.3.4.

`tre`'s `disabled` is only what's announced: a disabled node still takes
focus and clicks. Tesserae's widgets (M40) make it behave.
"""

from __future__ import annotations

from typing import Any, Callable

__all__ = ["ACTIONS", "LIVE", "ROLES", "check", "describe", "on_action"]

#: The roles `tre` accepts (`none` for a node that's only structure).
ROLES = frozenset({
    "button", "checkbox", "radio", "switch", "slider", "progressbar", "link", "textbox", "tab", "tablist",
    "tabpanel", "menu", "menuitem", "dialog", "alert", "list", "listitem", "tree", "treeitem", "heading",
    "img", "group", "none",
})
#: How a changing node is announced.
LIVE = frozenset({"off", "polite", "assertive"})
#: The requests assistive technology can make of a node.
ACTIONS = frozenset({"increment", "decrement", "expand", "collapse", "scroll_into_view", "set_value"})

_BOOLS = ("checked", "selected", "expanded", "disabled", "hidden")
_NUMBERS = ("value", "value_min", "value_max", "value_step")


def check(fields: dict[str, Any], where: str = "") -> dict[str, Any]:
    """Checks `describe`'s fields and returns them as `tre` properties
    (`hidden` becomes `a11y_hidden`). Raises `ValueError` naming the field."""
    prefix = f"{where}: " if where else ""
    props: dict[str, Any] = {}
    for name, value in fields.items():
        if name == "role":
            if value not in ROLES:
                raise ValueError(f"{prefix}a11y role {value!r} isn't one of {', '.join(sorted(ROLES))}")
        elif name == "label":
            if value is not None and not isinstance(value, str):
                raise ValueError(f"{prefix}a11y label must be a string, got {value!r}")
        elif name == "live":
            if value not in LIVE:
                raise ValueError(f"{prefix}a11y live {value!r} isn't one of {', '.join(sorted(LIVE))}")
        elif name == "level":
            if value is not None and (isinstance(value, bool) or not isinstance(value, int) or value < 1):
                raise ValueError(f"{prefix}a11y level must be a positive whole number, got {value!r}")
        elif name in _BOOLS:
            if not isinstance(value, bool):
                raise ValueError(f"{prefix}a11y {name} must be true or false, got {value!r}")
        elif name in _NUMBERS:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"{prefix}a11y {name} must be a number, got {value!r}")
            value = float(value)
        else:
            known = sorted({"role", "label", "live", "level", *_BOOLS, *_NUMBERS})
            raise ValueError(f"{prefix}unknown a11y field {name!r} (known: {', '.join(known)})")
        props["a11y_hidden" if name == "hidden" else name] = value
    return props


def describe(node: Any, **fields: Any) -> None:
    """Sets what `node` tells assistive technology, for example
    `describe(node, role="switch", label="Wi-Fi", checked=True)`. Every
    field is checked before any is set."""
    node.set(**check(fields))


def on_action(node: Any, handlers: dict[str, Callable[[Any], Any]],
              listen: Callable[[Any, str, Callable[[Any], None]], Callable[[], None]] | None = None,
              ) -> Callable[[], None]:
    """Routes `node`'s `a11y_action` events to `handlers[action]`, each
    given the event (`event.value` carries `set_value`'s value). Returns a
    function that removes the routing. `listen` is a shared-dispatcher
    registrar (a `View`'s `_listen`); without one, the node's own
    `a11y_action` listener is replaced."""
    unknown = set(handlers) - ACTIONS
    if unknown:
        raise ValueError(f"unknown a11y action(s) {sorted(unknown)} (known: {', '.join(sorted(ACTIONS))})")

    def route(event: Any) -> None:
        handler = handlers.get(event.action)
        if handler is not None:
            handler(event)

    if listen is not None:
        return listen(node, "a11y_action", route)
    node.on("a11y_action", route)
    return lambda: node.off("a11y_action")
