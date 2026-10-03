"""A declarative app shell: a `*_Shell.yaml` file, loaded with
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

Each part can take a `style:` (0.3.3), a node's: `top_bar: {title: Studio,
style: {height: 40}}`, and the same on `navigation` and `status_bar`; at the
top of the file, `style:` is the whole shell's; `content: {style: ...}` is
where the screens show; and a zone is `left: {size: 220, style: {...}}`
(`left: 220` still works). A zone's size is its `size`, not a style's.

It's a small schema, not a widget tree: Python builds it through the
existing `AppShell`, `Dock` and `tesserae.widgets`, so the view pipeline
is untouched. Every key is optional. A mistake raises `ShellSpecError`
(a `ValueError`) naming the file and the key.

A panel is a view named like a screen (M52 Q2): `Files` is the screen
already registered as `Files`, or else `Files_View.yaml` next to the
shell file, with `Files_ViewModel.py`'s `FilesViewModel` if there is one.
It's registered under its name, so it's hot-reloaded as screens are, its
title is its name, and `app.show("Files")` brings its tab forward.

The rail's items name screens: choosing one calls `app.navigate(screen)`,
and `app.show` from anywhere moves the rail's selection to match. With
`on_navigate: method`, choosing one calls that method of the `viewmodel`
given to `load_shell` with the screen's name instead, and it decides.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import yaml

from tesserae.naming import check_naming_convention

__all__ = ["SHELL_SUFFIX", "ShellSpecError", "bind_navigation", "build_shell", "check_references", "load_shell_spec",
           "parse_shell_spec", "place_panels", "reload_shell"]

SHELL_SUFFIX = "_Shell.yaml"
_KEYS = {"top_bar", "navigation", "status_bar", "zones", "center", "panels", "style", "content"}
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

    styles: dict[str, dict[str, Any]] = {}
    frame_style = _style(raw.get("style"), "style", fail)
    if frame_style:
        styles["frame"] = frame_style
    content = _mapping(raw.get("content"), "content", {"style"}, fail)
    if content is not None:
        content_style = _style(content.get("style"), "content.style", fail)
        if content_style:
            styles["content"] = content_style

    top_bar = _mapping(raw.get("top_bar"), "top_bar", {"title", "leading_icon", "trailing_icons", "style"}, fail)
    if top_bar is not None:
        if not isinstance(top_bar.get("title"), str):
            raise fail("top_bar.title", "a top bar needs a title (text)")
        _optional_text(top_bar, "leading_icon", "top_bar", fail)
        top_bar["trailing_icons"] = _texts(top_bar.get("trailing_icons") or [], "top_bar.trailing_icons", fail)
        top_bar["style"] = _style(top_bar.get("style"), "top_bar.style", fail)

    navigation = _mapping(raw.get("navigation"), "navigation", {"items", "on_navigate", "style"}, fail)
    if navigation is not None:
        navigation["style"] = _style(navigation.get("style"), "navigation.style", fail)
        items = navigation.get("items")
        if not isinstance(items, list) or not items:
            raise fail("navigation.items", "a list of {screen, icon}, at least one")
        for i, item in enumerate(items):
            key = f"navigation.items[{i}]"
            item = _mapping(item, key, {"screen", "icon"}, fail)
            if item is None or not isinstance(item.get("screen"), str) or not isinstance(item.get("icon"), str):
                raise fail(key, "needs a screen name and an icon (text)")
        _optional_text(navigation, "on_navigate", "navigation", fail)

    status_bar = _mapping(raw.get("status_bar"), "status_bar", {"text", "style"}, fail)
    if status_bar is not None and not isinstance(status_bar.get("text"), str):
        raise fail("status_bar.text", "a status bar needs its text")
    if status_bar is not None:
        status_bar["style"] = _style(status_bar.get("style"), "status_bar.style", fail)

    zones = raw.get("zones") or {}
    if not isinstance(zones, dict):
        raise fail("zones", f"a mapping of side to size, sides from {', '.join(_EDGES)}")
    sizes: dict[str, Any] = {}
    for side, size in zones.items():
        if side not in _EDGES:
            raise fail(f"zones.{side}", f"not a side (zones are {', '.join(_EDGES)})")
        if isinstance(size, dict):  # `{size: 220, style: {...}}`, for a zone with a style (0.3.3)
            zone = _mapping(size, f"zones.{side}", {"size", "style"}, fail)
            zone_style = _style(zone.get("style"), f"zones.{side}.style", fail)
            if zone_style and {"width", "height"} & set(zone_style):
                raise fail(f"zones.{side}.style", "a zone's size is its `size:`, so its style has no width or height")
            if zone_style:
                styles[side] = zone_style
            size = zone.get("size")
        if isinstance(size, bool) or not isinstance(size, (int, float)) or size <= 0:
            raise fail(f"zones.{side}", f"a size in pixels, more than 0, got {size!r}")
        sizes[side] = size
    zones = sizes

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
            "panels": {side: list(names) for side, names in panels.items()}, "styles": styles}


def _style(value: Any, key: str, fail: Any) -> Optional[dict[str, Any]]:
    """A part's `style:` (0.3.3): a mapping of a node's style fields, or nothing."""
    from tesserae.spec.build import _did_you_mean
    from tesserae.spec.cascade import STYLE_FIELDS

    if value is None:
        return None
    if not isinstance(value, dict):
        raise fail(key, "a mapping of style fields (`height: 40`, `background: surface`, ...)")
    for field in value:
        if field not in STYLE_FIELDS:
            raise fail(f"{key}.{field}", f"unknown style field{_did_you_mean([field], STYLE_FIELDS)}")
        if field == "foreground":
            raise fail(f"{key}.{field}", "a bar or area has no text of its own to colour: use `background`")
    return dict(value)


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
    it takes the app's theme and follows it."""
    from tesserae.shell import AppShell
    window = app.window
    bar = rail = status = None
    if spec["top_bar"] is not None:
        bar = _top_bar(app, spec["top_bar"])
    if spec["navigation"] is not None:
        rail = _rail(app, spec["navigation"], 0)
    if spec["status_bar"] is not None:
        status = _status_bar(app, spec["status_bar"])
    return AppShell(window, top_bar=bar, navigation=rail, status_bar=status, zones=spec["zones"],
                    center=spec["center"], styles=spec["styles"])


