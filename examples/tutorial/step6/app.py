import sys
from pathlib import Path

from tesserae import App, Signal

HERE = Path(__file__).parent


class AppState:
    """What every screen shares: `self.state` in a ViewModel, `state` in a binding."""

    def __init__(self):
        self.user = Signal("Ada")


app = App(
    title="Tasks",
    custom_theme=HERE / "Brand_Theme.yaml",
    stylesheet=HERE / "Tasks_Stylesheet.yaml",
    state=AppState(),
)
app.load(HERE / "Window_View.yaml")  # the window: its title bar, its rail, and the screens in it

app.navigate_to(sys.argv[1] if len(sys.argv) > 1 else "")
app.run()
