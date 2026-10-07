#!/usr/bin/env python3
"""Window performance poll: the Tasks tutorial as it ends (a navigation rail and a status bar), in a native or a
custom window, with every frame, every resize and a background sample of the frame counter recorded while a person
resizes and drags it by hand.

    python tools/window_perf.py native            # the OS draws the title bar and borders
    python tools/window_perf.py custom            # `decorations=False`: the shell's top bar is the title bar
    python tools/window_perf.py bare-native       # a bare `tre` window (no Tesserae), the OS's frame
    python tools/window_perf.py bare-custom       # a bare `tre` window, undecorated, with a drag region and a resize border

Keys (the window must have focus): `1` marks "resizing", `2` "dragging", `0` "idle"; `q` ends the run and writes the
results. Closing the window ends it too. Results go to `--out`: the raw events as JSON and a text summary, which is
also printed.

`--selftest` runs a few seconds on its own and exits, to check the harness.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECT = ROOT / "examples" / "tutorial_project" / "step6"
PHASES = {"1": "resize", "2": "drag", "0": "idle"}


def build(mode: str):
    from tesserae import App, Signal

    class AppState:
        def __init__(self):
            self.user = Signal("Ada")

    app = App(width=640, height=480, title=f"Tasks ({mode})", root=PROJECT, decorations=(mode == "native"),
              custom_theme="Brand", stylesheet="Tasks", state=AppState())
    app.load("Main")
    app.load("Settings")
    app.route("", "Main")
    app.route("settings", "Settings")
    app.load_shell("Tasks")
    app.navigate_to("")
    return app


class _Bare:
    """A bare `tre` window standing in for a Tesserae `App`: the same few members the recorder uses."""

    def __init__(self, mode: str, present_mode: str | None = None, resize_border: int = 6) -> None:
        import tre

        decorated = mode == "bare-native"
        self.window = tre.Window(width=640, height=480, title=f"tre ({mode})")
        root = self.window.root
        root.set(fill=(0x14, 0x12, 0x18, 0xFF), flex_direction="vertical", padding=0, gap=0)
        if present_mode:
            self.window.set(present_mode=present_mode)  # tre 0.5.4: "vsync" (the default) or "low_latency"
        if not decorated:
            self.window.set(decorations=False, resize_border=0 if resize_border == 0 else 6)
        bar = self.window.create("box", height=48.0, fill=(0x4A, 0x44, 0x58, 0xFF), window_region="drag")
        body = self.window.create("box", flex_grow=1.0, flex_direction="horizontal", gap=8.0, padding=8.0)
        rail = self.window.create("box", width=80.0, fill=(0x2B, 0x29, 0x30, 0xFF))
        content = self.window.create("box", flex_grow=1.0, fill=(0x21, 0x1F, 0x26, 0xFF))
        status = self.window.create("box", height=28.0, fill=(0x4A, 0x44, 0x58, 0xFF))
        for node in (bar, body, status):
            root.add_child(node)
        for node in (rail, content):
            body.add_child(node)
        self._app = tre.App()
        self._app.add_window(self.window)

    def stats_handle(self):
        return self.window.stats_handle()

    def run(self) -> None:
        self._app.run()


class Recorder:
    def __init__(self, app, mode: str) -> None:
        self.app, self.mode = app, mode
        self.t0 = time.perf_counter()
        self.phase = "idle"
        self.marks: list[tuple[float, str]] = [(0.0, "idle")]
        self.frames: list[tuple[float, str, dict]] = []     # (t, phase, the frame's stats)
        self.resizes: list[tuple[float, str, float, float]] = []  # (t, phase, width, height)
        self.pointer: list[tuple[float, str, str]] = []     # (t, phase, event)
        self.samples: list[tuple[float, str, int, float]] = []    # (t, phase, frames so far, fps)
        self.done = threading.Event()
        self.frames_available = True
        window = app.window
        try:
            window.on("frame", self.on_frame)
        except ValueError:  # tre before 0.5.4 has no `frame` event: only the resize events are recorded
            self.frames_available = False
        window.on("resize", self.on_resize)
        window.on("closed", lambda e: self.done.set())
        for name in ("pointer_down", "pointer_up", "pointer_cancel"):
            window.root.on(name, lambda e, name=name: self.pointer.append((self.now(), self.phase, name)))
        window.root.on("key_down", self.on_key)
        # a bright strip over the bottom of the window, so the keys can't be missed
        self.strip = window.create("box", position="absolute", x=0.0, y="88%", width="100%", height=44.0, fill=(255, 196, 0, 255),
                                   z_index=1000, hit_testable=False, a11y_hidden=True, align_items="center",
                                   justify_content="center")
        self.label = window.create("text", text=" ", font_family="Roboto", font_size=17.0, font_weight=700.0,
                                   fill=(0, 0, 0, 255), width=620.0, height=24.0, hit_testable=False, a11y_hidden=True,
                                   text_align="center", wrap="none")
        self.strip.add_child(self.label)
        window.root.add_child(self.strip)
        self.show_phase()

    def now(self) -> float:
        return time.perf_counter() - self.t0

    def show_phase(self) -> None:
        text = f"{self.mode.upper()}  now: {self.phase.upper()}    press  1 = resize   2 = drag   0 = idle   q = finish"
        self.label.set(text=text)
        self.app.window.set(title=f"[{self.phase.upper()}]  1 resize  2 drag  0 idle  q finish")

    def on_frame(self, event) -> None:
        self.frames.append((self.now(), self.phase, dict(event.stats or {})))

    def on_resize(self, event) -> None:
        self.resizes.append((self.now(), self.phase, float(event.width), float(event.height)))

    def on_key(self, event) -> None:
        self.pointer.append((self.now(), self.phase, f"key:{event.key}"))
        if event.key in PHASES:
            self.phase = PHASES[event.key]
            self.marks.append((self.now(), self.phase))
            self.show_phase()
        elif event.key == "q":
            self.app.window.close()

    def sample_loop(self, handle) -> None:
        """20 times a second, from another thread: how many frames have been drawn. A modal OS drag that stops the
        event loop shows here as a counter that doesn't move."""
        while not self.done.is_set():
            try:
                stats = handle.read()
                self.samples.append((self.now(), self.phase, int(stats.get("frames", 0)),
                                     float((stats.get("recent") or {}).get("fps", 0.0))))
            except Exception:  # the window is going
                pass
            self.done.wait(0.05)


