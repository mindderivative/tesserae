#!/usr/bin/env python3
"""Render a view headlessly and save what it draws as a PNG, so a change that shows on screen can be looked at.

    python3 tools/shot.py examples/counter --view Counter --viewmodel Counter_ViewModel.CounterViewModel --out /tmp/counter.png
    python3 tools/shot.py examples/counter --view Counter --viewmodel Counter_ViewModel.CounterViewModel --click root.button --out /tmp/after.png
    python3 tools/shot.py some/project --view Main --size 640x480 --dark --seed 6750A4 --out /tmp/main.png

ROOT is a folder holding `<Name>_View.yaml` files (and the ViewModel module, when one is named). The window is tre's headless one: it
draws text, shaders, gradients and backdrop blur without a GPU or display, the same snapshot `tests/test_pixels.py` reads. It does not show
timing, scroll feel, an OS window's decorations or anything another platform draws differently. Say so when reporting what you saw.

    --click NODE     dispatch a click on the node (a path like `root.button`) after the first frames; repeatable
    --frames N       16 ms frames to advance before the shot (default 8); after a click, the same again
    --reduced-motion draw without animation (default: animation on, as a user without the OS setting sees it)
    --names          print each named node's path and box, to choose a click target

Prints the PNG path, its size and the share of pixels that are not the background colour (a blank render shows as 0%).
"""

import argparse
import importlib
import sys
from pathlib import Path

from PIL import Image


def parse_size(text):
    width, height = text.lower().split("x")
    return int(width), int(height)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("root", type=Path)
    parser.add_argument("--view", required=True, help="the view's name: Main for Main_View.yaml")
    parser.add_argument("--viewmodel", help="module.Class of the ViewModel, found on ROOT")
    parser.add_argument("--out", type=Path, default=Path("/tmp/tesserae-shot.png"))
    parser.add_argument("--size", type=parse_size, default=(480, 320))
    parser.add_argument("--seed", default="6750A4", help="theme seed colour, RRGGBB")
    parser.add_argument("--dark", action="store_true")
    parser.add_argument("--frames", type=int, default=8)
    parser.add_argument("--click", action="append", default=[])
    parser.add_argument("--reduced-motion", action="store_true")
    parser.add_argument("--names", action="store_true")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    sys.path.insert(0, str(root))
    from tesserae import App

    seed = tuple(int(args.seed[i:i + 2], 16) for i in (0, 2, 4)) + (0xFF,)
    app = App(root=root, width=args.size[0], height=args.size[1], theme_seed=seed, dark=args.dark,
              reduced_motion=args.reduced_motion, search=["."])
    if args.viewmodel:
        module, _, cls = args.viewmodel.rpartition(".")
        app.bind(getattr(importlib.import_module(module), cls))
    view = app.open_view(args.view)
    window = app.show(args.view)
    for _ in range(args.frames):
        window.advance(16)
    if args.names:
        for path, node in view._built.nodes.items():  # private: the public API only looks a node up by id
            box = [round(node.get(k)) for k in ("layout_x", "layout_y", "layout_width", "layout_height")]
            print(f"  {path}  x,y,w,h = {box}")
    for path in args.click:
        window.simulate("click", node=view.node(path))
        for _ in range(args.frames):
            window.advance(16)
    rgba, width, height = window.snapshot()
    image = Image.frombytes("RGBA", (width, height), bytes(rgba))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    image.save(args.out)
    data = image.tobytes()
    different = sum(1 for i in range(0, len(data), 4) if data[i:i + 4] != data[:4])
    print(f"{args.out}  {width}x{height}  {100 * different / (width * height):.1f}% of pixels differ from the corner colour")
    return 0


if __name__ == "__main__":
    sys.exit(main())
