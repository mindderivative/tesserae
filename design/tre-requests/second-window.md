# Request to tre: open a second window while the app runs

*Drafted for Tesserae 0.5.0 (#229). Not sent: sending it to tre is the project owner's decision.*

## What Tesserae needs

More than one window: a detached panel, a preferences window, a second view of a document. Material 3 says nothing about it, but a desktop framework needs it.

## What the spike found (tre 0.5.4, Linux/Wayland, a person at the machine, 2026-10-08)

`tools/spikes/second_window.py`: `App.add_window` is documented as registering a window to open the next time `run()` is called. Called while the app runs, from a key handler on the loop thread and from `thread_handle().call_soon`, it raised `RuntimeError: Already borrowed` both times. No second window appeared (it drew 0 frames); closing the first ended the run normally. Results: `spike-results/second-window-*.json`.

`Window.set` also accepts only title, partial_redraw, show_damage, profile_nodes, glyph_cache, decorations, fullscreen, min_width, min_height, icon, resize_border, system_menu, gpu_watchdog, present_mode, dpi_scaling, transparent, blur_behind and click_through: no `parent`, `owner`, `modal`, `transient_for`, `always_on_top`, `skip_taskbar`, `x`, `y` or `position`.

## The ask

1. Make `add_window` work while `run()` is going (the loop must not hold the app borrowed across handlers), and return a window that draws, takes input, and can be closed without ending the run; closing the last window ends it.
2. Window properties: `parent` (or `transient_for`), `modal`, `always_on_top`, `skip_taskbar`, and `x`/`y` (or `position`) with a way to centre on the parent.

## How Tesserae uses it

`app.open_window(view, ...)` and a `Window`-level ownership of screens (#229, #204). Until then an app has one window, and a second "window" is an Overlay.
