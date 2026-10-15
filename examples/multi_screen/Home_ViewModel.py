"""Serves `Home_View.yaml`. Its handler navigates with `self.app.navigate(...)` and records where the user came from in the app's shared state:
`self.app` and `self.state` are found through the view's window. Switching from inside a real dispatched handler is the reentrant case."""

from tesserae import ViewModel


class HomeViewModel(ViewModel):
    views = "Home"

    def go_to_settings(self):
        self.state.came_from.set("from Home")
        self.app.navigate("Settings")  # a step in the history: Settings goes back from it
