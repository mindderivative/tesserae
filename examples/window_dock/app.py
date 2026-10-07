#!/usr/bin/env python3
"""Tesserae's window, dock and embedded views, in the same YAML as any view.

The frame -- the title bar, the rail, the docked panels, the screens and the status bar -- is `Window_View.yaml`, loaded
with `app.load()`. There are no widgets made in Python:

- The panels (`Files`, `Outline`, `Properties`, `Console`) are `view:` nodes; `Console` has a `Console_ViewModel.py` too.
- The screens (`Home`, `Notes`) are `view:` nodes with a `route:`; the rail's items name them, and `app.navigate`
  moves the rail's selection.
- Everything follows the app's theme: no `theme=` anywhere.

It checks itself, then renders 20 frames with hot reload on (omit `max_frames` for a real, interactive run).
"""

from pathlib import Path

from loguru import logger

from tesserae import App, configure_logging

configure_logging()

directory = Path(__file__).parent
SEED = (0x67, 0x50, 0xA4, 0xFF)

app = App(title="Tesserae Window", theme_seed=SEED, dark=False)
view, _ = app.load(directory / "Window_View.yaml")  # the whole frame, from the file
app.navigate_to("")
window = app.window
window.advance(16)

dock = view.dock_host("dock")
console = view.embedded("console_view").viewmodel

# -- self-checks: the same things a user would do ---------------------------------
assert app.borderless is True and app.current_screen.get() == "Home"
assert view.node("root").get("visible") is not False
layout = dock.layout()["zones"]
assert layout["left"]["panels"] == ["Files", "Outline"] and layout["right"]["panels"] == ["Properties"]
assert layout["bottom"]["panels"] == ["Console"] and layout["center"]["panels"] == ["Screens"]
assert console.last.get() == "tesserae: window started"

window.simulate("click", node=view.node("nav.item.1"))  # the rail opens Notes
window.advance(16)
assert app.current == "Notes" and app.current_screen.get() == "Notes"
assert view.embedded("home").node("title").get("text") == "Welcome"
app.navigate("Home")
assert app.current_screen.get() == "Home"

dock.set_size("left", 300)  # what dragging the handle does
window.advance(16)
assert dock.size("left") == 300
saved = dock.layout()
dock.restore(saved)  # ...and putting a saved layout back

app.set_dark(True)  # the frame follows the app's theme
app.set_dark(False)

logger.info("layout: {}", saved)
app.run(max_frames=20, hot_reload=True)  # the window view and the views in it are watched while it runs
logger.info("examples/window_dock/app.py: exited cleanly after a real 20-frame render loop")
