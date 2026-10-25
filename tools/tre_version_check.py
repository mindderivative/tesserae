"""Compares the `tesserae-engine` pin in pyproject.toml with the installed version and the newest on PyPI.

    python3 tools/tre_version_check.py

Prints whether a newer release fits the pin, or falls outside it (a new tre line is a new Tesserae line). Needs network access. Exits 1 on a
release that fits the pin but is not the one installed.
"""

import json
import re
import sys
import urllib.request
from importlib import metadata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def key(v):
    return tuple(int(p) for p in re.findall(r"\d+", v)[:4])


def main():
    pin = re.search(r'"tesserae-engine([^"]*)"', (ROOT / "pyproject.toml").read_text(encoding="utf-8")).group(1)
    low = re.search(r">=([\d.]+)", pin).group(1)
    high = re.search(r"<([\d.]+)", pin).group(1)
    try:
        installed = metadata.version("tesserae-engine")
    except metadata.PackageNotFoundError:
        installed = "not installed"
    with urllib.request.urlopen("https://pypi.org/pypi/tesserae-engine/json", timeout=20) as r:
        releases = [v for v in json.load(r)["releases"] if re.fullmatch(r"[\d.]+", v)]
    fits = [v for v in releases if key(low) <= key(v) < key(high)]
    newest, newest_fit = max(releases, key=key), max(fits, key=key)
    print(f"pin {pin} | installed {installed} | newest in range {newest_fit} | newest overall {newest}")
    if key(newest) >= key(high):
        print(f"{newest} is outside the pin: a new Tesserae line.")
    return int(installed != newest_fit)


if __name__ == "__main__":
    sys.exit(main())
