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

`load()` builds each view with the app's theme and stylesheet, and a
screen built from a file is hot-reloaded by `app.run(hot_reload=True)`.
"""

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

window = app.show("Home")
assert app.current == "Home"
assert home_view.node("came_from").get("text") == "just started"

home_button = home_view.node("button")
settings_button = settings_view.node("button")

# Three real, dispatched clicks, each firing from whichever screen is
# genuinely active at that moment -- Home -> Settings -> Home -> Settings,
# each switch happening *from inside* the handler App.show() calls into,
# the exact reentrant scenario tre's own M42 Phase 2 caught and fixed a
# real borrow-panic bug for. Each click also writes the shared state,
# which both screens show.
window.simulate("click", node=home_button)
assert app.current == "Settings"
assert settings_view.node("came_from").get("text") == home_view.node("came_from").get("text") == "from Home"

window.simulate("click", node=settings_button)
assert app.current == "Home"
assert home_view.node("came_from").get("text") == "from Settings"

window.simulate("click", node=home_button)
assert app.current == "Settings"
assert app.state.came_from.get() == "from Home"

logger.info(f"final screen: {app.current!r}, came {app.state.came_from.get()}")

app.run(max_frames=20)
logger.info("examples/multi_screen/app.py: exited cleanly after a real 20-frame render loop")
