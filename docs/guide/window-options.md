# Window Options & the OS

`App(...)` takes these options, which are the window's.

| Option | Default | What it does |
| --- | --- | --- |
| `dpi_scaling` | `True` | Scales the window by the screen's density, so a 16-pixel size is the same size on every screen. `False` draws in device pixels. |
| `present_mode` | `"vsync"` | How frames reach the screen: `vsync` paces frames to the display, `low_latency` shows the newest frame at once, at the cost of drawing as fast as it can while something animates. |
| `transparent` | `False` | A window with no background of its own: what is not drawn shows the desktop. Fixed when the window opens. `app.transparent_active` says whether the platform could. |
| `blur_behind` | `False` | The OS blurs the desktop behind a transparent window. |
| `click_through` | `False` | Presses fall through the window to what is under it. |
| `ripple` | `"nodes"` | How a press ripple is drawn: `nodes` grows a circle per press and lets the engine animate it; `shader` draws up to three at once with one fill shader (soft edges, one node per clickable thing), moved a frame at a time. |
| `focus_ring` | `"solid"` | The ring around a keyboard-focused node: `solid` is one colour; `gradient` is a sweep through `secondary`, `primary` and `tertiary` that turns once every three seconds (standing still when motion is reduced). tre does not animate a gradient border, so Python sets the angle 30 times a second while a ring shows. |
| `glyph_cache` | `False` | Keeps the shapes of letters between frames: less work for a lot of text. |
| `system_fonts` | `False` | Lets a font family that isn't registered be found among the system's. |

`app.scale_factor` is the current density. A platform that can't do an option says so, naming it.

## Less motion, more contrast

Operating systems let users ask for less animation and for more contrast. An app follows both unless told otherwise:
`App(reduced_motion="system", high_contrast="system")` is the default, `True` or `False` fixes the setting, and
`app.set_reduced_motion(...)` and `app.set_high_contrast(...)` change it later.

- **Reduced motion**: animations take no time, so things are where they are going at once, and indicators that
  would repeat for ever (the indeterminate progress bar and spinner, the loading indicator) stay still.
- **High contrast**: the theme is made again at the highest contrast level of Material 3's palette, so text and
  outlines stand out, and the app re-themes at once, as it does for dark mode. It follows the OS as the user turns it
  on and off.

`app.reduced_motion` and `app.high_contrast` are what the app is doing now. For your own animations,
`tesserae.motion.duration(window, ms)` is `ms`, or 0 when motion is reduced.

## Spring easing

An animation's easing can be a spring: `Theme.easing("spring")`, or `Theme.spring(bounce)` with a `bounce` from -1
to 1 (above 0 overshoots). The duration is the spring's period, and it runs until it settles:

```python
node.animate("scale", 1.0, 300, easing=Theme.spring(0.3))
```

## What a frame costs

`app.frame_stats()` says what the frames cost (`frames`, `last`, and `recent`: the frame rate and the mean, 95th
percentile and maximum of the frame time). `app.profile_nodes = True` measures each node's drawing too, and
`app.start_trace("trace.json")` / `app.stop_trace()` record every frame for [Perfetto](https://ui.perfetto.dev).
`app.stats_handle()` is an object another thread can read the stats from.

For a quick look, `app.stats_overlay = True` shows the frame rate and time in the window's corner, and running with
`TESSERAE_STATS=1` in the environment turns it on for a run from the terminal:

```bash
TESSERAE_STATS=1 python app.py
```
