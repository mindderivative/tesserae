#!/usr/bin/env python3
"""Which tests cover the files I touched? Prints the pytest command; runs nothing unless `--run`.

    python3 -I tools/tests_for.py                    # uncommitted changes (staged, unstaged, new files)
    python3 -I tools/tests_for.py --base HEAD~3      # also what was committed since that ref
    python3 -I tools/tests_for.py src/tesserae/binding.py tests/test_build.py
    python3 -I tools/tests_for.py --list --include-core --base origin/main   # what CI runs: paths only, core importers included
    python3 -I tools/tests_for.py --run              # run the picked tests with the repo's .venv (pytest -q -x)

The full suite takes about three minutes and is run only when the user calls for it (`tools/check.py --full`); this picks the tests that cover a change so a step takes seconds:

  * a changed test file is itself the test;
  * a changed `src/tesserae/**.py` module gives the tests that import it (read with `ast`: `import a.b`, `from a import b`,
    `from a.b import c`), and the tests whose file name matches the module's (`widgets/buttons.py` -> `test_button*.py`);
  * the tests that mention a public function, class or constant the module defines (compound names only, and not ones found in over a tenth of the tests);
  * a changed view or component file (`views/Button_View.yaml`, `spec/components/*.yaml`) gives the tests whose name matches its stem
    or that mention the file name;
  * a changed page under `docs/` gives the tests that read the docs (`DOC_TESTS`: the generated pages, the examples in them, no version history, the
    tutorials, the schemas);
  * a changed example (`examples/<name>/...`) gives the tests that mention the example by folder (`examples/<name>`, or `"<name>"` in a test that
    mentions `examples`): the run-every-example test, the tutorials' and the example's own;
  * a changed `tools/*.py` gives the tests that mention the script's name.

It is a name and import match, not coverage data, so it misses a test that reaches the code only through another module. A module that
more than a third of the tests import (`tesserae` itself, `spec.build`...) is a core module: only its name matches are listed and the
output says to run the full check. Read the "why" column before trusting a pick.
"""

import argparse
import ast
import fnmatch
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORE_SHARE = 1 / 3
#: The tests that read the documentation or files generated for it: a change under `docs/` picks them (CI's docs job runs the same).
DOC_TESTS = ("test_*docs*.py", "test_tutorials_current.py", "test_*schema.py", "test_component_order.py", "test_component_docs.py")


def git(*args):
    done = subprocess.run(["git", *args], capture_output=True, text=True, cwd=ROOT)
    return done.stdout.splitlines() if done.returncode == 0 else []


def relative(name):
    """A path as the repository names it: the hooks pass absolute ones."""
    path = Path(name)
    return path.resolve().relative_to(ROOT).as_posix() if path.is_absolute() and path.resolve().is_relative_to(ROOT) else name


def changed_files(base):
    files = set(git("diff", "--name-only", "HEAD")) | set(git("ls-files", "--others", "--exclude-standard"))
    if base:
        files |= set(git("diff", "--name-only", f"{base}...HEAD")) | set(git("diff", "--name-only", base, "HEAD"))
    return sorted(f for f in files if (ROOT / f).exists())


def norm(stem):
    """`Button_View` -> `button`; `buttons` -> `button`; `test_button_group` -> `buttongroup`."""
    stem = re.sub(r"(?i)_(view|stylesheet|theme)$", "", stem).removeprefix("test_")
    stem = stem.lower().replace("_", "")
    return stem[:-1] if stem.endswith("s") and len(stem) > 3 else stem


def module_name(path):
    parts = Path(path).relative_to("src").with_suffix("").parts
    return ".".join(parts[:-1] if parts[-1] == "__init__" else parts)


def imports_of(text):
    found = set()
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return found
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            found.add(node.module)
            found.update(f"{node.module}.{a.name}" for a in node.names)
    return found


