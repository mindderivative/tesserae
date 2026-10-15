#!/usr/bin/env python3
"""Tesserae's window, dock and embedded views, in the same YAML as any view.

The frame -- the title bar, the rail, the docked panels, the screens and the status bar -- is `Window_View.yaml`, opened
with `app.open_view()`. There are no widgets made in Python:

- The panels (`Files`, `Outline`, `Properties`, `Console`) are views the window calls; the ones that show state (`Console`, and the
  `Notes` screen) read the names of `Window_ViewModel.py`, which serves the window.
- `Compare` is a panel of two halves (a split): drag a tab onto a half to add it as a tab, or onto its edge to split it.
- The screens (`Home`, `Notes`) are views called with a `route:`; the rail's items name them, and `app.navigate`
  moves the rail's selection.
- Everything follows the app's theme: no `theme=` anywhere.

It checks itself, then renders 20 frames with hot reload on and exits. Run it with `--interactive` to keep the window open
(close it to quit) and try it by hand: drag a tab onto a half of `Compare`, onto its edge, and back out.
"""

import sys
from pathlib import Path

from loguru import logger

from tesserae import App, configure_logging
from Window_ViewModel import WindowViewModel

configure_logging()

directory = Path(__file__).parent
SEED = (0x67, 0x50, 0xA4, 0xFF)

app = App(title="Tesserae Window", theme_seed=SEED, dark=False, root=directory, search=["."])
app.bind(WindowViewModel)
view = app.open_view("Window")  # the whole frame, from Window_View.yaml
app.navigate_to("")
window = app.window
window.advance(16)

dock = view.dock_host("root.body.dock")  # a node's id is its path from the root
console = app.bindings.viewmodel_for("Window")

# -- self-checks: the same things a user would do ---------------------------------
assert app.borderless is True and app.current_screen.get() == "Home"
assert view.node("root").get("visible") is not False
layout = dock.layout()["zones"]
assert layout["left"]["panels"] == ["Files", "Outline"] and layout["right"]["panels"] == ["Properties"]
assert layout["bottom"]["panels"] == ["Console"] and layout["center"]["panels"] == ["Screens", "Compare"]
assert console.last.get() == "tesserae: window started"

window.simulate("click", node=view.node("root.body.nav.item[Notes]"))  # the rail opens Notes
window.advance(16)
assert app.current == "Notes" and app.current_screen.get() == "Notes"
assert view.node("root.body.dock.screens.home.title").get("text") == "Welcome"
app.navigate("Home")
assert app.current_screen.get() == "Home"

dock.set_size("left", 300)  # what dragging the handle does
window.advance(16)
assert dock.size("left") == 300
saved = dock.layout()
dock.restore(saved)  # ...and putting a saved layout back

# The Compare panel has two halves, each a small zone with a tab strip. Dragging a tab onto a half adds it as a tab, onto an edge
# splits the half; from code, `move` does the first. The layout keeps the halves and the splits the user made.
dock.dock.show(view.node("root.body.dock.compare"))
window.advance(16)
before, after = "root.body.dock.compare.before", "root.body.dock.compare.after"  # the halves' ids are their paths too
assert list(dock.halves()) == [before, after] and dock.halves()[after] == {"panels": [], "shown": None}
dock.move("root.body.dock.outline", after)
window.advance(16)
assert dock.half_of("root.body.dock.outline") == after
assert dock.halves()[after] == {"panels": ["root.body.dock.outline"], "shown": "root.body.dock.outline"}
saved = dock.layout()  # plain data: it could be written to a file
assert saved["halves"][after] == {"panels": ["Outline"], "shown": "Outline"}
dock.move("root.body.dock.outline", "left")  # back in its zone...
dock.restore(saved)  # ...and into the half again
window.advance(16)
assert dock.half_of("root.body.dock.outline") == after
dock.move("root.body.dock.outline", "left")  # put it back, so a hand-run starts with the Outline tab in the left zone and Compare showing
window.advance(16)
assert dock.half_of("root.body.dock.outline") is None

app.set_dark(True)  # the frame follows the app's theme
app.set_dark(False)

logger.info("layout: {}", saved)
if "--interactive" in sys.argv[1:]:
    logger.info("interactive: close the window to quit")
    app.run(hot_reload=True)  # until the window is closed
else:
    app.run(max_frames=20, hot_reload=True)  # the window view and the views in it are watched while it runs
    logger.info("examples/window_dock/app.py: exited cleanly after a real 20-frame render loop")
