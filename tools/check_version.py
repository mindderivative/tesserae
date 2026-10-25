#!/usr/bin/env python3
"""Check that every place the Tesserae version lives agrees, before a release.

The version is in `pyproject.toml` and is the newest heading of `docs/changelog.md`.

    python3 tools/check_version.py                    # all places agree
    python3 tools/check_version.py --expect 0.5.2     # ... and equal the release you are cutting
    python3 tools/check_version.py --pypi             # ... and PyPI does not have it yet (network)

PyPI never accepts the same version twice, so --pypi is the pre-flight for a publish. With --pypi
and no --expect, a version PyPI already has is an error (the usual state right after a release).
Exit status 1 on any problem.
"""
import argparse
import json
import re
import sys
import tomllib
import urllib.error
import urllib.request
from pathlib import Path

DIST = "tesserae-ui"


def found_versions(root):
    """Return ({label: version}, [problems]) for every place the version is kept."""
    found, problems = {}, []
    found["pyproject.toml"] = tomllib.loads((root / "pyproject.toml").read_text())["project"]["version"]
    heading = re.search(r"^## (\S+)", (root / "docs" / "changelog.md").read_text(), re.M)
    if heading:
        found["docs/changelog.md"] = heading[1]
    else:
        problems.append("docs/changelog.md has no `## <version>` heading")
    return found, problems


def on_pypi(version):
    url = f"https://pypi.org/pypi/{DIST}/json"
    try:
        with urllib.request.urlopen(url, timeout=15) as reply:
            return version in json.load(reply)["releases"]
    except urllib.error.HTTPError as err:
        if err.code == 404:
            return False
        raise


def check(root, expect=None, pypi=False, published=on_pypi):
    found, problems = found_versions(root)
    distinct = set(found.values())
    if len(distinct) > 1:
        problems.append("versions disagree: " + ", ".join(f"{k}={v}" for k, v in found.items()))
    version = next(iter(distinct)) if len(distinct) == 1 else None
    if version and not re.fullmatch(r"\d+\.\d+\.\d+(\.\d+)?", version):
        problems.append(f"{version!r} is not a plain x.y.z[.w] version")
    if expect and version != expect:
        problems.append(f"expected {expect}, the files say {version}")
    if pypi and version and published(expect or version):
        problems.append(f"{DIST} {expect or version} is already on PyPI (it never accepts a version twice)")
    return version, problems


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--expect")
    parser.add_argument("--pypi", action="store_true")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    args = parser.parse_args(argv)
    version, problems = check(args.root, args.expect, args.pypi)
    for problem in problems:
        print("problem:", problem)
    if not problems:
        print(f"ok: {version} everywhere" + (" and free on PyPI" if args.pypi else ""))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