def _pct(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(round(q * (len(ordered) - 1))))]


def _line(name: str, values: list[float], unit: str = "ms") -> str:
    if not values:
        return f"    {name:<22} -"
    return (f"    {name:<22} mean {statistics.fmean(values):7.2f}  p50 {_pct(values, .5):7.2f}  p95 {_pct(values, .95):7.2f}"
            f"  p99 {_pct(values, .99):7.2f}  max {max(values):7.2f} {unit}")


def summarize(rec: Recorder) -> str:
    end = rec.now()
    spans = []
    for (start, phase), nxt in zip(rec.marks, [m[0] for m in rec.marks[1:]] + [end]):
        spans.append((phase, start, nxt))
    out = [f"window performance: {rec.mode}", f"  total {end:.1f}s, {len(rec.frames)} frames, {len(rec.resizes)} resize events"]
    for phase in ("resize", "drag", "idle"):
        seconds = sum(b - a for p, a, b in spans if p == phase)
        if seconds <= 0:
            continue
        frames = [(t, s) for t, p, s in rec.frames if p == phase]
        resizes = [(t, w, h) for t, p, w, h in rec.resizes if p == phase]
        samples = [s for s in rec.samples if s[1] == phase]
        out += ["", f"== {phase}: {seconds:.1f}s =="]
        out.append(f"  frames {len(frames)} ({len(frames) / seconds:.1f}/s), resize events {len(resizes)} "
                   f"({len(resizes) / seconds:.1f}/s), pointer events {sum(1 for p in rec.pointer if p[1] == phase)}")
        times = [t for t, _ in frames]
        gaps = [(b - a) * 1000 for a, b in zip(times, times[1:])]
        out.append(_line("frame interval", gaps))
        out.append(f"    gaps over 50 ms: {sum(1 for g in gaps if g > 50)}, over 100 ms: {sum(1 for g in gaps if g > 100)}")
        for key in ("total_ms", "cpu_ms", "gpu_ms"):
            out.append(_line(f"frame {key}", [s[key] for _, s in frames if isinstance(s.get(key), (int, float))]))
        stages: dict[str, list[float]] = {}
        for _, s in frames:
            for name, value in (s.get("stage_ms") or {}).items():
                if isinstance(value, (int, float)):
                    stages.setdefault(name, []).append(value)
        for name, values in stages.items():
            out.append(_line(f"stage {name}", values))
        if resizes:
            rt = [t for t, _, _ in resizes]
            out.append(_line("resize interval", [(b - a) * 1000 for a, b in zip(rt, rt[1:])]))
            ft = [t for t, _ in frames]
            latency = []
            for t in rt:
                later = [f for f in ft if f >= t]
                if later:
                    latency.append((later[0] - t) * 1000)
            out.append(_line("resize -> next frame", latency))
            w0, h0 = resizes[0][1:]
            w1, h1 = resizes[-1][1:]
            out.append(f"    size {w0:.0f}x{h0:.0f} -> {w1:.0f}x{h1:.0f}")
        if samples:
            counts = [c for _, _, c, _ in samples]
            stalls, longest, run = 0, 0.0, 0.0
            for (ta, _, ca, _), (tb, _, cb, _) in zip(samples, samples[1:]):
                if cb == ca:
                    run += tb - ta
                    longest = max(longest, run)
                else:
                    stalls += run > 0.15
                    run = 0.0
            out.append(f"    sampled counter: {counts[0]} -> {counts[-1]}; stalls over 150 ms: {stalls + (run > 0.15)}, "
                       f"longest {max(longest, run) * 1000:.0f} ms with no new frame")
    return "\n".join(out)


