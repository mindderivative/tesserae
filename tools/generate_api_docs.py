#!/usr/bin/env python3
"""Writes the Python API reference page, `docs/api/python.md` (0.3.4, #83).

One page for every public class, function and constant, read from the code:
the names a module lists in `__all__`, a class's public methods and
properties, each with its signature and the first paragraph of its docstring.
Nothing is written by hand, so a new method can't be left out; one with no
docstring is listed by `--check`, and the test fails.

    python tools/generate_api_docs.py          # write docs/api/python.md
    python tools/generate_api_docs.py --check  # exit 1 if it is out of date, or anything has no description
"""

from __future__ import annotations

import argparse
import enum
import importlib
import inspect
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "docs" / "api" / "python.md"

#: (module, heading, one line on what it is[, the names to list, if not the module's `__all__`]), in page order.
SECTIONS = (
    ("tesserae.app", "App", "The entry point: screens, one window, the loop.", ("App",)),
    ("tesserae.reactive", "Reactivity", "Signals, computed values, effects and the ViewModel base class."),
    ("tesserae.view", "Views and components", "A loaded `*_View.yaml`, and an embedded instance of one."),
    ("tesserae.component", "Embedding", "A component with a ViewModel of its own, inside a view.", ("instantiate",)),
    ("tesserae.repeater", "Repeater", "A list signal kept in step with a list of components.", ("Repeater",)),
    ("tesserae.theme", "Themes", "A resolved MD3 theme, read from code."),
    ("tesserae.tokens", "Tokens", "MD3's colour, type, shape and motion tokens."),
    ("tesserae.widgets", "Widgets", "One function per MD3 widget, called against a window."),
    ("tesserae.controls", "Controls", "MD3's stateful controls."),
    ("tesserae.overlays", "Overlays", "Dialogs, menus, snackbars, tooltips, sheets, drawers."),
    ("tesserae.shell", "App shell", "Bars, navigation and docked zones around the screens."),
    ("tesserae.shell_file", "Shell files", "Reading and building a `*_Shell.yaml`."),
    ("tesserae.docking", "Docking", "Panels the user can drag between zones."),
    ("tesserae.interaction", "Interaction", "State layer, ripple and focus ring."),
    ("tesserae.a11y", "Accessibility", "What a node tells assistive technology."),
    ("tesserae.binding", "Bindings", "The `{{ expression }}` language."),
    ("tesserae.fonts", "Fonts", "Registering font files.", ("register_font",)),
    ("tesserae.icons", "Icons", "The built-in icon set."),
    ("tesserae.log", "Logging", "Tesserae's log format."),
    ("tesserae.spec", "Spec loading", "Reading, expanding and watching view files."),
)

def _paragraph(doc: str | None, sentences: int = 1) -> str:
    """The first `sentences` sentences of a docstring's first paragraph, on one line."""
    if not doc:
        return ""
    first = re.sub(r"\s+", " ", inspect.cleandoc(doc).split("\n\n", 1)[0]).strip()
    cut, found = 0, 0
    for match in re.finditer(r"(?<!e\.g)(?<!i\.e)(?<!etc)\. (?=[A-Z`(\"])", first):
        found += 1
        cut = match.start() + 1
        if found == sentences:
            return first[:cut]
    return first


def _annotation(note: Any) -> str:
    text = note if isinstance(note, str) else getattr(note, "__name__", None) or str(note)
    return re.sub(r"\btesserae\.[\w.]*\.(\w+)", r"\1", text).replace("typing.", "")


def _default(value: Any) -> str:
    """A default as source reads it: a lambda or function by its name, a set in order."""
    if hasattr(value, "write") and hasattr(value, "flush"):  # a stream, as the signature's `sys.stderr`
        return "sys.stderr"
    if callable(value) and getattr(value, "__name__", None):
        return "<lambda>" if value.__name__ == "<lambda>" else value.__name__
    if isinstance(value, (set, frozenset)):
        return "{" + ", ".join(sorted(map(repr, value))) + "}"
    return repr(value)


def _signature(obj: Any, name: str) -> str:
    """`name(param: annotation = default, ...) -> annotation`, annotations as written."""
    try:
        sig = inspect.signature(obj)
    except (TypeError, ValueError):
        return name
    parts, star = [], False
    for param in sig.parameters.values():
        text = param.name
        if param.kind is param.VAR_POSITIONAL:
            text, star = "*" + text, True
        elif param.kind is param.VAR_KEYWORD:
            text = "**" + text
        elif param.kind is param.KEYWORD_ONLY and not star:
            parts.append("*")
            star = True
        if param.annotation is not param.empty:
            text += f": {_annotation(param.annotation)}"
        if param.default is not param.empty:
            text += f" = {_default(param.default)}"
        parts.append(text)
    out = f"{name}({', '.join(parts)})"
    if sig.return_annotation is not sig.empty:
        out += f" -> {_annotation(sig.return_annotation)}"
    return out


def _wrap(signature: str) -> str:
    """A long signature, one parameter to a line."""
    if len(signature) <= 88:
        return signature
    head, _, rest = signature.partition("(")
    body, _, tail = rest.rpartition(")")
    parts, depth, current = [], 0, ""
    for char in body:
        depth += char in "([{"
        depth -= char in ")]}"
        if char == "," and depth == 0:
            parts.append(current.strip())
            current = ""
        else:
            current += char
    if current.strip():
        parts.append(current.strip())
    return f"{head}(\n" + ",\n".join("    " + part for part in parts) + f"\n){tail}"


