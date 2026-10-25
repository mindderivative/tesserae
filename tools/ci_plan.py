#!/usr/bin/env python3
"""Decides what CI runs for a push, a pull request or a manual run: `docs`, `partial` or `full`.

    python3 -I tools/ci_plan.py --base SHA [--head SHA]      # what CI does; env vars below
    python3 -I tools/ci_plan.py --base origin/main           # try it locally on your own commits

The mode, first rule that matches:

  full     called for: a manual run with mode `full`, a pull request labelled `full-test`, or `[full-ci]` in the head commit's message or the
           pull request's title; or the release series moves up (the first three parts of the version in pyproject.toml change: 0.5.1.x -> 0.5.2).
  docs     every changed file is documentation (see `is_doc`): the docs checks and the tests that read the docs, and nothing else.
  partial  everything else: the tests `tools/tests_for.py` picks for the change, with the tests that import a core module included (a change to
           one affects them). If nothing is picked, a few smoke tests run, so a change to a file no test names is not unchecked.

The docs checks (`tools/docs_audit.py`, `mkdocs build --strict`, the doc tests) run in every mode; the platform jobs (a clean install, a built
executable) run in `full`, and in `partial` when a packaging file changed.

Environment, set by the workflow: EVENT_NAME, DISPATCH_MODE (auto, docs, partial or full), LABELS (a JSON list), MESSAGE (the head commit's message
and a pull request's title). Writes `mode`, `reason`, `tests`, `doc_tests`, `packaging` to $GITHUB_OUTPUT when it is set, and prints them.
"""

import argparse
import fnmatch
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

DOC_DIRS = ("docs/", "design/", ".agents/", "spike-results/")
DOC_FILES = ("mkdocs.yml", "AGENTS.md", "CLAUDE.md")
#: The tests that read the documentation or files generated for it.
DOC_TESTS = ("test_*docs*.py", "test_tutorials_current.py", "test_*schema.py", "test_component_order.py", "test_component_docs.py")
#: Run when no test covers a change. `test_examples_run.py` runs six example apps end to end, so it is the cross-platform smoke test of the whole.
SMOKE = ("tests/test_app.py", "tests/test_build.py", "tests/test_composed.py", "tests/test_pixels.py", "tests/test_examples_run.py")
PACKAGING = ("tools/clean_install_smoke.py", "src/tesserae/templates/*", "src/tesserae/cli.py", "src/tesserae/build.py",
             ".github/workflows/ci.yml")
OUTPUTS = ("mode", "reason", "tests", "doc_tests", "packaging")  # what `plan` declares in .github/workflows/ci.yml
FULL_MARKS = ("[full-ci]", "[full ci]", "[full test]")


def is_doc(path):
    """Documentation: the docs and design pages, notes for agents and skills, the root `*.md` files and the MkDocs config."""
    return path.startswith(DOC_DIRS) or path in DOC_FILES or ("/" not in path and path.endswith(".md"))


def series(version):
    """The release series: the first three numeric parts of a version (`0.5.1.2` -> `0.5.1`)."""
    return ".".join(re.findall(r"\d+", version)[:3])


def decide(files, *, dispatch="auto", labels=(), message="", base_version=None, head_version=None):
    """Return (mode, reason) for the changed `files` and the trigger."""
    if dispatch in ("full", "docs", "partial"):
        return dispatch, f"asked for by hand: mode {dispatch}"
    if "full-test" in labels:
        return "full", "the pull request has the `full-test` label"
    mark = next((m for m in FULL_MARKS if m in message.lower()), None)
    if mark:
        return "full", f"{mark} is in the commit message or the pull request's title"
    if base_version and head_version and series(base_version) != series(head_version):
        return "full", f"the release series moved up: {series(base_version)} -> {series(head_version)} (version {base_version} -> {head_version})"
    if files and all(is_doc(f) for f in files):
        return "docs", f"only documentation changed ({len(files)} file(s))"
    return "partial", f"{len(files)} file(s) changed; tests picked by what they cover"


def doc_tests():
    found = {str(p.relative_to(ROOT)) for pattern in DOC_TESTS for p in (ROOT / "tests").glob(pattern)}
    return sorted(found)


def partial_tests(files):
    import tests_for

    picks, _notes = tests_for.pick(files, tests_for.load_tests(), include_core=True)
    chosen = sorted(picks) or [t for t in SMOKE if (ROOT / t).exists()]
    return chosen, not picks


def git(*args):
    done = subprocess.run(["git", *args], capture_output=True, text=True, cwd=ROOT)
    return done.stdout if done.returncode == 0 else ""


def version_at(ref):
    text = git("show", f"{ref}:pyproject.toml") if ref else (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    found = re.search(r'(?m)^version\s*=\s*"([^"]+)"', text)
    return found[1] if found else None


def packaging_changed(files, base, head):
    """A packaging file changed. `pyproject.toml` counts only for a line other than `version =`: every release step bumps that."""
    if any(fnmatch.fnmatch(f, p) for f in files for p in PACKAGING):
        return True
    if "pyproject.toml" not in files:
        return False
    diff = git("diff", "-U0", f"{base}...{head}", "--", "pyproject.toml").splitlines()
    return any(line[:1] in "+-" and not line.startswith(("+++", "---")) and not re.match(r"[+-]version\s*=", line) for line in diff)


def changed(base, head):
    zero = not base or set(base) == {"0"}
    if zero:  # a new branch: against the trunk
        base = git("merge-base", "origin/main", head).strip() or f"{head}~1"
    return [f for f in git("diff", "--name-only", f"{base}...{head}").splitlines() if f], base


def emit(values):
    assert set(values) == set(OUTPUTS), f"ci.yml declares {OUTPUTS}"
    lines = [f"{k}={v}" for k, v in values.items()]
    print("\n".join(lines))
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as handle:
            handle.write("\n".join(lines) + "\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base", default="", help="the commit before the change (a push's `before`, a pull request's base)")
    parser.add_argument("--head", default="HEAD")
    args = parser.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")

    files, base = changed(args.base, args.head)
    mode, reason = decide(
        files, dispatch=os.environ.get("DISPATCH_MODE", "auto") or "auto", labels=json.loads(os.environ.get("LABELS") or "[]") or [],
        message=os.environ.get("MESSAGE", ""), base_version=version_at(base), head_version=version_at(None) if args.head == "HEAD" else version_at(args.head))
    tests, fallback = partial_tests(files) if mode == "partial" else ([], False)
    if fallback:
        reason += "; no test covers these files, so only the smoke tests run"
    packaging = mode == "full" or packaging_changed(files, base, args.head)
    emit({"mode": mode, "reason": reason, "tests": " ".join(tests), "doc_tests": " ".join(doc_tests()), "packaging": str(packaging).lower()})
    print(f"::notice title=CI mode: {mode}::{reason}" if os.environ.get("GITHUB_ACTIONS") else f"(changed: {', '.join(files[:6])}{' ...' if len(files) > 6 else ''})",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
