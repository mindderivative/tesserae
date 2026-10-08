#!/usr/bin/env python3
"""#105 phase 1 spike (0.5.0): can tre open a second window while the app is running, and what can that window be told?

tre's `App.add_window` says it registers a window "to be opened the next time `run()` is called". This tries it anyway, in a
real window, with bare `tre` (no Tesserae code), so the answer is tre's own:

    .venv/bin/python tools/spikes/second_window.py [--out DIR]
    .venv/bin/python tools/spikes/second_window.py --dry     # only probes which `Window.set` properties exist, no window

Keys (the first window must have focus):
  2  add the second window from this key handler (on the loop thread)
  3  add the second window through `thread_handle().call_soon`
  4  close the second window (`close()`; its `close_requested` and `closed` are logged)
  5  probe `Window.set` on the second window for parent, owner, modal, transient_for, always_on_top, x, y
  q  close the first window and end the run

Do 2 (or 3), look at the screen: does a second window appear, does it draw (its frame count rises), can it be moved and closed,
does closing it leave the first running, does closing the first leave it? Results go to `--out` (default `spike-results/`).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

PROBES = ("parent", "owner", "modal", "transient_for", "always_on_top", "skip_taskbar", "x", "y", "position", "title", "min_width")


def probe(window) -> dict:
    """Which properties `Window.set` accepts (a rejected one raises ValueError; an accepted one is set to a harmless value)."""
    answers = {}
    for name in PROBES:
        value = {"title": "second window", "min_width": 100, "x": 100, "y": 100}.get(name, False)
        try:
            window.set(**{name: value})
            answers[name] = "accepted"
        except Exception as exc:  # noqa: BLE001 - the message is the answer
            answers[name] = f"{type(exc).__name__}: {str(exc)[:90]}"
    return answers


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    parser.add_argument("--out", type=Path, default=Path("spike-results"))
    parser.add_argument("--dry", action="store_true", help="probe the Window.set properties and exit")
    args = parser.parse_args(argv)
    import tre

    if args.dry:
        for name, answer in probe(tre.Window(width=200, height=100, title="probe")).items():
            print(f"  {name:14} {answer}")
        return 0

    t0 = time.perf_counter()
    log: list[dict] = []

    def note(kind, **fields):
        log.append({"t": round(time.perf_counter() - t0, 3), "kind": kind, **fields})
        print(kind, fields)

    app = tre.App()
    first = tre.Window(width=420, height=220, title="First window (keys: 2 3 4 5 q)")
    first.root.set(fill=(0x21, 0x1F, 0x26, 0xFF))
    app.add_window(first)
    second = tre.Window(width=300, height=160, title="Second window")
    second.root.set(fill=(0x4A, 0x44, 0x58, 0xFF))
    frames = {"first": 0, "second": 0}
    first.on("frame", lambda e: frames.__setitem__("first", frames["first"] + 1))
    second.on("frame", lambda e: frames.__setitem__("second", frames["second"] + 1))
    second.on("closed", lambda e: note("second_closed", frames=frames["second"]))
    second.on("close_requested", lambda e: note("second_close_requested"))
    first.on("closed", lambda e: note("first_closed", second_frames=frames["second"]))
    handle = app.thread_handle()

    def add(how):
        try:
            app.add_window(second)
            note("add_window_returned", how=how)
        except Exception as exc:  # noqa: BLE001
            note("add_window_raised", how=how, error=f"{type(exc).__name__}: {exc}")
        handle.call_soon(lambda: note("after_add", how=how, first_frames=frames["first"], second_frames=frames["second"]))

    def on_key(event):
        if event.key == "2":
            add("key handler")
        elif event.key == "3":
            handle.call_soon(lambda: add("call_soon"))
        elif event.key == "4":
            second.close()
            note("second_close_called")
        elif event.key == "5":
            note("probe", answers=probe(second))
        elif event.key == "q":
            first.close()

    first.root.on("key_down", on_key)
    print("Keys: 2/3 add the second window, 4 close it, 5 probe its properties, q quit (the first window must have focus).")
    app.run()
    note("run_returned", frames=dict(frames))

    text = "\n".join(f"{e['t']:8.3f}s {e['kind']} " + ", ".join(f"{k}={v}" for k, v in e.items() if k not in ("t", "kind")) for e in log)
    args.out.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    (args.out / f"second-window-{stamp}.json").write_text(json.dumps({"log": log, "frames": frames}, indent=0), encoding="utf-8")
    (args.out / f"second-window-{stamp}.txt").write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
