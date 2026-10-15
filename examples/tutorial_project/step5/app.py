import sys
from pathlib import Path

from tesserae import App, Signal

HERE = Path(__file__).parent


class AppState:
    """What every screen shares: `self.state` in a ViewModel, `app.state` in a view."""

    def __init__(self):
        self.user = Signal("Ada")


state = AppState()
app = App(width=420, height=520, title="Tasks", root=HERE, custom_theme="Brand", stylesheet="Tasks", state=state)
app.bind(app.project.viewmodel("Main"))
app.bind(app.project.viewmodel("Settings")(state))  # a ViewModel you made yourself
app.open_view("Main")
app.open_view("Settings")
app.route("", "Main")
app.route("settings", "Settings")

app.navigate_to(sys.argv[1] if len(sys.argv) > 1 else "")  # a route: `python app.py settings`
app.run()
