#!/usr/bin/env python3
"""Writes the component pages and the stylesheet pages (0.3.4, #83).

- `docs/components/<slug>.md`: one page for each MD3 component, from `tools/component_docs.yaml`
  (the MD3 text, the usage examples) and the fragments themselves (their YAML, parameters and parts).
- `docs/stylesheets/<slug>/<fragment>.md`: one page for each component stylesheet: the file, how it is tied to
  its component, what each part's rules do, and what they expand to for example parameters.
- the two overview pages, and the `nav:` entries for both, between markers in `mkdocs.yml`.

    python tools/generate_component_docs.py          # write them
    python tools/generate_component_docs.py --check  # exit 1 if they are out of date
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import sys
import textwrap
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "tools" / "component_docs.yaml"
FRAGMENTS = ROOT / "src" / "tesserae" / "spec" / "components"
DOCS = ROOT / "docs"
MKDOCS = ROOT / "mkdocs.yml"
NAV_MARKS = ("# >>> components (written by tools/generate_component_docs.py)", "# <<< components")

#: Example values for a fragment's parameters, to show what its stylesheet expands to.
SAMPLE = {"label": "Go", "title": "Title", "text": "Hello", "headline": "Headline", "width": 120, "height": 40,
          "corner_radius": 20, "size": 40, "icon": "home", "value": 0.5, "src": "photo.png", "fit": "cover",
          "placeholder": "Search", "day": 7, "hour": 3, "minute": 15, "background": "primary", "left_padding": 16,
          "item_width": 100, "scrim_width": 400, "scrim_height": 300, "frame": "frame", "min": 0, "max": 10, "step": 1,
          "typography_role": "body_large", "color": "primary", "fab_size": "default", "button": "ButtonFilled",
          "selected": False, "checked": False}
ITEMS = {"ButtonGroup": [{"label": "A"}, {"label": "B"}], "Menu": [{"label": "A"}, {"label": "B"}],
         "Tabs": [{"label": "A", "selected": True}, {"label": "B"}],
         "NavigationRail": [{"label": "A", "icon": "home", "selected": True}, {"label": "B", "icon": "search"}],
         "NavigationDrawer": [{"label": "A", "icon": "home", "selected": True}, {"label": "B", "icon": "search"}]}


def _kebab(name: str) -> str:
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "-", name).lower()


def _style_field_help() -> dict[str, str]:
    """What each style field does, from the schema generator's own descriptions."""
    spec = importlib.util.spec_from_file_location("generate_yaml_schema", ROOT / "tools" / "generate_yaml_schema.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    style = module._definitions(fragment=False)["style"]["properties"]
    return {name: " ".join(prop.get("description", "").split()) for name, prop in style.items()}


# -- reading the fragments ---------------------------------------------------------------------

class Fragment:
    def __init__(self, name: str) -> None:
        self.name = name
        self.path = FRAGMENTS / f"{name}_Component.yaml"
        self.text = self.path.read_text(encoding="utf-8")
        self.data = yaml.safe_load(self.text)
        self.summary = self.text.splitlines()[0].lstrip("# ").strip()
        self.sheet_path = FRAGMENTS / f"{name}_Stylesheet.yaml"
        self.sheet_text = self.sheet_path.read_text(encoding="utf-8") if self.sheet_path.exists() else None
        self.rules = yaml.safe_load(self.sheet_text)["styles"] if self.sheet_text else []
        self.params: list[tuple[str, bool, Any]] = []  # (name, required, default)
        for entry in self.data.get("params") or []:
            if isinstance(entry, str):
                self.params.append((entry, True, None))
            else:
                key, default = next(iter(entry.items()))
                self.params.append((key, False, default))

    @property
    def body(self) -> str:
        """The fragment's YAML without its header comment."""
        return "\n".join(line for line in self.text.splitlines() if not line.startswith("#")).strip() + "\n"

    def parts(self) -> list[tuple[str, str]]:
        out: list[tuple[str, str]] = []

        def walk(node: dict[str, Any]) -> None:
            if isinstance(node.get("id"), str):
                kind = node.get("kind") or ("component " + str(node["component"]) if "component" in node else "?")
                out.append((node["id"], kind))
            for child in node.get("children") or []:
                walk(child)

        walk(self.data)
        return out

    def sample(self) -> dict[str, Any]:
        params = {name: SAMPLE[name] for name, required, _ in self.params if name in SAMPLE}
        if "items" in {name for name, _, _ in self.params}:
            params["items"] = ITEMS[self.name]
        return params

    def expanded_styles(self) -> dict[str, Any]:
        """Each part's style once the stylesheet is applied, for the example parameters."""
        from tesserae.spec.expand import expand_components_to_spec

        spec = expand_components_to_spec(yaml.safe_dump({"id": "x", "component": self.name, "with": self.sample()}))
        out: dict[str, Any] = {}

        def walk(node: dict[str, Any]) -> None:
            if node.get("style"):
                out[node["id"].removeprefix("x.") if node["id"] != "x" else "root"] = node["style"]
            for child in node.get("children") or []:
                walk(child)

        walk(spec)
        return out


def _value(raw: Any) -> str:
    """A rule's value in words: a parameter, a conditional, or the value itself."""
    if isinstance(raw, str):
        found = re.fullmatch(r"\{\{\s*(\w+)\s*\}\}", raw)
        if found:
            return f"the `{found.group(1)}` parameter"
    if isinstance(raw, dict) and "if" in raw:
        cond = re.sub(r"[{}\s]", "", str(raw["if"]))
        text = f"{_value(raw['then'])} if `{cond}`"
        return text + (f", else {_value(raw['else'])}" if "else" in raw else "")
    if isinstance(raw, dict):
        return ", ".join(f"{k} {_value(v)}" for k, v in raw.items())
    return f"`{raw}`"


# -- the pages ---------------------------------------------------------------------------------

def _fence(code: str, lang: str) -> list[str]:
    return [f"```{lang}", code.rstrip("\n"), "```", ""]


def _indent(text: str, by: int) -> str:
    return textwrap.indent(text.rstrip("\n"), " " * by)


def component_page(entry: dict[str, Any], fragments: dict[str, Fragment], rel_sheet) -> str:
    out = [f"# {entry['title']}", "", f"*{entry['group']}*", "", "## In Material Design 3", "", entry["md3"].strip(), ""]
    out += ["## In Tesserae", "", entry["built"].strip(), ""]
    frags = [fragments[name] for name in entry["fragments"]]
    if frags:
        out += ["| Fragment | What it is | Stylesheet |", "| --- | --- | --- |"]
        for frag in frags:
            sheet = f"[`{frag.name}_Stylesheet.yaml`]({rel_sheet(entry, frag)})" if frag.sheet_text else "none: the control draws itself"
            out.append(f"| `component: {frag.name}` | {frag.summary} | {sheet} |")
        out.append("")
        out += ["## How it is built", "",
                "Each fragment is a `*_Component.yaml`: its structure, and the parameters it takes. "
                "Its look is in its stylesheet, linked under each one.", ""]
        groups: list[list[Fragment]] = []  # fragments with one structure and parameters are shown once
        for frag in frags:
            for group in groups:
                if group[0].body == frag.body and group[0].params == frag.params:
                    group.append(frag)
                    break
            else:
                groups.append([frag])
        for group in groups:
            out += ["### " + ", ".join(f"`{f.name}`" for f in group), ""]
            if len(group) == 1:
                frag = group[0]
                link = f" Its look: [`{frag.name}_Stylesheet.yaml`]({rel_sheet(entry, frag)})." if frag.sheet_text else ""
                out += [f"{frag.summary}{link}", ""]
            first = group[0]
            if first.params:
                out += ["| Parameter | | Default |", "| --- | --- | --- |"]
                for name, required, default in first.params:
                    out.append(f"| `{name}` | {'required' if required else 'optional'} | {'' if required else f'`{default}`'} |")
                out.append("")
            else:
                out += ["It takes no parameters.", ""]
            if len(group) > 1:
                out += [f"These {len(group)} have one structure; only their stylesheets, above, differ.", ""]
            out += _fence(first.body, "yaml")
    else:
        out += ["This component has no `component:` fragment: build it in Python.", ""]
    if entry.get("usage"):
        out += ["## Using it", "", "In a view:", ""]
        out += _fence("# Home_View.yaml\nid: root\nkind: Container\nchildren:\n" + _indent(entry["usage"], 2), "yaml")
    if entry.get("python"):
        out += ["In Python:" if entry.get("usage") else "## Using it", ""] if entry.get("usage") else ["## Using it", "", "In Python:", ""]
        out += _fence(entry["python"], "python")
    sheeted = [f for f in frags if f.sheet_text]
    if sheeted:
        frag = sheeted[0]
        rule = next((r for r in frag.rules if {"background", "foreground"} & set(r["style"])), frag.rules[0])
        field = "background" if "background" in rule["style"] else "foreground" if "foreground" in rule["style"] else next(iter(rule["style"]))
        out += ["## Changing its look", "",
                "To restyle a component in your whole app, put a stylesheet of the same name next to your views. "
                "Its rules go over the built-in ones, field by field, and the rest is kept:", ""]
        out += _fence(f"# {frag.name}_Stylesheet.yaml, next to your views\nstyles:\n  - id: {rule['id']}\n    style: {{{field}: tertiary}}", "yaml")
        out += ["See [Component stylesheets](../stylesheets/index.md).", ""]
    see = [f"[{Path(p).stem.replace('-', ' ').title()}](../{p})" for p in entry.get("see", [])]
    out += ["## See also", "", "- " + "\n- ".join(see + ["[Python API reference](../api/python.md)", "[YAML reference](../api/yaml.md)"]), ""]
    return "\n".join(out)


def stylesheet_page(entry: dict[str, Any], frag: Fragment, help_: dict[str, str]) -> str:
    out = [f"# {frag.name}_Stylesheet.yaml", "", frag.summary, "",
           f"The look of [`{frag.name}`](../../components/{entry['slug']}.md) (in [{entry['title']}](../../components/{entry['slug']}.md)). "
           "[How component stylesheets work](../index.md).", "",
           "## The stylesheet", ""]
    out += _fence(frag.sheet_text.rstrip("\n"), "yaml")
    out += ["## How it is tied to the component", "",
            f"`{frag.name}_Component.yaml` holds the structure: the parts, each with an `id`. This file holds the look: "
            "each rule's `id` names a part, and its `style` is what that part looks like. When a view uses "
            f"`component: {frag.name}`, Tesserae fills in the parameters (a value like `\"{{{{ width }}}}\"` becomes the "
            "`width` the view passed), picks a branch of any `if:`, and puts each rule under the style the part "
            "already has, so a part's own `style:` always wins.", ""]
    parts = dict(frag.parts())
    out += ["## The parts", ""]
    for rule in frag.rules:
        out += [f"### `{rule['id']}` ({parts.get(rule['id'], '?')})", "", "| Field | Value | What it does |", "| --- | --- | --- |"]
        for field, raw in rule["style"].items():
            out.append(f"| `{field}` | {_value(raw)} | {help_.get(field, '')} |")
        out.append("")
    expanded = frag.expanded_styles()
    if expanded:
        shown = {part: expanded[part] for part in expanded}
        out += ["## What it makes", "",
                f"With `{', '.join(f'{k}: {v}' for k, v in frag.sample().items() if not isinstance(v, list))}"
                + ("`, and a list of items" if "items" in frag.sample() else "`") + ", each part's style is:", ""]
        out += _fence(yaml.safe_dump(shown, sort_keys=False, default_flow_style=None, width=100), "yaml")
    rule = next((r for r in frag.rules if {"background", "foreground"} & set(r["style"])), frag.rules[0])
    field = "background" if "background" in rule["style"] else "foreground" if "foreground" in rule["style"] else next(iter(rule["style"]))
    out += ["## Changing it", "",
            f"Put a `{frag.name}_Stylesheet.yaml` next to your views. Its rules go over this file's, field by field:", ""]
    out += _fence(f"styles:\n  - id: {rule['id']}\n    style: {{{field}: tertiary}}", "yaml")
    return "\n".join(out)


def overview_components(data: dict[str, Any]) -> str:
    out = ["# MD3 Components", "",
           "Material Design 3's components, as Tesserae builds them. Each page says what the component is in MD3, how "
           "Tesserae builds it (the YAML), how to use it, and links to its stylesheet. The tree on the left opens "
           "and closes by group.", ""]
    for group in data["groups"]:
        out += [f"## {group}", "", "| Component | Fragments |", "| --- | --- |"]
        for entry in data["components"]:
            if entry["group"] == group:
                frags = ", ".join(f"`{f}`" for f in entry["fragments"]) or "Python only"
                out.append(f"| [{entry['title']}]({entry['slug']}.md) | {frags} |")
        out.append("")
    return "\n".join(out)


def overview_stylesheets(data: dict[str, Any], fragments: dict[str, Fragment]) -> str:
    out = ["# Component Stylesheets", "",
           "Every built-in component keeps its look in a stylesheet, `<Name>_Stylesheet.yaml`, beside its structure, "
           "`<Name>_Component.yaml`. Each page here shows one stylesheet, how it is tied to its component, "
           "and what it makes.", "",
           "## How they work", "",
           "A stylesheet is a list of rules. Each names a part of the component by its `id` and gives that part's `style`:", ""]
    out += _fence('styles:\n  - id: root\n    style: {background: primary, width: "{{ width }}"}\n  - id: label\n    style: {foreground: on_primary}', "yaml")
    out += ["- A value in `{{ }}` is one of the component's parameters, filled in where the component is used.",
            "- A value can be `{if: \"{{ selected }}\", then: primary, else: on_surface}`, chosen by a parameter.",
            "- A part's own `style:` in the fragment is kept, and wins over its stylesheet.",
            "- Your own `<Name>_Stylesheet.yaml` next to your views goes over the built-in one, field by field. "
            "A fragment of your own with the same name as a built-in one replaces it, and the built-in stylesheet "
            "with it.",
            "- Hot reload watches the stylesheets a view uses.", "",
            "This is a different thing from a view's stylesheet (`App(stylesheet=)`), whose rules match many nodes "
            "by `kind`, `classes` or `id`: see [Themes](../themes/index.md). A component's stylesheet styles one "
            "component's parts.", ""]
    for group in data["groups"]:
        entries = [e for e in data["components"] if e["group"] == group and any(fragments[f].sheet_text for f in e["fragments"])]
        if not entries:
            continue
        out += [f"## {group}", ""]
        for entry in entries:
            links = ", ".join(f"[`{f}`]({entry['slug']}/{_kebab(f)}.md)" for f in entry["fragments"] if fragments[f].sheet_text)
            out.append(f"- **{entry['title']}**: {links}")
        out.append("")
    return "\n".join(out)


def nav_block(data: dict[str, Any], fragments: dict[str, Fragment]) -> str:
    lines = ["  - Components:", "      - Overview: components/index.md"]
    for group in data["groups"]:
        lines.append(f"      - {group}:")
        for entry in data["components"]:
            if entry["group"] == group:
                lines.append(f"          - {entry['title']}: components/{entry['slug']}.md")
    lines += ["  - Stylesheets:", "      - Overview: stylesheets/index.md"]
    for group in data["groups"]:
        entries = [e for e in data["components"] if e["group"] == group and any(fragments[f].sheet_text for f in e["fragments"])]
        if not entries:
            continue
        lines.append(f"      - {group}:")
        for entry in entries:
            lines.append(f"          - {entry['title']}:")
            for name in entry["fragments"]:
                if fragments[name].sheet_text:
                    lines.append(f"              - {name}: stylesheets/{entry['slug']}/{_kebab(name)}.md")
    return "\n".join(lines)


def build() -> dict[Path, str]:
    data = yaml.safe_load(DATA.read_text(encoding="utf-8"))
    names = sorted(p.name.removesuffix("_Component.yaml") for p in FRAGMENTS.glob("*_Component.yaml"))
    fragments = {name: Fragment(name) for name in names}
    listed = [name for entry in data["components"] for name in entry["fragments"]]
    if sorted(listed) != names:
        raise SystemExit(f"tools/component_docs.yaml must list every fragment once: missing {sorted(set(names) - set(listed))}, "
                         f"extra or repeated {sorted(set(listed) - set(names)) or sorted({n for n in listed if listed.count(n) > 1})}")
    help_ = _style_field_help()

    def rel_sheet(entry: dict[str, Any], frag: Fragment) -> str:
        return f"../stylesheets/{entry['slug']}/{_kebab(frag.name)}.md"

    pages: dict[Path, str] = {DOCS / "components" / "index.md": overview_components(data),
                              DOCS / "stylesheets" / "index.md": overview_stylesheets(data, fragments)}
    for entry in data["components"]:
        pages[DOCS / "components" / f"{entry['slug']}.md"] = component_page(entry, fragments, rel_sheet)
        for name in entry["fragments"]:
            if fragments[name].sheet_text:
                pages[DOCS / "stylesheets" / entry["slug"] / f"{_kebab(name)}.md"] = stylesheet_page(entry, fragments[name], help_)
    pages = {path: text.rstrip("\n") + "\n" for path, text in pages.items()}
    pages[MKDOCS] = _with_nav(MKDOCS.read_text(encoding="utf-8"), nav_block(data, fragments))
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
        print(f"leftover (delete it): {path.relative_to(ROOT)}")
    print(f"wrote {len(pages)} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
