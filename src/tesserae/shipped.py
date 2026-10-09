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

__all__ = ["SHIPPED", "ViewLibrary", "shipped_rules", "shipped_views"]

SHIPPED = Path(__file__).parent / "views"
_RULES: Optional[list[RuleSheet]] = None


def shipped_views() -> dict[str, Path]:
    """The shipped views by name."""
    return {p.name.removesuffix("_View.yaml"): p for p in sorted(SHIPPED.glob("*_View.yaml"))} if SHIPPED.is_dir() else {}


def shipped_rules() -> list[RuleSheet]:
    """The shipped stylesheets, the lowest layer of an app's rules."""
    global _RULES
    if _RULES is None:
        _RULES = [load_rule_sheet(p) for p in sorted(SHIPPED.glob("*_Stylesheet.yaml"))] if SHIPPED.is_dir() else []
    return _RULES


class ViewLibrary:
    """Finds a view by name among the project's (`project`, name to path) and the shipped ones; the project's wins."""

    def __init__(self, project: Optional[dict[str, Path]] = None) -> None:
        self.paths: dict[str, Path] = {**shipped_views(), **(project or {})}
        #: shipped views the project has replaced with its own: their shipped looks are not used either
        self.replaced: set[str] = set(shipped_views()) & set(project or {})
        self._docs: dict[Path, ViewDoc] = {}

    def decl(self, name: str) -> Optional[WidgetDecl]:
        """The declaration of the view `name`'s params, or `None` when there is no such view."""
        path = self.paths.get(name)
        if path is None:
            return None
        params = (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get("params")
        return decl_from_params(name, params) if params is not None else WidgetDecl(name, view=True, container=True)

    def doc(self, name: str) -> Optional[ViewDoc]:
        """The parsed view `name`, or `None`."""
        path = self.paths.get(name)
        if path is None:
            return None
        if path not in self._docs:
            self._docs[path] = parse_view(path.read_text(encoding="utf-8"), str(path), resolver=self.decl, view_name=name)
        return self._docs[path]

    def parse(self, path: Path, name: Optional[str] = None) -> ViewDoc:
        """Parses a view file that is not looked up by name (the one being opened), against this library."""
        return parse_view(path.read_text(encoding="utf-8"), str(path), resolver=self.decl, view_name=name or path.name.removesuffix("_View.yaml"))
