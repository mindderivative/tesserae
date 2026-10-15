import sys
from pathlib import Path

from tesserae import App, Signal

HERE = Path(__file__).parent


class AppState:
    """What every screen shares: `self.state` in a ViewModel, `app.state` in a view."""

    def __init__(self):
        self.user = Signal("Ada")


state = AppState()
app = App(title="Tasks", root=HERE, custom_theme="Brand", stylesheet="Tasks", state=state, window_border=False)
app.bind(app.project.viewmodel("Window")(state))
app.open_view("Window")  # Views/Window_View.yaml: the window, its rail and its screens

app.navigate_to(sys.argv[1] if len(sys.argv) > 1 else "")
app.run()
