---
name: live-check
description: Use when a Tesserae change should show on screen (a view, stylesheet, theme, widget, layout, colour, icon, text or animation change), when asked "does it look right", to reproduce a visual bug, or before reporting a UI change as done. Renders the view headlessly to a PNG with tools/shot.py, looks at it, drives clicks, and says plainly what a headless render can and cannot show.
---

# Looking at what a change draws

Unit tests say a value is right; they do not say the window looks right. `tools/shot.py` renders a view in tre's headless window (no GPU, no display) and saves the pixels, and the `read` tool shows the PNG. Use it for any change a user would see.

## 1. Render

```bash
python3 tools/shot.py examples/counter --view Counter --viewmodel Counter_ViewModel.CounterViewModel --size 240x120 --out /tmp/shots/before.png
```

- ROOT holds `<Name>_View.yaml` files (the view's folder, an example, or a scratch folder you make under `/tmp` for a one-off view; pass `--viewmodel module.Class` when the view needs one).
- `--names` lists each node's id and box (`root.button  x,y,w,h = [16, 60, 120, 40]`): use it to pick a `--click` target or to check a layout number.
- `--click root.button` (repeatable) dispatches real clicks, then renders. `--dark`, `--seed RRGGBB`, `--size WxH` and `--reduced-motion` vary the conditions.
- The last line reports how much of the image differs from the corner colour; 0% means a blank render, which is a failure, not a pass.

## 2. Compare

Render **before and after** the change (stash or check out the old state for the first one) to two files, `read` both, and describe the difference in words: what moved, what changed colour, what is clipped. For a state (hover, pressed, focus, disabled) render each. For a theme or colour change render light and dark. A change that "looks fine" with nothing to compare against is not evidence.

To keep a check, turn it into a pixel test (`tests/test_pixels.py` has `opened(...)` and `pixel(...)` helpers) with a mutation check, as in the `issue-workflow` skill.

## 3. A real window (only when asked)

The machine runs KDE Plasma on Wayland and real windows can open from a shell, but **the person at the machine drives them**: only open one when the user asks or is watching, run it under `timeout 60`, and stop it by its own pid, never `pkill -f` on a pattern in your own command line. Wayland ignores window position and `always_on_top`. `tools/window_perf.py` and anything that opens a second OS window need a display; headless tests skip without one.

## 4. Report what you saw, and what you could not

Say which images you looked at and what they showed. The headless render does **not** show: frame timing, scroll feel and snap, the OS's window decoration, real fonts if the machine has different ones, GPU-specific shader differences, other platforms (macOS and Windows are CI's), or how it feels to a person. Write "not seen" for those; never "looks fine" for a thing a snapshot cannot show.
