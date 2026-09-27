"""A declarative app shell (M52): a `*_Shell.yaml` file, loaded with
`app.load_shell(path)`, describes M45's `AppShell` -- the bars, the
navigation, the docked zones, center tabs and the panels in them --
instead of assembling it in Python (M52 Q1):

    top_bar: {title: Tesserae Studio, trailing_icons: [settings]}
    navigation:
      items:
        - {screen: Home, icon: home}
        - {screen: Notes, icon: search}
    status_bar: {text: Ready}
    zones: {left: 220, right: 260, bottom: 160}
    center: true
    panels: {left: [Files, Outline], right: [Properties]}

It's a small schema, not a widget tree: Python builds it through the
existing `AppShell`, `Dock` and `tesserae.widgets`, so the view pipeline
is untouched. Every key is optional. A mistake raises `ShellSpecError`
(a `ValueError`) naming the file and the key.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import yaml

__all__ = ["SHELL_SUFFIX", "ShellSpecError", "build_shell", "load_shell_spec", "parse_shell_spec"]

SHELL_SUFFIX = "_Shell.yaml"
_KEYS = {"top_bar", "navigation", "status_bar", "zones", "center", "panels"}
_EDGES = ("left", "right", "top", "bottom")


class ShellSpecError(ValueError):
    """A `*_Shell.yaml` that doesn't follow the schema."""


def load_shell_spec(path: str | Path) -> dict[str, Any]:
    """Reads and checks a `*_Shell.yaml`, returning its spec with every
    key filled in (`None`, `{}` or `False` for one it leaves out)."""
    path = Path(path)
    if not path.name.endswith(SHELL_SUFFIX):
        raise ShellSpecError(f"{path.name!r} does not follow the required *{SHELL_SUFFIX} naming convention")
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ShellSpecError(f"{path}: {exc}") from None
    return parse_shell_spec(raw, str(path))


def parse_shell_spec(raw: Any, where: str = "shell") -> dict[str, Any]:
    """Checks a shell spec (the parsed YAML); `where` names it in errors."""
    def fail(key: str, problem: str) -> ShellSpecError:
        return ShellSpecError(f"{where}: {key}: {problem}")

    raw = {} if raw is None else raw
    if not isinstance(raw, dict):
        raise ShellSpecError(f"{where}: a shell file is a mapping of {', '.join(sorted(_KEYS))}")
    unknown = sorted(set(raw) - _KEYS)
    if unknown:
        raise fail(unknown[0], f"unknown key (a shell has {', '.join(sorted(_KEYS))})")

    top_bar = _mapping(raw.get("top_bar"), "top_bar", {"title", "leading_icon", "trailing_icons"}, fail)
    if top_bar is not None:
        if not isinstance(top_bar.get("title"), str):
            raise fail("top_bar.title", "a top bar needs a title (text)")
        _optional_text(top_bar, "leading_icon", "top_bar", fail)
        top_bar["trailing_icons"] = _texts(top_bar.get("trailing_icons") or [], "top_bar.trailing_icons", fail)

    navigation = _mapping(raw.get("navigation"), "navigation", {"items", "on_navigate"}, fail)
    if navigation is not None:
        items = navigation.get("items")
        if not isinstance(items, list) or not items:
            raise fail("navigation.items", "a list of {screen, icon}, at least one")
        for i, item in enumerate(items):
            key = f"navigation.items[{i}]"
            item = _mapping(item, key, {"screen", "icon"}, fail)
            if item is None or not isinstance(item.get("screen"), str) or not isinstance(item.get("icon"), str):
                raise fail(key, "needs a screen name and an icon (text)")
        _optional_text(navigation, "on_navigate", "navigation", fail)

    status_bar = _mapping(raw.get("status_bar"), "status_bar", {"text"}, fail)
    if status_bar is not None and not isinstance(status_bar.get("text"), str):
        raise fail("status_bar.text", "a status bar needs its text")

    zones = raw.get("zones") or {}
    if not isinstance(zones, dict):
        raise fail("zones", f"a mapping of side to size, sides from {', '.join(_EDGES)}")
    for side, size in zones.items():
        if side not in _EDGES:
            raise fail(f"zones.{side}", f"not a side (zones are {', '.join(_EDGES)})")
        if isinstance(size, bool) or not isinstance(size, (int, float)) or size <= 0:
            raise fail(f"zones.{side}", f"a size in pixels, more than 0, got {size!r}")

    center = raw.get("center", False)
    if not isinstance(center, bool):
        raise fail("center", f"true or false, got {center!r}")

    panels = raw.get("panels") or {}
    if not isinstance(panels, dict):
        raise fail("panels", "a mapping of side to a list of panel names")
    sides = [*zones, *(["center"] if center else [])]
    seen: set[str] = set()
    for side, names in panels.items():
        if side not in sides:
            raise fail(f"panels.{side}", f"no such zone here (this shell's zones are {', '.join(sides) or 'none'})")
        for name in _texts(names, f"panels.{side}", fail):
            if name in seen:
                raise fail(f"panels.{side}", f"{name!r} is placed twice")
            seen.add(name)

    return {"top_bar": top_bar, "navigation": navigation, "status_bar": status_bar,
            "zones": {side: float(size) for side, size in zones.items()}, "center": center,
            "panels": {side: list(names) for side, names in panels.items()}}


def _mapping(value: Any, key: str, allowed: set[str], fail: Any) -> Optional[dict[str, Any]]:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise fail(key, f"a mapping of {', '.join(sorted(allowed))}")
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise fail(f"{key}.{unknown[0]}", f"unknown key (it has {', '.join(sorted(allowed))})")
    return dict(value)


def _optional_text(mapping: dict[str, Any], field: str, key: str, fail: Any) -> None:
    if mapping.get(field) is not None and not isinstance(mapping[field], str):
        raise fail(f"{key}.{field}", "text")


def _texts(value: Any, key: str, fail: Any) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise fail(key, "a list of names (text)")
    return list(value)


def build_shell(app: Any, spec: dict[str, Any]) -> Any:
    """Builds `spec`'s `AppShell` on `app`'s window: its bars stretch
    across the window, its rail lists the navigation items' screens, and
    it takes the app's theme and follows it (M50)."""
    from tesserae.shell import AppShell
    from tesserae.widgets import navigation_rail, status_bar, top_app_bar

    window = app.window
    width = float(app._width)
    bar = rail = status = None
    if spec["top_bar"] is not None:
        top = spec["top_bar"]
        bar = top_app_bar(window, top["title"], leading_icon=top.get("leading_icon"),
                          trailing_icons=top["trailing_icons"], width=width)
        bar.node.set(width="100%")  # across the window as it resizes
    if spec["navigation"] is not None:
        items = spec["navigation"]["items"]
        rail = navigation_rail(window, [i["screen"] for i in items], [i["icon"] for i in items], selected=0)
    if spec["status_bar"] is not None:
        status = status_bar(window, spec["status_bar"]["text"], width=width)
        status.node.set(width="100%")
    return AppShell(window, top_bar=bar, navigation=rail, status_bar=status, zones=spec["zones"],
                    center=spec["center"])
