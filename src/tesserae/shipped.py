"""Views Tesserae ships, and how a project's views and the shipped ones are found together (spec section 4, step 4).

`tesserae/views/` holds the components Tesserae provides in the view language: `<Name>_View.yaml` and, beside it, `<Name>_Stylesheet.yaml` with
the look as rules. A project's own view of the same name wins, so a component can be replaced by writing a file with its name.

`ViewLibrary` is the one lookup an app uses: it knows the project's views and the shipped ones, parses a view when first called and keeps it,
and hands the composer both the declaration of a view's params (for checking a call) and its parsed document.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml

from tesserae.spec.nodes import ViewDoc, parse_view
from tesserae.spec.rules import RuleSheet, load_rule_sheet
from tesserae.spec.widgets import WidgetDecl, decl_from_params

__all__ = ["SHIPPED", "ViewLibrary", "shipped_rules", "shipped_sheet", "shipped_views"]

SHIPPED = Path(__file__).parent / "views"
_RULES: Optional[list[RuleSheet]] = None
_SHEETS: dict[str, Optional[RuleSheet]] = {}


def shipped_views() -> dict[str, Path]:
    """The shipped views by name."""
    return {p.name.removesuffix("_View.yaml"): p for p in sorted(SHIPPED.glob("*_View.yaml"))} if SHIPPED.is_dir() else {}


def shipped_sheet(name: str) -> Optional[RuleSheet]:
    """The shipped stylesheet of the widget or view `name` (`<name>_Stylesheet.yaml`), read the first time it is asked for, or `None` when it has none.
    An app reads only the ones for the widgets it uses."""
    if name not in _SHEETS:
        path = SHIPPED / f"{name}_Stylesheet.yaml"
        _SHEETS[name] = load_rule_sheet(path) if path.is_file() else None
    return _SHEETS[name]


def shipped_rules() -> list[RuleSheet]:
    """Every shipped stylesheet (not what an app uses: that is `shipped_sheet` for the widgets it has; this is for a tool that wants them all)."""
    global _RULES
    if _RULES is None:
        _RULES = [load_rule_sheet(p) for p in sorted(SHIPPED.glob("*_Stylesheet.yaml"))] if SHIPPED.is_dir() else []
    return _RULES


class ViewLibrary:
    """Finds a view by name among the project's (`project`, name to path) and the shipped ones; the project's wins."""

    def __init__(self, project: Optional[dict[str, Path]] = None, sheets: Optional[dict[str, Path]] = None) -> None:
        self.paths: dict[str, Path] = {**shipped_views(), **(project or {})}
        #: the project's own views, and its stylesheets by name (`Styles/Name_Stylesheet.yaml`): a view's stylesheet may also sit beside its view
        self.project_views: dict[str, Path] = dict(project or {})
        self.project_sheets: dict[str, Path] = dict(sheets or {})
        #: shipped views the project has replaced with its own: their shipped looks are not used either
        self.replaced: set[str] = set(shipped_views()) & set(project or {})
        self._docs: dict[Path, ViewDoc] = {}
        #: every view file read through this library (the one opened, and each view it calls), for a hot reload to watch
        self.read: set[Path] = set()

    def decl(self, name: str) -> Optional[WidgetDecl]:
        """The declaration of the view `name`'s params, or `None` when there is no such view."""
        path = self.paths.get(name)
        if path is None:
            return None
        self.read.add(path.resolve())
        params = (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get("params")
        return decl_from_params(name, params) if params is not None else WidgetDecl(name, view=True, container=True)

    def doc(self, name: str) -> Optional[ViewDoc]:
        """The parsed view `name`, or `None`."""
        path = self.paths.get(name)
        if path is None:
            return None
        if path not in self._docs:
            self.read.add(path.resolve())
            self._docs[path] = parse_view(path.read_text(encoding="utf-8"), str(path), resolver=self.decl, view_name=name)
        return self._docs[path]

    def parse(self, path: Path, name: Optional[str] = None) -> ViewDoc:
        """Parses a view file that is not looked up by name (the one being opened), against this library."""
        self.read.add(path.resolve())
        return parse_view(path.read_text(encoding="utf-8"), str(path), resolver=self.decl, view_name=name or path.name.removesuffix("_View.yaml"))

    def used(self, doc: ViewDoc) -> set[str]:
        """The names of the widgets `doc` uses: its own nodes' and, through every view it calls (and those call), theirs. A view's stylesheet belongs to
        the application only when its name is here."""
        names: set[str] = set()
        pending = [doc]
        while pending:
            for node in pending.pop().root.walk():
                if node.widget not in names:
                    names.add(node.widget)
                    if node.widget in self.paths:
                        pending.append(self.doc(node.widget))
        return names

    def project_sheet(self, name: str) -> Optional[Path]:
        """The project's stylesheet for the widget or view `name`: `<name>_Stylesheet.yaml` beside the project's `<name>_View.yaml`, else the one of that
        name in the project's stylesheet folders; `None` when there is none."""
        beside = self.project_views.get(name)
        if beside is not None and beside.with_name(f"{name}_Stylesheet.yaml").is_file():
            return beside.with_name(f"{name}_Stylesheet.yaml")
        return self.project_sheets.get(name)

    def sheets_of(self, used: set[str], app_sheet: Optional[Path] = None) -> tuple[list[RuleSheet], list[Path]]:
        """`(rules, files)`: the stylesheets of the widgets in `used`, lowest layer first (the shipped ones, then the project's), and the project files they
        came from. A widget the project has replaced with a view of its own has not its shipped look; `app_sheet` (the app's own stylesheet) is not read
        twice when it is also named like a view's."""
        rules: list[RuleSheet] = []
        files: list[Path] = []
        for name in sorted(used):
            sheet = shipped_sheet(name) if name not in self.replaced else None
            if sheet is not None:
                rules.append(sheet)
        for name in sorted(used):
            path = self.project_sheet(name)
            if path is None or (app_sheet is not None and path.resolve() == app_sheet.resolve()):
                continue
            rules.append(load_rule_sheet(path))
            files.append(path.resolve())
        return rules, files
