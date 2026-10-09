"""`kind: Window`: the root of a `*_View.yaml` that is a whole OS window.

    id: root
    kind: Window
    title: Tasks                 # the window's title
    borderless: true             # no OS title bar or borders: the title bar below is the window's
    fullscreen: false            # also maximized, transparent, blur_behind, click_through: the OS window's options, when given
    min_width: 480
    min_height: 320
    style: {width: 900, height: 600, background: surface}   # the window's size, and its background
    title_bar: {title: Tasks, icon: home, buttons: [minimize, maximize, close]}
    children:                    # the window's content, under the title bar
      - id: ...

A Window has no parent: it is the root of its view, there is one per app, and it can't be embedded (`view:`) or nested in
another. Before the view is built, it is turned into a vertical `Container` that fills the window, holding the `TitleBar`
(when it has a `title_bar:`) and a `<id>.content` container with its `children`; the keys the app needs, to set the OS window,
stay on the root as `window:`. `style:`'s `width` and `height` are the window's size (when numbers), its `background` is the
window's, and the rest of `style:` lays out the content. `tesserae.App` reads `window:` when the view is loaded.
"""

from __future__ import annotations

import copy
from typing import Any

__all__ = ["WindowError", "expand_windows", "window_of"]

_KEYS = frozenset({"id", "kind", "title", "borderless", "min_width", "min_height", "title_bar", "style", "classes", "a11y",
                   "children", "remember", *("fullscreen", "maximized", "transparent", "blur_behind", "click_through")})
#: The yes/no options of the OS window: shown by the app when the view is loaded, only when the view gives them.
_FLAGS = ("fullscreen", "maximized", "transparent", "blur_behind", "click_through")
#: What a Window's `title_bar:` takes (a `TitleBar`'s keys, without its `kind` and `id`).
_BAR_KEYS = frozenset({"id", "title", "icon", "buttons", "children", "style", "classes", "a11y"})


class WindowError(ValueError):
    """A `Window` written wrongly, said on one line naming its id."""


def expand_windows(spec: Any) -> Any:
    """`spec` with its root `kind: Window` turned into the container and title bar it stands for (a copy; `spec` itself is
    left as it is). A `Window` anywhere but the root is an error."""
    if not isinstance(spec, dict):
        return spec
    spec = copy.deepcopy(spec)
    for child in spec.get("children") or []:
        _no_window(child, spec.get("id"))
    return _window(spec) if spec.get("kind") == "Window" else spec


def _no_window(node: Any, parent_id: Any) -> None:
    if not isinstance(node, dict):
        return
    if node.get("kind") == "Window":
        raise WindowError(f"widget {node.get('id')!r}: a Window is the root of its view (there is one window), "
                          f"it can't be inside {parent_id!r}")
    for child in node.get("children") or []:
        _no_window(child, node.get("id"))


def window_of(spec: Any) -> dict[str, Any] | None:
    """The `window:` a root `Window` left on `spec` (title, borderless, min sizes, size), or `None`."""
    return spec.get("window") if isinstance(spec, dict) and isinstance(spec.get("window"), dict) else None


def _number(where: str, name: str, value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise WindowError(f"{where} {name} is a number of pixels, 0 or more, got {value!r}")
    return float(value)


def _window(node: dict[str, Any]) -> dict[str, Any]:
    node_id = node.get("id")
    where = f"widget {node_id!r}: the Window's"
    if not isinstance(node_id, str):
        raise WindowError("a `Window` needs an `id:`")
    unknown = sorted(set(node) - _KEYS)
    if unknown:
        raise WindowError(f"widget {node_id!r}: a Window takes {', '.join(sorted(_KEYS - {'id', 'kind'}))}; not {', '.join(unknown)}")
    title = node.get("title")
    if title is not None and not isinstance(title, str):
        raise WindowError(f"{where} title is text, got {title!r}")
    borderless = node.get("borderless", False)
    if not isinstance(borderless, bool):
        raise WindowError(f"{where} borderless is true or false, got {borderless!r}")
    options: dict[str, Any] = {"title": title, "borderless": borderless}
    remember = node.get("remember")
    if remember is not None:
        if not isinstance(remember, (bool, str)) or remember == "":
            raise WindowError(f"{where} remember is true, or a name to keep the state under, got {remember!r}")
        if remember is not False:
            options["remember"] = remember
    for name in _FLAGS:
        if name in node:
            if not isinstance(node[name], bool):
                raise WindowError(f"{where} {name} is true or false, got {node[name]!r}")
            options[name] = node[name]
    for name in ("min_width", "min_height"):
        if name in node:
            options[name] = _number(where, name, node[name])
    style = node.get("style") or {}
    if not isinstance(style, dict):
        raise WindowError(f"{where} style is a mapping of style fields, got {style!r}")
    style = dict(style)
    width, height = style.pop("width", None), style.pop("height", None)
    if isinstance(width, (int, float)) and isinstance(height, (int, float)) and not isinstance(width, bool):
        options["size"] = (float(width), float(height))
    elif width is not None or height is not None:
        raise WindowError(f"{where} size is a width and a height in pixels, got width {width!r}, height {height!r}")
    background = style.pop("background", "surface")

    children: list[dict[str, Any]] = []
    bar = node.get("title_bar")
    if bar is not None and bar is not False:
        bar = {} if bar is True else bar
        if not isinstance(bar, dict) or set(bar) - _BAR_KEYS:
            raise WindowError(f"{where} title_bar takes {', '.join(sorted(_BAR_KEYS - {'id'}))}, got {bar!r}")
        bar = dict(bar)
        bar.setdefault("id", f"{node_id}.title_bar")
        if title is not None:
            bar.setdefault("title", title)
        if not borderless:  # the OS draws the window's own buttons: a bar in a bordered window is a plain header
            bar.setdefault("buttons", [])
        children.append({"kind": "TitleBar", **bar})
    content_style = {"flex": "fill", **style}
    children.append({"id": f"{node_id}.content", "kind": "Container", "classes": ["window_content"], "style": content_style,
                     "children": list(node.get("children") or [])})
    out: dict[str, Any] = {
        "id": node_id, "kind": "Container", "classes": ["window", *(node.get("classes") or [])],
        "window": options,
        "style": {"width": "100%", "height": "100%", "flex_direction": "vertical", "background": background},
        "children": children,
    }
    if "a11y" in node:
        out["a11y"] = node["a11y"]
    return out
