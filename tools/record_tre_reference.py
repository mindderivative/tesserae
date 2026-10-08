"""M43: records `tre`'s answers for the parity tests (`tests/reference.py`)
into `tests/reference/*.json`.

Run it on `tre` 0.3.4 -- the last release with the `View`, `Signal` and
window theme the answers come from -- whenever a parity test asks `tre`
something new:

    TRE_SOURCE_DIR=... .venv/bin/python tools/record_tre_reference.py

It runs the parity tests with `TESSERAE_RECORD_TRE=1`, which makes each
`reference.tre(fn)` call `fn` and keep its answer. The files are written
only if every test passes (a mismatch is never written in as `tre`'s
answer); each module's file is replaced whole.

The corpora a recording builds keep every question asked before, exactly
as it was asked (`reference.previous`), and add only what's new, so an
existing answer never changes: the tree corpus reuses each recorded
case's spec and frames, and the binding corpus each recorded expression.
Fragments and views `tre` 0.3.4 can't build are left out (`Tabs`, whose
divider is `width: "100%"`, which 0.3.4's `View` doesn't take).
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODULES = ["test_tree_parity", "test_spec_build", "test_tokens", "test_theme_object",
           "test_view", "test_clickable", "test_wide_gamut"]


def main() -> int:
    import tre

    missing = [name for name in ("View", "Signal") if not hasattr(tre, name)]
    if missing or not hasattr(tre.Window, "set_theme"):
        print(f"tre has no {', '.join(missing) or 'Window.set_theme'}: record in an environment with tre 0.3.4 "
              "(0.3.5 has no View, Signal or window theme to ask)", file=sys.stderr)
        return 2
    env = {**os.environ, "TESSERAE_RECORD_TRE": "1"}
    args = [sys.executable, "-m", "pytest", "-q", *(f"tests/{m}.py" for m in MODULES), *sys.argv[1:]]
    result = subprocess.run(args, cwd=ROOT, env=env)
    if result.returncode == 0:
        print(f"recorded tre's answers in {ROOT / 'tests/reference'}")
    else:
        print("a test failed, so nothing was written", file=sys.stderr)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
