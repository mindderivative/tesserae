#!/usr/bin/env python3
"""Writes the component pages and the stylesheet pages.

- `docs/components/<slug>.md`: one page for each MD3 component, from `tools/component_docs.yaml` (the MD3 text, the usage examples) and from the
  code itself: each shipped view (`src/tesserae/views/<Name>_View.yaml`: its parameters, slots and parts) and each built-in widget it names
  (`tesserae.spec.widgets`: its properties).
- `docs/stylesheets/<slug>/<view>.md`: one page for each shipped stylesheet (`<Name>_Stylesheet.yaml`): the file, how rules reach the view, and what
  each part's rules do.
- the two overview pages, and the `nav:` entries for both, between markers in `mkdocs.yml`.

Nothing here is written by hand except `tools/component_docs.yaml`. Every shipped view must be listed under exactly one component and every
built-in widget under one or in `NOT_COMPONENTS`, so a new one cannot go undocumented.

    python tools/generate_component_docs.py          # write them
    python tools/generate_component_docs.py --check  # exit 1 if they are out of date
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
DATA = ROOT / "tools" / "component_docs.yaml"
VIEWS = ROOT / "src" / "tesserae" / "views"
DOCS = ROOT / "docs"
MKDOCS = ROOT / "mkdocs.yml"
NAV_MARKS = ("# >>> components (written by tools/generate_component_docs.py)", "# <<< components")

#: Built-in widgets that are building blocks, not components: they are in the view language guide and the YAML reference.
NOT_COMPONENTS = frozenset({"Container", "Rect", "Icon", "Canvas", "ScrollView", "VirtualList", "Overlay", "Slot"})
#: A value longer than this is cut in a table (the whole stylesheet is on the page).
CUT = 110


def _kebab(name: str) -> str:
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "-", name).lower()


def _style_field_help() -> dict[str, str]:
    """What each style field does, from the schema generator's own descriptions."""
    spec = importlib.util.spec_from_file_location("generate_yaml_schema", ROOT / "tools" / "generate_yaml_schema.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    style = module._definitions(fragment=False)["style"]["properties"]
    return {name: " ".join(prop.get("description", "").split()).removesuffix(f" ({prop['x-group']}.)") if "x-group" in prop
            else " ".join(prop.get("description", "").split()) for name, prop in style.items()}


# -- reading the code ----------------------------------------------------------------------------

class View:
    """A shipped view: its header comment, parameters, slots and parts, and its stylesheet's rules."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.path = VIEWS / f"{name}_View.yaml"
        self.text = self.path.read_text(encoding="utf-8")
        self.data = yaml.safe_load(self.text)
        self.summary = _header(self.text)
        self.params: dict[str, Any] = self.data.get("params") or {}
        self.sheet_path = VIEWS / f"{name}_Stylesheet.yaml"
        self.sheet_text = self.sheet_path.read_text(encoding="utf-8") if self.sheet_path.exists() else None
        self.rules: list[dict[str, Any]] = (yaml.safe_load(self.sheet_text) or {}).get("styles", []) if self.sheet_text else []
        self.sheet_summary = _header(self.sheet_text) if self.sheet_text else ""
        self.slots: list[str] = []
        self.parts: list[tuple[str, str]] = []
        self._walk(self.data, root=True)

    def _walk(self, node: Any, root: bool = False) -> None:
        if isinstance(node, dict):
            if "widget" in node:
                if node["widget"] == "Slot":
                    self.slots.append(str(node.get("name", "default")))
                elif isinstance(node.get("name"), str) and not root:
                    self.parts.append((node["name"], str(node["widget"])))
            for value in node.values():
                self._walk(value)
        elif isinstance(node, list):
            for item in node:
                self._walk(item)


def _header(text: str) -> str:
    """The comment at the top of a file, as one paragraph."""
    lines = []
    for line in text.splitlines():
        if not line.startswith("#"):
            break
        lines.append(line.lstrip("#").strip())
    return " ".join(part for part in lines if part)


def _cell(value: Any) -> str:
    """A value in a table cell: code, cut if it is long, with `|` kept from ending the cell."""
    if value is None or value == "":
        return ""
    text = value if isinstance(value, str) else yaml.safe_dump(value, default_flow_style=True, width=10_000).strip().removesuffix("...").strip()
    if len(text) > CUT:
        text = text[:CUT - 1] + "…"
    return "`" + text.replace("|", "\\|").replace("`", "'") + "`"


def _doc(text: Any) -> str:
    return " ".join(str(text or "").split()).replace("|", "\\|")


def _type(spec: Any) -> str:
    kind = spec.get("type", "any") if isinstance(spec, dict) else str(spec)
    choices = spec.get("choices") if isinstance(spec, dict) else None
    out = " or ".join(f"`{c}`" for c in choices) if choices else f"`{kind}`"
    low, high = (spec.get("min"), spec.get("max")) if isinstance(spec, dict) else (None, None)
    if low is not None and high is not None:
        out += f", {low:g} to {high:g}"
    elif low is not None:
        out += f", {low:g} or more"
    elif high is not None:
        out += f", {high:g} or less"
    return out


def _widget(name: str) -> Any:
    from tesserae.spec.widgets import lookup

    decl = lookup(name)
    if decl is None:
        raise SystemExit(f"tools/component_docs.yaml names the widget {name!r}, which is not registered")
    return decl


def _registered_widgets() -> set[str]:
    from tesserae.spec.widgets import names

    return set(names())


# -- the pages -------------------------------------------------------------------------------------

def _fence(code: str, lang: str) -> list[str]:
    return [f"```{lang}", code.rstrip("\n"), "```", ""]


def _view_section(view: View, entry: dict[str, Any]) -> list[str]:
    out = [f"### `{view.name}`", "", view.summary or "A view Tesserae ships.", ""]
    if view.params:
        out += ["| Parameter | Type | Default | Meaning |", "| --- | --- | --- | --- |"]
        for name, spec in view.params.items():
            spec = spec if isinstance(spec, dict) else {"type": spec}
            default = "required" if spec.get("required") else _cell(spec.get("default"))
            model = " Two-way: give it a bare reference and the view writes it back." if spec.get("model") else ""
            out.append(f"| `{name}` | {_type(spec)} | {default} | {_doc(spec.get('doc'))}{model} |")
        out.append("")
    else:
        out += ["It takes no parameters.", ""]
    if view.slots:
        out += ["Children go in " + (", ".join(f"the `{s}` slot" if s != "default" else "the default slot" for s in view.slots)) + ".", ""]
    if view.parts:
        out += ["Its parts, by name (a stylesheet rule's `part:` or `name:` addresses one): " + ", ".join(f"`{n}` ({w})" for n, w in view.parts) + ".", ""]
    if view.sheet_text:
        out += [f"Its look is in [`{view.name}_Stylesheet.yaml`](../stylesheets/{entry['slug']}/{_kebab(view.name)}.md).", ""]
    return out


def _widget_section(name: str) -> list[str]:
    decl = _widget(name)
    out = [f"### `{name}`", "", decl.doc or "A built-in widget.", ""]
    if decl.properties:
        out += ["| Property | Type | Default | Meaning |", "| --- | --- | --- | --- |"]
        for pname, prop in decl.properties.items():
            if prop.required:
                default = "required"
            else:
                default = _cell(prop.default) if prop.default not in (None, "", False) else ""
            spec = {"type": prop.type, "choices": prop.choices, "min": prop.minimum, "max": prop.maximum}
            model = " Two-way." if prop.model else ""
            out.append(f"| `{pname}` | {_type(spec)} | {default} | {_doc(prop.doc)}{model} |")
        out.append("")
    else:
        out += ["It takes no properties of its own (see [The View Language](../guide/view-language.md) for what every node takes).", ""]
    if decl.extras:
        out += ["Its `style:` also takes " + ", ".join(f"`{e}`" for e in decl.extras) + ".", ""]
    return out


def component_page(entry: dict[str, Any], views: dict[str, View]) -> str:
    out = [f"# {entry['title']}", "", f"*{entry['group']}*", "", "## In Material Design 3", "", entry["md3"].strip(), ""]
    out += ["## In Tesserae", "", entry["built"].strip(), ""]
    shown_views = [views[name] for name in entry.get("views") or []]
    widgets = entry.get("widgets") or []
    if shown_views or widgets:
        out += ["## How it is built", ""]
        if shown_views:
            out += ["A view Tesserae ships is a `<Name>_View.yaml` (what it takes and what it is made of) with a `<Name>_Stylesheet.yaml` (how it looks). "
                    "Use it by name: `widget: " + shown_views[0].name + "`. A file of the same name in your project replaces it.", ""]
        for view in shown_views:
            out += _view_section(view, entry)
        for name in widgets:
            out += _widget_section(name)
    elif entry.get("shares"):
        out += ["## How it is built", "", f"It is the same view as the [{entry['shares'].replace('-', ' ')}](../components/{entry['shares']}.md): see there for what it takes and how it looks.", ""]
    if entry.get("usage_view"):
        out += ["## Using it", ""] + _fence(entry["usage_view"].rstrip("\n"), "yaml")
    if entry.get("after"):
        out += entry["after"].rstrip("\n").split("\n") + [""]
    if entry.get("python"):
        out += ["## Using it in Python", ""] if entry.get("usage_view") else ["## Using it", "", "In Python:", ""]
        out += _fence(entry["python"], "python")
    sheeted = [v for v in shown_views if v.sheet_text]
    if sheeted:
        view = sheeted[0]
        rule = next((r for r in view.rules if {"background", "foreground"} & set(r["style"]) and r.get("part")), None) \
            or next((r for r in view.rules if {"background", "foreground"} & set(r["style"])), view.rules[0])
        field = "background" if "background" in rule["style"] else "foreground" if "foreground" in rule["style"] else next(iter(rule["style"]))
        selectors = {k: v for k, v in rule.items() if k not in ("style",)}
        selectors.setdefault("widget", view.name)
        out += ["## Changing its look", "",
                "To restyle it in your whole app, write rules for it in your app's stylesheet, or put `<Name>_Stylesheet.yaml` next to your views (or in `Styles/`); it is read only while the app uses the view. "
                "A rule names the widget and may narrow it by the properties it declares, a part and a state; the most specific rule wins, "
                "and a node's own `style:` beats every rule:", ""]
        out += _fence(f"# {view.name}_Stylesheet.yaml, or any stylesheet your app loads\nstyles:\n  - " + yaml.safe_dump(
            {**selectors, "style": {field: "tertiary"}}, default_flow_style=None, sort_keys=False, width=200).strip().replace("\n", "\n    "), "yaml")
        out += ["See [Component stylesheets](../stylesheets/index.md).", ""]
    see = [f"[{Path(p).stem.replace('-', ' ').title()}](../{p})" for p in entry.get("see", [])]
    out += ["## See also", "", "- " + "\n- ".join(see + ["[Python API reference](../api/python.md)", "[YAML reference](../api/yaml.md)"]), ""]
    return "\n".join(out)


def _when(rule: dict[str, Any]) -> str:
    """When a rule applies, in words: its selectors, state, classes and name."""
    parts = [f"`{k}: {v}`" for k, v in rule.items() if k not in ("widget", "part", "style", "state", "classes", "name")]
    if rule.get("state"):
        parts.append(f"state `{rule['state']}`")
    if rule.get("classes"):
        parts.append("classes " + ", ".join(f"`{c}`" for c in rule["classes"]))
    if rule.get("name"):
        parts.append(f"the node named `{rule['name']}`")
    return ", ".join(parts) or "always"


def stylesheet_page(entry: dict[str, Any], view: View, help_: dict[str, str]) -> str:
    out = [f"# {view.name}_Stylesheet.yaml", "", view.sheet_summary or f"The look of `{view.name}`.", "",
           f"The look of [`{view.name}`](../../components/{entry['slug']}.md) (in [{entry['title']}](../../components/{entry['slug']}.md)). "
           "[How component stylesheets work](../index.md).", "", "## The stylesheet", ""]
    out += _fence(view.sheet_text.rstrip("\n"), "yaml")
    out += ["## How it reaches the view", "",
            f"Each rule names `widget: {view.name}` and may add the properties the view declares (a `variant`, a `size`, a `shape`), `classes`, a node `name`, "
            "a `part` (one of the view's named nodes) and a `state` (`hovered`, `focused`, `pressed`, `disabled`, `selected`, ...). A rule's values may be "
            "expressions over the view's parameters. The most specific rule wins: a `name`, then the number of properties matched (all the `classes` count as one more), then a `state`, "
            "then the widget alone; a later rule wins a tie. These rules are the lowest layer: your app's stylesheet goes over them, and a node's own `style:` "
            "beats every rule for the fields it sets.", ""]
    by_part: dict[str, list[dict[str, Any]]] = {}
    for rule in view.rules:
        by_part.setdefault(rule.get("part") or "", []).append(rule)
    out += ["## The rules", ""]
    for part, rules in by_part.items():
        widget = dict(view.parts).get(part)
        out += [f"### `{part}`" + (f" ({widget})" if widget else "") if part else f"### `{view.name}` itself", "",
                "| When | Field | Value | What it does |", "| --- | --- | --- | --- |"]
        for rule in rules:
            when = _when(rule)
            for field, raw in rule["style"].items():
                out.append(f"| {when} | `{field}` | {_cell(raw)} | {_doc(help_.get(field, ''))} |")
        out.append("")
    first = next((r for r in view.rules if {"background", "foreground"} & set(r["style"])), view.rules[0])
    field = "background" if "background" in first["style"] else "foreground" if "foreground" in first["style"] else next(iter(first["style"]))
    selectors = {k: v for k, v in first.items() if k != "style"}
    out += ["## Changing it", "", "Write a rule of your own; it goes over this file's, field by field:", ""]
    out += _fence("styles:\n  - " + yaml.safe_dump({**selectors, "style": {field: "tertiary"}}, default_flow_style=None, sort_keys=False, width=200).strip().replace("\n", "\n    "), "yaml")
    return "\n".join(out)


def overview_components(data: dict[str, Any]) -> str:
    out = ["# MD3 Components", "",
           "Material Design 3's components, as Tesserae builds them. Each page says what the component is in MD3, how Tesserae builds it (the view or "
           "widget, with everything it takes), how to use it, and links to its stylesheet. The tree on the left opens and closes by group.", ""]
    for group in data["groups"]:
        out += [f"## {group}", "", "| Component | Made of |", "| --- | --- |"]
        for entry in data["components"]:
            if entry["group"] == group:
                made = [f"`{v}`" for v in entry.get("views") or []] + [f"`{w}`" for w in entry.get("widgets") or []]
                text = ", ".join(made) or (f"the {entry['shares'].replace('-', ' ')} view" if entry.get("shares") else "see the page")
                out.append(f"| [{entry['title']}]({entry['slug']}.md) | {text} |")
        out.append("")
    return "\n".join(out)


def overview_stylesheets(data: dict[str, Any], views: dict[str, View]) -> str:
    out = ["# Component Stylesheets", "",
           "Most shipped views keep their look in a stylesheet, `<Name>_Stylesheet.yaml`, beside the view itself, `<Name>_View.yaml` (a few, such as the tab and chip groups, have only their params). Each page here shows one "
           "stylesheet, how its rules reach the view, and what each part's rules do.", "",
           "## How they work", "",
           "A stylesheet is a list of rules. A rule names a widget (the view), may narrow it, and gives a `style`:", ""]
    out += _fence("styles:\n  - widget: Button\n    variant: filled\n    style: {background: primary, foreground: on_primary}\n"
                  "  - widget: Button\n    variant: filled\n    state: disabled\n    style: {background: \"on_surface@12%\"}\n"
                  "  - widget: Card\n    part: headline\n    style: {foreground: on_surface}", "yaml")
    out += ["- A rule narrows by the properties the view declares (`variant`, `size`, `shape`), `classes`, a node `name`, a `part` (a named node inside the view) and a `state`.",
            "- A value in `{{ }}` is an expression over the view's parameters, worked out where the view is used.",
            "- The most specific rule wins; a node's own `style:` beats every rule for the fields it sets.",
            "- A stylesheet is read only when the application uses its widget: the widgets in the views you open, and in the views those call. The shipped rules are the lowest layer, a `<Name>_Stylesheet.yaml` of yours (next to your views, or in `Styles/`) goes over them, and your app's stylesheet goes over that. A view of the same name that you wrote replaces the shipped one and its look.",
            "- Hot reload watches the stylesheets a view uses.", "",
            "See [The View Language](../guide/view-language.md#style) for the rule syntax and [Themes](../themes/index.md) for colours, type and shape.", ""]
    for group in data["groups"]:
        entries = [e for e in data["components"] if e["group"] == group and any(views[v].sheet_text for v in e.get("views") or [])]
        if not entries:
            continue
        out += [f"## {group}", ""]
        for entry in entries:
            links = ", ".join(f"[`{v}`]({entry['slug']}/{_kebab(v)}.md)" for v in entry["views"] if views[v].sheet_text)
            out.append(f"- **{entry['title']}**: {links}")
        out.append("")
    return "\n".join(out)


def nav_block(data: dict[str, Any], views: dict[str, View]) -> str:
    lines = ["  - Components:", "      - Overview: components/index.md"]
    for group in data["groups"]:
        lines.append(f"      - {group}:")
        for entry in data["components"]:
            if entry["group"] == group:
                lines.append(f"          - {entry['title']}: components/{entry['slug']}.md")
    lines += ["  - Stylesheets:", "      - Overview: stylesheets/index.md"]
    for group in data["groups"]:
        entries = [e for e in data["components"] if e["group"] == group and any(views[v].sheet_text for v in e.get("views") or [])]
        if not entries:
            continue
        lines.append(f"      - {group}:")
        for entry in entries:
            lines.append(f"          - {entry['title']}:")
            for name in entry["views"]:
                if views[name].sheet_text:
                    lines.append(f"              - {name}: stylesheets/{entry['slug']}/{_kebab(name)}.md")
    return "\n".join(lines)


def check_coverage(data: dict[str, Any], shipped: list[str]) -> None:
    """Every shipped view under exactly one component, every built-in widget under one or in `NOT_COMPONENTS`, every name real."""
    listed = [v for entry in data["components"] for v in entry.get("views") or []]
    problems = []
    if sorted(listed) != sorted(shipped):
        problems.append(f"shipped views not listed: {sorted(set(shipped) - set(listed))}; "
                        f"named but not shipped, or listed twice: {sorted(set(listed) - set(shipped)) or sorted({v for v in listed if listed.count(v) > 1})}")
    placed = {w for entry in data["components"] for w in entry.get("widgets") or []}
    registered = _registered_widgets()
    missing = sorted(registered - placed - NOT_COMPONENTS - set(shipped))
    if missing:
        problems.append(f"built-in widgets under no component (list them, or add to NOT_COMPONENTS): {missing}")
    unknown = sorted(placed - registered)
    if unknown:
        problems.append(f"widgets named that are not registered: {unknown}")
    slugs = {entry["slug"] for entry in data["components"]}
    bad_shares = sorted(e["slug"] for e in data["components"] if e.get("shares") and e["shares"] not in slugs)
    if bad_shares:
        problems.append(f"`shares` names no component: {bad_shares}")
    if problems:
        raise SystemExit("tools/component_docs.yaml: " + "; ".join(problems))


def build() -> dict[Path, str]:
    data = yaml.safe_load(DATA.read_text(encoding="utf-8"))
    shipped = sorted(p.name.removesuffix("_View.yaml") for p in VIEWS.glob("*_View.yaml"))
    check_coverage(data, shipped)
    views = {name: View(name) for name in shipped}
    help_ = _style_field_help()
    pages: dict[Path, str] = {DOCS / "components" / "index.md": overview_components(data),
                              DOCS / "stylesheets" / "index.md": overview_stylesheets(data, views)}
    for entry in data["components"]:
        pages[DOCS / "components" / f"{entry['slug']}.md"] = component_page(entry, views)
        for name in entry.get("views") or []:
            if views[name].sheet_text:
                pages[DOCS / "stylesheets" / entry["slug"] / f"{_kebab(name)}.md"] = stylesheet_page(entry, views[name], help_)
    pages = {path: text.rstrip("\n") + "\n" for path, text in pages.items()}
    pages[MKDOCS] = _with_nav(MKDOCS.read_text(encoding="utf-8"), nav_block(data, views))
    return pages


def _with_nav(text: str, block: str) -> str:
    start, end = (re.escape(mark) for mark in NAV_MARKS)
    pattern = re.compile(rf"(?P<head>^[ ]*{start}\n).*?(?P<tail>^[ ]*{end}$)", re.S | re.M)
    if not pattern.search(text):
        raise SystemExit(f"mkdocs.yml needs the lines `{NAV_MARKS[0]}` and `{NAV_MARKS[1]}` where the tree goes")
    return pattern.sub(lambda m: m.group("head") + block + "\n" + m.group("tail"), text)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--check", action="store_true", help="exit 1 if the pages are out of date")
    args = parser.parse_args()
    pages = build()
    stale = [p for p, t in pages.items() if not p.exists() or p.read_text(encoding="utf-8") != t]
    # pages for a component that has gone
    existing = {p for folder in (DOCS / "components", DOCS / "stylesheets") for p in folder.rglob("*.md")}
    orphans = sorted(existing - set(pages))
    if args.check:
        for path in [*stale, *orphans]:
            print(f"out of date: {path.relative_to(ROOT)}")
        return 1 if stale or orphans else 0
    for path, text in pages.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    for path in orphans:
        path.unlink()
        print(f"removed: {path.relative_to(ROOT)}")
    for folder in sorted((DOCS / "stylesheets").glob("*/")):
        if folder.is_dir() and not any(folder.iterdir()):
            folder.rmdir()
    print(f"wrote {len(pages)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
