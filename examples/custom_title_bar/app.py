#!/usr/bin/env python3
"""A window with no OS title bar, whose title bar the app draws.

`App(borderless=True)` turns the OS's title bar and borders off; the
view's `widget: TitleBar` draws one in the app's theme -- its icon, title
and window buttons -- with a search field of the app's own in it, and a
second bar, built by hand, shows the pieces a TitleBar is made of:
`window_region: drag` and the `window.*` handlers.

Drag either bar to move the window, double-click one to maximize it,
and drag an edge to resize it. On macOS the OS keeps its traffic lights,
and the bar makes room for them.
"""

from pathlib import Path

from loguru import logger

from tesserae import App, configure_logging

from Home_ViewModel import HomeViewModel

configure_logging()

HERE = Path(__file__).parent

app = App(width=720, height=420, title="Notes", theme_seed=(0x67, 0x50, 0xA4, 0xFF),
          borderless=True, min_width=480, min_height=280, root=HERE, search=["."])
app.bind(HomeViewModel)
view = app.open_view("Home")  # Home_View.yaml
app.show("Home")

# The example checks itself, as the others do: both bars drag the window, and the search field in the title bar follows the ViewModel.
assert view.node("root.bar").get("window_region") == "drag"  # the TitleBar's own region
assert view.node("root.body.own_bar").get("window_region") == "drag"  # the bar built by hand
search = view.node("root.bar.search")
viewmodel = app.bindings.viewmodel_for("Home")
assert search.get("text") == ""
viewmodel.query.set("meeting notes")
app.window.advance(16)
assert search.get("text") == "meeting notes"
close = view.node("root.body.own_bar.own_close")
assert (close.get("role"), close.get("label")) == ("button", "Close")  # the hand-made close button is a named button for a screen reader
logger.info("examples/custom_title_bar/app.py: both bars drag, the search field follows its ViewModel")

app.run(max_frames=20)  # a bounded run, as the other examples; remove max_frames to keep it open
logger.info("examples/custom_title_bar/app.py: exited cleanly after a real 20-frame render loop")
