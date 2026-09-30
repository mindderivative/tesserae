"""Tesserae's dependency on `tre` is capped below 0.5 (the user, 2026-09-30).

`tre` 0.5.0 brings custom windowing, and moving to it is Tesserae 0.3.0, a
milestone the user starts. Until then Tesserae is 0.2.x, and `>=` alone
would let pip (and CI) take 0.5.0 the day it's released, as it took 0.4.4.
"""

import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _project():
    return tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]


def test_tre_is_capped_below_0_5():
    engine = next(d for d in _project()["dependencies"] if d.startswith("tesserae-engine"))
    bounds = set(re.findall(r"(>=|<)\s*([\d.]+)", engine))
    assert ("<", "0.5") in bounds, f"{engine!r}: tre 0.5.0 is Tesserae 0.3.0's move, the user's to start"
    assert any(op == ">=" for op, _ in bounds)


def test_tesserae_is_0_2():
    assert _project()["version"].startswith("0.2.")