def bursts(rec: Recorder) -> str:
    """The resizes found by their own timing, however the keys were used: a burst is resize events with no gap over half
    a second. For each, whether a frame followed every event, how soon, and what the frames cost."""
    import bisect

    groups: list[list[tuple[float, str, float, float]]] = []
    for r in rec.resizes:
        if groups and r[0] - groups[-1][-1][0] <= 0.5:
            groups[-1].append(r)
        else:
            groups.append([r])
    frame_times = [t for t, _, _ in rec.frames]
    out = ["", "== resize bursts (found by timing) =="]
    for g in (g for g in groups if len(g) > 5):
        t0, t1 = g[0][0], g[-1][0]
        inside = [(t, s) for t, _, s in rec.frames if t0 <= t <= t1 + 0.05]
        gaps = [(b[0] - a[0]) * 1000 for a, b in zip(inside, inside[1:])]
        latency = []
        for r in g:
            i = bisect.bisect_left(frame_times, r[0])
            if i < len(frame_times):
                latency.append((frame_times[i] - r[0]) * 1000)
        totals = [s.get("total_ms", 0.0) for _, s in inside]
        out.append(f"  {t0:6.1f}-{t1:6.1f}s ({t1 - t0:4.1f}s)  {g[0][2]:.0f}x{g[0][3]:.0f} -> {g[-1][2]:.0f}x{g[-1][3]:.0f}  "
                   f"events {len(g)}, frames {len(inside)}")
        if gaps and latency:
            out.append(f"      frame gap p50 {_pct(gaps, .5):.1f} p95 {_pct(gaps, .95):.1f} max {max(gaps):.1f} ms;  "
                       f"frame total p50 {_pct(totals, .5):.1f} p95 {_pct(totals, .95):.1f} max {max(totals):.1f} ms;  "
                       f"resize->frame p50 {_pct(latency, .5):.1f} p95 {_pct(latency, .95):.1f} max {max(latency):.1f} ms")
    out.append(f"  pointer/key events: {[(round(t, 1), e) for t, _, e in rec.pointer][:30]}")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    parser.add_argument("mode", choices=["native", "custom", "bare-native", "bare-custom"])
    parser.add_argument("--out", type=Path, default=Path("window-perf"))
    parser.add_argument("--selftest", action="store_true", help="run a few seconds by itself and exit")
    parser.add_argument("--present-mode", choices=["vsync", "low_latency"], help="bare modes: set the window's present mode")
    parser.add_argument("--resize-border", type=int, default=6, help="bare-custom: the resize border (0 leaves resizing to the compositor)")
    parser.add_argument("--profile-nodes", action="store_true", help="also time each node's drawing")
    args = parser.parse_args(argv)
    sys.path.insert(0, str(ROOT / "src"))

    app = _Bare(args.mode, args.present_mode, args.resize_border) if args.mode.startswith("bare") else build(args.mode)
    if args.profile_nodes:
        app.profile_nodes = True
    rec = Recorder(app, args.mode)
    if hasattr(app, "stats_handle") and rec.frames_available:
        threading.Thread(target=rec.sample_loop, args=(app.stats_handle(),), daemon=True).start()
    if args.selftest:
        rec.phase = "resize"
        rec.marks.append((rec.now(), "resize"))
        count = [0]
        spinner = app.window.create("box", width=4.0, height=4.0, position="absolute", x=0.0, y=0.0, hit_testable=False,
                                    fill=(255, 0, 0, 255))
        app.window.root.add_child(spinner)

        def keep_drawing() -> None:  # a still window draws nothing, so give it something to draw
            spinner.set(translate_x=0.0)
            spinner.animate("translate_x", 8.0, 16, on_complete=keep_drawing)

        keep_drawing()

        def stop(event):
            count[0] += 1
            if count[0] == 90:
                app.window.close()

        if rec.frames_available:
            app.window.on("frame", lambda e: (rec.on_frame(e), stop(e)))
    app.run()
    rec.done.set()
    text = summarize(rec) + "\n" + bursts(rec)
    args.out.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    (args.out / f"{args.mode}-{stamp}.json").write_text(json.dumps({
        "mode": args.mode, "t0": rec.t0, "marks": rec.marks, "frames": rec.frames, "resizes": rec.resizes, "pointer": rec.pointer,
        "samples": rec.samples}, indent=0), encoding="utf-8")
    (args.out / f"{args.mode}-{stamp}.txt").write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
