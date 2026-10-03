import sys
from pathlib import Path

from tesserae import App, Signal

from Settings_ViewModel import SettingsViewModel
from Tasks_ViewModel import TasksViewModel

HERE = Path(__file__).parent


class AppState:
    """What every screen shares: `self.state` in a ViewModel, `state` in a binding."""

    def __init__(self):
        self.user = Signal("Ada")


app = App(
    width=420,
    height=520,
    title="Tasks",
    custom_theme=HERE / "Brand_Theme.yaml",
    stylesheet=HERE / "Tasks_Stylesheet.yaml",
    state=AppState(),
)
app.load(HERE / "Tasks_View.yaml", TasksViewModel)
app.load(HERE / "Settings_View.yaml", SettingsViewModel)
app.route("", "Tasks")
app.route("settings", "Settings")

app.navigate_to(sys.argv[1] if len(sys.argv) > 1 else "")  # a route: `python app.py settings`
app.run()
