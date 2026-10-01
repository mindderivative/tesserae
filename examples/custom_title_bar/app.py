#!/usr/bin/env python3
"""A window with no OS title bar, whose title bar the app draws (0.3.0).

`App(decorations=False)` turns the OS's title bar and borders off; the
view's `kind: TitleBar` draws one in the app's theme -- its icon, title
and window buttons -- with a search field of the app's own in it, and a
second bar, built by hand, shows the pieces a TitleBar is made of:
`window_region: drag` and the `window.*` handlers.

Drag either bar to move the window, double-click one to maximize it,
and drag an edge to resize it. On macOS the OS keeps its traffic lights,
and the bar makes room for them.
"""

from pathlib import Path

from tesserae import App, configure_logging

from Home_ViewModel import HomeViewModel

configure_logging()

HERE = Path(__file__).parent

app = App(width=720, height=420, title="Notes", theme_seed=(0x67, 0x50, 0xA4, 0xFF),
          decorations=False, min_width=480, min_height=280)
app.load(HERE / "Home_View.yaml", HomeViewModel)
app.show("Home")
app.run(max_frames=20)  # a bounded run, as the other examples; remove max_frames to keep it open
