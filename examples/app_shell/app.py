#!/usr/bin/env python3
"""Tesserae's app shell (M45): an app framed by a top app bar, a
navigation rail and a status bar, with docked tool panels around a
center where its screens are tabs.

- `AppShell(..., center=True)` makes the middle a dock zone, so `app.show`
  opens each screen as a tab there and brings it forward after.
- The Files, Outline, Properties and Console panels are docked in the
  left, right and bottom zones; drag a tab to another zone, or use its
  context menu (right click, the Menu key, Shift+F10) to "Move to" one.
  Drag a zone's handle (or focus it and use the arrow keys) to resize it.
- The rail switches screens; a panel moving zone updates the status bar.
- Nothing is given `theme=`: the bars, rail, shell, dock and panels are
  made on `app.window`, so they take the app's theme and follow it (M50)
  -- `app.set_dark(True)` re-colours them all with the screens.

It checks itself, then renders 20 frames (omit `max_frames` for a real,
interactive run).
"""

from pathlib import Path

from loguru import logger

from tesserae import App, View, configure_logging
from tesserae.shell import AppShell
from tesserae.widgets import navigation_rail, status_bar, top_app_bar

from Home_ViewModel import HomeViewModel
from Notes_ViewModel import NotesViewModel

configure_logging()

directory = Path(__file__).parent
SCREENS = ["Home", "Notes"]
SEED = (0x67, 0x50, 0xA4, 0xFF)

app = App(width=1100, height=700, title="Tesserae App Shell", theme_seed=SEED, dark=False)
window = app.window  # everything made on it follows the app's theme (M50)

bar = top_app_bar(window, "Tesserae Studio", trailing_icons=["settings"], width=1100)
rail = navigation_rail(window, SCREENS, ["home", "search"], selected=0)
status = status_bar(window, "Ready", width=1100)
shell = AppShell(window, top_bar=bar, navigation=rail, status_bar=status,
                 zones={"left": 220, "right": 260, "bottom": 160}, center=True)


def panel(lines: list[str]) -> View:
    """A simple tool panel: a column of text lines."""
    return View({"id": "root", "kind": "Container", "style": {"flex_direction": "vertical", "gap": 8, "padding": 16},
                 "children": [{"id": f"line{i}", "kind": "Text", "text": {"content": line, "typography_role": "body_medium"},
                               "style": {"foreground": "on_surface"}} for i, line in enumerate(lines)]},
                window=window)


dock = shell.dock
files = panel(["app.py", "Home_View.yaml", "Notes_View.yaml"])
dock.add_panel("left", files.root, "Files")
dock.add_panel("left", panel(["Home", "Notes"]).root, "Outline")
dock.add_panel("right", panel(["Width: 1100", "Height: 700"]).root, "Properties")
dock.add_panel("bottom", panel(["tesserae: app shell started"]).root, "Console")

home_view = app.build_view(directory / "Home_View.yaml")
home_vm = HomeViewModel(home_view, app)
app.register("Home", home_view, home_vm)
notes_view = app.build_view(directory / "Notes_View.yaml")
app.register("Notes", notes_view, NotesViewModel(notes_view))

app.use_shell(shell)
rail.on_change(lambda index: app.show(SCREENS[index]))


def moved(node, side):
    home_vm.panels_moved.set(home_vm.panels_moved.get() + 1)
    status.part("text").set(text=f"Moved a panel to the {side}")


dock.on_move(moved)
app.show("Home")
window.advance(16)

# -- self-checks: the same things a user would do ---------------------------------
assert dock.titles("center") == ["Home"]
window.simulate("click", node=rail.part("item1"))  # the rail opens Notes as a center tab
assert dock.titles("center") == ["Home", "Notes"] and dock.shown_title("center") == "Notes"
app.show("Home")
window.simulate("click", node=home_view.node("open_notes"))  # a screen's own button opens Notes
assert dock.shown_title("center") == "Notes"

dock.move(dock.panel("Outline"), "right")  # what "Move to right" does
window.advance(16)
assert dock.titles("right") == ["Properties", "Outline"] and home_vm.summary.get() == "Panels moved this session: 1"
assert status.part("text").get("text") == "Moved a panel to the right"

shell.set_size("left", 260)
layout = shell.layout()
logger.info("layout: {}", layout)
assert layout["zones"]["left"] == {"panels": ["Files"], "shown": "Files", "size": 260.0}
assert layout["zones"]["center"]["panels"] == ["Home", "Notes"]

app.set_dark(True)  # everything follows: the screens, bars, rail, shell, dock and panels
dark = app.theme
assert shell.node.get("fill") == dark.role("surface") and bar.node.get("fill") == dark.role("surface")
assert dock._zones["left"].node.get("fill") == dark.role("surface_container_low")
assert files.node("line0").get("fill") == dark.role("on_surface")
app.set_dark(False)

app.run(max_frames=20)
logger.info("examples/app_shell/app.py: exited cleanly after a real 20-frame render loop")
