"""Runs every generator's `--check` and lists the ones whose output is out of date with the code.

    python3 tools/docs_audit.py

Exits 1 if any generated page, schema or the component order differs from what the generator now writes. Fast: run it before the strict docs build.
"""

import subprocess
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
PY = str(ROOT / ".venv" / "bin" / "python")
GENERATORS = ["generate_api_docs", "generate_yaml_docs", "generate_component_docs", "generate_component_order", "generate_yaml_schema"]


def main():
    stale = []
    for name in GENERATORS:
        done = subprocess.run([PY, str(TOOLS / f"{name}.py"), "--check"], cwd=ROOT, capture_output=True, text=True)
        status = "ok" if done.returncode == 0 else "OUT OF DATE"
        print(f"{name}: {status}")
        if done.returncode:
            stale.append(name)
            print("   " + "\n   ".join((done.stdout + done.stderr).strip().splitlines()[-5:]))
    return int(bool(stale))


if __name__ == "__main__":
    sys.exit(main())
