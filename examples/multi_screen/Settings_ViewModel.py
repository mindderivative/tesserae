"""`Home_ViewModel.py`'s counterpart: it serves `Settings_View.yaml`. See its docstring."""

from tesserae import ViewModel


class SettingsViewModel(ViewModel):
    views = "Settings"

    def go_to_home(self):
        self.state.came_from.set("from Settings")
        self.app.back()  # to the screen that navigated here
