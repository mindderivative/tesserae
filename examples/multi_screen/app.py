#!/usr/bin/env python3
"""Tesserae's own real, second vertical slice: `App.show(name)` switching
between two fully-bootstrapped, independent screens -- `Home`/`Settings`,
each its own `*_View.yaml` + `*_ViewModel.py` pair -- through the same
live `Window`, entirely from inside a real dispatched click handler on
each screen's own nav button.

Mirrors `tre`'s own `examples/live_view_switch.py` (which proves the
same real capability one layer lower, via `tre.Window.show_view`
directly) -- this proves it through Tesserae's own real `App` entry
point instead, the shape a real Tesserae app actually uses.

Uses `App.register()` directly rather than `App.load()`: each
`ViewModel` here needs a live reference to `app` itself (to call
`app.show(...)` from its own handler), which `load()`'s own narrower
`viewmodel_cls(view)` construction doesn't pass -- a real, honest
scope boundary, not an oversight. `load()` stays the right choice for
the common case (`examples/counter/app.py`), where a `ViewModel` never
needs to reach back into `App`.

Each view is built with `app.build_view`, not `tre.View(path)`: Tesserae
reads the file (and anything it includes) and hands `tre` only the
finished spec (M29), using the app's theme and stylesheet (M30) -- the
way to theme a screen given to `register()`.
"""

from pathlib import Path

from loguru import logger

from tesserae import App, configure_logging

from Home_ViewModel import HomeViewModel
from Settings_ViewModel import SettingsViewModel

configure_logging()  # Tesserae's console format; configure_logging("DEBUG") shows more

directory = Path(__file__).parent

app = App(width=240, height=120, title="Tesserae Multi-Screen")

home_view = app.build_view(directory / "Home_View.yaml")
home_vm = HomeViewModel(home_view, app)
app.register("Home", home_view, home_vm)

settings_view = app.build_view(directory / "Settings_View.yaml")
settings_vm = SettingsViewModel(settings_view, app)
app.register("Settings", settings_view, settings_vm)

window = app.show("Home")
assert app.current == "Home"

home_button = home_view.node("button")
settings_button = settings_view.node("button")

# Three real, dispatched clicks, each firing from whichever screen is
# genuinely active at that moment -- Home -> Settings -> Home -> Settings,
# each switch happening *from inside* the handler App.show() calls into,
# the exact reentrant scenario tre's own M42 Phase 2 caught and fixed a
# real borrow-panic bug for.
window.click(home_button)
assert app.current == "Settings"

window.click(settings_button)
assert app.current == "Home"

window.click(home_button)
assert app.current == "Settings"

logger.info(f"final screen: {app.current!r}")

app.run(max_frames=20)
logger.info("examples/multi_screen/app.py: exited cleanly after a real 20-frame render loop")