def _own(cls: type) -> bool:
    return cls.__module__.split(".")[0] == "tesserae"


def _public_members(cls: type) -> list[tuple[str, Any]]:
    """The public methods and properties `cls` itself defines; a base's are listed under the base."""
    return sorted((name, value) for name, value in vars(cls).items() if not name.startswith("_"))


def _kind(value: Any) -> str:
    if isinstance(value, property):
        return "property"
    if callable(_func_of(value)):
        return "method"
    return "attribute"


def _func_of(value: Any) -> Any:
    return value.__func__ if isinstance(value, (classmethod, staticmethod)) else value


def _describe_class(cls: type, qualname: str, missing: list[str]) -> list[str]:
    bases = [base.__name__ for base in cls.__bases__ if base is not object and _own(base)]
    desc = _paragraph(cls.__doc__, 2)
    if not desc:
        missing.append(qualname)
    sig = _wrap(_signature(cls, cls.__name__))
    out = [f"### `{cls.__name__}`", "", "```python", f"class {sig}" + (f"  # extends {', '.join(bases)}" if bases else ""), "```", ""]
    if desc:
        out += [desc, ""]
    if bases:
        out += [f"Also has everything {' and '.join(f'`{b}`' for b in bases)} has.", ""]
    if issubclass(cls, enum.Enum):
        out += ["| Member | Value |", "| --- | --- |"] + [f"| `{m.name}` | `{m.value!r}` |" for m in cls] + [""]
    rows = []
    for name, value in _public_members(cls):
        kind = _kind(value)
        if kind == "attribute":
            continue
        func = _func_of(value)
        doc = _paragraph(inspect.getdoc(getattr(cls, name)) if kind != "property" else inspect.getdoc(value))
        if not doc:
            missing.append(f"{qualname}.{name}")
        if kind == "property":
            sig = name
        else:
            sig = _signature(func, name)
            for lead in ("self", "cls"):
                sig = sig.replace(f"({lead}, ", "(").replace(f"({lead})", "()")
        rows.append((kind, sig, doc))
    for kind, sig, doc in rows:
        out.append(f"- `{sig}`" + (" *(property)*" if kind == "property" else "") + f": {doc}")
    return out + ([""] if rows else [])


def _describe_function(fn: Any, name: str, qualname: str, missing: list[str]) -> list[str]:
    desc = _paragraph(fn.__doc__, 2)
    if not desc:
        missing.append(qualname)
    return [f"### `{name}`", "", "```python", _wrap(_signature(fn, name)), "```", ""] + ([desc, ""] if desc else [])


def _describe_constant(value: Any, name: str) -> str:
    shown = _default(value)
    if len(shown) > 90:
        shown = f"{type(value).__name__} of {len(value)}" if hasattr(value, "__len__") else type(value).__name__
    return f"- `{name}` = `{shown}`"


def render() -> tuple[str, list[str]]:
    missing: list[str] = []
    out = ["# Python API Reference", "",
           "Every public class, function and constant, with its signature and what it does. "
           "This page is written from the code by `tools/generate_api_docs.py`, so it can't fall behind it.", ""]
    contents = ["## Contents", ""]
    body: list[str] = []
    seen: set[int] = set()
    for module_name, heading, blurb, *only in SECTIONS:
        module = importlib.import_module(module_name)
        names = list(only[0]) if only else list(getattr(module, "__all__", ()))
        classes, functions, constants = [], [], []
        for name in names:
            value = getattr(module, name)
            if inspect.ismodule(value):
                continue
            if inspect.isclass(value) or callable(value):
                if id(value) in seen:
                    continue
                seen.add(id(value))
                (classes if inspect.isclass(value) else functions).append((name, value))
            else:
                constants.append((name, value))
        if not (classes or functions or constants):
            continue
        anchor = re.sub(r"[^a-z0-9 -]", "", heading.lower()).replace(" ", "-")
        contents.append(f"- [{heading}](#{anchor}): {blurb}")
        body += [f"## {heading}", "", f"`{module_name}`: {blurb}", ""]
        for name, cls in classes:
            body += _describe_class(cls, f"{module_name}.{name}", missing)
        for name, fn in functions:
            body += _describe_function(fn, name, f"{module_name}.{name}", missing)
        if constants:
            body += ["**Constants**", ""] + [_describe_constant(v, n) for n, v in constants] + [""]
    return "\n".join(out + contents + [""] + body).rstrip() + "\n", missing


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--check", action="store_true", help="exit 1 if the page is out of date or anything has no description")
    args = parser.parse_args()
    text, missing = render()
    if args.check:
        bad = False
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != text:
            print(f"{OUTPUT.relative_to(ROOT)} is out of date: run `python tools/generate_api_docs.py`")
            bad = True
        if missing:
            print("no docstring:\n  " + "\n  ".join(missing))
            bad = True
        return 1 if bad else 0
    OUTPUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUTPUT.relative_to(ROOT)}: {len(text.splitlines())} lines; {len(missing)} without a docstring")
    print("\n".join(f"  {name}" for name in missing))
    return 0


if __name__ == "__main__":
    sys.exit(main())
