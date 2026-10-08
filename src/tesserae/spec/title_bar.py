"""`kind: TitleBar` (0.3.0 M3): a window's title bar in a YAML view, for an
app whose window has no OS title bar (`App(borderless=True)`).

    - id: bar
      kind: TitleBar
      title: Notes
      icon: home                      # optional: an icon name
      buttons: [minimize, maximize, close]   # the default; any of them
      children:                       # the app's own content, between the
        - {id: search, kind: TextField, ...}   # title and the buttons

Its height is 40 px unless its `style:` gives another, which every part
follows. It's expanded, before the view is built, into ordinary nodes -- so a
theme, a stylesheet, reconcile and hot reload treat it as they treat any:

- `<id>.inset`: on macOS, room for the traffic lights (`app.titlebar_inset`);
- the bar, `<id>`: a `Container` that's the window's drag region
  (`window_region: drag`) -- a press on it, or on its title or icon,
  moves the window, and a double-click maximizes it;
- `<id>.icon` and `<id>.title`, when given;
- `<id>.content`: the bar's `children`, growing to push the buttons right;
- `<id>.buttons`, holding `<id>.minimize`, `<id>.maximize` and
  `<id>.close` flush together: icon buttons whose handlers are the app's
  window actions (`window.minimize`, `window.toggle_maximized`,
  `window.close`). The maximize button shows the restore glyph while
  `app.maximized` is true, and the buttons hide while the OS's own
  controls show (`app.native_controls`, macOS).

Each part has a class for stylesheets: `title_bar`, `title_bar_icon`,
`title_bar_title`, `title_bar_content`, `title_bar_buttons`,
`title_bar_button`, `title_bar_close` and `title_bar_glyph`. Its look
(`STYLES`) is Material 3 roles on those classes, in the cascade's first
layer, so a theme or stylesheet overrides any of it; it needs a themed
app (`theme_seed`), as the Material fragments do. While the window
isn't the focused one (`app.active`), the title, icon and buttons fade,
and close's hover is red.
"""

from __future__ import annotations

import copy
from typing import Any

__all__ = ["BUTTONS", "STYLES", "SURFACE_BUTTONS", "TitleBarError", "expand_title_bars", "window_parts"]

#: The window buttons a title bar can have, in the order they're laid out.
BUTTONS = ("minimize", "maximize", "close")
#: What a bar in a dialog or a sheet has instead (0.4.4): a button that closes the surface it is in.
SURFACE_BUTTONS = ("dismiss",)
_KEYS = {"id", "kind", "title", "icon", "buttons", "children", "style", "classes", "a11y"}
_ACTIONS = {"minimize": "window.minimize", "maximize": "window.toggle_maximized", "close": "window.close"}
_LABELS = {"minimize": "Minimize", "maximize": "Maximize", "close": "Close"}
#: The bar's height and each button's width: the size desktops use. The
#: height is a default: `style: {height: ...}` on the TitleBar sets it,
#: and every part takes the bar's height.
HEIGHT, BUTTON_WIDTH, GLYPH = 40, 46, 16
#: How far the title, icon and buttons fade while the window isn't the
#: focused one, as desktops dim an inactive title bar.
INACTIVE = 0.6
_DIM = f"{{{{ app.active.get() and 1 or {INACTIVE} }}}}"

#: A title bar's look (0.3.0 M3 Phase 3): Material 3 roles on its parts'
#: classes. It's the cascade's first layer, under every theme, so an
#: app's theme or stylesheet restyles any part, and a theme of the app's
#: own can't leave a part without its colour.
STYLES = {"styles": [
    {"classes": ["title_bar"], "style": {"background": "surface"}},
    {"classes": ["title_bar_title"], "style": {"foreground": "on_surface"}},
    {"classes": ["title_bar_icon"], "style": {"foreground": "on_surface"}},
    {"classes": ["title_bar_glyph"], "style": {"foreground": "on_surface"}},
    # 0.3.0 M4: a borderless window's border (App(window_border=...)).
    {"classes": ["window_border"], "style": {"background": "transparent", "border_color": "outline_variant",
                                             "border_width": 1}},
]}


