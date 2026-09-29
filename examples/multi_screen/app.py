#!/usr/bin/env python3
"""Tesserae's second vertical slice: `App.show(name)` switching between two
fully-bootstrapped, independent screens -- `Home`/`Settings`, each its
own `*_View.yaml` + `*_ViewModel.py` pair -- through the same live
`Window`, from inside a real dispatched click handler on each screen's
own nav button.

Mirrors `tre`'s own `examples/live_view_switch.py` (the same capability
one layer lower, attaching and detaching screen roots directly) -- this
proves it through Tesserae's `App`, the shape a real Tesserae app uses.

Both screens are `load()`ed. Their ViewModels reach the app as
`self.app` (to call `show`) and its shared state as `self.state`, found
through the view's window (M65), so neither needs a widened constructor
and `load()`'s plain `viewmodel_cls(view)` does. The state is one
`Signal`, `came_from`, which each handler sets and both screens bind to
(`{{ state.came_from.get() }}`): one write, both screens.

Home navigates to Settings (`self.app.navigate`), a step in the app's
history, and Settings goes `back()` (M66). Routes name the screens
(`""` for Home, `"settings"`), so `python app.py settings` opens on
Settings, a deep link, and `app.location` says where the app is.

`load()` builds each view with the app's theme and stylesheet, and a
screen built from a file is hot-reloaded by `app.run(hot_reload=True)`.
"""

import sys
from pathlib import Path

from loguru import logger

from tesserae import App, Signal, configure_logging

from Home_ViewModel import HomeViewModel
from Settings_ViewModel import SettingsViewModel

configure_logging()  # Tesserae's console format; configure_logging("DEBUG") shows more

directory = Path(__file__).parent


class AppState:
    """What both screens share (M65)."""

    def __init__(self):
        self.came_from = Signal("just started")


app = App(width=240, height=150, title="Tesserae Multi-Screen", state=AppState())

home_view, _ = app.load(directory / "Home_View.yaml", HomeViewModel)
settings_view, _ = app.load(directory / "Settings_View.yaml", SettingsViewModel)

app.route("", "Home")
app.route("settings", "Settings")

# A deep link from the command line; with none, the root route: Home.
window = app.navigate_to(sys.argv[1] if len(sys.argv) > 1 else "")
if app.current == "Settings":  # opened by a deep link: show it for the run, skip the walk-through
    app.run(max_frames=20)
    sys.exit(0)
assert app.current == "Home" and app.location == ""
assert home_view.node("came_from").get("text") == "just started"

home_button = home_view.node("button")
settings_button = settings_view.node("button")

# Three real, dispatched clicks, each firing from whichever screen is
# genuinely active at that moment -- Home -> Settings -> back to Home -> Settings,
# each switch happening *from inside* the handler App.show() calls into,
# the exact reentrant scenario tre's own M42 Phase 2 caught and fixed a
# real borrow-panic bug for. Each click also writes the shared state,
# which both screens show.
window.simulate("click", node=home_button)
assert app.current == "Settings" and app.location == "settings" and app.can_go_back.get()
assert settings_view.node("came_from").get("text") == home_view.node("came_from").get("text") == "from Home"

window.simulate("click", node=settings_button)  # back()
assert app.current == "Home" and app.can_go_forward.get()
assert home_view.node("came_from").get("text") == "from Settings"

window.simulate("click", node=home_button)
assert app.current == "Settings"
assert app.state.came_from.get() == "from Home"

logger.info(f"final screen: {app.current!r} (location {app.location!r}), came {app.state.came_from.get()}")

app.run(max_frames=20)
logger.info("examples/multi_screen/app.py: exited cleanly after a real 20-frame render loop")
