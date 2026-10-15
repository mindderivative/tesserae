#!/usr/bin/env python3
"""Tesserae's first vertical slice: a `Counter_View.yaml` and the `Counter_ViewModel.py` that serves it, opened through `App`.

`app.py` is the entry point: it binds the ViewModel, opens the view and shows it. It checks itself with real dispatched clicks, then renders 20 frames
and exits. Run it with `--interactive` to keep the window open. `app.run(hot_reload=True)` shows an edit to the view at once, the count kept.
"""

import sys
from pathlib import Path

from loguru import logger

from tesserae import App, configure_logging

from Counter_ViewModel import CounterViewModel

configure_logging()  # Tesserae's console format; configure_logging("DEBUG") shows more

directory = Path(__file__).parent

app = App(width=240, height=120, title="Tesserae Counter", root=directory, search=["."])
app.bind(CounterViewModel)  # the ViewModel that serves the view named `Counter`
view = app.open_view("Counter")  # Counter_View.yaml
window = app.show("Counter")

label = view.node("root.label")
button = view.node("root.button")

logger.info(f"before any click: label={label.get('text')!r}")
assert label.get("text") == "Count: 0"

for _ in range(3):  # three real, dispatched clicks
    window.simulate("click", node=button)

logger.info(f"after 3 clicks: label={label.get('text')!r}")
assert label.get("text") == "Count: 3"
assert button.get("label") == "Increment, count is 3"  # the button's accessible name follows the count
assert app.current == "Counter"

if "--interactive" in sys.argv[1:]:
    app.run(hot_reload=True)
else:
    app.run(max_frames=20)
    logger.info("examples/counter/app.py: exited cleanly after a real 20-frame render loop")