class TitleBarError(ValueError):
    """A `TitleBar` written wrongly, said on one line naming its id."""


def expand_title_bars(spec: Any) -> Any:
    """`spec` with each `kind: TitleBar` expanded into its nodes (a copy;
    `spec` itself is left as it is). Anything else passes through."""
    if not isinstance(spec, dict):
        return spec
    return _expand(copy.deepcopy(spec))


def _expand(node: dict[str, Any]) -> dict[str, Any]:
    children = node.get("children")
    if isinstance(children, list):
        node["children"] = [_expand(c) if isinstance(c, dict) else c for c in children]
    return _title_bar(node) if node.get("kind") == "TitleBar" else node


def _title_bar(node: dict[str, Any]) -> dict[str, Any]:
    bar_id = node.get("id")
    where = f"widget {bar_id!r}: a TitleBar"
    unknown = set(node) - _KEYS
    if unknown:
        raise TitleBarError(f"{where} takes {', '.join(sorted(_KEYS - {'id', 'kind'}))}; "
                            f"not {', '.join(sorted(unknown))}")
    title, icon = node.get("title"), node.get("icon")
    if title is not None and not isinstance(title, str):
        raise TitleBarError(f"{where}'s title is text, got {title!r}")
    if icon is not None and not isinstance(icon, str):
        raise TitleBarError(f"{where}'s icon is an icon name, got {icon!r}")
    buttons = node.get("buttons", list(BUTTONS))
    surface = isinstance(buttons, list) and any(b in SURFACE_BUTTONS for b in buttons)
    if surface:  # a bar in a dialog or a sheet: no window to move, no window buttons, no OS controls to make room for
        if buttons != list(SURFACE_BUTTONS):
            raise TitleBarError(f"{where}'s `dismiss` button is on its own (a bar is for a window or for a dialog or sheet), "
                                f"got {buttons!r}")
        parts: list[dict[str, Any]] = []
        controls = {"id": f"{bar_id}.buttons", "kind": "Container", "classes": ["title_bar_buttons"],
                    "style": {"height": "100%"}, "children": [_dismiss(bar_id)]}
    else:
        if not isinstance(buttons, list) or any(b not in BUTTONS for b in buttons) or len(set(buttons)) != len(buttons):
            raise TitleBarError(f"{where}'s buttons are some of {', '.join(BUTTONS)}, each once, or just "
                                f"{', '.join(SURFACE_BUTTONS)} in a dialog or a sheet; got {buttons!r}")
        inset, controls = window_parts(bar_id, buttons)
        parts = [inset]
    dim = {} if surface else {"bindings": {"opacity": _DIM}}  # a window's bar fades while the window isn't focused
    if icon is not None:
        parts.append({"id": f"{bar_id}.icon", "kind": "Icon", "icon": {"name": icon}, "classes": ["title_bar_icon"],
                      "style": {"width": 20, "height": 20}, **dim})
    if title is not None:
        parts.append({"id": f"{bar_id}.title", "kind": "Text", "classes": ["title_bar_title"],
                      "text": {"content": title, "typography_role": "title_small"},
                      "style": {}, **dim})
    parts.append({"id": f"{bar_id}.content", "kind": "Container", "classes": ["title_bar_content"],
                  "style": {"flex": "expand_horizontal", "height": "100%", "align_content": "left", "gap": 8},
                  "children": list(node.get("children") or [])})
    if controls is not None:
        parts.append(controls)
    return {
        "id": bar_id, "kind": "Container", "window_region": "none" if surface else "drag",
        "classes": ["title_bar", *(node.get("classes") or [])],
        **({"a11y": node["a11y"]} if "a11y" in node else {}),
        "style": {"height": HEIGHT, "align_content": "left", "gap": 8,
                  "padding": {"left": 12, "right": 0, "top": 0, "bottom": 0}, **(node.get("style") or {})},
        "children": parts,
    }


