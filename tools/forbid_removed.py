"""M43 Phase 4: runs a script with every name `tre` 0.3.5 removes made to
raise -- `tre`'s `TRE_FORBID_REMOVED` switch, from the copy vendored in
`tests/tre_removed.py` (the pinned 0.3.4 doesn't ship it):

    python tools/forbid_removed.py examples/counter/app.py

The script runs as `__main__`, with its own folder on `sys.path`, as
`python <script>` would run it.
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("usage: python tools/forbid_removed.py <script.py> [args...]")
    import tre

    if "tre._removed" not in sys.modules:  # a tre with its own switch installs it itself
        sys.path.insert(0, str(ROOT / "tests"))
        import tre_removed

        tre_removed.install()
    script = Path(sys.argv[1]).resolve()
    sys.argv = [str(script), *sys.argv[2:]]
    sys.path.insert(0, str(script.parent))
    runpy.run_path(str(script), run_name="__main__")


if __name__ == "__main__":
    main()
