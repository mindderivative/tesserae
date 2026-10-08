#!/usr/bin/env python3
"""#106 phase 1 spike (0.5.0): what a real tre panel drag reports, and whether Tesserae can find the split half under the pointer.

Question: while the user drags a dock tab in a real window, do the window root's `pointer_move` events keep arriving with
`window_x`/`window_y` (they do under `simulate`)? If so, Tesserae can hit-test a DockPanel split's halves itself from the last
position before `dock_drop`, and tre needs no change. `dock_target`/`dock_drop` carry only the zone and the panel.

Run it at the machine, with a person dragging:

    .venv/bin/python tools/spikes/drag_events.py [--out DIR]
    .venv/bin/python tools/spikes/drag_events.py --dry     # builds the window, prints the halves' rectangles, no window

Drag the tabs (Files, Outline, Notes, Properties, Console) onto: the Source half's left edge, its middle, its right edge; the
Preview half's edges and middle; another zone; and release outside every zone once. Press `q` (window focused) to end; closing the
window ends it too. The summary says, for each drop, which zone tre reported, the last pointer position, and which half and band
(edge or middle) that position is in. Results go to `--out` (default `spike-results/`) as JSON and text.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "src"))

HALVES = ("source", "preview")
EDGE = 0.25  # the outer quarter of a half's side is its edge band


def absolute_rect(node):
    """(x, y, width, height) of `node` in the window (tre's `layout_x`/`layout_y` are already window coordinates)."""
    return node.get("layout_x"), node.get("layout_y"), node.get("layout_width"), node.get("layout_height")


def band_of(rect, x, y):
    """Which part of `rect` the point is in: `left`, `right`, `top`, `bottom` (an edge band) or `middle`; `None` outside."""
    rx, ry, rw, rh = rect
    if not (rx <= x <= rx + rw and ry <= y <= ry + rh):
        return None
    fx, fy = (x - rx) / rw, (y - ry) / rh
    for name, inside in (("left", fx < EDGE), ("right", fx > 1 - EDGE), ("top", fy < EDGE), ("bottom", fy > 1 - EDGE)):
        if inside:
            return name
    return "middle"


def where(view, x, y):
    for half in HALVES:
        band = band_of(absolute_rect(view.node(half)), x, y)
        if band is not None:
            return half, band
    return None, None


def build():
    from tesserae import App

    app = App(title="Drag spike", theme_seed=(0x67, 0x50, 0xA4, 0xFF))
    view, _ = app.load(HERE / "SplitDrag_View.yaml")
    app.window.advance(16)
    return app, view


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    parser.add_argument("--out", type=Path, default=Path("spike-results"))
    parser.add_argument("--dry", action="store_true", help="build the window and print the halves' rectangles, then exit")
    args = parser.parse_args(argv)
    app, view = build()
    if args.dry:
        for half in HALVES:
            print(half, absolute_rect(view.node(half)))
        x, y, w, h = absolute_rect(view.node("source"))
        print("a point 5 px inside Source's left edge:", where(view, x + 5, y + h / 2))
        print("the middle of Preview:", where(view, *[a + b / 2 for a, b in zip(absolute_rect(view.node("preview"))[:2],
                                                                           absolute_rect(view.node("preview"))[2:])]))
        return 0

    window = app.window
    dock = view.dock_host("dock").dock
    t0 = time.perf_counter()
    events: list[dict] = []
    last = {"x": None, "y": None, "drag": False}

    def log(kind, **fields):
        events.append({"t": round(time.perf_counter() - t0, 4), "kind": kind, **fields})

    def titled(panel):
        for side in dock._zones:
            for title in dock.titles(side):
                if dock.panel(title) is panel:
                    return title
        return None

    def pointer(name):
        def handler(event):
            x, y = event.window_x, event.window_y
            if x is not None:
                last["x"], last["y"] = x, y
            log(name, x=x, y=y, dragging=last["drag"])
        return handler

    for name in ("pointer_move", "pointer_down", "pointer_up", "pointer_cancel"):
        window.root.on(name, pointer(name))

    def on_target(event):
        last["drag"] = True
        log("dock_target", side=event.side, x=event.window_x, y=event.window_y)
        dock._on_target(event)

    def on_drop(event):
        half, band = where(view, last["x"], last["y"]) if last["x"] is not None else (None, None)
        log("dock_drop", side=event.side, panel=titled(event.panel), last_x=last["x"], last_y=last["y"], half=half, band=band)
        last["drag"] = False
        dock._on_drop(event)

    window.on("dock_target", on_target)
    window.on("dock_drop", on_drop)

    def on_key(event):
        if event.key == "q":
            app.close()

    window.root.on("key_down", on_key)
    print("Drag the tabs onto the halves' edges and middles and the other zones; press q when done.")
    app.run()

    drops = [e for e in events if e["kind"] == "dock_drop"]
    moves_in_drag = [e for e in events if e["kind"] == "pointer_move" and e.get("dragging")]
    lines = [f"drag spike: {len(events)} events, {len(drops)} drops, {len(moves_in_drag)} pointer_moves during a drag",
             "root pointer_move kept arriving during a drag: " + ("YES" if moves_in_drag else "NO (Tesserae cannot hit-test; ask tre)")]
    for drop in drops:
        lines.append(f"  drop {drop['panel']!r}: tre said {drop['side']!r}; last pointer ({drop['last_x']}, {drop['last_y']}); "
                     f"half {drop['half']!r}, band {drop['band']!r}")
    text = "\n".join(lines)
    args.out.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    (args.out / f"drag-{stamp}.json").write_text(json.dumps({"events": events}, indent=0), encoding="utf-8")
    (args.out / f"drag-{stamp}.txt").write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
