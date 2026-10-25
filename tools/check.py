"""The check before work is called done, as a summary of what failed: no new type errors, then the docs build with warnings as errors.

    python3 tools/check.py          # types, then docs (about a minute); NO tests
    python3 tools/check.py --docs   # the docs build only
    python3 tools/check.py --full   # also the whole test suite (about three minutes): only when the user calls for a full test

The standing rule is to run only the tests that cover a change (`python3 -I tools/tests_for.py --run`); CI runs the rest. `--full` is for when the
user asks for it. The type check is `tools/mypy_ratchet.py`: the old errors are a baseline and only a new one fails.

Exits 1 on any failure. `tools/fullcheck.sh` is the same as `--full` with the raw tails.
"""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
def venv_python(root):
    """The checkout's own `.venv` Python when there is one, else the Python running this (CI installs into the runner's, with no `.venv`)."""
    venv = root / ".venv" / "bin" / "python"
    return str(venv) if venv.exists() else sys.executable


PY = venv_python(ROOT)


def run(*args):
    return subprocess.run([PY, *args], cwd=ROOT, capture_output=True, text=True)


def main(argv):
    failed = False
    if "--docs" not in argv:
        types = subprocess.run([sys.executable, "-I", str(ROOT / "tools" / "mypy_ratchet.py")], cwd=ROOT, capture_output=True, text=True)
        print("types: " + (types.stdout.strip().splitlines() or ["no output"])[0] if types.returncode == 0 else "types: " + types.stdout.strip())
        failed |= types.returncode != 0
    if "--full" in argv:
        done = run("-m", "pytest", "-q", "-rfE", "--no-header", "-p", "no:cacheprovider")
        lines = done.stdout.splitlines()
        bad = [line for line in lines if re.match(r"(FAILED|ERROR) ", line)]
        print(lines[-1] if lines else done.stderr.strip())
        for line in bad:
            print("  ", line)
        failed |= done.returncode != 0
    done = run("-m", "mkdocs", "build", "--strict")
    problems = [line for line in (done.stdout + done.stderr).splitlines() if re.match(r"(WARNING|ERROR)", line)]
    print("docs: " + ("ok" if done.returncode == 0 else f"{len(problems)} problem(s)"))
    for line in problems[:20]:
        print("  ", line)
    return int(failed or done.returncode != 0)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
