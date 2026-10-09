#!/usr/bin/env python3
"""Adds Material Symbols to Tesserae's icon set from a folder of their SVG files (#216).

    python tools/import_material_symbols.py DIR [--names home,search,...]

Each `DIR/<name>.svg` (or `<name>_24px.svg`, `<name>_wght400.svg`) is one icon in Google's 960-unit view box (`0 -960 960 960`) with a single
`<path d="...">`; the file name is the icon's name. The paths are written to `src/tesserae/icon_data/material_symbols.json`, which
`tesserae.icons` merges under the icons already built in. Material Symbols is Apache-2.0: get the files from github.com/google/material-design-icons
(`symbols/web/<name>/materialsymbolsoutlined/<name>_24px.svg`). Names already built in are kept as they are.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "src" / "tesserae" / "icon_data" / "material_symbols.json"
VIEW_BOX = "0 -960 960 960"
_NAME = re.compile(r"^[a-z][a-z0-9_]*$")
_SUFFIX = re.compile(r"(_\d+px|_wght\d+|_fill\d|_grad-?\d+)+$")
_PATHS = re.compile(r"<path\b[^>]*?\sd=\"([^\"]+)\"", re.S)
_VIEW_BOX = re.compile(r"viewBox=\"([^\"]+)\"")


def read(path: Path) -> tuple[str, str]:
    """`(name, path data)` of one SVG file, or a `ValueError` saying what is wrong with it."""
    name = _SUFFIX.sub("", path.stem)
    if not _NAME.match(name):
        raise ValueError(f"{path.name}: an icon name is lower-case letters, digits and underscores, not {name!r}")
    text = path.read_text(encoding="utf-8")
    box = _VIEW_BOX.search(text)
    if not box or box.group(1).split() != VIEW_BOX.split():
        raise ValueError(f"{path.name}: the view box is {box.group(1) if box else 'missing'}, not {VIEW_BOX}")
    paths = _PATHS.findall(text)
    if len(paths) != 1:
        raise ValueError(f"{path.name}: expected one <path>, found {len(paths)}")
    return name, " ".join(paths[0].split())


def collect(folder: Path, names: set[str] | None = None) -> dict[str, str]:
    icons: dict[str, str] = {}
    for path in sorted(folder.glob("*.svg")):
        name = _SUFFIX.sub("", path.stem)
        if names is not None and name not in names:
            continue
        name, data = read(path)
        icons[name] = data
    missing = sorted((names or set()) - set(icons))
    if missing:
        raise ValueError(f"no SVG file for: {', '.join(missing)}")
    return icons


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("folder", type=Path)
    parser.add_argument("--names", help="only these icons, comma-separated")
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args(argv)
    try:
        icons = collect(args.folder, set(args.names.split(",")) if args.names else None)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 1
    existing = json.loads(args.out.read_text(encoding="utf-8")) if args.out.exists() else {}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({**existing, **icons}, indent=0, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {len(existing | icons)} icons to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
