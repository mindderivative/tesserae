"""Remembering the window between runs: its size, where it was (where the platform lets an app say) and whether it was maximized.

A window view that says `remember: true` (or `remember: notes`, a name of its own) is put back as it was left. The state is a small JSON file in the
user's config directory, named for the key; `TESSERAE_STATE_DIR` puts it somewhere else (tests do).
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

__all__ = ["load", "save", "slug", "state_dir"]


def state_dir() -> Path:
    """Where the files go: `TESSERAE_STATE_DIR`, else the platform's per-user config directory."""
    override = os.environ.get("TESSERAE_STATE_DIR")
    if override:
        return Path(override)
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return base / "tesserae"


def slug(text: str) -> str:
    """A file-name-safe key from a title or a name."""
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "app"


def _path(key: str) -> Path:
    return state_dir() / f"{slug(key)}.window.json"


def _number(value: Any, low: float, high: float) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not low <= value <= high:
        return None
    return float(value)


def load(key: str) -> dict[str, Any]:
    """What was saved for `key`, checked field by field (a file that is missing, damaged or hand-edited gives less, never an error)."""
    try:
        data = json.loads(_path(key).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if not isinstance(data, dict):
        return {}
    out: dict[str, Any] = {}
    width, height = _number(data.get("width"), 100, 20000), _number(data.get("height"), 60, 20000)
    if width is not None and height is not None:
        out["width"], out["height"] = width, height
    x, y = _number(data.get("x"), -20000, 20000), _number(data.get("y"), -20000, 20000)
    if x is not None and y is not None:
        out["x"], out["y"] = x, y
    if isinstance(data.get("maximized"), bool):
        out["maximized"] = data["maximized"]
    return out


def save(key: str, state: dict[str, Any]) -> bool:
    """Writes `state` for `key`; False when the directory cannot be written (an app that cannot remember still runs)."""
    path = _path(key)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(state), encoding="utf-8")
        tmp.replace(path)
    except OSError:
        return False
    return True
