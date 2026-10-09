"""Accessibility on `tre` 0.3.4's nodes: what a node tells assistive
technology, checked here so a mistake names the field, and requests
coming back from it (`a11y_action`).

`tre` exposes each node through AccessKit from its accessibility
properties: `role`, `label`, `value`, `value_min`/`value_max`/`value_step`,
`checked`, `selected`, `expanded`, `disabled`, `level`, `live` and
`a11y_hidden`. The requests a screen reader can make of a node arrive as
an `a11y_action` event, one of `ACTIONS`; activating (clicking) isn't
one of them in 0.3.4.

`tre`'s `disabled` is only what's announced: a disabled node still takes
focus and clicks. Tesserae's widgets make it behave.

`bind` keeps a node's `label`, `hidden`, `level`, `checked`, `selected`, `expanded` or `value` (with `value_min`, `value_max`, `value_step`) following a
`Signal`, a `Computed` or a function, as a YAML `a11y:` binding does.
"""

from __future__ import annotations

from typing import Any, Callable

__all__ = ["ACTIONS", "BINDABLE", "CURRENT", "EXTRAS", "LIVE", "RELATIONS", "ROLES", "apply_extras", "bind", "check", "describe", "on_action"]

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

#: The states tre 0.5.4 has no property for yet (requested: mindderivative/tre#160). The language and Tesserae's widgets set them; they reach the
#: engine when it takes them, and until then each is dropped, said once by name.
EXTRAS = ("pressed", "invalid", "description", "current", "value_now", "value_text", "busy")
#: `describedby` and `controls` name other nodes of the view (by their `name:`), or a list of them; the view resolves them to nodes.
RELATIONS = ("describedby", "controls")
CURRENT = frozenset({"page", "step", "location", "date", "time"})
_BOOLS = ("checked", "selected", "expanded", "disabled", "hidden", "invalid", "busy")
_NUMBERS = ("value", "value_min", "value_max", "value_step")
#: The states and numbers tre holds as "not set" (`None`) until a node says: `expanded` is absent on a node that cannot expand, and
#: `checked: null` is a box that is neither on nor off to a screen reader. `hidden` and `disabled` are always one or the other.
_OPTIONAL = frozenset({"checked", "selected", "expanded", "value", "value_min", "value_max", "value_step", "invalid", "busy", "pressed",
                       "description", "current", "value_now", "value_text"})
_NUMBERS_EXTRA = ("value_now",)


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
        elif name in _OPTIONAL and value is None:
            pass
        elif name == "pressed":
            if value not in (True, False, "mixed") or (isinstance(value, int) and not isinstance(value, bool)):
                raise ValueError(f"{prefix}a11y pressed must be true, false or mixed, got {value!r}")
        elif name in ("description", "value_text"):
            if not isinstance(value, str):
                raise ValueError(f"{prefix}a11y {name} must be a string, got {value!r}")
        elif name == "current":
            if value is not True and value is not False and value not in CURRENT:
                raise ValueError(f"{prefix}a11y current must be true, false or one of {', '.join(sorted(CURRENT))}, got {value!r}")
        elif name in RELATIONS:
            names = [value] if isinstance(value, str) else value
            if not isinstance(names, list) or not names or not all(isinstance(n, str) and n for n in names):
                raise ValueError(f"{prefix}a11y {name} is the name of a node, or a list of names, got {value!r}")
        elif name in _BOOLS:
            if not isinstance(value, bool):
                raise ValueError(f"{prefix}a11y {name} must be true or false, got {value!r}")
        elif name in _NUMBERS or name in _NUMBERS_EXTRA:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"{prefix}a11y {name} must be a number, got {value!r}")
            value = float(value)
        else:
            known = sorted({"role", "label", "live", "level", *_BOOLS, *_NUMBERS, *EXTRAS, *RELATIONS})
            raise ValueError(f"{prefix}unknown a11y field {name!r} (known: {', '.join(known)})")
        props["a11y_hidden" if name == "hidden" else name] = value
    return props


_WARNED: set[str] = set()


def apply_extras(node: Any, props: dict[str, Any]) -> None:
    """Sets the accessibility states tre may not have yet (`EXTRAS`, and relations resolved to nodes) one at a time, so a property tre does not
    know costs only that property: it is skipped, with one warning naming it."""
    for name, value in props.items():
        try:
            node.set(**{name: value})
        except ValueError as exc:
            if "unknown node property" not in str(exc) and "unknown property" not in str(exc):
                raise
            if name not in _WARNED:
                _WARNED.add(name)
                from loguru import logger

                logger.warning("a11y {}: this tre has no such property, so it is not sent to the screen reader", name)


def describe(node: Any, **fields: Any) -> None:
    """Sets what `node` tells assistive technology, for example
    `describe(node, role="switch", label="Wi-Fi", checked=True)`. Every
    field is checked before any is set. States tre does not have yet
    (`EXTRAS`) are applied as far as it takes them."""
    if any(name in RELATIONS for name in fields):
        raise ValueError("a11y.describe: describedby and controls name nodes of a view; write them in the view's `a11y:`")
    props = check(fields)
    extras = {k: props.pop(k) for k in list(props) if k in EXTRAS or k in RELATIONS}
    node.set(**props)
    apply_extras(node, extras)


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


#: The fields `bind` can keep up to date (M47 Q2): values that change as
#: the app runs. `role` and `live` say what a node is and how it's
#: announced, so they're set once, with `describe`.
BINDABLE = ("label", "hidden", "level", "checked", "selected", "expanded", "value", "value_min", "value_max", "value_step", *EXTRAS)


def bind(node: Any, **fields: Any) -> Callable[[], None]:
    """Keeps `node`'s `label`, `hidden` or `level` up to date: each
    is a `Signal` or `Computed` (anything with `.get()`), a function of no
    arguments, or a plain value, and it's set now and again whenever what
    it read changes, checked as `describe` checks it (a wrong value raises,
    naming the field). `node` is a node, or a widget or control (its
    `.node`). Returns the function that stops it.

        stop = a11y.bind(button.node, label=Computed(lambda: f"{count.get()} unread"))
    """
    from tesserae.reactive import Effect

    unknown = sorted(set(fields) - set(BINDABLE))
    if unknown:
        raise ValueError(f"a11y.bind: {unknown[0]!r} can't be bound -- only {', '.join(BINDABLE)} "
                         f"(set role and live with describe)")
    target = node if hasattr(node, "set") else node.node
    effects = []

    def follow(name: str, source: Any) -> None:
        read = source.get if hasattr(source, "get") else source if callable(source) else (lambda: source)

        def apply() -> None:
            props = check({name: read()}, "a11y.bind")
            if name in EXTRAS:
                apply_extras(target, props)
            elif any(target.get(k) != v for k, v in props.items()):
                target.set(**props)
        effects.append(Effect(apply))

    try:
        for name, source in fields.items():
            follow(name, source)
    except Exception:
        for effect in effects:
            effect.dispose()
        raise

    def stop() -> None:
        for effect in effects:
            effect.dispose()
        effects.clear()
    return stop
