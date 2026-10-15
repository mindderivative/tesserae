import sys
from pathlib import Path

from tesserae import App, Signal

from Window_ViewModel import WindowViewModel

HERE = Path(__file__).parent


class AppState:
    """What every screen shares: `self.state` in a ViewModel, `app.state` in a view."""

    def __init__(self):
        self.user = Signal("Ada")


state = AppState()
app = App(
    title="Tasks",
    root=HERE,
    search=["."],
    custom_theme=HERE / "Brand_Theme.yaml",
    stylesheet=HERE / "Tasks_Stylesheet.yaml",
    state=state,
    window_border=False,  # no 1 px line around the frame; the title bar is the window's edge
)
app.bind(WindowViewModel(state))
app.open_view("Window")  # the window: its title bar, its rail, and the screens in it

app.navigate_to(sys.argv[1] if len(sys.argv) > 1 else "")
app.run()
