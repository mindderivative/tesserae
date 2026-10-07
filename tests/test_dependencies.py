"""Tesserae's dependency on `tre` is capped below `tre`'s next minor line.

Moving to a new `tre` line is a new Tesserae line, which the user starts:
the user (2026-09-30) made `tre` 0.5.0 and custom windowing Tesserae 0.3.0,
started by them, and `>=` alone would let pip (and CI) take a new line the
day it's released, as it took 0.4.4. On the 0.3 line `tre` is 0.5.x.
"""

import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _project():
    return tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]


def test_tre_is_the_0_5_line():
    engine = next(d for d in _project()["dependencies"] if d.startswith("tesserae-engine"))
    bounds = set(re.findall(r"(>=|<)\s*([\d.]+)", engine))
    assert (">=", "0.5.5") in bounds, f"{engine!r}: Tesserae 0.4.3.3 needs tre 0.5.5 (resizing without vsync stalls)"
    assert ("<", "0.6") in bounds, f"{engine!r}: a new tre line is a new Tesserae line, the user's to start"


def test_tesserae_is_0_4():
    assert _project()["version"].startswith("0.4.")
