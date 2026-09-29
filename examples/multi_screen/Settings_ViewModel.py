"""`Home_ViewModel.py`'s counterpart -- see its docstring."""

from tesserae import ViewModel


class SettingsViewModel(ViewModel):
    def go_to_home(self):
        self.state.came_from.set("from Settings")
        self.app.show("Home")
