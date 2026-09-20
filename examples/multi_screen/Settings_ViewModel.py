"""`Home_ViewModel.py`'s own real counterpart -- see its docstring."""

from tesserae import ViewModel


class SettingsViewModel(ViewModel):
    def __init__(self, view, app):
        self._app = app
        super().__init__(view)

    def go_to_home(self):
        self._app.show("Home")