def check_references(app: Any, spec: dict[str, Any], path: Path, viewmodel: Any = None) -> None:
    """Checks what the file names outside itself -- each panel's screen or
    view file, and `on_navigate`'s method -- before anything is built, so
    a mistake leaves the app as it was."""
    for side, names in spec["panels"].items():
        for name in names:
            if name not in app._registered and _panel_file(app, name, path, "view") is None:
                raise ShellSpecError(f"{path}: panels.{side}: no screen is registered as {name!r}, "
                                     f"and there's no {name}_View.yaml next to the shell file or in the project")
    navigation = spec["navigation"]
    method = navigation.get("on_navigate") if navigation is not None else None
    if method is not None:
        if viewmodel is None:
            raise ShellSpecError(f"{path}: navigation.on_navigate: names {method!r}, "
                                 "but load_shell was given no viewmodel")
        if not callable(getattr(viewmodel, method, None)):
            raise ShellSpecError(f"{path}: navigation.on_navigate: {type(viewmodel).__name__} "
                                 f"has no method {method!r}")


def place_panels(app: Any, shell: Any, spec: dict[str, Any], path: Path) -> None:
    """Docks each named panel in its zone: the screen registered under
    that name, or else the `<Name>_View.yaml` next to the shell file (with
    its `<Name>_ViewModel.py`, if any), loaded and registered under it."""
    for side, names in spec["panels"].items():
        for name in names:
            registered = app._registered.get(name)
            view = registered.view if registered is not None else _load_panel(app, name, side, path)
            root = view.root
            if shell.dock.side_of(root) is not None:
                if shell.dock.side_of(root) != side:
                    shell.dock.move(root, side)
                continue
            shell.dock.add_panel(side, root, name)  # `dock_panel` takes it from wherever it is


def _panel_file(app: Any, name: str, shell: Path, kind: str) -> Any:
    """A panel's view or viewmodel file: next to the shell file, else in the app's project."""
    suffix = "_View.yaml" if kind == "view" else "_ViewModel.py"
    beside = shell.parent / f"{name}{suffix}"
    if beside.exists():
        return beside
    return app.project.index(kind).get(name)


def _load_panel(app: Any, name: str, side: str, path: Path) -> Any:
    view_file = _panel_file(app, name, path, "view")  # there: `check_references` saw it
    view = app.build_view(view_file)
    viewmodel = None
    vm_file = _panel_file(app, name, path, "viewmodel")
    if vm_file is not None:
        cls = getattr(_import(vm_file), f"{name}ViewModel", None)
        if cls is None:
            raise ShellSpecError(f"{path}: panels.{side}: {vm_file.name} has no class {name}ViewModel")
        check_naming_convention(view_file, cls)
        viewmodel = cls(view)
    app.register(name, view, viewmodel)
    return view


def _import(file: Path) -> Any:
    """`file`'s module, imported once under its own name (the naming check
    finds a class's file through `sys.modules`)."""
    import importlib.util
    import sys

    module = sys.modules.get(file.stem)
    if module is not None and Path(getattr(module, "__file__", "") or "").resolve() == file.resolve():
        return module
    module_spec = importlib.util.spec_from_file_location(file.stem, file)
    module = importlib.util.module_from_spec(module_spec)
    sys.modules[file.stem] = module
    module_spec.loader.exec_module(module)
    return module


def bind_navigation(app: Any, shell: Any, spec: dict[str, Any], path: Path, viewmodel: Any = None) -> None:
    """Choosing a rail item navigates to its screen, a step `back()`
    returns from, or calls the `on_navigate` method of `viewmodel`
    with the screen's name."""
    navigation = spec["navigation"]
    if navigation is None:
        return
    screens = [item["screen"] for item in navigation["items"]]
    method = navigation.get("on_navigate")
    handler = getattr(viewmodel, method) if method is not None else app.navigate  # `check_references` checked it
    shell.navigation.on_change(lambda index: handler(screens[index]))
    app._navigation = (shell.navigation, screens)


