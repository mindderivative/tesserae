"""`tesserae migrate-yaml`: moves a project's view files to the current syntax (spec section 15; phase 7 of #209).

`migrate_project(root)` reads every `*_View.yaml`, `*_Component.yaml` and `*_Stylesheet.yaml` under `root` and works out what each becomes:

- a view or a fragment in the old syntax is translated (`spec/translate.py`); a fragment is renamed `*_View.yaml`; a view that has a
  `<Name>_ViewModel.py` beside it gets `name: <Name>`, the bind key the ViewModel's `views` lists;
- a stylesheet in the old shape becomes rules: a component's own stylesheet names the view and its parts, an app's maps `kind` to `widget` and
  `id` to `name`;
- a file already in the new syntax is left alone, and so are themes and style files.

Before anything is written every result is checked with the same loader the app uses. By default nothing is written (a dry run that reports);
`write=True` writes only if every file checked out, or `force=True` writes what translated anyway. Header comments (the `#` lines at the top
of a file) are kept; comments inside a file are not, and the report says which files had them. ViewModels are Python, so the report lists what to
change in them instead of changing them.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml

from tesserae.spec.nodes import LoadError, parse_view
from tesserae.spec.rules import RuleSheet, is_rule_sheet
from tesserae.spec.translate import Translator, to_yaml, translate_rules
from tesserae.spec.widgets import WidgetDecl, decl_from_params

__all__ = ["FileResult", "Report", "migrate_project"]

_SKIPPED = frozenset({".git", ".venv", "venv", "node_modules", "site", "build", "dist", "__pycache__", "site-packages"})
_OLD_KEYS = ("kind", "component", "view", "include")
_VIEW = re.compile(r"^(.*)_(View|Component)\.yaml$")
_SHEET = re.compile(r"^(.*)_Stylesheet\.yaml$")
_OLD_INIT = re.compile(r"def\s+__init__\s*\(\s*self\s*,\s*view\b")


@dataclass
class FileResult:
    """What one file becomes. `status` is `migrated`, `current` (already new), `skipped` or `failed`."""

    path: Path
    status: str
    new_path: Optional[Path] = None
    text: Optional[str] = None
    notes: list[str] = field(default_factory=list)
    error: Optional[str] = None
    lost_comments: bool = False


@dataclass
class Report:
    results: list[FileResult] = field(default_factory=list)
    python: list[str] = field(default_factory=list)
    written: bool = False

    @property
    def failed(self) -> list[FileResult]:
        return [r for r in self.results if r.status == "failed"]

    def render(self, root: Optional[Path] = None) -> str:
        def rel(path: Path) -> str:
            try:
                return (path.relative_to(root) if root else path).as_posix()
            except ValueError:
                return path.as_posix()

        lines: list[str] = []
        for r in self.results:
            target = f" -> {rel(r.new_path)}" if r.new_path and r.new_path != r.path else ""
            detail = f": {r.error}" if r.error else ""
            lines.append(f"{r.status:<9} {rel(r.path)}{target}{detail}")
            lines.extend(f"          note: {note}" for note in r.notes)
            if r.lost_comments:
                lines.append("          note: comments inside the file were not kept (the ones at the top were)")
        if self.python:
            lines.append("")
            lines.append("In the ViewModels (Python):")
            lines.extend(f"  {item}" for item in self.python)
        counts = {s: sum(r.status == s for r in self.results) for s in ("migrated", "current", "skipped", "failed")}
        lines.append("")
        lines.append(", ".join(f"{n} {s}" for s, n in counts.items() if n) or "no view files found")
        lines.append("written" if self.written else ("nothing written" + (": fix the failed files, or use --force" if self.failed else "")))
        return "\n".join(lines)


def _files(root: Path, pattern: str) -> list[Path]:
    return sorted(p for p in root.rglob(pattern) if not _SKIPPED & set(p.relative_to(root).parts))


def _header(text: str) -> str:
    """The comment block at the top of a file, with its blank lines."""
    lines: list[str] = []
    for line in text.splitlines():
        if line.strip() == "" or line.lstrip().startswith("#"):
            lines.append(line)
        else:
            break
    while lines and lines[-1].strip() == "":
        lines.pop()
    return "\n".join(lines) + "\n" if lines else ""


def _has_inner_comments(text: str) -> bool:
    """Whether the body of a file (after its header) has a `#` comment, not counting a `#` inside a quoted string (a colour)."""
    for line in text[len(_header(text)):].splitlines():
        if "#" in re.sub(r"(\"[^\"]*\"|'[^']*')", "", line):
            return True
    return False


def _is_old(data: Any) -> bool:
    return isinstance(data, dict) and any(k in data for k in _OLD_KEYS) and "widget" not in data


def _old_rules(data: dict[str, Any]) -> bool:
    rules = data.get("styles")
    return isinstance(rules, list) and any(isinstance(r, dict) and set(r) & {"kind", "id", "classes"} for r in rules)


def migrate_project(root: str | Path, *, write: bool = False, force: bool = False) -> Report:
    """Works out (and with `write=True`, writes) the migration of the project under `root`."""
    root = Path(root).resolve()
    report = Report()
    view_files = [p for p in _files(root, "*.yaml") if _VIEW.match(p.name)]
    sheet_files = _files(root, "*_Stylesheet.yaml")
    viewmodels = {p.name.removesuffix("_ViewModel.py"): p for p in _files(root, "*_ViewModel.py")}

    loaded: dict[Path, Any] = {}
    for path in view_files + sheet_files:
        try:
            loaded[path] = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            report.results.append(FileResult(path, "failed", error=f"invalid YAML: {str(exc).splitlines()[0]}"))
    params: dict[str, Any] = {}
    for path in view_files:
        data = loaded.get(path)
        if isinstance(data, dict):
            params.setdefault(_VIEW.match(path.name).group(1), data.get("params"))  # type: ignore[union-attr]

    translated: dict[Path, FileResult] = {}
    claimed: set[Path] = set()
    for path in view_files:
        if path not in loaded:
            continue
        data = loaded[path]
        stem, flavour = _VIEW.match(path.name).groups()  # type: ignore[union-attr]
        if not _is_old(data):
            current = isinstance(data, dict) and "widget" in data
            report.results.append(FileResult(path, "current" if current else "skipped", error=None if current else "not a view"))
            continue
        translator = Translator(params_of=params.get)
        new = translator.translate(data)
        if flavour == "View" and stem in viewmodels and isinstance(new, dict):
            new = {"name": stem, **new}
            translator.notes.append(f"named '{stem}', the bind key for {viewmodels[stem].name}")
        text = path.read_text(encoding="utf-8")
        result = FileResult(path, "migrated", path.with_name(f"{stem}_View.yaml"), _header(text) + to_yaml(new), translator.notes,
                            lost_comments=_has_inner_comments(text))
        assert result.new_path is not None
        if result.new_path != path and (result.new_path in claimed or result.new_path.exists()):
            result.status, result.error = "failed", f"{result.new_path.name} already exists"
        claimed.add(result.new_path)
        translated[path] = result
        report.results.append(result)

    for path in sheet_files:
        if path not in loaded:
            continue
        data = loaded[path]
        if not isinstance(data, dict) or is_rule_sheet(data) or not _old_rules(data):
            report.results.append(FileResult(path, "current" if is_rule_sheet(data) else "skipped"))
            continue
        stem = _SHEET.match(path.name).group(1)  # type: ignore[union-attr]
        own = stem if stem in params or (path.parent / f"{stem}_Component.yaml").exists() else None
        new, notes = translate_rules(data, own)
        text = path.read_text(encoding="utf-8")
        result = FileResult(path, "migrated", path, _header(text) + to_yaml(new), notes, lost_comments=_has_inner_comments(text))
        translated[path] = result
        report.results.append(result)

    _validate(translated, params)
    report.python = _python_hints(root, viewmodels, translated)
    if write and (not report.failed or force):
        for path, result in translated.items():
            if result.status != "migrated" or result.text is None or result.new_path is None:
                continue
            result.new_path.write_text(result.text, encoding="utf-8")
            if result.new_path != path:
                path.unlink()
        report.written = True
    return report


def _validate(translated: dict[Path, FileResult], params: dict[str, Any]) -> None:
    """Loads every translated file with the loader the app uses and marks the ones that do not load as failed."""
    decls: dict[str, WidgetDecl] = {}
    for stem, header in params.items():
        try:
            decls[stem] = decl_from_params(stem, header) if header is not None else WidgetDecl(stem, view=True, container=True)
        except ValueError:
            decls[stem] = WidgetDecl(stem, view=True, container=True)
    for path, result in translated.items():
        if result.status != "migrated" or result.text is None:
            continue
        try:
            if path.name.endswith("_Stylesheet.yaml"):
                RuleSheet.of(yaml.safe_load(result.text))
            else:
                parse_view(result.text, str(result.new_path), resolver=decls.get)
        except LoadError as exc:
            result.status, result.error = "failed", f"does not load yet: {exc.message}" + (f" ({exc.hint})" if exc.hint else "")


def _python_hints(root: Path, viewmodels: dict[str, Path], translated: dict[Path, FileResult]) -> list[str]:
    """What each ViewModel of a migrated view needs, since Python is not rewritten."""
    hints = []
    for result in translated.values():
        if result.new_path is None or not result.new_path.name.endswith("_View.yaml"):
            continue
        stem = result.new_path.name.removesuffix("_View.yaml")
        if result.status != "migrated" or stem not in viewmodels:
            continue
        vm = viewmodels[stem]
        steps = [f"add `views = \"{stem}\"` to the class"]
        if _OLD_INIT.search(vm.read_text(encoding="utf-8")):
            steps.append("let `__init__` take no `view` and call `super().__init__()`")
        steps.append(f"bind it with `app.bind(...)` and open the view with `app.open_view(\"{stem}\")`")
        try:
            shown = vm.relative_to(root)
        except ValueError:
            shown = vm
        hints.append(f"{shown.as_posix()}: " + "; ".join(steps))
    return sorted(hints)
