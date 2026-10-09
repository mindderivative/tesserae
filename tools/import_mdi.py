#!/usr/bin/env python3
"""Adds Material Design Icons (Pictogrammers' MDI, Apache-2.0) to Tesserae's icon set from the Iconify JSON file (#216).

    python tools/import_mdi.py mdi.json [--names account,home-variant,...] [--all]

`mdi.json` is the Iconify `mdi` collection (`{"icons": {name: {"body": "<path d=.../>"}}, "aliases": {...}, "width": 24, "height": 24}`).
Only icons whose body is one `<path>` are used. Names become `snake_case` (`account-check` is `account_check`). With no `--names` a curated set of
the icons user interfaces need is written; `--all` writes every icon (about 2 MB). The paths go to `src/tesserae/icon_data/mdi.json`, in MDI's own
24 x 24 box, which `tesserae.icons` merges under the icons already built in.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "src" / "tesserae" / "icon_data" / "mdi.json"
_PATH = re.compile(r'^<path\b[^>]*?\sd="([^"]+)"[^>]*/>$')
#: The set written when no names are given: what the Material 3 components and ordinary user interfaces reach for.
CURATED = """
account account-circle account-outline alert alert-circle alert-outline arrow-collapse arrow-down arrow-expand arrow-left arrow-right arrow-up
bell bell-outline bookmark bookmark-outline calendar calendar-month camera cart cellphone check check-circle check-circle-outline chevron-double-left
chevron-double-right chevron-down chevron-left chevron-right chevron-up circle circle-outline clipboard clock clock-outline close close-circle cloud
cog cog-outline content-copy content-cut content-paste content-save delete delete-outline dock-window dots-horizontal dots-vertical download drag
drag-vertical email email-outline eye eye-off file file-document filter filter-variant flag folder folder-open format-align-center format-align-left
format-align-right format-bold format-italic format-list-bulleted format-list-numbered format-underline fullscreen fullscreen-exit gesture-tap heart
heart-outline help-circle help-circle-outline history home home-outline image information information-outline lightbulb link link-variant lock lock-open
login logout magnify map-marker menu menu-down menu-left menu-right menu-up microphone minus music-note open-in-new palette pause pencil phone pin
play plus plus-circle redo refresh repeat rewind send share share-variant shuffle skip-next skip-previous star star-outline stop swap-horizontal
swap-vertical sync tag text-box thumb-down thumb-up timer tune undo unfold-less-horizontal unfold-more-horizontal upload view-grid view-list
volume-high volume-low volume-medium volume-off wifi window-close window-maximize window-minimize window-restore
keyboard keyboard-outline calendar-edit calendar-today view-carousel file-tree folder-outline
""".split()
_NAME = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def collect(data: dict, names: list[str] | None) -> dict[str, str]:
    """`{snake_case name: path data}` for `names` (the curated set when `None`; everything for `["*"]`)."""
    if data.get("width") != 24 or data.get("height") != 24:
        raise ValueError(f"the collection is {data.get('width')} x {data.get('height')}, not MDI's 24 x 24")
    icons, aliases = data["icons"], data.get("aliases", {})
    wanted = list(icons) if names == ["*"] else (names or CURATED)
    out: dict[str, str] = {}
    missing = []
    for name in wanted:
        if not _NAME.match(name):
            raise ValueError(f"{name!r} is not an icon name (lower-case letters, digits and hyphens)")
        key = aliases[name]["parent"] if name not in icons and name in aliases else name
        entry = icons.get(key)
        if entry is None:
            missing.append(name)
            continue
        found = _PATH.match(entry["body"].replace("\n", "").strip())
        if not found:
            if names is None or names == ["*"]:
                continue  # more than one shape, or a colour: not an icon this set can tint
            raise ValueError(f"{name}: not a single <path> (this set tints one shape)")
        out[name.replace("-", "_")] = " ".join(found.group(1).split())
    if missing and names != ["*"]:
        raise ValueError(f"not in the collection: {', '.join(missing)}")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("source", type=Path)
    parser.add_argument("--names", help="only these icons, comma-separated (MDI names, with hyphens)")
    parser.add_argument("--all", action="store_true", help="every icon in the collection")
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args(argv)
    try:
        icons = collect(json.loads(args.source.read_text(encoding="utf-8")), ["*"] if args.all else args.names.split(",") if args.names else None)
    except (ValueError, KeyError, json.JSONDecodeError) as exc:
        print(exc, file=sys.stderr)
        return 1
    existing = json.loads(args.out.read_text(encoding="utf-8")) if args.out.exists() else {}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({**existing, **icons}, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"wrote {len(existing | icons)} icons to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