def reload_shell(app: Any, shell: Any, old: dict[str, Any], new: dict[str, Any], path: Path,
                 viewmodel: Any = None) -> list[str]:
    """Applies an edited shell file in place and returns what it
    couldn't: the structural changes that need a restart. The bars, the
    rail, the zones and `center` are compared with the live shell; panels
    with the file as it was, so a panel the user dragged stays where it is
    unless the file moved it. A panel the file dropped is undocked, and its
    screen stays registered."""
    needs: list[str] = []
    for key, live in (("top_bar", shell.top_bar), ("navigation", shell.navigation),
                      ("status_bar", shell.status_bar)):
        if (live is None) != (new[key] is None):
            needs.append(f"{key} {'added' if new[key] is not None else 'removed'}")
    added, dropped = sorted(set(new["zones"]) - set(shell._zone_nodes)), sorted(set(shell._zone_nodes) - set(new["zones"]))
    if added or dropped:
        needs.append("zones " + ", ".join([*(f"{s} added" for s in added), *(f"{s} removed" for s in dropped)]))
    if new["center"] != shell.center:
        needs.append(f"center changed to {str(new['center']).lower()}")
    before, after = _placed(old), _placed(new)

    if shell.top_bar is not None and new["top_bar"] is not None and new["top_bar"] != old["top_bar"]:
        top = new["top_bar"]
        bar = _swap(shell.top_bar, lambda: _top_bar(app, top))
        shell.top_bar = bar
    if shell.status_bar is not None and new["status_bar"] is not None and new["status_bar"] != old["status_bar"]:
        if new["status_bar"].get("style") != old["status_bar"].get("style"):
            shell.status_bar = _swap(shell.status_bar, lambda: _status_bar(app, new["status_bar"]))
        else:
            shell.status_bar.part("text").set(text=new["status_bar"]["text"])
    for side, size in new["zones"].items():
        if side in shell._zone_nodes and size != old["zones"].get(side):
            shell.set_size(side, size)
    for part in sorted({*old["styles"], *new["styles"]}):  # the shell's own parts: its frame, content and zones
        if old["styles"].get(part) != new["styles"].get(part) and (part in ("frame", "content") or part in shell._zone_nodes):
            shell.set_style(part, new["styles"].get(part))
    if shell.navigation is not None and new["navigation"] is not None and new["navigation"] != old["navigation"]:
        screens = [item["screen"] for item in new["navigation"]["items"]]
        selected = screens.index(app.current) if app.current in screens else 0
        shell.navigation = _swap(shell.navigation, lambda: _rail(app, new["navigation"], selected))
        bind_navigation(app, shell, new, path, viewmodel)
    sides = {*shell._zone_nodes, *(["center"] if shell.center else [])}
    moved_or_new = {name: side for name, side in after.items() if before.get(name) != side and side in sides}
    grouped: dict[str, list[str]] = {}
    for name, side in moved_or_new.items():
        grouped.setdefault(side, []).append(name)
    place_panels(app, shell, {"panels": grouped}, path)
    for name in sorted(set(before) - set(after)):  # undocked (M53); the screen stays registered
        registered = app._registered.get(name)
        if registered is not None and shell.dock.side_of(registered.view.root) is not None:
            shell.dock.remove_panel(registered.view.root)
    return needs


def _placed(spec: dict[str, Any]) -> dict[str, str]:
    return {name: side for side, names in spec["panels"].items() for name in names}


def _top_bar(app: Any, top: dict[str, Any]) -> Any:
    from tesserae.widgets import top_app_bar

    style = top.get("style")
    bar = top_app_bar(app.window, top["title"], leading_icon=top.get("leading_icon"),
                      trailing_icons=top["trailing_icons"], width=float(app._width), style=style)
    if "width" not in (style or {}):
        bar.node.set(width="100%")  # across the window as it resizes
    return bar


def _status_bar(app: Any, status: dict[str, Any]) -> Any:
    from tesserae.widgets import status_bar

    style = status.get("style")
    bar = status_bar(app.window, status["text"], width=float(app._width), style=style)
    if "width" not in (style or {}):
        bar.node.set(width="100%")
    return bar


def _rail(app: Any, navigation: dict[str, Any], selected: int) -> Any:
    from tesserae.widgets import navigation_rail

    items = navigation["items"]
    return navigation_rail(app.window, [i["screen"] for i in items], [i["icon"] for i in items], selected=selected,
                           style=navigation.get("style"))


def _swap(old: Any, make: Any) -> Any:
    """A new widget where `old`'s node is, and `old` destroyed."""
    parent = old.node.parent()
    index = parent.children().index(old.node)
    new = make()
    parent.insert_child(index, new.node)
    old.destroy()
    return new
