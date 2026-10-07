"""`view:` nodes (0.4.4): another `*_View.yaml` shown inside this one.

    - id: left
      view: Left_View.yaml        # or a name found in the project: `view: Left`
      with: {size: 3}             # optional: what the embedded view's ViewModel is given, by keyword
      style: {width: 220}         # where it sits and how big, in its parent

The embedded view is a view of its own (its own ids, its own ViewModel when it has one: `Left_ViewModel.py` beside it or
in the project, and none is fine), built in the host's window with the host's theme, so two views can both have
`id: root`. Before the host is built, each `view:` node is turned into a plain `Container` holding the request in
`embed:`; `tesserae.View` then builds the embedded view into that container (`tesserae.component.embed`).

A `view:` node has an `id` and a `view`, and optionally `with`, `route`, `style`, `classes`, `a11y` and `group`. With a `route:` the
view is a screen of the app (the Window view's routed views): registered under its name and that route, shown in this node when
the route is current, and kept apart, with its state, when it isn't. It has no `kind`,
`component`, `children` or content of its own.
"""

from __future__ import annotations

import copy
from typing import Any

__all__ = ["EmbedError", "embeds_of", "expand_embeds"]

#: What a `view:` node may carry besides `view` itself.
_ALLOWED = frozenset({"id", "view", "with", "route", "style", "classes", "a11y", "group", "window_region"})


class EmbedError(ValueError):
    """A `view:` node written wrongly, said on one line naming its id."""


def expand_embeds(spec: Any) -> Any:
    """`spec` with each `view:` node turned into a `Container` that holds an `embed:` request (a copy; `spec` itself is
    left as it is). Anything else passes through."""
    if not isinstance(spec, dict):
        return spec
    return _expand(copy.deepcopy(spec))


def _expand(node: dict[str, Any]) -> dict[str, Any]:
    children = node.get("children")
    if isinstance(children, list):
        node["children"] = [_expand(c) if isinstance(c, dict) else c for c in children]
    return _placeholder(node) if "view" in node else node


def _placeholder(node: dict[str, Any]) -> dict[str, Any]:
    node_id = node.get("id")
    where = f"widget {node_id!r}: a view:"
    if not isinstance(node_id, str):
        raise EmbedError("a `view:` node needs an `id:`")
    extra = sorted(set(node) - _ALLOWED)
    if extra:
        raise EmbedError(f"{where} node has {', '.join(extra)}, which it can't (it takes {', '.join(sorted(_ALLOWED - {'id'}))})")
    ref = node["view"]
    if not isinstance(ref, str) or not ref.strip():
        raise EmbedError(f"{where} is a view's name or file, got {ref!r}")
    arguments = node.get("with", {})
    if not isinstance(arguments, dict) or not all(isinstance(k, str) for k in arguments):
        raise EmbedError(f"{where} `with:` is a mapping of keyword arguments for the ViewModel, got {arguments!r}")
    out = {k: v for k, v in node.items() if k not in ("view", "with", "route")}
    out["kind"] = "Container"
    out["embed"] = {"view": ref.strip(), "with": dict(arguments)}
    if "route" in node:
        route = node["route"]
        if not isinstance(route, str):
            raise EmbedError(f"{where} `route:` is the route's path, such as `\"\"`, `settings` or `notes/{{id}}`, got {route!r}")
        out["embed"]["route"] = route.strip("/")
    return out


def embeds_of(spec: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """`{node id: {"view": ref, "with": {...}}}` for every `embed:` in an expanded `spec`, in order."""
    found: dict[str, dict[str, Any]] = {}

    def walk(node: dict[str, Any]) -> None:
        if isinstance(node.get("embed"), dict):
            found[node["id"]] = node["embed"]
        for child in node.get("children") or []:
            if isinstance(child, dict):
                walk(child)

    walk(spec)
    return found