def public_names(path):
    """The module's `__all__`, or its top-level public def/class/assignment names, keeping only compound names (`parse_binding`,
    `GradientRing`): a single plain word (`Handle`, `evaluate`) matches too many tests by accident."""
    try:
        tree = ast.parse((ROOT / path).read_text(encoding="utf-8"))
    except (SyntaxError, OSError):
        return []
    names, exported = [], None
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.append(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__" and isinstance(node.value, (ast.List, ast.Tuple)):
                    exported = [e.value for e in node.value.elts if isinstance(e, ast.Constant) and isinstance(e.value, str)]
                elif isinstance(target, ast.Name):
                    names.append(target.id)
    compound = lambda n: not n.startswith("_") and ("_" in n.strip("_") or re.search(r"[a-z][A-Z]", n))  # noqa: E731
    return [n for n in (exported if exported is not None else names) if compound(n)]


def load_tests():
    tests = {}
    for path in sorted((ROOT / "tests").rglob("test_*.py")):
        text = path.read_text(encoding="utf-8", errors="replace")
        tests[path.relative_to(ROOT).as_posix()] = (text, imports_of(text))  # git and pytest say `tests/x.py` on every platform
    return tests


def pick(files, tests, include_core=False):
    """Return ({test: [reasons]}, [notes]). `include_core` keeps the tests that import a core module: for CI, where a change to one affects them all."""
    picks = defaultdict(list)  # test -> [reasons]
    notes = []

    def add(test, why):
        if why not in picks[test]:
            picks[test].append(why)

    for f in files:
        path = Path(f)
        if f.startswith("tests/") and path.name.startswith("test_") and f in tests:
            add(f, f"changed: {f}")
        elif f.startswith("tests/") and path.suffix == ".py":
            users = [t for t, (text, _) in tests.items() if re.search(rf"\b{re.escape(path.stem)}\b", text)]
            for t in users:
                add(t, f"uses the changed test helper {f}")
        elif f.startswith("src/") and path.suffix == ".py":
            module = module_name(f)
            direct = [t for t, (_, imps) in tests.items() if module in imps]
            named = [t for t in tests if norm(path.stem) and norm(path.stem) in norm(Path(t).stem)]
            if len(direct) > CORE_SHARE * len(tests) and not include_core:
                notes.append(f"{f} is a core module ({len(direct)} of {len(tests)} tests import {module}): hand-pick the tests that mention what you changed (grep -l); the full suite only if asked")
                direct = []
            for t in direct:
                add(t, f"imports {module}")
            for t in named:
                add(t, f"name matches {path.name}")
            by_name = []
            for name in public_names(f):
                users = [t for t, (text, _) in tests.items() if re.search(rf"\b{re.escape(name)}\b", text)]
                if 0 < len(users) <= 0.1 * len(tests):
                    by_name += [(t, name) for t in users]
            for t, name in by_name[:12]:
                add(t, f"mentions {name}")
            if not direct and not named and not by_name and not any("core module" in n for n in notes if f in n):
                notes.append(f"{f}: no test imports {module} or matches its name; look for one by hand")
        elif f.startswith("src/") and path.suffix in (".yaml", ".yml"):
            key = norm(path.stem)
            for t, (text, _) in tests.items():
                if path.name in text:
                    add(t, f"mentions {path.name}")
                elif key and key in norm(Path(t).stem):
                    add(t, f"name matches {path.name}")
            if not any(path.name in " ".join(r) for r in picks.values()):
                notes.append(f"{f}: no test names or mentions it; look for one by hand (tests/test_shipped*.py)")
        elif f.startswith("examples/") and len(path.parts) > 2:
            name = path.parts[1]
            for t, (text, _) in tests.items():
                if f"examples/{name}" in text or ("examples" in text and re.search(rf"""["']{re.escape(name)}["']""", text)):
                    add(t, f"mentions the example {name}")
            if not any(f"example {name}" in " ".join(r) for r in picks.values()):
                notes.append(f"{f}: no test names the example {name}; run it by hand: python examples/{name}/app.py")
        elif f.startswith("tools/") and path.suffix == ".py":
            for t, (text, _) in tests.items():
                if re.search(rf"\b{re.escape(path.stem)}\b", text):
                    add(t, f"mentions {path.stem}")
        elif f.startswith("docs/") or f.endswith(".md"):
            if f.startswith("docs/"):
                for pattern in DOC_TESTS:
                    for t in sorted(tests):
                        if fnmatch.fnmatch(Path(t).name, pattern):
                            add(t, f"reads the docs: {f}")
            notes.append(f"{f}: documentation; also run tools/docs_audit.py and tools/check.py --docs")
    return picks, notes


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("files", nargs="*", help="files to look up (default: what git says changed)")
    parser.add_argument("--base", help="a ref: also count what was committed since it")
    parser.add_argument("--include-core", action="store_true", help="also pick every test that imports a core module (what CI does)")
    parser.add_argument("--list", action="store_true", help="print only the picked test paths, one per line")
    parser.add_argument("--run", action="store_true", help="run the picked tests with .venv/bin/python -m pytest -q -x")
    args = parser.parse_args(argv)

    files = [relative(f) for f in args.files] or changed_files(args.base)
    if not files:
        print("nothing changed (the tree is clean). Pass files, or --base REF to include committed work.")
        return 0
    tests = load_tests()
    picks, notes = pick(files, tests, args.include_core)
    if args.list:
        print("\n".join(sorted(picks)))
        return 0
    print(f"changed: {', '.join(files[:8])}{' ...' if len(files) > 8 else ''}")
    for t in sorted(picks):
        print(f"  {t}  <- {'; '.join(picks[t][:2])}")
    for note in notes:
        print(f"  note: {note}")
    if not picks:
        print("no test picked.")
        return 0
    command = [".venv/bin/python" if (ROOT / ".venv" / "bin" / "python").exists() else sys.executable, "-m", "pytest", "-q", "-x", *sorted(picks)]
    print(f"\n{len(picks)} test file(s):\n  " + " ".join(command), flush=True)
    if args.run:
        return subprocess.run(command, cwd=ROOT).returncode
    return 0


if __name__ == "__main__":
    sys.exit(main())
