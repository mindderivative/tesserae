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
    root=HERE,
    custom_theme="Brand",
    stylesheet="Tasks",
    state=AppState(),
)
app.load("Window")  # Views/Window_View.yaml: its title bar, its rail, and the screens in it

app.navigate_to(sys.argv[1] if len(sys.argv) > 1 else "")
app.run()
