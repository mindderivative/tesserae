#!/usr/bin/env python3
"""Tesserae's app shell from a file (M52): the same studio as
`examples/app_shell/`, but its frame -- the top app bar, the navigation
rail, the status bar, the docked zones, center tabs and the panels in
them -- is declared in `Studio_Shell.yaml` and built by
`app.load_shell()`, with no widgets made in Python.

- The panels are views named like screens: `Files`, `Outline` and
  `Properties` are just `*_View.yaml` files, and `Console` has a
  `Console_ViewModel.py` too. `load_shell` finds each by name, next to the
  shell file, and registers it, so `app.show("Console")` brings its tab
  forward and each one is hot-reloaded.
- The rail's items name screens: choosing one calls `app.show`, and
  `app.show` from anywhere else moves the rail's selection.
- Everything follows the app's theme (M50) -- no `theme=` anywhere.
- With `app.run(hot_reload=True)`, editing `Studio_Shell.yaml` changes
  the title, the status text, zone sizes, the rail and the panels in
  place; a structural edit (a zone added, say) is logged as needing a
  restart.

It checks itself, then renders 20 frames with hot reload on (omit
`max_frames` for a real, interactive run).
"""

from pathlib import Path

from loguru import logger

from tesserae import App, configure_logging

from Home_ViewModel import HomeViewModel
from Notes_ViewModel import NotesViewModel

configure_logging()

directory = Path(__file__).parent
SEED = (0x67, 0x50, 0xA4, 0xFF)

app = App(width=1100, height=700, title="Tesserae App Shell (from a file)", theme_seed=SEED, dark=False)

# The screens. Home's ViewModel needs the app, so it's registered here;
# Notes needs only its view, so `load` does it.
home_view = app.build_view(directory / "Home_View.yaml")
home_vm = HomeViewModel(home_view, app)
app.register("Home", home_view, home_vm)
app.load(directory / "Notes_View.yaml", NotesViewModel)
app.show("Home")

shell = app.load_shell(directory / "Studio_Shell.yaml")  # the whole frame, from the file
dock = shell.dock
console_view, console = app.screen("Console")  # a panel: its view, and the ViewModel built from Console_ViewModel.py


def moved(node, side):
    home_vm.panels_moved.set(home_vm.panels_moved.get() + 1)
    shell.status_bar.part("text").set(text=f"Moved a panel to the {side}")
    console.log(f"moved a panel to the {side}")


dock.on_move(moved)
window = app.window
window.advance(16)

# -- self-checks: the same things a user would do ---------------------------------
assert shell.top_bar.part("title").get("text") == "Tesserae Studio"
assert dock.titles("left") == ["Files", "Outline"] and dock.titles("right") == ["Properties"]
assert dock.titles("bottom") == ["Console"] and dock.titles("center") == ["Home"]
assert console_view.node("last").get("text") == "tesserae: app shell started"

window.simulate("click", node=shell.navigation.part("item1"))  # the rail opens Notes as a center tab
assert app.current == "Notes" and dock.titles("center") == ["Home", "Notes"]
window.simulate("click", node=shell.navigation.part("item0"))
window.simulate("click", node=home_view.node("open_notes"))  # a screen's own button opens Notes...
assert shell.navigation.selected.get() == 1  # ...and the rail follows

app.show("Files")  # a panel is a screen: its tab comes forward, where it's docked
files_view, _ = app.screen("Files")
assert dock.shown("left") == files_view.root and dock.side_of(dock.panel("Files")) == "left"

dock.move(dock.panel("Outline"), "right")  # what "Move to right" does
window.advance(16)
assert home_vm.summary.get() == "Panels moved this session: 1"
assert console_view.node("last").get("text") == "moved a panel to the right"

app.set_dark(True)  # the file-built frame follows the app's theme
dark = app.theme
assert shell.top_bar.node.get("fill") == dark.role("surface")
assert dock._zones["left"].node.get("fill") == dark.role("surface_container_low")
app.set_dark(False)

layout = shell.layout()
logger.info("layout: {}", layout)
assert layout["zones"]["right"]["panels"] == ["Properties", "Outline"]

app.run(max_frames=20, hot_reload=True)  # the shell file, screens and panels are watched while it runs
logger.info("examples/app_shell_file/app.py: exited cleanly after a real 20-frame render loop")