def _dismiss(bar_id: str) -> dict[str, Any]:
    """The close button of a bar in a dialog or a sheet: it closes the surface (`surface.dismiss`)."""
    button_id = f"{bar_id}.dismiss"
    return {"id": button_id, "kind": "Container", "classes": ["title_bar_button", "title_bar_close"],
            "interaction": {"color": "error"}, "handlers": {"on_click": "surface.dismiss"}, "a11y": {"label": "Close"},
            "style": {"width": BUTTON_WIDTH, "height": "100%", "align_content": "center"},
            "children": [_glyph(button_id, "close")]}


def window_parts(bar_id: str, buttons: Any = BUTTONS) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """A title bar's window parts, for a bar's start and end: `<id>.inset`,
    room for macOS's traffic lights (as wide as `app.titlebar_inset`
    says, 0 elsewhere), and `<id>.buttons`, the window buttons flush
    together (`None` for none), hidden while the OS's own controls show
    and faded while the window isn't focused. A `TitleBar` has them, and
    so does a top app bar on a borderless window.
    Their bindings and handlers reach the app, so the view they're in
    needs a ViewModel on the app's window."""
    inset = {"id": f"{bar_id}.inset", "kind": "Container", "classes": ["title_bar_inset"],
             "style": {"width": 0, "height": "100%"},
             "bindings": {"width": "{{ app.titlebar_inset.get()[1] }}"}}
    if not buttons:
        return inset, None
    return inset, {"id": f"{bar_id}.buttons", "kind": "Container", "classes": ["title_bar_buttons"],
                   "style": {"height": "100%"},
                   "bindings": {"opacity": _DIM, "visible": "{{ not app.native_controls.get() }}"},
                   "children": [_button(bar_id, name) for name in BUTTONS if name in buttons]}


def _glyph(button_id: str, name: str, **extra: Any) -> dict[str, Any]:
    style = extra.pop("style", {})
    return {"id": f"{button_id}.{name}", "kind": "Icon", "icon": {"name": name}, "classes": ["title_bar_glyph"],
            "style": {"width": GLYPH, "height": GLYPH, **style}, **extra}


def _button(bar_id: str, name: str) -> dict[str, Any]:
    button_id = f"{bar_id}.{name}"
    classes = ["title_bar_button", *(["title_bar_close"] if name == "close" else [])]
    if name == "maximize":
        # Two glyphs in one place, a glyph-sized box the button centres at
        # any height: restore shows while the window is maximized.
        at = {"position": "absolute", "x": 0, "y": 0}
        glyphs = [{"id": f"{button_id}.glyphs", "kind": "Container",
                   "style": {"width": GLYPH, "height": GLYPH},
                   "children": [_glyph(button_id, "window_maximize", style=dict(at),
                                       bindings={"opacity": "{{ 1 - (app.maximized.get() and 1 or 0) }}"}),
                                _glyph(button_id, "window_restore", style=dict(at),
                                       bindings={"opacity": "{{ app.maximized.get() and 1 or 0 }}"})]}]
    else:
        glyphs = [_glyph(button_id, "window_minimize" if name == "minimize" else "close")]
    # Close's hover and pressed layers are red, as desktops colour close
    # (`error`: `error_container` is too pale at a state layer's 8%).
    tint = {"interaction": {"color": "error"}} if name == "close" else {}
    return {"id": button_id, "kind": "Container", "classes": classes, **tint,
            "handlers": {"on_click": _ACTIONS[name]}, "a11y": {"label": _LABELS[name]},
            "style": {"width": BUTTON_WIDTH, "height": "100%", "align_content": "center"},
            "children": glyphs}
