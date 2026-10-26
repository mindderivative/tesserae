"""Tesserae's dependency on `tre` is one exact release (it was a range below `tre`'s next minor line until 0.5.8).

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


def test_tre_is_pinned_to_the_release_the_suite_was_run_on():
    """`tre` 0.5.8 (published the day the user pinned it) changed hit testing and broke four tests in CI, which had taken it because the range allowed it."""
    engine = next(d for d in _project()["dependencies"] if d.startswith("tesserae-engine"))
    found = re.fullmatch(r"tesserae-engine==(0\.5\.(\d+))", engine)
    assert found, f"{engine!r}: pin one exact tre release (==0.5.x); a new one is tried by the user first, then this moves"
    assert int(found[2]) >= 8, f"{engine!r}: Tesserae needs tre 0.5.8 (a press hit-tests a rounded shape; calc, insets and anchored layout came in 0.5.7)"


def test_tesserae_is_0_5():
    assert _project()["version"].startswith("0.5.")
