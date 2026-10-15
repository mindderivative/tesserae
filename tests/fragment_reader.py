"""The old-syntax component fragments (`src/tesserae/spec/components/*_Component.yaml`), read for the sweeps in tests that still cover the
compatibility loader. (The docs generator now documents the shipped views; this is the part of its old reader that the tests used.)"""

from __future__ import annotations

import re
import textwrap
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
FRAGMENTS = ROOT / "src" / "tesserae" / "spec" / "components"

#: Example values for a fragment's parameters, to show what its stylesheet expands to.
SAMPLE = {"label": "Go", "title": "Title", "text": "Hello", "headline": "Headline", "width": 120, "height": 40,
          "corner_radius": 20, "size": 40, "icon": "home", "value": 0.5, "src": "photo.png", "fit": "cover",
          "placeholder": "Search", "day": 7, "hour": 3, "minute": 15, "background": "primary", "left_padding": 16,
          "item_width": 100, "scrim_width": 400, "scrim_height": 300, "frame": "frame", "min": 0, "max": 10, "step": 1,
          "typography_role": "body_large", "color": "primary", "fab_size": "default", "button": "ButtonFilled",
          "selected": False, "checked": False, "screen": "Main"}
ITEMS = {"ButtonGroup": [{"label": "A"}, {"label": "B"}], "Menu": [{"label": "A"}, {"label": "B"}],
         "Tabs": [{"label": "A", "selected": True}, {"label": "B"}],
         "NavigationRail": [{"label": "A", "icon": "home", "selected": True}, {"label": "B", "icon": "search"}],
         "NavigationRailScreens": [{"label": "A", "icon": "home", "screen": "A"}, {"label": "B", "icon": "search", "screen": "B"}],
         "NavigationDrawer": [{"label": "A", "icon": "home", "selected": True}, {"label": "B", "icon": "search"}]}




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


